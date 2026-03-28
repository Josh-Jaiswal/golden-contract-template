import streamlit as st
import requests
import time
import json
import base64
from datetime import datetime
from pathlib import Path
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
  --gold-dim: rgba(255,230,0,0.15);
  --gold-glow: rgba(255,230,0,0.08);
  --bg: #ffffff;
  --surface: #f9f9f9;
  --surface2: #f0f0f0;
  --border: #e4e4e4;
  --border-bright: #d0d0d0;
  --text: #1c1c1c;
  --text-muted: #777777;
  --text-dim: #aaaaaa;
  --green: #00875a;
  --green-dim: rgba(0,135,90,0.10);
  --amber: #b45309;
  --amber-dim: rgba(180,83,9,0.10);
  --red: #c0392b;
  --red-dim: rgba(192,57,43,0.08);
  --blue: #1d4ed8;
  --blue-dim: rgba(29,78,216,0.10);
}

html, body, [class*="css"], .stApp {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
}
div[data-testid="stAppViewContainer"],
div[data-testid="stMain"],
section[data-testid="stSidebar"],
div[data-testid="stHeader"] {
  background: var(--bg) !important;
}
/* Force ALL text dark unless overridden */
p, span, div, label, li, td, th, h1, h2, h3, h4 { color: var(--text); }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #c8c8c8; border-radius: 4px; }

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
.ey-logo { display: flex; align-items: center; gap: 14px; }
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
  font-weight: 800;
  font-size: 20px;
  color: var(--text);
  letter-spacing: -0.3px;
}
.ey-wordmark span { color: var(--text-muted); font-weight: 400; font-size: 18px; }
.ey-header-right { display: flex; align-items: center; gap: 20px; }
.ey-status-dot {
  width: 8px; height: 8px;
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

/* ── NAV CARD ── */
.ey-nav-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  margin: 14px 0 0 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  width: 100%;
  box-sizing: border-box;
}
.ey-nav-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 1;                    /* equal width — matches st.columns(4) */
  padding: 9px 12px;
  border-radius: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  cursor: default;            /* real button on top handles cursor */
  border: 1px solid transparent;
  transition: all 0.15s ease;
  text-decoration: none;
  white-space: nowrap;
  letter-spacing: 0.2px;
  user-select: none;
  pointer-events: none;       /* pass clicks through to overlay button */
}
.ey-nav-item.active {
  color: #1c1c1c;
  background: var(--gold);
  border-color: rgba(255,230,0,0.6);
  font-weight: 700;
}
.ey-nav-item.active .ey-nav-icon {
  filter: drop-shadow(0 0 4px rgba(255,230,0,0.5));
}
.ey-nav-icon { font-size: 14px; }
.ey-nav-divider {
  width: 1px;
  height: 20px;
  background: var(--border);
  margin: 0 4px;
  flex-shrink: 0;
}
.ey-nav-spacer { flex: 1; }
.ey-nav-badge {
  font-family: 'DM Mono', monospace;
  font-size: 9px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--text-muted);
  background: var(--surface2);
  border: 1px solid var(--border);
  padding: 2px 7px;
  border-radius: 10px;
}

/* ── PAGE HEADER CARD ── */
.page-header-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 24px;
  margin: 20px 0 28px 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}
