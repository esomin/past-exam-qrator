import { useState, useEffect, useCallback } from 'react'
import FileUpload from './components/FileUpload'
import ProcessingOptions from './components/ProcessingOptions'
import ResultsDisplay from './components/ResultsDisplay'
import ErrorDisplay from './components/ErrorDisplay'
import ProgressIndicator from './components/ProgressIndicator'
import { processFile, downloadFile, getServerStatus } from './services/api'
import { useErrorHandler } from './utils/errorHandler'
import type { ProcessingOption, ProcessingResult, ErrorState } from './types'
import './App.css'

function App() {
  // State management
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [selectedOptions, setSelectedOptions] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [isUploading] = useState(false)
  const [results, setResults] = useState<ProcessingResult[]>([])
  const [errors, setErrors] = useState<ErrorState[]>([])
  const [serverAvailable, setServerAvailable] = useState<boolean | null>(null)
  const [serverError, setServerError] = useState<string | null>(null)
  const [processingProgress, setProcessingProgress] = useState<number>(0)
  const [processingMessage, setProcessingMessage] = useState<string>('')
  
  // Error handling
  const { handleError } = useErrorHandler()

  // Processing options configuration
  const processingOptions: ProcessingOption[] = [
    {
      id: 'category',
      label: 'Category Classification',
      description: 'Group questions by their category fields'
    },
    {
      id: 'institution',
      label: 'Institution Classification',
      description: 'Group questions by institution extracted from solve field'
    },
    {
      id: 'year',
      label: 'Year Classification',
      description: 'Group questions by year extracted from solve field'
    }
  ]

  // Check server health on component mount and periodically
  useEffect(() => {
    const checkServer = async () => {
      const status = await getServerStatus()
      setServerAvailable(status.available)
      
      if (!status.available) {
        setServerError(status.error || 'Server is not available')
      } else {
        setServerError(null)
      }
    }
    
    // Initial check
    checkServer()
    
    // Periodic health checks every 30 seconds when server is unavailable
    const interval = setInterval(() => {
      if (!serverAvailable) {
        checkServer()
      }
    }, 30000)
    
    return () => clearInterval(interval)
  }, [serverAvailable])

  // Handle file upload
  const handleFileUpload = useCallback((file: File) => {
    setUploadedFile(file)
    setErrors([]) // Clear previous errors
    setResults([]) // Clear previous results
  }, [])

  // Handle processing options change
  const handleOptionsChange = useCallback((options: string[]) => {
    setSelectedOptions(options)
    // Clear validation errors when options change
    setErrors(prev => prev.filter(error => error.code !== 'NO_OPTIONS_SELECTED'))
  }, [])

  // Handle file processing
  const handleProcessFile = useCallback(async () => {
    if (!uploadedFile || selectedOptions.length === 0) {
      const errorState = handleError(
        {
          code: 'NO_OPTIONS_SELECTED',
          message: 'Please upload a file and select at least one processing option'
        },
        'File Processing'
      )
      setErrors(prev => [...prev, errorState])
      return
    }

    setIsProcessing(true)
    setErrors([]) // Clear previous errors
    setProcessingProgress(0)
    setProcessingMessage('Preparing file for processing...')

    try {
      // Simulate progress updates for better UX
      const progressSteps = [
        { progress: 10, message: 'Uploading file to server...' },
        { progress: 30, message: 'Parsing JSON data...' },
        { progress: 50, message: `Processing ${selectedOptions.length} classification${selectedOptions.length > 1 ? 's' : ''}...` },
        { progress: 80, message: 'Generating output files...' },
        { progress: 95, message: 'Finalizing results...' }
      ]

      // Update progress incrementally
      for (const step of progressSteps) {
        setProcessingProgress(step.progress)
        setProcessingMessage(step.message)
        await new Promise(resolve => setTimeout(resolve, 500)) // Small delay for UX
      }

      const response = await processFile(uploadedFile, selectedOptions)
      
      setProcessingProgress(100)
      setProcessingMessage('Processing complete!')
      
      if (response.success && response.results) {
        // Convert API results to ProcessingResult format
        const processedResults: ProcessingResult[] = response.results.map(result => ({
          id: result.download_id,
          type: result.type,
          filename: result.filename,
          data: null // Data is not returned in the API response, only download_id
        }))
        
        setResults(processedResults)
      } else if (response.error) {
        const errorState = handleError(
          response.error,
          'File Processing',
          () => handleProcessFile() // Retry action
        )
        setErrors(prev => [...prev, errorState])
      }
    } catch (err) {
      const errorState = handleError(
        {
          code: 'INTERNAL_ERROR',
          message: 'An unexpected error occurred during processing',
          details: err instanceof Error ? err.message : 'Unknown error'
        },
        'File Processing',
        () => handleProcessFile() // Retry action
      )
      setErrors(prev => [...prev, errorState])
    } finally {
      setIsProcessing(false)
      setProcessingProgress(0)
      setProcessingMessage('')
    }
  }, [uploadedFile, selectedOptions, handleError])

  // Handle file download
  const handleDownload = useCallback(async (resultId: string) => {
    const result = results.find(r => r.id === resultId)
    if (!result) {
      const errorState = handleError(
        {
          code: 'FILE_NOT_FOUND',
          message: 'Result not found'
        },
        'File Download'
      )
      setErrors(prev => [...prev, errorState])
      return
    }

    try {
      await downloadFile(resultId, result.filename)
    } catch (err) {
      const errorState = handleError(
        {
          code: 'DOWNLOAD_ERROR',
          message: err instanceof Error ? err.message : 'Download failed',
          details: err instanceof Error ? err.message : 'Unknown download error'
        },
        'File Download',
        () => handleDownload(resultId) // Retry action
      )
      setErrors(prev => [...prev, errorState])
    }
  }, [results, handleError])

  // Determine if processing should be enabled
  const canProcess = uploadedFile && selectedOptions.length > 0 && !isProcessing && serverAvailable

  // Error management functions
  const dismissError = useCallback((index: number) => {
    setErrors(prev => prev.filter((_, i) => i !== index))
  }, [])

  const dismissAllErrors = useCallback(() => {
    setErrors([])
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>React File Processor</h1>
        <p>Upload JSON files and process them with multiple classification options</p>
      </header>

      <main className="app-main">
        {/* Server status indicator */}
        {serverAvailable === false && (
          <ErrorDisplay
            error={{
              message: serverError || 'Unable to connect to the processing server. Please ensure the Python backend is running.',
              code: 'NETWORK_ERROR',
              timestamp: new Date(),
              recoverable: true,
              retryAction: async () => {
                const status = await getServerStatus()
                setServerAvailable(status.available)
                if (!status.available) {
                  setServerError(status.error || 'Server is not available')
                } else {
                  setServerError(null)
                }
              }
            }}
            className="server-error"
          />
        )}

        {/* Error Display Section */}
        {errors.length > 0 && (
          <section className="error-section">
            {errors.length > 1 && (
              <div className="error-header">
                <h3>Multiple Errors ({errors.length})</h3>
                <button className="dismiss-all-btn" onClick={dismissAllErrors}>
                  Dismiss All
                </button>
              </div>
            )}
            {errors.map((error, index) => (
              <ErrorDisplay
                key={`${error.code}-${error.timestamp.getTime()}`}
                error={error}
                onDismiss={() => dismissError(index)}
                showDetails={true}
                className="app-error"
              />
            ))}
          </section>
        )}

        {/* File Upload Section */}
        <section className="upload-section">
          <FileUpload 
            onFileUpload={handleFileUpload}
            isUploading={isUploading}
          />
        </section>

        {/* Processing Options Section */}
        {uploadedFile && (
          <section className="options-section">
            <ProcessingOptions
              options={processingOptions}
              onOptionsChange={handleOptionsChange}
              disabled={!serverAvailable}
              isProcessing={isProcessing}
            />
          </section>
        )}

        {/* Process Button */}
        {uploadedFile && selectedOptions.length > 0 && (
          <section className="process-section">
            <button
              className={`process-btn ${isProcessing ? 'processing' : ''}`}
              onClick={handleProcessFile}
              disabled={!canProcess}
            >
              {isProcessing ? (
                <>
                  <div className="process-spinner"></div>
                  Processing...
                </>
              ) : (
                <>
                  <span className="process-icon">⚡</span>
                  Process File
                </>
              )}
            </button>
          </section>
        )}



        {/* Results Display */}
        {isProcessing && (
          <section className="results-section">
            <div className="results-loading">
              <div className="results-loading-spinner"></div>
              <div className="results-loading-text">Processing your file...</div>
              <div className="results-loading-subtext">
                This may take a few moments depending on file size
              </div>
            </div>
          </section>
        )}

        {!isProcessing && results.length > 0 && (
          <section className="results-section">
            <ResultsDisplay
              results={results}
              onDownload={handleDownload}
            />
          </section>
        )}
      </main>

      <footer className="app-footer">
        <p>Upload your JSON files and select processing options to get started</p>
      </footer>

      {/* Progress Indicator Overlay */}
      <ProgressIndicator
        isVisible={isProcessing}
        message={processingMessage}
        progress={processingProgress}
        subMessage={`Processing ${selectedOptions.length} classification type${selectedOptions.length > 1 ? 's' : ''}`}
      />
    </div>
  )
}

export default App
