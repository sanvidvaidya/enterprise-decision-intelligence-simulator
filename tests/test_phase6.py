from datetime import date
from pathlib import Path
import pandas as pd
from decision_intelligence.database import create_database, connect
from decision_intelligence.generate_data import build_extracts
from decision_intelligence.validation import validate_extracts

def frames(): return {name: pd.DataFrame(rows) for name,rows in build_extracts().items()}
def test_synthetic_extracts_are_valid(): assert validate_extracts(frames()) == []
def test_invalid_foreign_key_is_reported():
    data=frames(); data["customers.csv"].loc[0,"account_manager_id"]="AM-999"
    assert any(issue.rule_name=="foreign_key" for issue in validate_extracts(data))
def test_warning_is_distinct_from_error():
    data=frames(); data["product_usage_events.csv"].loc[0,"active_users"] = 999999
    issues=validate_extracts(data); assert any(issue.severity=="WARNING" for issue in issues)
def test_schema_enforces_foreign_keys():
    import sqlite3
    schema = Path("data/schema.sql").read_text(encoding="utf-8")
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(schema)
    try:
        con.execute("INSERT INTO customers VALUES ('C','Name','Tech','SMB',1,'NA','missing','Active','2026-01-01')")
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("foreign key should reject missing manager")
def test_generated_usage_volume(): assert len(build_extracts()["product_usage_events.csv"]) == 180
def test_risk_score_has_evidence_for_high_risk_customer():
    from decision_intelligence.risk_engine import assess_all_customers
    results = assess_all_customers(date(2026, 8, 28))
    assert results[0]["risk_level"] == "High"
    assert results[0]["risk_score"] >= 55
    assert all(factor["evidence_record_ids"] for factor in results[0]["factors"])