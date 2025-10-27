import axios, { AxiosError } from 'axios';
import type { ProcessFileResponse, ApiError, NetworkError, ValidationError } from '../types';

// Environment-based API base URL configuration
const getApiBaseUrl = (): string => {
  // Check if we're in development mode
  if (import.meta.env.DEV) {
    // Development: direct connection to Python backend
    return 'http://localhost:5001/api';
  } else {
    // Production: assume API is served from same origin
    return '/api';
  }
};

const API_BASE_URL = getApiBaseUrl();

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 second timeout for large file processing
  headers: {
    'Content-Type': 'application/json',
  },
  maxContentLength: Infinity,
  maxBodyLength: Infinity,
});

// Enhanced error handling utilities
const handleApiError = (error: AxiosError): ApiError | NetworkError => {
  // Log detailed error information for debugging
  console.error('API Error Details:', {
    message: error.message,
    code: error.code,
    status: error.response?.status,
    statusText: error.response?.statusText,
    data: error.response?.data,
    config: {
      url: error.config?.url,
      method: error.config?.method,
      timeout: error.config?.timeout,
      dataSize: error.config?.data ? JSON.stringify(error.config.data).length : 0
    }
  });

  if (error.response?.data) {
    // Server returned an error response
    const serverError = error.response.data as any;
    return {
      code: serverError.error?.code || 'SERVER_ERROR',
      message: serverError.error?.message || 'An error occurred on the server',
      details: serverError.error?.details,
    };
  } else if (error.request) {
    // Network error - no response received
    let errorMessage = 'Unable to connect to the server. Please check your connection and try again.';
    let errorDetails = error.message;

    // Provide more specific error messages based on error code
    if (error.code === 'ECONNABORTED') {
      errorMessage = 'Request timeout. The file may be too large or the server is taking too long to respond.';
      errorDetails = 'Try uploading a smaller file or check your network connection.';
    } else if (error.code === 'ERR_NETWORK') {
      errorMessage = 'Network error. Unable to reach the server.';
      errorDetails = 'Please check if the server is running and your network connection is stable.';
    } else if (error.message.includes('timeout')) {
      errorMessage = 'Request timeout. The operation took too long to complete.';
      errorDetails = 'This may be due to a large file size or slow network connection.';
    }

    const networkError: NetworkError = {
      code: 'NETWORK_ERROR',
      message: errorMessage,
      details: errorDetails,
      isNetworkError: true,
      retryable: true,
    };
    return networkError;
  } else {
    // Request setup error
    return {
      code: 'REQUEST_ERROR',
      message: 'An error occurred while preparing the request',
      details: error.message,
    };
  }
};

// Client-side validation utilities
const validateFile = (file: File): ValidationError[] => {
  const errors: ValidationError[] = [];

  // File type validation
  if (!file.type.includes('json') && !file.name.endsWith('.json')) {
    errors.push({
      field: 'file',
      message: 'Please upload a valid JSON file',
      code: 'INVALID_FILE_TYPE'
    });
  }

  // File size validation (50MB limit - increased for larger files)
  const maxSize = 50 * 1024 * 1024; // 50MB
  const fileSizeMB = file.size / (1024 * 1024);

  console.log(`File validation: ${file.name}, Size: ${fileSizeMB.toFixed(2)}MB`);

  if (file.size > maxSize) {
    errors.push({
      field: 'file',
      message: `File size must be less than 50MB (current: ${fileSizeMB.toFixed(2)}MB)`,
      code: 'FILE_TOO_LARGE'
    });
  }

  // Warning for large files (over 10MB)
  if (file.size > 10 * 1024 * 1024 && file.size <= maxSize) {
    console.warn(`Large file detected: ${file.name} (${fileSizeMB.toFixed(2)}MB). Processing may take longer.`);
  }

  // File name validation
  if (file.name.length > 255) {
    errors.push({
      field: 'filename',
      message: 'Filename is too long (maximum 255 characters)',
      code: 'FILENAME_TOO_LONG'
    });
  }

  return errors;
};

