import streamlit as st
import requests
import time
import json
import base64
from datetime import datetime
import pytz

API_URL = "http://localhost:8000"
API_KEY = "GoldenEY1479"

st.set_page_config(layout="wide", page_title="EY Contract Intelligence", page_icon="⚡")

# ─────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

:root {
    --gold: #FFE600;
    --gold-dim: rgba(255,230,0,0.12);
    --gold-glow: rgba(255,230,0,0.08);
    --bg: #080808;
    --surface: #111111;
    --surface2: #181818;
    --border: #222222;
    --border-bright: #2e2e2e;
    --text: #f0f0f0;
    --text-muted: #666;
    --text-dim: #999;
    --green: #00e87a;
    --green-dim: rgba(0,232,122,0.12);
    --amber: #ffb300;
    --amber-dim: rgba(255,179,0,0.12);
    --red: #ff4d4d;
    --red-dim: rgba(255,77,77,0.12);
    --blue: #4d9fff;
    --blue-dim: rgba(77,159,255,0.10);
}

html, body, [class*="css"], .stApp {
    background: var(--bg) !important;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 4px; }

/* ── HEADER ── */
.ey-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--bg);
    position: sticky;
    top: 0;
    z-index: 100;
}

.ey-logo {
    display: flex;
    align-items: center;
    gap: 14px;
}

.ey-logo-mark {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 22px;
    color: var(--gold);
    letter-spacing: -0.5px;
    background: var(--gold-dim);
    border: 1px solid rgba(255,230,0,0.25);
    padding: 4px 12px;
    border-radius: 6px;
}

.ey-wordmark {
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 15px;
    color: var(--text);
    letter-spacing: 0.4px;
}

.ey-wordmark span {
    color: var(--text-muted);
    font-weight: 300;
}

.ey-header-right {
    display: flex;
    align-items: center;
    gap: 20px;
}

.ey-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 8px var(--green);
    display: inline-block;
    margin-right: 6px;
}

.ey-env-tag {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--text-muted);
    background: var(--surface2);
    border: 1px solid var(--border);
    padding: 4px 10px;
    border-radius: 4px;
    letter-spacing: 0.5px;
}

/* ── NAV ── */
.ey-nav {
    display: flex;
    gap: 2px;
    padding: 12px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--bg);
}

/* ── SECTION TITLES ── */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.3px;
    margin-bottom: 4px;
}
.section-sub {
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 24px;
}

/* ── CARDS ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
}
.card:hover { border-color: var(--border-bright); }

.card-highlight {
    background: var(--surface);
    border: 1px solid rgba(255,230,0,0.2);
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 12px;
}

/* ── BADGES ── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.3px;
    font-family: 'DM Mono', monospace;
    text-transform: uppercase;
}
.badge-success { background: var(--green-dim); color: var(--green); border: 1px solid rgba(0,232,122,0.25); }
.badge-warning  { background: var(--amber-dim);  color: var(--amber);  border: 1px solid rgba(255,179,0,0.25); }
.badge-error    { background: var(--red-dim);     color: var(--red);    border: 1px solid rgba(255,77,77,0.25); }
.badge-idle     { background: var(--surface2);    color: var(--text-muted); border: 1px solid var(--border); }

/* ── TIMELINE ── */
.timeline-wrap {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 20px 0;
}

.tl-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    flex: 1;
    position: relative;
}

.tl-dot {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    z-index: 1;
    position: relative;
}

.tl-dot-done  { background: var(--green);  color: #000; box-shadow: 0 0 12px rgba(0,232,122,0.4); }
.tl-dot-active{ background: var(--gold);   color: #000; box-shadow: 0 0 14px rgba(255,230,0,0.5); animation: pulse 1.5s ease-in-out infinite; }
.tl-dot-idle  { background: var(--surface2); color: var(--text-muted); border: 1px solid var(--border); }

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 8px rgba(255,230,0,0.3); }
    50%       { box-shadow: 0 0 20px rgba(255,230,0,0.7); }
}

.tl-line {
    position: absolute;
    top: 14px;
    left: 50%;
    width: 100%;
    height: 2px;
    z-index: 0;
}

