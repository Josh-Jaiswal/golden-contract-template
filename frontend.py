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
# 🎨 DESIGN SYSTEM + HEADER + NAV
# ============================================================
st.markdown("""
<style>

/* GLOBAL */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #0b0b0b;
    color: #f5f5f5;
}

/* HEADER */
.header {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:16px 24px;
    border-bottom:2px solid #FFE600;
}

.header-title {
    font-size:20px;
    font-weight:600;
}

/* NAV */
.navbar {
    display:flex;
    gap:30px;
    padding:10px 24px;
    border-bottom:1px solid #2a2a2a;
}

.nav-item {
    font-size:14px;
    color:#aaa;
    cursor:pointer;
}

.nav-active {
    color:#FFE600;
    border-bottom:2px solid #FFE600;
}

/* CARD */
.card {
    background:#141414;
    padding:1.4rem;
    border-radius:10px;
    border:1px solid #2a2a2a;
    margin-bottom:1rem;
}

/* BUTTON */
button[kind="primary"] {
    background:#FFE600 !important;
    color:black !important;
}

/* BADGE */
.badge {
    padding:4px 10px;
    border-radius:6px;
    font-size:12px;
}
.success { background: rgba(0,255,150,0.15); color:#00ffa2; }
.warning { background: rgba(255,200,0,0.15); color:#ffd000; }
.error { background: rgba(255,0,0,0.15); color:#ff5c5c; }

/* LOADER */
.loader {
    border:4px solid #333;
    border-top:4px solid #FFE600;
    border-radius:50%;
    width:40px;
    height:40px;
    animation:spin 0.8s linear infinite;
}
@keyframes spin {100% {transform:rotate(360deg);}}

/* FOOTER */
.footer {
    margin-top:50px;
    border-top:1px solid #2a2a2a;
    padding:10px;
    display:flex;
    justify-content:space-between;
    color:#888;
    font-size:13px;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# 🧠 HEADER
# ============================================================
st.markdown("""
<div class="header">
    <div class="header-title">EY Contract Intelligence Platform</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 🧭 NAVIGATION (CLEAN FIX)
# ============================================================

pages = ["Upload", "Job Status", "Dashboard", "Canonical Viewer"]

if "page" not in st.session_state:
    st.session_state.page = "Upload"

nav_cols = st.columns(len(pages))

for i, p in enumerate(pages):
    if nav_cols[i].button(p):
        st.session_state.page = p

page = st.session_state.page

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
    dt = datetime.fromisoformat(ts.replace("Z","+00:00"))
    ist = pytz.timezone("Asia/Kolkata")
    return dt.astimezone(ist).strftime("%d %b %Y, %I:%M %p")


def timeline(status):
    steps = ["Uploaded","Queued","Processing","Generating Docs","Completed"]
    mapping = {"queued":1,"processing":2,"complete":4}
    current = mapping.get(status,0)

    html = "<div style='display:flex;gap:20px;'>"
    for i,s in enumerate(steps):
        if i < current:
            color="#00ffa2"
        elif i == current:
            color="#FFE600"
        else:
            color="#555"

        html += f"<div style='color:{color}'>{s}</div>"
    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


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
            loader = st.empty()
            loader.markdown('<div class="loader"></div>', unsafe_allow_html=True)

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

    timeline_box = st.empty()
    status_box = st.empty()
    progress = st.progress(0)

    p = 0

    while True:
        job = requests.get(f"{API_URL}/jobs/{job_id}", headers={"X-API-Key": API_KEY}).json()
        s = job["status"]

        timeline_box.empty()
        with timeline_box:
            timeline(s)

        status_box.markdown(f"<div class='card'>{badge(s)}</div>", unsafe_allow_html=True)

        if s == "complete":
            progress.progress(100)

            urls = job.get("download_urls",{})

            st.subheader("Documents")
            c1, c2 = st.columns(2)

            with c1:
                try:
                    nda = requests.get(f"{API_URL}{urls['nda_pdf']}", headers={"X-API-Key": API_KEY}).content
                    preview_pdf(nda)
                    st.download_button("Download NDA", nda)
                except:
                    st.warning("NDA not ready")

            with c2:
                try:
                    sow = requests.get(f"{API_URL}{urls['sow_pdf']}", headers={"X-API-Key": API_KEY}).content
                    preview_pdf(sow)
                    st.download_button("Download SOW", sow)
                except:
                    st.warning("SOW not ready")

            st.markdown(f"<div class='card'><b>Uploaded:</b> {format_time(job.get('created_at'))}</div>", unsafe_allow_html=True)
            break

        elif s == "processing":
            p = min(p+15,85)
        elif s == "queued":
            p = 20
        elif s == "failed":
            st.error("Failed")
            break

        progress.progress(p)
        time.sleep(2)

# ============================================================
# 📊 DASHBOARD
# ============================================================

if page == "Dashboard":

    jobs = requests.get(f"{API_URL}/jobs", headers={"X-API-Key": API_KEY}).json().get("jobs",[])

    for j in jobs[::-1]:

        st.markdown('<div class="card">', unsafe_allow_html=True)

        c1,c2 = st.columns([3,1])

        with c1:
            st.markdown(f"<b>{j['job_id']}</b><br>{badge(j['status'])}", unsafe_allow_html=True)

        with c2:
            if j["status"]=="complete":
                try:
                    urls = j["download_urls"]
                    nda = requests.get(f"{API_URL}{urls['nda_pdf']}", headers={"X-API-Key": API_KEY}).content
                    sow = requests.get(f"{API_URL}{urls['sow_pdf']}", headers={"X-API-Key": API_KEY}).content

                    st.download_button("NDA", nda)
                    st.download_button("SOW", sow)

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

    tabs = st.tabs(["Summary","JSON","Missing Fields","Conflicts"])

    with tabs[0]:
        st.write(job_id)

    with tabs[1]:
        st.code(json.dumps(canonical,indent=2))

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
<div class="footer">
    <div>© 2026 EY Contract Intelligence</div>
    <div>Internal Platform · Confidential</div>
</div>
""", unsafe_allow_html=True)