const validateProcessingOptions = (options: string[]): ValidationError[] => {
  const errors: ValidationError[] = [];
  const validOptions = ['category', 'institution', 'year'];

  if (!Array.isArray(options) || options.length === 0) {
    errors.push({
      field: 'options',
      message: 'Please select at least one processing option',
      code: 'NO_OPTIONS_SELECTED'
    });
    return errors;
  }

  const invalidOptions = options.filter(option => !validOptions.includes(option));
  if (invalidOptions.length > 0) {
    errors.push({
      field: 'options',
      message: `Invalid processing options: ${invalidOptions.join(', ')}`,
      code: 'INVALID_OPTIONS'
    });
  }

  return errors;
};

// Retry mechanism for network errors
const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: Error;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error as Error;

      // Only retry on network errors
      if (error instanceof Error && error.message.includes('NETWORK_ERROR') && attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, delay * attempt));
        continue;
      }

      throw error;
    }
  }

  throw lastError!;
};

// Note: fileToBase64 function removed - now using FormData for better performance

// API Functions

/**
 * Upload and process a JSON file with selected classification options
 */
export const processFile = async (
  file: File,
  selectedOptions: string[],
  similarityThreshold: number = 0.8,
  filterOptions?: any,
  onProgress?: (progress: number, message: string) => void
): Promise<ProcessFileResponse> => {
  try {
    // Client-side validation
    const fileErrors = validateFile(file);
    if (fileErrors.length > 0) {
      return {
        success: false,
        error: {
          code: fileErrors[0].code,
          message: fileErrors[0].message,
          details: fileErrors.map(e => e.message).join('; ')
        },
      };
    }

    const optionErrors = validateProcessingOptions(selectedOptions);
    if (optionErrors.length > 0) {
      return {
        success: false,
        error: {
          code: optionErrors[0].code,
          message: optionErrors[0].message,
          details: optionErrors.map(e => e.message).join('; ')
        },
      };
    }

    // Use FormData instead of base64 for better performance
    const fileSizeMB = file.size / (1024 * 1024);
    console.log(`Preparing file upload: ${file.name} (${fileSizeMB.toFixed(2)}MB)`);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('options', JSON.stringify(selectedOptions));
    formData.append('similarity_threshold', similarityThreshold.toString());
    if (filterOptions) {
      formData.append('filter_options', JSON.stringify(filterOptions));
    }

    console.log(`Sending request to server: ${fileSizeMB.toFixed(2)}MB`);
    console.log(`Request details: file=${file.name}, options=${selectedOptions.join(',')}, threshold=${similarityThreshold}`);

    // Start timing
    const startTime = Date.now();

    // Use retry mechanism for network requests (no retry for large files to avoid timeout)
    const shouldRetry = fileSizeMB < 10; // Only retry for files smaller than 10MB
    const response = await retryRequest(
      () => api.post<ProcessFileResponse>('/process', formData, {
        timeout: fileSizeMB > 10 ? 300000 : 120000, // 5 minutes for large files, 2 minutes for normal
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            console.log(`Upload progress: ${percentCompleted}%`);
            if (onProgress) {
              onProgress(percentCompleted, 'Uploading file to server...');
            }
          }
        }
      }),
      shouldRetry ? 2 : 1, // Retry only for smaller files
      2000
    );

    // Calculate total processing time
    const endTime = Date.now();
    const totalTime = ((endTime - startTime) / 1000).toFixed(2);
    console.log(`✅ Processing completed in ${totalTime}s`);
    console.log('Server response received successfully');
    return response.data;
  } catch (error) {
    const apiError = handleApiError(error as AxiosError);
    return {
      success: false,
      error: apiError,
    };
  }
};

/**
 * Upload and process multiple JSON files as a merged dataset with selected classification options
 */
