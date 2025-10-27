// Type definitions for the application

export interface ProcessingOption {
  id: string;
  label: string;
  description: string;
  disabled?: boolean; // Optional property to disable specific options
}

export interface ProcessingResult {
  id: string;
  type: string;
  filename: string;
  data: any;
  downloadUrl?: string;
  sourceId?: string; // For markdown files that reference original JSON data
  sourceFilename?: string; // Original source file name
  selected?: boolean; // For bulk download selection
}

export interface FileUploadProps {
  onFileUpload: (files: File[]) => void;
  isUploading: boolean;
  multiple?: boolean;
  maxFiles?: number;
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
  onBulkDownload?: (selectedIds: string[]) => void;
  onSelectionChange?: (resultId: string, selected: boolean) => void;
}

// API Request/Response Types
export interface ProcessFileRequest {
  file_data: string; // base64 encoded JSON
  filename: string;
  options: string[]; // ["category", "institution", "year"]
  similarity_threshold?: number; // 0.0 to 1.0, default 0.8
}

export interface ProcessMultipleFilesRequest {
  files: Array<{
    file_data: string; // base64 encoded JSON
    filename: string;
  }>;
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

export interface CategoryStatistics {
  total_items: number;
  duplicate_items: number;
  unique_items: number;
  duplicate_percentage: number;
  unique_percentage: number;
}

export interface FilterStatistics {
  original_items: number;
  filtered_items: number;
  filter_percentage: number;
}

export interface ProcessFileResponse {
  success: boolean;
  results?: ProcessingResultInfo[];
  statistics?: ProcessingStatistics;
  category_statistics?: CategoryStatistics;
  filter_statistics?: FilterStatistics;
  processed_items?: number;
  original_questions?: number;
  error?: ApiError;
}

export interface ProcessingResultInfo {
  type: string;
  filename: string;
  download_id: string;
  sourceFilename?: string;
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