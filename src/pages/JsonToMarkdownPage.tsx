import { useState, useRef, useMemo, useCallback, useEffect } from 'react'
import json2md from 'json2md'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import './JsonToMarkdownPage.css'

const dummyData = [
  { h1: 'Project Documentation' },
  { p: 'This is a sample project documentation generated from JSON data.' },
  { h2: 'Features' },
  {
    ul: [
      'Easy to use JSON to Markdown converter',
      'Real-time conversion',
      'Clean and simple interface',
      'Support for various markdown elements'
    ]
  },
  { h2: 'Installation' },
  { code: { language: 'bash', content: 'npm install json2md' } },
  { h2: 'Usage Example' },
  {
    p: 'Here is a simple example of how to use this converter:'
  },
  {
    code: {
      language: 'javascript',
      content: `const json2md = require('json2md');
const result = json2md([
  { h1: 'Title' },
  { p: 'Paragraph' }
]);`
    }
  },
  { h2: 'Table Example' },
  {
    table: {
      headers: ['Feature', 'Status', 'Priority'],
      rows: [
        ['JSON Input', 'Complete', 'High'],
        ['MD Output', 'Complete', 'High'],
        ['Live Preview', 'Complete', 'Medium']
      ]
    }
  },
  { h2: 'Conclusion' },
  { p: 'This tool makes it easy to convert JSON data into readable Markdown format.' }
]

