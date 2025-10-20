import axios, { AxiosError } from 'axios';
import type { ProcessFileRequest, ProcessFileResponse, ApiError, NetworkError, ValidationError } from '../types';

const API_BASE_URL = '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout for file processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Enhanced error handling utilities
const handleApiError = (error: AxiosError): ApiError | NetworkError => {
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
    const networkError: NetworkError = {
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to the server. Please check your connection and try again.',
      details: error.message,
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
  
  // File size validation (10MB limit)
  const maxSize = 10 * 1024 * 1024; // 10MB
  if (file.size > maxSize) {
    errors.push({
      field: 'file',
      message: 'File size must be less than 10MB',
      code: 'FILE_TOO_LARGE'
    });
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

// Convert File to base64 string
const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      // Remove the data:application/json;base64, prefix
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = (error) => reject(error);
  });
};

// API Functions

/**
 * Upload and process a JSON file with selected classification options
 */
export const processFile = async (
  file: File,
  selectedOptions: string[]
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

    // Convert file to base64 with error handling
    let fileData: string;
    try {
      fileData = await fileToBase64(file);
    } catch (error) {
      return {
        success: false,
        error: {
          code: 'FILE_READ_ERROR',
          message: 'Failed to read the uploaded file',
          details: error instanceof Error ? error.message : 'Unknown file read error'
        },
      };
    }

    const requestData: ProcessFileRequest = {
      file_data: fileData,
      filename: file.name,
      options: selectedOptions,
    };

    // Use retry mechanism for network requests
    const response = await retryRequest(
      () => api.post<ProcessFileResponse>('/process', requestData),
      3,
      1000
    );
    
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
    console.warn('Server health check failed:', error);
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

    console.log(`Fetching JSON data for download ID: ${downloadId}`);
    console.log(`Request URL: ${API_BASE_URL}/data/${downloadId}`);

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

    console.log(`Successfully fetched data, status: ${response.status}`);
    console.log(`Response headers:`, response.headers);

    // Validate response
    if (!response.data) {
      throw new Error('No data received from server');
    }

    console.log(`Data type: ${typeof response.data}, size: ${JSON.stringify(response.data).length} chars`);
    return response.data;
  } catch (error) {
    console.error('Error in fetchJsonData:', error);
    
    const apiError = handleApiError(error as AxiosError);
    
    // Provide more specific error messages for data fetch
    let errorMessage = apiError.message;
    if (apiError.code === 'NETWORK_ERROR') {
      errorMessage = 'Failed to fetch data due to network issues. Please check your connection and try again.';
    } else if (apiError.code === 'FILE_NOT_FOUND') {
      errorMessage = 'The requested data is no longer available. It may have expired.';
    }
    
    console.error(`Final error message: ${errorMessage}`);
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