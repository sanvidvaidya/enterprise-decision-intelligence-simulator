"""Tests for Live Event Ingestion and Action Dispatch Bridge."""

from datetime import date
import io
import json
from pathlib import Path
import sys
from uuid import uuid4

import pandas as pd
import pytest

from decision_intelligence.database import SCHEMA_PATH, connect
from decision_intelligence.generate_data import build_extracts
from decision_intelligence.ingestion import LOAD_ORDER, _upsert_extract
from decision_intelligence.ingest_stream import (
    ingest_usage_event,
    ingest_support_ticket,
    ingest_contract_event,
    IngestionResult,
)
from decision_intelligence.dispatch import (
    dispatch_action,
    list_dispatch_history,
    ensure_dispatch_table,
    DispatchRecord,
)

# Project root for backend API testing
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from backend_api import DecisionSimulatorAPIHandler


class MockSocket:
    """Mock socket simulating HTTP client request/response stream."""

    def __init__(self, request_bytes: bytes) -> None:
        self.rfile = io.BytesIO(request_bytes)
        self.output = io.BytesIO()

    def makefile(self, mode: str, *args, **kwargs) -> io.BytesIO:
        if "r" in mode:
            return self.rfile
        return self.output

    def sendall(self, data: bytes) -> None:
        self.output.write(data)


