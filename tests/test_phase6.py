"""Cross-phase verification for data, rules, persistence, and exports."""

from datetime import date
import io
from pathlib import Path
from uuid import uuid4
import zipfile

import pandas as pd
import pytest

from decision_intelligence.database import SCHEMA_PATH, connect
from decision_intelligence.deployment import (
    PRIVATE_BUSINESS,
    PUBLIC_DEMO,
    deployment_mode,
    require_private_mode,
)
from decision_intelligence.generate_data import REFERENCE_DATE, build_extracts
import decision_intelligence.ingestion as ingestion_module
from decision_intelligence.ingestion import LOAD_ORDER, _upsert_extract, ingest
from decision_intelligence.onboarding import (
    active_business_dataset,
    data_dictionary,
    register_business_dataset,
    template_bundle,
)
from decision_intelligence.planner import plan_interventions, save_capacity_plan
from decision_intelligence.policy import (
    DEFAULT_POLICY,
    create_policy_draft,
    decide_policy,
    ensure_default_policy,
    get_active_policy,
    preview_policy_impact,
    validate_policy,
)
from decision_intelligence.reports import executive_html, portfolio_dataframe
from decision_intelligence.risk_engine import assess_all_customers, risk_level, simulate_customer
from decision_intelligence.timeline import customer_event_timeline, risk_change_history
from decision_intelligence.validation import SOURCE_SPECS, validate_extracts
from decision_intelligence.workflow import (
    create_action,
    list_actions,
    list_decisions,
    log_decision,
    save_scenario,
    snapshot_portfolio,
    update_action_status,
)


def frames() -> dict[str, pd.DataFrame]:
    return {name: pd.DataFrame(rows) for name, rows in build_extracts().items()}


@pytest.fixture
def memory_database():
    """Use a shared in-memory URI, with no OS temp directory permissions required."""

    uri = f"file:test-{uuid4()}?mode=memory&cache=shared"
    anchor = connect(uri)
    anchor.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    extracts = frames()
    for filename in LOAD_ORDER:
        _upsert_extract(anchor, filename, extracts[filename])
    anchor.commit()
    yield uri, anchor
    anchor.close()


def test_synthetic_extracts_are_valid():
    assert validate_extracts(frames()) == []


def test_deployment_mode_defaults_to_safe_public_demo(monkeypatch):
    monkeypatch.delenv("EDS_DEPLOYMENT_MODE", raising=False)
    mode = deployment_mode()
    assert mode.key == PUBLIC_DEMO
    assert mode.writes_enabled is False
    assert mode.data_uploads_enabled is False


def test_private_business_mode_explicitly_enables_governed_writes(monkeypatch):
    monkeypatch.setenv("EDS_DEPLOYMENT_MODE", PRIVATE_BUSINESS)
    mode = deployment_mode()
    assert mode.is_private_business
    assert mode.writes_enabled
    assert mode.data_uploads_enabled
    require_private_mode(mode, "test operation")


def test_public_demo_rejects_persistent_operations():
    with pytest.raises(PermissionError, match="disabled in Public Demo mode"):
        require_private_mode(deployment_mode(PUBLIC_DEMO), "Business data activation")


def test_unknown_deployment_mode_is_rejected():
    with pytest.raises(ValueError, match="Invalid EDS_DEPLOYMENT_MODE"):
        deployment_mode("unsafe_guess")


def test_invalid_foreign_key_is_reported():
    data = frames()
    data["customers.csv"].loc[0, "account_manager_id"] = "AM-999"
    assert any(issue.rule_name == "foreign_key" for issue in validate_extracts(data))


def test_warning_is_distinct_from_error():
    data = frames()
    data["product_usage_events.csv"].loc[0, "active_users"] = 999999
    issues = validate_extracts(data)
    assert any(issue.severity == "WARNING" for issue in issues)


def test_empty_required_source_and_bad_schema_are_reported_without_crashing():
    data = frames()
    data["customers.csv"] = pd.DataFrame(columns=["wrong_column"])
    issues = validate_extracts(data)
    assert any(
        issue.source_file == "customers.csv" and issue.rule_name == "required_column"
        for issue in issues
    )

    data = frames()
    data["contracts.csv"] = data["contracts.csv"].iloc[0:0]
    issues = validate_extracts(data)
    assert any(
        issue.source_file == "contracts.csv" and issue.rule_name == "source_rows"
        for issue in issues
    )


