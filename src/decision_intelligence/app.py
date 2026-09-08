"""Streamlit command center for explainable renewal decisions."""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from datetime import date, timedelta
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from decision_intelligence.database import DEFAULT_DATABASE_PATH, connect, create_database
from decision_intelligence.deployment import (
    deployment_mode,
    initialize_public_demo_database,
    require_private_mode,
)
from decision_intelligence.ingestion import ingest
from decision_intelligence.onboarding import (
    MAX_SOURCE_FILE_BYTES,
    active_business_dataset,
    data_dictionary,
    list_business_datasets,
    profile_extracts,
    register_business_dataset,
    template_bundle,
)
from decision_intelligence.planner import list_capacity_plans, plan_interventions, save_capacity_plan
from decision_intelligence.policy import (
    create_policy_draft,
    decide_policy,
    ensure_default_policy,
    get_active_policy,
    get_policy_parameters,
    list_policy_versions,
    policy_editor_rows,
    preview_policy_impact,
    validate_policy,
)
from decision_intelligence.reports import executive_html, portfolio_csv, portfolio_dataframe
from decision_intelligence.risk_engine import assess_customer, simulate_customer
from decision_intelligence.timeline import customer_event_timeline, risk_change_history
from decision_intelligence.validation import SOURCE_SPECS, validate_extracts
from decision_intelligence.workflow import (
    assessment_history,
    create_action,
    evidence_records,
    list_actions,
    list_decisions,
    list_scenarios,
    log_decision,
    save_scenario,
    snapshot_portfolio,
    update_action_status,
)


