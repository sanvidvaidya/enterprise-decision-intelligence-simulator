# Live Event Ingestion & Action Dispatch Bridge

This document details the real-time operational layer of the Enterprise Decision Simulator: streaming telemetry ingestion, support desk ticket webhooks, contract updates, and the closed-loop action dispatch bridge.

---

## 1. Architectural Overview

The operational layer connects streaming business events to the Structural Causal Model (SCM) and the deterministic risk engine:

```
[External Webhooks]
  - Telemetry (Segment / Mixpanel)  --> POST /api/events/ingest (usage)
  - Support Desk (Zendesk / JSM)    --> POST /api/events/ingest (ticket)
  - Billing (Stripe / Chargebee)    --> POST /api/events/ingest (contract)
           |
           v
[Validation & Idempotency Layer]
           |
           v
[SQLite Relational Store]
           |
           +--> Instant Causal Risk Re-Assessment
           |      - Recalculate Risk Score (0-100)
           |      - Abduct Latent Noise & Extract Causal Drivers
           |      - Alert if Risk enters 'High' or delta >= 15 pts
           |
           v
[Action Dispatch Bridge]
  - Slack Block Kit Alerts          --> POST /api/dispatch/action (slack)
  - Automated CRM / Linear Tasks    --> POST /api/dispatch/action (crm_task)
  - Webhook Notification Envelopes  --> POST /api/dispatch/action (webhook)
           |
           v
[Audit Log & Closed-Loop Continuity]
  - action_dispatches audit table
  - account_actions status update ('In Progress')
  - decision_events traceability entry
```

---

## 2. Ingestion Contracts (`POST /api/events/ingest`)

The ingestion endpoint accepts three event categories:

### A. Usage & Telemetry Events
```json
{
  "event_type": "usage",
  "payload": {
    "customer_id": "CUS-020",
    "event_date": "2026-09-01",
    "active_users": 42,
    "seats_purchased": 50,
    "sessions": 320,
    "feature_adoption_pct": 74.5,
    "source_system": "segment_telemetry"
  }
}
```
* **Validation Rules:**
  * `customer_id` must match an existing portfolio customer.
  * `event_date` must follow strict ISO `YYYY-MM-DD`.
  * `active_users >= 0`, `seats_purchased > 0`, `sessions >= 0`.
  * `feature_adoption_pct` must lie between `0.0` and `100.0`.
* **Idempotency:** Upserts on unique `(customer_id, event_date)` pair.

### B. Support Desk Tickets
```json
{
  "event_type": "ticket",
  "payload": {
    "customer_id": "CUS-020",
    "priority": "Critical",
    "ticket_status": "Open",
    "ticket_category": "API Integration",
    "ticket_summary": "Production webhook signature verification failing.",
    "csat_score": 1,
    "opened_at": "2026-09-02T10:15:00Z",
    "source_system": "zendesk"
  }
}
```
* **Validation Rules:**
  * `priority` must be one of `Low`, `Normal`, `High`, or `Critical`.
  * `ticket_status` must be one of `Open`, `In Progress`, `Resolved`, or `Closed`.
  * `csat_score` (if present) must be between 1 and 5.
* **Alert Trigger:** Automatically flags `alert_triggered = true` when priority is `Critical` or new score enters `High`.

### C. Contract & Renewal Events
```json
{
  "event_type": "contract",
  "payload": {
    "customer_id": "CUS-020",
    "annual_contract_value": 125000.0,
    "contract_status": "Active",
    "renewal_date": "2026-11-30",
    "auto_renew": true
  }
}
```

---

## 3. Real-Time Ingestion Response Envelope

Every successful ingestion returns the updated risk profile and top causal drivers:

```json
{
  "success": true,
  "event_type": "usage_telemetry",
  "event_id": "usage-stream-a1b2c3d4e5f6",
  "customer_id": "CUS-020",
  "message": "Usage telemetry successfully ingested and risk recomputed.",
  "previous_risk_score": 95,
  "new_risk_score": 50,
  "previous_risk_level": "High",
  "new_risk_level": "Medium",
  "score_delta": -45,
  "top_causal_drivers": [
    {"driver": "seat_utilization", "value": 0.84},
    {"driver": "critical_tickets", "value": 0.0}
  ],
  "alert_triggered": false,
  "details": {
    "active_users": 42,
    "seats_purchased": 50,
    "utilization": 0.84,
    "sessions": 320,
    "feature_adoption_pct": 74.5
  }
}
```

---

## 4. Action Dispatch Bridge (`POST /api/dispatch/action`)

When an intervention is planned or an alert is triggered, the dispatch bridge sends actionable payloads to external destinations:

```json
{
  "customer_id": "CUS-020",
  "channel": "slack",
  "action_text": "Assign Senior Solutions Architect for onboarding stabilization",
  "simulate": true
}
```

### Supported Channels
1. **`slack`:** Formats an executive Slack Block Kit card with risk level, score, annual contract value, account owner, and recommended action.
2. **`webhook`:** Canonical event envelope sent via HTTP POST with `decision_intelligence.action_dispatched` event schema, full factor breakdown, and custom metadata.
3. **`crm_task`:** Creates a structured renewal risk task payload for HubSpot, Salesforce, Linear, or Jira.
4. **`email`:** Formats an urgent risk notification for the assigned account manager.

### Closed-Loop Action Continuity
When `action_id` is supplied:
1. Updates `account_actions.action_status` to `'In Progress'`.
2. Inserts an immutable audit record into `decision_events`.
3. Records the dispatch payload, destination, status, and HTTP response code in `action_dispatches`.

---

## 5. Audit History (`GET /api/dispatch/history`)

Inspect past dispatches filtered by customer:
```http
GET /api/dispatch/history?customer_id=CUS-020&limit=20
```
