import React, { useState, useCallback } from 'react';
import { FiFile, FiFolder } from 'react-icons/fi';
import type { FileUploadProps, ErrorState } from '../types';
import { useErrorHandler } from '../utils/errorHandler';
import ErrorDisplay from './ErrorDisplay';

export default function FileUpload({ onFileUpload, isUploading, multiple = false, maxFiles = 10 }: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [errors, setErrors] = useState<ErrorState[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  const { handleError } = useErrorHandler();

  const validateFile = async (file: File): Promise<{ isValid: boolean; errors: ErrorState[] }> => {
    const validationErrors: ErrorState[] = [];
    
    try {
      // File type validation
      if (file.type !== 'application/json' && !file.name.endsWith('.json')) {
        validationErrors.push(handleError({
          code: 'INVALID_FILE_TYPE',
          message: `${file.name}: Please upload a JSON file only`
        }, 'File Validation'));
      }
      
      // File size validation (10MB limit)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        validationErrors.push(handleError({
          code: 'FILE_TOO_LARGE',
          message: `${file.name}: File size must be less than 10MB`
        }, 'File Validation'));
      }
      
      // Empty file validation
      if (file.size === 0) {
        validationErrors.push(handleError({
          code: 'FILE_EMPTY',
          message: `${file.name}: The uploaded file is empty`
        }, 'File Validation'));
      }
      
      // Filename validation
      if (file.name.length > 255) {
        validationErrors.push(handleError({
          code: 'FILENAME_TOO_LONG',
          message: `${file.name}: Filename is too long (maximum 255 characters)`
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
            message: `${file.name}: The file contains invalid JSON format`
          }, 'File Validation'));
        }
      }
      
      return { isValid: validationErrors.length === 0, errors: validationErrors };
    } catch (error) {
      return { 
        isValid: false, 
        errors: [handleError({
          code: 'VALIDATION_ERROR',
          message: `${file.name}: Failed to validate file`
        }, 'File Validation')]
      };
    }
  };

  const validateFiles = async (files: File[]): Promise<{ validFiles: File[]; allErrors: ErrorState[] }> => {
    setIsValidating(true);
    const validFiles: File[] = [];
    const allErrors: ErrorState[] = [];

    // Check file count limit
    if (multiple && files.length > maxFiles) {
      allErrors.push(handleError({
        code: 'TOO_MANY_FILES',
        message: `Maximum ${maxFiles} files allowed. Selected ${files.length} files.`
      }, 'File Validation'));
      files = files.slice(0, maxFiles);
    }

    // Check for duplicate filenames
    const filenames = new Set<string>();
    const duplicateFiles: string[] = [];
    
    for (const file of files) {
      if (filenames.has(file.name)) {
        duplicateFiles.push(file.name);
      } else {
        filenames.add(file.name);
      }
    }

    if (duplicateFiles.length > 0) {
      allErrors.push(handleError({
        code: 'DUPLICATE_FILENAMES',
        message: `Duplicate filenames found: ${duplicateFiles.join(', ')}`
      }, 'File Validation'));
    }

    // Validate each file
    for (const file of files) {
      if (!duplicateFiles.includes(file.name)) {
        const { isValid, errors } = await validateFile(file);
        if (isValid) {
          validFiles.push(file);
        }
        allErrors.push(...errors);
      }
    }

    setIsValidating(false);
    return { validFiles, allErrors };
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
      const filesToProcess = multiple ? files : [files[0]];
      const { validFiles, allErrors } = await validateFiles(filesToProcess);
      
      setErrors(allErrors);
      
      if (validFiles.length > 0) {
        const newFiles = multiple ? [...uploadedFiles, ...validFiles] : validFiles;
        setUploadedFiles(newFiles);
        onFileUpload(newFiles);
      }
    }
  }, [onFileUpload, multiple, uploadedFiles, maxFiles]);

  const handleFileInput = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const filesToProcess = Array.from(files);
      const { validFiles, allErrors } = await validateFiles(filesToProcess);
      
      setErrors(allErrors);
      
      if (validFiles.length > 0) {
        const newFiles = multiple ? [...uploadedFiles, ...validFiles] : validFiles;
        setUploadedFiles(newFiles);
        onFileUpload(newFiles);
      }
    }
    
    // Reset input value to allow re-uploading the same file
    e.target.value = '';
  }, [onFileUpload, multiple, uploadedFiles, maxFiles]);

  const removeFile = useCallback((index: number) => {
    const newFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(newFiles);
    onFileUpload(newFiles);
    setErrors([]);
  }, [uploadedFiles, onFileUpload]);

  const clearAllFiles = useCallback(() => {
    setUploadedFiles([]);
    onFileUpload([]);
    setErrors([]);
  }, [onFileUpload]);

  return (
    <div className="file-upload-container">
      <div
        className={`file-upload-area ${isDragOver ? 'drag-over' : ''} ${uploadedFiles.length > 0 ? 'has-files' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="upload-content">
          {isUploading ? (
            <div className="uploading-state">
              <div className="spinner"></div>
              <p>Uploading {multiple ? 'files' : 'file'}...</p>
            </div>
          ) : isValidating ? (
            <div className="validating-state">
              <div className="spinner"></div>
              <p>Validating {multiple ? 'files' : 'file'}...</p>
            </div>
          ) : uploadedFiles.length > 0 ? (
            <div className="files-success-content">
              <div className="success-header">
                <div className="success-icon-container">
                  <FiFile className="success-file-icon" />
                  <div className="success-badge">✓</div>
                </div>
                <div className="success-info">
                  <h3 className="success-title">
                    {uploadedFiles.length} File{uploadedFiles.length > 1 ? 's' : ''} Ready
                  </h3>
                  <div className="success-meta">
                    <span className="meta-item">
                      {(uploadedFiles.reduce((sum, file) => sum + file.size, 0) / 1024).toFixed(2)} KB total
                    </span>
                    <span className="meta-separator">•</span>
                    <span className="meta-item">JSON</span>
                  </div>
                </div>
                {uploadedFiles.length > 1 && (
                  <button 
                    className="clear-all-btn"
                    onClick={clearAllFiles}
                    title="Remove all files"
                  >
                    Clear All
                  </button>
                )}
              </div>
              
              <div className="uploaded-files-list">
                {uploadedFiles.map((file, index) => (
                  <div key={`${file.name}-${index}`} className="uploaded-file-item">
                    <div className="file-info">
                      <FiFile className="file-icon" />
                      <div className="file-details">
                        <span className="file-name">{file.name}</span>
                        <span className="file-size">{(file.size / 1024).toFixed(2)} KB</span>
                      </div>
                    </div>
                    <button 
                      className="remove-file-btn"
                      onClick={() => removeFile(index)}
                      title={`Remove ${file.name}`}
                      aria-label={`Remove ${file.name}`}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
              
              {multiple && uploadedFiles.length < maxFiles && (
                <label className="add-more-label">
                  <input
                    type="file"
                    accept=".json,application/json"
                    onChange={handleFileInput}
                    className="file-input"
                    multiple={multiple}
                  />
                  Add More Files ({uploadedFiles.length}/{maxFiles})
                </label>
              )}
            </div>
          ) : (
            <div className="upload-prompt">
              <FiFolder className="upload-icon" />
              <h3>Drop your JSON {multiple ? 'files' : 'file'} here</h3>
              <p>or</p>
              <label className="file-input-label">
                <input
                  type="file"
                  accept=".json,application/json"
                  onChange={handleFileInput}
                  className="file-input"
                  multiple={multiple}
                />
                Choose {multiple ? 'Files' : 'File'}
              </label>
              <p className="file-requirements">
                Only JSON files are supported
                {multiple && ` (max ${maxFiles} files)`}
              </p>
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