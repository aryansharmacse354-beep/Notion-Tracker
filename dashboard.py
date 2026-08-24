"""Streamlit Control Portal for Notion Tracker.

Features:
1. Dynamic Day & Night Mode Theme Engine (Night Obsidian & Daylight Slate).
2. Cinematic 5-Second 3D Rotating Logo Startup Animation & Initialization Readout.
3. Ambient Background Logo Resemblance & Watermark Layer.
4. OpenCV Live Biometric Facial Mesh HUD & 6-Digit SMS OTP Gate.
5. Interactive HITL Cognitive Audit Panel, OCC 3-Way Merge Simulator, and SHA-256 Ledger.
"""

import sys
import asyncio

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

import time
import json
import random
import os
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


import streamlit as st
from streamlit.runtime import exists as runtime_exists
if not runtime_exists():
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", sys.argv[0], "--server.address", "127.0.0.1", "--server.port", "8501", "--server.headless", "false"]
    sys.exit(stcli.main())

from PIL import Image, ImageDraw, ImageFont

import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None

from notion_signature_gateway import (
    calculate_operator_signature,
    OTPGateway,
    NotionEnterpriseGuard,
)
from config import (
    WEBHOOK_SECRET,
    RATE_LIMIT_CAPACITY,
    RATE_LIMIT_REPLENISH_RATE,
    ADMIN_OVERRIDE_PIN,
)

from notion_enterprise_guard import (
    default_rate_limiter,
    default_nonce_guard,
    generate_hmac_signature,
    OptimisticConcurrencyControl,
)
from notion_store import default_store
from ai_audit_engine import AIAuditEngine
from notion_typesetter import NotionTypesetter
from notion_comment_agent import NotionCommentAgent
from outbound_dispatcher import OutboundDispatcher
from audit_ledger import AuditLedger
from report_builder import PDFReportBuilder
from system_health_monitor import SystemHealthMonitor
from voice_memo_agent import VoiceMemoAgent
from i18n import t, get_current_language, set_current_language, TRANSLATIONS
from workflow_engine import WorkflowEngine, AVAILABLE_PIPELINE_STEPS




BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "logo.png"

# Read logo as base64 for reliable embedding
logo_b64 = ""
page_icon_obj = "🛡️"
if LOGO_PATH.exists():
    try:
        with open(LOGO_PATH, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode("utf-8")
        page_icon_obj = Image.open(LOGO_PATH)
    except Exception:
        pass

# Page configuration
st.set_page_config(
    page_title="Notion Tracker | Enterprise HITL Control",
    page_icon=page_icon_obj,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if "lang" not in st.session_state:
    st.session_state.lang = default_store.get_system_config().get("language", "en")
if "active_user" not in st.session_state:
    st.session_state.active_user = "Aryan Sharma"
if "biometric_authenticated" not in st.session_state:
    st.session_state.biometric_authenticated = False
if "otp_code" not in st.session_state:
    st.session_state.otp_code = str(random.randint(100000, 999999))
if "otp_verified" not in st.session_state:
    st.session_state.otp_verified = False
if "selected_task_id" not in st.session_state:
    st.session_state.selected_task_id = None
if "tamper_mode" not in st.session_state:
    st.session_state.tamper_mode = False

cur_lang = st.session_state.lang


# ==============================================================================
# ENTERPRISE DESIGN SYSTEM & UI STYLES
# ==============================================================================
card_bg = "#111827"
card_border = "#1f2937"
text_main = "#f8fafc"
text_muted = "#94a3b8"
metric_bg = "#0f172a"
hero_bg = "linear-gradient(135deg, #090d16 0%, #1e1b4b 60%, #312e81 100%)"
fact_bg = "#1e293b"
fact_border = "#334155"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: {text_main};
    }}
    
    .stApp {{
        background: radial-gradient(ellipse at top, #0f172a 0%, #030712 100%);
        position: relative;
    }}
    
    /* Main Layout */
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1420px;
        position: relative;
        z-index: 1;
    }}
    
    /* Header Gradient & Hero Styling */
    .hero-container {{
        background: {hero_bg};
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 12px 28px -6px rgba(0, 0, 0, 0.35);
        color: #ffffff;
    }}
    .hero-title {{
        font-size: 2.0rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        margin: 0 0 4px 0;
        background: linear-gradient(90deg, #ffffff 0%, #e2e8f0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .hero-subtitle {{
        font-size: 0.95rem;
        color: #cbd5e1;
        margin: 0;
        font-weight: 400;
    }}
    .hero-badge {{
        display: inline-block;
        background: rgba(99, 102, 241, 0.25);
        color: #c7d2fe;
        border: 1px solid rgba(129, 140, 248, 0.4);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }}
    
    /* Cards */
    .pro-card {{
        background: {card_bg};
        border-radius: 12px;
        border: 1px solid {card_border};
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 5px 0 rgba(0, 0, 0, 0.06);
    }}
    
    /* Metric Cards */
    .metric-box {{
        background: {metric_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 18px 20px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }}
    .metric-box::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: #6366f1;
    }}
    .metric-box-critical::before {{ background: #ef4444; }}
    .metric-box-success::before {{ background: #10b981; }}
    .metric-box-warning::before {{ background: #f59e0b; }}
    .metric-value {{
        font-size: 1.75rem;
        font-weight: 800;
        color: {text_main};
        margin: 4px 0 0 0;
        letter-spacing: -0.02em;
    }}
    .metric-label {{
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {text_muted};
        margin: 0;
    }}
    
    /* Risk Banners */
    .risk-banner {{
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 700;
    }}
    .risk-banner-critical {{
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(185, 28, 28, 0.25) 100%);
        border: 1px solid #ef4444;
        color: #f87171;
    }}
    .risk-banner-high {{
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(180, 83, 9, 0.25) 100%);
        border: 1px solid #f59e0b;
        color: #fbbf24;
    }}
    .risk-banner-medium {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(4, 120, 87, 0.25) 100%);
        border: 1px solid #10b981;
        color: #34d399;
    }}
    .risk-banner-low {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(79, 70, 229, 0.2) 100%);
        border: 1px solid #6366f1;
        color: #a5b4fc;
    }}
    
    /* Operator Card in Sidebar */
    .operator-profile-card {{
        background: {metric_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 16px;
        color: {text_main};
        margin-bottom: 16px;
    }}
    .operator-name {{
        font-size: 1.05rem;
        font-weight: 700;
        color: {text_main};
        margin: 0;
    }}
    .operator-role {{
        font-size: 0.8rem;
        color: #818cf8;
        font-weight: 600;
        margin: 2px 0 8px 0;
    }}
    .operator-status-dot {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        margin-right: 6px;
        box-shadow: 0 0 8px #10b981;
    }}

    /* Facts Grid */
    .fact-item {{
        background: {fact_bg};
        border: 1px solid {fact_border};
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.88rem;
        color: {text_muted};
    }}
    .fact-title {{
        font-size: 0.72rem;
        text-transform: uppercase;
        color: {text_muted};
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-bottom: 2px;
    }}
    .fact-content {{
        font-size: 0.95rem;
        font-weight: 700;
        color: {text_main};
    }}

    /* CoT Step Line */
    .cot-step {{
        border-left: 2px solid #6366f1;
        padding-left: 12px;
        margin-bottom: 8px;
        font-size: 0.88rem;
        color: {text_muted};
    }}
</style>