st.set_page_config(page_title="Enterprise Decision Simulator", page_icon="◈", layout="wide")
st.markdown(
    """<style>
    :root {
        --eds-ease-apple: cubic-bezier(0.23, 1, 0.32, 1);
        --eds-ease-spring: cubic-bezier(0.32, 0.72, 0, 1);
        --eds-duration-fast: 120ms;
        --eds-duration-normal: 220ms;
    }
    .block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
    
    /* Apple Hairline Scroll Progress Bar pinned to top of viewport */
    .eds-scroll-track {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 3px;
        background: transparent;
        z-index: 999999;
        pointer-events: none;
    }
    .eds-scroll-bar {
        height: 100%;
        width: 100%;
        background: linear-gradient(90deg, #1f68c4 0%, #38bdf8 35%, #6366f1 70%, #ec4899 100%);
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.8), 0 0 18px rgba(99, 102, 241, 0.4);
        animation: edsScrollGlow 3.5s ease-in-out infinite alternate;
    }
    @keyframes edsScrollGlow {
        0% { filter: brightness(1); }
        100% { filter: brightness(1.3) drop-shadow(0 0 8px rgba(56, 189, 248, 0.8)); }
    }

    /* Apple Staggered Reveals */
    @keyframes edsReveal {
        from {
            opacity: 0;
            transform: translateY(12px) scale(0.98);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    .eds-metric, .eds-brief, .eds-readiness, .eds-journey, .eds-lifecycle, [data-testid="stMetric"] {
        animation: edsReveal 280ms var(--eds-ease-apple) both;
    }
    .eds-metric:nth-child(1) { animation-delay: 20ms; }
    .eds-metric:nth-child(2) { animation-delay: 50ms; }
    .eds-metric:nth-child(3) { animation-delay: 80ms; }
    .eds-metric:nth-child(4) { animation-delay: 110ms; }
    .eds-metric:nth-child(5) { animation-delay: 140ms; }

    /* Emil Kowalski Tactile Button Press Physics */
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(27, 83, 145, 0.12) !important;
        transition: transform var(--eds-duration-fast) var(--eds-ease-apple), box-shadow var(--eds-duration-fast) var(--eds-ease-apple), border-color var(--eds-duration-fast) ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1.5px) !important;
        box-shadow: 0 6px 18px rgba(27, 83, 145, 0.22) !important;
    }
    div.stButton > button:active {
        transform: scale(0.97) translateY(0) !important;
        box-shadow: 0 1px 4px rgba(27, 83, 145, 0.2) !important;
    }

    /* Dynamic Island Live Telemetry Beacon */
    .eds-live-beacon {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        font-size: 0.65rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 800;
        color: #0b4f8a;
        background: rgba(45, 115, 200, 0.1);
        border: 1px solid rgba(45, 115, 200, 0.28);
        padding: 3px 10px;
        border-radius: 999px;
    }
    .eds-beacon-dot {
        width: 6.5px;
        height: 6.5px;
        border-radius: 50%;
        background: #10b981;
        position: relative;
    }
    .eds-beacon-dot::after {
        content: "";
        position: absolute;
        inset: -3px;
        border-radius: 50%;
        border: 1.5px solid #10b981;
        animation: edsRadar 2s cubic-bezier(0, 0, 0.2, 1) infinite;
    }
    @keyframes edsRadar {
        0% { transform: scale(0.8); opacity: 0.9; }
        100% { transform: scale(2.4); opacity: 0; }
    }

    [data-testid="stMetric"] {border: 1px solid #d7e6f4; border-radius: 14px; padding: 14px; background: linear-gradient(145deg, #fff 0%, #f4f9ff 100%); box-shadow: 0 6px 20px rgba(35,83,132,0.06);}
    .eyebrow {font-size:.75rem; letter-spacing:.12em; text-transform:uppercase; color:#527092; font-weight:750;}
    .hero {font-size:2.35rem; line-height:1.1; font-weight:760; margin:.3rem 0 .5rem; letter-spacing: -0.03em; color: #0d2b50;}
    .subtle {color:#607892; max-width:850px; line-height: 1.6;}
    .eds-home {color:#102a4c; margin-top:.2rem;}
    .eds-hero {position:relative; overflow:hidden; color:#f8fbff; border:1px solid rgba(255,255,255,.45); border-radius:28px; padding:1.25rem 1.4rem 1.4rem; margin-bottom:1.2rem; box-shadow:0 28px 75px rgba(27,83,145,.24); background:radial-gradient(circle at 88% 2%,rgba(230,249,255,.92) 0%,rgba(230,249,255,0) 26%),radial-gradient(circle at 72% 94%,rgba(80,169,241,.7) 0%,rgba(80,169,241,0) 38%),linear-gradient(128deg,#071b35 0%,#123d70 36%,#2d73c8 66%,#a8e0fa 100%);}
    .eds-hero:before {content:""; position:absolute; width:460px; height:460px; border-radius:50%; right:-160px; top:-210px; pointer-events:none; border:1px solid rgba(255,255,255,.4); box-shadow:0 0 0 46px rgba(255,255,255,.06),0 0 0 92px rgba(255,255,255,.045);}
    .eds-hero:after {content:""; position:absolute; inset:0; pointer-events:none; opacity:.24; background-image:linear-gradient(rgba(255,255,255,.14) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.14) 1px,transparent 1px); background-size:52px 52px; mask-image:linear-gradient(90deg,transparent 18%,#000 100%);}
    .eds-masthead {position:relative; z-index:2; display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.15rem .25rem 1rem; border-bottom:1px solid rgba(235,247,255,.32); font-size:.66rem; letter-spacing:.15em; text-transform:uppercase; color:#d9edff; font-weight:750;}
    .eds-live {display:inline-flex; align-items:center; gap:.45rem; color:#f5fbff;}
    .eds-live:before {content:""; width:7px; height:7px; border-radius:50%; background:#66f0bc; box-shadow:0 0 0 4px rgba(102,240,188,.16);}
    .eds-hero-grid {position:relative; z-index:2; display:grid; grid-template-columns:minmax(0,1.58fr) minmax(300px,.82fr); gap:2.25rem; padding:3.15rem .5rem 2.25rem; align-items:center;}
    .eds-kicker {font-size:.72rem; line-height:1.4; letter-spacing:.2em; text-transform:uppercase; color:#b9dcff; font-weight:800; margin-bottom:1.1rem;}
    .eds-hero .eds-title {font-family:'Source Sans',Arial,sans-serif!important; font-size:clamp(2.8rem,4.7vw,4.9rem)!important; line-height:1.01!important; letter-spacing:-.045em!important; font-weight:760!important; max-width:790px; margin:0 0 1.35rem; color:#fff;}
    .eds-title em {font-style:normal; font-weight:760; color:#d8f3ff; text-shadow:0 6px 30px rgba(178,230,255,.22);}
    .eds-copy {font-size:1.02rem; line-height:1.7; color:#e1effd; max-width:700px; margin:0;}
    .eds-proof {display:grid; grid-template-columns:repeat(3,1fr); gap:.65rem; margin-top:1.65rem; max-width:720px;}
    .eds-proof-item {padding:.72rem .8rem; border:1px solid rgba(230,245,255,.22); background:rgba(6,35,70,.18); border-radius:12px; backdrop-filter:blur(8px);}
    .eds-proof-item + .eds-proof-item {padding-left:.8rem;}
    .eds-proof-value {display:block; font-size:1.18rem; font-weight:760; color:#fff; margin-bottom:.1rem;}
    .eds-proof-label {font-size:.59rem; letter-spacing:.1em; text-transform:uppercase; color:#cbe4fa;}
    .eds-priority {background:linear-gradient(155deg,rgba(255,255,255,.94),rgba(233,246,255,.82)); color:#102a4c; padding:1.25rem 1.3rem 1.35rem; border:1px solid rgba(255,255,255,.75); border-radius:20px; box-shadow:0 22px 55px rgba(5,38,76,.26); backdrop-filter:blur(16px); transition: transform 200ms var(--eds-ease-apple), box-shadow 200ms var(--eds-ease-apple);}
    .eds-priority:hover {transform: translateY(-2.5px); box-shadow: 0 28px 65px rgba(5,38,76,.32);}
    .eds-priority-head {display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(61,111,168,.2); padding-bottom:.7rem; margin-bottom:1rem; font-size:.62rem; letter-spacing:.14em; text-transform:uppercase; color:#527092; font-weight:800;}
    .eds-priority-index {display:flex; align-items:center; justify-content:center; width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#1f68c4,#64b5ee); font-size:.85rem; font-weight:800; color:#fff; letter-spacing:0; box-shadow:0 8px 20px rgba(31,104,196,.25);}
    .eds-priority-name {font-size:1.72rem; line-height:1.08; letter-spacing:-.025em; font-weight:750; margin-bottom:.85rem; color:#0d2b50;}
    .eds-priority-stats {display:grid; grid-template-columns:repeat(3,1fr); border-top:1px solid rgba(61,111,168,.18); border-bottom:1px solid rgba(61,111,168,.18); margin:.8rem 0;}
    .eds-priority-stat {padding:.72rem .55rem .72rem 0;}
    .eds-priority-stat + .eds-priority-stat {border-left:1px solid rgba(61,111,168,.18); padding-left:.6rem;}
    .eds-priority-stat strong {display:block; font-size:.98rem; color:#0d2b50;}
    .eds-priority-stat span {font-size:.58rem; text-transform:uppercase; letter-spacing:.1em; color:#66809e;}
    .eds-priority-label {font-size:.59rem; letter-spacing:.12em; text-transform:uppercase; color:#527092; font-weight:800; margin-top:.85rem;}
    .eds-priority-copy {font-size:.78rem; line-height:1.5; margin:.28rem 0 0; color:#2f506f;}
    .eds-ticker {position:relative; z-index:2; display:grid; grid-template-columns:1.1fr repeat(4,1fr); overflow:hidden; border:1px solid rgba(232,247,255,.22); border-radius:14px; background:rgba(5,34,68,.2); backdrop-filter:blur(9px);}
    .eds-ticker-cell {padding:.82rem .85rem; min-height:64px;}
    .eds-ticker-cell + .eds-ticker-cell {border-left:1px solid rgba(232,247,255,.2);}
    .eds-ticker-label {display:block; font-size:.56rem; letter-spacing:.12em; text-transform:uppercase; color:#c2ddf5; margin-bottom:.22rem;}
    .eds-ticker-value {font-size:.84rem; color:#fff; font-weight:700;}
    .eds-section-head {display:grid; grid-template-columns:180px 1fr; gap:1.5rem; align-items:start; border-top:1px solid #c7d9ec; padding-top:1.15rem; margin:3.2rem 0 1.45rem;}
    .eds-section-number {display:inline-flex; width:max-content; padding:.32rem .58rem; border-radius:999px; background:#eaf4ff; font-size:.61rem; letter-spacing:.13em; text-transform:uppercase; color:#1766bd; font-weight:800;}
    .eds-section-title {font-family:'Source Sans',Arial,sans-serif; font-size:2.25rem; line-height:1.08; letter-spacing:-.028em; color:#102a4c; margin:0; font-weight:740;}
    .eds-section-subtitle {font-size:.9rem; color:#607892; line-height:1.55; margin:.45rem 0 0; max-width:720px;}
    .eds-metric-grid {display:grid; grid-template-columns:repeat(5,1fr); gap:.7rem; background:transparent;}
    .eds-metric {position:relative; overflow:hidden; padding:1.2rem 1rem 1.1rem; min-height:126px; border:1px solid #d7e6f4; border-top:1px solid #ffffff; border-radius:16px; background:linear-gradient(145deg,#fff 0%,#f2f8ff 100%); box-shadow:0 10px 28px rgba(35,83,132,.07); transition: transform 200ms var(--eds-ease-apple), box-shadow 200ms var(--eds-ease-apple);}
    .eds-metric:hover {transform: translateY(-2.5px); box-shadow: 0 16px 36px rgba(35,83,132,.12);}
    .eds-metric:before {content:""; position:absolute; height:3px; inset:0 0 auto; background:linear-gradient(90deg,#72b8ed,#2d73c8);}
    .eds-metric + .eds-metric {border-left:1px solid #d7e6f4;}
    .eds-metric-label {font-size:.59rem; letter-spacing:.105em; text-transform:uppercase; color:#607892; min-height:32px;}
    .eds-metric-value {font-size:1.85rem; line-height:1; font-weight:750; color:#103b6b; margin:.55rem 0 .35rem;}
    .eds-metric-context {font-size:.68rem; color:#7890a7;}
    .eds-metric.alert {background:linear-gradient(145deg,#fff 0%,#eef7ff 70%,#fdf2f3 100%);}
    .eds-metric.alert:before {background:linear-gradient(90deg,#2d73c8,#df6c78);}
    .eds-metric.alert .eds-metric-value {color:#a52a3d;}
    .eds-brief {border:1px solid #cfe2f5; border-top: 1px solid #ffffff; border-radius:20px; background:linear-gradient(145deg,#f5faff 0%,#e8f4ff 100%); padding:1.6rem 1.7rem; min-height:340px; box-shadow:0 16px 42px rgba(31,93,153,.1); transition: transform 200ms var(--eds-ease-apple);}
    .eds-brief:hover {transform: translateY(-2px);}
    .eds-brief-top {display:flex; align-items:center; justify-content:space-between; gap:1rem; border-bottom:1px solid #c9ddef; padding-bottom:.8rem; margin-bottom:1.2rem;}
    .eds-brief-tag {font-size:.6rem; letter-spacing:.13em; text-transform:uppercase; color:#1766bd; font-weight:800;}
    .eds-brief-risk {font-size:.66rem; letter-spacing:.08em; text-transform:uppercase; color:#a52a3d; font-weight:800;}
    .eds-brief-name {font-size:2.15rem; line-height:1.08; font-weight:750; color:#102f55; margin-bottom:.65rem;}
    .eds-brief-thesis {font-size:.94rem; line-height:1.65; color:#365877; max-width:780px;}
    .eds-brief-move {border-left:4px solid #2d73c8; border-radius:0 10px 10px 0; background:rgba(255,255,255,.62); margin-top:1.3rem; padding:.7rem .85rem; color:#163e68; font-size:.9rem; line-height:1.5;}
    .eds-readiness {border:1px solid #2f73b8; border-radius:20px; background:radial-gradient(circle at 100% 0%,rgba(112,188,241,.42),transparent 34%),linear-gradient(145deg,#0b2b50 0%,#174d83 100%); padding:1.25rem 1.35rem; min-height:340px; box-shadow:0 16px 42px rgba(15,57,99,.16);}
    .eds-readiness-title {font-size:1.28rem; font-weight:750; margin-bottom:.9rem; color:#fff;}
    .eds-readiness-row {display:flex; justify-content:space-between; gap:1rem; border-top:1px solid rgba(213,236,255,.18); padding:.58rem 0; font-size:.7rem;}
    .eds-readiness-row span {color:#b9d6ed;}
    .eds-readiness-row strong {color:#fff; text-align:right;}
    .eds-journey {position:relative; overflow:hidden; border:1px solid #d4e4f3; border-top:1px solid #ffffff; border-radius:16px; background:linear-gradient(155deg,#fff,#f3f9ff); padding:1.15rem 1rem .7rem; min-height:190px; box-shadow:0 10px 28px rgba(35,83,132,.07); transition:transform 200ms var(--eds-ease-apple),box-shadow 200ms var(--eds-ease-apple);}
    .eds-journey:before {content:""; position:absolute; inset:0 0 auto; height:4px; background:linear-gradient(90deg,#92d1f3,#2d73c8);}
    .eds-journey:hover {transform:translateY(-3px); box-shadow:0 16px 34px rgba(35,83,132,.12);}
    .eds-journey-number {color:#2672c6; font-size:1.48rem; font-weight:750;}
    .eds-journey-title {font-size:.9rem; text-transform:uppercase; letter-spacing:.055em; font-weight:800; margin:.7rem 0 .55rem; color:#12385f;}
    .eds-journey-copy {font-size:.78rem; line-height:1.55; color:#617a93;}
    .eds-lifecycle {border:1px solid #d6e6f5; border-radius:14px; background:linear-gradient(150deg,#fff,#edf6ff); padding:.85rem .7rem; min-height:108px; box-shadow:0 8px 22px rgba(35,83,132,.06);}
    .eds-lifecycle strong {display:block; color:#1766bd; font-size:.75rem; margin-bottom:.4rem;}
    .eds-lifecycle span {font-size:.68rem; line-height:1.45; color:#607892;}
    .eds-trust {background:linear-gradient(90deg,#e9f5ff,#f5fbff); border:1px solid #cbe2f5; border-left:5px solid #2d73c8; border-radius:12px; padding:1rem 1.2rem; color:#365877; font-size:.8rem; line-height:1.55; margin-top:2rem; box-shadow:0 8px 24px rgba(35,83,132,.06);}
    @media (max-width: 1050px) {.eds-hero-grid{grid-template-columns:1fr;gap:2rem}.eds-priority{max-width:620px}.eds-metric-grid{grid-template-columns:repeat(2,1fr)}.eds-ticker{grid-template-columns:repeat(2,1fr)}}
    @media (max-width: 700px) {.eds-hero{padding:1rem;border-radius:20px}.eds-masthead{align-items:flex-start;flex-direction:column}.eds-hero-grid{padding:2.4rem 0 .9rem}.eds-hero .eds-title{font-size:2.55rem!important}.eds-proof{grid-template-columns:1fr}.eds-ticker,.eds-metric-grid{grid-template-columns:1fr}.eds-ticker-cell + .eds-ticker-cell{border-left:0;border-top:1px solid rgba(230,245,255,.18)}.eds-section-head{grid-template-columns:1fr;gap:.55rem}.eds-section-title{font-size:1.8rem}}
    
    /* Native Tabs with Apple Pill Style */
    [data-testid="stTabs"] button[role="tab"] {
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        color: #64748b !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        transition: all var(--eds-duration-fast) var(--eds-ease-apple) !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #1e40af !important;
        background: #eff6ff !important;
        border-bottom: 2px solid #2563eb !important;
    }

    @media (prefers-reduced-motion: reduce) {
        *, .eds-metric, .eds-brief, .eds-readiness, .eds-journey, .eds-lifecycle, [data-testid="stMetric"], .eds-scroll-bar, div.stButton > button {
            animation: none !important;
            transition: none !important;
            transform: none !important;
        }
    }
    </style>""",
    unsafe_allow_html=True,
)

