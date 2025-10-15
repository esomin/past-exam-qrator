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
    <div className="app" role="main">
      {/* Skip to main content link for accessibility */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <header className="app-header" role="banner">
        <div className="header-content">
          <h1 className="app-title">React File Processor</h1>
          <p className="app-description">
            Upload JSON files and process them with multiple classification options
          </p>
          
          {/* Server status indicator */}
          {serverAvailable !== null && (
            <div className={`server-status ${serverAvailable ? 'online' : 'offline'}`}>
              <span className="status-indicator" aria-hidden="true">
                {serverAvailable ? '🟢' : '🔴'}
              </span>
              <span className="status-text">
                Server {serverAvailable ? 'Online' : 'Offline'}
              </span>
            </div>
          )}
        </div>
      </header>

      <main id="main-content" className="app-main" role="main">
        {/* Server connection error */}
        {serverAvailable === false && (
          <section className="server-error-section" role="alert" aria-live="polite">
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
          </section>
        )}

        {/* Application errors */}
        {errors.length > 0 && (
          <section className="error-section" role="alert" aria-live="polite">
            <div className="error-container">
              {errors.length > 1 && (
                <div className="error-header">
                  <h2 className="error-title">Multiple Errors ({errors.length})</h2>
                  <button 
                    className="dismiss-all-btn"
                    onClick={dismissAllErrors}
                    aria-label={`Dismiss all ${errors.length} errors`}
                  >
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
            </div>
          </section>
        )}

        {/* Application workflow */}
        <div className="app-workflow">
          {/* Step 1: File Upload */}
          <section className="workflow-step upload-step" aria-labelledby="upload-heading">
            <div className="step-header">
              <div className="step-number" aria-hidden="true">1</div>
              <h2 id="upload-heading" className="step-title">Upload File</h2>
            </div>
            <div className="step-content">
              <FileUpload 
                onFileUpload={handleFileUpload}
                isUploading={isUploading}
              />
            </div>
          </section>

          {/* Step 2: Processing Options */}
          {uploadedFile && (
            <section className="workflow-step options-step" aria-labelledby="options-heading">
              <div className="step-header">
                <div className="step-number" aria-hidden="true">2</div>
                <h2 id="options-heading" className="step-title">Select Options</h2>
              </div>
              <div className="step-content">
                <ProcessingOptions
                  options={processingOptions}
                  onOptionsChange={handleOptionsChange}
                  disabled={!serverAvailable}
                  isProcessing={isProcessing}
                />
              </div>
            </section>
          )}

          {/* Step 3: Process File */}
          {uploadedFile && selectedOptions.length > 0 && (
            <section className="workflow-step process-step" aria-labelledby="process-heading">
              <div className="step-header">
                <div className="step-number" aria-hidden="true">3</div>
                <h2 id="process-heading" className="step-title">Process File</h2>
              </div>
              <div className="step-content">
                <button
                  className={`process-btn ${isProcessing ? 'processing' : ''}`}
                  onClick={handleProcessFile}
                  disabled={!canProcess}
                  aria-describedby="process-description"
                >
                  {isProcessing ? (
                    <>
                      <div className="process-spinner" aria-hidden="true"></div>
                      <span>Processing...</span>
                    </>
                  ) : (
                    <>
                      <span className="process-icon" aria-hidden="true">⚡</span>
                      <span>Process File</span>
                    </>
                  )}
                </button>
                <p id="process-description" className="process-description">
                  Click to start processing your file with the selected classification options
                </p>
              </div>
            </section>
          )}

          {/* Step 4: Results */}
          {(isProcessing || results.length > 0) && (
            <section className="workflow-step results-step" aria-labelledby="results-heading">
              <div className="step-header">
                <div className="step-number" aria-hidden="true">4</div>
                <h2 id="results-heading" className="step-title">Download Results</h2>
              </div>
              <div className="step-content">
                {isProcessing && (
                  <div className="results-loading" role="status" aria-live="polite">
                    <div className="results-loading-spinner" aria-hidden="true"></div>
                    <div className="results-loading-text">Processing your file...</div>
                    <div className="results-loading-subtext">
                      This may take a few moments depending on file size
                    </div>
                  </div>
                )}

                {!isProcessing && results.length > 0 && (
                  <ResultsDisplay
                    results={results}
                    onDownload={handleDownload}
                  />
                )}
              </div>
            </section>
          )}
        </div>
      </main>

      <footer className="app-footer" role="contentinfo">
        <div className="footer-content">
          <p className="footer-text">
            Upload your JSON files and select processing options to get started
          </p>
          <div className="footer-info">
            <span className="app-version">v1.0.0</span>
            <span className="separator">•</span>
            <span className="tech-stack">React + Python</span>
          </div>
        </div>
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