.page-header-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--gold);
  border-radius: 3px 0 0 3px;
}
.page-header-icon {
  font-size: 22px;
  width: 42px; height: 42px;
  display: flex; align-items: center; justify-content: center;
  background: var(--gold-dim);
  border: 1px solid rgba(255,230,0,0.2);
  border-radius: 10px;
  flex-shrink: 0;
}
.page-header-text { flex: 1; min-width: 0; }
.page-header-label {
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 1.4px;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 3px;
}
.page-header-title {
  font-family: 'Syne', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.3px;
  line-height: 1.2;
}
.page-header-sub {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
  line-height: 1.4;
}
.page-header-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}
.page-header-pill {
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  background: var(--surface2);
  border: 1px solid var(--border);
  padding: 3px 10px;
  border-radius: 20px;
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
.section-sub { font-size: 13px; color: var(--text-muted); margin-bottom: 24px; }

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
.badge-warning { background: var(--amber-dim); color: var(--amber); border: 1px solid rgba(255,179,0,0.25); }
.badge-error { background: var(--red-dim); color: var(--red); border: 1px solid rgba(255,77,77,0.25); }
.badge-idle { background: var(--surface2); color: var(--text-muted); border: 1px solid var(--border); }

/* ── TIMELINE ── */
.timeline-wrap { display: flex; align-items: center; gap: 0; padding: 20px 0; }
.tl-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
  position: relative;
}
.tl-dot {
  width: 28px; height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  z-index: 1;
  position: relative;
}
.tl-dot-done { background: var(--green); color: #000; box-shadow: 0 0 12px rgba(0,232,122,0.4); }
.tl-dot-active { background: var(--gold); color: #000; box-shadow: 0 0 14px rgba(255,230,0,0.5); animation: pulse 1.5s ease-in-out infinite; }
.tl-dot-idle { background: var(--surface2); color: var(--text-muted); border: 1px solid var(--border); }
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 8px rgba(255,230,0,0.3); }
  50% { box-shadow: 0 0 20px rgba(255,230,0,0.7); }
}
.tl-line {
  position: absolute;
  top: 14px; left: 50%;
  width: 100%; height: 2px;
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
.tl-label-done { color: var(--green); }

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
.conflict-body { display: grid; grid-template-columns: 1fr 1fr; }
.conflict-side { padding: 16px 18px; }
.conflict-side:first-child { border-right: 1px solid var(--border); }
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

/* ── MISSING FIELD (legacy, kept for fallback) ── */
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
.missing-icon { font-size: 16px; }
.missing-field { font-family: 'DM Mono', monospace; font-size: 13px; color: var(--amber); }
.missing-hint { font-size: 12px; color: var(--text-muted); margin-left: auto; }

/* ── MISSING FIELDS TREE ── */
.mf-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 10px;
  overflow: hidden;
}
.mf-section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 18px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
  background: var(--surface);
}
.mf-section-header:hover { background: var(--surface2); }
.mf-chevron {
  font-size: 11px;
  color: var(--text-muted);
  transition: transform 0.2s;
  width: 14px;
  text-align: center;
}
.mf-section-icon { font-size: 15px; }
.mf-section-name {
  font-family: 'Syne', sans-serif;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  flex: 1;
}
.mf-section-count {
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  color: var(--amber);
  background: var(--amber-dim);
  border: 1px solid rgba(255,179,0,0.2);
  padding: 2px 8px;
  border-radius: 12px;
}
.mf-items {
  border-top: 1px solid var(--border);
  padding: 8px 0;
  background: var(--surface2);
}
.mf-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 18px 9px 42px;
  transition: background 0.1s;
}
.mf-item:hover { background: rgba(255,179,0,0.04); }
.mf-item-icon { font-size: 13px; color: var(--amber); }
.mf-item-name {
  font-family: 'DM Mono', monospace;
  font-size: 12.5px;
  color: var(--amber);
  flex: 1;
}
.mf-item-hint {
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'DM Sans', sans-serif;
}
.mf-connector {
  width: 1px;
  background: var(--border);
  margin-left: 24px;
  height: 100%;
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
  width: 36px; height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.job-id-main { font-family: 'DM Mono', monospace; font-size: 13px; color: var(--text); }
.job-id-sub { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

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
.summary-val { font-size: 13px; color: var(--text); line-height: 1.5; }
.summary-val-empty { font-size: 13px; color: var(--text-muted); font-style: italic; }

/* ── CONTRACT VIEWER PAGE BANNER ── */
.cv-page-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  background: linear-gradient(135deg, rgba(255,230,0,0.08) 0%, rgba(255,179,0,0.04) 100%);
  border: 1px solid rgba(255,230,0,0.2);
  border-radius: 10px;
  margin-bottom: 20px;
}
.cv-page-banner-icon {
  font-size: 20px;
}
.cv-page-banner-label {
  font-family: 'Syne', sans-serif;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: var(--gold);
}
.cv-page-banner-title {
  font-family: 'Syne', sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin-top: 1px;
}
.cv-page-banner-id {
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
  margin-left: auto;
  background: var(--surface2);
  border: 1px solid var(--border);
  padding: 4px 10px;
  border-radius: 4px;
}

/* ── STREAMLIT OVERRIDES ── */
div[data-testid="stFileUploader"] {
  background: #fafafa !important;
  border: 1.5px dashed #c8c8c8 !important;
  border-radius: 10px !important;
  padding: 20px !important;
}
div[data-testid="stFileUploader"] * { color: var(--text) !important; }
div[data-testid="stFileUploader"] small { color: var(--text-muted) !important; }
div[data-testid="stFileUploader"] svg { color: var(--text-muted) !important; }
div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] span {
  color: var(--text) !important; font-size: 15px !important; font-weight: 500 !important;
}
/* Selectbox */
div[data-testid="stSelectbox"] > div { background: #ffffff !important; color: var(--text) !important; border: 1.5px solid var(--border-bright) !important; }
div[data-testid="stSelectbox"] * { color: var(--text) !important; }
div[data-testid="stSelectbox"] label { color: var(--text) !important; font-weight: 600 !important; font-size: 14px !important; }
div[data-baseweb="select"] { background: #ffffff !important; }
div[data-baseweb="select"] * { color: var(--text) !important; }
div[data-baseweb="popover"] { background: #ffffff !important; }
div[data-baseweb="menu"] { background: #ffffff !important; border: 1px solid var(--border) !important; }
ul[role="listbox"] li { color: var(--text) !important; background: #ffffff !important; }
ul[role="listbox"] li:hover { background: var(--surface2) !important; }
button[kind="primary"],
.stButton > button {
  background: var(--gold) !important;
  color: #1c1c1c !important;
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
/* Download buttons */
div[data-testid="stDownloadButton"] > button {
  background: var(--gold) !important;
  color: #1c1c1c !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 700 !important;
  font-size: 13px !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 10px 20px !important;
  transition: opacity 0.2s !important;
}
div[data-testid="stDownloadButton"] > button:hover { opacity: 0.88 !important; }

/* ── TABS: Bigger, Bolder, Premium Style ── */

.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  gap: 8px;
  border-bottom: 1px solid var(--border) !important;
  padding-bottom: 6px;
}

/* INACTIVE TAB */
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: #555555 !important;

  font-family: 'DM Sans', sans-serif !important;
  font-size: 18px !important;      /*  Bigger text */
  font-weight: 700 !important;     /*  Bolder */
  letter-spacing: 0.3px !important;

  padding: 14px 26px !important;   /*  Taller + wider */
  line-height: 22px !important;

  border-radius: 6px 6px 0 0 !important;
  border-bottom: 3px solid transparent !important;

  transition: all 0.15s ease !important;
}

/* ACTIVE TAB */
.stTabs [aria-selected="true"] {
  color: #1c1c1c !important;
  background: rgba(255,230,0,0.20) !important;
  border-bottom: 3px solid #e6c800 !important;
  font-size: 19px !important;
  font-weight: 800 !important;
}

.stProgress > div > div { background: var(--gold) !important; border-radius: 4px; }
.stProgress { background: #e8e8e8 !important; border-radius: 4px; }
/* Override Streamlit's blue default progress */
div[data-testid="stProgress"] > div > div > div { background: var(--gold) !important; }
div[data-testid="stMetric"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px 20px;
}
.stAlert { background: var(--surface) !important; border-radius: 8px !important; border: 1px solid var(--border) !important; color: var(--text) !important; }
.stAlert p, .stAlert div { color: var(--text) !important; }

/* Nav routing buttons — overlaid invisibly on top of the visual nav card */
.nav-btn-overlay {
  position: relative;
  margin-top: -58px;
  height: 58px;
  overflow: visible;
  z-index: 10;
}
.nav-btn-overlay > div[data-testid="stHorizontalBlock"] {
  height: 58px !important;
  gap: 6px !important;
  padding: 0 16px !important;
  align-items: stretch !important;
}
.nav-btn-overlay .stButton,
.nav-btn-overlay div[data-testid="column"] {
  height: 58px !important;
}
.nav-btn-overlay .stButton > button {
  width: 100% !important;
  height: 58px !important;
  min-height: 58px !important;
  opacity: 0 !important;
  cursor: pointer !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
  border-radius: 8px !important;
}
/* Kill the gap Streamlit adds under button columns */
.nav-btn-overlay div[data-testid="column"] > div {
  padding: 0 !important;
  gap: 0 !important;
}

/* ── INLINE EDIT BUTTONS in summary ── */
[data-testid="stButton"] button {
  color: var(--text) !important;
}
/* ✎ edit icon buttons */
button[title^="Edit "] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-muted) !important;
  border-radius: 4px !important;
}
/* ── EDITED PILL — gold on white is hard to read, use navy instead ── */
span[style*="color:var(--gold)"],
span[style*="color: var(--gold)"] {
  color: #1d4ed8 !important;
  background: rgba(29,78,216,0.08) !important;
  border-color: rgba(29,78,216,0.2) !important;
}
/* ── ACCEPT CHOSEN VALUE button — make visible without hover ── */
button[title^="Keep the already-chosen"],
button[data-testid*="accept_chosen"] {
  background: var(--surface) !important;
  border: 1.5px solid var(--border-bright) !important;
  color: var(--text) !important;
}

/* ── RAW JSON light mode ── */
.stCodeBlock, div[data-testid="stCode"] > div {
  background: #f5f5f5 !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}
.stCodeBlock code, div[data-testid="stCode"] code,
pre, code { color: #1c1c1c !important; background: transparent !important; }
/* JSON tokens */
.token.string { color: #0a7c59 !important; }
.token.number { color: #1d4ed8 !important; }
.token.boolean { color: #c0392b !important; }
.token.null { color: #999 !important; }
.token.property { color: #1c1c1c !important; font-weight: 600; }
.token.punctuation { color: #666 !important; }

/* ── RADIO BUTTONS ── */
div[data-testid="stRadio"] label { color: var(--text) !important; }
div[data-testid="stRadio"] * { color: var(--text) !important; }

/* ── EXPANDERS ── */
div[data-testid="stExpander"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }
div[data-testid="stExpander"] summary { color: var(--text) !important; font-weight: 600 !important; }
div[data-testid="stExpander"] summary p { color: var(--text) !important; }

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── TEXTAREA ── */
div[data-testid="stTextArea"] textarea {
  background: #ffffff !important;
  color: var(--text) !important;
  border: 1.5px solid var(--border-bright) !important;
  border-radius: 6px !important;
}
div[data-testid="stTextArea"] textarea::placeholder { color: #aaaaaa !important; }
div[data-testid="stTextArea"] label { color: var(--text) !important; }

/* ── TEXT INPUT STATES ── */
div[data-testid="stTextInput"] input {
  background: #ffffff !important;
  border: 1.5px solid var(--border-bright) !important;
  border-radius: 6px !important;
  color: var(--text) !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #aaaaaa !important; opacity: 1 !important; }
div[data-testid="stTextInput"] label { color: var(--text) !important; font-weight: 500 !important; }
div[data-testid="stTextInput"] input:focus:placeholder-shown {
  border-color: #e6c800 !important;
  box-shadow: 0 0 0 2px rgba(255,230,0,0.20) !important;
  outline: none !important;
}
div[data-testid="stTextInput"] input:focus:not(:placeholder-shown) {
  border-color: var(--green) !important;
  box-shadow: 0 0 0 2px rgba(0,135,90,0.18) !important;
  outline: none !important;
}
div[data-testid="stTextInput"] input:not(:placeholder-shown) {
  border-color: rgba(0,232,122,0.45) !important;
  box-shadow: none !important;
}
div[data-testid="stTextInput"] input:not(:focus):placeholder-shown {
  border-color: var(--border-bright) !important;
  box-shadow: none !important;
}

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

/* ── CONFLICTS COUNTER ── */
.conflict-count-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: #fff8f8;
  border: 1.5px solid #f5c0bc;
  border-radius: 10px;
  border-left: 4px solid var(--red);
}
.conflict-count-num {
  font-family: 'Syne', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.3px;
}
.conflict-count-label {
  font-size: 13px;
  color: var(--text-muted);
  font-family: 'DM Sans', sans-serif;
}
.conflict-count-icon {
  font-size: 18px;
  margin-left: auto;
  color: var(--red);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.timeline-container { display: flex; gap: 18px; align-items: center; }
.tl-step { display: flex; align-items: center; position: relative; }
.tl-line { width: 60px; height: 3px; margin: 0 6px; border-radius: 4px; }
.tl-dot {
  width: 26px; height: 26px;
  border-radius: 50%;
  display: flex; justify-content: center; align-items: center;
  font-size: 13px; font-weight: 600;
}
.tl-dot-done { background: var(--green); color: white; }
.tl-dot-active { background: var(--yellow); color: black; }
.tl-dot-idle { background: var(--border); color: black; }
.tl-label { font-size: 13px; margin-top: 4px; text-align: center; }
.tl-label-done { color: var(--green); }
.tl-label-active { color: var(--yellow); }
.conflict-box {
  border: 1px solid var(--border);
  padding: 0;
  border-radius: 10px;
  margin-bottom: 14px;
  background: var(--surface);
  overflow: hidden;
}
.conflict-box-header {
  background: rgba(255,77,77,0.06);
  border-bottom: 1px solid var(--border);
  padding: 12px 18px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--red);
  font-family: 'DM Mono', monospace;
}
.conflict-title { font-weight: bold; margin-bottom: 12px; }
.conflict-body { display: flex; gap: 0; }
.conflict-side { flex: 1; padding: 14px 18px; }
.conflict-side:not(:last-child) { border-right: 1px solid #222; }
.conflict-doc-label {
  font-size: 10px;
  font-weight: 600;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #555;
  font-family: 'DM Mono', monospace;
}
.conflict-text {
  background: var(--surface2);
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--text);
  line-height: 1.55;
  border-left: 2px solid var(--red);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.mf-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    transition: 0.15s ease;
}
.mf-card:hover {
    border-color: var(--border-bright);
    background: var(--surface2);
}

.mf-icon {
    font-size: 15px;
    color: var(--amber);
    font-weight: 700;
    margin-bottom: 4px;
}

.mf-field {
    font-size: 14px;
    color: var(--text);
    font-weight: 500;
}

.mf-hint {
    font-size: 12px;
    color: var(--text-muted);
    padding-left: 2px;
}

.mf-badge {
    background: var(--surface2);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-family: 'DM Mono', monospace;
    color: var(--text);
    margin-left: 8px;
}

.mf-header {
    font-size: 15px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
}

.mf-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
}
@media (min-width: 900px) {
    .mf-grid {
        grid-template-columns: 1fr 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* --- COLLAPSIBLE SECTION SYSTEM --- */
.mf-section {
    border: 1px solid var(--border);
    background: var(--surface);
    border-radius: 8px;
    margin-bottom: 14px;
}

.mf-toggle {
    display: none;
}

.mf-label {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    cursor: pointer;
    user-select: none;
    font-size: 15px;
    font-weight: 600;
}

.mf-label:hover {
    background: var(--surface2);
}

.mf-chevron {
    transition: transform 0.2s ease;
    font-size: 14px;
    opacity: 0.7;
}

.mf-toggle:checked + .mf-label .mf-chevron {
    transform: rotate(90deg);
}

.mf-content {
    display: none;
    padding: 0 16px 16px 16px;
}

.mf-toggle:checked ~ .mf-content {
    display: block;
}

/* --- BADGE --- */
.mf-badge {
    background: var(--surface2);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    color: var(--text);
    margin-left: 10px;
}

/* --- FIELD CARDS --- */
.mf-card {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 12px 14px;
    border-radius: 6px;
    margin-top: 10px;
}

.mf-icon {
    color: var(--amber);
    font-size: 15px;
}

.mf-field {
    font-size: 14px;
    font-weight: 500;
    margin-top: 6px;
}

.mf-hint {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 2px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

.mf-section {
    border: 1px solid var(--border);
    background: var(--surface);
    border-radius: 8px;
    margin-bottom: 14px;
}

/* Collapsible logic */
.mf-toggle { display: none; }

.mf-label {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    cursor: pointer;
    user-select: none;
    font-size: 15px;
    font-weight: 600;
}

.mf-label:hover { background: var(--surface2); }

.mf-chevron {
    transition: transform 0.2s ease;
    font-size: 14px;
    opacity: 0.7;
}

.mf-toggle:checked + .mf-label .mf-chevron {
    transform: rotate(90deg);
}

.mf-content {
    display: none;
    padding: 0 16px 16px 16px;
}

.mf-toggle:checked ~ .mf-content {
    display: block;
}


/*** --- Card Style --- ***/

.mf-card {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 12px 14px;
    border-radius: 6px;
    margin-top: 10px;
    transition: 0.15s ease;
}

.mf-card:hover {
    background: var(--surface2);
    border-color: var(--border-bright);
}

.mf-icon {
    font-size: 16px;
    margin-bottom: 4px;
}

.mf-field {
    font-size: 14px;
    font-weight: 500;
    color: var(--text);
}

.mf-hint {
    font-size: 12px;
    color: var(--text-muted);
}

.mf-badge {
    background: var(--surface2);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    color: var(--text);
    margin-left: 10px;
}

/*** JSON Highlighting ***/
.highlight-json {
    background: var(--surface2) !important;
    padding: 4px;
    border-radius: 4px;
}

</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="ey-header">
  <div class="ey-logo">
    <img src="data:image/png;base64,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" alt="EY" style="height:46px;width:auto;display:block;"/>
    <div style="display:flex;flex-direction:column;justify-content:center;padding-left:4px;">
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

# ---- NAV BUTTONS ----
pages = ["Upload & Analyze", "Job Status", "Dashboard", "Contract Viewer"]

if "page" not in st.session_state:
    st.session_state.page = "Upload & Analyze"

#  Add spacing around the whole bar
st.write("")   # small vertical space
nav_cols = st.columns([1, 1, 1, 1], gap="large")   # ✅ large spacing between buttons

for i, p in enumerate(pages):
    with nav_cols[i]:
        if st.button(p, use_container_width=True):
            st.session_state.page = p
            st.rerun()

page = st.session_state.page

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
    html = '<div class="timeline-container">'
    for i, step in enumerate(steps):
        is_last_step = (i == len(steps) - 1)
        if i < current or (is_last_step and status == "complete"):
            dot_class = "tl-dot tl-dot-done"
            label_class = "tl-label tl-label-done"
            icon = "✓"
            line_color = "var(--green)"
        elif i == current:
            dot_class = "tl-dot tl-dot-active"
            label_class = "tl-label tl-label-active"
            icon = str(i + 1)
            line_color = "var(--border)"
        else:
            dot_class = "tl-dot tl-dot-idle"
            label_class = "tl-label"
            icon = str(i + 1)
            line_color = "var(--border)"
        line_html = ""
        if i < len(steps) - 1:
            lc = "var(--green)" if i < current else "var(--border)"
            line_html = f'<div class="tl-line" style="background:{lc};"></div>'
        html += f"""
        <div class="tl-step">
          {line_html}
          <div class="{dot_class}">{icon}</div>
          <div class="{label_class}">{step}</div>
        </div>
        """
    html += "</div>"
    return html

def preview_pdf(data):
    b64 = base64.b64encode(data).decode()
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{b64}" '
        f'width="100%" height="560" style="border:1px solid var(--border);border-radius:8px;background:#fafafa"></iframe>',
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
# GROUP + RENDER MISSING FIELDS USING EXPANDERS
# ─────────────────────────────────────────────

SECTION_META = {
    "parties":        {"icon": "👥", "label": "Parties"},
    "dates":          {"icon": "📅", "label": "Dates"},
    "scope":          {"icon": "📐", "label": "Scope of Work"},
    "confidentiality":{"icon": "🔒", "label": "Confidentiality"},
    "commercials":    {"icon": "💰", "label": "Commercials"},
    "legal":          {"icon": "⚖️", "label": "Legal"},
    "payment":        {"icon": "💳", "label": "Payment"},
    "termination":    {"icon": "🚫", "label": "Termination"},
    "projectgovernance": {"icon": "📊", "label": "Project Governance"},
    "other":          {"icon": "📋", "label": "Other"},
}

def group_missing_fields(missing_list):
    sections = {}
    for f in missing_list:
        if isinstance(f, dict):
            label = f.get("field") or f.get("name", str(f))
            hint = f.get("hint") or f.get("description", "Required for compliance")
        else:
            label = str(f)
            hint = "Required for compliance"

        parts = label.split(".")
        section_key = parts[0].lower() if len(parts) > 1 else "other"
        subfield = ".".join(parts[1:]) if len(parts) > 1 else label

        if section_key not in sections:
            sections[section_key] = []

        sections[section_key].append({
            "label": subfield,
            "full": label,
            "hint": hint
        })
    return sections

def render_missing_fields_tree(missing_list):
    sections = group_missing_fields(missing_list)

    for sec_key, items in sections.items():
        meta = SECTION_META.get(sec_key, {"icon": "📋", "label": sec_key.capitalize()})

        header = f"{meta['icon']} {meta['label']} · {len(items)} missing"

        with st.expander(header, expanded=False):
            for item in items:
                st.markdown(f"""
                <div style="
                    background:var(--surface);
                    border:1px solid var(--border);
                    border-radius:8px;
                    padding:12px 14px;
                    margin-bottom:10px;
                ">
                    <div style="color:var(--amber);font-size:18px;margin-bottom:4px;">⚠</div>
                    <div style="font-size:14px;font-weight:600;color:var(--text);">
                        {item['label']}
                    </div>
                    <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">
                        {item['hint']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: UPLOAD
# ─────────────────────────────────────────────
if page == "Upload & Analyze":
    st.markdown("""
    <div class="page-header-card">
      <div class="page-header-icon">⚡</div>
      <div class="page-header-text">
        <div class="page-header-label">Upload & Analyze</div>
        <div class="page-header-title">Upload Contract</div>
        <div class="page-header-sub">Upload a contract document to begin AI-powered extraction and analysis.</div>
      </div>
      <div class="page-header-meta">
        <div class="page-header-pill">PDF · DOCX · EML · MP3 · WAV · M4A</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1.6, 1], gap="large")

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        AUDIO_TYPES = ["mp3", "wav", "m4a", "mp4", "m4v"]
        DOC_TYPES   = ["pdf", "docx", "doc", "txt", "eml"]
        file = st.file_uploader(
            "Drop your contract here",
            type=AUDIO_TYPES + DOC_TYPES,
            help="Supported formats: PDF, DOCX, TXT, MP3, WAV, M4A, M4V"
        )
        contract_type = st.selectbox(
            "Contract Type",
            ["auto", "nda", "sow", "both"],
            format_func=lambda x: {
                "auto": "🔍 Auto-detect",
                "nda":  "📋 NDA — Non-Disclosure Agreement",
                "sow":  "📄 SOW — Statement of Work",
                "both": "📑 Both — Generate NDA + SOW"
            }[x]
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("⚡ Start Analysis", type="primary"):
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
        <div class="card" style="height:100%;padding:22px 24px;">

          <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:700;
               color:var(--text-muted);letter-spacing:1.4px;text-transform:uppercase;
               margin-bottom:20px;border-bottom:1px solid var(--border);padding-bottom:12px;">
            Analysis Pipeline
          </div>

          <!-- Step 1 -->
          <div style="display:flex;gap:16px;align-items:flex-start;">
            <div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;">
              <div style="width:34px;height:34px;background:var(--gold-dim);border:1px solid rgba(255,230,0,0.3);
                   border-radius:8px;display:flex;align-items:center;justify-content:center;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1c1c1c" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                </svg>
              </div>
              <div style="width:1px;height:28px;background:linear-gradient(to bottom,rgba(0,0,0,0.15),transparent);margin-top:4px;"></div>
            </div>
            <div style="padding-top:6px;padding-bottom:20px;">
              <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:3px;">Document Parsing</div>
              <div style="font-size:12px;color:var(--text-muted);line-height:1.6;">
                Your file is uploaded and parsed — PDF, DOCX, email thread, or audio transcript. 
                Raw text and structure are extracted, preserving section hierarchy and clause boundaries.
              </div>
            </div>
          </div>

          <!-- Step 2 -->
          <div style="display:flex;gap:16px;align-items:flex-start;">
            <div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;">
              <div style="width:34px;height:34px;background:var(--gold-dim);border:1px solid rgba(255,230,0,0.3);
                   border-radius:8px;display:flex;align-items:center;justify-content:center;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1c1c1c" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  <line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/>
                </svg>
              </div>
              <div style="width:1px;height:28px;background:linear-gradient(to bottom,rgba(0,0,0,0.15),transparent);margin-top:4px;"></div>
            </div>
            <div style="padding-top:6px;padding-bottom:20px;">
              <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:3px;">AI Field Extraction</div>
              <div style="font-size:12px;color:var(--text-muted);line-height:1.6;">
                Azure Content Understanding and GPT-4o analyse the parsed content, 
                mapping 45+ canonical fields — parties, dates, commercials, legal terms, 
                confidentiality clauses, scope, and governance.
              </div>
            </div>
          </div>

          <!-- Step 3 -->
          <div style="display:flex;gap:16px;align-items:flex-start;">
            <div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;">
              <div style="width:34px;height:34px;background:var(--gold-dim);border:1px solid rgba(255,230,0,0.3);
                   border-radius:8px;display:flex;align-items:center;justify-content:center;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1c1c1c" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <div style="width:1px;height:28px;background:linear-gradient(to bottom,rgba(0,0,0,0.15),transparent);margin-top:4px;"></div>
            </div>
            <div style="padding-top:6px;padding-bottom:20px;">
              <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:3px;">Conflict &amp; Gap Detection</div>
              <div style="font-size:12px;color:var(--text-muted);line-height:1.6;">
                Extracted values are merged across all source documents. Where sources 
                disagree — different dates, payment terms, or governing law — conflicts 
                are flagged with both values shown side-by-side for you to resolve.
              </div>
            </div>
          </div>

          <!-- Step 4 -->
          <div style="display:flex;gap:16px;align-items:flex-start;">
            <div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;">
              <div style="width:34px;height:34px;background:var(--gold-dim);border:1px solid rgba(255,230,0,0.3);
                   border-radius:8px;display:flex;align-items:center;justify-content:center;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1c1c1c" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              </div>
              <div style="width:1px;height:28px;background:linear-gradient(to bottom,rgba(0,0,0,0.08),transparent);margin-top:4px;"></div>
            </div>
            <div style="padding-top:6px;">
              <div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:3px;">PDF Generation</div>
              <div style="font-size:12px;color:var(--text-muted);line-height:1.6;">
                Standardised NDA and SOW documents are generated as ready-to-review PDFs, 
                with an audit trail appendix capturing extraction provenance, 
                confidence scores, and any unresolved items.
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
    job_id   = st.session_state.job_id
    short_id = job_id[:8] + "\u2026" + job_id[-6:]
    st.markdown(f"""
    <div class="page-header-card">
      <div class="page-header-icon">\U0001f4e1</div>
      <div class="page-header-text">
        <div class="page-header-label">Pipeline</div>
        <div class="page-header-title">Job Status</div>
        <div class="page-header-sub">Track extraction, analysis and document generation in real time.</div>
      </div>
      <div class="page-header-meta">
        <div class="page-header-pill">JOB · {short_id}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    timeline_ph = st.empty()
    status_ph   = st.empty()
    progress_ph = st.progress(0)
    content_ph  = st.empty()

    p = 0
    while True:
        r = api_get(f"/jobs/{job_id}")
        if not r:
            st.error("Cannot reach API")
            break
        job = r.json()
        s   = job["status"].lower()

        timeline_ph.html(render_timeline(s))
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
            ct   = job.get("contract_type", "auto").lower()
            nda  = api_get_bytes(urls.get("nda_pdf", "")) if urls.get("nda_pdf") else None
            sow  = api_get_bytes(urls.get("sow_pdf", "")) if urls.get("sow_pdf") else None

            with content_ph.container():
                st.markdown("---")
                st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:16px;font-weight:600;margin-bottom:16px">Generated Documents</div>', unsafe_allow_html=True)

                # ── Detection / generation result banner ──────────────────
                if ct == "auto":
                    if nda and sow:
                        detected_label = "Auto-detected: NDA + SOW — both documents generated"
                        detected_icon  = "🔍"
                        banner_color   = "#1c1c1c"
                        glow_color     = "rgba(255,230,0,0.20)"
                        border_color   = "rgba(230,200,0,0.50)"
                    elif nda:
                        detected_label = "Auto-detected: Non-Disclosure Agreement"
                        detected_icon  = "🔍"
                        banner_color   = "#1c1c1c"
                        glow_color     = "rgba(255,230,0,0.20)"
                        border_color   = "rgba(230,200,0,0.50)"
                    elif sow:
                        detected_label = "Auto-detected: Statement of Work"
                        detected_icon  = "🔍"
                        banner_color   = "#1c1c1c"
                        glow_color     = "rgba(255,230,0,0.20)"
                        border_color   = "rgba(230,200,0,0.50)"
                    else:
                        detected_label = "Auto-detect complete — no documents generated"
                        detected_icon  = "⚠"
                        banner_color   = "#ffb300"
                        glow_color     = "rgba(255,179,0,0.15)"
                        border_color   = "rgba(255,179,0,0.3)"
                elif ct == "nda":
                    detected_label = "Generated: Non-Disclosure Agreement"
                    detected_icon  = "📋"
                    banner_color   = "#4d9fff"
                    glow_color     = "rgba(77,159,255,0.15)"
                    border_color   = "rgba(77,159,255,0.3)"
                elif ct == "sow":
                    detected_label = "Generated: Statement of Work"
                    detected_icon  = "📄"
                    banner_color   = "#00e87a"
                    glow_color     = "rgba(0,232,122,0.15)"
                    border_color   = "rgba(0,232,122,0.3)"
                else:  # both
                    detected_label = "Generated: NDA + SOW"
                    detected_icon  = "📑"
                    banner_color   = "#1c1c1c"
                    glow_color     = "rgba(255,230,0,0.20)"
                    border_color   = "rgba(230,200,0,0.50)"

                st.markdown(f"""
                <div style="
                    background: {glow_color};
                    border: 1px solid {border_color};
                    border-radius: 10px;
                    padding: 14px 20px;
                    margin-bottom: 20px;
                    display: flex;
                    align-items: center;
                    gap: 14px;
                    box-shadow: 0 0 24px {glow_color}, 0 0 6px {glow_color};
                    position: relative;
                    overflow: hidden;
                ">
                  <div style="
                    font-size: 22px;
                    filter: drop-shadow(0 0 6px {banner_color});
                  ">{detected_icon}</div>
                  <div>
                    <div style="
                      font-family: 'Syne', sans-serif;
                      font-size: 13px;
                      font-weight: 700;
                      color: {banner_color};
                      letter-spacing: 0.3px;
                      text-shadow: none;
                    ">{detected_label}</div>
                    <div style="font-size: 11px; color: var(--text-muted); margin-top: 3px; font-family: 'DM Mono', monospace;">
                      Contract type · {ct.upper()}
                    </div>
                  </div>
                  <div style="
                    position: absolute;
                    right: 0; top: 0; bottom: 0;
                    width: 120px;
                    background: linear-gradient(to left, {glow_color}, transparent);
                  "></div>
                </div>
                """, unsafe_allow_html=True)

                # ── Render only the doc(s) that were actually generated ───
                if nda and sow:
                    c1, c2 = st.columns(2, gap="medium")
                    with c1:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<div style="font-size:11px;font-family:\'DM Mono\',monospace;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px">Non-Disclosure Agreement</div>', unsafe_allow_html=True)
                        preview_pdf(nda)
                        st.download_button("⬇ Download NDA", nda, file_name="NDA.pdf", mime="application/pdf")
                        st.markdown("</div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<div style="font-size:11px;font-family:\'DM Mono\',monospace;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px">Statement of Work</div>', unsafe_allow_html=True)
                        preview_pdf(sow)
                        st.download_button("⬇ Download SOW", sow, file_name="SOW.pdf", mime="application/pdf")
                        st.markdown("</div>", unsafe_allow_html=True)
                elif nda:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown('<div style="font-size:11px;font-family:\'DM Mono\',monospace;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px">Non-Disclosure Agreement</div>', unsafe_allow_html=True)
                    preview_pdf(nda)
                    st.download_button("⬇ Download NDA", nda, file_name="NDA.pdf", mime="application/pdf")
                    st.markdown("</div>", unsafe_allow_html=True)
                elif sow:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown('<div style="font-size:11px;font-family:\'DM Mono\',monospace;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px">Statement of Work</div>', unsafe_allow_html=True)
                    preview_pdf(sow)
                    st.download_button("⬇ Download SOW", sow, file_name="SOW.pdf", mime="application/pdf")
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.warning("No documents were generated for this job.")

                st.markdown(
                    f'<div class="card" style="margin-top:8px"><span style="font-size:12px;color:var(--text-muted)">Submitted</span>'
                    f'<span style="font-size:13px;color:var(--text);margin-left:16px">{format_time(job.get("created_at"))}</span></div>',
                    unsafe_allow_html=True
                )

                # ── Source file preview ───────────────────────────────────
                file_name = job.get("file_name", "")
                file_ext  = Path(file_name).suffix.lower() if file_name else ""
                AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".mp4", ".m4v"}
                DOC_EXTS   = {".pdf"}
                TEXT_EXTS  = {".txt", ".eml"}

                if file_ext:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:16px;font-weight:600;margin-bottom:12px;">Source File</div>', unsafe_allow_html=True)

                    if file_ext in AUDIO_EXTS:
                        type_icon, type_label = "🎙", "Audio Recording"
                    elif file_ext in DOC_EXTS:
                        type_icon, type_label = "📄", "PDF Document"
                    elif file_ext in TEXT_EXTS:
                        type_icon, type_label = "✉", "Email / Text"
                    else:
                        type_icon, type_label = "📎", "Document"

                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:12px;background:var(--surface);
                         border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin-bottom:12px;">
                      <div style="font-size:22px;">{type_icon}</div>
                      <div>
                        <div style="font-size:13px;font-weight:600;color:var(--text);">{file_name}</div>
                        <div style="font-size:11px;color:var(--text-muted);margin-top:2px;font-family:'DM Mono',monospace;">
                          {type_label} &nbsp;·&nbsp; {file_ext.lstrip('.').upper()}
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    source_bytes = api_get_bytes(f"/download/{job_id}/source")
                    if source_bytes:
                        if file_ext in AUDIO_EXTS:
                            mime = "audio/mpeg" if file_ext == ".mp3" else ("audio/wav" if file_ext == ".wav" else "audio/mp4")
                            st.audio(source_bytes, format=mime)
                            st.download_button("⬇ Download Audio", source_bytes, file_name=file_name, mime=mime, key="dl_source_audio")
                        elif file_ext in DOC_EXTS:
                            with st.expander("👁  Preview uploaded PDF", expanded=False):
                                preview_pdf(source_bytes)
                            st.download_button("⬇ Download Source PDF", source_bytes, file_name=file_name, mime="application/pdf", key="dl_source_pdf")
                        elif file_ext in TEXT_EXTS:
                            with st.expander("👁  Preview source text", expanded=False):
                                st.code(source_bytes.decode("utf-8", errors="replace"), language=None)
                            st.download_button("⬇ Download File", source_bytes, file_name=file_name, mime="text/plain", key="dl_source_text")
                        else:
                            st.markdown('<div style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px 16px;font-size:12px;color:var(--text-muted);">In-browser preview not available for this file type. Download to view locally.</div>', unsafe_allow_html=True)
                            st.download_button("⬇ Download File", source_bytes, file_name=file_name, key="dl_source_other")
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
    st.markdown("""
    <div class="page-header-card">
      <div class="page-header-icon">📊</div>
      <div class="page-header-text">
        <div class="page-header-label">Overview</div>
        <div class="page-header-title">All Jobs</div>
        <div class="page-header-sub">Monitor all contract analysis jobs, download outputs and track pipeline health.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    r = api_get("/jobs")
    if not r:
        st.error("Cannot reach API")
        st.stop()

    jobs = r.json().get("jobs", [])
    if not jobs:
        st.info("No jobs found.")
        st.stop()

    total      = len(jobs)
    complete   = sum(1 for j in jobs if j["status"].lower() == "complete")
    processing = sum(1 for j in jobs if j["status"].lower() in ["processing", "queued"])
    failed     = sum(1 for j in jobs if j["status"].lower() == "failed")

    m1, m2, m3, m4 = st.columns(4, gap="small")
    m1.markdown(f'<div class="metric-card"><div class="metric-label">Total Jobs</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">Completed</div><div class="metric-value" style="color:var(--green)">{complete}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">In Progress</div><div class="metric-value" style="color:var(--amber)">{processing}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-label">Failed</div><div class="metric-value" style="color:var(--red)">{failed}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    for idx, j in enumerate(reversed(jobs)):
        jid    = j["job_id"]
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
                ct = j.get("contract_type", "auto").upper()
                st.markdown(f'<div style="padding-top:8px;font-family:\'DM Mono\',monospace;font-size:12px;color:var(--text-muted)">{ct}</div>', unsafe_allow_html=True)
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
# PAGE: CONTRACT VIEWER
# ─────────────────────────────────────────────
elif page == "Contract Viewer":
    selected_field = st.query_params.get("highlight", None)
    if "job_id" not in st.session_state:
        st.warning("No active job. Upload a contract first.")
        st.stop()

    job_id = st.session_state.job_id

    short_id_cv = job_id[:8] + "…" + job_id[-6:]
    st.markdown(f"""
    <div class="page-header-card">
      <div class="page-header-icon">📄</div>
      <div class="page-header-text">
        <div class="page-header-label">Contract Viewer</div>
        <div class="page-header-title">Canonical Analysis</div>
        <div class="page-header-sub">Review extracted fields, resolve conflicts and fill missing values.</div>
      </div>
      <div class="page-header-meta">
        <div class="page-header-pill">JOB · {short_id_cv}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    r = api_get(f"/download/{job_id}/canonical")
    if not r or r.status_code != 200:
        st.error("Could not load canonical data. Ensure the job is complete.")
        st.stop()

    canonical = r.json()
    _all_conflicts     = canonical.get("conflicts", [])
    _dismissed_set     = st.session_state.get("conflict_dismissed", set())
    _remaining_count   = len([c for c in _all_conflicts if c.get("field", "") not in _dismissed_set])
    _conflict_tab_label = f"⚡  Conflicts  ({_remaining_count})" if _remaining_count else "⚡  Conflicts  ✓"
    tabs = st.tabs(["📋  Summary", _conflict_tab_label, "🔍  Missing Fields", "{ }  Raw JSON"])

    # ── Restore active tab after rerun ──────────────────────────────────────────
    # Streamlit always resets to tab 0 on rerun. We work around this by injecting
    # JS that repeatedly tries to click the correct tab until the DOM is ready.
    if "active_cv_tab" not in st.session_state:
        st.session_state.active_cv_tab = 0
    _active_tab_idx = st.session_state.active_cv_tab
    if _active_tab_idx > 0:
        # Place the script inside the iframe via st.components would be ideal,
        # but unsafe_allow_html scripts DO execute in Streamlit's frontend.
        # We use a retry loop with increasing delays to handle slow renders.
        st.markdown(f"""
        <script>
        (function() {{
            var _target = {_active_tab_idx};
            var _attempts = 0;
            var _maxAttempts = 30;
            function _tryClick() {{
                _attempts++;
                var btns = window.parent.document.querySelectorAll('button[role="tab"]');
                if (btns.length > _target) {{
                    btns[_target].click();
                }} else if (_attempts < _maxAttempts) {{
                    setTimeout(_tryClick, 100);
                }}
            }}
            // Small initial delay then retry loop
            setTimeout(_tryClick, 150);
        }})();
        </script>
        """, unsafe_allow_html=True)

    # ── TAB: SUMMARY ──────────────────────────
    with tabs[0]:
        st.markdown("<br>", unsafe_allow_html=True)

        def fmt_val(v):
            """Flatten any value to a clean readable string."""
            if v is None:
                return None
            if isinstance(v, str):
                s = v.strip()
                return s if s else None
            if isinstance(v, list):
                # Filter empties, join as bullet list
                items = [str(i).strip() for i in v if str(i).strip()]
                return items if items else None
            if isinstance(v, dict):
                # Return dict as-is for structured rendering below
                return v if any(val for val in v.values() if val not in (None, "", [], {})) else None
            return str(v) if v else None

        # ── Session state for summary inline edits ──────────────────────
        if "summary_edits" not in st.session_state:
            st.session_state.summary_edits   = {}   # {canon_path: new_value}
        if "summary_editing" not in st.session_state:
            st.session_state.summary_editing = set() # paths open in edit mode

        st.markdown("""
        <style>
        [data-testid="stButton"] button[title^="Edit "] {
          background:var(--surface2)!important;border:1px solid var(--border)!important;
          color:var(--text)!important;padding:1px 6px!important;font-size:11px!important;
          height:24px!important;min-height:unset!important;box-shadow:none!important;
        }
        [data-testid="stButton"] button[title^="Edit "]:hover {
          background:rgba(255,230,0,0.1)!important;
          border-color:rgba(255,230,0,0.3)!important;color:var(--gold)!important;
        }
        [data-testid="stButton"] button[title="Save"],
        [data-testid="stButton"] button[title="Cancel"] {
          background:transparent!important;border:1px solid #333!important;
          color:#999!important;padding:2px 8px!important;height:28px!important;
          min-height:unset!important;box-shadow:none!important;font-size:12px!important;
        }
        [data-testid="stButton"] button[title="Save"]:hover {
          border-color:var(--green)!important;color:var(--green)!important;
          background:rgba(0,232,122,0.08)!important;
        }
        [data-testid="stButton"] button[title="Cancel"]:hover {
          border-color:var(--red)!important;color:var(--red)!important;
          background:rgba(255,77,77,0.08)!important;
        }
        </style>
        """, unsafe_allow_html=True)

        def fmt_val(v):
            if v is None: return None
            if isinstance(v, str): s = v.strip(); return s if s else None
            if isinstance(v, list):
                items = [str(i).strip() for i in v if str(i).strip()]
                return items if items else None
            if isinstance(v, dict):
                return v if any(val for val in v.values() if val not in (None, "", [], {})) else None
            return str(v) if v else None

        def _patch_canonical(dot_path, new_value):
            """
            Update the canonical JSON dict using a dot-path.
            Example: dot_path='legal.governingLaw'
            """
            try:
                parts = dot_path.split(".")
                ref = canonical

                # Traverse until second last
                for p in parts[:-1]:
                    if p not in ref or not isinstance(ref[p], dict):
                        ref[p] = {}
                    ref = ref[p]

                # Update the final leaf
                ref[parts[-1]] = new_value

            except Exception as e:
                print("Patch Error:", e)

        def render_summary_row(key, val, icon="", canon_path=""):
            """Render a summary row with inline pencil edit.
            canon_path: dot-path into canonical JSON e.g. 'legal.governingLaw'
            """
            if val is None:
                return
            fk = canon_path if canon_path else key.lower().replace(" ", "_")
            is_editing = fk in st.session_state.summary_editing
            is_edited  = fk in st.session_state.summary_edits
            display_val = st.session_state.summary_edits[fk] if is_edited else val

            if isinstance(display_val, list):
                flat = "\n".join(str(i) for i in display_val)
            elif isinstance(display_val, dict):
                flat = "\n".join(f"{k}: {v}" for k, v in display_val.items() if v not in (None, "", [], {}))
            else:
                flat = str(display_val) if display_val is not None else ""

            edited_pill = (
                ' <span style="display:inline-flex;align-items:center;gap:3px;'
                'font-size:10px;font-family:\'DM Mono\',monospace;color:#1d4ed8;'
                'background:rgba(29,78,216,0.08);border:1px solid rgba(29,78,216,0.2);'
                'border-radius:4px;padding:1px 5px;">✎ edited</span>'
            ) if is_edited else ""

            if not is_editing:
                if isinstance(display_val, list) and not is_edited:
                    bullets = "".join(
                        f'<div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:5px;">'
                        f'<div style="color:var(--gold);margin-top:2px;font-size:10px;">▸</div>'
                        f'<div style="font-size:13px;color:var(--text);line-height:1.5;">{item}</div></div>'
                        for item in display_val
                    )
                    val_html = f'<div style="flex:1;padding-top:2px;">{bullets}</div>'
                elif isinstance(display_val, dict) and not is_edited:
                    pairs = "".join(
                        f'<div style="display:flex;gap:8px;align-items:baseline;margin-bottom:6px;">'
                        f'<div style="font-size:10px;font-family:\'DM Mono\',monospace;color:var(--text-muted);'
                        f'text-transform:uppercase;letter-spacing:0.4px;min-width:120px;">{k}</div>'
                        f'<div style="font-size:13px;color:var(--text);">{str(dv)}</div></div>'
                        for k, dv in display_val.items() if dv not in (None, "", [], {})
                    )
                    if not pairs: return
                    val_html = f'<div style="flex:1;padding-top:2px;">{pairs}</div>'
                else:
                    color = "var(--gold)" if is_edited else "var(--text)"
                    val_html = f'<div class="summary-val" style="color:{color};">{flat}{edited_pill}</div>'

                col_val, col_btn = st.columns([22, 1])
                with col_val:
                    st.markdown(
                        f'<div class="summary-row" style="align-items:flex-start;">'
                        f'<div class="summary-key">{icon} {key}</div>{val_html}</div>',
                        unsafe_allow_html=True
                    )
                with col_btn:
                    st.markdown('<div style="padding-top:10px">', unsafe_allow_html=True)
                    if st.button("✎", key=f"eb_{fk}", help=f"Edit {key}"):
                        st.session_state.summary_editing.add(fk)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="padding:6px 0 2px 0;font-family:\'DM Mono\',monospace;'
                    f'font-size:11px;color:var(--gold);text-transform:uppercase;letter-spacing:0.6px;">'
                    f'{icon} {key}</div>', unsafe_allow_html=True
                )
                col_inp, col_save, col_cancel = st.columns([16, 1.3, 1.3])
                with col_inp:
                    new_text = st.text_area(f"edit_{fk}", value=flat, key=f"ei_{fk}",
                                            label_visibility="collapsed", height=72)
                with col_save:
                    st.markdown('<div style="padding-top:6px">', unsafe_allow_html=True)
                    if st.button("✓", key=f"sv_{fk}", help="Save"):
                        st.session_state.summary_edits[fk] = new_text
                        if canon_path:
                            _patch_canonical(canon_path, new_text)
                        st.session_state.summary_editing.discard(fk)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with col_cancel:
                    st.markdown('<div style="padding-top:6px">', unsafe_allow_html=True)
                    if st.button("✕", key=f"cx_{fk}", help="Cancel"):
                        st.session_state.summary_editing.discard(fk)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div style="border-bottom:1px solid var(--border);margin:4px 0 6px 0"></div>', unsafe_allow_html=True)

        # ── Parties block ──
        parties = canonical.get("parties", {})
        client  = parties.get("client", {})
        vendor  = parties.get("vendor", {})

        st.markdown("""
        <div style="font-family:'Syne',sans-serif;font-size:11px;font-weight:700;
             color:var(--text-muted);letter-spacing:1.2px;text-transform:uppercase;
             margin-bottom:10px;">Parties</div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="card" style="margin-bottom:16px;">', unsafe_allow_html=True)

        if client.get("name") or vendor.get("name"):
            col_c, col_v = st.columns(2, gap="large")

            # NOTE: render_summary_row calls st.columns([22,1]) internally.
            # Streamlit forbids nesting st.columns inside an active column —
            # it silently breaks, causing vendor content to render under client.
            # _party_field renders purely with markdown + standalone buttons instead.
            def _party_field(party_data, party_key, field_label, field_value, canon_path):
                if not field_value:
                    return
                fk         = canon_path
                is_editing = fk in st.session_state.summary_editing
                is_edited  = fk in st.session_state.summary_edits
                display    = st.session_state.summary_edits[fk] if is_edited else field_value
                edited_pill = (
                    ' <span style="display:inline-flex;align-items:center;gap:3px;font-size:10px;'
                    'font-family:\'DM Mono\',monospace;color:var(--gold);background:rgba(255,230,0,0.1);'
                    'border:1px solid rgba(255,230,0,0.2);border-radius:4px;padding:1px 5px;">✎ edited</span>'
                ) if is_edited else ""
                if not is_editing:
                    color = "var(--gold)" if is_edited else "var(--text)"
                    st.markdown(
                        f'<div class="summary-row" style="align-items:flex-start;">'
                        f'<div class="summary-key" style="font-size:11px;">{field_label}</div>'
                        f'<div class="summary-val" style="color:{color};">{display}{edited_pill}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("✎", key=f"eb_{fk}", help=f"Edit {field_label}"):
                        st.session_state.summary_editing.add(fk)
                        st.rerun()
                else:
                    st.markdown(
                        f'<div style="font-family:\'DM Mono\',monospace;font-size:11px;color:var(--gold);'
                        f'text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;">{field_label}</div>',
                        unsafe_allow_html=True,
                    )
                    new_val = st.text_input(field_label, value=str(display), key=f"ei_{fk}", label_visibility="collapsed")
                    c_save, c_cancel = st.columns([1, 1])
                    with c_save:
                        if st.button("✓ Save", key=f"sv_{fk}"):
                            st.session_state.summary_edits[fk] = new_val
                            _patch_canonical(canon_path, new_val)
                            st.session_state.summary_editing.discard(fk)
                            st.rerun()
                    with c_cancel:
                        if st.button("✕ Cancel", key=f"cx_{fk}"):
                            st.session_state.summary_editing.discard(fk)
                            st.rerun()
                    st.markdown('<div style="border-bottom:1px solid var(--border);margin:4px 0 6px 0"></div>', unsafe_allow_html=True)

            with col_c:
                st.markdown('<div style="font-size:10px;font-family:\'DM Mono\',monospace;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Client</div>', unsafe_allow_html=True)
                _party_field(client, "client", "Name", client.get("name"), "parties.client.name")
                for si, sig in enumerate(client.get("signatories", [])):
                    if sig.get("name"):
                        sig_val = sig["name"] + (f"  ·  {sig['title']}" if sig.get("title") else "")
                        _party_field(client, "client", f"Signatory {si+1}", sig_val, f"parties.client.signatories.{si}.name")

            with col_v:
                st.markdown('<div style="font-size:10px;font-family:\'DM Mono\',monospace;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Vendor</div>', unsafe_allow_html=True)
                _party_field(vendor, "vendor", "Name", vendor.get("name"), "parties.vendor.name")
                for si, sig in enumerate(vendor.get("signatories", [])):
                    if sig.get("name"):
                        sig_val = sig["name"] + (f"  ·  {sig['title']}" if sig.get("title") else "")
                        _party_field(vendor, "vendor", f"Signatory {si+1}", sig_val, f"parties.vendor.signatories.{si}.name")
        else:
            st.markdown('<div style="color:var(--text-muted);font-size:13px;">No party information extracted.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Dates block ──
        dates = canonical.get("dates", {})
        date_fields = {
            "Effective Date":  dates.get("effectiveDate") or canonical.get("effective_date"),
            "Expiry Date":     dates.get("expiryDate")    or canonical.get("expiry_date"),
            "Execution Date":  dates.get("executionDate"),
            "Review Date":     dates.get("reviewDate"),
        }
        date_fields = {k: v for k, v in date_fields.items() if v}
        if date_fields:
            st.markdown("""<div style="font-family:'Syne',sans-serif;font-size:11px;font-weight:700;
                 color:var(--text-muted);letter-spacing:1.2px;text-transform:uppercase;
                 margin-bottom:10px;">Dates</div>""", unsafe_allow_html=True)
            st.markdown('<div class="card" style="margin-bottom:16px;">', unsafe_allow_html=True)
            date_paths = {"Effective Date":"dates.effectiveDate","Expiry Date":"dates.expiryDate",
                "Execution Date":"dates.executionDate","Review Date":"dates.reviewDate"}
            for label, val in date_fields.items():
                render_summary_row(label, fmt_val(val), canon_path=date_paths.get(label,""))
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Legal block ──
        legal = canonical.get("legal", {})
        legal_fields = {
            "Governing Law":          legal.get("governingLaw")    or canonical.get("governing_law"),
            "Jurisdiction":           legal.get("jurisdiction")    or canonical.get("jurisdiction"),
            "Liability Cap":          legal.get("liabilityCap")    or canonical.get("liability_limit"),
            "IP Ownership":           legal.get("ipOwnership"),
            "Dispute Resolution":     legal.get("disputeResolution"),
        }
        legal_fields = {k: v for k, v in legal_fields.items() if v}
        if legal_fields:
            st.markdown("""<div style="font-family:'Syne',sans-serif;font-size:11px;font-weight:700;
                 color:var(--text-muted);letter-spacing:1.2px;text-transform:uppercase;
                 margin-bottom:10px;">Legal</div>""", unsafe_allow_html=True)
            st.markdown('<div class="card" style="margin-bottom:16px;">', unsafe_allow_html=True)
            legal_paths = {"Governing Law":"legal.governingLaw","Jurisdiction":"legal.jurisdiction",
                "Liability Cap":"legal.liabilityCap","IP Ownership":"legal.ipOwnership",
                "Dispute Resolution":"legal.disputeResolution"}
            for label, val in legal_fields.items():
                render_summary_row(label, fmt_val(val), canon_path=legal_paths.get(label,""))
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Confidentiality block ──
        conf = canonical.get("confidentiality", {})
        conf_term        = conf.get("term")         or canonical.get("confidentiality_period")
        conf_obligations = conf.get("obligations",  [])
        conf_exceptions  = conf.get("exceptions",   [])
        if conf_term or conf_obligations or conf_exceptions:
            st.markdown("""<div style="font-family:'Syne',sans-serif;font-size:11px;font-weight:700;
                 color:var(--text-muted);letter-spacing:1.2px;text-transform:uppercase;
                 margin-bottom:10px;">Confidentiality</div>""", unsafe_allow_html=True)
            st.markdown('<div class="card" style="margin-bottom:16px;">', unsafe_allow_html=True)
            if conf_term:
                render_summary_row("Term", fmt_val(conf_term), canon_path="confidentiality.term")
            if conf_obligations:
                render_summary_row("Obligations", fmt_val(conf_obligations), canon_path="confidentiality.obligations")
            if conf_exceptions:
                render_summary_row("Exceptions", fmt_val(conf_exceptions), canon_path="confidentiality.exceptions")
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Scope of Work block ──
        scope = canonical.get("scope", {})
        scope_desc    = scope.get("description")   or canonical.get("scope_of_work")
        scope_deliv   = scope.get("deliverables",  [])
        scope_out     = scope.get("outOfScope",    [])
        scope_miles   = scope.get("milestones",    [])
        if scope_desc or scope_deliv or scope_out:
            st.markdown("""<div style="font-family:'Syne',sans-serif;font-size:11px;font-weight:700;
                 color:var(--text-muted);letter-spacing:1.2px;text-transform:uppercase;
                 margin-bottom:10px;">Scope of Work</div>""", unsafe_allow_html=True)
            st.markdown('<div class="card" style="margin-bottom:16px;">', unsafe_allow_html=True)
            if scope_desc:
                render_summary_row("Description", fmt_val(scope_desc), canon_path="scope.description")
            if scope_deliv:
                render_summary_row("Deliverables", fmt_val(scope_deliv), canon_path="scope.deliverables")
            if scope_out:
                render_summary_row("Out of Scope", fmt_val(scope_out), canon_path="scope.outOfScope")
            if scope_miles:
                render_summary_row("Milestones", fmt_val(scope_miles), canon_path="scope.milestones")
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Commercials block ──
        comm = canonical.get("commercials", {})
        comm_fields = {
            "Total Value":     comm.get("totalValue"),
            "Currency":        comm.get("currency"),
            "Payment Terms":   comm.get("paymentTerms") or canonical.get("payment_terms"),
            "Pricing Model":   comm.get("pricingModel"),
            "Taxes":           comm.get("taxes"),
        }
        comm_fields = {k: v for k, v in comm_fields.items() if v}
        if comm_fields:
            st.markdown("""<div style="font-family:'Syne',sans-serif;font-size:11px;font-weight:700;
                 color:var(--text-muted);letter-spacing:1.2px;text-transform:uppercase;
                 margin-bottom:10px;">Commercials</div>""", unsafe_allow_html=True)
            st.markdown('<div class="card" style="margin-bottom:16px;">', unsafe_allow_html=True)
            comm_paths = {"Total Value":"commercials.totalValue","Currency":"commercials.currency",
                "Payment Terms":"commercials.paymentTerms","Pricing Model":"commercials.pricingModel",
                "Taxes":"commercials.taxes"}
            for label, val in comm_fields.items():
                render_summary_row(label, fmt_val(val), canon_path=comm_paths.get(label,""))
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Security block ──
        sec = canonical.get("security", {})
        sec_fields = {
            "Data Residency":        sec.get("dataResidency"),
            "Compliance Standard":   sec.get("complianceStandard"),
            "Personal Data Processing": sec.get("personalDataProcessing"),
            "Privacy Requirements":  sec.get("privacyRequirements"),
        }
        sec_fields = {k: v for k, v in sec_fields.items() if v}
        if sec_fields:
            st.markdown("""<div style="font-family:'Syne',sans-serif;font-size:11px;font-weight:700;
                 color:var(--text-muted);letter-spacing:1.2px;text-transform:uppercase;
                 margin-bottom:10px;">Security & Privacy</div>""", unsafe_allow_html=True)
            st.markdown('<div class="card" style="margin-bottom:16px;">', unsafe_allow_html=True)
            sec_paths = {"Data Residency":"security.dataResidency","Compliance Standard":"security.complianceStandard",
                "Personal Data Processing":"security.personalDataProcessing","Privacy Requirements":"security.privacyRequirements"}
            for label, val in sec_fields.items():
                render_summary_row(label, fmt_val(val), canon_path=sec_paths.get(label,""))
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Project Governance block ──
        pg = canonical.get("projectGovernance", {})
        pg_fields = {
            "Project Timeline":  pg.get("projectTimeline"),
            "Kickoff Date":      pg.get("kickoffDate"),
            "Review Milestones": pg.get("reviewMilestones"),
        }
        pg_fields = {k: v for k, v in pg_fields.items() if v}
        if pg_fields:
            st.markdown("""<div style="font-family:'Syne',sans-serif;font-size:11px;font-weight:700;
                 color:var(--text-muted);letter-spacing:1.2px;text-transform:uppercase;
                 margin-bottom:10px;">Project Governance</div>""", unsafe_allow_html=True)
            st.markdown('<div class="card" style="margin-bottom:16px;">', unsafe_allow_html=True)
            pg_paths = {"Project Timeline":"projectGovernance.projectTimeline",
                "Kickoff Date":"projectGovernance.kickoffDate",
                "Review Milestones":"projectGovernance.reviewMilestones"}
            for label, val in pg_fields.items():
                render_summary_row(label, fmt_val(val), canon_path=pg_paths.get(label,""))
            st.markdown("</div>", unsafe_allow_html=True)

        # Fallback if nothing rendered
        all_blocks = [parties, dates, legal, conf, scope, comm, sec, pg]
        if not any(bool(b) for b in all_blocks):
            st.markdown('<div style="color:var(--text-muted);padding:20px 0;font-size:13px">No structured fields extracted. Check the Raw JSON tab.</div>', unsafe_allow_html=True)

        # ── Regenerate bar ───────────────────────────────────────────────
        edited_count = len(st.session_state.get("summary_edits", {}))
        if edited_count > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            label_s = "s" if edited_count != 1 else ""
            regen_html = (
                "<div style='background:rgba(255,230,0,0.05);border:1px solid rgba(255,230,0,0.22);"
                "border-radius:10px;padding:14px 20px;display:flex;align-items:center;gap:12px;'>"
                "<span style='font-size:18px;'>✎</span>"
                "<div>"
                "<div style='font-family:Syne,sans-serif;font-size:13px;font-weight:700;color:#1d4ed8;'>"
                f"{edited_count} field{label_s} edited"
                "</div>"
                "<div style='font-size:11px;color:#666;margin-top:2px;'>"
                "Updated values shown in gold above &middot; Regenerate to apply to your documents"
                "</div></div></div>"
            )
            st.markdown(regen_html, unsafe_allow_html=True)
            st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
            col_regen, col_clear = st.columns([5, 1])
            with col_regen:
                btn_label = f"⚡ Regenerate Documents  ({edited_count} field{label_s} edited)"
                if st.button(btn_label, type="primary", use_container_width=True, key="regen_summary"):
                    overrides = dict(st.session_state.summary_edits)
                    with st.spinner("Submitting edits and queuing regeneration…"):
                        try:
                            r2 = requests.post(
                                f"{API_URL}/jobs/{job_id}/regenerate",
                                headers={"X-API-Key": API_KEY},
                                json={"overrides": overrides},
                            )
                            if r2.status_code == 200:
                                st.session_state.summary_edits   = {}
                                st.session_state.summary_editing = set()
                                st.session_state.page = "Job Status"
                                st.rerun()
                            elif r2.status_code == 404:
                                st.error("The /regenerate endpoint is not deployed yet.")
                            else:
                                st.error(f"API error {r2.status_code}: {r2.text}")
                        except Exception as e:
                            st.error(f"Connection failed: {e}")
            with col_clear:
                if st.button("✕ Clear", key="clear_summ", use_container_width=True):
                    st.session_state.summary_edits   = {}
                    st.session_state.summary_editing = set()
                    st.rerun()
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
            # ── Session state for per-conflict user choices ──────────
            if "conflict_overrides" not in st.session_state:
                st.session_state.conflict_overrides = {}
            if "conflict_custom_text" not in st.session_state:
                st.session_state.conflict_custom_text = {}
            if "regen_submitted" not in st.session_state:
                st.session_state.regen_submitted = False
            if "conflict_dismissed" not in st.session_state:
                st.session_state.conflict_dismissed = set()
            if "conflict_pending_confirm" not in st.session_state:
                st.session_state.conflict_pending_confirm = set()

            dismissed_count  = len(st.session_state.conflict_dismissed)
            remaining_count  = len(conflicts) - dismissed_count
            _h_num  = f"{remaining_count} conflict{'s' if remaining_count != 1 else ''} remaining" if remaining_count else "All conflicts resolved"
            _h_sub  = "Accept the chosen value to dismiss a conflict, or pick an override · then regenerate"
            _h_icon = "✓" if remaining_count == 0 else "⚡"
            _h_col  = "var(--green)" if remaining_count == 0 else "#ffffff"
            _h_bg   = "rgba(0,232,122,0.05)" if remaining_count == 0 else "rgba(255,77,77,0.05)"
            _h_bdr  = "rgba(0,232,122,0.15)" if remaining_count == 0 else "rgba(255,77,77,0.15)"
            st.markdown(f"""
            <div class="conflict-count-header" style="background:{_h_bg};border-color:{_h_bdr};">
              <div>
                <div class="conflict-count-num" style="color:var(--text);">{_h_num}</div>
                <div class="conflict-count-label">{_h_sub}</div>
              </div>
              <div class="conflict-count-icon">{_h_icon}</div>
            </div>
            """, unsafe_allow_html=True)

            resolved_count = 0
            _active_conflicts = [c for c in conflicts if c.get("field", "") not in st.session_state.conflict_dismissed]
            _active_total = len(_active_conflicts)
            _active_i = 0  # renumbered index among non-dismissed conflicts

            for i, conflict in enumerate(conflicts):
                field   = conflict.get("field", f"Conflict {i+1}")
                chosen  = conflict.get("chosen", "—")
                source  = conflict.get("chosenSource", "—")
                alts    = conflict.get("alternatives", [])

                # ── Skip dismissed (accepted) conflicts ──────────────────
                if field in st.session_state.conflict_dismissed:
                    resolved_count += 1   # count it toward regenerate tally
                    continue

                _active_i += 1  # increment visible conflict number

                def _clean_conflict_val(v):
                    """Flatten list values and strip noise for display."""
                    if isinstance(v, list):
                        parts = [str(x).strip().strip('"\'') for x in v if str(x).strip()]
                        return " · ".join(parts) if parts else "—"
                    s = str(v).strip()
                    # Remove outer list brackets that sometimes leak through e.g. ["value"]
                    if s.startswith("[") and s.endswith("]"):
                        inner = s[1:-1].strip().strip('"\'')
                        return inner if inner else "—"
                    return s if s else "—"

                chosen_display = _clean_conflict_val(chosen)
                chosen_short   = chosen_display[:80] + "…" if len(chosen_display) > 80 else chosen_display

                # Build the radio options: chosen + each alternative + custom.
                # Store a label→value map so regenerate can recover the full
                # value even when the radio label is truncated at 80 chars.
                radio_options  = [f"✅ Keep chosen  ·  {chosen_short}  [{source}]"]
                alt_values     = []
                label_to_value = {}
                for a in alts:
                    alt_display = _clean_conflict_val(a.get("value", "—"))
                    alt_short   = alt_display[:80] + "…" if len(alt_display) > 80 else alt_display
                    alt_label   = f"🔄 Use overridden  ·  {alt_short}  [{a.get('source','?')}]"
                    radio_options.append(alt_label)
                    alt_values.append(str(a.get("value", "")))
                    label_to_value[alt_label] = str(a.get("value", ""))
                radio_options.append("✏️ Enter custom value")

                if "conflict_label_values" not in st.session_state:
                    st.session_state.conflict_label_values = {}
                st.session_state.conflict_label_values[field] = label_to_value

                # Header card
                st.markdown(f"""
                <div style="
                    background: var(--surface);
                    border: 1px solid var(--border);
                    border-left: 4px solid #e6c800;
                    border-radius: 10px;
                    padding: 16px 20px 8px 20px;
                    margin-bottom: 4px;
                ">
                  <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                    <div style="
                        background:rgba(255,230,0,0.1);
                        border:1px solid rgba(255,230,0,0.25);
                        border-radius:5px;
                        padding:2px 9px;
                        font-family:'DM Mono',monospace;
                        font-size:10px;
                        color:var(--gold);
                        letter-spacing:0.6px;
                        text-transform:uppercase;
                    ">Conflict {_active_i} of {_active_total}</div>
                    <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:var(--text);">⚡ {field}</div>
                  </div>
                  <div style="display:flex;gap:24px;flex-wrap:wrap;margin-bottom:12px;">
                    <div>
                      <div style="font-size:10px;color:var(--text-muted);font-family:'DM Mono',monospace;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px;">Chosen Value</div>
                      <div style="font-size:13px;color:var(--text);font-weight:500;">{chosen_display}</div>
                    </div>
                    <div>
                      <div style="font-size:10px;color:var(--text-muted);font-family:'DM Mono',monospace;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px;">Source</div>
                      <div style="font-size:13px;color:var(--text-dim);">{source}</div>
                    </div>
                    {"".join(f'''<div>
                      <div style="font-size:10px;color:var(--text-muted);font-family:'DM Mono',monospace;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px;">Overridden · {a.get("source","?")}</div>
                      <div style="font-size:13px;color:#aaa;">{_clean_conflict_val(a.get("value","—"))}</div>
                    </div>''' for a in alts)}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Radio selector
                current_choice = st.session_state.conflict_overrides.get(field, radio_options[0])
                if current_choice not in radio_options:
                    current_choice = radio_options[0]

                chosen_option = st.radio(
                    f"Resolution for **{field}**",
                    radio_options,
                    index=radio_options.index(current_choice),
                    key=f"conflict_radio_{i}",
                    label_visibility="collapsed",
                )
                st.session_state.conflict_overrides[field] = chosen_option

                # Custom value text input — only shown when "Enter custom value" picked
                if chosen_option == "✏️ Enter custom value":
                    custom_val = st.text_input(
                        "Your custom value",
                        value=st.session_state.conflict_custom_text.get(field, ""),
                        key=f"conflict_custom_{i}",
                        placeholder=f"Type replacement value for '{field}'…",
                    )
                    st.session_state.conflict_custom_text[field] = custom_val

                # Count as resolved if user has picked anything other than "keep chosen"
                if not chosen_option.startswith("✅ Keep chosen"):
                    # For custom, only count if they've typed something
                    if chosen_option == "✏️ Enter custom value":
                        if st.session_state.conflict_custom_text.get(field, "").strip():
                            resolved_count += 1
                    else:
                        resolved_count += 1

                # ── Per-card: Accept Chosen Value ────────────────────────
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                _pending = field in st.session_state.conflict_pending_confirm

                if not _pending:
                    _btn_col, _ = st.columns([2, 5])
                    with _btn_col:
                        if st.button(
                            "✓  Accept Chosen Value",
                            key=f"accept_chosen_{i}",
                            help=f"Keep the already-chosen value for '{field}' and dismiss this conflict",
                        ):
                            st.session_state.conflict_pending_confirm.add(field)
                            st.session_state.active_cv_tab = 1  # stay on Conflicts tab
                            st.rerun()
                else:
                    # Confirmation banner — no regenerate here, just dismiss
                    st.markdown(f"""
                    <div style="
                        background: #f0faf6;
                        border: 1.5px solid #6dcfac;
                        border-radius: 8px;
                        padding: 14px 16px;
                        margin-bottom: 6px;
                    ">
                      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                        <div style="font-size:16px;">✅</div>
                        <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:700;color:var(--green);">
                            Accept chosen value for <em>{field}</em>?
                        </div>
                      </div>
                      <div style="font-size:12px;color:var(--text-muted);line-height:1.5;padding-left:26px;">
                          This conflict will be dismissed and the chosen value will be kept.
                          Click <strong style="color:var(--gold);">Regenerate Documents</strong> at the bottom of the page for this to reflect in your documents.
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    _c_confirm, _c_cancel, _ = st.columns([1.2, 1, 5])
                    with _c_confirm:
                        if st.button("✓  Confirm", key=f"confirm_accept_{i}", type="primary"):
                            st.session_state.conflict_dismissed.add(field)
                            st.session_state.conflict_pending_confirm.discard(field)
                            st.session_state.active_cv_tab = 1  # stay on Conflicts tab
                            st.rerun()
                    with _c_cancel:
                        if st.button("✕ Cancel", key=f"cancel_accept_{i}"):
                            st.session_state.conflict_pending_confirm.discard(field)
                            st.session_state.active_cv_tab = 1  # stay on Conflicts tab
                            st.rerun()

                st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)

            # ── Scroll nudge — appears once at least 1 conflict is dismissed/resolved ──
            _dismissed_c = len(st.session_state.conflict_dismissed)
            _override_c  = resolved_count - _dismissed_c
            if resolved_count > 0:
                _nudge_parts = []
                if _dismissed_c > 0:
                    _nudge_parts.append(f"{_dismissed_c} accepted")
                if _override_c > 0:
                    _nudge_parts.append(f"{_override_c} override{'s' if _override_c != 1 else ''}")
                _nudge_str = " · ".join(_nudge_parts)
                st.markdown(f"""
                <div style="
                    display:flex;
                    align-items:center;
                    gap:12px;
                    background:rgba(255,230,0,0.18);
                    border:1px solid rgba(220,190,0,0.40);
                    border-radius:8px;
                    padding:12px 18px;
                    margin: 8px 0 20px 0;
                    animation: fadeIn 0.4s ease;
                ">
                  <div style="font-size:18px;">👇</div>
                  <div>
                    <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:600;color:var(--gold);">
                        {_nudge_str} ready
                    </div>
                    <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">
                        Scroll down and click Regenerate Documents for changes to reflect in your documents
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            # ── Regenerate button — always visible, pulsing when there's something to apply ──
            st.markdown("""
            <div style="
                border-top:1px solid var(--border);
                margin: 16px 0 20px 0;
            "></div>
            """, unsafe_allow_html=True)

            _regen_parts = []
            if _dismissed_c > 0:
                _regen_parts.append(f"{_dismissed_c} accepted")
            if _override_c > 0:
                _regen_parts.append(f"{_override_c} override{'s' if _override_c != 1 else ''}")
            regen_label = f"⚡ Regenerate Documents  ({', '.join(_regen_parts)})" if _regen_parts else "⚡ Regenerate Documents"

            if resolved_count > 0:
                st.markdown("""
                <style>
                div[data-testid="stButton"] > button[kind="primary"] {
                    box-shadow: 0 0 18px rgba(255,230,0,0.35), 0 0 6px rgba(255,230,0,0.2);
                    animation: pulseBtn 2s ease-in-out infinite;
                }
                @keyframes pulseBtn {
                    0%,100% { box-shadow: 0 0 10px rgba(255,230,0,0.2); }
                    50%     { box-shadow: 0 0 26px rgba(255,230,0,0.55), 0 0 8px rgba(255,230,0,0.3); }
                }
                </style>
                """, unsafe_allow_html=True)

            if st.button(regen_label, type="primary", use_container_width=True):
                # Build overrides dict — skip dismissed (accepted) conflicts
                overrides = {}
                for i, conflict in enumerate(conflicts):
                    field        = conflict.get("field", f"Conflict {i+1}")
                    chosen_opt   = st.session_state.conflict_overrides.get(field, "")
                    alts         = conflict.get("alternatives", [])

                    # Dismissed = user accepted the chosen value; no override needed
                    if field in st.session_state.conflict_dismissed:
                        continue
                    if not chosen_opt or chosen_opt.startswith("✅ Keep chosen"):
                        continue  # no override needed
                    elif chosen_opt == "✏️ Enter custom value":
                        custom = st.session_state.conflict_custom_text.get(field, "").strip()
                        if custom:
                            overrides[field] = custom
                    else:
                        field_map = st.session_state.get("conflict_label_values", {}).get(field, {})
                        if chosen_opt in field_map:
                            overrides[field] = field_map[chosen_opt]
                        else:
                            for a in alts:
                                raw = str(a.get("value", ""))
                                if raw[:80] in chosen_opt or raw in chosen_opt:
                                    overrides[field] = raw
                                    break

                # Accepted conflicts count as resolved even with no payload override
                _has_work = overrides or st.session_state.conflict_dismissed
                if not _has_work:
                    st.warning("Accept or override at least one conflict before regenerating.")
                else:
                    with st.spinner("Submitting overrides and queuing regeneration…"):
                        try:
                            r = requests.post(
                                f"{API_URL}/jobs/{job_id}/regenerate",
                                headers={"X-API-Key": API_KEY},
                                json={
                                    "overrides": overrides,
                                    "dismissed_fields": list(st.session_state.conflict_dismissed),
                                },
                            )
                            if r.status_code == 200:
                                new_job_id = r.json().get("job_id", job_id)
                                st.session_state.job_id = new_job_id
                                # Clear all conflict state for fresh run
                                st.session_state.conflict_overrides = {}
                                st.session_state.conflict_custom_text = {}
                                st.session_state.conflict_dismissed = set()
                                st.session_state.conflict_pending_confirm = set()
                                st.session_state.page = "Job Status"
                                st.rerun()
                            elif r.status_code == 404:
                                # API endpoint not yet built — fall back gracefully
                                st.error("The /regenerate endpoint isn't deployed yet. Ask your backend dev to add POST /jobs/{job_id}/regenerate — see the spec below.")
                                st.code(json.dumps({
                                    "endpoint": f"POST /jobs/{job_id}/regenerate",
                                    "body":     {"overrides": overrides},
                                    "expected_response": {"job_id": "<new_or_same_job_id>", "status": "queued"}
                                }, indent=2), language="json")
                            else:
                                st.error(f"API error {r.status_code}: {r.text}")
                        except Exception as e:
                            st.error(f"Connection failed: {e}")

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
            # ── Session state for missing field fills ──────────────────
            if "missing_fills" not in st.session_state:
                st.session_state.missing_fills = {}

            filled_count = sum(
                1 for f in missing
                if st.session_state.missing_fills.get(
                    f if isinstance(f, str) else f.get("field", str(f)), ""
                ).strip()
            )

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
              <span class="badge badge-warning">⚠ {len(missing)} missing field{'s' if len(missing) != 1 else ''}</span>
              <span style="font-size:12px;color:var(--text-muted);">
                Grouped by section · fill in values to include them in a regenerated document
              </span>
            </div>
            """, unsafe_allow_html=True)

            # ── Group and render with fillable inputs ─────────────────
            sections = group_missing_fields(missing)

            for sec_key, items in sections.items():
                meta   = SECTION_META.get(sec_key, {"icon": "📋", "label": sec_key.capitalize()})
                filled_in_section = sum(
                    1 for item in items
                    if st.session_state.missing_fills.get(item["full"], "").strip()
                )
                header_suffix = f" · {filled_in_section}/{len(items)} filled" if filled_in_section else f" · {len(items)} missing"
                header = f"{meta['icon']} {meta['label']}{header_suffix}"

                with st.expander(header, expanded=False):
                    for item in items:
                        field_key = item["full"]
                        current   = st.session_state.missing_fills.get(field_key, "")

                        # Field card header
                        st.markdown(f"""
                        <div style="
                            background: var(--surface2);
                            border: 1px solid {'rgba(255,230,0,0.25)' if current.strip() else 'var(--border)'};
                            border-left: 3px solid var(--gold);
                            border-radius: 8px;
                            padding: 10px 14px 4px 14px;
                            margin-bottom: 4px;
                        ">
                          <div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">
                            <div style="font-size:{'14px' if current.strip() else '13px'};color:{'var(--gold)' if current.strip() else 'var(--amber)'};">
                                {'✅' if current.strip() else '⚠'}
                            </div>
                            <div style="font-size:13px;font-weight:600;color:var(--text);">{item['label']}</div>
                            <div style="font-size:10px;font-family:'DM Mono',monospace;color:var(--text-muted);
                                 background:var(--surface2);border:1px solid var(--border);border-radius:4px;
                                 padding:1px 7px;">{field_key}</div>
                          </div>
                          <div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">{item['hint']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Text input below the card
                        new_val = st.text_input(
                            f"Value for {item['label']}",
                            value=current,
                            key=f"missing_{field_key}",
                            placeholder=f"Enter {item['label'].lower()}…",
                            label_visibility="collapsed",
                        )
                        st.session_state.missing_fills[field_key] = new_val
                        st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)

            # ── Scroll nudge once any field is filled ──────────────────
            filled_count = sum(
                1 for item in [i for sec in sections.values() for i in sec]
                if st.session_state.missing_fills.get(item["full"], "").strip()
            )

            if filled_count > 0:
                st.markdown(f"""
                <div style="
                    display:flex;align-items:center;gap:12px;
                    background:rgba(255,230,0,0.18);
                    border:1px solid rgba(220,190,0,0.40);
                    border-radius:8px;
                    padding:12px 18px;
                    margin:16px 0 20px 0;
                ">
                  <div style="font-size:18px;">👇</div>
                  <div>
                    <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:600;color:var(--gold);">
                        {filled_count} field{'s' if filled_count != 1 else ''} filled in
                    </div>
                    <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">
                        Scroll down to regenerate your documents with these values included
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            # ── Regenerate button ──────────────────────────────────────
            st.markdown('<div style="border-top:1px solid var(--border);margin:16px 0 20px 0;"></div>', unsafe_allow_html=True)

            regen_label_mf = f"⚡ Regenerate Documents ({filled_count} field{'s' if filled_count != 1 else ''} added)" if filled_count > 0 else "⚡ Regenerate Documents"

            if filled_count > 0:
                st.markdown("""
                <style>
                div[data-testid="stButton"] > button[kind="primary"] {
                    box-shadow: 0 0 18px rgba(255,230,0,0.35), 0 0 6px rgba(255,230,0,0.2);
                    animation: pulseBtn 2s ease-in-out infinite;
                }
                </style>
                """, unsafe_allow_html=True)

            if st.button(regen_label_mf, type="primary", use_container_width=True, key="regen_missing"):
                fills = {
                    item["full"]: st.session_state.missing_fills[item["full"]]
                    for sec in sections.values()
                    for item in sec
                    if st.session_state.missing_fills.get(item["full"], "").strip()
                }
                if not fills:
                    st.warning("Fill in at least one field value before regenerating.")
                else:
                    with st.spinner("Submitting filled values and queuing regeneration…"):
                        try:
                            r = requests.post(
                                f"{API_URL}/jobs/{job_id}/regenerate",
                                headers={"X-API-Key": API_KEY},
                                json={"overrides": fills},
                            )
                            if r.status_code == 200:
                                st.session_state.job_id = r.json().get("job_id", job_id)
                                st.session_state.missing_fills = {}
                                st.session_state.page = "Job Status"
                                st.rerun()
                            elif r.status_code == 404:
                                st.error("The /regenerate endpoint isn't deployed yet.")
                                st.code(json.dumps({"endpoint": f"POST /jobs/{job_id}/regenerate", "body": {"overrides": fills}}, indent=2), language="json")
                            else:
                                st.error(f"API error {r.status_code}: {r.text}")
                        except Exception as e:
                            st.error(f"Connection failed: {e}")

    # ── TAB: RAW JSON ─────────────────────────
    with tabs[3]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.code(json.dumps(canonical, indent=2), language="json")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("""
<div class="ey-footer">
  <div>© 2026 Ernst & Young LLP · Contract Intelligence Platform</div>
  <div>Internal Use Only · Do Not Distribute</div>
</div>
""", unsafe_allow_html=True)
