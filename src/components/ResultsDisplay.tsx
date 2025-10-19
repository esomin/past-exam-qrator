import { useState } from 'react';
import {
  FiFolder,
  FiHome,
  FiCalendar,
  FiFile,
  FiDownload,
  FiLoader,
  FiX,
  FiBarChart
} from 'react-icons/fi';
import type { ResultsDisplayProps } from '../types';

export default function ResultsDisplay({ results, onDownload }: ResultsDisplayProps) {
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Map<string, string>>(new Map());
  const [downloadProgress, setDownloadProgress] = useState<Map<string, number>>(new Map());

  const handleDownload = async (resultId: string) => {
    setDownloadingIds(prev => new Set(prev).add(resultId));
    setErrors(prev => {
      const newErrors = new Map(prev);
      newErrors.delete(resultId);
      return newErrors;
    });

    // Simulate download progress for better UX
    const progressInterval = setInterval(() => {
      setDownloadProgress(prev => {
        const newProgress = new Map(prev);
        const currentProgress = newProgress.get(resultId) || 0;
        if (currentProgress < 90) {
          newProgress.set(resultId, currentProgress + 10);
        }
        return newProgress;
      });
    }, 100);

    try {
      await onDownload(resultId);
      setDownloadProgress(prev => {
        const newProgress = new Map(prev);
        newProgress.set(resultId, 100);
        return newProgress;
      });

      // Clear progress after a short delay
      setTimeout(() => {
        setDownloadProgress(prev => {
          const newProgress = new Map(prev);
          newProgress.delete(resultId);
          return newProgress;
        });
      }, 1000);
    } catch (error) {
      setErrors(prev => {
        const newErrors = new Map(prev);
        newErrors.set(resultId, error instanceof Error ? error.message : 'Download failed');
        return newErrors;
      });
    } finally {
      clearInterval(progressInterval);
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
        return <FiFolder className="result-type-icon" />;
      case 'institution':
        return <FiHome className="result-type-icon" />;
      case 'year':
        return <FiCalendar className="result-type-icon" />;
      default:
        return <FiFile className="result-type-icon" />;
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
      <h3 className="results-title">Processing Results</h3>
      <p className="results-description">
        Your file has been processed successfully. Download the results below:
      </p>

      <div className="results-list">
        {results.map((result) => {
          const isDownloading = downloadingIds.has(result.id);
          const error = errors.get(result.id);
          const progress = downloadProgress.get(result.id);

          return (
            <div key={result.id} className="result-item">
              <div className="result-info">
                <div className="result-icon">
                  {getFileTypeIcon(result.type)}
                </div>
                <div className="result-details">
                  <h4 className="result-item-title">
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
                      <FiLoader className="download-spinner" />
                      {progress !== undefined ? `${progress}%` : 'Downloading...'}
                    </>
                  ) : (
                    <>
                      <FiDownload className="download-icon" />
                      Download
                    </>
                  )}
                </button>
              </div>

              {isDownloading && progress !== undefined && (
                <div className="download-progress">
                  <div className="download-progress-bar">
                    <div
                      className="download-progress-fill"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              )}

              {error && (
                <div className="result-error">
                  <FiX className="error-icon" />
                  <span className="error-message">{error}</span>
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
        <FiBarChart className="summary-icon" />
        <span className="summary-text">
          {results.length} result{results.length > 1 ? 's' : ''} ready for download
        </span>
      </div>
    </div>
  );
}