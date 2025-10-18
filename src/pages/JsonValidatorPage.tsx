import { useState, useCallback, useRef } from 'react'
import Ajv from 'ajv'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import './JsonValidatorPage.css'

interface JsonError {
  line: number
  column: number
  message: string
  severity: 'error' | 'warning'
  type?: 'syntax' | 'schema'
}

interface SchemaValidationError {
  instancePath: string
  schemaPath: string
  keyword: string
  params: any
  message?: string
}

function JsonValidatorPage() {
  const [jsonInput, setJsonInput] = useState('')
  const [schemaInput, setSchemaInput] = useState('')
  const [errors, setErrors] = useState<JsonError[]>([])
  const [isValid, setIsValid] = useState<boolean | null>(null)
  const [fullscreenSection, setFullscreenSection] = useState<'editor' | 'schema' | 'problems' | null>(null)
  const [showSchema, setShowSchema] = useState(false)
  const [parsedJson, setParsedJson] = useState<any>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const validateJson = useCallback((input: string, schema?: string) => {
    if (!input.trim()) {
      setErrors([])
      setIsValid(null)
      setParsedJson(null)
      return
    }

    const newErrors: JsonError[] = []
    let parsed: any = null

    // First, validate JSON syntax
    try {
      parsed = JSON.parse(input)
      setParsedJson(parsed)
    } catch (error) {
      setIsValid(false)
      setParsedJson(null)
      
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
        
        newErrors.push({
          line,
          column,
          message,
          severity: 'error',
          type: 'syntax'
        })
      }
      setErrors(newErrors)
      return
    }

    // If JSON is valid and schema is provided, validate against schema
    if (parsed && schema && schema.trim()) {
      try {
        const parsedSchema = JSON.parse(schema)
        const ajv = new Ajv({ allErrors: true })
        const validate = ajv.compile(parsedSchema)
        const valid = validate(parsed)
        
        if (!valid && validate.errors) {
          validate.errors.forEach((error: SchemaValidationError) => {
            newErrors.push({
              line: 1, // Schema errors don't have specific line numbers
              column: 1,
              message: `${error.instancePath || 'root'}: ${error.message}`,
              severity: 'error',
              type: 'schema'
            })
          })
        }
      } catch (schemaError) {
        newErrors.push({
          line: 1,
          column: 1,
          message: 'Invalid JSON schema',
          severity: 'error',
          type: 'schema'
        })
      }
    }

    setErrors(newErrors)
    setIsValid(newErrors.length === 0)
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setJsonInput(value)
    validateJson(value, schemaInput)
  }

  const handleSchemaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setSchemaInput(value)
    validateJson(jsonInput, value)
  }

  const handleClear = () => {
    setJsonInput('')
    setSchemaInput('')
    setErrors([])
    setIsValid(null)
    setParsedJson(null)
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

  const toggleFullscreen = (section: 'editor' | 'schema' | 'problems') => {
    if (fullscreenSection === section) {
      setFullscreenSection(null)
    } else {
      setFullscreenSection(section)
    }
  }

  const closeFullscreen = () => {
    setFullscreenSection(null)
  }

  const jumpToLine = (line: number, column: number) => {
    if (!textareaRef.current) return
    
    const textarea = textareaRef.current
    const lines = textarea.value.split('\n')
    
    // Calculate the position in the text
    let position = 0
    for (let i = 0; i < line - 1 && i < lines.length; i++) {
      position += lines[i].length + 1 // +1 for newline character
    }
    position += Math.min(column - 1, lines[line - 1]?.length || 0)
    
    // Focus the textarea and set cursor position
    textarea.focus()
    textarea.setSelectionRange(position, position)
    
    // Scroll to the line
    const lineHeight = 22.4 // matches CSS line-height
    const scrollTop = Math.max(0, (line - 1) * lineHeight - textarea.clientHeight / 2)
    textarea.scrollTop = scrollTop
  }



  return (
    <main className="json-validator-page dark-mode" role="main">
      <div className="page-content">
        <div className={`validator-content ${fullscreenSection ? 'has-fullscreen' : ''}`}>
          {/* Editor section - 80% height */}
          <div className={`editor-section ${fullscreenSection === 'editor' ? 'fullscreen' : ''}`}>
            <div className="editor-header">
              <div className="editor-title">
                <span className="file-icon">📄</span>
                <span>JSON Editor</span>
              </div>
              <div className="editor-actions">
                <button 
                  className="action-btn schema-btn"
                  onClick={() => setShowSchema(!showSchema)}
                  title="Toggle Schema Validation"
                >
                  {showSchema ? 'Hide Schema' : 'Add Schema'}
                </button>
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
            
            <div className="editor-content">
              <div className="editor-main-layout">
                {/* Left side - JSON Editor (50%) */}
                <div className="editor-left-panel">
                  <div className="editor-wrapper">
                    <div className="line-numbers">
                      {jsonInput.split('\n').map((_, index) => (
                        <div key={index} className="line-number">
                          {index + 1}
                        </div>
                      ))}
                    </div>
                    <textarea
                      ref={textareaRef}
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
                      {schemaInput && (
                        <span className="schema-status">
                          {errors.some(e => e.type === 'schema') ? '(Schema validation failed)' : '(Schema validation passed)'}
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Right side - Formatted JSON (50%) */}
                <div className="editor-right-panel">
                  <div className="formatted-json-header">
                    <h3>Formatted JSON:</h3>
                  </div>
                  <div className="formatted-json-content">
                    {parsedJson ? (
                      <SyntaxHighlighter
                        language="json"
                        style={vscDarkPlus}
                        customStyle={{
                          margin: 0,
                          borderRadius: '4px',
                          fontSize: '14px',
                          height: '100%',
                          overflow: 'auto'
                        }}
                      >
                        {JSON.stringify(parsedJson, null, 2)}
                      </SyntaxHighlighter>
                    ) : (
                      <div className="formatted-json-placeholder">
                        <p>Enter valid JSON to see formatted output</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {showSchema && (
                <div className="schema-wrapper">
                  <div className="schema-header">
                    <div className="schema-title">
                      <span className="file-icon">🔧</span>
                      <span>JSON Schema</span>
                    </div>
                    <button 
                      className="fullscreen-btn" 
                      onClick={() => toggleFullscreen('schema')}
                      title={fullscreenSection === 'schema' ? "Exit Fullscreen" : "Fullscreen"}
                    >
                      {fullscreenSection === 'schema' ? '✕' : '⛶'}
                    </button>
                  </div>
                  
                  <textarea
                    className="schema-editor"
                    value={schemaInput}
                    onChange={handleSchemaChange}
                    placeholder={`Enter JSON Schema here...\n\nExample:\n{\n  "type": "object",\n  "properties": {\n    "name": { "type": "string" },\n    "age": { "type": "number" }\n  },\n  "required": ["name"]\n}`}
                    spellCheck={false}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Problems section - 20% height at bottom */}
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
                  <div 
                    key={index} 
                    className={`problem-item ${error.severity} ${error.type || 'syntax'} clickable`}
                    onClick={() => error.type !== 'schema' && jumpToLine(error.line, error.column)}
                    title={error.type !== 'schema' ? 'Click to jump to line' : 'Schema validation error'}
                  >
                    <div className="problem-icon">
                      {error.severity === 'error' ? '❌' : '⚠️'}
                    </div>
                    <div className="problem-details">
                      <div className="problem-message">{error.message}</div>
                      <div className="problem-location">
                        <span className="location-label">{error.type === 'schema' ? 'schema' : 'json'}</span>
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
