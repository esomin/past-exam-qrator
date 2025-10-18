import { useState, useCallback } from 'react'
import './JsonValidatorPage.css'

interface JsonError {
  line: number
  column: number
  message: string
  severity: 'error' | 'warning'
}

function JsonValidatorPage() {
  const [jsonInput, setJsonInput] = useState('')
  const [errors, setErrors] = useState<JsonError[]>([])
  const [isValid, setIsValid] = useState<boolean | null>(null)
  const [fullscreenSection, setFullscreenSection] = useState<'editor' | 'problems' | null>(null)

  const validateJson = useCallback((input: string) => {
    if (!input.trim()) {
      setErrors([])
      setIsValid(null)
      return
    }

    try {
      JSON.parse(input)
      setErrors([])
      setIsValid(true)
    } catch (error) {
      setIsValid(false)
      
      if (error instanceof SyntaxError) {
        const match = error.message.match(/position (\d+)/)
        const position = match ? parseInt(match[1]) : 0
        
        const lines = input.substring(0, position).split('\n')
        const line = lines.length
        const column = lines[lines.length - 1].length + 1
        
        let message = error.message
        if (message.includes('Unexpected token')) {
          message = 'Unexpected token'
        } else if (message.includes('Expected')) {
          message = 'Expected comma or closing bracket'
        }
        
        setErrors([{
          line,
          column,
          message,
          severity: 'error'
        }])
      }
    }
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setJsonInput(value)
    validateJson(value)
  }

  const handleClear = () => {
    setJsonInput('')
    setErrors([])
    setIsValid(null)
  }

  const handleFormat = () => {
    if (isValid && jsonInput) {
      try {
        const formatted = JSON.stringify(JSON.parse(jsonInput), null, 2)
        setJsonInput(formatted)
      } catch (e) {
        // Already validated, shouldn't happen
      }
    }
  }

  const toggleFullscreen = (section: 'editor' | 'problems') => {
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
    <main className="json-validator-page" role="main">
      <div className="page-content">
        <div className={`validator-content ${fullscreenSection ? 'has-fullscreen' : ''}`}>
          <div className={`editor-section ${fullscreenSection === 'editor' ? 'fullscreen' : ''}`}>
            <div className="editor-header">
              <div className="editor-title">
                <span className="file-icon">📄</span>
                <span>JSON Editor</span>
              </div>
              <div className="editor-actions">
                <button 
                  className="action-btn format-btn"
                  onClick={handleFormat}
                  disabled={!isValid}
                  title="Format JSON"
                >
                  Format
                </button>
                <button 
                  className="action-btn clear-btn"
                  onClick={handleClear}
                  disabled={!jsonInput}
                  title="Clear"
                >
                  Clear
                </button>
                <button 
                  className="fullscreen-btn" 
                  onClick={() => toggleFullscreen('editor')}
                  title={fullscreenSection === 'editor' ? "Exit Fullscreen" : "Fullscreen"}
                >
                  {fullscreenSection === 'editor' ? '✕' : '⛶'}
                </button>
              </div>
            </div>
            
            <div className="editor-wrapper">
              <div className="line-numbers">
                {jsonInput.split('\n').map((_, index) => (
                  <div key={index} className="line-number">
                    {index + 1}
                  </div>
                ))}
              </div>
              <textarea
                className={`json-editor ${isValid === false ? 'has-error' : ''}`}
                value={jsonInput}
                onChange={handleInputChange}
                placeholder='Enter JSON here...\n\nExample:\n{\n  "name": "John",\n  "age": 30\n}'
                spellCheck={false}
              />
            </div>

            {isValid !== null && (
              <div className={`validation-status ${isValid ? 'valid' : 'invalid'}`}>
                <span className="status-icon">
                  {isValid ? '✓' : '✗'}
                </span>
                <span className="status-text">
                  {isValid ? 'Valid JSON' : 'Invalid JSON'}
                </span>
              </div>
            )}
          </div>

          <div className={`problems-section ${fullscreenSection === 'problems' ? 'fullscreen' : ''}`}>
            <div className="problems-header">
              <div className="problems-title">
                <span className="problems-icon">⚠️</span>
                <h2>Problems</h2>
                <span className="problems-count">{errors.length}</span>
              </div>
              <button 
                className="fullscreen-btn" 
                onClick={() => toggleFullscreen('problems')}
                title={fullscreenSection === 'problems' ? "Exit Fullscreen" : "Fullscreen"}
              >
                {fullscreenSection === 'problems' ? '✕' : '⛶'}
              </button>
            </div>

            <div className="problems-list">
              {errors.length === 0 ? (
                <div className="no-problems">
                  <span className="no-problems-icon">✓</span>
                  <p>No problems detected</p>
                </div>
              ) : (
                errors.map((error, index) => (
                  <div key={index} className={`problem-item ${error.severity}`}>
                    <div className="problem-icon">
                      {error.severity === 'error' ? '❌' : '⚠️'}
                    </div>
                    <div className="problem-details">
                      <div className="problem-message">{error.message}</div>
                      <div className="problem-location">
                        <span className="location-label">json</span>
                        <span className="location-separator">({error.severity})</span>
                        <span className="location-position">
                          [Ln {error.line}, Col {error.column}]
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {fullscreenSection && (
        <div className="fullscreen-overlay" onClick={closeFullscreen} />
      )}
    </main>
  )
}

export default JsonValidatorPage
