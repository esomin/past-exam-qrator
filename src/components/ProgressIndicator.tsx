// React import removed - not needed in React 17+

interface ProgressIndicatorProps {
  isVisible: boolean;
  message: string;
  progress?: number; // 0-100 percentage
  subMessage?: string;
  showSpinner?: boolean;
}

export default function ProgressIndicator({ 
  isVisible, 
  message, 
  progress, 
  subMessage,
  showSpinner = true 
}: ProgressIndicatorProps) {
  if (!isVisible) return null;

  return (
    <div className="progress-indicator">
      <div className="progress-content">
        {showSpinner && (
          <div className="progress-spinner"></div>
        )}
        <div className="progress-text">
          <h4 className="progress-message">{message}</h4>
          {subMessage && (
            <p className="progress-sub-message">{subMessage}</p>
          )}
        </div>
      </div>
      
      {typeof progress === 'number' && (
        <div className="progress-bar-container">
          <div className="progress-bar">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            />
          </div>
          <span className="progress-percentage">{Math.round(progress)}%</span>
        </div>
      )}
    </div>
  );
}