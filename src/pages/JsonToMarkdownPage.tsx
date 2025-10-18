import { useState } from 'react'
import json2md from 'json2md'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
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
  const [markdownOutput, setMarkdownOutput] = useState('')
  const [isPreviewMode, setIsPreviewMode] = useState(false)
  const [fullscreenSection, setFullscreenSection] = useState<'input' | 'output' | null>(null)

  const handleConvert = () => {
    const markdown = json2md(dummyData)
    setMarkdownOutput(markdown)
    setIsPreviewMode(false)
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

  return (
    <main className="json-to-markdown-page" role="main">
      <div className="page-content">
        <div className={`converter-section ${fullscreenSection ? 'has-fullscreen' : ''}`}>
          <div className={`input-section ${fullscreenSection === 'input' ? 'fullscreen' : ''}`}>
            <div className="section-header">
              <h2>JSON Input</h2>
              <button 
                className="fullscreen-btn" 
                onClick={() => toggleFullscreen('input')}
                title={fullscreenSection === 'input' ? "Exit Fullscreen" : "Fullscreen"}
              >
                {fullscreenSection === 'input' ? '✕' : '⛶'}
              </button>
            </div>
            <div className="json-display">
              <pre>{JSON.stringify(dummyData, null, 2)}</pre>
            </div>
            {fullscreenSection !== 'input' && (
              <button className="convert-btn" onClick={handleConvert}>
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
                  <button 
                    className="preview-toggle-btn" 
                    onClick={togglePreview}
                    title={isPreviewMode ? "Show Raw Markdown" : "Show Preview"}
                  >
                    {isPreviewMode ? '📄' : '🔍'}
                  </button>
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
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {markdownOutput}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="markdown-raw">
                  <pre>{markdownOutput}</pre>
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