.tl-label {
    font-size: 11px;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.3px;
    color: var(--text-muted);
    text-align: center;
    white-space: nowrap;
}

.tl-label-active { color: var(--gold); }
.tl-label-done   { color: var(--green); }

/* ── METRIC CARDS ── */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
}
.metric-label {
    font-size: 11px;
    font-family: 'DM Mono', monospace;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 6px;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: var(--text);
}
.metric-sub { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

/* ── CONFLICT CARD ── */
.conflict-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 14px;
}
.conflict-header {
    background: rgba(255,77,77,0.06);
    border-bottom: 1px solid var(--border);
    padding: 12px 18px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    color: var(--red);
    font-family: 'DM Mono', monospace;
}
.conflict-body {
    display: grid;
    grid-template-columns: 1fr 1fr;
}
.conflict-side {
    padding: 16px 18px;
}
.conflict-side:first-child {
    border-right: 1px solid var(--border);
}
.conflict-doc-label {
    font-size: 10px;
    font-family: 'DM Mono', monospace;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
}
.conflict-text {
    font-size: 13px;
    color: var(--text);
    line-height: 1.6;
    background: var(--surface2);
    border-radius: 6px;
    padding: 10px 12px;
    border-left: 2px solid var(--red);
}

/* ── MISSING FIELD ── */
.missing-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 8px;
}
.missing-icon {
    font-size: 16px;
}
.missing-field {
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    color: var(--amber);
}
.missing-hint {
    font-size: 12px;
    color: var(--text-muted);
    margin-left: auto;
}

/* ── DASHBOARD JOB ROW ── */
.job-row {
    display: grid;
    grid-template-columns: 44px 1fr auto auto auto;
    align-items: center;
    gap: 16px;
    padding: 16px 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-bottom: 8px;
    transition: border-color 0.15s;
}
.job-row:hover { border-color: var(--border-bright); }

.job-num {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--text-muted);
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.job-id-main {
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    color: var(--text);
}
.job-id-sub {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 2px;
}

/* ── UPLOAD ZONE ── */
.upload-hint {
    border: 1.5px dashed var(--border-bright);
    border-radius: 12px;
    padding: 40px 32px;
    text-align: center;
    margin-bottom: 20px;
    background: var(--surface);
}
.upload-hint-icon { font-size: 32px; margin-bottom: 10px; }
.upload-hint-title { font-family: 'Syne', sans-serif; font-size: 16px; font-weight: 600; color: var(--text); }
.upload-hint-sub { font-size: 13px; color: var(--text-muted); margin-top: 4px; }

/* ── JSON VIEWER ── */
.json-viewer {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    font-family: 'DM Mono', monospace;
    font-size: 12.5px;
    line-height: 1.7;
    overflow-x: auto;
    max-height: 600px;
    overflow-y: auto;
}

/* ── SUMMARY SECTION ── */
.summary-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 14px 0;
    border-bottom: 1px solid var(--border);
}
.summary-row:last-child { border-bottom: none; }
.summary-key {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.6px;
    width: 160px;
    flex-shrink: 0;
    padding-top: 2px;
}
.summary-val {
    font-size: 13px;
    color: var(--text);
    line-height: 1.5;
}
.summary-val-empty {
    font-size: 13px;
    color: var(--text-muted);
    font-style: italic;
}

/* ── STREAMLIT OVERRIDES ── */
div[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1.5px dashed var(--border-bright) !important;
    border-radius: 10px !important;
    padding: 20px !important;
}
div[data-testid="stSelectbox"] > div { background: var(--surface2) !important; }

button[kind="primary"],
.stButton > button {
    background: var(--gold) !important;
    color: #000 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.3px !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 4px;
    border-bottom: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    border-radius: 0 !important;
    padding: 8px 16px !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--gold) !important;
    border-bottom: 2px solid var(--gold) !important;
}

.stProgress > div > div { background: var(--gold) !important; border-radius: 4px; }
.stProgress { background: var(--surface2) !important; border-radius: 4px; }

div[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
}

