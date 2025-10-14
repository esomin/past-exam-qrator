import { useState, useEffect } from 'react'
import FileUpload from './components/FileUpload'
import ProcessingOptions from './components/ProcessingOptions'
import ResultsDisplay from './components/ResultsDisplay'
import { processFile, downloadFile, checkServerHealth } from './services/api'
import type { ProcessingOption, ProcessingResult } from './types'
import './App.css'

function App() {
  // State management
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [selectedOptions, setSelectedOptions] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [isUploading] = useState(false)
  const [results, setResults] = useState<ProcessingResult[]>([])
  const [error, setError] = useState<string | null>(null)
  const [serverAvailable, setServerAvailable] = useState<boolean | null>(null)

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

  // Check server health on component mount
  useEffect(() => {
    const checkServer = async () => {
      const isAvailable = await checkServerHealth()
      setServerAvailable(isAvailable)
    }
    checkServer()
  }, [])

  // Handle file upload
  const handleFileUpload = (file: File) => {
    setUploadedFile(file)
    setError(null)
    setResults([]) // Clear previous results
  }

  // Handle processing options change
  const handleOptionsChange = (options: string[]) => {
    setSelectedOptions(options)
  }

  // Handle file processing
  const handleProcessFile = async () => {
    if (!uploadedFile || selectedOptions.length === 0) {
      setError('Please upload a file and select at least one processing option')
      return
    }

    setIsProcessing(true)
    setError(null)

    try {
      const response = await processFile(uploadedFile, selectedOptions)
      
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
        setError(response.error.message)
      }
    } catch (err) {
      setError('An unexpected error occurred during processing')
      console.error('Processing error:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  // Handle file download
  const handleDownload = async (resultId: string) => {
    const result = results.find(r => r.id === resultId)
    if (!result) {
      throw new Error('Result not found')
    }

    await downloadFile(resultId, result.filename)
  }

  // Determine if processing should be enabled
  const canProcess = uploadedFile && selectedOptions.length > 0 && !isProcessing && serverAvailable

  return (
    <div className="app">
      <header className="app-header">
        <h1>React File Processor</h1>
        <p>Upload JSON files and process them with multiple classification options</p>
      </header>

      <main className="app-main">
        {/* Server status indicator */}
        {serverAvailable === false && (
          <div className="server-error">
            <span className="error-icon">⚠️</span>
            Unable to connect to the processing server. Please ensure the Python backend is running.
          </div>
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

        {/* Error Display */}
        {error && (
          <section className="error-section">
            <div className="error-message">
              <span className="error-icon">❌</span>
              {error}
            </div>
          </section>
        )}

        {/* Results Display */}
        {results.length > 0 && (
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
    </div>
  )
}

export default App
