import streamlit as st
import requests
import time
import json
import base64
from datetime import datetime

API_URL = "http://localhost:8000"
API_KEY = "GoldenEY1479"

st.set_page_config(layout="wide", page_title="EY Contract Intelligence")

# ============================================================
# 🎨 DESIGN SYSTEM
# ============================================================
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #0b0b0b;
    color: #f5f5f5;
}

/* Top Nav */
.topbar {
    padding: 1.2rem 2rem;
    border-bottom: 2px solid #FFE600;
}

/* Cards */
.card {
    background: #141414;
    padding: 1.5rem;
    border-radius: 10px;
    border: 1px solid #2a2a2a;
    margin-bottom: 1.2rem;
}

/* Inputs */
input, select, textarea {
    background: #111 !important;
    color: white !important;
    border-radius: 8px !important;
    border: 1px solid #333 !important;
}

/* Buttons */
button[kind="primary"] {
    background: #FFE600 !important;
    color: black !important;
    font-weight: 600 !important;
}

/* Badges */
.badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
}
.success { background: rgba(0,255,150,0.15); color:#00ffa2; }
.warning { background: rgba(255,200,0,0.15); color:#ffd000; }
.error { background: rgba(255,0,0,0.15); color:#ff5c5c; }

/* Tabs */
.stTabs [aria-selected="true"] {
    color: #FFE600 !important;
}

/* Loader */
.loader {
    border: 4px solid #333;
    border-top: 4px solid #FFE600;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 0.8s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg);} }

.center {
    display:flex;
    justify-content:center;
    align-items:center;
    flex-direction:column;
    padding:2rem;
}

/* Footer */
.footer {
    margin-top:60px;
    padding:20px 0;
    border-top:1px solid #2a2a2a;
    display:flex;
    justify-content:space-between;
    font-size:13px;
    color:#888;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# 🧭 NAVIGATION (TOP BAR)
# ============================================================
pages = ["Upload", "Job Status", "Dashboard", "Canonical Viewer"]

if "page" not in st.session_state:
    st.session_state.page = "Upload"

cols = st.columns([3,6])
with cols[0]:
    st.markdown("### EY Contract Intelligence")

with cols[1]:
    nav_cols = st.columns(len(pages))
    for i, p in enumerate(pages):
        if nav_cols[i].button(p):
            st.session_state.page = p

page = st.session_state.page

# ============================================================
# HELPERS
# ============================================================

def badge(status):
    if status == "complete":
        return '<span class="badge success">Completed</span>'
    elif status == "processing":
        return '<span class="badge warning">Processing</span>'
    elif status == "failed":
        return '<span class="badge error">Failed</span>'
    return '<span class="badge warning">Queued</span>'


def timeline(status):
    steps = ["Uploaded", "Queued", "Processing", "Generating Docs", "Completed"]

    mapping = {
        "queued": 1,
        "processing": 2,
        "complete": 4,
        "failed": -1
    }

    current = mapping.get(status, 0)

    html = "<div style='display:flex; gap:20px; align-items:center;'>"

    for i, step in enumerate(steps):

        if i < current:
            color = "#00ffa2"
        elif i == current:
            color = "#FFE600"
        else:
            color = "#555"

        html += f"""
        <div style="text-align:center;">
            <div style="width:18px;height:18px;border-radius:50%;background:{color};margin:auto;"></div>
            <div style="font-size:12px;margin-top:6px;color:{color}">{step}</div>
        </div>
        """

        if i < len(steps)-1:
            html += "<div style='flex:1;height:2px;background:#333;'></div>"

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def audit_trail(job):
    st.markdown("#### Audit Trail")

    created = job.get("created_at", "")
    now = datetime.now().strftime("%H:%M:%S")

    timeline_data = [
        ("Uploaded", created),
        ("Queued", created),
        ("Processing", created),
        ("Completed", now if job["status"] == "complete" else "-")
    ]

    for step, t in timeline_data:
        st.markdown(f"""
        <div class="card">
            <b>{step}</b><br>
            <small>{t}</small>
        </div>
        """, unsafe_allow_html=True)


def preview_pdf(data):
    b64 = base64.b64encode(data).decode()
    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="500"></iframe>', unsafe_allow_html=True)

# ============================================================
# 📤 UPLOAD
# ============================================================

if page == "Upload":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Upload Contract")

    file = st.file_uploader("Upload document")
    contract_type = st.selectbox("Contract Type", ["auto","nda","sow"])

    if st.button("Start Analysis"):

        if not file:
            st.error("Upload required")
        else:
            loader = st.empty()
            loader.markdown('<div class="center"><div class="loader"></div><p>Analyzing...</p></div>', unsafe_allow_html=True)

            try:
                r = requests.post(
                    f"{API_URL}/analyze",
                    headers={"X-API-Key": API_KEY},
                    files={"file": (file.name, file, file.type)},
                    data={"contract_type": contract_type}
                )

                loader.empty()

                if r.status_code == 200:
                    st.session_state.job_id = r.json()["job_id"]
                    st.success("Job started")
                else:
                    st.error("Backend error")

            except:
                loader.empty()
                st.error("Connection failed")

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# ⏳ JOB STATUS
# ============================================================

if page == "Job Status":

    if "job_id" not in st.session_state:
        st.warning("Upload first")
        st.stop()

    job_id = st.session_state.job_id

    box = st.empty()
    progress = st.progress(0)
    p = 0

    while True:
        job = requests.get(f"{API_URL}/jobs/{job_id}", headers={"X-API-Key": API_KEY}).json()
        s = job["status"]

        timeline(s)

        box.markdown(f"<div class='card'><b>{job_id}</b><br>{badge(s)}</div>", unsafe_allow_html=True)

        if s == "complete":
            progress.progress(100)
            audit_trail(job)

            urls = job["download_urls"]
            nda = requests.get(f"{API_URL}{urls['nda_pdf']}", headers={"X-API-Key": API_KEY}).content
            sow = requests.get(f"{API_URL}{urls['sow_pdf']}", headers={"X-API-Key": API_KEY}).content

            st.download_button("Download NDA", nda)
            st.download_button("Download SOW", sow)

            break

        elif s == "processing":
            p = min(p+15, 90)
        elif s == "queued":
            p = 10
        elif s == "failed":
            st.error("Failed")
            break

        progress.progress(p)
        time.sleep(2)

# ============================================================
# 📊 DASHBOARD
# ============================================================

if page == "Dashboard":

    jobs = requests.get(f"{API_URL}/jobs", headers={"X-API-Key": API_KEY}).json().get("jobs", [])

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Jobs", len(jobs))
    c2.metric("Completed", len([j for j in jobs if j["status"]=="complete"]))
    c3.metric("Processing", len([j for j in jobs if j["status"]=="processing"]))

    st.markdown("---")

    for j in jobs[::-1]:
        st.markdown(f"""
        <div class="card">
        <b>{j['job_id']}</b><br>
        {badge(j['status'])}
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# 🧩 CANONICAL VIEWER
# ============================================================

if page == "Canonical Viewer":

    if "job_id" not in st.session_state:
        st.warning("Upload first")
        st.stop()

    job_id = st.session_state.job_id
    job = requests.get(f"{API_URL}/jobs/{job_id}", headers={"X-API-Key": API_KEY}).json()

    if "download_urls" not in job:
        st.warning("Not ready")
        st.stop()

    timeline(job["status"])
    audit_trail(job)

    urls = job["download_urls"]

    nda = requests.get(f"{API_URL}{urls['nda_pdf']}", headers={"X-API-Key": API_KEY}).content
    sow = requests.get(f"{API_URL}{urls['sow_pdf']}", headers={"X-API-Key": API_KEY}).content
    canonical = requests.get(f"{API_URL}/download/{job_id}/canonical", headers={"X-API-Key": API_KEY}).json()

    tabs = st.tabs(["Summary", "Documents", "JSON", "Issues"])

    with tabs[0]:
        st.markdown(f"<div class='card'><b>{job_id}</b><br>{badge(job['status'])}</div>", unsafe_allow_html=True)

    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1:
            st.write("NDA")
            preview_pdf(nda)
        with c2:
            st.write("SOW")
            preview_pdf(sow)

    with tabs[2]:
        st.code(json.dumps(canonical, indent=2))

    with tabs[3]:
        if canonical.get("missingFields"):
            st.warning(", ".join(canonical["missingFields"]))
        if canonical.get("conflicts"):
            for c in canonical["conflicts"]:
                st.write(c)

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
    <div>© 2026 EY Contract Intelligence</div>
    <div>Internal Platform · Confidential</div>
</div>
""", unsafe_allow_html=True)