.stAlert { background: var(--surface2) !important; border-radius: 8px !important; border: 1px solid var(--border) !important; }

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── FOOTER ── */
.ey-footer {
    margin-top: 60px;
    border-top: 1px solid var(--border);
    padding: 16px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--text-muted);
    font-size: 12px;
    font-family: 'DM Mono', monospace;
}

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="ey-header">
    <div class="ey-logo">
        <div class="ey-logo-mark">EY</div>
        <div>
            <div class="ey-wordmark">Contract Intelligence <span>Platform</span></div>
        </div>
    </div>
    <div class="ey-header-right">
        <span style="font-size:12px;color:#555;font-family:'DM Mono',monospace">
            <span class="ey-status-dot"></span>API Connected
        </span>
        <div class="ey-env-tag">INTERNAL · CONFIDENTIAL</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# NAV
# ─────────────────────────────────────────────
pages = ["Upload & Analyze", "Job Status", "Dashboard", "Contract Viewer"]

if "page" not in st.session_state:
    st.session_state.page = "Upload & Analyze"

nav_cols = st.columns([1.2, 1, 1, 1.2, 4])
page_map = {
    "Upload & Analyze": 0,
    "Job Status": 1,
    "Dashboard": 2,
    "Contract Viewer": 3,
}

for i, p in enumerate(pages):
    if nav_cols[i].button(p, key=f"nav_{p}"):
        st.session_state.page = p

page = st.session_state.page

st.markdown('<div style="padding: 32px 32px 0 32px;">', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def badge_html(status):
    s = status.lower()
    if s == "complete":
        return '<span class="badge badge-success">● Complete</span>'
    elif s == "processing":
        return '<span class="badge badge-warning">◐ Processing</span>'
    elif s == "failed":
        return '<span class="badge badge-error">✕ Failed</span>'
    return '<span class="badge badge-idle">○ Queued</span>'


def format_time(ts):
    if not ts:
        return "—"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        ist = pytz.timezone("Asia/Kolkata")
        return dt.astimezone(ist).strftime("%d %b %Y · %I:%M %p IST")
    except:
        return ts


def render_timeline(status):
    steps = ["Uploaded", "Queued", "Processing", "Generating", "Complete"]
    status_map = {"queued": 1, "processing": 2, "generating": 3, "complete": 4}
    current = status_map.get(status.lower(), 0)

    html = '<div class="timeline-wrap">'
    for i, step in enumerate(steps):
        if i < current:
            dot_cls = "tl-dot-done"
            lbl_cls = "tl-label tl-label-done"
            icon = "✓"
            line_color = "var(--green)"
        elif i == current:
            dot_cls = "tl-dot-active"
            lbl_cls = "tl-label tl-label-active"
            icon = str(i + 1)
            line_color = "var(--border)"
        else:
            dot_cls = "tl-dot-idle"
            lbl_cls = "tl-label"
            icon = str(i + 1)
            line_color = "var(--border)"

        line_html = ""
        if i < len(steps) - 1:
            lc = "var(--green)" if i < current else "var(--border)"
            line_html = f'<div class="tl-line" style="background:linear-gradient(90deg,{lc} 0%,{lc} 100%)"></div>'

        html += f"""
        <div class="tl-step">
            {line_html}
            <div class="tl-dot {dot_cls}">{icon}</div>
            <div class="{lbl_cls}">{step}</div>
        </div>
        """
    html += "</div>"
    return html


def preview_pdf(data):
    b64 = base64.b64encode(data).decode()
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{b64}" '
        f'width="100%" height="560" style="border:none;border-radius:8px;background:#111"></iframe>',
        unsafe_allow_html=True
    )


def api_get(path):
    try:
        return requests.get(f"{API_URL}{path}", headers={"X-API-Key": API_KEY})
    except:
        return None


def api_get_bytes(path):
    try:
        r = requests.get(f"{API_URL}{path}", headers={"X-API-Key": API_KEY})
        return r.content if r.status_code == 200 else None
    except:
        return None


