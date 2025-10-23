import { useState, useEffect, useCallback } from 'react'
import FileUpload from '../components/FileUpload'
import ProcessingOptions from '../components/ProcessingOptions'
import ResultsDisplay from '../components/ResultsDisplay'
import ErrorDisplay from '../components/ErrorDisplay'
import ProgressIndicator from '../components/ProgressIndicator'
import { processFile, processMultipleFiles, downloadFile, downloadMultipleFiles, downloadMarkdownFile, getServerStatus } from '../services/api'
import { useErrorHandler } from '../utils/errorHandler'

import type { ProcessingOption, ProcessingResult, ErrorState, CategoryStatistics } from '../types/index'

function FileProcessorPage() {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [selectedOptions, setSelectedOptions] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [isUploading] = useState(false)
  const [results, setResults] = useState<ProcessingResult[]>([])
  const [errors, setErrors] = useState<ErrorState[]>([])
  const [serverAvailable, setServerAvailable] = useState<boolean | null>(null)
  const [serverError, setServerError] = useState<string | null>(null)
  const [processingProgress, setProcessingProgress] = useState<number>(0)
  const [processingMessage, setProcessingMessage] = useState<string>('')
  const [statistics, setStatistics] = useState<{
    original_questions: number
    original_answers: number
    result_questions: number
    result_answers: number
    duplicate_count: number
    removed_duplicate_answers: number
  } | null>(null)
  
  const [categoryStatistics, setCategoryStatistics] = useState<{
    total_items: number
    duplicate_items: number
    unique_items: number
    duplicate_percentage: number
    unique_percentage: number
  } | null>(null)

  const { handleError } = useErrorHandler()

  const processingOptions: ProcessingOption[] = [
    {
      id: 'category',
      label: 'Category Classification',
      description: 'Group questions by their category1 field',
      disabled: false // Re-enabled with new simple classification
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

    checkServer()

    const interval = setInterval(() => {
      if (!serverAvailable) {
        checkServer()
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [serverAvailable])

  const handleFileUpload = useCallback((files: File[]) => {
    setUploadedFiles(files)
    setErrors([])
    setResults([])
    setStatistics(null)
    setCategoryStatistics(null)
  }, [])

  const handleOptionsChange = useCallback((options: string[]) => {
    setSelectedOptions(options)
    setErrors(prev => prev.filter(error => error.code !== 'NO_OPTIONS_SELECTED'))
  }, [])

  const handleProcessFile = useCallback(async () => {
    if (uploadedFiles.length === 0 || selectedOptions.length === 0) {
      const errorState = handleError(
        {
          code: 'NO_OPTIONS_SELECTED',
          message: `Please upload ${uploadedFiles.length === 0 ? 'at least one file' : 'files'} and select at least one processing option`
        },
        'File Processing'
      )
      setErrors(prev => [...prev, errorState])
      return
    }

    setIsProcessing(true)
    setErrors([])
    setProcessingProgress(0)
    setProcessingMessage('Preparing file for processing...')

    try {
      // Separate classification options from format options
      const classificationOptions = selectedOptions.filter(opt =>
        ['category', 'institution', 'year'].includes(opt)
      )
      const formatOptions = selectedOptions.filter(opt =>
        ['json', 'markdown'].includes(opt)
      )

      const progressSteps = [
        { progress: 10, message: 'Uploading file to server...' },
        { progress: 30, message: 'Parsing JSON data...' },
        { progress: 50, message: `Processing ${classificationOptions.length} classification${classificationOptions.length > 1 ? 's' : ''}...` },
        { progress: 80, message: 'Generating output files...' },
        { progress: 95, message: 'Finalizing results...' }
      ]

      for (const step of progressSteps) {
        setProcessingProgress(step.progress)
        setProcessingMessage(step.message)
        await new Promise(resolve => setTimeout(resolve, 500))
      }

      // Process with classification options only
      const response = uploadedFiles.length === 1
        ? await processFile(uploadedFiles[0], classificationOptions)
        : await processMultipleFiles(uploadedFiles, classificationOptions)

      setProcessingProgress(100)
      setProcessingMessage('Processing complete!')

      if (response.success && response.results) {
        let processedResults: ProcessingResult[] = []

        // Handle JSON format results (only if JSON format is selected)
        if (formatOptions.includes('json')) {
          const jsonResults = response.results.map(result => ({
            id: result.download_id,
            type: result.type,
            filename: result.filename,
            data: null,
            sourceFilename: result.sourceFilename || undefined,
            selected: false
          }))
          processedResults.push(...jsonResults)
        }

        // Handle Markdown format results
        if (formatOptions.includes('markdown')) {
          // We need to get the processed data from the backend to convert to markdown
          // For now, create placeholder markdown results that will be converted on download
          const markdownResults = response.results.map(result => ({
            id: `${result.download_id}_md`,
            type: `${result.type}_markdown`,
            filename: result.filename.replace('.json', '.md'),
            data: null, // Will be converted on download
            sourceId: result.download_id, // Store reference to original JSON result
            sourceFilename: result.sourceFilename || undefined,
            selected: false
          }))
          processedResults.push(...markdownResults)
        }

        // If no format options are selected, default to JSON
        if (formatOptions.length === 0) {
          const jsonResults = response.results.map(result => ({
            id: result.download_id,
            type: result.type,
            filename: result.filename,
            data: null,
            sourceFilename: result.sourceFilename || undefined,
            selected: false
          }))
          processedResults.push(...jsonResults)
        }

        setResults(processedResults)

        // 통계 정보 설정
        if (response.statistics) {
          setStatistics(response.statistics)
        }
        
        // 카테고리 통계 정보 설정
        if (response.category_statistics) {
          setCategoryStatistics(response.category_statistics)
        }
      } else if (response.error) {
        const errorState = handleError(
          response.error,
          'File Processing',
          () => handleProcessFile()
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
        () => handleProcessFile()
      )
      setErrors(prev => [...prev, errorState])
    } finally {
      setIsProcessing(false)
      setProcessingProgress(0)
      setProcessingMessage('')
    }
  }, [uploadedFiles, selectedOptions, handleError])

  const handleSelectionChange = useCallback((resultId: string, selected: boolean) => {
    setResults(prev => prev.map(result =>
      result.id === resultId ? { ...result, selected } : result
    ))
  }, [])

  const handleBulkDownload = useCallback(async (selectedIds: string[]) => {
    if (selectedIds.length === 0) {
      const errorState = handleError(
        {
          code: 'NO_FILES_SELECTED',
          message: 'Please select at least one file to download'
        },
        'Bulk Download'
      )
      setErrors(prev => [...prev, errorState])
      return
    }

    try {
      const archiveName = uploadedFiles.length === 1
        ? `${uploadedFiles[0].name.replace('.json', '')}_processed.zip`
        : `processed_files_${new Date().toISOString().slice(0, 10)}.zip`

      await downloadMultipleFiles(selectedIds, archiveName)
    } catch (err) {
      const errorState = handleError(
        {
          code: 'BULK_DOWNLOAD_ERROR',
          message: err instanceof Error ? err.message : 'Bulk download failed',
          details: err instanceof Error ? err.message : 'Unknown bulk download error'
        },
        'Bulk Download',
        () => handleBulkDownload(selectedIds)
      )
      setErrors(prev => [...prev, errorState])
    }
  }, [uploadedFiles, handleError])

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
      // Handle markdown files - fetch JSON data and convert
      if (result.filename.endsWith('.md') && (result as any).sourceId) {
        const sourceId = (result as any).sourceId

        // Determine exclude columns based on result type
        let excludeColumns: string[] = []
        if (result.type.includes('year')) {
          excludeColumns = ['year'] // 연도별 분류에서는 year 컬럼 제외
        } else if (result.type.includes('institution')) {
          excludeColumns = ['institution'] // 기관별 분류에서는 institution 컬럼 제외
        }

        // Download markdown file from backend
        await downloadMarkdownFile(sourceId, result.filename, excludeColumns)
      } else if (result.data && result.filename.endsWith('.md')) {
        // Handle markdown files with local data
        const blob = new Blob([result.data], { type: 'text/markdown' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = result.filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      } else {
        // Handle JSON files from server
        await downloadFile(resultId, result.filename)
      }
    } catch (err) {
      const errorState = handleError(
        {
          code: 'DOWNLOAD_ERROR',
          message: err instanceof Error ? err.message : 'Download failed',
          details: err instanceof Error ? err.message : 'Unknown download error'
        },
        'File Download',
        () => handleDownload(resultId)
      )
      setErrors(prev => [...prev, errorState])
    }
  }, [results, handleError])

  const canProcess = uploadedFiles.length > 0 && selectedOptions.length > 0 && !isProcessing && serverAvailable

  const dismissError = useCallback((index: number) => {
    setErrors(prev => prev.filter((_, i) => i !== index))
  }, [])

  const dismissAllErrors = useCallback(() => {
    setErrors([])
  }, [])

  return (
    <main id="main-content" className="app-main" role="main">
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

      <div className="app-workflow">
        <section className="workflow-step upload-step" aria-labelledby="upload-heading">
          <div className="step-header">
            <div className="step-number" aria-hidden="true">1</div>
            <h2 id="upload-heading" className="step-title">Upload File</h2>
          </div>
          <div className="step-content">
            <FileUpload
              onFileUpload={handleFileUpload}
              isUploading={isUploading}
              multiple={true}
              maxFiles={10}
            />
          </div>
        </section>

        {uploadedFiles.length > 0 && (
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

        {uploadedFiles.length > 0 && selectedOptions.length > 0 && (
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
                Click to start processing your {uploadedFiles.length} file{uploadedFiles.length > 1 ? 's' : ''} with the selected classification options
              </p>
            </div>
          </section>
        )}

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
                  <div className="results-loading-text">Processing your {uploadedFiles.length} file{uploadedFiles.length > 1 ? 's' : ''}...</div>
                  <div className="results-loading-subtext">
                    This may take a few moments depending on file size{uploadedFiles.length > 1 ? 's' : ''}
                  </div>
                </div>
              )}

              {!isProcessing && results.length > 0 && (
                <>
                  {statistics && (
                    <div className="processing-statistics" role="region" aria-labelledby="stats-heading">
                      <h3 id="stats-heading" className="stats-title">처리 결과 통계</h3>
                      <div className="stats-grid">
                        <div className="stat-item">
                          <span className="stat-label">원본 선택지 수:</span>
                          <span className="stat-value">{statistics.original_answers.toLocaleString()}개</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-label">결과 선택지 수:</span>
                          <span className="stat-value">{statistics.result_answers.toLocaleString()}개</span>
                        </div>
                        <div className="stat-item highlight">
                          <span className="stat-label">제거된 동일 선택지 수:</span>
                          <span className="stat-value">{statistics.removed_duplicate_answers.toLocaleString()}개</span>
                        </div> 
                      </div>
                    </div>
                  )}
                  
                  {categoryStatistics && (
                    <div className="processing-statistics" role="region" aria-labelledby="category-stats-heading">
                      <h3 id="category-stats-heading" className="stats-title">Category 중복 제거 통계</h3>
                      <div className="stats-grid">
                        <div className="stat-item">
                          <span className="stat-label">중복제거 최종 선택지 수:</span>
                          <span className="stat-value">{categoryStatistics.unique_items.toLocaleString()}개 ({categoryStatistics.unique_percentage}%)</span>
                        </div>
                        <div className="stat-item highlight">
                          <span className="stat-label">제거된 중복 선택지 수:</span>
                          <span className="stat-value">{categoryStatistics.duplicate_items.toLocaleString()}개 ({categoryStatistics.duplicate_percentage}%)</span>
                        </div>
                      </div>
                    </div>
                  )}
                  <ResultsDisplay
                    results={results}
                    onDownload={handleDownload}
                    onBulkDownload={handleBulkDownload}
                    onSelectionChange={handleSelectionChange}
                  />
                </>
              )}
            </div>
          </section>
        )}
      </div>

      <ProgressIndicator
        isVisible={isProcessing}
        message={processingMessage}
        progress={processingProgress}
        subMessage={`Processing ${selectedOptions.length} classification type${selectedOptions.length > 1 ? 's' : ''}`}
      />
    </main>
  )
}

export default FileProcessorPage
