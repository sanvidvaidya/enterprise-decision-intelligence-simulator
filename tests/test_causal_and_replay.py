"""Verification for Causal DAG, Structural Causal Model, and Time-Travel Replay."""

from datetime import date
from pathlib import Path
import io
import json
import sys
from uuid import uuid4

import pandas as pd
import pytest

from decision_intelligence.database import SCHEMA_PATH, connect
from decision_intelligence.generate_data import build_extracts
from decision_intelligence.ingestion import LOAD_ORDER, _upsert_extract
from decision_intelligence.causal import (
    CausalDAG,
    StructuralCausalModel,
    analyze_customer_causality,
    extract_customer_causal_state,
)
from decision_intelligence.replay import (
    PointInTimeCheckpoint,
    StreamEvent,
    TimeTravelReplayEngine,
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
    uri = f"file:test-causal-{uuid4()}?mode=memory&cache=shared"
    anchor = connect(uri)
    anchor.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    extracts = {name: pd.DataFrame(rows) for name, rows in build_extracts().items()}
    for filename in LOAD_ORDER:
        _upsert_extract(anchor, filename, extracts[filename])
    anchor.commit()
    yield uri
    anchor.close()


def test_causal_dag_structure_and_acyclicity():
    dag = CausalDAG()
    assert len(dag.nodes) == 9
    assert len(dag.edges) == 12

    topo = dag.topological_order()
    assert len(topo) == 9
    assert topo[-1] == "renewal_risk_score"

    parents = dag.get_parents("renewal_risk_score")
    parent_ids = {e.source for e in parents}
    assert "critical_tickets" in parent_ids
    assert "active_user_decline" in parent_ids
    assert "seat_utilization" in parent_ids
    assert "days_to_renewal" in parent_ids
    assert "contract_acv" in parent_ids


def test_causal_dag_paths_and_mediators():
    dag = CausalDAG()
    paths = dag.find_paths("critical_tickets", "renewal_risk_score")
    assert len(paths) >= 2

    # Direct edge path
    assert ["critical_tickets", "renewal_risk_score"] in paths

    # Mediated paths
    mediated_lengths = [len(p) for p in paths if len(p) > 2]
    assert len(mediated_lengths) >= 1


def test_scm_do_operator_edge_cutting():
    scm = StructuralCausalModel()

    # When critical_tickets = 2, default csat drops
    base_state = {"critical_tickets": 2.0}
    eval_csat = scm.evaluate_node("csat_score", base_state)
    assert eval_csat < 4.0

    # With do(csat_score = 4.9), csat is forced regardless of critical tickets
    simulated = scm.simulate(
        base_state={"critical_tickets": 2.0},
        interventions={"csat_score": 4.9},
    )
    assert simulated["critical_tickets"] == 2.0
    assert simulated["csat_score"] == 4.9


def test_scm_mediation_decomposition():
    scm = StructuralCausalModel()
    observed = {
        "critical_tickets": 1.0,
        "csat_score": 3.0,
        "feature_adoption": 60.0,
        "seat_utilization": 0.45,
        "active_user_decline": 0.35,
        "days_to_renewal": 30.0,
        "contract_acv": 60000.0,
        "executive_sponsor_engaged": 0.5,
    }
    observed["renewal_risk_score"] = scm.evaluate_node("renewal_risk_score", observed)

    decomp = scm.decompose_effects(
        observed,
        intervention_node="critical_tickets",
        intervention_val=0.0,
    )
    assert decomp.intervention_node == "critical_tickets"
    assert decomp.target_node == "renewal_risk_score"
    # Total Effect must equal Direct Effect + Indirect Effect (within floating tolerance)
    assert abs(decomp.total_effect - (decomp.direct_effect + decomp.indirect_effect)) < 1e-6
    assert decomp.direct_effect < 0.0  # reducing critical tickets reduces score directly


def test_scm_abduction_and_counterfactual():
    scm = StructuralCausalModel()
    observed = {
        "critical_tickets": 2.0,
        "csat_score": 2.8,
        "feature_adoption": 55.0,
        "seat_utilization": 0.35,
        "active_user_decline": 0.40,
        "days_to_renewal": 40.0,
        "contract_acv": 80000.0,
        "executive_sponsor_engaged": 0.4,
    }
    observed["renewal_risk_score"] = scm.evaluate_node("renewal_risk_score", observed)

    cf = scm.counterfactual_query(observed, {"critical_tickets": 0.0})
    assert cf["score_reduction"] > 0
    assert cf["counterfactual"]["critical_tickets"] == 0.0
    assert cf["counterfactual"]["renewal_risk_score"] < observed["renewal_risk_score"]


def test_root_cause_attribution():
    scm = StructuralCausalModel()
    observed = {
        "critical_tickets": 1.0,
        "csat_score": 2.5,
        "feature_adoption": 45.0,
        "seat_utilization": 0.30,
        "active_user_decline": 0.45,
        "days_to_renewal": 25.0,
        "contract_acv": 90000.0,
        "executive_sponsor_engaged": 0.3,
    }
    observed["renewal_risk_score"] = scm.evaluate_node("renewal_risk_score", observed)

    attributions = scm.attribute_root_causes(observed)
    assert len(attributions) >= 4
    total_pct = sum(r.percentage_of_risk for r in attributions)
    assert 99.0 <= total_pct <= 101.0
    # Top driver should have substantial points
    assert attributions[0].causal_points > 0.0


def test_time_travel_point_in_time_reconstruction_no_leakage(memory_db):
    engine = TimeTravelReplayEngine(database_path=memory_db)

    # Reconstruct state at 2026-03-01
    early_date = date(2026, 3, 1)
    cp_early = engine.reconstruct_checkpoint("CUS-020", early_date)
    assert cp_early.checkpoint_date == "2026-03-01"
    assert cp_early.critical_tickets_count == 0  # tickets were opened later in the year
    assert cp_early.risk_score == 0

    # Reconstruct state at 2026-08-01
    later_date = date(2026, 8, 1)
    cp_later = engine.reconstruct_checkpoint("CUS-020", later_date)
    assert cp_later.checkpoint_date == "2026-08-01"
    assert cp_later.risk_score > cp_early.risk_score


def test_time_travel_factual_trajectory(memory_db):
    engine = TimeTravelReplayEngine(database_path=memory_db)

    trajectory = engine.replay_factual_trajectory("CUS-020")
    assert len(trajectory) >= 3
    # Checkpoints must be ordered chronologically
    dates = [cp.checkpoint_date for cp in trajectory]
    assert dates == sorted(dates)


def test_time_travel_counterfactual_branch_divergence(memory_db):
    engine = TimeTravelReplayEngine(database_path=memory_db)

    branch_res = engine.branch_counterfactual_trajectory(
        customer_id="CUS-020",
        branch_date="2026-06-01",
        intervention_type="comprehensive_playbook",
        intervention_params={"lift_pct": 35.0, "extension_days": 60},
    )

    trajectory = branch_res["trajectory_comparison"]
    assert len(trajectory) >= 3

    # Check that before 2026-06-01, factual and counterfactual scores are identical
    for t in trajectory:
        if t["checkpoint_date"] < "2026-06-01":
            assert t["factual_score"] == t["counterfactual_score"]
            assert t["score_delta"] == 0
        elif t["checkpoint_date"] >= "2026-08-01":
            # After branch date and propagation, counterfactual score must be lower
            assert t["counterfactual_score"] < t["factual_score"]
            assert t["score_delta"] < 0

    assert branch_res["impact_summary"]["score_reduction"] > 0


def test_customer_causal_analysis_integration(memory_db):
    analysis = analyze_customer_causality("CUS-020", database_path=memory_db)
    assert analysis["customer_id"] == "CUS-020"
    assert "baseline_state" in analysis
    assert "root_cause_attributions" in analysis
    assert len(analysis["intervention_evaluations"]) == 4

    # Critical escalation should reduce score
    esc = next(it for it in analysis["intervention_evaluations"] if it["action"] == "resolve_critical_tickets")
    assert esc["score_reduction"] > 0


def test_api_causal_graph_endpoint():
    status, payload = execute_api_call("GET", "/api/causal/graph")
    assert status == 200
    assert "nodes" in payload
    assert "edges" in payload
    assert len(payload["nodes"]) == 9


def test_api_causal_customer_endpoint():
    status, payload = execute_api_call("GET", "/api/causal/customer?id=CUS-020")
    assert status == 200
    assert payload["customer_id"] == "CUS-020"
    assert "root_cause_attributions" in payload
    assert "intervention_evaluations" in payload


def test_api_replay_customer_endpoint():
    status, payload = execute_api_call("GET", "/api/replay/customer?id=CUS-020")
    assert status == 200
    assert payload["customer_id"] == "CUS-020"
    assert "checkpoints" in payload
    assert len(payload["checkpoints"]) >= 3


def test_api_causal_counterfactual_post():
    body = {
        "customer_id": "CUS-020",
        "interventions": {"critical_tickets": 0.0, "seat_utilization": 0.85},
    }
    status, payload = execute_api_call("POST", "/api/causal/counterfactual", body)
    assert status == 200
    assert "counterfactual" in payload
    assert payload["score_reduction"] > 0


def test_api_replay_branch_post():
    body = {
        "customer_id": "CUS-020",
        "branch_date": "2026-06-01",
        "intervention_type": "resolve_critical_tickets",
        "intervention_params": {},
    }
    status, payload = execute_api_call("POST", "/api/replay/branch", body)
    assert status == 200
    assert "trajectory_comparison" in payload
    assert "impact_summary" in payload
    assert payload["impact_summary"]["score_reduction"] > 0