export const processMergedFiles = async (
  files: File[],
  selectedOptions: string[],
  similarityThreshold: number = 0.8,
  filterOptions?: any,
  onProgress?: (progress: number, message: string) => void
): Promise<ProcessFileResponse> => {
  try {
    // Validate files array
    if (!Array.isArray(files) || files.length === 0) {
      return {
        success: false,
        error: {
          code: 'NO_FILES_PROVIDED',
          message: 'Please provide at least one file to process',
        },
      };
    }

    // Client-side validation for all files
    const allFileErrors: ValidationError[] = [];
    for (let i = 0; i < files.length; i++) {
      const fileErrors = validateFile(files[i]);
      if (fileErrors.length > 0) {
        allFileErrors.push(...fileErrors.map(error => ({
          ...error,
          message: `File ${i + 1} (${files[i].name}): ${error.message}`
        })));
      }
    }

    if (allFileErrors.length > 0) {
      return {
        success: false,
        error: {
          code: allFileErrors[0].code,
          message: allFileErrors[0].message,
          details: allFileErrors.map(e => e.message).join('; ')
        },
      };
    }

    const optionErrors = validateProcessingOptions(selectedOptions);
    if (optionErrors.length > 0) {
      return {
        success: false,
        error: {
          code: optionErrors[0].code,
          message: optionErrors[0].message,
          details: optionErrors.map(e => e.message).join('; ')
        },
      };
    }

    // Use FormData instead of base64 for better performance
    const totalSizeMB = files.reduce((sum, f) => sum + f.size, 0) / (1024 * 1024);
    console.log(`Preparing merged file upload: ${files.length} files, total: ${totalSizeMB.toFixed(2)}MB`);

    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    formData.append('options', JSON.stringify(selectedOptions));
    formData.append('similarity_threshold', similarityThreshold.toString());
    if (filterOptions) {
      formData.append('filter_options', JSON.stringify(filterOptions));
    }

    console.log(`Sending merged request to server: ${totalSizeMB.toFixed(2)}MB (${files.length} files)`);
    console.log(`Request details: files=${files.map(f => f.name).join(', ')}, options=${selectedOptions.join(',')}, threshold=${similarityThreshold}`);

    // Start timing
    const startTime = Date.now();

    // Use retry mechanism for network requests (no retry for large files to avoid timeout)
    const shouldRetry = totalSizeMB < 10; // Only retry for files smaller than 10MB total
    const response = await retryRequest(
      () => api.post<ProcessFileResponse>('/process-merged', formData, {
        timeout: totalSizeMB > 10 ? 300000 : 120000, // 5 minutes for large files, 2 minutes for normal
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            console.log(`Upload progress: ${percentCompleted}%`);
            if (onProgress) {
              onProgress(percentCompleted, 'Uploading files to server...');
            }
          }
        }
      }),
      shouldRetry ? 2 : 1, // Retry only for smaller files
      2000
    );

    // Calculate total processing time
    const endTime = Date.now();
    const totalTime = ((endTime - startTime) / 1000).toFixed(2);
    console.log(`✅ Processing completed in ${totalTime}s`);
    console.log('Server response received successfully');
    return response.data;
  } catch (error) {
    const apiError = handleApiError(error as AxiosError);
    return {
      success: false,
      error: apiError,
    };
  }
};

/**
 * Upload and process multiple JSON files individually with selected classification options
 */
