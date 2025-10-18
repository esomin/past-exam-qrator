import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import FileProcessorPage from './pages/FileProcessorPage'
import JsonValidatorPage from './pages/JsonValidatorPage'
import JsonToMarkdownPage from './pages/JsonToMarkdownPage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app" role="main">
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>

        <Header />

        <Routes>
          <Route path="/" element={<FileProcessorPage />} />
          <Route path="/json-validator" element={<JsonValidatorPage />} />
          <Route path="/json-to-markdown" element={<JsonToMarkdownPage />} />
        </Routes>

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
      </div>
    </Router>
  )
}

export default App
