import React, { useState, useCallback } from 'react';
import { FiFile, FiFolder } from 'react-icons/fi';
import type { FileUploadProps, ErrorState } from '../types';
import { useErrorHandler } from '../utils/errorHandler';
import ErrorDisplay from './ErrorDisplay';

export default function FileUpload({ onFileUpload, isUploading }: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [errors, setErrors] = useState<ErrorState[]>([]);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const { handleError } = useErrorHandler();

  const validateFile = async (file: File): Promise<boolean> => {
    setIsValidating(true);
    const validationErrors: ErrorState[] = [];
    
    try {
      // File type validation
      if (file.type !== 'application/json' && !file.name.endsWith('.json')) {
        validationErrors.push(handleError({
          code: 'INVALID_FILE_TYPE',
          message: 'Please upload a JSON file only'
        }, 'File Validation'));
      }
      
      // File size validation (10MB limit)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        validationErrors.push(handleError({
          code: 'FILE_TOO_LARGE',
          message: 'File size must be less than 10MB'
        }, 'File Validation'));
      }
      
      // Empty file validation
      if (file.size === 0) {
        validationErrors.push(handleError({
          code: 'FILE_EMPTY',
          message: 'The uploaded file is empty'
        }, 'File Validation'));
      }
      
      // Filename validation
      if (file.name.length > 255) {
        validationErrors.push(handleError({
          code: 'FILENAME_TOO_LONG',
          message: 'Filename is too long (maximum 255 characters)'
        }, 'File Validation'));
      }

      // JSON content validation (basic check)
      if (validationErrors.length === 0) {
        try {
          const text = await file.text();
          JSON.parse(text);
        } catch (jsonError) {
          validationErrors.push(handleError({
            code: 'INVALID_JSON',
            message: 'The file contains invalid JSON format'
          }, 'File Validation'));
        }
      }
      
      setErrors(validationErrors);
      return validationErrors.length === 0;
    } finally {
      setIsValidating(false);
    }
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

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      if (await validateFile(file)) {
        setUploadedFile(file);
        onFileUpload(file);
      }
    }
  }, [onFileUpload]);

  const handleFileInput = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (await validateFile(file)) {
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
          ) : isValidating ? (
            <div className="validating-state">
              <div className="spinner"></div>
              <p>Validating file...</p>
            </div>
          ) : uploadedFile ? (
            <div className="file-success-content">
              <div className="success-icon-container">
                <FiFile className="success-file-icon" />
                <div className="success-badge">✓</div>
              </div>
              <h3 className="success-title">File Ready</h3>
              <p className="success-filename">{uploadedFile.name}</p>
              <div className="success-meta">
                <span className="meta-item">{(uploadedFile.size / 1024).toFixed(2)} KB</span>
                <span className="meta-separator">•</span>
                <span className="meta-item">JSON</span>
              </div>
              <button 
                className="change-file-btn"
                onClick={() => {
                  setUploadedFile(null);
                  setErrors([]);
                }}
              >
                Upload Different File
              </button>
            </div>
          ) : (
            <div className="upload-prompt">
              <FiFolder className="upload-icon" />
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
      
      {errors.length > 0 && (
        <div className="upload-errors">
          {errors.map((error, index) => (
            <ErrorDisplay
              key={`${error.code}-${error.timestamp.getTime()}`}
              error={error}
              onDismiss={() => setErrors(prev => prev.filter((_, i) => i !== index))}
              className="upload-error"
            />
          ))}
        </div>
      )}
    </div>
  );
}