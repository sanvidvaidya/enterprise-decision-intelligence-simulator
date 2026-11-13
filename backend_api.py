"""Enterprise Decision Simulator - REST API Bridge
Exposes the deterministic SQLite risk engine, causal DAG, and replay engine to frontends.
Run with: python backend_api.py --port 8002
"""

from __future__ import annotations

from decision_intelligence.gametheory import (
    GameTheoreticSimulator,
    DEFAULT_COMPETITORS,
    VendorStrategy,
    CompetitorCounterMove,
)

import argparse
from dataclasses import asdict
from datetime import date
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys
from urllib.parse import urlparse, parse_qs

# Ensure 'src' is in sys.path to import decision_intelligence
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from decision_intelligence.database import DEFAULT_DATABASE_PATH, connect
from decision_intelligence.policy import get_active_policy, DEFAULT_POLICY
from decision_intelligence.risk_engine import (
    assess_all_customers,
    assess_customer,
    simulate_customer,
)
from decision_intelligence.planner import plan_interventions
from decision_intelligence.causal import (
    CausalDAG,
    StructuralCausalModel,
    analyze_customer_causality,
    extract_customer_causal_state,
)
from decision_intelligence.replay import TimeTravelReplayEngine
from decision_intelligence.ingest_stream import (
    ingest_usage_event,
    ingest_support_ticket,
    ingest_contract_event,
)
from decision_intelligence.dispatch import (
    dispatch_action,
    list_dispatch_history,
)

MAX_BODY_SIZE = 5 * 1024 * 1024  # 5 MB ceiling
ALLOWED_ORIGIN = os.environ.get("SIMULATOR_ALLOWED_ORIGIN", "http://localhost:5173")


class DecisionSimulatorAPIHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, data: any, status_code: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> tuple[dict | None, tuple[str, int] | None]:
        content_length_header = self.headers.get("Content-Length")
        if not content_length_header:
            return {}, None
        try:
            content_length = int(content_length_header)
        except ValueError:
            return None, ("Invalid Content-Length header", 400)

        if content_length > MAX_BODY_SIZE:
            return None, (f"Request body exceeds {MAX_BODY_SIZE // (1024*1024)}MB limit", 413)

        try:
            raw_body = self.rfile.read(content_length)
            return json.loads(raw_body.decode("utf-8")), None
        except Exception:
            return None, ("Malformed JSON body", 400)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        try:
            if path == "/api/health":
                with connect() as conn:
                    cust_count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
                    contract_count = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
                self._send_json({
                    "status": "healthy",
                    "system": "Enterprise Decision Simulator",
                    "database": "SQLite connected",
                    "active_database_path": str(DEFAULT_DATABASE_PATH),
                    "customers_count": cust_count,
                    "contracts_count": contract_count,
                    "engine": "Deterministic Evidence Risk Engine v0.3.0",
                })

            elif path == "/api/customers":
                # Assess all customers directly from the SQLite store
                results = assess_all_customers()
                self._send_json({
                    "as_of": date.today().isoformat(),
                    "total": len(results),
                    "customers": results,
                })

            elif path == "/api/customer":
                cust_id = params.get("id", [None])[0]
                if not cust_id:
                    self._send_json({"error": "Missing 'id' parameter"}, 400)
                    return
                assessment = assess_customer(cust_id)
                self._send_json(assessment)

            elif path == "/api/planner":
                # Return capacity allocation plan from planner.py
                plan = plan_interventions(
                    available_hours=120.0,
                    available_budget=50000.0,
                    support_slots=10,
                    enablement_slots=10,
                )
                self._send_json(plan)

            elif path == "/api/policy":
                version, policy = get_active_policy()
                self._send_json({
                    "version": version,
                    "policy": policy,
                })

            elif path == "/api/causal/graph":
                dag = CausalDAG()
                self._send_json(dag.to_dict())

            elif path == "/api/causal/customer":
                cust_id = params.get("id", [None])[0]
                if not cust_id:
                    self._send_json({"error": "Missing 'id' parameter"}, 400)
                    return
                causal_res = analyze_customer_causality(cust_id)
                self._send_json(causal_res)

            elif path == "/api/dispatch/history":
                cust_id = params.get("customer_id", params.get("id", [None]))[0]
                limit_str = params.get("limit", ["50"])[0]
                try:
                    limit = min(500, max(1, int(limit_str)))
                except ValueError:
                    limit = 50
                history = list_dispatch_history(customer_id=cust_id, limit=limit)
                self._send_json({
                    "total": len(history),
                    "customer_id": cust_id,
                    "dispatches": history,
                })

            elif path == "/api/dispatch/channels":
                self._send_json({
                    "supported_channels": [
                        {
                            "channel": "webhook",
                            "description": "HTTP POST webhook event to external endpoint (Zapier, n8n, Make, custom gateway)",
                            "required_fields": ["customer_id"],
                            "optional_fields": ["destination", "action_id", "action_text", "simulate", "custom_data"],
                        },
                        {
                            "channel": "slack",
                            "description": "Slack Block Kit formatted alert to CS/Renewal team channel",
                            "required_fields": ["customer_id"],
                            "optional_fields": ["destination", "action_id", "action_text", "simulate"],
                        },
                        {
                            "channel": "crm_task",
                            "description": "Structured renewal task creation for CRM / Linear / Jira",
                            "required_fields": ["customer_id"],
                            "optional_fields": ["destination", "action_id", "action_text", "owner", "simulate"],
                        },
                        {
                            "channel": "email",
                            "description": "Executive risk alert email notification to account team",
                            "required_fields": ["customer_id"],
                            "optional_fields": ["destination", "action_text", "simulate"],
                        },
                    ]
                })

            elif path == "/api/replay/customer":
                cust_id = params.get("id", [None])[0]
                if not cust_id:
                    self._send_json({"error": "Missing 'id' parameter"}, 400)
                    return
                engine = TimeTravelReplayEngine()
                self._send_json({
                    "customer_id": cust_id,
                    "checkpoints": [asdict(cp) for cp in engine.replay_factual_trajectory(cust_id)],
                    "events": [asdict(e) for e in engine.get_customer_event_stream(cust_id)],
                })

            elif path == "/api/gametheory/competitors":
                self._send_json({
                    "competitors_count": len(DEFAULT_COMPETITORS),
                    "competitors": [asdict(c) for c in DEFAULT_COMPETITORS]
                })

            elif path == "/api/gametheory/vulnerability":
                cust_id = params.get("id", [None])[0]
                if not cust_id:
                    self._send_json({"error": "Missing 'id' parameter"}, 400)
                    return
                simulator = GameTheoreticSimulator()
                vuln = simulator.assess_customer_vulnerability(cust_id)
                if not vuln:
                    self._send_json({"error": f"Customer '{cust_id}' not found"}, 404)
                    return
                self._send_json(asdict(vuln))

            elif path == "/api/gametheory/equilibrium":
                simulator = GameTheoreticSimulator()
                eq_res = simulator.run_portfolio_simulation()
                self._send_json(asdict(eq_res))

            else:
                self._send_json({"error": f"Endpoint not found: {path}"}, 404)

        except Exception as e:
            self._send_json({"error": f"Internal server error: {e}"}, 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            payload, err = self._read_json_body()
            if err:
                self._send_json({"error": err[0]}, err[1])
                return

            if path == "/api/simulate":
                cust_id = payload.get("customer_id")
                recovery = float(payload.get("usage_recovery_pct", 50))
                resolve_critical = bool(payload.get("resolve_critical", False))
                extension_days = int(payload.get("renewal_extension_days", 0))

                if cust_id:
                    res = simulate_customer(
                        cust_id,
                        usage_recovery_pct=recovery,
                        resolve_critical=resolve_critical,
                        renewal_extension_days=extension_days,
                    )
                    self._send_json(res)
                else:
                    with connect() as conn:
                        all_ids = [r[0] for r in conn.execute("SELECT customer_id FROM customers").fetchall()]
                    sim_results = []
                    for cid in all_ids:
                        sim_results.append(simulate_customer(
                            cid,
                            usage_recovery_pct=recovery,
                            resolve_critical=resolve_critical,
                            renewal_extension_days=extension_days,
                        ))
                    self._send_json({
                        "total": len(sim_results),
                        "simulations": sim_results,
                    })

            elif path == "/api/causal/counterfactual":
                cust_id = payload.get("customer_id")
                interventions = payload.get("interventions", {})
                if not cust_id:
                    self._send_json({"error": "Missing 'customer_id' parameter"}, 400)
                    return
                state = extract_customer_causal_state(cust_id)
                scm = StructuralCausalModel()
                cf_res = scm.counterfactual_query(state, interventions)
                self._send_json(cf_res)

            elif path == "/api/replay/branch":
                cust_id = payload.get("customer_id")
                branch_date = payload.get("branch_date")
                intervention_type = payload.get("intervention_type", "resolve_critical_tickets")
                intervention_params = payload.get("intervention_params", {})
                if not cust_id or not branch_date:
                    self._send_json({"error": "Missing 'customer_id' or 'branch_date' parameter"}, 400)
                    return
                engine = TimeTravelReplayEngine()
                branch_res = engine.branch_counterfactual_trajectory(
                    cust_id, branch_date, intervention_type, intervention_params
                )
                self._send_json(branch_res)

            elif path == "/api/events/ingest":
                event_type = payload.get("event_type", "").lower()
                event_data = payload.get("payload", payload)
                if not event_type:
                    # Infer event type from keys
                    if "active_users" in event_data or "sessions" in event_data:
                        event_type = "usage"
                    elif "priority" in event_data or "ticket_summary" in event_data or "ticket_status" in event_data:
                        event_type = "ticket"
                    elif "annual_contract_value" in event_data or "contract_status" in event_data:
                        event_type = "contract"
                    else:
                        self._send_json({"error": "Could not infer event_type; specify 'event_type': 'usage' | 'ticket' | 'contract'"}, 400)
                        return

                try:
                    if event_type in ("usage", "telemetry"):
                        res = ingest_usage_event(event_data)
                    elif event_type in ("ticket", "support"):
                        res = ingest_support_ticket(event_data)
                    elif event_type in ("contract", "renewal"):
                        res = ingest_contract_event(event_data)
                    else:
                        self._send_json({"error": f"Unsupported event_type '{event_type}'"}, 400)
                        return
                    self._send_json(asdict(res))
                except ValueError as e:
                    self._send_json({"error": str(e)}, 400)
                except Exception as e:
                    self._send_json({"error": f"Ingestion failure: {str(e)}"}, 500)

            elif path == "/api/dispatch/action":
                cust_id = payload.get("customer_id")
                channel = payload.get("channel", "slack")
                if not cust_id:
                    self._send_json({"error": "Missing required 'customer_id' parameter"}, 400)
                    return
                try:
                    disp = dispatch_action(
                        customer_id=cust_id,
                        channel=channel,
                        destination=payload.get("destination"),
                        action_id=payload.get("action_id"),
                        action_text=payload.get("action_text"),
                        owner=payload.get("owner"),
                        simulate=payload.get("simulate", True),
                        custom_data=payload.get("custom_data"),
                    )
                    self._send_json(asdict(disp))
                except ValueError as e:
                    self._send_json({"error": str(e)}, 400)
                except Exception as e:
                    self._send_json({"error": f"Dispatch failure: {str(e)}"}, 500)

            elif path == "/api/upload":
                accounts = payload.get("accounts", [])
                if not accounts:
                    self._send_json({"error": "No accounts provided in payload"}, 400)
                    return
                if not isinstance(accounts, list) or len(accounts) > 5000:
                    self._send_json({"error": "Accounts payload must be a list of up to 5,000 items"}, 400)
                    return

                assessed_accounts = []
                for acc in accounts:
                    acv = float(acc.get("annual_contract_value", acc.get("arr", 50000)))
                    critical_tickets = int(acc.get("critical_tickets", 0))
                    seats = max(1, int(acc.get("seats_purchased", 100)))
                    active_users = int(acc.get("active_users", seats))
                    penetration = active_users / seats
                    
                    points = 0
                    factors = []
                    if penetration < 0.50:
                        pts = 35
                        points += pts
                        factors.append({
                            "name": "Low seat engagement",
                            "points": pts,
                            "explanation": f"Only {penetration:.0%} of purchased seats active.",
                            "evidence_record_ids": ["EVID-UP-01"],
                            "recommended_action": "Run targeted adoption enablement.",
                        })
                    if critical_tickets > 0:
                        pts = 25
                        points += pts
                        factors.append({
                            "name": "Unresolved critical support",
                            "points": pts,
                            "explanation": f"{critical_tickets} critical ticket(s) open.",
                            "evidence_record_ids": ["EVID-UP-02"],
                            "recommended_action": "Escalate to executive support lead.",
                        })
                    if acv >= 100000:
                        pts = 15
                        points += pts
                        factors.append({
                            "name": "High contract value",
                            "points": pts,
                            "explanation": f"Annual contract value is ${acv:,.0f}.",
                            "evidence_record_ids": ["EVID-UP-03"],
                            "recommended_action": "Involve VP and renewal sponsor.",
                        })
                    
                    score = min(100, points + 10)
                    level = "High" if score >= 60 else "Medium" if score >= 30 else "Low"
                    
                    assessed_accounts.append({
                        "customer": {
                            "customer_id": acc.get("customer_id", f"CUST-UP-{len(assessed_accounts)+1:03d}"),
                            "customer_name": acc.get("customer_name", "Custom Corp"),
                            "industry": acc.get("industry", "Technology"),
                            "segment": acc.get("segment", "Enterprise"),
                            "account_manager_name": acc.get("account_manager", "Assigned Specialist"),
                        },
                        "contract": {
                            "contract_id": f"CTR-UP-{len(assessed_accounts)+1:03d}",
                            "annual_contract_value": acv,
                            "renewal_date": acc.get("renewal_date", "2026-12-31"),
                        },
                        "risk_score": score,
                        "risk_level": level,
                        "factors": factors,
                        "recommended_actions": [f["recommended_action"] for f in factors],
                    })

                self._send_json({
                    "status": "success",
                    "imported_count": len(assessed_accounts),
                    "customers": assessed_accounts,
                })

            elif path == "/api/gametheory/simulate":
                simulator = GameTheoreticSimulator()
                eq_res = simulator.run_portfolio_simulation()
                self._send_json(asdict(eq_res))

            else:
                self._send_json({"error": f"Endpoint not found: {path}"}, 404)

        except Exception as e:
            self._send_json({"error": f"Internal server error: {e}"}, 500)

    def log_message(self, format, *args):
        pass


def run_server(host: str = "127.0.0.1", port: int = 8002):
    server_address = (host, port)
    httpd = HTTPServer(server_address, DecisionSimulatorAPIHandler)
    print(f"[Simulator API] Running on http://{host}:{port} (SQLite: {DEFAULT_DATABASE_PATH})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Simulator API] Shutting down.")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8002, help="Port to listen on")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
