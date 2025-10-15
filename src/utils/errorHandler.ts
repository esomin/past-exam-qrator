/**
 * Error handling utilities for the React File Processor
 */

import type { ApiError, ErrorState, NetworkError } from '../types';

export class ErrorHandler {
  /**
   * Convert API error to user-friendly error state
   */
  static createErrorState(error: ApiError | NetworkError, retryAction?: () => void): ErrorState {
    const isNetworkError = 'isNetworkError' in error && error.isNetworkError;
    
    return {
      message: this.getUserFriendlyMessage(error),
      code: error.code,
      details: error.details,
      timestamp: new Date(),
      recoverable: this.isRecoverable(error),
      retryAction: (isNetworkError || this.isRecoverable(error)) ? retryAction : undefined
    };
  }

  /**
   * Get user-friendly error message based on error code
   */
  static getUserFriendlyMessage(error: ApiError | NetworkError): string {
    switch (error.code) {
      case 'NETWORK_ERROR':
        return 'Unable to connect to the server. Please check your internet connection and try again.';
      
      case 'INVALID_FILE_TYPE':
        return 'Please upload a valid JSON file. Other file types are not supported.';
      
      case 'FILE_TOO_LARGE':
        return 'The file is too large. Please upload a file smaller than 10MB.';
      
      case 'NO_OPTIONS_SELECTED':
        return 'Please select at least one processing option before continuing.';
      
      case 'PROCESSING_ERROR':
        return 'There was an error processing your file. Please check the file format and try again.';
      
      case 'FILE_NOT_FOUND':
        return 'The requested file is no longer available. It may have expired or been removed.';
      
      case 'DOWNLOAD_ERROR':
        return 'Failed to download the file. Please try again.';
      
      case 'SERVER_ERROR':
        return 'A server error occurred. Please try again in a few moments.';
      
      case 'INTERNAL_ERROR':
        return 'An unexpected error occurred. Please try again or contact support if the problem persists.';
      
      case 'FILE_READ_ERROR':
        return 'Unable to read the uploaded file. Please ensure the file is not corrupted and try again.';
      
      case 'INVALID_OPTIONS':
        return 'Invalid processing options selected. Please refresh the page and try again.';
      
      case 'MISSING_FIELD':
        return 'Required information is missing. Please refresh the page and try again.';
      
      case 'REQUEST_ERROR':
        return 'There was an error preparing your request. Please try again.';
      
      default:
        return error.message || 'An unexpected error occurred. Please try again.';
    }
  }

  /**
   * Determine if an error is recoverable (user can retry)
   */
  static isRecoverable(error: ApiError | NetworkError): boolean {
    const recoverableErrors = [
      'NETWORK_ERROR',
      'SERVER_ERROR',
      'INTERNAL_ERROR',
      'DOWNLOAD_ERROR',
      'REQUEST_ERROR'
    ];
    
    return recoverableErrors.includes(error.code);
  }

  /**
   * Determine if an error should show retry button
   */
  static shouldShowRetry(error: ApiError | NetworkError): boolean {
    return this.isRecoverable(error) || ('retryable' in error && error.retryable);
  }

  /**
   * Get error severity level for styling
   */
  static getErrorSeverity(error: ApiError | NetworkError): 'error' | 'warning' | 'info' {
    const warningErrors = ['INVALID_FILE_TYPE', 'NO_OPTIONS_SELECTED', 'FILE_TOO_LARGE'];
    const infoErrors = ['FILE_NOT_FOUND'];
    
    if (warningErrors.includes(error.code)) {
      return 'warning';
    }
    
    if (infoErrors.includes(error.code)) {
      return 'info';
    }
    
    return 'error';
  }

  /**
   * Log error for debugging (in development)
   */
  static logError(error: ApiError | NetworkError, context?: string): void {
    if (process.env.NODE_ENV === 'development') {
      console.group(`🚨 Error${context ? ` in ${context}` : ''}`);
      console.error('Code:', error.code);
      console.error('Message:', error.message);
      if (error.details) {
        console.error('Details:', error.details);
      }
      console.error('Timestamp:', new Date().toISOString());
      console.groupEnd();
    }
  }

  /**
   * Create recovery suggestions based on error type
   */
  static getRecoverySuggestions(error: ApiError | NetworkError): string[] {
    switch (error.code) {
      case 'NETWORK_ERROR':
        return [
          'Check your internet connection',
          'Ensure the server is running',
          'Try refreshing the page',
          'Wait a moment and try again'
        ];
      
      case 'INVALID_FILE_TYPE':
        return [
          'Upload a .json file',
          'Check the file extension',
          'Ensure the file contains valid JSON data'
        ];
      
      case 'FILE_TOO_LARGE':
        return [
          'Reduce the file size',
          'Split large datasets into smaller files',
          'Remove unnecessary data from the JSON'
        ];
      
      case 'PROCESSING_ERROR':
        return [
          'Check the JSON file format',
          'Ensure all required fields are present',
          'Validate the JSON structure',
          'Try with a smaller dataset first'
        ];
      
      case 'SERVER_ERROR':
      case 'INTERNAL_ERROR':
        return [
          'Wait a few moments and try again',
          'Refresh the page',
          'Contact support if the problem persists'
        ];
      
      default:
        return ['Try again', 'Refresh the page if the problem persists'];
    }
  }
}

/**
 * Hook for managing error state in components
 */
export const useErrorHandler = () => {
  const handleError = (error: ApiError | NetworkError, context?: string, retryAction?: () => void): ErrorState => {
    ErrorHandler.logError(error, context);
    return ErrorHandler.createErrorState(error, retryAction);
  };

  return { handleError };
};