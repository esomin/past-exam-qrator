import { useState, useRef } from 'react'
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
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleConvert = () => {
    try {
      const parsedJson = JSON.parse(jsonInput)
      const markdown = json2md(parsedJson)
      setMarkdownOutput(markdown)
      setJsonError('')
      setIsPreviewMode(false)
    } catch (error) {
      setJsonError(error instanceof Error ? error.message : 'Invalid JSON')
      setMarkdownOutput('')
    }
  }

  const handleJsonInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setJsonInput(e.target.value)
    setJsonError('')
  }

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
                  title="Load Sample Data"
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
                  placeholder="Enter JSON array for json2md conversion..."
                  spellCheck={false}
                />
                <div className="json-editor-highlight">
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
                </div>
              ) : (
                <div className="markdown-raw">
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
