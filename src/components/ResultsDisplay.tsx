import { useState, useCallback, useMemo } from 'react';
import {
  FiFolder,
  FiHome,
  FiCalendar,
  FiFile,
  FiDownload,
  FiLoader,
  FiX,
  FiBarChart,
  FiPackage
} from 'react-icons/fi';
import type { ResultsDisplayProps } from '../types';

export default function ResultsDisplay({
  results,
  onDownload,
  onBulkDownload,
  onSelectionChange
}: ResultsDisplayProps) {
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Map<string, string>>(new Map());
  const [downloadProgress, setDownloadProgress] = useState<Map<string, number>>(new Map());
  const [isBulkDownloading, setIsBulkDownloading] = useState(false);

  const selectedResults = useMemo(() =>
    results.filter(result => result.selected),
    [results]
  );

  const allSelected = useMemo(() =>
    results.length > 0 && results.every(result => result.selected),
    [results]
  );

  const someSelected = useMemo(() =>
    results.some(result => result.selected),
    [results]
  );

  const handleSelectAll = useCallback(() => {
    const newSelected = !allSelected;
    results.forEach(result => {
      if (onSelectionChange) {
        onSelectionChange(result.id, newSelected);
      }
    });
  }, [allSelected, results, onSelectionChange]);

  const handleSelectionChange = useCallback((resultId: string, selected: boolean) => {
    if (onSelectionChange) {
      onSelectionChange(resultId, selected);
    }
  }, [onSelectionChange]);

  // Group results by source filename for better organization
  const groupedResults = useMemo(() => {
    const groups = new Map<string, typeof results>();
    results.forEach(result => {
      const sourceFile = result.sourceFilename || 'Unknown';
      if (!groups.has(sourceFile)) {
        groups.set(sourceFile, []);
      }
      groups.get(sourceFile)!.push(result);
    });
    return groups;
  }, [results]);

  const handleSourceFileSelectAll = useCallback((sourceFile: string) => {
    const fileResults = groupedResults.get(sourceFile) || [];
    const allFileSelected = fileResults.every(result => result.selected);
    const newSelected = !allFileSelected;

    fileResults.forEach(result => {
      if (onSelectionChange) {
        onSelectionChange(result.id, newSelected);
      }
    });
  }, [groupedResults, onSelectionChange]);

  const handleBulkDownload = useCallback(async () => {
    if (!onBulkDownload || selectedResults.length === 0) return;

    setIsBulkDownloading(true);
    try {
      const selectedIds = selectedResults.map(result => result.id);

      // 하나의 파일만 선택된 경우 개별 다운로드
      if (selectedIds.length === 1) {
        await onDownload(selectedIds[0]);
      } else {
        // 여러 파일 선택시 zip으로 다운로드
        await onBulkDownload(selectedIds);
      }
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setIsBulkDownloading(false);
    }
  }, [onBulkDownload, onDownload, selectedResults]);

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
      <div className="results-header">
        <div className="results-title-section">
          <h3 className="results-title">Processing Results</h3>
          <p className="results-description">
            Your {results.length > 1 ? 'files have' : 'file has'} been processed successfully.
            {onBulkDownload && ' Select files and download individually or in bulk:'}
          </p>
        </div>

        {onBulkDownload && (
          <div className="bulk-actions">
            {results.length > 1 && (
              <label className="select-all-label">
                <input
                  type="checkbox"
                  checked={allSelected}
                  ref={input => {
                    if (input) input.indeterminate = someSelected && !allSelected;
                  }}
                  onChange={handleSelectAll}
                  className="select-all-checkbox"
                />
                Select All ({results.length})
              </label>
            )}

            <button
              className={`bulk-download-btn ${isBulkDownloading ? 'downloading' : ''}`}
              onClick={handleBulkDownload}
              disabled={selectedResults.length === 0 || isBulkDownloading}
            >
              {isBulkDownloading ? (
                <>
                  <FiLoader className="download-spinner" />
                  {selectedResults.length === 1 ? 'Downloading...' : 'Creating Archive...'}
                </>
              ) : (
                <>
                  {selectedResults.length === 1 ? (
                    <>
                      <FiDownload className="download-icon" />
                      Download File
                    </>
                  ) : (
                    <>
                      <FiPackage className="bulk-icon" />
                      Download Selected ({selectedResults.length})
                    </>
                  )}
                </>
              )}
            </button>
          </div>
        )}
      </div>

      <div className="results-content">
        {Array.from(groupedResults.entries()).map(([sourceFile, fileResults]) => {
          const allFileSelected = fileResults.every(result => result.selected);
          const someFileSelected = fileResults.some(result => result.selected);

          return (
            <div key={sourceFile} className="source-file-group">
              {groupedResults.size > 1 && (
                <div className="source-file-header">
                  <h4 className="source-file-title">
                    <FiFile className="source-file-icon" />
                    {sourceFile}
                  </h4>
                  {onSelectionChange && (
                    <label className="source-select-all-label">
                      <input
                        type="checkbox"
                        checked={allFileSelected}
                        ref={input => {
                          if (input) input.indeterminate = someFileSelected && !allFileSelected;
                        }}
                        onChange={() => handleSourceFileSelectAll(sourceFile)}
                        className="source-select-all-checkbox"
                        aria-label={`Select all files from ${sourceFile}`}
                      />
                      Select All ({fileResults.length})
                    </label>
                  )}
                </div>
              )}

              <div className="results-list">
                {fileResults.map((result) => {
                  const isDownloading = downloadingIds.has(result.id);
                  const error = errors.get(result.id);
                  const progress = downloadProgress.get(result.id);

                  return (
                    <label
                      key={result.id}
                      className={`result-item ${result.selected ? 'selected' : ''} ${onSelectionChange ? 'clickable' : ''}`}
                    >
                      {onSelectionChange && (
                        <input
                          type="checkbox"
                          checked={result.selected || false}
                          onChange={(e) => handleSelectionChange(result.id, e.target.checked)}
                          className="result-checkbox"
                          aria-label={`Select ${result.filename}`}
                        />
                      )}

                      <div className="result-content">
                        <div className="result-header">
                          <div className="result-icon">
                            {getFileTypeIcon(result.type)}
                          </div>
                          <span className="result-label">
                            {formatFileType(result.type)}
                          </span>
                        </div>
                        <div className="result-description">
                          <span className="result-filename">{result.filename}</span>
                          {result.data && (
                            <span className="result-stats">
                              {Object.keys(result.data).length} categories found
                            </span>
                          )}
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
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDownload(result.id);
                              }}
                            >
                              Retry
                            </button>
                          </div>
                        )}
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>
          )
        })}
      </div>

      <div className="results-summary">
        <FiBarChart className="summary-icon" />
        <span className="summary-text">
          {results.length} result{results.length > 1 ? 's' : ''} ready for download
          {onBulkDownload && selectedResults.length > 0 &&
            ` • ${selectedResults.length} selected`
          }
        </span>
      </div>
    </div>
  );
}