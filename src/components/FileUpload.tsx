import React, { useState, useCallback } from 'react';
import { FileUploadProps } from '../types';

export default function FileUpload({ onFileUpload, isUploading }: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const validateFile = (file: File): boolean => {
    if (file.type !== 'application/json' && !file.name.endsWith('.json')) {
      setError('Please upload a JSON file only');
      return false;
    }
    setError(null);
    return true;
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      if (validateFile(file)) {
        setUploadedFile(file);
        onFileUpload(file);
      }
    }
  }, [onFileUpload]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (validateFile(file)) {
        setUploadedFile(file);
        onFileUpload(file);
      }
    }
  }, [onFileUpload]);

  return (
    <div className="file-upload-container">
      <div
        className={`file-upload-area ${isDragOver ? 'drag-over' : ''} ${uploadedFile ? 'has-file' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="upload-content">
          {isUploading ? (
            <div className="uploading-state">
              <div className="spinner"></div>
              <p>Uploading file...</p>
            </div>
          ) : uploadedFile ? (
            <div className="file-info">
              <div className="file-icon">📄</div>
              <p className="file-name">{uploadedFile.name}</p>
              <p className="file-size">{(uploadedFile.size / 1024).toFixed(2)} KB</p>
              <button 
                className="change-file-btn"
                onClick={() => {
                  setUploadedFile(null);
                  setError(null);
                }}
              >
                Change File
              </button>
            </div>
          ) : (
            <div className="upload-prompt">
              <div className="upload-icon">📁</div>
              <h3>Drop your JSON file here</h3>
              <p>or</p>
              <label className="file-input-label">
                <input
                  type="file"
                  accept=".json,application/json"
                  onChange={handleFileInput}
                  className="file-input"
                />
                Choose File
              </label>
              <p className="file-requirements">Only JSON files are supported</p>
            </div>
          )}
        </div>
      </div>
      
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}
    </div>
  );
}