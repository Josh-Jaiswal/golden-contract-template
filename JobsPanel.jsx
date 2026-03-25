import "./JobsPanel.css";

const STATUS_PROGRESS = { queued: 15, processing: 60, complete: 100, failed: 100 };

export function JobsPanel({ jobs, onDownload, onDelete }) {
  return (
    <div className="jobs-panel">
      <span className="section-label">Active Jobs</span>

      {jobs.length === 0 ? (
        <div className="jobs-empty">
          <EmptyIcon />
          <p className="jobs-empty-title">No active jobs</p>
          <p className="jobs-empty-hint">Upload a contract to start processing.</p>
        </div>
      ) : (
        <div className="jobs-list">
          {jobs.map(job => (
            <JobCard
              key={job.id}
              job={job}
              onDownload={onDownload}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function JobCard({ job, onDownload, onDelete }) {
  const progress = STATUS_PROGRESS[job.status] ?? 0;

  return (
    <div className={`job-card job-card--${job.status}`}>
      <div className="job-card-header">
        <div className={`job-icon job-icon--${job.status}`}>
          <StatusIcon status={job.status} />
        </div>
        <div className="job-card-info">
          <p className="job-filename">{job.filename}</p>
          <p className="job-id">{job.id?.slice(0, 12)}…</p>
        </div>
        <span className={`job-badge job-badge--${job.status}`}>
          {job.status}
        </span>
      </div>

      <div className="job-progress-track">
        <div
          className={`job-progress-fill job-progress-fill--${job.status}`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {job.status === "complete" && (
        <div className="job-downloads">
          <button className="dl-btn" onClick={() => onDownload(job.id, "nda")}>
            <DownloadIcon /> NDA PDF
          </button>
          <button className="dl-btn" onClick={() => onDownload(job.id, "sow")}>
            <DownloadIcon /> SOW PDF
          </button>
        </div>
      )}

      {job.status === "failed" && job.error && (
        <p className="job-error">{job.error}</p>
      )}
    </div>
  );
}

// ── Icons ──
function StatusIcon({ status }) {
  switch (status) {
    case "queued":
      return (
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
        </svg>
      );
    case "processing":
      return (
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="2" x2="12" y2="6" />
          <line x1="12" y1="18" x2="12" y2="22" />
          <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
          <line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
          <line x1="2" y1="12" x2="6" y2="12" />
          <line x1="18" y1="12" x2="22" y2="12" />
          <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
          <line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
        </svg>
      );
    case "complete":
      return (
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      );
    case "failed":
      return (
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      );
    default: return null;
  }
}

function DownloadIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

function EmptyIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}
