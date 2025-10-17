import { useState } from 'react'
import json2md from 'json2md'
import './Page2.css'

// 더미 데이터
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

function Page2() {
  const [markdownOutput, setMarkdownOutput] = useState('')

  const handleConvert = () => {
    const markdown = json2md(dummyData)
    setMarkdownOutput(markdown)
  }

  return (
    <main className="page2-container" role="main">
      <div className="page2-content">
        <div className="converter-section">
          <div className="input-section">
            <h2>JSON Input</h2>
            <div className="json-display">
              <pre>{JSON.stringify(dummyData, null, 2)}</pre>
            </div>
            <button className="convert-btn" onClick={handleConvert}>
              <span className="convert-icon">🔄</span>
              Convert to Markdown
            </button>
          </div>

          <div className="output-section">
            <h2>Markdown Output</h2>
            {markdownOutput ? (
              <div className="markdown-display">
                <pre>{markdownOutput}</pre>
              </div>
            ) : (
              <div className="empty-state">
                <span className="empty-icon">📝</span>
                <p>Click "Convert to Markdown" to see the result</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}

export default Page2
