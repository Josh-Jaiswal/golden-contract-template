import streamlit as st
import requests
import time
import json
import base64
from datetime import datetime
import pytz

API_URL = "http://localhost:8000"
API_KEY = "GoldenEY1479"

st.set_page_config(layout="wide", page_title="EY Contract Intelligence")

# ============================================================
# 🎨 DESIGN SYSTEM
# ============================================================
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #0b0b0b;
    color: #f5f5f5;
}

/* NAVBAR */
.navbar {
    display: flex;
    gap: 40px;
    border-bottom: 1px solid #2a2a2a;
    padding: 0.8rem 0;
    margin-bottom: 1.5rem;
}
.nav-item {
    font-size: 15px;
    font-weight: 500;
    color: #aaa;
}
.nav-active {
    color: #FFE600;
    border-bottom: 2px solid #FFE600;
}

/* CARDS */
.card {
    background: #141414;
    padding: 1.5rem;
    border-radius: 10px;
    border: 1px solid #2a2a2a;
    margin-bottom: 1rem;
}

/* BUTTON */
button[kind="primary"] {
    background: #FFE600 !important;
    color: black !important;
}

/* BADGE */
.badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
}
.success { background: rgba(0,255,150,0.15); color:#00ffa2; }
.warning { background: rgba(255,200,0,0.15); color:#ffd000; }
.error { background: rgba(255,0,0,0.15); color:#ff5c5c; }

</style>
""", unsafe_allow_html=True)

# ============================================================
# 🧭 NAVIGATION
# ============================================================

pages = ["Upload", "Job Status", "Dashboard", "Canonical Viewer"]

selected = st.radio("", pages, horizontal=True)
page = selected

# ============================================================
# HELPERS
# ============================================================

def badge(status):
    status = status.lower()
    if status == "complete":
        return '<span class="badge success">Completed</span>'
    elif status == "processing":
        return '<span class="badge warning">Processing</span>'
    elif status == "failed":
        return '<span class="badge error">Failed</span>'
    return '<span class="badge warning">Queued</span>'


def format_time(ts):
    if not ts:
        return "-"
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    ist = pytz.timezone("Asia/Kolkata")
    return dt.astimezone(ist).strftime("%d %b %Y, %I:%M %p")


def timeline(status):
    steps = ["Uploaded", "Queued", "Processing", "Completed"]
    mapping = {"queued":1,"processing":2,"complete":3}
    current = mapping.get(status, 0)

    html = "<div style='display:flex;gap:20px;'>"
    for i, step in enumerate(steps):
        color = "#FFE600" if i == current else "#555"
        if i < current: color = "#00ffa2"

        html += f"<div style='text-align:center;color:{color}'>{step}</div>"
    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


def audit_trail(job):
    st.subheader("Audit Trail")

    created = format_time(job.get("created_at"))
    completed = format_time(job.get("completed_at"))

    st.markdown(f"""
    <div class="card"><b>Uploaded</b><br>{created}</div>
    <div class="card"><b>Completed</b><br>{completed}</div>
    """, unsafe_allow_html=True)


def preview_pdf(data):
    b64 = base64.b64encode(data).decode()
    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="500"></iframe>', unsafe_allow_html=True)

# ============================================================
# 📤 UPLOAD
# ============================================================

if page == "Upload":

    st.markdown('<div class="card">', unsafe_allow_html=True)

    file = st.file_uploader("Upload document")
    contract_type = st.selectbox("Contract Type", ["auto","nda","sow"])

    if st.button("Start Analysis"):

        if not file:
            st.error("Upload required")
        else:
            r = requests.post(
                f"{API_URL}/analyze",
                headers={"X-API-Key": API_KEY},
                files={"file": (file.name, file, file.type)},
                data={"contract_type": contract_type}
            )

            if r.status_code == 200:
                st.session_state.job_id = r.json()["job_id"]
                st.success("Job started")

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# ⏳ JOB STATUS
# ============================================================

if page == "Job Status":

    if "job_id" not in st.session_state:
        st.warning("Upload first")
        st.stop()

    job_id = st.session_state.job_id

    job = requests.get(f"{API_URL}/jobs/{job_id}", headers={"X-API-Key": API_KEY}).json()

    timeline(job["status"])

    st.markdown(f"<div class='card'>{badge(job['status'])}</div>", unsafe_allow_html=True)

    if job["status"] == "complete":

        urls = job["download_urls"]

        st.subheader("Documents")

        col1, col2 = st.columns(2)

        with col1:
            nda = requests.get(f"{API_URL}{urls['nda_pdf']}", headers={"X-API-Key": API_KEY}).content
            preview_pdf(nda)
            st.download_button("Download NDA", nda, "NDA.pdf")

        with col2:
            sow = requests.get(f"{API_URL}{urls['sow_pdf']}", headers={"X-API-Key": API_KEY}).content
            preview_pdf(sow)
            st.download_button("Download SOW", sow, "SOW.pdf")

    else:
        st.warning("Documents not ready yet")

    audit_trail(job)

# ============================================================
# 📊 DASHBOARD
# ============================================================

if page == "Dashboard":

    jobs = requests.get(f"{API_URL}/jobs", headers={"X-API-Key": API_KEY}).json().get("jobs", [])

    for j in jobs[::-1]:

        st.markdown('<div class="card">', unsafe_allow_html=True)

        col1, col2 = st.columns([3,1])

        with col1:
            st.markdown(f"<b>{j['job_id']}</b><br>{badge(j['status'])}", unsafe_allow_html=True)

        with col2:
            if j["status"] == "complete":
                try:
                    urls = j["download_urls"]

                    nda = requests.get(f"{API_URL}{urls['nda_pdf']}", headers={"X-API-Key": API_KEY}).content
                    sow = requests.get(f"{API_URL}{urls['sow_pdf']}", headers={"X-API-Key": API_KEY}).content

                    st.download_button("NDA", nda, f"{j['job_id']}_NDA.pdf")
                    st.download_button("SOW", sow, f"{j['job_id']}_SOW.pdf")

                except:
                    st.warning("Docs not ready")
            else:
                st.warning("Not ready")

        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 🧩 CANONICAL VIEWER
# ============================================================

if page == "Canonical Viewer":

    if "job_id" not in st.session_state:
        st.warning("Upload first")
        st.stop()

    job_id = st.session_state.job_id

    canonical = requests.get(
        f"{API_URL}/download/{job_id}/canonical",
        headers={"X-API-Key": API_KEY}
    ).json()

    tabs = st.tabs(["Summary", "JSON", "Missing Fields", "Conflicts"])

    with tabs[0]:
        st.write(job_id)

    with tabs[1]:
        st.code(json.dumps(canonical, indent=2))

    with tabs[2]:
        if canonical.get("missingFields"):
            for f in canonical["missingFields"]:
                st.warning(f)
        else:
            st.success("No missing fields")

    with tabs[3]:
        if canonical.get("conflicts"):
            for c in canonical["conflicts"]:
                st.write(c)
        else:
            st.success("No conflicts")

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div style="margin-top:50px;border-top:1px solid #2a2a2a;padding:10px;color:#888;display:flex;justify-content:space-between;">
    <div>© 2026 EY Contract Intelligence</div>
    <div>Internal Platform · Confidential</div>
</div>
""", unsafe_allow_html=True)
