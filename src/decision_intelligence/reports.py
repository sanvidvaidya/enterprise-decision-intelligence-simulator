"""Portable executive exports built from the governed decision context."""

from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path

import pandas as pd

from decision_intelligence.database import DEFAULT_DATABASE_PATH
from decision_intelligence.onboarding import active_business_dataset
from decision_intelligence.policy import get_active_policy, list_policy_versions
from decision_intelligence.risk_engine import assess_all_customers


def portfolio_dataframe(
    as_of: date | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> pd.DataFrame:
    """Flatten explainable assessments into an executive-ready table."""

    as_of = as_of or date.today()
    active_policy_id, _ = get_active_policy(database_path)
    version = next(
        (item for item in list_policy_versions(database_path) if item["policy_version_id"] == active_policy_id),
        None,
    )
    policy_label = f"v{version['version_number']} · {version['policy_name']}" if version else "Default baseline"
    rows = []
    for assessment in assess_all_customers(as_of, database_path):
        customer = assessment["customer"]
        contract = assessment["contract"] or {}
        renewal = contract.get("renewal_date")
        rows.append(
            {
                "customer_id": customer["customer_id"],
                "customer_name": customer["customer_name"],
                "segment": customer["segment"],
                "region": customer["region"],
                "account_manager": customer["account_manager_name"],
                "risk_level": assessment["risk_level"],
                "risk_score": assessment["risk_score"],
                "annual_contract_value": contract.get("annual_contract_value", 0),
                "renewal_date": renewal,
                "days_to_renewal": (date.fromisoformat(renewal) - as_of).days if renewal else None,
                "risk_factors": "; ".join(factor["name"] for factor in assessment["factors"]) or "None",
                "next_action": assessment["recommended_actions"][0] if assessment["recommended_actions"] else "Monitor normally.",
                "policy_version": policy_label,
            }
        )
    return pd.DataFrame(rows)


def portfolio_csv(
    as_of: date | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> bytes:
    return portfolio_dataframe(as_of, database_path).to_csv(index=False).encode("utf-8")


def executive_html(
    as_of: date | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> str:
    """Create a self-contained, print-friendly HTML portfolio brief."""

    as_of = as_of or date.today()
    portfolio = portfolio_dataframe(as_of, database_path)
    business_profile = active_business_dataset(database_path)
    policy_label = portfolio["policy_version"].iloc[0] if not portfolio.empty else "No active policy"
    high_risk = portfolio[portfolio["risk_level"] == "High"]
    acv_at_risk = high_risk["annual_contract_value"].sum()
    body_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.customer_name))}</td>"
        f"<td><span class='pill {escape(str(row.risk_level).lower())}'>{escape(str(row.risk_level))}</span></td>"
        f"<td>{int(row.risk_score)}</td>"
        f"<td>${float(row.annual_contract_value):,.0f}</td>"
        f"<td>{escape(str(row.renewal_date))}</td>"
        f"<td>{escape(str(row.risk_factors))}</td>"
        f"<td>{escape(str(row.next_action))}</td>"
        "</tr>"
        for row in portfolio.itertuples(index=False)
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Renewal Intelligence Brief</title>
<style>
body{{font-family:Arial,sans-serif;color:#172033;max-width:1200px;margin:40px auto;padding:0 24px}}
h1{{margin-bottom:4px}} .muted{{color:#667085}} .kpis{{display:flex;gap:18px;margin:28px 0}}
.kpi{{border:1px solid #d7dce5;border-radius:10px;padding:16px;min-width:180px}}
.value{{font-size:26px;font-weight:700}} table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{border-bottom:1px solid #e4e7ec;padding:10px;text-align:left;vertical-align:top}}
th{{background:#f7f8fa}} .pill{{padding:3px 8px;border-radius:12px;font-weight:700}}
.high{{background:#fee4e2;color:#b42318}} .medium{{background:#fef0c7;color:#b54708}}
.low{{background:#dcfae6;color:#067647}} footer{{margin-top:28px;font-size:12px;color:#667085}}
</style></head><body>
<h1>Enterprise Renewal Intelligence Brief</h1>
<div class="muted">Deterministic portfolio assessment as of {as_of.isoformat()} · Policy {escape(str(policy_label))}</div>
<div class="kpis"><div class="kpi"><div class="muted">Customers</div><div class="value">{len(portfolio)}</div></div>
<div class="kpi"><div class="muted">High risk</div><div class="value">{len(high_risk)}</div></div>
<div class="kpi"><div class="muted">High-risk ACV</div><div class="value">${acv_at_risk:,.0f}</div></div></div>
<table><thead><tr><th>Customer</th><th>Risk</th><th>Score</th><th>ACV</th><th>Renewal</th><th>Evidence-based factors</th><th>Next action</th></tr></thead>
<tbody>{body_rows}</tbody></table>
<footer>{escape(str(business_profile['organization_name']))} · {escape(str(business_profile['data_classification']))} · Rules-based decision support, not a prediction or automated decision.</footer>
</body></html>"""
