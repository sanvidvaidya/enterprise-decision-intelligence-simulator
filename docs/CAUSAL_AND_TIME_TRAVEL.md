# Causal DAG Analysis and Time-Travel Event Replay

Enterprise Decision Simulator provides deterministic causal inference and point-in-time counterfactual trajectory simulation alongside its rule-based risk scoring and capacity planner.

## 1. Structural Causal Model and Causal DAG

The structural causal model (`decision_intelligence.causal`) formalizes enterprise churn mechanics as a directed acyclic graph (DAG) of 9 nodes and 12 directed edges across four categories:
- **Exogenous Drivers:** Contract ACV (`contract_acv`), Days to Renewal (`days_to_renewal`), Executive Sponsor Engaged (`executive_sponsor_engaged`).
- **Operational Drivers:** Critical Support Tickets (`critical_tickets`).
- **Customer Health Mediators:** CSAT Score (`csat_score`), Feature Adoption (`feature_adoption`), Seat Utilization (`seat_utilization`), Active User Decline (`active_user_decline`).
- **Target Outcome:** Renewal Risk Score (`renewal_risk_score`).

### Directed Edge Topology
```text
critical_tickets ----------> csat_score -----------> seat_utilization
      |                          |                           |
      |                          v                           v
      |----------> active_user_decline ---------> renewal_risk_score
      |                                                      ^
      +------------------------------------------------------+
```

### Key Capabilities
1. **Pearl's Do-Calculus (Edge Cutting):**
   Evaluating $do(X = x)$ severs inbound structural edges into node $X$, simulating policy interventions rather than passive conditioning.
2. **Mediation Decomposition:**
   Decomposes total effect ($TE$) into direct effect ($DE$) and indirect effect ($IE$) through downstream mediators, ensuring $TE = DE + IE$.
3. **Abduction-Action-Prediction Counterfactuals:**
   Extracts exogenous background variables $U$ from observed customer state, applies intervention $do(X = x)$, and evaluates the counterfactual outcome under identical latent conditions.
4. **Deterministic Root-Cause Attribution:**
   Computes counterfactual marginal contributions of each active risk factor and normalizes them into percentage shares totaling 100%.

---

## 2. Event-Stream Time-Travel Replay Engine

The time-travel replay engine (`decision_intelligence.replay`) reconstructs exact historical customer states without future data leakage:

1. **Strict Point-in-Time Reconstruction:**
   When evaluating customer health as of date $T$, only events and records with timestamps $\le T$ are considered. Future ticket escalations and usage changes are strictly excluded.
2. **Chronological Event Stream:**
   Synthesizes customer-level chronological streams combining contract starts, monthly usage audits, seat changes, ticket open/close events, and risk threshold crossings.
3. **Counterfactual Trajectory Branching:**
   Enables branching at any historical checkpoint $T_{\text{branch}}$:
   - Prior to $T_{\text{branch}}$, counterfactual scores match factual history.
   - At $T_{\text{branch}}$, an intervention (for example, executive ticket resolution or adoption enablement) is applied.
   - Forward checkpoints reflect the counterfactual trajectory, quantifying avoided high-risk periods and protected Annual Contract Value (ACV).

---

## 3. REST API Endpoints

The API bridge (`backend_api.py`) exposes five new endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/causal/graph` | Returns nodes, edges, categories, and descriptions for the 9-node DAG |
| `GET` | `/api/causal/customer?id=...` | Returns baseline state, root causes, and simulated interventions for a customer |
| `GET` | `/api/replay/customer?id=...` | Returns historical checkpoints and event stream for point-in-time replay |
| `POST` | `/api/causal/counterfactual` | Executes Pearl's 3-step abduction counterfactual query for custom interventions |
| `POST` | `/api/replay/branch` | Branches a counterfactual trajectory at a historical date and compares factual vs counterfactual |