export const processMultipleFiles = async (
  files: File[],
  selectedOptions: string[],
  similarityThreshold: number = 0.8,
  filterOptions?: any,
  onProgress?: (progress: number, message: string) => void
): Promise<ProcessFileResponse> => {
  try {
    // Validate files array
    if (!Array.isArray(files) || files.length === 0) {
      return {
        success: false,
        error: {
          code: 'NO_FILES_PROVIDED',
          message: 'Please provide at least one file to process',
        },
      };
    }

    // Client-side validation for all files
    const allFileErrors: ValidationError[] = [];
    for (let i = 0; i < files.length; i++) {
      const fileErrors = validateFile(files[i]);
      if (fileErrors.length > 0) {
        allFileErrors.push(...fileErrors.map(error => ({
          ...error,
          message: `File ${i + 1} (${files[i].name}): ${error.message}`
        })));
      }
    }

    if (allFileErrors.length > 0) {
      return {
        success: false,
        error: {
          code: allFileErrors[0].code,
          message: allFileErrors[0].message,
          details: allFileErrors.map(e => e.message).join('; ')
        },
      };
    }

    const optionErrors = validateProcessingOptions(selectedOptions);
    if (optionErrors.length > 0) {
      return {
        success: false,
        error: {
          code: optionErrors[0].code,
          message: optionErrors[0].message,
          details: optionErrors.map(e => e.message).join('; ')
        },
      };
    }

    // Process each file individually
    const allResults: any[] = [];
    let totalProcessedItems = 0;
    let totalOriginalQuestions = 0;
    const combinedStats = {
      original_questions: 0,
      original_answers: 0,
      result_questions: 0,
      result_answers: 0,
      duplicate_count: 0,
      removed_duplicate_answers: 0
    };

    // Start timing
    const startTime = Date.now();

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const fileSizeMB = file.size / (1024 * 1024);
      console.log(`Processing file ${i + 1}/${files.length}: ${file.name} (${fileSizeMB.toFixed(2)}MB)`);

      try {
        // Process individual file with progress callback
        const fileResult = await processFile(file, selectedOptions, similarityThreshold, filterOptions, (progress, message) => {
          if (onProgress) {
            // Distribute progress across all files
            const fileProgress = Math.round((i / files.length) * 20 + (progress / files.length));
            onProgress(fileProgress, `${message} (${i + 1}/${files.length})`);
          }
        });

        if (fileResult.success && fileResult.results) {
          // Add source filename to each result
          const resultsWithSource = fileResult.results.map(result => ({
            ...result,
            sourceFilename: file.name
          }));
          allResults.push(...resultsWithSource);

          totalProcessedItems += fileResult.processed_items || 0;
          totalOriginalQuestions += fileResult.original_questions || 0;

          // Combine statistics
          if (fileResult.statistics) {
            Object.keys(combinedStats).forEach(key => {
              combinedStats[key as keyof typeof combinedStats] +=
                fileResult.statistics![key as keyof typeof combinedStats] || 0;
            });
          }
        } else if (fileResult.error) {
          return {
            success: false,
            error: {
              ...fileResult.error,
              message: `Error processing ${file.name}: ${fileResult.error.message}`
            }
          };
        }
      } catch (error) {
        return {
          success: false,
          error: {
            code: 'FILE_PROCESSING_ERROR',
            message: `Failed to process file: ${file.name}`,
            details: error instanceof Error ? error.message : 'Unknown error'
          }
        };
      }
    }

    // Calculate total processing time
    const endTime = Date.now();
    const totalTime = ((endTime - startTime) / 1000).toFixed(2);
    console.log(`✅ All files processing completed in ${totalTime}s`);

    return {
      success: true,
      results: allResults,
      processed_items: totalProcessedItems,
      original_questions: totalOriginalQuestions,
      statistics: combinedStats
    };

  } catch (error) {
    const apiError = handleApiError(error as AxiosError);
    return {
      success: false,
      error: apiError,
    };
  }
};

/**
 * Download multiple files as a ZIP archive
 */
export const downloadMultipleFiles = async (resultIds: string[], archiveName: string = 'processed_files.zip'): Promise<void> => {
  try {
    if (!resultIds || resultIds.length === 0) {
      throw new Error('No files selected for download');
    }

    // Use retry mechanism for bulk download requests
    const response = await retryRequest(
      () => {
        return api.post('/download-multiple', {
          result_ids: resultIds,
          archive_name: archiveName
        }, {
          responseType: 'blob',
          timeout: 120000, // 2 minute timeout for bulk downloads
        });
      },
      2,
      2000
    );

    // Validate response
    if (!response.data || response.data.size === 0) {
      throw new Error('Downloaded archive is empty or corrupted');
    }

    // Create blob URL and trigger download
    const blob = new Blob([response.data], { type: 'application/zip' });
    const url = window.URL.createObjectURL(blob);

    try {
      // Create temporary link element and trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = archiveName;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
    } finally {
      // Always cleanup the blob URL
      window.URL.revokeObjectURL(url);
    }
  } catch (error) {
    const apiError = handleApiError(error as AxiosError);

    // Provide more specific error messages for bulk downloads
    let errorMessage = apiError.message;
    if (apiError.code === 'NETWORK_ERROR') {
      errorMessage = 'Bulk download failed due to network issues. Please check your connection and try again.';
    } else if (apiError.code === 'FILE_NOT_FOUND') {
      errorMessage = 'Some of the requested files are no longer available. They may have expired.';
    }

    throw new Error(errorMessage);
  }
};

/**
 * Download a processed file by its download ID
 */
