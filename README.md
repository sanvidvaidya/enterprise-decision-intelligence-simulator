# 📊 Enterprise Decision Intelligence Simulator

> **The Core Mission:**  
> *Transform enterprise customer renewal risk into a deterministic, causally verifiable, and mathematically auditable decision science — without black-box AI hallucinations or unexplainable scores.*

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://enterprise-decision-intelligence-si.vercel.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: Passing](https://img.shields.io/badge/tests-66%20passed-emerald.svg)](tests/)

---

## 💡 Explain It To Me Like I'm Five: How I Created This & What It Does

Imagine you run a subscription software company with 100 enterprise corporate customers paying you millions of dollars a year.
Every month, some customers silently decide **not** to renew their contracts ("customer churn"), which costs your company millions.

Today, executive teams try to solve this in two flawed ways:
1. **Gut Feelings & Optimism:** They ask account managers, who almost always say: *"Everything is fine, the client loves us!"* — until the client cancels.
2. **Black-Box AI Models:** They buy expensive machine learning software that spits out a score like: `Risk: 84%`. But when the VP of Sales asks: *"Why is it 84% and what exact action will fix it?"*, the black box can't answer. It's guessing based on opaque correlations.

### How I Built This Simulator to Fix It
**I built a deterministic, auditable flight simulator for enterprise revenue decisions.**