DEPLOYMENT = deployment_mode()

def render_customer_score_waterfall(assessment: dict) -> go.Figure | None:
    factors = assessment.get("factors", [])
    if not factors:
        return None
    names = [f["name"] for f in factors]
    points = [f["points"] for f in factors]
    total_score = assessment["risk_score"]
    
    fig = go.Figure(go.Waterfall(
        name="Risk Points",
        orientation="v",
        measure=["relative"] * len(factors) + ["total"],
        x=names + ["Calculated Risk Score"],
        textposition="outside",
        text=[f"+{p} pts" for p in points] + [f"{total_score} / 100"],
        y=points + [total_score],
        connector={"line": {"color": "rgba(31, 104, 196, 0.4)", "width": 1.5, "dash": "dot"}},
        decreasing={"marker": {"color": "#10b981"}},
        increasing={"marker": {"color": "#ef4444"}},
        totals={"marker": {"color": "#1e40af"}},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(tickangle=-15, tickfont=dict(size=11, color="#334155")),
        yaxis=dict(title="Score Contribution (Points)", range=[0, 110], gridcolor="rgba(0,0,0,0.06)", tickfont=dict(size=10, color="#64748b")),
        height=320,
        showlegend=False,
    )
    return fig


def render_command_center_bubble(portfolio: pd.DataFrame) -> go.Figure:
    color_map = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}
    fig = px.scatter(
        portfolio,
        x="days_to_renewal",
        y="risk_score",
        size="annual_contract_value",
        color="risk_level",
        color_discrete_map=color_map,
        hover_name="customer_name",
        hover_data={
            "days_to_renewal": True,
            "risk_score": True,
            "annual_contract_value": ":$,.0f",
            "account_manager": True,
            "risk_level": False,
        },
        labels={
            "days_to_renewal": "Days to Renewal (Contract Urgency)",
            "risk_score": "Risk Score (0-100)",
            "annual_contract_value": "Contract ACV",
        },
        size_max=28,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=15, b=10),
        xaxis=dict(gridcolor="rgba(0,0,0,0.06)", zeroline=False, tickfont=dict(size=10, color="#64748b")),
        yaxis=dict(gridcolor="rgba(0,0,0,0.06)", zeroline=False, range=[0, 105], tickfont=dict(size=10, color="#64748b")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=300,
    )
    return fig


def render_segment_exposure_bar(high_portfolio: pd.DataFrame) -> go.Figure:
    segment_risk = high_portfolio.groupby("segment", as_index=False).annual_contract_value.sum()
    fig = px.bar(
        segment_risk,
        x="annual_contract_value",
        y="segment",
        orientation="h",
        color="annual_contract_value",
        color_continuous_scale=["#93c5fd", "#1d4ed8"],
        labels={"annual_contract_value": "High-Risk ACV ($)", "segment": "Segment"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=15, t=15, b=10),
        coloraxis_showscale=False,
        xaxis=dict(gridcolor="rgba(0,0,0,0.06)", tickprefix="$", tickfont=dict(size=10, color="#64748b")),
        yaxis=dict(tickfont=dict(size=11, color="#334155")),
        height=300,
    )
    return fig


