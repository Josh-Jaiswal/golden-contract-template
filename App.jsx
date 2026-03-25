import { useState, useEffect, useCallback } from "react";
import { Header } from "./components/Header";
import { UploadPanel } from "./components/UploadPanel";
import { JobsPanel } from "./components/JobsPanel";
import { JobsTable } from "./components/JobsTable";
import { Toast } from "./components/Toast";
import { useApi } from "./hooks/useApi";
import { useToast } from "./hooks/useToast";
import "./styles/globals.css";

export default function App() {
  const [config, setConfig] = useState({ apiKey: "", baseUrl: "localhost:8000" });
  const [contractType, setContractType] = useState("auto");
  const [jobs, setJobs] = useState([]);
  const [allJobs, setAllJobs] = useState([]);
  const { toast, showToast } = useToast();
  const { healthCheck, submitFile, pollJob, fetchAllJobs, deleteJob, downloadFile } = useApi(config);

  // Health polling
  const [apiStatus, setApiStatus] = useState("offline");
  useEffect(() => {
    const check = async () => {
      const ok = await healthCheck();
      setApiStatus(ok ? "online" : "offline");
    };
    check();
    const id = setInterval(check, 15000);
    return () => clearInterval(id);
  }, [config.baseUrl]);

  // Load all jobs when API key is set
  useEffect(() => {
    if (config.apiKey) loadAllJobs();
  }, [config.apiKey]);

  const loadAllJobs = useCallback(async () => {
    const data = await fetchAllJobs();
    if (data) setAllJobs(Array.isArray(data) ? data : Object.values(data));
  }, [fetchAllJobs]);

  const handleSubmit = useCallback(async (file) => {
    if (!config.apiKey) { showToast("Enter your API key first.", "error"); return; }
    const result = await submitFile(file, contractType);
    if (!result) { showToast("Submission failed. Check your API key and server.", "error"); return; }

    showToast(`Job started: ${result.job_id.slice(0, 8)}…`, "success");
    const newJob = {
      id: result.job_id,
      filename: file.name,
      status: "queued",
      progress: 15,
      created_at: new Date().toISOString(),
    };
    setJobs(prev => [newJob, ...prev]);

    // Begin polling
    const interval = setInterval(async () => {
      const updated = await pollJob(result.job_id);
      if (!updated) return;
      setJobs(prev => prev.map(j =>
        j.id === result.job_id
          ? { ...j, status: updated.status, progress: statusToProgress(updated.status), error: updated.error }
          : j
      ));
      if (updated.status === "complete") {
        showToast("Contract ready — download your PDFs!", "success");
        clearInterval(interval);
        loadAllJobs();
      }
      if (updated.status === "failed") {
        showToast("Processing failed. See job details.", "error");
        clearInterval(interval);
        loadAllJobs();
      }
    }, 3000);
  }, [config, contractType, submitFile, pollJob, showToast, loadAllJobs]);

  const handleDelete = useCallback(async (jobId) => {
    const ok = await deleteJob(jobId);
    if (ok) {
      showToast("Job deleted.", "success");
      setJobs(prev => prev.filter(j => j.id !== jobId));
      loadAllJobs();
    } else {
      showToast("Delete failed.", "error");
    }
  }, [deleteJob, showToast, loadAllJobs]);

  const handleDownload = useCallback(async (jobId, type) => {
    const ok = await downloadFile(jobId, type);
    if (!ok) showToast(`Download failed.`, "error");
  }, [downloadFile, showToast]);

  return (
    <div className="app">
      <Header apiStatus={apiStatus} />
      <main className="main-layout">
        <section className="hero">
          <div className="hero-content">
            <h1 className="hero-headline">
              Transform contracts<br />into <em>golden</em><br />standards.
            </h1>
            <p className="hero-sub">
              Multimodal AI pipeline — PDF, DOCX, EML, and Audio<br />
              processed into standardised NDA &amp; SOW documents.
            </p>
          </div>
          <div className="hero-badges">
            {["PDF", "DOCX", "EML", "MP3", "WAV", "M4A"].map(f => (
              <span key={f} className="badge">{f}</span>
            ))}
          </div>
        </section>

        <div className="workspace">
          <UploadPanel
            config={config}
            onConfigChange={setConfig}
            contractType={contractType}
            onContractTypeChange={setContractType}
            onSubmit={handleSubmit}
          />
          <JobsPanel
            jobs={jobs}
            onDownload={handleDownload}
            onDelete={handleDelete}
          />
        </div>

        <JobsTable
          jobs={allJobs}
          onRefresh={loadAllJobs}
          onDownload={handleDownload}
          onDelete={handleDelete}
        />
      </main>
      <Toast toast={toast} />
    </div>
  );
}

function statusToProgress(s) {
  return { queued: 15, processing: 60, complete: 100, failed: 100 }[s] ?? 0;
}