def test_schema_enforces_foreign_keys():
    import sqlite3

    schema = Path("data/schema.sql").read_text(encoding="utf-8")
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(schema)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO customers VALUES ('C','Name','Tech','SMB',1,'NA','missing','Active','2026-01-01')"
        )


def test_generated_usage_volume():
    assert len(build_extracts()["product_usage_events.csv"]) == 180


def test_risk_score_has_evidence_for_high_risk_customer(memory_database):
    uri, _ = memory_database
    results = assess_all_customers(REFERENCE_DATE, uri)
    assert results[0]["risk_level"] == "High"
    assert results[0]["risk_score"] >= 55
    assert all(factor["evidence_record_ids"] for factor in results[0]["factors"])


def test_risk_bands_are_documented_boundaries():
    assert risk_level(29) == "Low"
    assert risk_level(30) == "Medium"
    assert risk_level(54) == "Medium"
    assert risk_level(55) == "High"


def test_intervention_scenario_reduces_high_risk_score(memory_database):
    uri, _ = memory_database
    high_risk_customer = assess_all_customers(REFERENCE_DATE, uri)[0]["customer"]["customer_id"]
    scenario = simulate_customer(
        high_risk_customer,
        REFERENCE_DATE,
        usage_recovery_pct=100,
        resolve_critical=True,
        renewal_extension_days=120,
        database_path=uri,
    )
    assert scenario["simulated"]["risk_score"] < scenario["baseline"]["risk_score"]
    assert "Unresolved critical support" not in {
        factor["name"] for factor in scenario["simulated"]["factors"]
    }


def test_scenario_rejects_impossible_assumptions(memory_database):
    uri, _ = memory_database
    with pytest.raises(ValueError):
        simulate_customer("CUS-001", REFERENCE_DATE, usage_recovery_pct=101, database_path=uri)
    with pytest.raises(ValueError):
        simulate_customer("CUS-001", REFERENCE_DATE, renewal_extension_days=-1, database_path=uri)


def test_snapshot_persists_assessments_and_factors(memory_database):
    uri, anchor = memory_database
    result = snapshot_portfolio(REFERENCE_DATE, uri)
    assert result["customers_assessed"] == 30
    assert anchor.execute("SELECT COUNT(*) FROM risk_assessments").fetchone()[0] == 30
    assert anchor.execute("SELECT COUNT(*) FROM risk_factor_results").fetchone()[0] > 0
    assert anchor.execute("SELECT COUNT(*) FROM assessment_policy_versions").fetchone()[0] == 30


def test_action_and_decision_workflow_is_auditable(memory_database):
    uri, _ = memory_database
    action_id = create_action(
        "CUS-001",
        "Run an adoption workshop",
        "Maya Chen",
        "High",
        "2026-09-05",
        ["USE-001-06"],
        uri,
    )
    update_action_status(action_id, "Completed", uri)
    event_id = log_decision(
        "CUS-001", "Customer meeting", "Maya Chen", "Workshop approved.", action_id, uri
    )
    actions = list_actions("CUS-001", uri)
    decisions = list_decisions("CUS-001", uri)
    assert actions[0]["action_status"] == "Completed"
    assert actions[0]["completed_at"]
    assert decisions[0]["decision_event_id"] == event_id


def test_saved_scenario_keeps_assumptions(memory_database):
    uri, anchor = memory_database
    scenario = simulate_customer(
        "CUS-005", REFERENCE_DATE, resolve_critical=True, database_path=uri
    )
    scenario_id = save_scenario("CUS-005", scenario, uri)
    row = anchor.execute(
        "SELECT assumptions_json FROM scenario_runs WHERE scenario_run_id = ?", (scenario_id,)
    ).fetchone()
    assert '"resolve_critical": true' in row["assumptions_json"]


def test_executive_exports_are_complete(memory_database):
    uri, _ = memory_database
    portfolio = portfolio_dataframe(REFERENCE_DATE, uri)
    report = executive_html(REFERENCE_DATE, uri)
    assert len(portfolio) == 30
    assert {"risk_score", "risk_factors", "next_action"}.issubset(portfolio.columns)
    assert "Enterprise Renewal Intelligence Brief" in report
    assert "Rules-based decision support" in report


