import "./Header.css";

export function Header({ apiStatus }) {
  return (
    <header className="header">
      <div className="header-logo">
        <div className="logo-mark">
          <span>CI</span>
        </div>
        <div className="logo-text">
          Contract <strong>Intelligence</strong>
        </div>
      </div>

      <nav className="header-nav">
        <a href="#workspace" className="nav-link">Upload</a>
        <a href="#all-jobs" className="nav-link">Jobs</a>
      </nav>

      <div className={`api-status api-status--${apiStatus}`}>
        <span className="status-dot" />
        <span className="status-text">
          {apiStatus === "online" ? "API Online" : "API Offline"}
        </span>
      </div>
    </header>
  );
}
