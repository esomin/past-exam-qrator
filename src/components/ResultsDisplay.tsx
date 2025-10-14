import { useState } from 'react';
import type { ResultsDisplayProps } from '../types';

export default function ResultsDisplay({ results, onDownload }: ResultsDisplayProps) {
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Map<string, string>>(new Map());

  const handleDownload = async (resultId: string) => {
    setDownloadingIds(prev => new Set(prev).add(resultId));
    setErrors(prev => {
      const newErrors = new Map(prev);
      newErrors.delete(resultId);
      return newErrors;
    });

    try {
      await onDownload(resultId);
    } catch (error) {
      setErrors(prev => {
        const newErrors = new Map(prev);
        newErrors.set(resultId, error instanceof Error ? error.message : 'Download failed');
        return newErrors;
      });
    } finally {
      setDownloadingIds(prev => {
        const newIds = new Set(prev);
        newIds.delete(resultId);
        return newIds;
      });
    }
  };

  const getFileTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'category':
        return '📂';
      case 'institution':
        return '🏛️';
      case 'year':
        return '📅';
      default:
        return '📄';
    }
  };

  const formatFileType = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1) + ' Classification';
  };

  if (results.length === 0) {
    return null;
  }

  return (
    <div className="results-display-container">
      <h3>Processing Results</h3>
      <p className="results-description">
        Your file has been processed successfully. Download the results below:
      </p>

      <div className="results-list">
        {results.map((result) => {
          const isDownloading = downloadingIds.has(result.id);
          const error = errors.get(result.id);

          return (
            <div key={result.id} className="result-item">
              <div className="result-info">
                <div className="result-icon">
                  {getFileTypeIcon(result.type)}
                </div>
                <div className="result-details">
                  <h4 className="result-title">
                    {formatFileType(result.type)}
                  </h4>
                  <p className="result-filename">{result.filename}</p>
                  {result.data && (
                    <p className="result-stats">
                      {Object.keys(result.data).length} categories found
                    </p>
                  )}
                </div>
              </div>

              <div className="result-actions">
                <button
                  className={`download-btn ${isDownloading ? 'downloading' : ''}`}
                  onClick={() => handleDownload(result.id)}
                  disabled={isDownloading}
                >
                  {isDownloading ? (
                    <>
                      <div className="download-spinner"></div>
                      Downloading...
                    </>
                  ) : (
                    <>
                      <span className="download-icon">⬇️</span>
                      Download
                    </>
                  )}
                </button>
              </div>

              {error && (
                <div className="result-error">
                  <span className="error-icon">❌</span>
                  {error}
                  <button
                    className="retry-btn"
                    onClick={() => handleDownload(result.id)}
                  >
                    Retry
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="results-summary">
        <span className="summary-icon">📊</span>
        {results.length} result{results.length > 1 ? 's' : ''} ready for download
      </div>
    </div>
  );
}