def test_incremental_ingestion_updates_only_changed_source_and_keeps_actions(
    memory_database, monkeypatch
):
    uri, anchor = memory_database
    source_frames = frames()
    checksums = {filename: "version-1" for filename in LOAD_ORDER}
    monkeypatch.setattr(ingestion_module, "read_extracts", lambda _: source_frames)
    monkeypatch.setattr(ingestion_module, "source_checksums", lambda _directory, _extracts: checksums)
    first = ingest(Path("."), uri)
    assert set(first["changed_files"]) == set(LOAD_ORDER)

    action_id = create_action(
        "CUS-001", "Preserve this workflow", "Maya Chen", "Medium", "2026-09-10", [], uri
    )
    source_frames["product_usage_events.csv"].loc[0, "sessions"] = 4321
    checksums["product_usage_events.csv"] = "version-2"
    second = ingest(Path("."), uri)

    assert second["changed_files"] == ["product_usage_events.csv"]
    assert second["loaded"] == 180
    assert anchor.execute(
        "SELECT sessions FROM product_usage_events WHERE usage_event_id = 'USE-001-01'"
    ).fetchone()[0] == 4321
    assert list_actions("CUS-001", uri)[0]["action_id"] == action_id


def test_policy_validation_enforces_governance_relationships():
    invalid = DEFAULT_POLICY.copy()
    invalid["medium_risk_threshold"] = invalid["high_risk_threshold"]
    invalid["renewal_near_days"] = invalid["renewal_mid_days"]
    errors = validate_policy(invalid)
    assert any("Medium-risk" in error for error in errors)
    assert any("Renewal windows" in error for error in errors)


def test_policy_draft_requires_independent_reviewer_and_becomes_active(memory_database):
    uri, _ = memory_database
    baseline_id = ensure_default_policy(uri)
    proposed = DEFAULT_POLICY.copy()
    proposed["critical_support_points"] = 45
    impact = preview_policy_impact(proposed, REFERENCE_DATE, uri)
    assert impact["average_score_delta"] > 0
    draft_id = create_policy_draft(
        "Stricter support policy", proposed, "Policy Author", "Escalate critical support exposure.", uri
    )
    with pytest.raises(ValueError, match="Maker-checker"):
        decide_policy(draft_id, "Approved", "Policy Author", "Self approval", uri)
    decide_policy(draft_id, "Approved", "Independent Reviewer", "Impact reviewed.", uri)
    active_id, active_parameters = get_active_policy(uri)
    assert active_id == draft_id
    assert active_id != baseline_id
    assert active_parameters["critical_support_points"] == 45


def test_risk_change_timeline_explains_policy_reweighting(memory_database):
    uri, _ = memory_database
    ensure_default_policy(uri)
    snapshot_portfolio(REFERENCE_DATE, uri)
    proposed = DEFAULT_POLICY.copy()
    proposed["critical_support_points"] = 5
    draft_id = create_policy_draft(
        "Lower support weight", proposed, "Policy Author", "Test temporal explanation.", uri
    )
    decide_policy(draft_id, "Approved", "Independent Reviewer", "Approved for test.", uri)
    snapshot_portfolio(REFERENCE_DATE, uri)
    changes = risk_change_history("CUS-005", uri)
    assert len(changes) == 2
    assert changes[-1]["score_delta"] < 0
    assert "Unresolved critical support" in changes[-1]["factors_reweighted"]
    assert "reweighted" in changes[-1]["change_explanation"]


def test_unified_timeline_combines_operational_and_decision_events(memory_database):
    uri, _ = memory_database
    snapshot_portfolio(REFERENCE_DATE, uri)
    log_decision("CUS-001", "Executive review", "Maya Chen", "Renewal plan accepted.", None, uri)
    event_types = {event["event_type"] for event in customer_event_timeline("CUS-001", uri)}
    assert {"Product usage", "Renewal milestone", "Risk assessment", "Human decision"}.issubset(event_types)


def test_capacity_planner_respects_every_constraint_and_is_deterministic(memory_database):
    uri, _ = memory_database
    ensure_default_policy(uri)
    inputs = {
        "available_hours": 18,
        "available_budget": 2_500,
        "support_slots": 1,
        "enablement_slots": 1,
        "as_of": REFERENCE_DATE,
        "database_path": uri,
    }
    first = plan_interventions(**inputs)
    second = plan_interventions(**inputs)
    selected = [item for item in first["items"] if item["selected"]]
    assert first["summary"]["hours_allocated"] <= inputs["available_hours"]
    assert first["summary"]["budget_allocated"] <= inputs["available_budget"]
    assert first["summary"]["support_slots_used"] <= inputs["support_slots"]
    assert first["summary"]["enablement_slots_used"] <= inputs["enablement_slots"]
    assert any(not item["selected"] and item["deferral_reason"] for item in first["items"])
    assert [(item["customer_id"], item["factor_name"]) for item in selected] == [
        (item["customer_id"], item["factor_name"])
        for item in second["items"]
        if item["selected"]
    ]