function JsonToMarkdownPage() {
  const [jsonInput, setJsonInput] = useState(JSON.stringify(dummyData, null, 2))
  const [markdownOutput, setMarkdownOutput] = useState('')
  const [isPreviewMode, setIsPreviewMode] = useState(false)
  const [fullscreenSection, setFullscreenSection] = useState<'input' | 'output' | null>(null)
  const [jsonError, setJsonError] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [shouldHighlight, setShouldHighlight] = useState(true)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const processingTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // 복사-붙여넣기 감지 및 최적화
  useEffect(() => {
    // 대용량 텍스트 감지
    const isLargeText = jsonInput.length > 5000
    
    if (isLargeText) {
      // 대용량 텍스트의 경우 syntax highlighting 비활성화
      setShouldHighlight(false)
      setIsProcessing(true)
      
      // 처리 완료 표시를 위한 짧은 지연
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current)
      }
      
      processingTimeoutRef.current = setTimeout(() => {
        setIsProcessing(false)
      }, 300)
    } else {
      // 소용량 텍스트는 즉시 syntax highlighting 활성화
      setShouldHighlight(true)
      setIsProcessing(false)
    }

    return () => {
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current)
      }
    }
  }, [jsonInput])



  const handleConvert = () => {
    try {
      const parsedJson = JSON.parse(jsonInput)
      const markdown = json2md(parsedJson)
      setMarkdownOutput(markdown)
      setJsonError('')
      setIsPreviewMode(false)
    } catch (error) {
      setJsonError(error instanceof Error ? error.message : 'Invalid JSON or unsupported json2md format')
      setMarkdownOutput('')
    }
  }

  const handleJsonInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    const isLargeChange = Math.abs(newValue.length - jsonInput.length) > 1000
    
    setJsonInput(newValue)
    setJsonError('')
    
    // 대용량 복사-붙여넣기 감지
    if (isLargeChange && newValue.length > 5000) {
      setIsProcessing(true)
      setShouldHighlight(false)
    }
  }, [jsonInput.length])

  // 복사-붙여넣기 이벤트 직접 처리
  const handlePaste = useCallback((e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const pastedText = e.clipboardData.getData('text')
    
    if (pastedText.length > 5000) {
      // 대용량 붙여넣기 최적화
      setIsProcessing(true)
      setShouldHighlight(false)
      
      // 즉시 처리 완료 표시
      setTimeout(() => {
        setIsProcessing(false)
      }, 200)
    }
  }, [])

  // 복사-붙여넣기 최적화된 JSON 하이라이팅
  const jsonHighlightElement = useMemo(() => {
    // 처리 중이거나 syntax highlighting이 비활성화된 경우
    if (isProcessing) {
      return (
        <div style={{
          margin: 0,
          padding: '1rem',
          background: 'transparent',
          fontSize: '14px',
          lineHeight: '1.5',
          fontFamily: "'Monaco', 'Menlo', 'Ubuntu Mono', monospace",
          minHeight: '300px',
          maxHeight: '600px',
          overflow: 'hidden',
          pointerEvents: 'none',
          color: '#6b7280',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: '1rem'
        }}>
          <div style={{ 
            width: '32px', 
            height: '32px', 
            border: '3px solid #374151',
            borderTop: '3px solid #6366f1',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          <span>Processing large JSON...</span>
        </div>
      )
    }

    if (!shouldHighlight || jsonInput.length > 5000) {
      return (
        <pre style={{
          margin: 0,
          padding: '1rem',
          background: 'transparent',
          fontSize: '14px',
          lineHeight: '1.5',
          fontFamily: "'Monaco', 'Menlo', 'Ubuntu Mono', monospace",
          minHeight: '300px',
          maxHeight: '600px',
          overflow: 'hidden',
          pointerEvents: 'none',
          color: '#f9fafb',
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word'
        }}>
          {jsonInput || ' '}
        </pre>
      )
    }
    
    return (
      <SyntaxHighlighter
        language="json"
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          padding: '1rem',
          background: 'transparent',
          fontSize: '14px',
          lineHeight: '1.5',
          fontFamily: "'Monaco', 'Menlo', 'Ubuntu Mono', monospace",
          minHeight: '300px',
          maxHeight: '600px',
          overflow: 'hidden',
          pointerEvents: 'none'
        }}
        showLineNumbers={false}
        wrapLines={true}
      >
        {jsonInput || ' '}
      </SyntaxHighlighter>
    )
  }, [jsonInput, shouldHighlight, isProcessing])

  // Memoized markdown preview
  const markdownPreviewElement = useMemo(() => {
    // 대용량 마크다운의 경우 간단한 렌더링
    if (markdownOutput.length > 50000) {
      return (
        <div style={{ 
          padding: '1rem',
          color: '#d1d5db',
          fontSize: '14px',
          lineHeight: '1.6',
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word'
        }}>
          <p style={{ color: '#fbbf24', marginBottom: '1rem' }}>
            ⚠️ Large content detected. Showing simplified preview for better performance.
          </p>
          {markdownOutput.substring(0, 5000)}
          {markdownOutput.length > 5000 && (
            <p style={{ color: '#9ca3af', fontStyle: 'italic', marginTop: '1rem' }}>
              ... and {markdownOutput.length - 5000} more characters
            </p>
          )}
        </div>
      )
    }
    
    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '')
            const inline = props.inline
            return !inline && match ? (
              <SyntaxHighlighter
                style={vscDarkPlus}
                language={match[1]}
                PreTag="div"
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={className}>
                {children}
              </code>
            )
          }
        }}
      >
        {markdownOutput}
      </ReactMarkdown>
    )
  }, [markdownOutput])

  // Memoized markdown raw display
  const markdownRawElement = useMemo(() => {
    // 대용량 마크다운의 경우 syntax highlighting 비활성화
    if (markdownOutput.length > 10000) {
      return (
        <pre style={{
          margin: 0,
          borderRadius: '4px',
          fontSize: '14px',
          color: '#f9fafb',
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
          padding: '1rem'
        }}>
          {markdownOutput}
        </pre>
      )
    }
    
    return (
      <SyntaxHighlighter
        language="markdown"
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          borderRadius: '4px',
          fontSize: '14px'
        }}
      >
        {markdownOutput}
      </SyntaxHighlighter>
    )
  }, [markdownOutput])

  const handleLoadSample = () => {
    setJsonInput(JSON.stringify(dummyData, null, 2))
    setJsonError('')
  }



  const togglePreview = () => {
    setIsPreviewMode(!isPreviewMode)
  }

  const toggleFullscreen = (section: 'input' | 'output') => {
    if (fullscreenSection === section) {
      setFullscreenSection(null)
    } else {
      setFullscreenSection(section)
    }
  }

  const closeFullscreen = () => {
    setFullscreenSection(null)
  }



  // Input upload functionality
  const handleFileUpload = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result as string
        setJsonInput(content)
        setJsonError('')
      }
      reader.readAsText(file)
    }
  }

  // Output copy functionality
  const handleCopyOutput = async () => {
    if (!markdownOutput) return

    try {
      await navigator.clipboard.writeText(markdownOutput)
      // Show temporary success feedback
      const button = document.querySelector('.copy-btn') as HTMLButtonElement
      if (button) {
        const originalText = button.innerHTML
        button.innerHTML = '✅ Copied!'
        button.disabled = true
        setTimeout(() => {
          button.innerHTML = originalText
          button.disabled = false
        }, 2000)
      }
    } catch (error) {
      console.error('Failed to copy to clipboard:', error)
    }
  }

  // Output download functionality
  const handleDownloadOutput = () => {
    if (!markdownOutput) return

    const blob = new Blob([markdownOutput], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'converted-markdown.md'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <main className="json-to-markdown-page" role="main">
      <div className="page-content">
        <div className={`converter-section ${fullscreenSection ? 'has-fullscreen' : ''}`}>
          <div className={`input-section ${fullscreenSection === 'input' ? 'fullscreen' : ''}`}>
            <div className="section-header">
              <h2>JSON Input</h2>
              <div className="header-actions">
                <button
                  className="action-btn upload-btn"
                  onClick={handleFileUpload}
                  title="Upload JSON File"
                >
                  <span className="btn-icon">📁</span>
                  <span className="btn-text">Upload</span>
                </button>
                <button
                  className="action-btn sample-btn"
                  onClick={handleLoadSample}
                  title="Load json2md Sample Data"
                >
                  <span className="btn-icon">📄</span>
                  <span className="btn-text">Sample</span>
                </button>
                <button
                  className="fullscreen-btn"
                  onClick={() => toggleFullscreen('input')}
                  title={fullscreenSection === 'input' ? "Exit Fullscreen" : "Fullscreen"}
                >
                  {fullscreenSection === 'input' ? '✕' : '⛶'}
                </button>
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.txt"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />

            <div className="json-input-wrapper">
              <div className={`json-editor-container ${jsonError ? 'has-error' : ''}`}>
                <textarea
                  className="json-editor-textarea"
                  value={jsonInput}
                  onChange={handleJsonInputChange}
                  onPaste={handlePaste}
                  placeholder="Enter json2md format JSON data..."
                  spellCheck={false}
                />
                <div className="json-editor-highlight">
                  {jsonHighlightElement}
                </div>
              </div>
              {jsonError && (
                <div className="json-error">
                  <span className="error-icon">❌</span>
                  <span className="error-message">{jsonError}</span>
                </div>
              )}
            </div>

            {fullscreenSection !== 'input' && (
              <button
                className="convert-btn"
                onClick={handleConvert}
                disabled={!jsonInput.trim()}
              >
                <span className="convert-icon">🔄</span>
                Convert to Markdown
              </button>
            )}
          </div>

          <div className={`output-section ${fullscreenSection === 'output' ? 'fullscreen' : ''}`}>
            <div className="output-header">
              <h2>Markdown Output</h2>
              <div className="header-actions">
                {markdownOutput && (
                  <>
                    <button
                      className="action-btn copy-btn"
                      onClick={handleCopyOutput}
                      title="Copy to Clipboard"
                    >
                      <span className="btn-icon">📋</span>
                      <span className="btn-text">Copy</span>
                    </button>
                    <button
                      className="action-btn download-btn"
                      onClick={handleDownloadOutput}
                      title="Download as .md file"
                    >
                      <span className="btn-icon">💾</span>
                      <span className="btn-text">Download</span>
                    </button>
                    <button
                      className="preview-toggle-btn"
                      onClick={togglePreview}
                      title={isPreviewMode ? "Show Raw Markdown" : "Show Preview"}
                    >
                      {isPreviewMode ? '📄' : '🔍'}
                    </button>
                  </>
                )}
                <button
                  className="fullscreen-btn"
                  onClick={() => toggleFullscreen('output')}
                  title={fullscreenSection === 'output' ? "Exit Fullscreen" : "Fullscreen"}
                  disabled={!markdownOutput}
                >
                  {fullscreenSection === 'output' ? '✕' : '⛶'}
                </button>
              </div>
            </div>
            {markdownOutput ? (
              isPreviewMode ? (
                <div className="markdown-preview">
                  {markdownPreviewElement}
                </div>
              ) : (
                <div className="markdown-raw">
                  {markdownRawElement}
                </div>
              )
            ) : (
              <div className="empty-state">
                <span className="empty-icon">📝</span>
                <p>Click "Convert to Markdown" to see the result</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {fullscreenSection && (
        <div className="fullscreen-overlay" onClick={closeFullscreen} />
      )}
    </main>
  )
}

export default JsonToMarkdownPage
