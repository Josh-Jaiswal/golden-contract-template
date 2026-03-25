import { useState, useRef, useCallback } from "react";
import "./UploadPanel.css";

const ACCEPTED = [".pdf", ".docx", ".doc", ".eml", ".mp3", ".wav", ".m4a"];
const CONTRACT_TYPES = [
  { value: "auto", label: "Auto Detect" },
  { value: "nda", label: "NDA" },
  { value: "sow", label: "SOW" },
];

function fmtSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function getFileIcon(filename) {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (["mp3", "wav", "m4a"].includes(ext)) return "audio";
  if (ext === "pdf") return "pdf";
  if (["docx", "doc"].includes(ext)) return "doc";
  if (ext === "eml") return "email";
  return "file";
}

export function UploadPanel({ config, onConfigChange, contractType, onContractTypeChange, onSubmit }) {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = useCallback((f) => {
    if (!f) return;
    const ext = "." + f.name.split(".").pop().toLowerCase();
    if (!ACCEPTED.includes(ext)) return;
    setFile(f);
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const handleSubmit = async () => {
    if (!file || submitting) return;
    setSubmitting(true);
    await onSubmit(file);
    setFile(null);
    setSubmitting(false);
  };

  return (
    <div className="upload-panel" id="workspace">
      {/* Config */}
      <div className="panel-section">
        <span className="section-label">Configuration</span>
        <div className="config-grid">
          <div className="field">
            <label className="field-label" htmlFor="api-key">API Key</label>
            <input
              id="api-key"
              className="field-input"
              type="password"
              placeholder="your_api_key_here"
              value={config.apiKey}
              onChange={e => onConfigChange(prev => ({ ...prev, apiKey: e.target.value }))}
            />
          </div>
          <div className="field">
            <label className="field-label" htmlFor="base-url">Server URL</label>
            <div className="url-row">
              <span className="url-prefix">http://</span>
              <input
                id="base-url"
                className="url-input"
                type="text"
                placeholder="localhost:8000"
                value={config.baseUrl}
                onChange={e => onConfigChange(prev => ({ ...prev, baseUrl: e.target.value }))}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Upload */}
      <div className="panel-section">
        <span className="section-label">Upload Contract</span>

        {!file ? (
          <div
            className={`drop-zone ${dragging ? "drop-zone--active" : ""}`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            <div className="drop-icon">
              <UploadIcon />
            </div>
            <p className="drop-title">Drop file or click to browse</p>
            <p className="drop-hint">PDF, Word, Email, or Audio recording</p>
            <div className="format-list">
              {ACCEPTED.map(f => (
                <span key={f} className="format-tag">{f.slice(1).toUpperCase()}</span>
              ))}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED.join(",")}
              style={{ display: "none" }}
              onChange={e => handleFile(e.target.files[0])}
            />
          </div>
        ) : (
          <div className="file-card">
            <div className={`file-type-icon file-type-icon--${getFileIcon(file.name)}`}>
              <FileTypeIcon type={getFileIcon(file.name)} />
            </div>
            <div className="file-details">
              <p className="file-name">{file.name}</p>
              <p className="file-size">{fmtSize(file.size)}</p>
            </div>
            <button className="file-remove" onClick={() => setFile(null)} title="Remove">
              <CloseIcon />
            </button>
          </div>
        )}
      </div>

      {/* Contract Type */}
      <div className="panel-section">
        <span className="section-label">Contract Type</span>
        <div className="type-selector">
          {CONTRACT_TYPES.map(t => (
            <button
              key={t.value}
              className={`type-btn ${contractType === t.value ? "type-btn--active" : ""}`}
              onClick={() => onContractTypeChange(t.value)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Submit */}
      <button
        className={`submit-btn ${submitting ? "submit-btn--loading" : ""}`}
        onClick={handleSubmit}
        disabled={!file || submitting}
      >
        {submitting ? (
          <>
            <span className="submit-spinner" />
            <span>Processing…</span>
          </>
        ) : (
          <>
            <span>Analyse Contract</span>
            <ArrowIcon />
          </>
        )}
      </button>
    </div>
  );
}

// ── Icons ──
function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}
function CloseIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: 16, height: 16 }}>
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  );
}
function FileTypeIcon({ type }) {
  if (type === "audio") return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18V5l12-2v13" /><circle cx="6" cy="18" r="3" /><circle cx="18" cy="16" r="3" />
    </svg>
  );
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  );
}