# ─────────────────────────────────────────────
# PAGE: UPLOAD
# ─────────────────────────────────────────────
if page == "Upload & Analyze":

    st.markdown('<div class="section-title">Upload Contract</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Upload a contract document to begin AI-powered extraction and analysis.</div>', unsafe_allow_html=True)

    col_left, col_right = st.columns([1.6, 1], gap="large")

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        file = st.file_uploader(
            "Drop your contract here",
            type=["pdf", "docx", "txt"],
            help="Supported formats: PDF, DOCX, TXT"
        )
        contract_type = st.selectbox(
            "Contract Type",
            ["auto", "nda", "sow"],
            format_func=lambda x: {
                "auto": "🔍 Auto-detect",
                "nda": "📋 NDA — Non-Disclosure Agreement",
                "sow": "📄 SOW — Statement of Work"
            }[x]
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("⚡  Start Analysis", type="primary"):
            if not file:
                st.error("Please upload a document first.")
            else:
                with st.spinner("Submitting to analysis pipeline..."):
                    try:
                        r = requests.post(
                            f"{API_URL}/analyze",
                            headers={"X-API-Key": API_KEY},
                            files={"file": (file.name, file, file.type)},
                            data={"contract_type": contract_type}
                        )
                        if r.status_code == 200:
                            st.session_state.job_id = r.json()["job_id"]
                            st.success(f"Job created: `{st.session_state.job_id}`")
                            time.sleep(0.8)
                            st.session_state.page = "Job Status"
                            st.rerun()
                        else:
                            st.error(f"API error {r.status_code}")
                    except Exception as e:
                        st.error(f"Connection failed: {e}")

    with col_right:
        st.markdown("""
        <div class="card" style="height:100%">
            <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:600;margin-bottom:16px;color:var(--text)">What happens next?</div>
            <div style="display:flex;flex-direction:column;gap:14px">
                <div style="display:flex;gap:12px;align-items:flex-start">
                    <div style="background:var(--gold-dim);border:1px solid rgba(255,230,0,0.2);border-radius:6px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:13px">1</div>
                    <div>
                        <div style="font-size:13px;font-weight:500;color:var(--text)">Document Parsing</div>
                        <div style="font-size:12px;color:var(--text-muted);margin-top:2px">Text extraction and structure detection</div>
                    </div>
                </div>
                <div style="display:flex;gap:12px;align-items:flex-start">
                    <div style="background:var(--gold-dim);border:1px solid rgba(255,230,0,0.2);border-radius:6px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:13px">2</div>
                    <div>
                        <div style="font-size:13px;font-weight:500;color:var(--text)">Clause Extraction</div>
                        <div style="font-size:12px;color:var(--text-muted);margin-top:2px">AI identifies and categorises legal clauses</div>
                    </div>
                </div>
                <div style="display:flex;gap:12px;align-items:flex-start">
                    <div style="background:var(--gold-dim);border:1px solid rgba(255,230,0,0.2);border-radius:6px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:13px">3</div>
                    <div>
                        <div style="font-size:13px;font-weight:500;color:var(--text)">Conflict Detection</div>
                        <div style="font-size:12px;color:var(--text-muted);margin-top:2px">Cross-document inconsistency analysis</div>
                    </div>
                </div>
                <div style="display:flex;gap:12px;align-items:flex-start">
                    <div style="background:var(--gold-dim);border:1px solid rgba(255,230,0,0.2);border-radius:6px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:13px">4</div>
                    <div>
                        <div style="font-size:13px;font-weight:500;color:var(--text)">Document Generation</div>
                        <div style="font-size:12px;color:var(--text-muted);margin-top:2px">NDA and SOW PDFs generated and ready</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE: JOB STATUS
# ─────────────────────────────────────────────
elif page == "Job Status":

    if "job_id" not in st.session_state:
        st.warning("No active job. Please upload a contract first.")
        st.stop()

    job_id = st.session_state.job_id

    st.markdown(f'<div class="section-title">Job Status</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub" style="font-family:\'DM Mono\',monospace">{job_id}</div>', unsafe_allow_html=True)

    timeline_ph = st.empty()
    status_ph = st.empty()
    progress_ph = st.progress(0)
    content_ph = st.empty()

    p = 0
    while True:
        r = api_get(f"/jobs/{job_id}")
        if not r:
            st.error("Cannot reach API")
            break
        job = r.json()
        s = job["status"].lower()

        timeline_ph.markdown(render_timeline(s), unsafe_allow_html=True)
        status_ph.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;padding:10px 0">'
            f'{badge_html(s)}'
            f'<span style="font-size:12px;color:var(--text-muted);font-family:\'DM Mono\',monospace">'
            f'Last updated: {format_time(job.get("updated_at") or job.get("created_at"))}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        if s == "complete":
            progress_ph.progress(100)
            urls = job.get("download_urls", {})

            with content_ph.container():
                st.markdown("---")
                st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:16px;font-weight:600;margin-bottom:16px">Generated Documents</div>', unsafe_allow_html=True)

                c1, c2 = st.columns(2, gap="medium")

                with c1:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown('<div style="font-size:11px;font-family:\'DM Mono\',monospace;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px">Non-Disclosure Agreement</div>', unsafe_allow_html=True)
                    nda = api_get_bytes(urls.get("nda_pdf", ""))
                    if nda:
                        preview_pdf(nda)
                        st.download_button("⬇ Download NDA", nda, file_name="NDA.pdf", mime="application/pdf")
                    else:
                        st.warning("NDA document unavailable")
                    st.markdown("</div>", unsafe_allow_html=True)

                with c2:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown('<div style="font-size:11px;font-family:\'DM Mono\',monospace;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px">Statement of Work</div>', unsafe_allow_html=True)
                    sow = api_get_bytes(urls.get("sow_pdf", ""))
                    if sow:
                        preview_pdf(sow)
                        st.download_button("⬇ Download SOW", sow, file_name="SOW.pdf", mime="application/pdf")
                    else:
                        st.warning("SOW document unavailable")
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown(
                    f'<div class="card" style="margin-top:8px"><span style="font-size:12px;color:var(--text-muted)">Submitted</span>'
                    f'<span style="font-size:13px;color:var(--text);margin-left:16px">{format_time(job.get("created_at"))}</span></div>',
                    unsafe_allow_html=True
                )
            break

        elif s == "failed":
            progress_ph.progress(100)
            content_ph.error("Analysis failed. Check logs or retry.")
            break
        elif s == "processing":
            p = min(p + 12, 80)
        elif s == "queued":
            p = 20

        progress_ph.progress(p)
        time.sleep(2)


# ─────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────
elif page == "Dashboard":

    st.markdown('<div class="section-title">All Jobs</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Overview of all contract analysis jobs.</div>', unsafe_allow_html=True)

    r = api_get("/jobs")
    if not r:
        st.error("Cannot reach API")
        st.stop()

    jobs = r.json().get("jobs", [])

    if not jobs:
        st.info("No jobs found.")
        st.stop()

    # Metrics row
    total = len(jobs)
    complete = sum(1 for j in jobs if j["status"].lower() == "complete")
    processing = sum(1 for j in jobs if j["status"].lower() in ["processing", "queued"])
    failed = sum(1 for j in jobs if j["status"].lower() == "failed")

    m1, m2, m3, m4 = st.columns(4, gap="small")
    m1.markdown(f'<div class="metric-card"><div class="metric-label">Total Jobs</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">Completed</div><div class="metric-value" style="color:var(--green)">{complete}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">In Progress</div><div class="metric-value" style="color:var(--amber)">{processing}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">Failed</div><div class="metric-value" style="color:var(--red)">{failed}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    for idx, j in enumerate(reversed(jobs)):
        jid = j["job_id"]
        status = j["status"].lower()

        with st.container():
            col_num, col_info, col_badge, col_time, col_actions = st.columns([0.4, 2.5, 1, 1.5, 1.5])

            with col_num:
                st.markdown(f'<div class="job-num">#{total - idx}</div>', unsafe_allow_html=True)

            with col_info:
                short = jid[:8] + "..." + jid[-6:] if len(jid) > 20 else jid
                st.markdown(
                    f'<div class="job-id-main">{short}</div>'
                    f'<div class="job-id-sub">{format_time(j.get("created_at"))}</div>',
                    unsafe_allow_html=True
                )

            with col_badge:
                st.markdown(f'<div style="padding-top:8px">{badge_html(status)}</div>', unsafe_allow_html=True)

            with col_time:
                contract_type = j.get("contract_type", "auto").upper()
                st.markdown(f'<div style="padding-top:8px;font-family:\'DM Mono\',monospace;font-size:12px;color:var(--text-muted)">{contract_type}</div>', unsafe_allow_html=True)

            with col_actions:
                if status == "complete":
                    urls = j.get("download_urls", {})
                    c1, c2 = st.columns(2)
                    nda = api_get_bytes(urls.get("nda_pdf", ""))
                    sow = api_get_bytes(urls.get("sow_pdf", ""))
                    if nda:
                        c1.download_button("NDA", nda, file_name="NDA.pdf", mime="application/pdf", key=f"nda_{jid}")
                    if sow:
                        c2.download_button("SOW", sow, file_name="SOW.pdf", mime="application/pdf", key=f"sow_{jid}")
                elif status in ["processing", "queued"]:
                    st.markdown('<div style="padding-top:8px"><span class="badge badge-warning">In progress</span></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="padding-top:8px"><span class="badge badge-error">Failed</span></div>', unsafe_allow_html=True)

            st.markdown('<div style="margin-bottom:8px"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE: CONTRACT VIEWER (was Canonical Viewer)
# ─────────────────────────────────────────────
elif page == "Contract Viewer":

    if "job_id" not in st.session_state:
        st.warning("No active job. Upload a contract first.")
        st.stop()

    job_id = st.session_state.job_id

    st.markdown('<div class="section-title">Contract Viewer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub" style="font-family:\'DM Mono\',monospace">{job_id}</div>', unsafe_allow_html=True)

    r = api_get(f"/download/{job_id}/canonical")
    if not r or r.status_code != 200:
        st.error("Could not load canonical data. Ensure the job is complete.")
        st.stop()

    canonical = r.json()

    tabs = st.tabs(["📋 Summary", "⚠ Conflicts", "🔍 Missing Fields", "{ } Raw JSON"])

    # ── TAB: SUMMARY ──────────────────────────
    with tabs[0]:
        st.markdown("<br>", unsafe_allow_html=True)

        # Try to pull key fields from canonical JSON for display
        # Adapt keys to whatever your API actually returns
        display_fields = [
            ("Contract Type",      canonical.get("contract_type") or canonical.get("type")),
            ("Parties",            canonical.get("parties") or canonical.get("party_names")),
            ("Effective Date",     canonical.get("effective_date")),
            ("Expiry / End Date",  canonical.get("expiry_date") or canonical.get("end_date")),
            ("Governing Law",      canonical.get("governing_law")),
            ("Jurisdiction",       canonical.get("jurisdiction")),
            ("Confidentiality",    canonical.get("confidentiality_period") or canonical.get("confidentiality")),
            ("Payment Terms",      canonical.get("payment_terms")),
            ("Scope of Work",      canonical.get("scope") or canonical.get("scope_of_work")),
            ("Notice Period",      canonical.get("notice_period")),
            ("Limitation of Liability", canonical.get("liability_limit") or canonical.get("limitation_of_liability")),
            ("Termination",        canonical.get("termination_clause") or canonical.get("termination")),
        ]

        st.markdown('<div class="card">', unsafe_allow_html=True)
        for key, val in display_fields:
            if val is None:
                continue
            if isinstance(val, (dict, list)):
                val_str = json.dumps(val, indent=2)
                st.markdown(
                    f'<div class="summary-row"><div class="summary-key">{key}</div>'
                    f'<pre style="font-family:\'DM Mono\',monospace;font-size:12px;color:var(--text-dim);background:var(--surface2);padding:10px;border-radius:6px;margin:0;overflow-x:auto">{val_str}</pre></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="summary-row"><div class="summary-key">{key}</div>'
                    f'<div class="summary-val">{val}</div></div>',
                    unsafe_allow_html=True
                )

        # Fallback: if no known fields matched, show a message
        matched = [v for _, v in display_fields if v is not None]
        if not matched:
            st.markdown('<div style="color:var(--text-muted);padding:20px 0;font-size:13px">No structured fields extracted. Check the Raw JSON tab.</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB: CONFLICTS ────────────────────────
    with tabs[1]:
        st.markdown("<br>", unsafe_allow_html=True)
        conflicts = canonical.get("conflicts", [])

        if not conflicts:
            st.markdown("""
            <div style="display:flex;flex-direction:column;align-items:center;padding:48px 0;color:var(--text-muted)">
                <div style="font-size:36px;margin-bottom:12px">✓</div>
                <div style="font-family:'Syne',sans-serif;font-size:16px;color:var(--green);font-weight:600">No Conflicts Detected</div>
                <div style="font-size:13px;margin-top:6px">All clauses across documents are consistent.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="margin-bottom:16px">{badge_html("failed")} <span style="font-size:13px;color:var(--text-muted);margin-left:8px">{len(conflicts)} conflict(s) found</span></div>', unsafe_allow_html=True)

            for i, conflict in enumerate(conflicts):
                # Support both dict-style and string-style conflicts
                if isinstance(conflict, dict):
                    field     = conflict.get("field", f"Conflict {i+1}")
                    nda_val   = conflict.get("nda_value") or conflict.get("doc1") or conflict.get("value_a", "—")
                    sow_val   = conflict.get("sow_value") or conflict.get("doc2") or conflict.get("value_b", "—")
                    note      = conflict.get("note") or conflict.get("description", "")
                else:
                    # string fallback
                    field   = f"Conflict {i+1}"
                    nda_val = str(conflict)
                    sow_val = "—"
                    note    = ""

                st.markdown(f"""
                <div class="conflict-card">
                    <div class="conflict-header">
                        ⚡ {field}
                        {"· <span style='font-size:11px;color:#888'>" + note + "</span>" if note else ""}
                    </div>
                    <div class="conflict-body">
                        <div class="conflict-side">
                            <div class="conflict-doc-label">NDA / Document A</div>
                            <div class="conflict-text">{nda_val}</div>
                        </div>
                        <div class="conflict-side">
                            <div class="conflict-doc-label">SOW / Document B</div>
                            <div class="conflict-text">{sow_val}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── TAB: MISSING FIELDS ───────────────────
    with tabs[2]:
        st.markdown("<br>", unsafe_allow_html=True)
        missing = canonical.get("missingFields") or canonical.get("missing_fields", [])

        if not missing:
            st.markdown("""
            <div style="display:flex;flex-direction:column;align-items:center;padding:48px 0;color:var(--text-muted)">
                <div style="font-size:36px;margin-bottom:12px">✓</div>
                <div style="font-family:'Syne',sans-serif;font-size:16px;color:var(--green);font-weight:600">All Fields Present</div>
                <div style="font-size:13px;margin-top:6px">No missing fields identified in this contract.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="margin-bottom:16px"><span class="badge badge-warning">⚠ {len(missing)} missing field(s)</span></div>', unsafe_allow_html=True)
            for f in missing:
                if isinstance(f, dict):
                    label = f.get("field") or f.get("name", str(f))
                    hint  = f.get("hint") or f.get("description", "Required for compliance")
                else:
                    label = str(f)
                    hint  = "Required for compliance"

                st.markdown(f"""
                <div class="missing-row">
                    <div class="missing-icon">⚠</div>
                    <div class="missing-field">{label}</div>
                    <div class="missing-hint">{hint}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── TAB: RAW JSON ─────────────────────────
    with tabs[3]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.code(json.dumps(canonical, indent=2), language="json")


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("</div>", unsafe_allow_html=True)  # close main padding div
st.markdown("""
<div class="ey-footer">
    <div>© 2026 Ernst & Young LLP · Contract Intelligence Platform</div>
    <div>Internal Use Only · Do Not Distribute</div>
</div>
""", unsafe_allow_html=True)
