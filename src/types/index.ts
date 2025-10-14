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
}

export interface FileUploadProps {
  onFileUpload: (file: File) => void;
  isUploading: boolean;
}

export interface ProcessingOptionsProps {
  options: ProcessingOption[];
  onOptionsChange: (selectedOptions: string[]) => void;
  disabled: boolean;
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

export interface ProcessFileResponse {
  success: boolean;
  results?: ProcessingResultInfo[];
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

export interface DownloadResponse {
  success: boolean;
  error?: ApiError;
}