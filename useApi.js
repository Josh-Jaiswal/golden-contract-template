import { useCallback } from "react";

export function useApi({ apiKey, baseUrl }) {
  const base = `http://${baseUrl || "localhost:8000"}`;
  const headers = { "X-API-Key": apiKey };

  const healthCheck = useCallback(async () => {
    try {
      const res = await fetch(`${base}/health`);
      return res.ok;
    } catch { return false; }
  }, [base]);

  const submitFile = useCallback(async (file, contractType) => {
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("contract_type", contractType);
      const res = await fetch(`${base}/analyze`, {
        method: "POST",
        headers,
        body: form,
      });
      if (!res.ok) return null;
      return await res.json();
    } catch { return null; }
  }, [base, apiKey]);

  const pollJob = useCallback(async (jobId) => {
    try {
      const res = await fetch(`${base}/jobs/${jobId}`, { headers });
      if (!res.ok) return null;
      return await res.json();
    } catch { return null; }
  }, [base, apiKey]);

  const fetchAllJobs = useCallback(async () => {
    try {
      const res = await fetch(`${base}/jobs`, { headers });
      if (!res.ok) return null;
      return await res.json();
    } catch { return null; }
  }, [base, apiKey]);

  const deleteJob = useCallback(async (jobId) => {
    try {
      const res = await fetch(`${base}/jobs/${jobId}`, {
        method: "DELETE",
        headers,
      });
      return res.ok;
    } catch { return false; }
  }, [base, apiKey]);

  const downloadFile = useCallback(async (jobId, type) => {
    try {
      const res = await fetch(`${base}/download/${jobId}/${type}`, { headers });
      if (!res.ok) return false;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${type.toUpperCase()}-${jobId.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 5000);
      return true;
    } catch { return false; }
  }, [base, apiKey]);

  return { healthCheck, submitFile, pollJob, fetchAllJobs, deleteJob, downloadFile };
}