def test_saved_capacity_plan_retains_selected_and_deferred_items(memory_database):
    uri, anchor = memory_database
    ensure_default_policy(uri)
    plan = plan_interventions(
        available_hours=10,
        available_budget=2_000,
        support_slots=1,
        enablement_slots=1,
        as_of=REFERENCE_DATE,
        database_path=uri,
    )
    plan_id = save_capacity_plan(plan, "Revenue Operations", uri)
    persisted = anchor.execute(
        "SELECT COUNT(*), SUM(selected) FROM capacity_plan_items WHERE capacity_plan_id = ?",
        (plan_id,),
    ).fetchone()
    assert persisted[0] == len(plan["items"])
    assert persisted[1] == plan["summary"]["selected_count"]
    selected_customer = next(item["customer_id"] for item in plan["items"] if item["selected"])
    assert "Capacity allocation" in {
        event["event_type"] for event in customer_event_timeline(selected_customer, uri)
    }


def test_onboarding_kit_contains_templates_examples_and_dictionary():
    with zipfile.ZipFile(io.BytesIO(template_bundle())) as archive:
        names = set(archive.namelist())
    assert "README.txt" in names
    for filename in SOURCE_SPECS:
        assert f"blank_templates/{filename}" in names
        assert f"synthetic_examples/{filename}" in names

    dictionary = data_dictionary()
    expected_fields = sum(len(spec["required"]) for spec in SOURCE_SPECS.values())
    assert len(dictionary) == expected_fields
    assert set(dictionary.source_file) == set(SOURCE_SPECS)


def test_completed_ingestion_can_activate_a_business_workspace(memory_database):
    uri, anchor = memory_database
    run_id = "completed-business-import"
    anchor.execute(
        """INSERT INTO ingestion_runs
           (ingestion_run_id, started_at, completed_at, run_status, source_directory,
            records_received, records_loaded, records_rejected)
           VALUES (?, ?, ?, 'COMPLETED', ?, ?, ?, 0)""",
        (run_id, "2026-08-31T09:00:00+00:00", "2026-08-31T09:00:01+00:00", "upload", 42, 42),
    )
    anchor.executemany(
        """INSERT INTO source_file_manifest
           (ingestion_run_id, source_file, sha256, row_count)
           VALUES (?, ?, ?, ?)""",
        [(run_id, filename, f"checksum-{index}", index + 1) for index, filename in enumerate(SOURCE_SPECS)],
    )
    anchor.commit()

    registration_id = register_business_dataset(
        "Acme Customer Success", "Jordan Lee", "Anonymized", run_id, uri
    )
    active = active_business_dataset(uri)
    assert active["business_data_import_id"] == registration_id
    assert active["organization_name"] == "Acme Customer Success"
    assert active["source_file_count"] == len(SOURCE_SPECS)
    assert active["source_row_count"] == sum(range(1, len(SOURCE_SPECS) + 1))


def test_business_workspace_rejects_an_incomplete_ingestion(memory_database):
    uri, anchor = memory_database
    anchor.execute(
        """INSERT INTO ingestion_runs
           (ingestion_run_id, started_at, run_status, source_directory)
           VALUES ('running-import', '2026-08-31T09:00:00+00:00', 'RUNNING', 'upload')"""
    )
    anchor.commit()
    with pytest.raises(ValueError, match="completed governed ingestion"):
        register_business_dataset(
            "Unready Workspace", "Jordan Lee", "Confidential internal", "running-import", uri
        )


def test_publishable_project_has_consistent_branding_and_no_long_dash_characters():
    project_root = Path(__file__).resolve().parents[1]
    publishable = [
        project_root / "README.md",
        project_root / "pyproject.toml",
        project_root / "streamlit_app.py",
    ]
    for folder, pattern in [
        ("src", "*.py"),
        ("tests", "*.py"),
        ("docs", "*.md"),
        ("data", "*.sql"),
        (".streamlit", "*.toml"),
        (".github", "*.yml"),
    ]:
        publishable.extend((project_root / folder).rglob(pattern))

    violations = []
    for path in publishable:
        text = path.read_text(encoding="utf-8")
        if "\u2014" in text or "\u2013" in text or ("V" + "3") in text:
            violations.append(str(path.relative_to(project_root)))
        old_brand = "Enterprise Decision " + "Intelligence Simulator"
        assert old_brand not in text
    assert violations == []