1. **The Four Unified Feeds:** It ingests real company data across **CRM accounts**, **legal contracts**, **daily product usage** (did their employees stop logging in?), and **support tickets** (are they angry about unresolved bugs?).
2. **Zero Black-Box Guessing:** Every single risk score is computed by transparent, audited mathematical business rules. Every point of risk links directly to the exact database row that caused it (e.g. *"Seat utilization dropped by 42% over the last 90 days; Contract renews in 45 days"*).
3. **The What-If Flight Simulator:** Executives can simulate real-world actions without touching production data: *"If we send an engineer to fix their 3 open tickets this week and offer a 90-day contract extension, does their risk drop from Critical to Safe?"*
4. **Causal Brain (Structural Causal Model):** Using Nobel-laureate-grade causal mathematics (Pearl's do-calculus), it proves whether poor product usage actually *caused* the customer to leave, or if both were caused by a hidden third factor (like a corporate reorganization).
5. **Game-Theoretic War Room:** It calculates how competitors will react (e.g. predatory discounting or poaching key users) using Nash Equilibrium game theory.

---

## 💼 The Real Business Reason Why This Exists

In enterprise B2B SaaS, **Net Revenue Retention (NRR)** is the single most important metric driving company valuation:

1. **The Compounding Value Destruction of Churn:** Losing just 5% of Annual Contract Value (ACV) to avoidable churn can erase 30% to 50% of an enterprise's market valuation over a 3-year horizon.
2. **Account Team Scarcity & Capacity Planning:** Customer success managers cannot save everyone. They have limited working hours, limited executive escalation slots, and strict intervention budgets. The simulator includes a **Capacity-Aware Intervention Planner** that mathematically solves for the highest-return intervention portfolio under real labor and budget constraints.
3. **Audited Governance (Maker-Checker Policy Studio):** In regulated enterprises, risk criteria cannot be silently altered. The simulator features a **Versioned Policy Studio** where threshold changes require independent review and approval before reclassifying millions in portfolio ACV.
4. **Distinguishing Correlation from Causation:** Standard AI often makes disastrous recommendations because it confuses correlation with causation (e.g. noticing that churned customers file lots of support tickets, and concluding the team should stop answering support tickets). The simulator's **Causal DAG** isolates genuine causal mechanisms.
5. **Game-Theoretic Defensive Strategy:** In competitive markets, retaining accounts requires anticipating rival counter-moves. The simulator's **Competitive Vulnerability Index (CVI)** and Minimax solvers model strategic equilibria.

---

## 🌟 What's New: The Groundbreaking Expansion

We've expanded the simulator with four advanced mathematical and real-time operational engines:

| Feature Engine | Mathematical Foundation / Spec | What It Solves |
| :--- | :--- | :--- |
| **Structural Causal Model (SCM) & Causal DAG** | Judea Pearl's do-calculus, DAG (9 nodes, 12 edges) | Mathematically proves true root cause and calculates direct vs. indirect causal effects of interventions, eliminating spurious correlations. |
| **Event-Stream Time-Travel & Counterfactual Replay** | Immutable event stream, point-in-time state reconstruction | Reconstructs the exact state of any account at historical dates without future data leakage, allowing teams to test counterfactual "what-if" decisions. |
| **Live Telemetry Ingestion & Action Dispatch** | Streaming webhooks (`/api/stream/usage`, `/api/stream/ticket`) | Ingests real-time product events and automatically dispatches operational interventions (e.g. triggering executive outreach or emergency engineering triage). |
| **Game-Theoretic Competitor Equilibrium Models** | Minimax, Nash Equilibrium, Payoff Matrices | Simulates competitor predatory moves (counter-discounting, aggressive feature matching) and scores portfolio accounts on the Competitive Vulnerability Index (CVI). |
| **Capacity-Aware Intervention Planner** | Knapsack / Constrained linear optimization | Optimizes allocation of limited account manager hours, escalation slots, and budget across at-risk accounts to maximize protected ACV. |
| **Maker-Checker Policy Studio** | Formal multi-version policy governance | Requires dual-party approval before any rule or threshold alteration is activated across the active customer portfolio. |

---

## 🏗️ Technical Architecture

```text
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                           ENTERPRISE DATA SOURCES                           │
  │   - CRM Accounts (Salesforce)          - Subscription Contracts             │
  │   - Daily Product Usage Logs           - Technical Support Tickets (Zendesk)│
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                      DECISION INTELLIGENCE CORE (Python)                    │
  │                                                                             │
  │   ┌───────────────────────────┐         ┌───────────────────────────────┐   │
  │   │ Deterministic Rules Core  │◀───────▶│ Local Relational SQLite Store │   │
  │   │ - 100% Explainable Scoring│         │ - Public Demo (Synthetic)     │   │
  │   │ - Source Row Traceability │         │ - Private Business (Governed) │   │
  │   └─────────────┬─────────────┘         └───────────────────────────────┘   │
  │                 │                                                           │
  │                 ▼                                                           │
  │   ┌───────────────────────────┐         ┌───────────────────────────────┐   │
  │   │ Structural Causal Model   │         │ Historical Event Replay       │   │
  │   │ - 9-Node Causal DAG       │         │ - Zero Data Leakage           │   │
  │   │ - Pearl's Do-Calculus     │         │ - Counterfactual Trajectories │   │
  │   └─────────────┬─────────────┘         └───────────────────────────────┘   │
  │                 │                                                           │
  │                 ▼                                                           │
  │   ┌───────────────────────────┐         ┌───────────────────────────────┐   │
  │   │ Game-Theoretic War Room   │         │ Capacity-Aware Planner        │   │
  │   │ - Competitor Minimax      │         │ - Resource-Constrained Hours  │   │
  │   │ - Nash Equilibrium Payoffs│         │ - Maximized Protected ACV     │   │
  │   └───────────────────────────┘         └───────────────────────────────┘   │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                          DUAL DEPLOYMENT WORKSPACES                         │
  │                                                                             │
  │   ┌───────────────────────────────────┐  ┌──────────────────────────────┐   │
  │   │ Executive Command Center          │  │ Real-Time Streaming & API    │   │
  │   │ - Customer 360 & Factor Trees     │  │ - Telemetry Webhook Ingest   │   │
  │   │ - Interactive Scenario Lab        │  │ - Automated Action Dispatch  │   │
  │   │ - Policy Studio (Maker-Checker)   │  │ - REST Endpoints for Bi-Sync │   │
  │   └───────────────────────────────────┘  └──────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Set Up the Virtual Environment
```bash
git clone https://github.com/sanvidvaidya/enterprise-decision-intelligence-simulator.git
cd enterprise-decision-intelligence-simulator
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scriptsctivate
pip install -r requirements.txt
```

### 2. Launch the Public Demonstration
```bash
# Safe default: loads isolated synthetic demonstration portfolio
python -m streamlit run streamlit_app.py
```
Open the local URL printed in the terminal (default: `http://localhost:8501`).

### 3. Run the Comprehensive Test Suite
```bash
# Runs all 66 unit, integration, and causal regression tests
pytest
```

---

## 🔒 Two Enforced Deployment Modes

- **Public Demo (Safe Default):** Generates an ephemeral in-memory synthetic dataset. Uploads and persistent modifications are disabled. Ideal for public showcases and Streamlit Community Cloud.
- **Private Business (Opt-in):** Activated via `EDS_DEPLOYMENT_MODE="private_business"`. Unlocks governed five-file CSV onboarding, persistent SQLite storage, and the maker-checker Policy Studio for authorized teams.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
