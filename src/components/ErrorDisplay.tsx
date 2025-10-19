import { useState } from 'react';
import type { ErrorState } from '../types';
import { ErrorHandler } from '../utils/errorHandler';

interface ErrorDisplayProps {
  error: ErrorState;
  onDismiss?: () => void;
  onRetry?: () => void;
  showDetails?: boolean;
  className?: string;
}

export default function ErrorDisplay({ 
  error, 
  onDismiss, 
  onRetry, 
  showDetails = false,
  className = '' 
}: ErrorDisplayProps) {
  const [showFullDetails, setShowFullDetails] = useState(false);
  
  const severity = ErrorHandler.getErrorSeverity({
    code: error.code || 'UNKNOWN',
    message: error.message
  });
  
  const suggestions = ErrorHandler.getRecoverySuggestions({
    code: error.code || 'UNKNOWN',
    message: error.message
  });

  const getIcon = () => {
    switch (severity) {
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '❌';
    }
  };

  const getSeverityClass = () => {
    switch (severity) {
      case 'warning':
        return 'error-warning';
      case 'info':
        return 'error-info';
      default:
        return 'error-error';
    }
  };

  return (
    <div className={`error-display ${getSeverityClass()} ${className}`}>
      <div className="error-header">
        <div className="error-icon-message">
          <span className="error-icon">{getIcon()}</span>
          <div className="error-content">
            <p className="error-message">{error.message}</p>
            {error.code && (
              <p className="error-code">Error Code: {error.code}</p>
            )}
          </div>
        </div>
        
        <div className="error-actions">
          {error.recoverable && (onRetry || error.retryAction) && (
            <button
              className="retry-btn"
              onClick={() => {
                if (onRetry) {
                  onRetry();
                } else if (error.retryAction) {
                  error.retryAction();
                }
              }}
            >
              🔄 Retry
            </button>
          )}
          
          {onDismiss && (
            <button
              className="dismiss-btn"
              onClick={onDismiss}
              aria-label="Dismiss error"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {suggestions.length > 0 && (
        <div className="error-suggestions">
          <p className="suggestions-title">Try these solutions:</p>
          <ul className="suggestions-list">
            {suggestions.map((suggestion, index) => (
              <li key={index} className="suggestion-item">
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}

      {(showDetails || error.details) && (
        <div className="error-details">
          <button
            className="details-toggle"
            onClick={() => setShowFullDetails(!showFullDetails)}
          >
            {showFullDetails ? '▼' : '▶'} Technical Details
          </button>
          
          {showFullDetails && (
            <div className="details-content">
              {error.details && (
                <div className="detail-item">
                  <strong>Details:</strong> {error.details}
                </div>
              )}
              <div className="detail-item">
                <strong>Timestamp:</strong> {error.timestamp.toLocaleString()}
              </div>
              {error.code && (
                <div className="detail-item">
                  <strong>Error Code:</strong> {error.code}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}