def render_scenario_gauge(baseline_score: int, simulated_score: int) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=simulated_score,
        title={'text': "Simulated Risk Score (After Intervention)", 'font': {'size': 13, 'color': '#0f172a'}},
        delta={'reference': baseline_score, 'decreasing': {'color': "#10b981"}, 'increasing': {'color': "#ef4444"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#64748b"},
            'bar': {'color': "#2563eb"},
            'bgcolor': "white",
            'borderwidth': 1,
            'bordercolor': "#cbd5e1",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(16, 185, 129, 0.2)'},
                {'range': [40, 70], 'color': 'rgba(245, 158, 11, 0.2)'},
                {'range': [70, 100], 'color': 'rgba(239, 68, 68, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "#ef4444", 'width': 3},
                'thickness': 0.8,
                'value': baseline_score
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=10),
        height=230,
    )
    return fig



@st.cache_resource(show_spinner="Preparing isolated synthetic demonstration data...")
def public_demo_database() -> Path:
    return initialize_public_demo_database()


DATABASE_PATH = public_demo_database() if DEPLOYMENT.is_public_demo else DEFAULT_DATABASE_PATH
create_database(DATABASE_PATH)
ensure_default_policy(DATABASE_PATH)
business_profile = active_business_dataset(DATABASE_PATH)
with connect(DATABASE_PATH) as connection:
    customers = pd.read_sql_query(
        """SELECT c.customer_id, c.customer_name, c.segment, c.region,
                  am.full_name AS account_manager_name
             FROM customers c JOIN account_managers am USING (account_manager_id)
            ORDER BY c.customer_name""",
        connection,
    )

st.sidebar.markdown(
    """<div style="margin-bottom:12px;">
        <span class="eds-live-beacon"><span class="eds-beacon-dot"></span><span>LIVE PORTFOLIO ACTIVE</span></span>
        <div style="font-size:1.35rem; font-weight:800; color:#0d2b50; letter-spacing:-0.02em; margin-top:8px;">◈ Decision Simulator</div>
    </div>""",
    unsafe_allow_html=True,
)
page = st.sidebar.radio(
    "Workspace",
    [
        "Home",
        "Data Onboarding",
        "Command Center",
        "Customer 360",
        "Change Timeline",
        "Scenario Lab",
        "Capacity Planner",
        "Actions & Decisions",
        "Policy Studio",
        "Data Health",
    ],
    label_visibility="collapsed",
    key="workspace",
)
with st.sidebar.expander("90-second guided demo", expanded=False):
    st.markdown(
        """1. Start at **Home** for the executive briefing.
2. Use **Command Center** to identify high-risk ACV.
3. Open **Customer 360** and trace every point to its source row.
4. Explain movement in **Change Timeline** and test an intervention.
5. Allocate resources in **Capacity Planner**.
6. Govern rules in **Policy Studio** and verify lineage in **Data Health**."""
    )
st.sidebar.caption(business_profile["organization_name"])
st.sidebar.caption(f"{DEPLOYMENT.label} mode")
st.sidebar.caption("Local by design · Rules, not guesses · No LLM")

if DEPLOYMENT.is_public_demo and page != "Home":
    st.info(
        "Public Demo mode: this instance uses an isolated synthetic dataset. "
        "Uploads and persistent workflow changes are disabled."
    )
elif not DEPLOYMENT.is_public_demo and page != "Home":
    st.success(
        "Private Business mode: governed uploads and persistent workflow changes are enabled "
        "for this local installation."
    )

if customers.empty and page != "Data Onboarding":
    st.error(
        "No integrated data found. Open Data Onboarding to activate business data, "
        "or run `python -m decision_intelligence.bootstrap` for the synthetic demonstration."
    )
    st.stop()


def customer_selector(label: str, key: str) -> tuple[str, str]:
    names = customers["customer_name"].tolist()
    selected = st.selectbox(label, names, key=key)
    customer_id = customers.loc[customers.customer_name.eq(selected), "customer_id"].iloc[0]
    return customer_id, selected


def risk_message(level: str, message: str) -> None:
    if level == "High":
        st.error(message)
    elif level == "Medium":
        st.warning(message)
    else:
        st.success(message)


def page_heading(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div><div class="hero">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtle">{subtitle}</div>', unsafe_allow_html=True)
    st.write("")


def navigate_to(workspace: str) -> None:
    """Navigation callback used by homepage calls to action."""

    st.session_state["workspace"] = workspace


def navigate_to_customer(customer_name: str) -> None:
    """Open Customer 360 with the briefing account already selected."""

    st.session_state["customer_360"] = customer_name
    st.session_state["workspace"] = "Customer 360"


if page == "Home":
    today = date.today()
    home_portfolio = portfolio_dataframe(today, DATABASE_PATH)
    home_high = home_portfolio[home_portfolio.risk_level.eq("High")]
    home_due = home_portfolio[home_portfolio.days_to_renewal.le(90)]
    top_account = home_portfolio.sort_values(
        ["risk_score", "annual_contract_value"], ascending=False
    ).iloc[0]
    home_actions = pd.DataFrame(list_actions(database_path=DATABASE_PATH))
    home_overdue = 0
    if not home_actions.empty:
        home_overdue = int(
            ((pd.to_datetime(home_actions.due_date).dt.date < today) & ~home_actions.action_status.eq("Completed")).sum()
        )
    active_policy_id, _ = get_active_policy(DATABASE_PATH)
    policy_versions = list_policy_versions(DATABASE_PATH)
    active_policy = next(
        (item for item in policy_versions if item["policy_version_id"] == active_policy_id), None
    )
    active_policy_label = f"v{active_policy['version_number']}" if active_policy else "Baseline"
    with connect(DATABASE_PATH) as connection:
        latest_run = connection.execute(
            """SELECT completed_at, run_status, records_loaded FROM ingestion_runs
                ORDER BY started_at DESC LIMIT 1"""
        ).fetchone()
        snapshot_count = connection.execute("SELECT COUNT(*) FROM risk_assessments").fetchone()[0]
        quality_issue_count = connection.execute("SELECT COUNT(*) FROM data_quality_issues").fetchone()[0]

    top_assessment = assess_customer(top_account.customer_id, today, DATABASE_PATH)
    factor_names = ", ".join(factor["name"] for factor in top_assessment["factors"])
    factor_summary = factor_names or "No rule-based risk factors are currently active"
    home_high_acv = float(home_high.annual_contract_value.sum())
    home_total_acv = float(home_portfolio.annual_contract_value.sum())
    home_exposure_pct = (home_high_acv / home_total_acv * 100) if home_total_acv else 0
    high_account_pct = (len(home_high) / len(home_portfolio) * 100) if len(home_portfolio) else 0
    latest_run_status = str(latest_run["run_status"]) if latest_run else "Not run"
    latest_completed_label = "Not available"
    if latest_run and latest_run["completed_at"]:
        latest_completed = pd.to_datetime(latest_run["completed_at"])
        latest_completed_label = latest_completed.strftime("%d %b %Y / %H:%M UTC")

    st.markdown(
        f"""<div class="eds-home"><section class="eds-hero">
        <div class="eds-masthead">
          <span>Enterprise Decision Simulator / Decision clarity at operating speed</span>
          <span class="eds-live">Live portfolio / {escape(today.strftime('%d %B %Y'))}</span>
        </div>
        <div class="eds-hero-grid">
          <div>
            <div class="eds-kicker">Integrated renewal intelligence</div>
            <h1 class="eds-title">Turn fragmented<br>signals into decisions<br><em>people can defend.</em></h1>
            <p class="eds-copy">See which customers are at risk, why the score moved, what evidence supports it, and which intervention deserves capacity. Every recommendation is transparent. Every rule can be challenged.</p>
            <div class="eds-proof">
              <div class="eds-proof-item"><span class="eds-proof-value">4</span><span class="eds-proof-label">Source domains integrated</span></div>
              <div class="eds-proof-item"><span class="eds-proof-value">100%</span><span class="eds-proof-label">Rule traceability</span></div>
              <div class="eds-proof-item"><span class="eds-proof-value">0</span><span class="eds-proof-label">Black-box models</span></div>
            </div>
          </div>
          <aside class="eds-priority">
            <div class="eds-priority-head"><span>Today's priority account</span><span class="eds-priority-index">01</span></div>
            <div class="eds-priority-name">{escape(str(top_account.customer_name))}</div>
            <div class="eds-priority-stats">
              <div class="eds-priority-stat"><strong>{escape(str(top_account.risk_level))}</strong><span>Risk</span></div>
              <div class="eds-priority-stat"><strong>{int(top_account.risk_score)}/100</strong><span>Score</span></div>
              <div class="eds-priority-stat"><strong>${float(top_account.annual_contract_value):,.0f}</strong><span>ACV</span></div>
            </div>
            <div class="eds-priority-label">Management diagnosis</div>
            <p class="eds-priority-copy">{escape(factor_summary)}</p>
            <div class="eds-priority-label">Recommended move</div>
            <p class="eds-priority-copy"><strong>{escape(str(top_account.next_action))}</strong></p>
          </aside>
        </div>
        <div class="eds-ticker">
          <div class="eds-ticker-cell"><span class="eds-ticker-label">Operating context</span><span class="eds-ticker-value">{escape(str(business_profile['organization_name']))}</span></div>
          <div class="eds-ticker-cell"><span class="eds-ticker-label">Customers monitored</span><span class="eds-ticker-value">{len(home_portfolio):,}</span></div>
          <div class="eds-ticker-cell"><span class="eds-ticker-label">High-risk ACV</span><span class="eds-ticker-value">${home_high_acv:,.0f}</span></div>
          <div class="eds-ticker-cell"><span class="eds-ticker-label">Active policy</span><span class="eds-ticker-value">{escape(active_policy_label)}</span></div>
          <div class="eds-ticker-cell"><span class="eds-ticker-label">Control boundary</span><span class="eds-ticker-value">{escape(DEPLOYMENT.label)}</span></div>
        </div>
        </section></div>""",
        unsafe_allow_html=True,
    )
    hero_left, hero_data, hero_mid, hero_right = st.columns([1.3, 1, 1, 1])
    hero_left.button(
        "Open the Renewal Command Center",
        type="primary",
        use_container_width=True,
        on_click=navigate_to,
        args=("Command Center",),
    )
    hero_data.button(
        "Onboard business data",
        use_container_width=True,
        on_click=navigate_to,
        args=("Data Onboarding",),
    )
    hero_mid.button(
        "Review highest-risk account",
        use_container_width=True,
        on_click=navigate_to_customer,
        args=(top_account.customer_name,),
    )
    hero_right.button(
        "Plan this week's capacity",
        use_container_width=True,
        on_click=navigate_to,
        args=("Capacity Planner",),
    )

    st.markdown(
        """<div class="eds-section-head"><div class="eds-section-number">01 / Portfolio signal</div>
        <div><h2 class="eds-section-title">The commercial situation, at a glance.</h2>
        <p class="eds-section-subtitle">A live view of exposure, urgency, and execution debt across the integrated customer portfolio.</p></div></div>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""<div class="eds-metric-grid">
        <div class="eds-metric"><div class="eds-metric-label">Customers monitored</div><div class="eds-metric-value">{len(home_portfolio):,}</div><div class="eds-metric-context">Integrated book of business</div></div>
        <div class="eds-metric alert"><div class="eds-metric-label">High-risk accounts</div><div class="eds-metric-value">{len(home_high):,}</div><div class="eds-metric-context">{high_account_pct:.0f}% of monitored accounts</div></div>
        <div class="eds-metric alert"><div class="eds-metric-label">High-risk ACV</div><div class="eds-metric-value">${home_high_acv:,.0f}</div><div class="eds-metric-context">{home_exposure_pct:.1f}% of portfolio ACV</div></div>
        <div class="eds-metric"><div class="eds-metric-label">Renewals within 90 days</div><div class="eds-metric-value">{len(home_due):,}</div><div class="eds-metric-context">Near-term contract urgency</div></div>
        <div class="eds-metric"><div class="eds-metric-label">Overdue actions</div><div class="eds-metric-value">{home_overdue:,}</div><div class="eds-metric-context">Unresolved execution debt</div></div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """<div class="eds-section-head"><div class="eds-section-number">02 / Executive brief</div>
        <div><h2 class="eds-section-title">One decision deserves the room first.</h2>
        <p class="eds-section-subtitle">The highest-priority renewal, the evidence behind it, and the action the operating team should debate today.</p></div></div>""",
        unsafe_allow_html=True,
    )
    briefing, readiness = st.columns([1.8, 1])
    with briefing:
        st.markdown(
            f"""<article class="eds-brief">
            <div class="eds-brief-top"><span class="eds-brief-tag">Management memo / Priority 01</span><span class="eds-brief-risk">{escape(str(top_account.risk_level))} risk / {int(top_account.risk_score)} points</span></div>
            <div class="eds-brief-name">{escape(str(top_account.customer_name))}</div>
            <div class="eds-brief-thesis"><strong>Decision thesis.</strong> ${float(top_account.annual_contract_value):,.0f} in annual contract value requires attention. The active scoring policy identifies {escape(factor_summary)}.</div>
            <div class="eds-brief-move"><strong>Recommended management move</strong><br>{escape(str(top_account.next_action))}</div>
            </article>""",
            unsafe_allow_html=True,
        )
        b1, b2 = st.columns(2)
        b1.button(
            "Inspect every source record",
            use_container_width=True,
            on_click=navigate_to_customer,
            args=(top_account.customer_name,),
            key="home_to_customer",
        )
        b2.button(
            "Negotiate a what-if scenario",
            use_container_width=True,
            on_click=navigate_to,
            args=("Scenario Lab",),
            key="home_to_scenario",
        )
    with readiness:
        st.markdown(
            f"""<aside class="eds-readiness">
            <div class="eds-readiness-title">Control environment</div>
            <div class="eds-readiness-row"><span>Organization</span><strong>{escape(str(business_profile['organization_name']))}</strong></div>
            <div class="eds-readiness-row"><span>Data classification</span><strong>{escape(str(business_profile['data_classification']))}</strong></div>
            <div class="eds-readiness-row"><span>Scoring policy</span><strong>{escape(active_policy_label)}</strong></div>
            <div class="eds-readiness-row"><span>Latest ingestion</span><strong>{escape(latest_run_status)}</strong></div>
            <div class="eds-readiness-row"><span>Data freshness</span><strong>{escape(latest_completed_label)}</strong></div>
            <div class="eds-readiness-row"><span>Assessment history</span><strong>{snapshot_count:,} snapshots</strong></div>
            <div class="eds-readiness-row"><span>Quality register</span><strong>{quality_issue_count:,} issues</strong></div>
            <div class="eds-readiness-row"><span>Integrated domains</span><strong>CRM / Contract / Product / Support</strong></div>
            </aside>""",
            unsafe_allow_html=True,
        )

    st.markdown(
        """<div class="eds-section-head"><div class="eds-section-number">03 / Decision path</div>
        <div><h2 class="eds-section-title">From weak signal to accountable action.</h2>
        <p class="eds-section-subtitle">A practical route through diagnosis, evidence, intervention design, and constrained execution.</p></div></div>""",
        unsafe_allow_html=True,
    )
    journey_columns = st.columns(4)
    journeys = [
        ("01", "Judge", "Rank accounts by evidence-backed risk, renewal urgency, commercial exposure, and accountable next action.", "Command Center", "Open portfolio"),
        ("02", "Understand", "Move from score to factor to the exact usage event, support ticket, contract record, and temporal change.", "Change Timeline", "Explain change"),
        ("03", "Negotiate", "Change explicit assumptions and compare current versus simulated outcomes without altering source data.", "Scenario Lab", "Open Scenario Lab"),
        ("04", "Allocate", "Fund the highest-value interventions within hours, budget, escalation, and enablement constraints.", "Capacity Planner", "Build capacity plan"),
    ]
    for index, (number, title, copy, destination, button_label) in enumerate(journeys):
        with journey_columns[index]:
            st.markdown(
                f"""<div class="eds-journey"><div class="eds-journey-number">{number}</div>
                <div class="eds-journey-title">{title}</div><div class="eds-journey-copy">{copy}</div></div>""",
                unsafe_allow_html=True,
            )
            st.button(
                button_label,
                use_container_width=True,
                on_click=navigate_to,
                args=(destination,),
                key=f"journey_{index}",
            )

    st.markdown(
        """<div class="eds-section-head"><div class="eds-section-number">04 / Operating model</div>
        <div><h2 class="eds-section-title">A governed decision lifecycle.</h2>
        <p class="eds-section-subtitle">The application separates evidence, policy, recommendation, and human action so every decision remains reviewable.</p></div></div>""",
        unsafe_allow_html=True,
    )
    lifecycle = [
        ("1", "Integrate", "Connect four operational domains"),
        ("2", "Validate", "Block errors and record provenance"),
        ("3", "Score", "Apply versioned deterministic policy"),
        ("4", "Explain", "Trace factors and temporal change"),
        ("5", "Simulate", "Compare explicit interventions"),
        ("6", "Act & govern", "Allocate, assign, approve, audit"),
    ]
    for column, (number, title, copy) in zip(st.columns(6), lifecycle):
        column.markdown(
            f'<div class="eds-lifecycle"><strong>{number} / {title}</strong><span>{copy}</span></div>',
            unsafe_allow_html=True,
        )

    trust_data = (
        "isolated synthetic data and blocked persistent changes"
        if DEPLOYMENT.is_public_demo
        else "an authorized local dataset, explicit approvals, and human-owned decisions"
    )
    st.markdown(
        f"""<div class="eds-trust"><strong>Trust boundary.</strong> {escape(trust_data.capitalize())}, deterministic rules, and source-linked evidence. This system supports judgment. It does not pretend to replace it.</div>""",
        unsafe_allow_html=True,
    )

elif page == "Data Onboarding":
    page_heading(
        "Bring your own business data",
        "Data Onboarding",
        "Replace the synthetic demonstration with governed customer, owner, contract, usage, and support data from your organization.",
    )
    o1, o2, o3 = st.columns(3)
    o1.metric("Active organization", business_profile["organization_name"])
    o2.metric("Classification", business_profile["data_classification"])
    o3.metric("Required source files", len(SOURCE_SPECS))
    if DEPLOYMENT.is_public_demo:
        st.info(
            "Public boundary: this process uses a temporary synthetic database and cannot open the private business database."
        )
        st.warning(
            "This public instance is a safe onboarding preview. You can download the templates and inspect the data contract, "
            "but uploads and activation are available only in Private Business mode."
        )
    else:
        st.info(
            "Privacy boundary: uploads are processed by this local Streamlit process and stored in the local SQLite database. "
            "Only upload data you are authorized to use, and remove unnecessary personal data before importing."
        )

    upload_tab, contract_tab, history_tab, access_tab = st.tabs(
        ["Upload business data", "Data contract", "Import history", "Shared access boundary"]
    )
    with upload_tab:
        intro_left, intro_right = st.columns([1.6, 1])
        with intro_left:
            st.markdown("#### Start with the governed templates")
            st.write(
                "The bundle contains five blank CSV templates, complete synthetic examples, and preparation instructions. "
                "Your stable IDs connect the five business domains."
            )
        with intro_right:
            st.download_button(
                "Download onboarding kit",
                data=template_bundle(),
                file_name="enterprise_decision_simulator_onboarding_kit.zip",
                mime="application/zip",
                use_container_width=True,
            )

        organization_name = st.text_input(
            "Organization or workspace name",
            placeholder="Enter your organization or workspace name",
            disabled=not DEPLOYMENT.data_uploads_enabled,
        )
        meta1, meta2 = st.columns(2)
        imported_by = meta1.text_input(
            "Data steward", disabled=not DEPLOYMENT.data_uploads_enabled
        )
        classification = meta2.selectbox(
            "Data classification",
            ["Anonymized", "Confidential internal", "Synthetic demo"],
            disabled=not DEPLOYMENT.data_uploads_enabled,
        )
        uploaded = st.file_uploader(
            "Upload all five CSV source snapshots",
            type="csv",
            accept_multiple_files=True,
            help="Required filenames: " + ", ".join(SOURCE_SPECS),
            key="business_onboarding_upload",
            disabled=not DEPLOYMENT.data_uploads_enabled,
        )
        extracts: dict[str, pd.DataFrame] = {}
        file_bytes: dict[str, bytes] = {}
        parse_errors: list[str] = []
        unknown_files: list[str] = []
        for upload in uploaded:
            if upload.name not in SOURCE_SPECS:
                unknown_files.append(upload.name)
                continue
            if upload.name in file_bytes:
                parse_errors.append(f"{upload.name}: duplicate filename")
                continue
            if upload.size > MAX_SOURCE_FILE_BYTES:
                parse_errors.append(f"{upload.name}: file exceeds the 50 MB local upload limit")
                continue
            file_bytes[upload.name] = upload.getvalue()
            try:
                upload.seek(0)
                extracts[upload.name] = pd.read_csv(upload, dtype=str, keep_default_na=False)
            except Exception as error:
                parse_errors.append(f"{upload.name}: {error}")
        if unknown_files:
            st.warning("Ignored unrecognized files: " + ", ".join(sorted(unknown_files)))
        for error in parse_errors:
            st.error("Could not read " + error)

        if uploaded:
            st.subheader("Upload profile")
            st.dataframe(pd.DataFrame(profile_extracts(extracts)), use_container_width=True, hide_index=True)
            validation_issues = validate_extracts(extracts)
            issue_frame = pd.DataFrame([asdict(issue) for issue in validation_issues])
            error_count = sum(issue.severity == "ERROR" for issue in validation_issues) + len(parse_errors)
            warning_count = sum(issue.severity == "WARNING" for issue in validation_issues)
            if error_count:
                st.error(f"Import blocked: {error_count} error(s) and {warning_count} warning(s).")
            elif warning_count:
                st.warning(f"Validation passed with {warning_count} warning(s) requiring approval.")
            else:
                st.success("Validation passed. Structural, domain, numeric, date, uniqueness, and relationship checks succeeded.")
            if not issue_frame.empty:
                st.dataframe(issue_frame, use_container_width=True, hide_index=True)
            with st.expander("Preview uploaded records"):
                for filename, frame in extracts.items():
                    st.markdown(f"**{filename}** ({len(frame):,} rows)")
                    st.dataframe(frame.head(10), use_container_width=True, hide_index=True)
            approve_warnings = st.checkbox(
                "I reviewed and approve warning-level exceptions",
                disabled=warning_count == 0,
                key="onboarding_warning_approval",
            )
            confirm_replace = st.checkbox(
                "I understand that changed source snapshots update the active local operational dataset",
                key="onboarding_replace_confirmation",
            )
            ready = (
                len(extracts) == len(SOURCE_SPECS)
                and error_count == 0
                and (warning_count == 0 or approve_warnings)
                and confirm_replace
                and bool(organization_name.strip())
                and bool(imported_by.strip())
                and DEPLOYMENT.data_uploads_enabled
            )
            if st.button("Activate validated business dataset", type="primary", disabled=not ready):
                require_private_mode(DEPLOYMENT, "Business data activation")
                with tempfile.TemporaryDirectory(prefix="decision-data-import-") as temporary:
                    temporary_path = Path(temporary)
                    for filename, content in file_bytes.items():
                        (temporary_path / filename).write_bytes(content)
                    result = ingest(
                        temporary_path,
                        database_path=DATABASE_PATH,
                        approve_warnings=approve_warnings,
                        approved_by=imported_by,
                    )
                if result["status"] in {"COMPLETED", "SKIPPED_UNCHANGED"}:
                    registration_id = register_business_dataset(
                        organization_name,
                        imported_by,
                        classification,
                        result["run_id"],
                        DATABASE_PATH,
                    )
                    st.success(
                        f"{organization_name} is now the active local workspace. Registration ID: {registration_id}"
                    )
                    st.button(
                        "Open Home with this dataset",
                        on_click=navigate_to,
                        args=("Home",),
                    )
                else:
                    st.error("The governed ingestion did not complete, so the dataset was not activated.")

    with contract_tab:
        st.markdown("#### Required upload contract")
        st.write(
            "All five files are evaluated together because customer, owner, contract, usage, and support relationships must remain consistent."
        )
        dictionary = data_dictionary()
        st.dataframe(dictionary, use_container_width=True, hide_index=True)
        st.download_button(
            "Download data dictionary (CSV)",
            dictionary.to_csv(index=False).encode("utf-8"),
            file_name="enterprise_decision_simulator_data_dictionary.csv",
            mime="text/csv",
        )
    with history_tab:
        registrations = pd.DataFrame(list_business_datasets(DATABASE_PATH))
        if registrations.empty:
            st.info("No external business dataset has been registered. The synthetic demonstration is active.")
        else:
            st.dataframe(registrations, use_container_width=True, hide_index=True)
    with access_tab:
        if DEPLOYMENT.is_public_demo:
            st.success(
                "This mode is designed for public portfolio access. Its database is synthetic, temporary, and isolated from Private Business data."
            )
            st.write(
                "Public visitors can explore evidence and calculate scenarios, but they cannot upload data or persist snapshots, actions, decisions, plans, scenarios, or policy changes."
            )
        else:
            st.warning(
                "Do not expose Private Business mode directly to the public internet. This project does not include authentication, authorization, encrypted secrets, tenant isolation, or production concurrency controls."
            )
            st.write(
                "A business can run this privately on an approved laptop or controlled local environment. Worldwide access to real business data requires identity management, HTTPS, backups, monitoring, and a production database."
            )

elif page == "Command Center":
    page_heading(
        "Portfolio workspace",
        "Renewal Command Center",
        "A prioritized operating view of revenue exposure, renewal timing, evidence, and accountable next actions.",
    )
    as_of = st.date_input("Assessment date", value=date.today(), key="portfolio_as_of")
    portfolio = portfolio_dataframe(as_of, DATABASE_PATH)
    action_rows = list_actions(database_path=DATABASE_PATH)
    actions = pd.DataFrame(action_rows)
    high = portfolio[portfolio.risk_level.eq("High")]
    due_soon = portfolio[portfolio.days_to_renewal.le(90)]
    overdue = 0
    if not actions.empty:
        overdue = int(
            ((pd.to_datetime(actions.due_date).dt.date < as_of) & ~actions.action_status.eq("Completed")).sum()
        )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("High-risk customers", len(high), f"of {len(portfolio)}")
    col2.metric("High-risk ACV", f"${high.annual_contract_value.sum():,.0f}")
    col3.metric("Renewals in 90 days", len(due_soon))
    col4.metric("Overdue actions", overdue)

    st.subheader("Priority queue")
    f1, f2, f3 = st.columns(3)
    risk_filter = f1.multiselect("Risk level", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
    segment_filter = f2.multiselect("Segment", sorted(portfolio.segment.unique()), default=sorted(portfolio.segment.unique()))
    owner_filter = f3.multiselect("Account manager", sorted(portfolio.account_manager.unique()), default=sorted(portfolio.account_manager.unique()))
    visible = portfolio[
        portfolio.risk_level.isin(risk_filter)
        & portfolio.segment.isin(segment_filter)
        & portfolio.account_manager.isin(owner_filter)
    ].sort_values(["risk_score", "annual_contract_value"], ascending=False)
    st.dataframe(
        visible.rename(
            columns={
                "customer_name": "Customer",
                "risk_level": "Risk",
                "risk_score": "Score",
                "annual_contract_value": "ACV",
                "renewal_date": "Renewal",
                "days_to_renewal": "Days",
                "account_manager": "Owner",
                "risk_factors": "Triggered evidence",
                "next_action": "Recommended next action",
            }
        )[["Customer", "Risk", "Score", "ACV", "Renewal", "Days", "Owner", "Triggered evidence", "Recommended next action"]],
        use_container_width=True,
        hide_index=True,
        column_config={"ACV": st.column_config.NumberColumn(format="$%.0f"), "Score": st.column_config.ProgressColumn(min_value=0, max_value=100)},
    )

    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Portfolio Risk vs. ACV Bubble Map")
        st.plotly_chart(render_command_center_bubble(portfolio), use_container_width=True)
    with right:
        st.subheader("Revenue Exposure by Segment")
        st.plotly_chart(render_segment_exposure_bar(high), use_container_width=True)

    d1, d2, d3 = st.columns([1, 1, 1])
    if d1.button(
        "Create portfolio snapshot",
        use_container_width=True,
        disabled=not DEPLOYMENT.writes_enabled,
        help="Persistent snapshots are available in Private Business mode.",
    ):
        require_private_mode(DEPLOYMENT, "Portfolio snapshot creation")
        result = snapshot_portfolio(as_of, DATABASE_PATH)
        st.success(f"Saved {result['customers_assessed']} explainable assessments as of {result['as_of_date']}.")
    d2.download_button(
        "Download operating queue (CSV)",
        data=portfolio_csv(as_of, DATABASE_PATH),
        file_name=f"renewal_queue_{as_of.isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )
    d3.download_button(
        "Download executive brief (HTML)",
        data=executive_html(as_of, DATABASE_PATH),
        file_name=f"renewal_brief_{as_of.isoformat()}.html",
        mime="text/html",
        use_container_width=True,
    )

elif page == "Customer 360":
    page_heading(
        "Evidence workspace",
        "Customer 360",
        "One integrated customer record, one explainable score, and an exact path back to every operational fact.",
    )
    customer_id, selected_name = customer_selector("Customer", "customer_360")
    assessment = assess_customer(customer_id, database_path=DATABASE_PATH)
    customer, contract = assessment["customer"], assessment["contract"]
    days = (date.fromisoformat(contract["renewal_date"]) - date.today()).days if contract else None
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Renewal risk", assessment["risk_level"])
    col2.metric("Weighted score", f"{assessment['risk_score']} / 100")
    col3.metric("Annual contract value", f"${contract['annual_contract_value']:,.0f}" if contract else "Not available")
    col4.metric("Days to renewal", days if days is not None else "Not available")
    risk_message(assessment["risk_level"], f"{selected_name} is {assessment['risk_level'].lower()} risk under the documented policy.")

    summary, contract_tab, usage_tab, support_tab = st.tabs(["Decision context", "Contract", "Usage", "Support"])
    with summary:
        st.markdown(
            f"**{customer['customer_name']}** · {customer['segment']} · {customer['industry']} · {customer['region']}  \n"
            f"Account manager: **{customer['account_manager_name']}** ({customer['account_manager_email']})"
        )
        if assessment["factors"]:
            st.subheader("Score contribution waterfall")
            wf_fig = render_customer_score_waterfall(assessment)
            if wf_fig:
                st.plotly_chart(wf_fig, use_container_width=True)
            else:
                waterfall = pd.DataFrame(assessment["factors"])[["name", "points"]].set_index("name")
                st.bar_chart(waterfall)
        else:
            st.success("No configured renewal-risk factors are currently triggered.")
        st.subheader("Why this score exists")
        for factor in assessment["factors"]:
            with st.expander(f"+{factor['points']} · {factor['name']}", expanded=True):
                st.write(factor["explanation"])
                st.info("Recommended intervention: " + factor["recommended_action"])
                records = evidence_records(factor["evidence_record_ids"], DATABASE_PATH)
                st.caption("Exact source records: " + ", ".join(factor["evidence_record_ids"]))
                st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
        history = pd.DataFrame(assessment_history(customer_id, DATABASE_PATH))
        if not history.empty:
            st.subheader("Persisted risk history")
            st.line_chart(history.set_index("assessed_at")["risk_score"])
            st.caption("Each point is a stored decision-time assessment, not a reconstruction.")
    with contract_tab:
        st.dataframe(pd.DataFrame([contract]) if contract else pd.DataFrame(), use_container_width=True, hide_index=True)
    with connect(DATABASE_PATH) as connection:
        usage = pd.read_sql_query(
            """SELECT usage_event_id, event_date, active_users, seats_purchased, sessions,
                      feature_adoption_pct, source_system
                 FROM product_usage_events WHERE customer_id = ? ORDER BY event_date""",
            connection,
            params=(customer_id,),
        )
        tickets = pd.read_sql_query(
            """SELECT ticket_id, opened_at, resolved_at, priority, ticket_status,
                      ticket_category, csat_score, ticket_summary, source_system
                 FROM support_tickets WHERE customer_id = ? ORDER BY opened_at DESC""",
            connection,
            params=(customer_id,),
        )
    with usage_tab:
        if not usage.empty:
            st.line_chart(usage.set_index("event_date")[["active_users", "seats_purchased"]])
        st.dataframe(usage, use_container_width=True, hide_index=True)
    with support_tab:
        st.dataframe(tickets, use_container_width=True, hide_index=True)

elif page == "Change Timeline":
    page_heading(
        "Temporal intelligence",
        "Risk Change Timeline",
        "See when an account moved, which factors were added, removed, or reweighted, and which operational or human events surrounded the change.",
    )
    customer_id, selected_name = customer_selector("Customer", "timeline_customer")
    if st.button(
        "Capture a current portfolio snapshot",
        disabled=not DEPLOYMENT.writes_enabled,
        help="Persistent snapshots are available in Private Business mode.",
    ):
        require_private_mode(DEPLOYMENT, "Portfolio snapshot creation")
        captured = snapshot_portfolio(date.today(), DATABASE_PATH)
        st.success(f"Captured {captured['customers_assessed']} policy-linked assessments.")
        st.rerun()
    changes = risk_change_history(customer_id, DATABASE_PATH)
    if not changes:
        st.info("No persisted assessments yet. Capture a snapshot to establish the baseline.")
    else:
        change_frame = pd.DataFrame(changes)
        c1, c2, c3 = st.columns(3)
        latest = changes[-1]
        c1.metric("Latest score", latest["risk_score"], latest["risk_level"])
        c2.metric("Stored assessments", len(changes))
        c3.metric("Latest policy", latest["policy"])
        st.subheader("Score trajectory")
        st.line_chart(change_frame.set_index("assessed_at")["risk_score"])
        st.subheader("Explain every transition")
        for change in reversed(changes):
            delta_text = "baseline" if change["score_delta"] is None else f"{change['score_delta']:+d} points"
            with st.expander(
                f"{change['as_of_date']} · {change['risk_level']} {change['risk_score']}/100 · {delta_text}",
                expanded=change is changes[-1],
            ):
                st.write(change["change_explanation"])
                st.caption("Policy: " + change["policy"])
                if change["evidence_record_ids"]:
                    st.caption("Evidence involved: " + ", ".join(change["evidence_record_ids"]))
                    st.dataframe(
                        pd.DataFrame(evidence_records(change["evidence_record_ids"], DATABASE_PATH)),
                        use_container_width=True,
                        hide_index=True,
                    )

    st.subheader(f"Unified account history · {selected_name}")
    events = pd.DataFrame(customer_event_timeline(customer_id, DATABASE_PATH))
    if not events.empty:
        event_types = sorted(events.event_type.unique())
        visible_types = st.multiselect("Event types", event_types, default=event_types)
        st.dataframe(
            events[events.event_type.isin(visible_types)],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No events are available for this customer.")

elif page == "Scenario Lab":
    page_heading(
        "What-if workspace",
        "Intervention Scenario Lab",
        "Test explicit business interventions against the same rules. Scenarios never alter source records and are not forecasts.",
    )
    customer_id, selected_name = customer_selector("Customer", "scenario_customer")
    a1, a2, a3 = st.columns(3)
    recovery = a1.slider("Recover inactive seats", 0, 100, 25, 5, format="%d%%")
    resolve_critical = a2.checkbox("Resolve all open critical tickets", value=False)
    extension = a3.slider("Renewal extension", 0, 180, 0, 15, format="%d days")
    scenario = simulate_customer(
        customer_id,
        usage_recovery_pct=recovery,
        resolve_critical=resolve_critical,
        renewal_extension_days=extension,
        database_path=DATABASE_PATH,
    )
    baseline, simulated = scenario["baseline"], scenario["simulated"]
    st.plotly_chart(render_scenario_gauge(baseline["risk_score"], simulated["risk_score"]), use_container_width=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Current score", baseline["risk_score"], baseline["risk_level"])
    col2.metric("Scenario score", simulated["risk_score"], simulated["risk_level"])
    col3.metric("Risk reduction", baseline["risk_score"] - simulated["risk_score"], "points")
    comparison = pd.DataFrame(
        [
            {"Factor": factor["name"], "Current points": factor["points"], "Scenario points": 0}
            for factor in baseline["factors"]
        ]
    )
    for factor in simulated["factors"]:
        if comparison.empty or factor["name"] not in comparison.Factor.values:
            comparison.loc[len(comparison)] = [factor["name"], 0, factor["points"]]
        else:
            comparison.loc[comparison.Factor.eq(factor["name"]), "Scenario points"] = factor["points"]
    st.subheader("Rule-by-rule impact")
    st.dataframe(comparison, use_container_width=True, hide_index=True)
    st.caption(
        f"Assumption: activate {recovery}% of currently inactive seats; "
        f"critical-ticket resolution = {resolve_critical}; renewal extension = {extension} days."
    )
    if st.button(
        "Save this governed scenario",
        type="primary",
        disabled=not DEPLOYMENT.writes_enabled,
        help="The simulation remains interactive. Saving is available in Private Business mode.",
    ):
        require_private_mode(DEPLOYMENT, "Scenario persistence")
        scenario_id = save_scenario(customer_id, scenario, DATABASE_PATH)
        st.success(f"Scenario saved with audit ID {scenario_id}.")
    saved = pd.DataFrame(list_scenarios(customer_id, DATABASE_PATH))
    if not saved.empty:
        st.subheader(f"Saved scenarios for {selected_name}")
        st.dataframe(saved, use_container_width=True, hide_index=True)

elif page == "Capacity Planner":
    page_heading(
        "Resource allocation",
        "Capacity-Aware Intervention Planner",
        "Allocate limited hours, budget, escalation slots, and enablement capacity to the highest-value evidence-backed interventions.",
    )
    as_of = st.date_input("Planning date", value=date.today(), key="planner_as_of")
    p1, p2, p3, p4 = st.columns(4)
    available_hours = p1.number_input("Team hours", min_value=0.0, value=40.0, step=4.0)
    available_budget = p2.number_input("Intervention budget", min_value=0.0, value=5_000.0, step=250.0)
    support_slots = p3.number_input("Support escalation slots", min_value=0, value=3, step=1)
    enablement_slots = p4.number_input("Enablement slots", min_value=0, value=4, step=1)
    max_per_customer = st.slider("Maximum interventions per customer", 1, 3, 2)
    plan = plan_interventions(
        available_hours=available_hours,
        available_budget=available_budget,
        support_slots=int(support_slots),
        enablement_slots=int(enablement_slots),
        as_of=as_of,
        max_interventions_per_customer=max_per_customer,
        database_path=DATABASE_PATH,
    )
    summary = plan["summary"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions funded", summary["selected_count"])
    c2.metric("Customers covered", summary["customers_covered"])
    c3.metric("High-priority ACV covered", f"${summary['acv_covered']:,.0f}")
    c4.metric("Addressable rule points", summary["addressable_points"])
    st.caption(
        f"Allocated {summary['hours_allocated']:,.1f}/{available_hours:,.1f} hours and "
        f"${summary['budget_allocated']:,.0f}/${available_budget:,.0f}."
    )
    items = pd.DataFrame(plan["items"])
    selected_items = items[items.selected] if not items.empty else items
    deferred_items = items[~items.selected] if not items.empty else items
    st.subheader("Funded intervention portfolio")
    if selected_items.empty:
        st.warning("No intervention fits the current constraints. Increase at least one constrained resource.")
    else:
        display_columns = [
            "priority_rank", "customer_name", "risk_level", "risk_score",
            "annual_contract_value", "factor_name", "intervention", "delivery_team",
            "estimated_hours", "estimated_cost", "addressable_points", "decision_value",
        ]
        st.dataframe(selected_items[display_columns], use_container_width=True, hide_index=True)
        st.download_button(
            "Download funded plan (CSV)",
            selected_items.to_csv(index=False).encode("utf-8"),
            file_name=f"capacity_plan_{as_of.isoformat()}.csv",
            mime="text/csv",
        )
    owner = st.text_input("Plan owner", value="Revenue Operations")
    if st.button(
        "Save allocation decision",
        type="primary",
        disabled=not DEPLOYMENT.writes_enabled,
        help="Saving allocation decisions is available in Private Business mode.",
    ):
        require_private_mode(DEPLOYMENT, "Capacity plan persistence")
        try:
            plan_id = save_capacity_plan(plan, owner, DATABASE_PATH)
            st.success(f"Capacity plan saved with audit ID {plan_id}.")
        except ValueError as error:
            st.error(str(error))
    with st.expander(f"Deferred interventions ({len(deferred_items)})"):
        if not deferred_items.empty:
            st.dataframe(
                deferred_items[["priority_rank", "customer_name", "intervention", "decision_value", "deferral_reason"]],
                use_container_width=True,
                hide_index=True,
            )
    with st.expander("How prioritization works"):
        st.code("decision value = addressable rule points × ACV × renewal urgency ÷ estimated hours ÷ 1,000")
        st.write(
            "Candidates are ranked deterministically, then selected in order while enforcing every capacity constraint. "
            "This is a transparent allocation heuristic. It is not a predicted financial return or a claim of mathematical optimality."
        )
    saved_plans = pd.DataFrame(list_capacity_plans(DATABASE_PATH))
    if not saved_plans.empty:
        st.subheader("Saved allocation decisions")
        st.dataframe(saved_plans, use_container_width=True, hide_index=True)

elif page == "Actions & Decisions":
    page_heading(
        "Execution workspace",
        "Actions & Decision Log",
        "Turn evidence into accountable work, then retain the human judgment that followed.",
    )
    customer_id, selected_name = customer_selector("Customer", "action_customer")
    assessment = assess_customer(customer_id, database_path=DATABASE_PATH)
    suggested = assessment["recommended_actions"][0] if assessment["recommended_actions"] else "Schedule a routine customer health review."
    owner = assessment["customer"]["account_manager_name"]
    evidence = [record_id for factor in assessment["factors"] for record_id in factor["evidence_record_ids"]]
    with st.form("new_action", clear_on_submit=True):
        st.subheader("Assign an intervention")
        action_text = st.text_area("Action", value=suggested)
        c1, c2, c3 = st.columns(3)
        action_owner = c1.text_input("Owner", value=owner)
        priority = c2.selectbox("Priority", ["High", "Critical", "Medium", "Low"])
        due = c3.date_input("Due date", value=date.today() + timedelta(days=7))
        submitted = st.form_submit_button(
            "Create action",
            type="primary",
            disabled=not DEPLOYMENT.writes_enabled,
            help="Creating actions is available in Private Business mode.",
        )
        if submitted:
            require_private_mode(DEPLOYMENT, "Action creation")
            action_id = create_action(
                customer_id, action_text, action_owner, priority, due, evidence, DATABASE_PATH
            )
            log_decision(
                customer_id,
                "Action assigned",
                action_owner,
                action_text,
                action_id,
                DATABASE_PATH,
            )
            st.success(f"Action created: {action_id}")

    customer_actions = pd.DataFrame(list_actions(customer_id, DATABASE_PATH))
    if not customer_actions.empty:
        st.subheader("Action register")
        st.dataframe(customer_actions, use_container_width=True, hide_index=True)
        open_actions = customer_actions.action_id.tolist()
        c1, c2, c3 = st.columns([2, 1, 1])
        action_choice = c1.selectbox("Action to update", open_actions, format_func=lambda value: customer_actions.loc[customer_actions.action_id.eq(value), "action_text"].iloc[0])
        new_status = c2.selectbox("New status", ["Open", "In Progress", "Blocked", "Completed"])
        if c3.button(
            "Update status",
            use_container_width=True,
            disabled=not DEPLOYMENT.writes_enabled,
            help="Updating workflow records is available in Private Business mode.",
        ):
            require_private_mode(DEPLOYMENT, "Action status update")
            update_action_status(action_choice, new_status, DATABASE_PATH)
            st.success("Action status updated. Refreshing the register…")
            st.rerun()
    else:
        st.info("No actions have been assigned to this customer yet.")

    with st.form("decision_log", clear_on_submit=True):
        st.subheader("Record a human decision")
        d1, d2 = st.columns(2)
        event_type = d1.selectbox("Decision type", ["Customer meeting", "Escalation", "Commercial decision", "Risk accepted", "Executive review"])
        actor = d2.text_input("Decision maker", value=owner)
        notes = st.text_area("What was decided, and why?")
        if st.form_submit_button(
            "Add to decision log",
            disabled=not DEPLOYMENT.writes_enabled,
            help="Decision logging is available in Private Business mode.",
        ):
            require_private_mode(DEPLOYMENT, "Decision logging")
            event_id = log_decision(
                customer_id, event_type, actor, notes, database_path=DATABASE_PATH
            )
            st.success(f"Decision recorded: {event_id}")
    decisions = pd.DataFrame(list_decisions(customer_id, DATABASE_PATH))
    if not decisions.empty:
        st.subheader(f"Decision timeline · {selected_name}")
        st.dataframe(decisions, use_container_width=True, hide_index=True)

elif page == "Policy Studio":
    page_heading(
        "Decision governance",
        "Renewal-Risk Policy Studio",
        "Edit business policy outside the code, preview portfolio consequences, and enforce maker-checker approval before activation.",
    )
    active_policy_id, active_parameters = get_active_policy(DATABASE_PATH)
    versions = list_policy_versions(DATABASE_PATH)
    active_version = next(
        (version for version in versions if version["policy_version_id"] == active_policy_id), None
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Active version", f"v{active_version['version_number']}" if active_version else "Baseline")
    c2.metric("Governed parameters", len(active_parameters))
    c3.metric("Drafts awaiting review", sum(version["policy_status"] == "Draft" for version in versions))
    if active_version:
        st.info(
            f"Active policy: **{active_version['policy_name']}** · activated "
            f"{active_version['activated_at']} · rationale: {active_version['rationale']}"
        )

    st.subheader("Draft proposed parameters")
    editor_source = pd.DataFrame(policy_editor_rows(active_parameters))[
        ["parameter_name", "category", "label", "value", "description"]
    ]
    edited = st.data_editor(
        editor_source,
        use_container_width=True,
        hide_index=True,
        disabled=["parameter_name", "category", "label", "description"],
        column_config={"value": st.column_config.NumberColumn("Proposed value", format="%.2f")},
        key="policy_editor",
    )
    proposed_parameters = {
        str(row.parameter_name): float(row.value) for row in edited.itertuples(index=False)
    }
    policy_errors = validate_policy(proposed_parameters)
    if policy_errors:
        for error in policy_errors:
            st.error(error)
    else:
        impact = preview_policy_impact(proposed_parameters, date.today(), DATABASE_PATH)
        i1, i2, i3 = st.columns(3)
        i1.metric("Classifications changed", impact["customers_changed"])
        i2.metric("ACV reclassified", f"${impact['acv_reclassified']:,.0f}")
        i3.metric("Average score movement", f"{impact['average_score_delta']:+.1f}")
        impact_frame = pd.DataFrame(impact["rows"])
        changed_only = st.checkbox("Show only classification changes", value=False)
        if changed_only:
            impact_frame = impact_frame[impact_frame.classification_changed]
        st.dataframe(impact_frame, use_container_width=True, hide_index=True)

    with st.form("save_policy_draft", clear_on_submit=True):
        st.subheader("Submit policy for review")
        s1, s2 = st.columns(2)
        policy_name = s1.text_input("Policy name", value="Renewal policy proposal")
        created_by = s2.text_input("Policy author")
        rationale = st.text_area("Business rationale and expected effect")
        save_draft = st.form_submit_button(
            "Save draft policy",
            type="primary",
            disabled=not DEPLOYMENT.writes_enabled,
            help="Policy persistence is available in Private Business mode.",
        )
        if save_draft:
            require_private_mode(DEPLOYMENT, "Policy draft persistence")
            if policy_errors:
                st.error("Correct the policy validation errors before saving.")
            else:
                try:
                    draft_id = create_policy_draft(
                        policy_name, proposed_parameters, created_by, rationale, DATABASE_PATH
                    )
                    st.success(f"Draft saved for independent review: {draft_id}")
                except ValueError as error:
                    st.error(str(error))

    versions = list_policy_versions(DATABASE_PATH)
    drafts = [version for version in versions if version["policy_status"] == "Draft"]
    if drafts:
        with st.form("review_policy"):
            st.subheader("Independent maker-checker review")
            draft_id = st.selectbox(
                "Draft",
                [version["policy_version_id"] for version in drafts],
                format_func=lambda value: next(
                    f"v{version['version_number']} · {version['policy_name']} · by {version['created_by']}"
                    for version in drafts
                    if version["policy_version_id"] == value
                ),
            )
            decision = st.radio("Decision", ["Approved", "Rejected"], horizontal=True)
            reviewer = st.text_input("Independent reviewer")
            review_notes = st.text_area("Decision notes")
            if st.form_submit_button(
                "Record governance decision",
                disabled=not DEPLOYMENT.writes_enabled,
                help="Policy approval is available in Private Business mode.",
            ):
                require_private_mode(DEPLOYMENT, "Policy approval")
                try:
                    decide_policy(draft_id, decision, reviewer, review_notes, DATABASE_PATH)
                    st.success(f"Policy {decision.lower()}. The active scoring policy is now updated if approved.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
    st.subheader("Policy version register")
    st.dataframe(pd.DataFrame(versions), use_container_width=True, hide_index=True)

else:
    page_heading(
        "Governance workspace",
        "Data Health",
        "Inspect source lineage, quality gates, checksums, warning approvals, and the audit history behind the active business dataset.",
    )
    with connect(DATABASE_PATH) as connection:
        runs = pd.read_sql_query("SELECT * FROM ingestion_runs ORDER BY started_at DESC", connection)
        issues = pd.read_sql_query("SELECT * FROM data_quality_issues ORDER BY created_at DESC", connection)
        manifests = pd.read_sql_query("SELECT * FROM source_file_manifest ORDER BY ingestion_run_id, source_file", connection)
    c1, c2, c3 = st.columns(3)
    latest_status = runs.iloc[0].run_status if not runs.empty else "Never run"
    c1.metric("Latest ingestion", latest_status)
    c2.metric("Recorded quality issues", len(issues))
    c3.metric("Manifested source files", len(manifests))
    run_tab, issue_tab, manifest_tab = st.tabs(["Ingestion runs", "Quality issues", "File lineage"])
    with run_tab:
        st.dataframe(runs, use_container_width=True, hide_index=True)
    with issue_tab:
        st.dataframe(issues, use_container_width=True, hide_index=True)
    with manifest_tab:
        st.dataframe(manifests, use_container_width=True, hide_index=True)

st.divider()
st.caption(
    f"{DEPLOYMENT.label} · {business_profile['organization_name']} · {business_profile['data_classification']} · "
    "Deterministic business rules · Source-linked evidence · Local SQLite system of record"
)
