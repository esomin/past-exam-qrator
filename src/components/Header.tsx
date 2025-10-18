import { Link, useLocation } from 'react-router-dom'
import './Header.css'

function Header() {
  const location = useLocation()

  return (
    <header className="app-header" role="banner">
      <nav className="header-nav" role="navigation">
        <Link
          to="/"
          className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
        >
          File Processor
        </Link>
        <Link
          to="/json-validator"
          className={`nav-link ${location.pathname === '/json-validator' ? 'active' : ''}`}
        >
          JSON Validator
        </Link>
        <Link
          to="/json-to-markdown"
          className={`nav-link ${location.pathname === '/json-to-markdown' ? 'active' : ''}`}
        >
          JSON to Markdown
        </Link>
      </nav>
    </header>
  )
}

export default Header
