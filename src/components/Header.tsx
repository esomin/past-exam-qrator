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
          to="/page2"
          className={`nav-link ${location.pathname === '/page2' ? 'active' : ''}`}
        >
          JSON to Markdown
        </Link>
      </nav>
    </header>
  )
}

export default Header