export const downloadFile = async (downloadId: string, filename: string): Promise<void> => {
  try {
    // Validate inputs
    if (!downloadId || !filename) {
      throw new Error('Download ID and filename are required');
    }

    // Use retry mechanism for download requests
    const response = await retryRequest(
      () => api.get(`/download/${downloadId}`, {
        responseType: 'blob',
        timeout: 60000, // 60 second timeout for downloads
      }),
      2, // Fewer retries for downloads
      2000
    );

    // Validate response
    if (!response.data || response.data.size === 0) {
      throw new Error('Downloaded file is empty or corrupted');
    }

    // Create blob URL and trigger download
    const blob = new Blob([response.data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);

    try {
      // Create temporary link element and trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
    } finally {
      // Always cleanup the blob URL
      window.URL.revokeObjectURL(url);
    }
  } catch (error) {
    const apiError = handleApiError(error as AxiosError);

    // Provide more specific error messages for downloads
    let errorMessage = apiError.message;
    if (apiError.code === 'NETWORK_ERROR') {
      errorMessage = 'Download failed due to network issues. Please check your connection and try again.';
    } else if (apiError.code === 'FILE_NOT_FOUND') {
      errorMessage = 'The requested file is no longer available. It may have expired.';
    }

    throw new Error(errorMessage);
  }
};

/**
 * Check if the backend server is available
 */
export const checkServerHealth = async (): Promise<boolean> => {
  try {
    await api.get('/health', { timeout: 5000 }); // 5 second timeout for health checks
    return true;
  } catch (error) {
    return false;
  }
};

/**
 * Fetch JSON data for a processed file by its download ID (for markdown conversion)
 */
export const fetchJsonData = async (downloadId: string): Promise<any> => {
  try {
    // Validate input
    if (!downloadId) {
      throw new Error('Download ID is required');
    }

    // Use retry mechanism for data fetch requests
    const response = await retryRequest(
      () => api.get(`/data/${downloadId}`, {
        responseType: 'json',
        timeout: 30000, // 30 second timeout
        headers: {
          'Accept': 'application/json',
        }
      }),
      2, // Fewer retries for data fetch
      1000
    );

    // Validate response
    if (!response.data) {
      throw new Error('No data received from server');
    }

    return response.data;
  } catch (error) {

    const apiError = handleApiError(error as AxiosError);

    // Provide more specific error messages for data fetch
    let errorMessage = apiError.message;
    if (apiError.code === 'NETWORK_ERROR') {
      errorMessage = 'Failed to fetch data due to network issues. Please check your connection and try again.';
    } else if (apiError.code === 'FILE_NOT_FOUND') {
      errorMessage = 'The requested data is no longer available. It may have expired.';
    }

    throw new Error(errorMessage);
  }
};

/**
 * Download markdown file converted from JSON data
 */
export const downloadMarkdownFile = async (downloadId: string, filename: string): Promise<void> => {
  try {
    // Validate inputs
    if (!downloadId || !filename) {
      throw new Error('Download ID and filename are required');
    }

    const url = `/convert-to-markdown/${downloadId}`;

    // Use retry mechanism for download requests
    const response = await retryRequest(
      () => api.get(url, {
        responseType: 'blob',
        timeout: 60000, // 60 second timeout for downloads
      }),
      2, // Fewer retries for downloads
      2000
    );

    // Validate response
    if (!response.data || response.data.size === 0) {
      throw new Error('Downloaded file is empty or corrupted');
    }

    // Create blob URL and trigger download
    const blob = new Blob([response.data], { type: 'text/markdown' });
    const blobUrl = window.URL.createObjectURL(blob);

    try {
      // Create temporary link element and trigger download
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
    } finally {
      // Always cleanup the blob URL
      window.URL.revokeObjectURL(blobUrl);
    }
  } catch (error) {
    const apiError = handleApiError(error as AxiosError);

    // Provide more specific error messages for downloads
    let errorMessage = apiError.message;
    if (apiError.code === 'NETWORK_ERROR') {
      errorMessage = 'Markdown download failed due to network issues. Please check your connection and try again.';
    } else if (apiError.code === 'FILE_NOT_FOUND') {
      errorMessage = 'The requested file is no longer available. It may have expired.';
    }

    throw new Error(errorMessage);
  }
};

/**
 * Enhanced server health check with detailed status
 */
export const getServerStatus = async (): Promise<{
  available: boolean;
  error?: string;
  details?: any;
}> => {
  try {
    const response = await api.get('/health', { timeout: 5000 });
    return {
      available: true,
      details: response.data
    };
  } catch (error) {
    const apiError = handleApiError(error as AxiosError);
    return {
      available: false,
      error: apiError.message,
      details: apiError
    };
  }
};