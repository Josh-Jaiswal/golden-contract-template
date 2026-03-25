import streamlit as st
import requests
import time
import json
import base64

API_URL = "http://localhost:8000"
API_KEY = "GoldenEY1479"

# ---------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------
st.set_page_config(
    page_title="EY Contract Intelligence",
    page_icon="📄",
    layout="wide",
)

# ---------------------------------------------------------------
# DESIGN SYSTEM (INSANE LEVEL)
# ---------------------------------------------------------------
st.markdown("""
<style>

:root {
    --ey-yellow: #FFE600;
    --ey-black: #0b0b0b;
    --ey-dark: #151515;
    --ey-card: #1c1c1c;
    --ey-border: #2a2a2a;
    --ey-text: #e6e6e6;
    --ey-muted: #9a9a9a;
}

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--ey-black);
    color: var(--ey-text);
}

/* Header */
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 2rem;
    border-bottom: 2px solid var(--ey-yellow);
}

.header-title {
    font-size: 26px;
    font-weight: 700;
}

/* Cards */
.card {
    background: var(--ey-card);
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid var(--ey-border);
    margin-bottom: 1.2rem;
    transition: 0.2s ease;
}

.card:hover {
    border-color: var(--ey-yellow);
}

/* Buttons */
button[kind="primary"] {
    background: var(--ey-yellow) !important;
    color: black !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}

/* Badges */
.badge {
    padding: 5px 10px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
}

.success { background: rgba(0,255,150,0.15); color: #00ffa2; }
.warning { background: rgba(255,200,0,0.15); color: #ffd000; }
.error { background: rgba(255,0,0,0.15); color: #ff5c5c; }

/* Loader */
.loader {
    border: 4px solid #333;
    border-top: 4px solid var(--ey-yellow);
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.center {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #111;
}

/* Code block */
.stCodeBlock {
    background: #0f0f0f !important;
}

/* PDF */
.pdf {
    border-radius: 10px;
    overflow: hidden;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------
st.markdown("""
<div class="header">
    <div class="header-title">EY Contract Intelligence Platform</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------
st.sidebar.markdown("## Navigation")
page = st.sidebar.radio("", ["Upload", "Job Status", "Dashboard", "Canonical Viewer"])

# ---------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------
def badge(status):
    if status == "complete":
        return '<span class="badge success">Completed</span>'
    elif status == "processing":
        return '<span class="badge warning">Processing</span>'
    elif status == "failed":
        return '<span class="badge error">Failed</span>'
    else:
        return '<span class="badge warning">Queued</span>'

def loader_ui(msg="Processing..."):
    st.markdown(f"""
    <div class="center">
        <div class="loader"></div>
        <p style="margin-top:10px;">{msg}</p>
    </div>
    """, unsafe_allow_html=True)

def preview_pdf(bytes_data):
    b64 = base64.b64encode(bytes_data).decode()
    st.markdown(f'<iframe class="pdf" src="data:application/pdf;base64,{b64}" width="100%" height="500"></iframe>', unsafe_allow_html=True)

# ===============================================================
# UPLOAD
# ===============================================================
if page == "Upload":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Upload Contract")

    col1, col2 = st.columns([2,1])

    with col1:
        file = st.file_uploader("Choose file", type=["pdf","docx","doc","eml","mp3","wav"])
        contract_type = st.selectbox("Contract Type", ["auto","nda","sow"])

        if st.button("Start Analysis", use_container_width=True):

            if not file:
                st.error("Upload required")
            else:
                loader = st.empty()
                loader_ui("Analyzing contract...")

                try:
                    r = requests.post(
                        f"{API_URL}/analyze",
                        headers={"X-API-Key": API_KEY},
                        files={"file": (file.name, file, file.type)},
                        data={"contract_type": contract_type}
                    )

                    loader.empty()

                    if r.status_code == 200:
                        st.session_state["job_id"] = r.json()["job_id"]
                        st.success("Job created successfully")
                        st.toast("Processing started 🚀")
                    else:
                        st.error("Backend error")

                except:
                    loader.empty()
                    st.error("Connection failed")

    with col2:
        st.markdown("""
        <div class="card">
        <b>Supported Inputs</b><br><br>
        • PDF<br>
        • Word<br>
        • Email<br>
        • Audio<br><br>
        AI auto-detects format
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ===============================================================
# JOB STATUS
# ===============================================================
if page == "Job Status":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Job Status")

    if "job_id" not in st.session_state:
        st.warning("Upload first")
        st.stop()

    job_id = st.session_state["job_id"]

    status_box = st.empty()
    progress = st.progress(0)

    p = 0

    while True:
        job = requests.get(f"{API_URL}/jobs/{job_id}", headers={"X-API-Key": API_KEY}).json()
        s = job["status"]

        status_box.markdown(f"""
        <div class="card">
            <b>Job ID:</b> {job_id}<br><br>
            {badge(s)}
        </div>
        """, unsafe_allow_html=True)

        if s == "queued":
            p = 10
        elif s == "processing":
            p = min(p+15, 90)
        elif s == "complete":
            p = 100
            progress.progress(p)

            urls = job["download_urls"]

            nda = requests.get(f"{API_URL}{urls['nda_pdf']}", headers={"X-API-Key": API_KEY}).content
            sow = requests.get(f"{API_URL}{urls['sow_pdf']}", headers={"X-API-Key": API_KEY}).content

            st.download_button("Download NDA", nda)
            st.download_button("Download SOW", sow)

            break
        elif s == "failed":
            st.error("Job failed")
            break

        progress.progress(p)
        time.sleep(2)

    st.markdown('</div>', unsafe_allow_html=True)

# ===============================================================
# DASHBOARD
# ===============================================================
if page == "Dashboard":

    st.subheader("Dashboard")

    jobs = requests.get(f"{API_URL}/jobs", headers={"X-API-Key": API_KEY}).json().get("jobs", [])

    cols = st.columns(3)

    cols[0].metric("Total Jobs", len(jobs))
    cols[1].metric("Completed", len([j for j in jobs if j["status"]=="complete"]))
    cols[2].metric("Processing", len([j for j in jobs if j["status"]=="processing"]))

    st.markdown("---")

    for job in jobs[::-1]:
        st.markdown(f"""
        <div class="card">
            <div style="display:flex;justify-content:space-between;">
                <div>
                    <b>{job['job_id']}</b><br>
                    <small>{job['created_at']}</small>
                </div>
                <div>{badge(job['status'])}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ===============================================================
# CANONICAL VIEWER
# ===============================================================
if page == "Canonical Viewer":

    if "job_id" not in st.session_state:
        st.warning("Upload first")
        st.stop()

    job_id = st.session_state["job_id"]
    job = requests.get(f"{API_URL}/jobs/{job_id}", headers={"X-API-Key": API_KEY}).json()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Summary")
    st.markdown(f"**Job ID:** {job_id}<br>{badge(job['status'])}", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if "download_urls" not in job:
        st.error("Not ready")
        st.stop()

    urls = job["download_urls"]

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Documents")

    col1, col2 = st.columns(2)

    nda = requests.get(f"{API_URL}{urls['nda_pdf']}", headers={"X-API-Key": API_KEY}).content
    sow = requests.get(f"{API_URL}{urls['sow_pdf']}", headers={"X-API-Key": API_KEY}).content

    with col1:
        st.write("NDA")
        preview_pdf(nda)

    with col2:
        st.write("SOW")
        preview_pdf(sow)

    st.markdown('</div>', unsafe_allow_html=True)

    # JSON
    canonical = requests.get(f"{API_URL}/download/{job_id}/canonical", headers={"X-API-Key": API_KEY}).json()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Canonical JSON")
    st.code(json.dumps(canonical, indent=2))
    st.markdown('</div>', unsafe_allow_html=True)

    if canonical.get("missingFields"):
        st.warning(", ".join(canonical["missingFields"]))

    if canonical.get("conflicts"):
        with st.expander("Conflicts"):
            for c in canonical["conflicts"]:
                st.write(c)

# ---------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------
st.markdown("""
<div style="text-align:center;margin-top:40px;color:#888;">
© 2026 EY Internal Platform
</div>
""", unsafe_allow_html=True)
