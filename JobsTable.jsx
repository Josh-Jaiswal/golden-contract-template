import "./JobsTable.css";

function fmtDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" });
  } catch { return iso; }
}

export function JobsTable({ jobs, onRefresh, onDownload, onDelete }) {
  return (
    <section className="jobs-table-section" id="all-jobs">
      <div className="jobs-table-header">
        <div>
          <h2 className="jobs-table-title">Job History</h2>
          <p className="jobs-table-subtitle">All submitted contracts and their status</p>
        </div>
        <button className="refresh-btn" onClick={onRefresh}>
          <RefreshIcon />
          Refresh
        </button>
      </div>

      <div className="table-wrapper">
        <table className="jobs-table">
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {!jobs || jobs.length === 0 ? (
              <tr>
                <td colSpan={4} className="table-empty">
                  No jobs found — submit a contract above to begin.
                </td>
              </tr>
            ) : (
              [...jobs].reverse().map(job => {
                const id = job.job_id || job.id || "—";
                const status = job.status || "—";
                return (
                  <tr key={id}>
                    <td>
                      <span className="td-id">{id}</span>
                    </td>
                    <td>
                      <span className={`td-badge td-badge--${status}`}>{status}</span>
                    </td>
                    <td className="td-date">{fmtDate(job.created_at || job.created)}</td>
                    <td>
                      <div className="td-actions">
                        {status === "complete" && (
                          <>
                            <button className="td-btn td-btn--dl" onClick={() => onDownload(id, "nda")}>
                              NDA
                            </button>
                            <button className="td-btn td-btn--dl" onClick={() => onDownload(id, "sow")}>
                              SOW
                            </button>
                          </>
                        )}
                        <button className="td-btn td-btn--del" onClick={() => onDelete(id)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function RefreshIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10" />
      <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
    </svg>
  );
}
