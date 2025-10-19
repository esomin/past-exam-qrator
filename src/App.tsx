import FileProcessorPage from './pages/FileProcessorPage'
import './App.css'

function App() {
  return (
    <div className="app" role="main">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <FileProcessorPage />

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
  )
}

export default App
