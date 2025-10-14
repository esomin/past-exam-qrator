import axios, { AxiosError } from 'axios';
import type { ProcessFileRequest, ProcessFileResponse, ApiError } from '../types';

const API_BASE_URL = 'http://localhost:5000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout for file processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Error handling utility
const handleApiError = (error: AxiosError): ApiError => {
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
    return {
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to the server. Please check your connection and try again.',
      details: error.message,
    };
  } else {
    // Request setup error
    return {
      code: 'REQUEST_ERROR',
      message: 'An error occurred while preparing the request',
      details: error.message,
    };
  }
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
    // Validate file type
    if (!file.type.includes('json') && !file.name.endsWith('.json')) {
      return {
        success: false,
        error: {
          code: 'INVALID_FILE_TYPE',
          message: 'Please upload a valid JSON file',
        },
      };
    }

    // Validate options
    if (selectedOptions.length === 0) {
      return {
        success: false,
        error: {
          code: 'NO_OPTIONS_SELECTED',
          message: 'Please select at least one processing option',
        },
      };
    }

    // Convert file to base64
    const fileData = await fileToBase64(file);

    const requestData: ProcessFileRequest = {
      file_data: fileData,
      filename: file.name,
      options: selectedOptions,
    };

    const response = await api.post<ProcessFileResponse>('/process', requestData);
    
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
    const response = await api.get(`/download/${downloadId}`, {
      responseType: 'blob',
    });

    // Create blob URL and trigger download
    const blob = new Blob([response.data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    
    // Create temporary link element and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    const apiError = handleApiError(error as AxiosError);
    throw new Error(apiError.message);
  }
};

/**
 * Check if the backend server is available
 */
export const checkServerHealth = async (): Promise<boolean> => {
  try {
    await api.get('/health');
    return true;
  } catch (error) {
    return false;
  }
};