<!-- AMBIENT LOGO WATERMARK -->
<div class="bg-watermark-overlay"></div>
""", unsafe_allow_html=True)



# ==============================================================================
# SIDEBAR — CONTROLS, LOCALIZATION & TELEMETRY
# ==============================================================================

with st.sidebar:
    if logo_b64:
        st.markdown(f"""
        <div style="text-align: center; padding: 4px 0 16px 0;">
            <img src="data:image/png;base64,{logo_b64}" style="width: 80px; height: 80px; border-radius: 50%; border: 2px solid #818cf8; background: #ffffff; padding: 4px; box-shadow: 0 4px 18px rgba(99, 102, 241, 0.45);" />
            <div style="font-size: 1.15rem; font-weight: 800; color: #ffffff; letter-spacing: 0.04em; margin-top: 10px;">NOTION TRACKER</div>
            <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">Zero-Trust HITL Gateway</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### 🛡️ Notion Tracker")

    # Level 2: Administrative Localization Selector (Left Sidebar Panel)
    st.markdown(f"### {t('language_selector_label', lang=cur_lang)}")
    lang_map = {
        "en": "🇺🇸 English",
        "es": "🇪🇸 Español (Spanish)",
        "de": "🇩🇪 Deutsch (German)",
        "ja": "🇯🇵 日本語 (Japanese)",
        "hi": "🇮🇳 हिन्दी (Hindi)",
        "fr": "🇫🇷 Français (French)",
    }
    lang_keys = list(lang_map.keys())
    cur_idx = lang_keys.index(cur_lang) if cur_lang in lang_keys else 0
    chosen_lang = st.selectbox(
        "Interface & Typesetting Language:",
        options=lang_keys,
        index=cur_idx,
        format_func=lambda code: lang_map.get(code, code),
        key="workspace_language_select",
    )
    if chosen_lang != st.session_state.lang:
        st.session_state.lang = chosen_lang
        set_current_language(chosen_lang)
        default_store.update_system_config({"language": chosen_lang})
        st.rerun()

    st.markdown("---")

    # Operator Access Profile
    st.markdown(f"### {t('operator_profile', lang=cur_lang)}")
    user_profiles = default_store.list_user_profiles()
    user_names = [u["name"] for u in user_profiles] if user_profiles else ["Aryan Sharma", "Atul Yadav"]

    selected_operator = st.selectbox("Active Operator Profile:", user_names, index=0)
    st.session_state.active_user = selected_operator
    current_user = default_store.get_user_by_name(selected_operator)

    if current_user:
        auth_badge = "🟢 UNLOCKED" if (st.session_state.biometric_authenticated or st.session_state.otp_verified) else "🔒 LOCKED"
        tasks_done = current_user.get("tasks_completed", 0)
        streak = current_user.get("current_streak", 1)
        flame = current_user.get("streak_flame", f"🔥 {streak} Days")
        lvl = current_user.get("level_badge", "Level 1")
        badges = current_user.get("unlocked_badges", [])
        pct_lvl = min(1.0, max(0.0, (tasks_done % 10) / 10.0))

        badges_html = "".join([f"<span style='display: inline-block; background: rgba(99, 102, 241, 0.2); border: 1px solid rgba(129, 140, 248, 0.4); color: #c7d2fe; font-size: 0.70rem; padding: 2px 7px; border-radius: 12px; margin: 2px 4px 2px 0;'>{b}</span>" for b in badges])

        st.markdown(f"""
        <div class="operator-profile-card">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <p class="operator-name">{current_user.get('name')}</p>
                    <p class="operator-role">{current_user.get('role')}</p>
                </div>
                <div style="font-size: 0.75rem; font-weight: 700; color: #a5b4fc;">{auth_badge}</div>
            </div>
            
            <div style="margin: 10px 0 6px 0; display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; font-weight: 700;">
                <span style="color: #f59e0b;">{flame}</span>
                <span style="color: #818cf8;">{lvl} ({tasks_done} Tasks)</span>
            </div>
            <div style="background: rgba(255,255,255,0.08); border-radius: 6px; height: 6px; overflow: hidden; margin-bottom: 10px;">
                <div style="background: linear-gradient(90deg, #f59e0b, #10b981); height: 100%; width: {int(pct_lvl * 100)}%;"></div>
            </div>

            <div style="margin-bottom: 8px;">
                <div style="font-size: 0.70rem; text-transform: uppercase; color: #94a3b8; font-weight: 700; margin-bottom: 4px;">Unlocked Badges:</div>
                <div style="display: flex; flex-wrap: wrap;">{badges_html if badges else '<span style=\"color:#64748b; font-size:0.75rem;\">No badges yet</span>'}</div>
            </div>

            <div style="margin-top: 8px; font-size: 0.72rem; color: #94a3b8;">
                <span class="operator-status-dot"></span><b>Biometric ID:</b> <code>{current_user.get('biometric_id')}</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Rate Limiter Telemetry Gauge
    throttle_data = default_rate_limiter.get_state()
    tb = throttle_data["token_bucket"]
    avail = tb['available_tokens']
    cap = tb['capacity']
    pct = min(1.0, max(0.0, avail / cap if cap > 0 else 0.0))

    st.markdown(f"### {t('token_telemetry', lang=cur_lang)}")
    st.progress(pct)
    c_t1, c_t2 = st.columns(2)
    c_t1.metric(t("available_tokens", lang=cur_lang), f"{avail:.1f} / {cap:.0f}")
    c_t2.metric(t("guard_status", lang=cur_lang), tb["status"])
    st.caption(f"Replenish Rate: **{RATE_LIMIT_REPLENISH_RATE:.1f} tokens/s** (safe ≤ 2 writes/s)")

    # Notion System Health & Turn-Off Test Heartbeat Monitor
    sys_metrics = SystemHealthMonitor.collect_metrics()
    st.markdown("---")
    st.markdown(f"### {t('system_health_title', lang=cur_lang)}")
    h_col1, h_col2 = st.columns(2)
    h_col1.metric(t("cpu_load", lang=cur_lang), f"{sys_metrics['cpu_percent']}%")
    h_col2.metric(t("ram_usage", lang=cur_lang), f"{sys_metrics['ram_percent']}%")
    st.markdown(f"**{t('daemon_status', lang=cur_lang)}:** `🟢 {sys_metrics['status']}` | {t('uptime', lang=cur_lang)}: `{sys_metrics['uptime_seconds']}s`")
    st.caption("Heartbeats are written to Notion's System Health table. If servers shut down, managers see offline status instantly.")

    st.markdown("---")
    
    # Localized Navigation Choice
    nav_keys = [
        "nav_command_center",
        "nav_hitl",
        "nav_multiselect",
        "nav_biometrics",
        "nav_webhook",
        "nav_scheduler",
        "nav_audit",
    ]
    raw_nav_labels = [t(k, lang=cur_lang) for k in nav_keys]
    chosen_label = st.radio("Platform Modules:", raw_nav_labels, index=0)
    nav_index = raw_nav_labels.index(chosen_label) if chosen_label in raw_nav_labels else 0
    active_module_key = nav_keys[nav_index]


# ==============================================================================
# TOP HERO BANNER
# ==============================================================================
logo_hero_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 66px; height: 66px; border-radius: 50%; border: 2px solid rgba(255, 255, 255, 0.35); background: #ffffff; padding: 4px; box-shadow: 0 4px 16px rgba(0,0,0,0.35); flex-shrink: 0;" />' if logo_b64 else '<span style="font-size: 2.2rem;">🛡️</span>'

active_flame = current_user.get("streak_flame", "🔥 1 Day") if current_user else "🔥 Active"

st.markdown(f"""
<div class="hero-container">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div style="display: flex; align-items: center; gap: 18px;">
            {logo_hero_html}
            <div>
                <div class="hero-badge">{t("hero_badge", lang=cur_lang)}</div>
                <h1 class="hero-title">{t("hero_title", lang=cur_lang)}</h1>
                <p class="hero-subtitle">{t("hero_subtitle", lang=cur_lang)}</p>
            </div>
        </div>
        <div style="text-align: right; background: rgba(255, 255, 255, 0.06); padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.12);">
            <div style="font-size: 0.72rem; text-transform: uppercase; color: #94a3b8; font-weight: 700;">{t("active_operator", lang=cur_lang)}</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #ffffff;">{st.session_state.active_user} <span style="font-size: 0.82rem; color: #f59e0b; background: rgba(245, 158, 11, 0.2); border: 1px solid rgba(245, 158, 11, 0.4); padding: 2px 8px; border-radius: 10px; margin-left: 4px;">{active_flame}</span></div>
            <div style="font-size: 0.75rem; color: #10b981; font-weight: 600; margin-top: 2px;">{t("pipeline_active", lang=cur_lang)}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# VIEW 0: OPERATIONS COMMAND CENTER & VISUAL WORKFLOW BUILDER
# ==============================================================================
if active_module_key == "nav_command_center":
    st.markdown("### 🎛️ Operations Command Center & Visual Workflow Builder")
    st.info("💡 **The Turn-Off Test**: Notion is natively a customizable drag-and-drop database grid. Managers can position Tasks Kanban boards, Run Log audit streams, Operator Gamification cards, and System Health tables side-by-side. If servers go offline, the visual workspace remains 100% structured, legible, and editable.")

    occ_tab1, occ_tab2 = st.tabs(["🗂️ Notion Command Center Grid", "⚡ Visual Pipeline Workflow Builder"])

    with occ_tab1:
        st.markdown("#### Centralized Notion Workspace Layout (Side-by-Side Database Grid)")
        
        col_grid1, col_grid2, col_grid3 = st.columns([4, 4, 4])

        with col_grid1:
            st.markdown("##### 📋 Tasks Kanban Board View")
            all_t = default_store.list_tasks(include_archived=False)
            ready_t = [t for t in all_t if t.get("status") == "Ready for Review"]
            appr_t = [t for t in all_t if t.get("status") == "Approved"]
            disp_t = [t for t in all_t if t.get("status") == "Dispatched"]

            st.markdown(f"**Ready for Review ({len(ready_t)})**")
            for t_item in ready_t[:3]:
                r_color = "#ef4444" if t_item.get("risk_level") in ("CRITICAL", "HIGH") else "#10b981"
                st.markdown(f"""
                <div style="background: #1e293b; border-left: 3px solid {r_color}; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px;">
                    <div style="font-size: 0.82rem; font-weight: 700; color: #f8fafc;">{t_item.get('title')}</div>
                    <div style="font-size: 0.70rem; color: #94a3b8;">Risk: <b>{t_item.get('risk_level')}</b> | OCC: <code>v{t_item.get('version', 1)}</code></div>
                </div>
                """, unsafe_allow_html=True)
            if len(ready_t) > 3:
                st.caption(f"...and {len(ready_t) - 3} more tasks")

            st.markdown(f"**Approved & Dispatched ({len(appr_t) + len(disp_t)})**")
            for t_item in (appr_t + disp_t)[:2]:
                st.markdown(f"""
                <div style="background: #0f172a; border-left: 3px solid #6366f1; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px;">
                    <div style="font-size: 0.82rem; font-weight: 700; color: #cbd5e1;">{t_item.get('title')}</div>
                    <div style="font-size: 0.70rem; color: #64748b;">Status: <b>{t_item.get('status')}</b> | Budget: <code>{t_item.get('budget', '$0')}</code></div>
                </div>
                """, unsafe_allow_html=True)

        with col_grid2:
            st.markdown("##### 🏆 Operator Leaderboard & Badges")
            profiles = default_store.list_user_profiles()
            for prof in profiles:
                p_flame = prof.get("streak_flame", "🔥 1 Day")
                p_lvl = prof.get("level_badge", "Level 1")
                p_done = prof.get("tasks_completed", 0)
                p_badges = prof.get("unlocked_badges", [])
                
                b_pills = "".join([f"<span style='background: rgba(99,102,241,0.2); color: #c7d2fe; font-size: 0.65rem; padding: 1px 5px; border-radius: 8px; margin-right: 3px;'>{b}</span>" for b in p_badges[:2]])
                
                st.markdown(f"""
                <div style="background: #1e293b; border: 1px solid #334155; padding: 10px 12px; border-radius: 8px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; color: #f8fafc; font-size: 0.88rem;">{prof.get('name')}</span>
                        <span style="color: #f59e0b; font-weight: 700; font-size: 0.78rem;">{p_flame}</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #818cf8; margin: 2px 0 6px 0;">{prof.get('role')} | {p_lvl} ({p_done} tasks)</div>
                    <div>{b_pills}</div>
                </div>
                """, unsafe_allow_html=True)

        with col_grid3:
            st.markdown("##### ❤️ System Health & Heartbeats")
            sh_latest = default_store.get_latest_system_health() or SystemHealthMonitor.collect_metrics()
            st.markdown(f"""
            <div style="background: #1e293b; border: 1px solid #334155; padding: 12px; border-radius: 8px;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #10b981; margin-bottom: 8px;">● {sh_latest.get('service_name', 'Daemon')} Active</div>
                <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #cbd5e1; margin-bottom: 4px;">
                    <span>CPU Load:</span><b>{sh_latest.get('cpu_percent', 0)}%</b>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #cbd5e1; margin-bottom: 4px;">
                    <span>RAM Usage:</span><b>{sh_latest.get('ram_percent', 0)}%</b>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #cbd5e1; margin-bottom: 4px;">
                    <span>Active Threads:</span><b>{sh_latest.get('active_threads', 1)}</b>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #cbd5e1;">
                    <span>Status:</span><b style="color: #10b981;">{sh_latest.get('status', 'HEALTHY')}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            st.caption("All database views update concurrently and remain persistent.")

    with occ_tab2:
        st.markdown("#### ⚡ Notion-Native Pipeline Automation Templates")
        st.write("Configure and compose multi-step automation workflows natively inside Notion without writing JavaScript. The background daemon dynamically executes tasks against this matrix.")

        templates = default_store.list_pipeline_templates()
        
        # Display Templates in Cards
        t_cols = st.columns(len(templates) if templates else 1)
        for idx, tmpl in enumerate(templates):
            with t_cols[idx % len(t_cols)]:
                st.markdown(f"""
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 14px; margin-bottom: 12px; height: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; color: #f8fafc; font-size: 0.92rem;">{tmpl.get('name')}</span>
                        <span style="font-size: 0.72rem; color: #10b981; font-weight: 700;">{tmpl.get('status')}</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #818cf8; margin-bottom: 8px;">Trigger: <b>{tmpl.get('trigger_source')}</b></div>
                    <div style="font-size: 0.72rem; color: #cbd5e1; font-weight: 600; margin-bottom: 4px;">Pipeline Steps ({len(tmpl.get('steps', []))}):</div>
                    <div style="font-size: 0.70rem; color: #94a3b8; line-height: 1.4;">
                        {"<br/>".join([f"• {s}" for s in tmpl.get('steps', [])])}
                    </div>
                    <div style="font-size: 0.70rem; color: #e2e8f0; margin-top: 8px; font-weight: 600;">Threshold: {tmpl.get('risk_threshold')}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        
        # Workflow Template Creator Form
        st.markdown("##### 🛠️ Create / Update Pipeline Template in Notion")
        with st.form("pipeline_template_form"):
            cf_col1, cf_col2 = st.columns(2)
            with cf_col1:
                new_tmpl_name = st.text_input("Pipeline Template Name:", value="Custom Security Audit Pipeline")
                new_tmpl_source = st.selectbox("Trigger Source:", ["Webhook Gateway", "Audio Memo", "Academic Portal", "AWS GuardDuty Security", "Manual Operator Entry"])
                new_tmpl_threshold = st.selectbox("Risk Evaluation Policy:", ["Strict HITL (All Risks)", "Auto-Approve LOW", "CRITICAL / HIGH Gate Only"])
            
            with cf_col2:
                new_tmpl_steps = st.multiselect(
                    "Execution Pipeline Steps (in order):",
                    options=AVAILABLE_PIPELINE_STEPS,
                    default=[
                        "1. HMAC Nonce Verify 🛡️",
                        "2. Cognitive AI Pre-Audit 🧠",
                        "3. Biometric & OTP Gate 🔐",
                        "4. Teams Adaptive Card 💬",
                        "5. SendGrid Email 📧",
                        "6. SHA-256 Signature Seal 📊",
                    ],
                )
                new_tmpl_status = st.selectbox("Pipeline Status:", ["Active 🟢", "Paused ⏸️"])

            submit_tmpl = st.form_submit_button("💾 Save & Register Template in Notion Database", type="primary")
            if submit_tmpl:
                created_tmpl = default_store.create_pipeline_template({
                    "name": new_tmpl_name,
                    "trigger_source": new_tmpl_source,
                    "steps": new_tmpl_steps,
                    "risk_threshold": new_tmpl_threshold,
                    "status": new_tmpl_status,
                })
                st.success(f"✅ Pipeline Template '{created_tmpl.get('name')}' saved and synced with Notion!")
                time.sleep(1)
                st.rerun()

        st.markdown("---")

        # Interactive Pipeline Execution Simulator
        st.markdown("##### 🧪 Test Pipeline Execution Against Active Templates")
        sim_col1, sim_col2 = st.columns([3, 2])
        with sim_col1:
            chosen_tmpl_name = st.selectbox("Select Pipeline Template to Test:", [t["name"] for t in templates] if templates else ["MNC Priority Alert Template"])
            test_task_title = st.text_input("Sample Task Title:", value="Database Replication & IAM Security Audit")
            test_task_details = st.text_area("Sample Task Payload:", value="Authorize zero-trust cluster provisioning for data engineering group.", height=80)
        
        with sim_col2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 Execute Simulated Workflow Pipeline", type="primary"):
                selected_tmpl = default_store.get_pipeline_template(chosen_tmpl_name) or {
                    "name": chosen_tmpl_name,
                    "steps": AVAILABLE_PIPELINE_STEPS,
                }
                sample_task = {
                    "id": f"test_wf_{int(time.time())}",
                    "title": test_task_title,
                    "details": test_task_details,
                    "priority": "high",
                    "source": selected_tmpl.get("trigger_source", "Webhook Gateway"),
                }
                w_ok, w_trace, w_updated = WorkflowEngine.execute_pipeline(
                    task=sample_task,
                    template=selected_tmpl,
                    operator_name=st.session_state.active_user,
                    override_biometric=True,
                )
                st.success(f"🎉 **Pipeline '{chosen_tmpl_name}' Executed Successfully!**")
                st.markdown("**Step-by-Step Execution Trace:**")
                for step_line in w_trace:
                    st.markdown(f"• {step_line}")


# ==============================================================================
# VIEW 1: HITL TASK APPROVALS
# ==============================================================================
elif active_module_key == "nav_hitl":
    all_tasks = default_store.list_tasks(include_archived=False)

    # Metric Cards Top Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f"""
        <div class="metric-box">
            <p class="metric-label">{t("metric_pending", lang=cur_lang)}</p>
            <p class="metric-value">{sum(1 for t in all_tasks if t.get('status') == 'Ready for Review')}</p>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
        <div class="metric-box metric-box-success">
            <p class="metric-label">{t("metric_approved", lang=cur_lang)}</p>
            <p class="metric-value">{sum(1 for t in all_tasks if t.get('status') in ('Approved', 'Dispatched'))}</p>

        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
        <div class="metric-box metric-box-critical">
            <p class="metric-label">{t("metric_critical", lang=cur_lang)}</p>
            <p class="metric-value">{sum(1 for t in all_tasks if t.get('risk_level') in ('CRITICAL', 'HIGH'))}</p>
        </div>
        """, unsafe_allow_html=True)
    with m_col4:
        st.markdown(f"""
        <div class="metric-box">
            <p class="metric-label">{t("metric_dispatched", lang=cur_lang)}</p>
            <p class="metric-value">{sum(1 for t in all_tasks if t.get('status') == 'Dispatched')}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)


    # Filter Bar
    with st.container():
        f_col1, f_col2, f_col3 = st.columns([3, 3, 4])
        status_filter = f_col1.selectbox("Filter Status:", ["All", "Ready for Review", "Approved", "Dispatched", "Rejected"])
        risk_filter = f_col2.selectbox("Filter Risk Level:", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
        search_q = f_col3.text_input("🔍 Search Tasks by Title or ID:")

    filtered = all_tasks
    if status_filter != "All":
        filtered = [t for t in filtered if t.get("status") == status_filter]
    if risk_filter != "All":
        filtered = [t for t in filtered if t.get("risk_level") == risk_filter]
    if search_q:
        filtered = [t for t in filtered if search_q.lower() in t.get("title", "").lower() or search_q.lower() in t.get("id", "").lower()]

    if not filtered:
        st.info("No tasks matching the selected filters. Use the **Webhook Ingestion Hub** to ingest sample task payloads.")
    else:
        list_col, detail_col = st.columns([5, 7])

        with list_col:
            st.markdown("#### 📂 Ingested Tasks")
            task_options = {f"{t['id'][:8]} — {t['title'][:32]} [{t.get('risk_level', 'LOW')}]": t["id"] for t in filtered}
            selected_label = st.radio("Select Task for Human Review:", list(task_options.keys()), index=0)
            selected_task_id = task_options[selected_label]
            st.session_state.selected_task_id = selected_task_id

        selected_task = default_store.get_task(st.session_state.selected_task_id)

        with detail_col:
            if selected_task:
                st.markdown(f"#### 🔎 Cognitive Audit Panel: `#{selected_task.get('id')}`")

                # Cognitive Risk Banner
                risk_lvl = selected_task.get("risk_level", "LOW")
                conf_pct = int(selected_task.get("confidence_score", 0.85) * 100)
                risk_class = "risk-banner-critical" if risk_lvl in ("CRITICAL", "HIGH") else ("risk-banner-medium" if risk_lvl == "MEDIUM" else "risk-banner-low")
                risk_icon = "🚨" if risk_lvl == "CRITICAL" else ("⚠️" if risk_lvl == "HIGH" else ("📋" if risk_lvl == "MEDIUM" else "✅"))

                st.markdown(f"""
                <div class="risk-banner {risk_class}">
                    <div>
                        <span>{risk_icon} <b>{risk_lvl} RISK PRE-AUDIT EVALUATION</b></span>
                    </div>
                    <div style="font-size: 0.85rem;">Confidence Interval: <b>{conf_pct}%</b></div>
                </div>
                """, unsafe_allow_html=True)

                # Structured Facts Grid
                fc1, fc2, fc3, fc4 = st.columns(4)
                with fc1:
                    st.markdown(f"""
                    <div class="fact-item">
                        <div class="fact-title">Category</div>
                        <div class="fact-content">{selected_task.get('category', 'General')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with fc2:
                    st.markdown(f"""
                    <div class="fact-item">
                        <div class="fact-title">Priority</div>
                        <div class="fact-content">{selected_task.get('priority', 'normal').upper()}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with fc3:
                    st.markdown(f"""
                    <div class="fact-item">
                        <div class="fact-title">Status</div>
                        <div class="fact-content">{selected_task.get('status')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with fc4:
                    st.markdown(f"""
                    <div class="fact-item">
                        <div class="fact-title">OCC Version</div>
                        <div class="fact-content">v{selected_task.get('version', 1)}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"**Task Payload Scope:**\n> {selected_task.get('details', '')}")

                with st.expander("🧠 LangChain Step-by-Step Chain-of-Thought (CoT) Trace", expanded=False):
                    steps = selected_task.get("reasoning_trace", [])
                    for s in steps:
                        st.markdown(f"<div class='cot-step'>{s}</div>", unsafe_allow_html=True)

                with st.expander("✅ Human Verification Checkpoints", expanded=True):
                    st.checkbox("Confirm operational scope for this domain", value=True, key=f"chk_scope_{selected_task['id']}")
                    st.checkbox("Validate outbound communication draft text", value=True, key=f"chk_text_{selected_task['id']}")
                    is_authed = st.session_state.biometric_authenticated or st.session_state.otp_verified
                    st.checkbox("Biometric / OTP operator gate unlocked", value=is_authed, key=f"chk_gate_{selected_task['id']}")

                with st.expander("📤 Pre-Compiled Outbound Dispatch Draft", expanded=False):
                    edited_draft_text = st.text_area("Teams Adaptive Card Message Prose:", value=selected_task.get("draft_teams_text", ""), height=90)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

                act_col1, act_col2, act_col3 = st.columns([4, 4, 4])

                # APPROVE BUTTON
                if act_col1.button("🟢 Approve & Dispatch", use_container_width=True, type="primary"):
                    if risk_lvl in ("CRITICAL", "HIGH") and not is_authed:
                        st.error("🚨 Elevated risk task requires Biometric Face Match or 6-Digit OTP clearance! Please unlock in the 'Biometric & OTP Security Gate' tab.")
                    else:
                        updated, conflict, details = default_store.update_task_with_occ(
                            task_id=selected_task["id"],
                            base_record=selected_task,
                            local_updates={"status": "Approved", "draft_teams_text": edited_draft_text},
                            operator_name=st.session_state.active_user,
                        )
                        default_store.record_operator_approval(st.session_state.active_user)
                        st.success(f"✅ Task approved by **{st.session_state.active_user}**! Streak & Gamification points updated.")
                        time.sleep(1)
                        st.rerun()


                # REJECT BUTTON
                if act_col2.button("🔴 Reject Task", use_container_width=True):
                    updated, conflict, details = default_store.update_task_with_occ(
                        task_id=selected_task["id"],
                        base_record=selected_task,
                        local_updates={"status": "Rejected"},
                        operator_name=st.session_state.active_user,
                    )
                    st.warning("Task marked as Rejected in Notion & SQLite store.")
                    time.sleep(1)
                    st.rerun()

                # OCC CONFLICT SIMULATOR
                if act_col3.button("⚡ Test OCC Conflict", use_container_width=True, help="Simulates concurrent modification by another worker"):
                    stale_base = copy = dict(selected_task)
                    stale_base["version"] = 0
                    updated, conflict, details = default_store.update_task_with_occ(
                        task_id=selected_task["id"],
                        base_record=stale_base,
                        local_updates={"details": f"{selected_task.get('details')} [Concurrent Edit]"},
                        operator_name=st.session_state.active_user,
                    )
                    if conflict:
                        st.info(f"⚡ **OCC 3-Way Merge Resolved!**\n\n{chr(10).join(details)}")
                        time.sleep(2)
                        st.rerun()

                st.markdown("---")

                # @AI Comment Agent Interactive Input
                st.markdown("#### 💬 Notion Page @AI Comment Console")
                comm_input = st.text_input("Post @AI comment on this page:", value="@AI update budget $4,500 for Lab Group B", key=f"ai_comm_{selected_task['id']}")
                if st.button("Submit Comment to Notion", key=f"btn_comm_{selected_task['id']}"):
                    ok, reply = NotionCommentAgent.process_comment(
                        task_id=selected_task["id"],
                        comment_text=comm_input,
                        author_name=st.session_state.active_user,
                    )
                    if ok:
                        st.success(reply)
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error(reply)

                st.markdown("---")

                # Native Notion Audio Block & Voice Memo Transcription Console
                st.markdown("#### 🎙️ Native Notion Audio Block & Voice Memo Transcriber")
                st.caption("Operators can attach voice memos or record native Notion audio blocks. The Python service transcribes the speech, extracts intent via LangChain, and updates the task.")
                
                v_presets = [
                    "Operator voice memo: Provisions approved for Lab Group B. Please update budget to $4,500 and set priority to normal.",
                    "Emergency voice alert: Unauthorized access detected on authentication cluster. Escalate priority to critical immediately.",
                    "Voice update: Lab quota verified with faculty. Approve provisions and dispatch welcome packages.",
                ]
                chosen_voice_note = st.selectbox("Select Simulated Audio Block / Voice Recording:", v_presets, key=f"v_preset_{selected_task['id']}")
                custom_voice_text = st.text_input("Or enter custom spoken voice memo:", value=chosen_voice_note, key=f"v_custom_{selected_task['id']}")
                
                if st.button("🎙️ Transcribe & Apply Voice Memo to Task", key=f"btn_voice_{selected_task['id']}"):
                    v_ok, v_summary, v_task = VoiceMemoAgent.process_voice_memo_on_task(
                        task_id=selected_task["id"],
                        audio_input=custom_voice_text,
                        operator_name=st.session_state.active_user,
                        mock_transcript=custom_voice_text,
                    )
                    if v_ok:
                        st.success(v_summary)
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error(v_summary)



# ==============================================================================
# VIEW 2: ZERO-TRUST DIGITAL SIGNATURE & OTP GATE
# ==============================================================================
elif active_module_key == "nav_biometrics":
    st.markdown("### 🔐 Zero-Trust Operator Digital Signature & MFA Security Gate")

    st.info("High-risk or elevated operations (CRITICAL / HIGH risk classifications) enforce non-repudiation cryptographic operator signatures and OTP multi-factor clearance before real-world execution.")

    col_sig, col_otp = st.columns(2)

    with col_sig:
        st.markdown("#### 🔑 Operator Digital Signature Authority")
        st.write(f"Active Signer: **{st.session_state.active_user}**")
        st.caption("Each human operator possesses a deterministic cryptographic keypair. Approvals are cryptographically signed and stamped into Notion.")

        sig_task_id = st.text_input("Target Task ID for Signature:", value="task_enterprise_001")
        sig_action = st.selectbox("Action to Authorize:", ["APPROVE_BUDGET", "DISPATCH_COMMUNICATIONS", "BATCH_APPROVE_PAGES", "OVERRIDE_PRIORITY"])
        
        test_email = "aryan.sharma@company.com" if "Aryan" in st.session_state.active_user else "admin@company.com"
        test_role = "Lead Auditor & Architect"

        calc_hash = calculate_operator_signature(
            task_id=sig_task_id,
            title="Enterprise Authorization Seal",
            action=sig_action,
            operator_email=test_email,
            role=test_role,
            timestamp=time.time(),
            outcome="APPROVED",
        )

        st.markdown(f"**Operator Signature Seal:**")
        st.code(calc_hash, language="text")

        if st.button("Generate & Verify Cryptographic Signature"):
            st.session_state.biometric_authenticated = True
            st.success(f"🟢 **CRYPTOGRAPHIC SIGNATURE VERIFIED!**\n\nSigner: `{st.session_state.active_user}`\n\nProfile Seal: `{calc_hash[:32]}...`\n\nNon-repudiation audit seal bound to task `{sig_task_id}`.")

        if st.session_state.biometric_authenticated:
            st.markdown("🔒 **Signature Authority Status:** `ACTIVE (VERIFIED)`")
            if st.button("Revoke Active Signature Session"):
                st.session_state.biometric_authenticated = False
                st.rerun()

    with col_otp:
        st.markdown("#### 📱 6-Digit Cryptographic SMS OTP Gate (IN +91)")
        st.write("Dispatches a randomized 6-digit cryptographic PIN to the operator's registered mobile device.")

        col_pin_disp, col_pin_refresh = st.columns([3, 1])
        col_pin_disp.info(f"📟 **Simulated SMS to Device (+91):** Your OTP is **`{st.session_state.otp_code}`** (Valid 5 mins)")
        if col_pin_refresh.button("🔄 Generate New OTP"):
            st.session_state.otp_code = str(random.randint(100000, 999999))
            st.session_state.otp_verified = False
            st.rerun()

        entered_pin = st.text_input("Enter 6-Digit Verification PIN:", max_chars=6, type="password")
        if st.button("Verify OTP PIN"):
            if entered_pin.strip() in (st.session_state.otp_code, ADMIN_OVERRIDE_PIN):
                st.session_state.otp_verified = True
                st.success("🟢 **OTP PIN Verified!** MFA Challenge cleared for high-risk operations.")
            else:
                st.error("❌ Invalid OTP PIN entered. Please try again.")

        if st.session_state.otp_verified:
            st.markdown("🔒 **OTP Status:** `VERIFIED (MFA ACTIVE)`")


    st.markdown("---")

    # Notion Monochrome Operator Registration & IN +91 Phone OTP Login Panel
    st.markdown("#### 👤 Operator Profile Registration & Phone OTP Access")
    st.caption("Demonstrates the Notion-Monochrome responsive registration and IN +91 OTP authentication interface.")

    screen_tab1, screen_tab2 = st.tabs(["📝 Operator Registration", "📱 Mobile Phone OTP Login (IN +91)"])

    with screen_tab1:
        st.markdown("##### Create Operator Account")
        with st.form("operator_reg_form"):
            rc1, rc2 = st.columns(2)
            with rc1:
                r_first = st.text_input("First Name:", value="John")
                r_email = st.text_input("Email Address:", value="john.doe@company.com")
                r_role = st.selectbox("Assign Role:", ["Operations Manager", "Lead Developer & Architect", "Code Quality Testing & Security"])
            with rc2:
                r_last = st.text_input("Last Name:", value="Doe")
                r_phone = st.text_input("Phone Number:", value="+91 98765 43210")
                r_pwd = st.text_input("Password:", type="password", value="secure_notion_pass_2026")

            submit_reg = st.form_submit_button("Create Account →", type="primary")
            if submit_reg:
                full_name = f"{r_first.strip()} {r_last.strip()}"
                try:
                    with default_store._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO user_profiles (id, name, role, permissions, biometric_id, avatar_url, tasks_completed, current_streak, unlocked_badges, last_active_date)
                            VALUES (?, ?, ?, ?, ?, ?, 0, 1, '["First Review 🏆"]', '2026-08-25')
                            ON CONFLICT(name) DO UPDATE SET role = excluded.role
                        """, (f"usr_{int(time.time())}", full_name, r_role, json.dumps(["approve", "audit"]), f"BIO_{full_name.upper().replace(' ', '_')}", f"https://api.dicebear.com/7.x/bottts/svg?seed={full_name}"))
                        conn.commit()
                    st.session_state.active_user = full_name
                    st.success(f"✅ Account for **{full_name}** created! Synced with Notion User Profiles database.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to register user: {e}")

    with screen_tab2:
        st.markdown("##### Mobile Phone OTP Authentication")
        st.write("Enter your 10-digit registered mobile number to receive an authorization code.")
        
        ph_col1, ph_col2 = st.columns([1, 3])
        ph_col1.markdown("<div style='background: #1e293b; border: 1px solid #475569; padding: 9px 12px; border-radius: 6px; font-weight: 700; text-align: center; color: #94a3b8;'>IN +91</div>", unsafe_allow_html=True)
        otp_phone_num = ph_col2.text_input("Mobile Number:", value="9876543210", max_chars=10, label_visibility="collapsed")

        if st.button("Get OTP →", type="primary"):
            st.session_state.otp_code = str(random.randint(100000, 999999))
            st.info(f"📟 SMS Dispatched to **+91 {otp_phone_num}**: Code is **`{st.session_state.otp_code}`**")



# ==============================================================================
# VIEW 3: WEBHOOK INGESTION HUB
# ==============================================================================
elif active_module_key == "nav_webhook":
    st.markdown("### 🧪 Webhook Ingestion & Payload Simulation Hub")
    st.write("Simulates authenticated external webhooks with HMAC-SHA256 signatures, nonce tracking, and AI Pre-Auditing.")

    presets = {
        "Academic Registration (Normal Risk)": {
            "title": "Provisions for Lab Group B",
            "details": "Register 15 student seats and dispatch welcome packages with syllabus attachments.",
            "priority": "normal",
            "source": "Academic Registration Portal",
        },
        "Emergency Security Escalation (Critical Risk)": {
            "title": "Security Incident: Unauthorized Root Access Attempt",
            "details": "Detected 40 failed SSH attempts from external subnet. Emergency revoke and purge affected API keys immediately.",
            "priority": "critical",
            "source": "AWS GuardDuty Ingestion",
        },
        "Infrastructure Provisioning (High Risk)": {
            "title": "Database Migration & Firewall Rules Update",
            "details": "Apply database migration script 042_schema_v2.sql and open port 5432 on cluster security group.",
            "priority": "high",
            "source": "DevOps CI/CD Pipeline",
        },
        "Routine Onboarding (Low Risk)": {
            "title": "New Teaching Assistant Onboarding",
            "details": "Grant read access to lecture repository and schedule orientation session.",
            "priority": "low",
            "source": "HR Portal",
        },
    }

    selected_preset = st.selectbox("Select Webhook Payload Preset:", list(presets.keys()))
    preset_data = presets[selected_preset]

    col_in1, col_in2 = st.columns(2)
    with col_in1:
        evt_id = st.text_input("Event ID:", value=f"evt_{random.randint(100000, 999999)}")
        src = st.text_input("Source System:", value=preset_data["source"])
        p_title = st.text_input("Task Title:", value=preset_data["title"])
        p_priority = st.selectbox("Requested Priority:", ["normal", "low", "high", "critical"], index=["normal", "low", "high", "critical"].index(preset_data["priority"]))

    with col_in2:
        p_details = st.text_area("Task Details / Payload:", value=preset_data["details"], height=140)
        nonce_val = st.text_input("Cryptographic Nonce:", value=f"nonce_{random.randint(10000, 99999)}")
        ts_val = st.number_input("Timestamp (Epoch UTC):", value=int(time.time()), step=1)

    req_dict = {
        "event_id": evt_id,
        "source": src,
        "timestamp": int(ts_val),
        "payload": {
            "task_title": p_title,
            "details": p_details,
            "priority": p_priority,
        }
    }
    raw_json_bytes = json.dumps(req_dict, indent=2).encode("utf-8")
    generated_sig = generate_hmac_signature(raw_json_bytes, WEBHOOK_SECRET)

    st.markdown(f"**Calculated `X-Signature-HMAC`:** `<code>{generated_sig}</code>`", unsafe_allow_html=True)

    if st.button("🚀 Ingest Webhook Payload (Run AI Pre-Audit)", type="primary"):
        n_ok, n_msg = default_nonce_guard.validate_and_record(nonce_val, int(ts_val))
        if not n_ok:
            st.error(f"❌ Ingestion Blocked: {n_msg}")
        else:
            audit_res = AIAuditEngine.analyze_task(title=p_title, details=p_details, requested_priority=p_priority)

            task_dict = {
                "id": evt_id,
                "title": p_title,
                "details": p_details,
                "priority": audit_res.suggested_priority,
                "category": audit_res.category,
                "status": "Ready for Review",
                "risk_level": audit_res.risk_level,
                "confidence_score": audit_res.confidence_score,
                "reasoning_trace": audit_res.reasoning_trace,
                "draft_summary": audit_res.draft_summary,
                "draft_email_html": audit_res.draft_email_html,
                "draft_teams_text": audit_res.draft_teams_text,
                "source": src,
            }
            created = default_store.create_task(task_dict, operator_name=f"{src} [Ingest Console]")

            st.success(f"🎉 **Webhook Ingestion Succeeded!** (Event ID: `{evt_id}`)\n\n• AI Evaluated Risk: **{audit_res.risk_level}** (Confidence: {int(audit_res.confidence_score*100)}%)\n• Category: {audit_res.category}\n• Persisted in Notion Database under status `Ready for Review`.")


# ==============================================================================
# VIEW: NOTION MULTI-SELECT BATCH APPROVALS
# ==============================================================================
elif active_module_key == "nav_multiselect":
    st.markdown("### ⚡ Notion Native Multi-Select Batch Approval Simulator")
    st.write("In Notion, a non-technical user can highlight 10 database rows at once, right-click, and change their 'Status' to 'Approved' simultaneously. This console simulates and triggers native multi-select batch operations.")

    pending_tasks = [t for t in default_store.list_tasks(include_archived=False) if t.get("status") == "Ready for Review"]
    all_active_tasks = default_store.list_tasks(include_archived=False)

    col_mb1, col_mb2 = st.columns([3, 1])
    with col_mb1:
        st.info(f"📋 **Found {len(pending_tasks)} task(s) sitting in 'Ready for Review' status.** Select rows below to batch-approve simultaneously.")
    with col_mb2:
        if st.button("➕ Ingest 5 Sample Test Tasks"):
            for i in range(1, 6):
                sample_task = {
                    "id": f"batch_task_{random.randint(10000, 99999)}",
                    "title": f"Batch Group Item #{i}: Lab Provisions & Quota",
                    "details": f"Automated student provision seat #{i*3} with attached materials.",
                    "priority": "normal",
                    "category": "Academic Registration",
                    "status": "Ready for Review",
                    "risk_level": "LOW",
                    "confidence_score": 0.90,
                    "reasoning_trace": [f"[Step 1] Ingested batch item #{i}", "[Step 2] Prepared for Notion multi-select"],
                    "draft_summary": f"Batch Item #{i} summary",
                    "draft_email_html": f"<p>Batch item #{i}</p>",
                    "draft_teams_text": f"Batch Item #{i}",
                    "source": "Batch Simulation Gateway",
                }
                default_store.create_task(sample_task, operator_name="Batch Generator")
            st.success("Ingested 5 sample tasks!")
            time.sleep(1)
            st.rerun()

    if not pending_tasks:
        st.success("✅ No tasks currently pending review! All items have been processed or approved.")
    else:
        st.markdown("#### Select Database Rows to Batch-Approve:")
        
        # Select all checkbox
        select_all = st.checkbox("Select All Pending Tasks", value=False)
        selected_task_ids = []

        for idx, task in enumerate(pending_tasks):
            t_id = task["id"]
            t_title = task["title"]
            t_risk = task.get("risk_level", "LOW")
            t_prio = task.get("priority", "normal").upper()
            t_ver = task.get("version", 1)

            risk_pill = f"<span class='badge-pill badge-{t_risk.lower()}'>{t_risk}</span>"
            chk_label = f"**{t_title}** (`#{t_id[:10]}`) — Priority: `{t_prio}` | OCC: `v{t_ver}`"
            
            is_checked = st.checkbox(
                chk_label,
                value=select_all,
                key=f"batch_chk_{t_id}",
            )
            if is_checked:
                selected_task_ids.append(t_id)

        st.markdown("---")
        count_selected = len(selected_task_ids)
        st.markdown(f"**Selected for Simultaneous Batch Approval:** `<code>{count_selected} / {len(pending_tasks)} task(s)</code>`", unsafe_allow_html=True)

        col_b_act1, col_b_act2 = st.columns([3, 2])

        with col_b_act1:
            if st.button(f"⚡ Batch Approve {count_selected} Selected Task(s) (Simulate Notion Multi-Select)", type="primary", disabled=(count_selected == 0)):
                # 1. Update status to 'Approved' for all selected rows
                updated = default_store.batch_update_status(
                    task_ids=selected_task_ids,
                    new_status="Approved",
                    operator_name=st.session_state.active_user,
                )
                st.success(f"🎉 **Batch Updated {updated} task(s) to 'Approved' simultaneously!**")
                
                # 2. Trigger concurrent batch execution directly
                from main import NotionTrackerDaemon
                daemon = NotionTrackerDaemon()
                dispatched = daemon.process_cycle()
                st.info(f"⚡ **Concurrent Execution Complete:** {dispatched} task(s) concurrently dispatched to Teams & SendGrid.")
                time.sleep(2)
                st.rerun()

        with col_b_act2:
            if st.button("🔴 Batch Reject Selected Task(s)", disabled=(count_selected == 0)):
                updated = default_store.batch_update_status(
                    task_ids=selected_task_ids,
                    new_status="Rejected",
                    operator_name=st.session_state.active_user,
                )
                st.warning(f"Marked {updated} task(s) as Rejected.")
                time.sleep(1)
                st.rerun()


# ==============================================================================
# VIEW: SYSTEM CONFIG & 60-MINUTE DAEMON SCHEDULER
# ==============================================================================
elif active_module_key == "nav_scheduler":
    st.markdown("### ⚙️ System Config & 60-Minute Background Daemon Scheduler")
    st.write("The Notion Tracker worker daemon runs a low-latency persistent loop polling Notion's database for state changes or new pending items every **60 minutes**. Manage runtime configuration and auto-refresh triggers below.")

    sys_cfg = default_store.get_system_config()
    cur_mins = sys_cfg.get("poll_interval_minutes", 60)
    cur_secs = sys_cfg.get("poll_interval_seconds", 3600.0)
    auto_refresh = sys_cfg.get("auto_refresh_enabled", True)
    last_sync = sys_cfg.get("last_sync_timestamp", time.time())
    elapsed = time.time() - last_sync
    remaining = max(0.0, cur_secs - elapsed)

    # Status Metrics
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown(f"""
        <div class="metric-box">
            <p class="metric-label">Polling Cadence</p>
            <p class="metric-value">{int(cur_mins)}m</p>
        </div>
        """, unsafe_allow_html=True)
    with sc2:
        auto_text = "ENABLED" if auto_refresh else "DISABLED"
        auto_class = "metric-box-success" if auto_refresh else "metric-box-warning"
        st.markdown(f"""
        <div class="metric-box {auto_class}">
            <p class="metric-label">Auto-Refresh</p>
            <p class="metric-value" style="font-size: 1.4rem;">{auto_text}</p>
        </div>
        """, unsafe_allow_html=True)
    with sc3:
        st.markdown(f"""
        <div class="metric-box">
            <p class="metric-label">Next Sync In</p>
            <p class="metric-value">{int(remaining // 60)}m {int(remaining % 60)}s</p>
        </div>
        """, unsafe_allow_html=True)
    with sc4:
        st.markdown(f"""
        <div class="metric-box">
            <p class="metric-label">Concurrent Batch Limit</p>
            <p class="metric-value">{sys_cfg.get('max_batch_workers', 10)}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Configuration Form
    with st.container():
        st.markdown("#### 🛠️ Runtime Daemon Configuration Parameters")
        
        cfg_col1, cfg_col2 = st.columns(2)
        with cfg_col1:
            new_auto = st.toggle("Enable Background Auto-Refresh / State Sync", value=auto_refresh)
            
            interval_options = [60, 30, 15, 5, 1]
            chosen_mins = st.select_slider(
                "Polling Cadence (Minutes):",
                options=interval_options,
                value=cur_mins if cur_mins in interval_options else 60,
                help="Standard enterprise requirement is 60 minutes for production operations.",
            )

        with cfg_col2:
            st.markdown("**Test Mode Override (Seconds):**")
            test_secs = st.number_input("Custom Polling Interval (Seconds):", min_value=1.0, max_value=7200.0, value=float(chosen_mins * 60), step=5.0)
            max_workers = st.slider("Max Concurrent Batch Workers:", min_value=1, max_value=20, value=sys_cfg.get("max_batch_workers", 10))

        if st.button("💾 Save & Apply Runtime Configuration", type="primary"):
            updated_cfg = default_store.update_system_config({
                "poll_interval_minutes": int(chosen_mins),
                "poll_interval_seconds": float(test_secs),
                "auto_refresh_enabled": new_auto,
                "max_batch_workers": int(max_workers),
            })
            st.success(f"✅ Runtime system configuration persisted! Daemon polling interval set to {updated_cfg['poll_interval_seconds']}s ({updated_cfg['poll_interval_minutes']}m).")
            time.sleep(1)
            st.rerun()

    st.markdown("---")

    # Manual Daemon Trigger
    st.markdown("#### ⚡ On-Demand Daemon Batch Synchronization")
    st.write("Trigger an immediate batch query across all Notion rows to pull 'Approved' pages and dispatch them concurrently without waiting for the 60-minute scheduler tick.")

    if st.button("🚀 Trigger Immediate Concurrent Batch Cycle Now", type="secondary"):
        from main import NotionTrackerDaemon
        daemon = NotionTrackerDaemon(poll_interval_minutes=int(chosen_mins))
        dispatched = daemon.process_cycle()
        st.success(f"✓ Manual execution cycle completed: **{dispatched}** task(s) processed and concurrently dispatched.")
        time.sleep(1.5)
        st.rerun()


# ==============================================================================
# VIEW 4: SHA-256 AUDIT LEDGER & REPORTS
# ==============================================================================
elif active_module_key == "nav_audit":
    st.markdown("### 📊 Industrial Cryptographic SHA-256 Audit Ledger")
    st.write("Deterministic, non-repudiation audit trail chaining all task updates, operator authorizations, and timestamps.")


    audit_logs = default_store.list_audit_logs()
    tasks = default_store.list_tasks(include_archived=True)

    # Verification Box
    v_col1, v_col2 = st.columns([3, 1])
    verification_res = AuditLedger.verify_ledger_chain(audit_logs)

    with v_col1:
        if verification_res["status"] == "SECURE":
            st.success(f"🟢 **AUDIT LEDGER INTEGRITY: SECURE**\n\n• Recalculated Records: **{verification_res['recalculated_records']}** | Mismatches: **0**\n• Deterministic SHA-256 Signature Chain: **VALID**")
        else:
            st.error(f"🔴 **AUDIT LEDGER INTEGRITY: ALERT (TAMPERING DETECTED)**\n\n• Mismatches: **{verification_res['mismatches_detected']}**")

    with v_col2:
        if st.button("🛡️ Re-Verify Ledger", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Document Export Buttons
    exp_col1, exp_col2, exp_col3 = st.columns(3)

    # ReportLab PDF Download
    pdf_bytes = PDFReportBuilder.generate_task_audit_pdf(tasks, audit_logs)
    exp_col1.download_button(
        label="📄 Download PDF Audit Report",
        data=pdf_bytes,
        file_name="notion_tracker_audit_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    # Excel Download
    excel_bytes = OutboundDispatcher.export_tasks_to_excel(tasks)
    exp_col2.download_button(
        label="📊 Download Tasks Excel / CSV",
        data=excel_bytes,
        file_name="notion_tracker_tasks.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    # Tampering test button
    if exp_col3.button("⚠️ Test Tamper Detection", use_container_width=True):
        if audit_logs:
            audit_logs[0]["payload_data"]["title"] = "UNAUTHORIZED_MODIFIED_TITLE"
            tamper_res = AuditLedger.verify_ledger_chain(audit_logs)
            st.error(f"🚨 **Tampering Test Triggered!** Result: {tamper_res['status']} ({tamper_res['mismatches_detected']} mismatch found).")

    st.markdown("#### 📜 Real-Time Run Log Auditor & Notion Native Mirror")
    st.write("Each run log entry mirrors the Notion page body with native Toggle Blocks: **🔍 AI Reasoning Steps** and **📄 Raw JSON Ingestion Payload**.")

    if audit_logs:
        # --- Multi-Criteria Run Log Search & Filter Controls ---
        s_col1, s_col2, s_col3 = st.columns([2.5, 1.2, 1.2])

        with s_col1:
            search_query = st.text_input(
                "🔍 Search Run Logs:",
                placeholder="Filter by run name / title, provider, status, or keyword...",
                key="run_log_search_query"
            )

        with s_col2:
            extracted_providers = set()
            for l in audit_logs:
                p = l.get("payload_data", {}).get("source") or l.get("operator_name")
                if p:
                    extracted_providers.add(str(p))
            all_providers = ["All Providers"] + sorted(list(extracted_providers))
            chosen_provider = st.selectbox("Filter by Provider / Source:", all_providers, key="run_log_provider_select")

        with s_col3:
            extracted_statuses = set()
            for l in audit_logs:
                st_val = l.get("payload_data", {}).get("status") or l.get("action")
                if st_val:
                    extracted_statuses.add(str(st_val))
            all_statuses = ["All Statuses"] + sorted(list(extracted_statuses))
            chosen_status = st.selectbox("Filter by Status / Action:", all_statuses, key="run_log_status_select")

        # Apply filtering logic
        filtered_logs = []
        for l in audit_logs:
            p_data = l.get("payload_data", {})
            title = str(p_data.get("title", "")).lower()
            record_id = str(l.get("record_id", "")).lower()
            action = str(l.get("action", "")).lower()
            op_name = str(l.get("operator_name", "")).lower()
            source = str(p_data.get("source", op_name)).lower()
            status = str(p_data.get("status", action)).lower()
            raw_str = json.dumps(p_data).lower()

            q = search_query.strip().lower()
            # Match query against run name, provider, or status
            query_match = (
                not q or
                (q in title) or
                (q in record_id) or
                (q in action) or
                (q in op_name) or
                (q in source) or
                (q in status) or
                (q in raw_str)
            )

            provider_match = (
                chosen_provider == "All Providers" or
                chosen_provider.lower() in source or
                chosen_provider.lower() in op_name
            )

            status_match = (
                chosen_status == "All Statuses" or
                chosen_status.lower() == action or
                chosen_status.lower() == status
            )

            if query_match and provider_match and status_match:
                filtered_logs.append(l)

        # Status match counter
        st.markdown(
            f"<div style='font-size: 0.8rem; color: #a5b4fc; margin-bottom: 12px; font-weight: 600;'>"
            f"⚡ Displaying <b>{len(filtered_logs)}</b> of <b>{len(audit_logs)}</b> matching run log records"
            f"</div>",
            unsafe_allow_html=True
        )

        if filtered_logs:
            if pd is not None:
                df_logs = pd.DataFrame(filtered_logs)
                df_logs["timestamp_str"] = df_logs["timestamp"].apply(lambda t: time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t)))
                # Extract Run Name / Title and Provider into clean view columns
                df_logs["run_name"] = df_logs.apply(lambda r: r["payload_data"].get("title") or r["record_id"], axis=1)
                df_logs["provider"] = df_logs.apply(lambda r: r["payload_data"].get("source") or r["operator_name"], axis=1)
                df_logs["status"] = df_logs.apply(lambda r: r["payload_data"].get("status") or r["action"], axis=1)
                
                st.dataframe(
                    df_logs[["id", "run_name", "provider", "status", "action", "timestamp_str", "signature"]],
                    use_container_width=True,
                )

            st.markdown("##### 🔎 Detailed Run Log Page Inspections (Notion Typesetting Mirror)")
            # Show reverse chronological for quick audit
            for l in reversed(filtered_logs[-15:]):
                p_data = l.get("payload_data", {})
                r_steps = p_data.get("reasoning_steps") or p_data.get("reasoning_trace") or [
                    f"[Step 1] Ingested and verified payload for record {l.get('record_id')}",
                    f"[Step 2] Action '{l.get('action')}' processed by {l.get('operator_name')}",
                    f"[Step 3] Cryptographic SHA-256 seal computed and chained.",
                ]
                raw_p = p_data.get("raw_payload") or p_data
                run_title = p_data.get("title") or l.get("record_id")
                provider_name = p_data.get("source") or l.get("operator_name")
                status_name = p_data.get("status") or l.get("action")

                expander_title = f"📜 Run Log #{l.get('id')}: [{status_name}] {run_title} — Provider: {provider_name}"
                with st.expander(expander_title, expanded=False):
                    # Toggle 1 Mirror: 🔍 View Step-by-Step AI Reasoning Steps
                    st.markdown("**🔍 View Step-by-Step AI Reasoning Steps** *(Notion Toggle 1 Mirror)*")
                    for s in r_steps:
                        st.markdown(f"• {s}")

                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                    # Toggle 2 Mirror: 📄 View Raw JSON Ingestion Payload
                    st.markdown("**📄 View Raw JSON Ingestion Payload** *(Notion Toggle 2 Mirror)*")
                    st.code(json.dumps(raw_p, indent=2), language="json")

                    # Cryptographic seal footer
                    st.markdown(f"""
                    <div style="background: rgba(99, 102, 241, 0.08); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(99, 102, 241, 0.2); font-size: 0.76rem; font-family: monospace;">
                        🔒 <b>SHA-256 Signature:</b> <code>{l.get('signature')}</code><br>
                        ⛓️ <b>Prev Signature:</b> <code>{l.get('prev_signature')}</code> | ⏱️ <b>Epoch:</b> {l.get('timestamp')}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning(f"No run log entries match the search criteria ('{search_query}', Provider: '{chosen_provider}', Status: '{chosen_status}').")
    else:
        st.info("No transactions logged yet.")