def execute_api_call(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    """Dispatch a test request directly to the API handler."""
    body_bytes = json.dumps(body).encode("utf-8") if body else b""
    headers = [
        f"{method} {path} HTTP/1.1",
        "Host: localhost",
        f"Content-Length: {len(body_bytes)}",
        "Content-Type: application/json",
        "",
        "",
    ]
    raw_req = "\r\n".join(headers).encode("utf-8") + body_bytes
    sock = MockSocket(raw_req)
    DecisionSimulatorAPIHandler(sock, ("127.0.0.1", 8002), None)

    raw_resp = sock.output.getvalue().decode("utf-8")
    header_part, _, body_part = raw_resp.partition("\r\n\r\n")
    status_line = header_part.splitlines()[0]
    status_code = int(status_line.split()[1])
    payload = json.loads(body_part) if body_part else {}
    return status_code, payload


@pytest.fixture
def memory_db():
    """Shared in-memory SQLite fixture with synthetic data loaded."""
    uri = f"file:test-ingest-{uuid4()}?mode=memory&cache=shared"
    anchor = connect(uri)
    anchor.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    extracts = {name: pd.DataFrame(rows) for name, rows in build_extracts().items()}
    for filename in LOAD_ORDER:
        _upsert_extract(anchor, filename, extracts[filename])
    anchor.commit()
    yield uri
    anchor.close()


# -----------------------------------------------------------------------------
# Ingestion Unit Tests
# -----------------------------------------------------------------------------


def test_ingest_usage_event_success(memory_db):
    payload = {
        "customer_id": "CUS-020",
        "event_date": "2026-09-01",
        "active_users": 40,
        "seats_purchased": 50,
        "sessions": 450,
        "feature_adoption_pct": 80.0,
        "source_system": "segment_live",
    }
    result = ingest_usage_event(payload, database_path=memory_db)
    assert result.success is True
    assert result.customer_id == "CUS-020"
    assert result.event_type == "usage_telemetry"
    assert result.new_risk_score >= 0
    assert result.details["utilization"] == 0.8
    assert result.details["active_users"] == 40


def test_ingest_usage_event_validation_errors(memory_db):
    # Non-existent customer
    with pytest.raises(ValueError, match="does not exist in portfolio"):
        ingest_usage_event({"customer_id": "NON_EXISTENT", "event_date": "2026-09-01"}, database_path=memory_db)

    # Invalid adoption percentage
    with pytest.raises(ValueError, match="feature_adoption_pct"):
        ingest_usage_event({
            "customer_id": "CUS-020",
            "event_date": "2026-09-01",
            "feature_adoption_pct": 150.0,
        }, database_path=memory_db)

    # Invalid negative active users
    with pytest.raises(ValueError, match="active_users cannot be negative"):
        ingest_usage_event({
            "customer_id": "CUS-020",
            "event_date": "2026-09-01",
            "active_users": -5,
        }, database_path=memory_db)


def test_ingest_support_ticket_critical_triggers_alert(memory_db):
    payload = {
        "customer_id": "CUS-020",
        "priority": "Critical",
        "ticket_status": "Open",
        "ticket_category": "Production Outage",
        "ticket_summary": "System outage during month-end closing.",
        "csat_score": 1,
    }
    result = ingest_support_ticket(payload, database_path=memory_db)
    assert result.success is True
    assert result.alert_triggered is True
    assert result.details["priority"] == "Critical"
    assert any(d["driver"] == "critical_tickets" for d in result.top_causal_drivers)


def test_ingest_contract_event_acv_update(memory_db):
    payload = {
        "customer_id": "CUS-020",
        "annual_contract_value": 125000.0,
        "contract_status": "Active",
        "renewal_date": "2026-11-30",
        "auto_renew": True,
    }
    result = ingest_contract_event(payload, database_path=memory_db)
    assert result.success is True
    assert result.details["annual_contract_value"] == 125000.0
    assert result.details["auto_renew"] == 1


# -----------------------------------------------------------------------------
# Dispatch Unit Tests
# -----------------------------------------------------------------------------


def test_dispatch_slack_simulation(memory_db):
    rec = dispatch_action(
        customer_id="CUS-020",
        channel="slack",
        action_text="Assign Senior Architect for onboarding stabilization",
        simulate=True,
        database_path=memory_db,
    )
    assert rec.status == "SIMULATED"
    assert rec.response_code == 200
    assert rec.channel == "slack"
    assert "blocks" in rec.payload
    assert rec.payload["blocks"][0]["type"] == "header"


def test_dispatch_crm_task_creation(memory_db):
    rec = dispatch_action(
        customer_id="CUS-020",
        channel="crm_task",
        action_text="Deliver custom executive business review",
        simulate=True,
        database_path=memory_db,
    )
    assert rec.status == "SIMULATED"
    assert rec.channel == "crm_task"
    assert rec.payload["task_type"] == "churn_prevention_intervention"
    assert "due_date" in rec.payload


def test_dispatch_webhook_payload_format(memory_db):
    rec = dispatch_action(
        customer_id="CUS-020",
        channel="webhook",
        destination="https://example.com/api/webhooks/renewal",
        action_text="Offer 10% multi-year renewal discount",
        simulate=True,
        custom_data={"campaign_id": "RENEWAL_2026_Q4"},
        database_path=memory_db,
    )
    assert rec.status == "SIMULATED"
    assert rec.destination == "https://example.com/api/webhooks/renewal"
    assert rec.payload["event_type"] == "decision_intelligence.action_dispatched"
    assert rec.payload["custom_data"]["campaign_id"] == "RENEWAL_2026_Q4"


def test_dispatch_history_retrieval(memory_db):
    dispatch_action(
        customer_id="CUS-020",
        channel="slack",
        action_text="Intervention 1",
        simulate=True,
        database_path=memory_db,
    )
    dispatch_action(
        customer_id="CUS-020",
        channel="webhook",
        action_text="Intervention 2",
        simulate=True,
        database_path=memory_db,
    )
    history = list_dispatch_history("CUS-020", database_path=memory_db)
    assert len(history) == 2
    assert history[0]["channel"] in ("slack", "webhook")


# -----------------------------------------------------------------------------
# REST API Endpoint Tests
# -----------------------------------------------------------------------------


def test_api_events_ingest_usage():
    body = {
        "event_type": "usage",
        "payload": {
            "customer_id": "CUS-020",
            "event_date": "2026-09-02",
            "active_users": 38,
            "seats_purchased": 50,
            "sessions": 300,
            "feature_adoption_pct": 75.0,
        },
    }
    status, res = execute_api_call("POST", "/api/events/ingest", body)
    assert status == 200
    assert res["success"] is True
    assert res["event_type"] == "usage_telemetry"
    assert "new_risk_score" in res


def test_api_events_ingest_support_ticket():
    body = {
        "event_type": "ticket",
        "payload": {
            "customer_id": "CUS-020",
            "priority": "Critical",
            "ticket_status": "Open",
            "ticket_category": "API",
            "ticket_summary": "Rate limiting causing failures",
        },
    }
    status, res = execute_api_call("POST", "/api/events/ingest", body)
    assert status == 200
    assert res["success"] is True
    assert res["alert_triggered"] is True


def test_api_dispatch_action_endpoint():
    body = {
        "customer_id": "CUS-020",
        "channel": "slack",
        "action_text": "Schedule executive sponsor alignment call",
        "simulate": True,
    }
    status, res = execute_api_call("POST", "/api/dispatch/action", body)
    assert status == 200
    assert res["status"] == "SIMULATED"
    assert res["channel"] == "slack"
    assert "dispatch_id" in res


def test_api_dispatch_history_endpoint():
    status, res = execute_api_call("GET", "/api/dispatch/history?customer_id=CUS-020")
    assert status == 200
    assert "dispatches" in res
    assert isinstance(res["dispatches"], list)


def test_api_dispatch_channels_endpoint():
    status, res = execute_api_call("GET", "/api/dispatch/channels")
    assert status == 200
    assert "supported_channels" in res
    channel_names = [c["channel"] for c in res["supported_channels"]]
    assert "webhook" in channel_names
    assert "slack" in channel_names
    assert "crm_task" in channel_names
