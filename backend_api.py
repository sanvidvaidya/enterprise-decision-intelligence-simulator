"""Enterprise Decision Simulator — REST API Bridge
Exposes the deterministic SQLite risk engine and capacity planner to the React frontend.
Run with: python backend_api.py --port 8002
"""

from __future__ import annotations

import argparse
from datetime import date
import json
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


class DecisionSimulatorAPIHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
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

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        try:
            if path in ("/api/health", "/api/status"):
                with connect() as conn:
                    cust_count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
                    contract_count = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
                self._send_json({
                    "status": "ok",
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

            else:
                self._send_json({"error": f"Endpoint not found: {path}"}, 404)

        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            payload = self._read_json_body()

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

            elif path == "/api/upload":
                accounts = payload.get("accounts", [])
                if not accounts:
                    self._send_json({"error": "No accounts provided in payload"}, 400)
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

            else:
                self._send_json({"error": f"Endpoint not found: {path}"}, 404)

        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def log_message(self, format, *args):
        pass


def run_server(port: int = 8002):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, DecisionSimulatorAPIHandler)
    print(f"[Simulator API] Running on http://127.0.0.1:{port} (SQLite: {DEFAULT_DATABASE_PATH})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Simulator API] Shutting down.")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8002, help="Port to listen on")
    args = parser.parse_args()
    run_server(args.port)
