// Type definitions for the application

export interface ProcessingOption {
  id: string;
  label: string;
  description: string;
}

export interface ProcessingResult {
  id: string;
  type: string;
  filename: string;
  data: any;
  downloadUrl?: string;
  sourceId?: string; // For markdown files that reference original JSON data
}

export interface FileUploadProps {
  onFileUpload: (file: File) => void;
  isUploading: boolean;
}

export interface ProcessingOptionsProps {
  options: ProcessingOption[];
  onOptionsChange: (selectedOptions: string[]) => void;
  disabled: boolean;
  isProcessing?: boolean;
}

export interface ResultsDisplayProps {
  results: ProcessingResult[];
  onDownload: (resultId: string) => void;
}

// API Request/Response Types
export interface ProcessFileRequest {
  file_data: string; // base64 encoded JSON
  filename: string;
  options: string[]; // ["category", "institution", "year"]
}

export interface ProcessingStatistics {
  original_questions: number;
  original_answers: number;
  result_questions: number;
  result_answers: number;
  duplicate_count: number;
  removed_duplicate_answers: number;
}

export interface ProcessFileResponse {
  success: boolean;
  results?: ProcessingResultInfo[];
  statistics?: ProcessingStatistics;
  error?: ApiError;
}

export interface ProcessingResultInfo {
  type: string;
  filename: string;
  download_id: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: string;
}

// Enhanced error types for better error handling
export interface ErrorState {
  message: string;
  code?: string;
  details?: string;
  timestamp: Date;
  recoverable: boolean;
  retryAction?: () => void;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface NetworkError extends ApiError {
  isNetworkError: true;
  retryable: boolean;
}

export interface DownloadResponse {
  success: boolean;
  error?: ApiError;
}