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
  font-weight: 600;
  font-size: 15px;
  color: var(--text);
  letter-spacing: 0.4px;
}
.ey-wordmark span { color: var(--text-muted); font-weight: 300; }
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
  background: #0d0d0d;
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
  color: var(--text-muted) !important;

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
  color: var(--gold) !important;
  background: rgba(255,230,0,0.08) !important;

  border-bottom: 3px solid var(--gold) !important;

  font-size: 19px !important;      /*  Slightly larger when active */
  font-weight: 800 !important;     /*  Stronger emphasis */
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

/* ── TEXT INPUT STATES ── */
div[data-testid="stTextInput"] input {
  background: var(--surface2) !important;
  border: 1px solid var(--border-bright) !important;
  border-radius: 6px !important;
  color: var(--text) !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
div[data-testid="stTextInput"] input:focus:placeholder-shown {
  border-color: var(--red) !important;
  box-shadow: 0 0 0 2px rgba(255,77,77,0.18) !important;
  outline: none !important;
}
div[data-testid="stTextInput"] input:focus:not(:placeholder-shown) {
  border-color: var(--green) !important;
  box-shadow: 0 0 0 2px rgba(0,232,122,0.18) !important;
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
  background: rgba(255,77,77,0.05);
  border: 1px solid rgba(255,77,77,0.15);
  border-radius: 10px;
}
.conflict-count-num {
  font-family: 'Syne', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.3px;
}
.conflict-count-label {
  font-size: 13px;
  color: var(--text-dim);
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
  border: 1px solid #2a2a2a;
  padding: 0;
  border-radius: 10px;
  margin-bottom: 14px;
  background: #111111;
  overflow: hidden;
}
.conflict-box-header {
  background: rgba(255,77,77,0.06);
  border-bottom: 1px solid #2a2a2a;
  padding: 12px 18px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #ff4d4d;
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
  background: #181818;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #e0e0e0;
  line-height: 1.55;
  border-left: 2px solid #ff4d4d;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.mf-card {
    background: #1b1b20;
    border: 1px solid #2b2b33;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    transition: 0.15s ease;
}
.mf-card:hover {
    border-color: #3f3f55;
    background: #212128;
}

.mf-icon {
    font-size: 15px;
    color: #ffcd4d;
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
    background: #2a2a33;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-family: 'DM Mono', monospace;
    color: #cfcfd9;
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
    border: 1px solid #2c2c33;
    background: #1a1a1f;
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
    background: #222229;
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
    background: #2f2f48;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    color: #e3e3f5;
    margin-left: 10px;
}

/* --- FIELD CARDS --- */
.mf-card {
    background: #202026;
    border: 1px solid #33333d;
    padding: 12px 14px;
    border-radius: 6px;
    margin-top: 10px;
}

.mf-icon {
    color: #ffcf4d;
    font-size: 15px;
}

.mf-field {
    font-size: 14px;
    font-weight: 500;
    margin-top: 6px;
}

.mf-hint {
    font-size: 12px;
    color: #9b9ba5;
    margin-top: 2px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

.mf-section {
    border: 1px solid #2c2c33;
    background: #1a1a1f;
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

.mf-label:hover { background: #222229; }

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
    background: #202026;
    border: 1px solid #33333d;
    padding: 12px 14px;
    border-radius: 6px;
    margin-top: 10px;
    transition: 0.15s ease;
}

.mf-card:hover {
    background: #27272f;
    border-color: #3f3f55;
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
    background: #2f2f48;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    color: #e3e3f5;
    margin-left: 10px;
}

/*** JSON Highlighting ***/
.highlight-json {
    background: #444450 !important;
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
                    background:#1c1c22;
                    border:1px solid #2d2d35;
                    border-radius:8px;
                    padding:12px 14px;
                    margin-bottom:10px;
                ">
                    <div style="color:#ffcf4c;font-size:18px;margin-bottom:4px;">⚠</div>
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
    st.markdown('<div class="section-title">Upload Contract</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Upload a contract document to begin AI-powered extraction and analysis.</div>', unsafe_allow_html=True)

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
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFE600" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                </svg>
              </div>
              <div style="width:1px;height:28px;background:linear-gradient(to bottom,rgba(255,230,0,0.3),rgba(255,230,0,0.05));margin-top:4px;"></div>
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
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFE600" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  <line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/>
                </svg>
              </div>
              <div style="width:1px;height:28px;background:linear-gradient(to bottom,rgba(255,230,0,0.3),rgba(255,230,0,0.05));margin-top:4px;"></div>
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
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFE600" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <div style="width:1px;height:28px;background:linear-gradient(to bottom,rgba(255,230,0,0.3),rgba(255,230,0,0.05));margin-top:4px;"></div>
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
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFE600" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              </div>
              <div style="width:1px;height:28px;background:linear-gradient(to bottom,rgba(255,230,0,0.05),transparent);margin-top:4px;"></div>
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
    st.markdown(f'<div class="section-title">Job Status</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-sub">'
        f'<span style="font-family:\'DM Sans\',sans-serif;color:var(--text-muted);font-size:12px;'
        f'text-transform:uppercase;letter-spacing:0.8px;font-weight:600;">Job ID&nbsp;&nbsp;</span>'
        f'<span style="font-family:\'DM Mono\',monospace;font-size:13px;color:var(--text-dim);">{job_id}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

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
                        banner_color   = "#FFE600"
                        glow_color     = "rgba(255,230,0,0.18)"
                        border_color   = "rgba(255,230,0,0.35)"
                    elif nda:
                        detected_label = "Auto-detected: Non-Disclosure Agreement"
                        detected_icon  = "🔍"
                        banner_color   = "#FFE600"
                        glow_color     = "rgba(255,230,0,0.18)"
                        border_color   = "rgba(255,230,0,0.35)"
                    elif sow:
                        detected_label = "Auto-detected: Statement of Work"
                        detected_icon  = "🔍"
                        banner_color   = "#FFE600"
                        glow_color     = "rgba(255,230,0,0.18)"
                        border_color   = "rgba(255,230,0,0.35)"
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
                    banner_color   = "#FFE600"
                    glow_color     = "rgba(255,230,0,0.18)"
                    border_color   = "rgba(255,230,0,0.35)"

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
                      text-shadow: 0 0 12px {banner_color};
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

    # ── Gold banner indicating active page ──
    st.markdown(f"""
    <div class="cv-page-banner">
      <div class="cv-page-banner-icon">📄</div>
      <div>
        <div class="cv-page-banner-label">Contract Viewer</div>
        <div class="cv-page-banner-title">Canonical Analysis</div>
      </div>
      <div class="cv-page-banner-id">{job_id[:8]}…{job_id[-6:]}</div>
    </div>
    """, unsafe_allow_html=True)

    r = api_get(f"/download/{job_id}/canonical")
    if not r or r.status_code != 200:
        st.error("Could not load canonical data. Ensure the job is complete.")
        st.stop()

    canonical = r.json()
    tabs = st.tabs(["📋  Summary", "⚡  Conflicts", "🔍  Missing Fields", "{ }  Raw JSON"])

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
          background:transparent!important;border:1px solid transparent!important;
          color:#444!important;padding:1px 6px!important;font-size:11px!important;
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
                'font-size:10px;font-family:\'DM Mono\',monospace;color:var(--gold);'
                'background:rgba(255,230,0,0.1);border:1px solid rgba(255,230,0,0.2);'
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

            # render_summary_row uses st.columns() internally which Streamlit
            # forbids inside an already-active column context — it silently
            # breaks layout causing vendor content to spill into client's column.
            # Instead: render the display HTML manually and place a standalone
            # edit button underneath each field, staying within one column only.

            def _party_field(party_data, party_key, field_label, field_value, canon_path):
                """Render one field row for a party — no nested st.columns."""
                if not field_value:
                    return
                fk = canon_path
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
                        f'<div style="font-family:\'DM Mono\',monospace;font-size:11px;'
                        f'color:var(--gold);text-transform:uppercase;letter-spacing:0.6px;'
                        f'margin-bottom:4px;">{field_label}</div>',
                        unsafe_allow_html=True,
                    )
                    new_val = st.text_input(
                        field_label, value=str(display),
                        key=f"ei_{fk}", label_visibility="collapsed",
                    )
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
                st.markdown(
                    '<div style="font-size:10px;font-family:\'DM Mono\',monospace;color:var(--text-muted);'
                    'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Client</div>',
                    unsafe_allow_html=True,
                )
                _party_field(client, "client", "Name", client.get("name"), "parties.client.name")
                for si, sig in enumerate(client.get("signatories", [])):
                    if sig.get("name"):
                        sig_val = sig["name"] + (f"  ·  {sig['title']}" if sig.get("title") else "")
                        _party_field(client, "client", f"Signatory {si+1}", sig_val, f"parties.client.signatories.{si}.name")

            with col_v:
                st.markdown(
                    '<div style="font-size:10px;font-family:\'DM Mono\',monospace;color:var(--text-muted);'
                    'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Vendor</div>',
                    unsafe_allow_html=True,
                )
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
                "<div style='font-family:Syne,sans-serif;font-size:13px;font-weight:700;color:#FFE600;'>"
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

            st.markdown(f"""
            <div class="conflict-count-header">
              <div>
                <div class="conflict-count-num">{len(conflicts)} conflict{'s' if len(conflicts) != 1 else ''} found</div>
                <div class="conflict-count-label">Select a value for each conflict you want to override · then regenerate documents below</div>
              </div>
              <div class="conflict-count-icon">⚡</div>
            </div>
            """, unsafe_allow_html=True)

            resolved_count = 0

            for i, conflict in enumerate(conflicts):
                field   = conflict.get("field", f"Conflict {i+1}")
                chosen  = conflict.get("chosen", "—")
                source  = conflict.get("chosenSource", "—")
                alts    = conflict.get("alternatives", [])

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
                # Also store a label→full-value map so the regenerate button can
                # recover the exact value even when the label is truncated at 80 chars.
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

                # Persist map so Regenerate button can look up exact values
                if "conflict_label_values" not in st.session_state:
                    st.session_state.conflict_label_values = {}
                st.session_state.conflict_label_values[field] = label_to_value

                # Header card
                st.markdown(f"""
                <div style="
                    background: var(--surface);
                    border: 1px solid #2a2a2a;
                    border-left: 3px solid rgba(255,230,0,0.5);
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
                    ">Conflict {i+1} of {len(conflicts)}</div>
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

                st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)

            # ── Scroll nudge — appears once at least 1 conflict is resolved ──
            if resolved_count > 0:
                st.markdown(f"""
                <div style="
                    display:flex;
                    align-items:center;
                    gap:12px;
                    background:rgba(255,230,0,0.06);
                    border:1px solid rgba(255,230,0,0.2);
                    border-radius:8px;
                    padding:12px 18px;
                    margin: 8px 0 20px 0;
                    animation: fadeIn 0.4s ease;
                ">
                  <div style="font-size:18px;">👇</div>
                  <div>
                    <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:600;color:var(--gold);">
                        {resolved_count} override{'s' if resolved_count != 1 else ''} ready
                    </div>
                    <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">
                        Scroll down to regenerate your documents with the updated values
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            # ── Regenerate button — always visible, but pulsing when resolves > 0 ──
            st.markdown("""
            <div style="
                border-top:1px solid #222;
                margin: 16px 0 20px 0;
            "></div>
            """, unsafe_allow_html=True)

            regen_label = f"⚡ Regenerate Documents ({resolved_count} override{'s' if resolved_count != 1 else ''})" if resolved_count > 0 else "⚡ Regenerate Documents"

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
                # Build overrides dict to POST to API
                overrides = {}
                for i, conflict in enumerate(conflicts):
                    field        = conflict.get("field", f"Conflict {i+1}")
                    chosen_opt   = st.session_state.conflict_overrides.get(field, "")
                    alts         = conflict.get("alternatives", [])

                    if chosen_opt.startswith("✅ Keep chosen"):
                        continue
                    elif chosen_opt == "✏️ Enter custom value":
                        custom = st.session_state.conflict_custom_text.get(field, "").strip()
                        if custom:
                            overrides[field] = custom
                    else:
                        # Use stored label→value map — avoids substring mismatch on
                        # long values that were truncated in the radio label
                        field_map = st.session_state.get("conflict_label_values", {}).get(field, {})
                        if chosen_opt in field_map:
                            overrides[field] = field_map[chosen_opt]
                        else:
                            # Fallback for short values where full text fits in label
                            for a in alts:
                                raw = str(a.get("value", ""))
                                if raw[:80] in chosen_opt or raw in chosen_opt:
                                    overrides[field] = raw
                                    break

                if not overrides:
                    st.warning("No overrides selected — please choose an alternative or custom value for at least one conflict.")
                else:
                    with st.spinner("Submitting overrides and queuing regeneration…"):
                        try:
                            r = requests.post(
                                f"{API_URL}/jobs/{job_id}/regenerate",
                                headers={"X-API-Key": API_KEY},
                                json={"overrides": overrides},
                            )
                            if r.status_code == 200:
                                new_job_id = r.json().get("job_id", job_id)
                                st.session_state.job_id = new_job_id
                                # Clear override state for fresh run
                                st.session_state.conflict_overrides = {}
                                st.session_state.conflict_custom_text = {}
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
                            border: 1px solid {'rgba(255,230,0,0.25)' if current.strip() else '#2d2d35'};
                            border-left: 3px solid {'var(--gold)' if current.strip() else '#ffcf4c'};
                            border-radius: 8px;
                            padding: 10px 14px 4px 14px;
                            margin-bottom: 4px;
                        ">
                          <div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">
                            <div style="font-size:{'14px' if current.strip() else '13px'};color:{'var(--gold)' if current.strip() else '#ffcf4c'};">
                                {'✅' if current.strip() else '⚠'}
                            </div>
                            <div style="font-size:13px;font-weight:600;color:var(--text);">{item['label']}</div>
                            <div style="font-size:10px;font-family:'DM Mono',monospace;color:var(--text-muted);
                                 background:var(--surface);border:1px solid #2a2a2a;border-radius:4px;
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
                    background:rgba(255,230,0,0.06);
                    border:1px solid rgba(255,230,0,0.2);
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
            st.markdown('<div style="border-top:1px solid #222;margin:16px 0 20px 0;"></div>', unsafe_allow_html=True)

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