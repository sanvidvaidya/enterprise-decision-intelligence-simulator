"""Validate CSV extracts and atomically load them into SQLite."""

from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from decision_intelligence.database import DEFAULT_DATABASE_PATH, create_database, connect
from decision_intelligence.validation import SOURCE_SPECS, ValidationIssue, validate_extracts

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "data" / "raw"
LOAD_ORDER = ["account_managers.csv", "customers.csv", "contracts.csv", "product_usage_events.csv", "support_tickets.csv"]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def source_checksums(source_directory: Path, extracts: dict[str, pd.DataFrame]) -> dict[str, str]:
    """Return SHA-256 checksums for immutable source-file lineage."""
    return {name: hashlib.sha256((source_directory / name).read_bytes()).hexdigest() for name in extracts}


def read_extracts(source_directory: Path) -> dict[str, pd.DataFrame]:
    """Read known source extracts as strings to preserve source values for validation."""
    extracts: dict[str, pd.DataFrame] = {}
    for filename in SOURCE_SPECS:
        source_path = source_directory / filename
        if source_path.exists():
            extracts[filename] = pd.read_csv(source_path, dtype=str, keep_default_na=False)
    return extracts


def _record_issues(connection, run_id: str, issues: list[ValidationIssue]) -> None:
    created_at = utc_timestamp()
    rows = [
        (str(uuid4()), run_id, issue.source_file, issue.row_number, issue.source_record_id, issue.field_name, issue.severity, issue.rule_name, issue.issue_message, issue.raw_value, created_at)
        for issue in issues
    ]
    connection.executemany(
        """INSERT INTO data_quality_issues
        (data_quality_issue_id, ingestion_run_id, source_file, row_number, source_record_id, field_name, severity, rule_name, issue_message, raw_value, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )


def _prepare_for_load(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    for column in ("resolved_at", "csat_score"):
        if column in prepared:
            prepared[column] = prepared[column].replace("", None)
    return prepared


def _upsert_extract(connection, filename: str, frame: pd.DataFrame) -> None:
    """Insert new records and update existing records for one changed source."""

    table_name = SOURCE_SPECS[filename]["table"]
    identifier = SOURCE_SPECS[filename]["id"]
    prepared = _prepare_for_load(frame)
    prepared = prepared.where(pd.notna(prepared), None)

    # Whitelist columns strictly against the authorized schema specification
    allowed_columns = set(SOURCE_SPECS[filename]["required"])
    columns = [column for column in prepared.columns if column in allowed_columns]
    if not columns or identifier not in columns:
        raise ValueError(f"Extracted columns do not match required schema for {table_name}")

    prepared = prepared[columns]
    placeholders = ", ".join("?" for _ in columns)
    quoted_cols = ", ".join(f'"{column}"' for column in columns)
    updates = ", ".join(f'"{column}" = excluded."{column}"' for column in columns if column != identifier)
    statement = (
        f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES ({placeholders}) '
        f'ON CONFLICT("{identifier}") DO UPDATE SET {updates}'
    )
    connection.executemany(statement, prepared.itertuples(index=False, name=None))


def _delete_records_missing_from_snapshot(connection, filename: str, frame: pd.DataFrame) -> None:
    """Remove stale rows because each CSV represents a complete source snapshot."""

    table_name = SOURCE_SPECS[filename]["table"]
    identifier = SOURCE_SPECS[filename]["id"]
    record_ids = frame[identifier].tolist()
    if not record_ids:
        connection.execute(f'DELETE FROM "{table_name}"')
        return
    placeholders = ", ".join("?" for _ in record_ids)
    connection.execute(
        f'DELETE FROM "{table_name}" WHERE "{identifier}" NOT IN ({placeholders})',
        record_ids,
    )


def _remove_workflow_for_deleted_customers(connection, customers: pd.DataFrame) -> None:
    """Keep workflow history for retained IDs and safely remove orphan-bound rows."""

    customer_ids = customers["customer_id"].tolist()
    placeholders = ", ".join("?" for _ in customer_ids)
    predicate = f"customer_id NOT IN ({placeholders})" if customer_ids else "1 = 1"
    parameters = customer_ids if customer_ids else []
    connection.execute(f"DELETE FROM capacity_plan_items WHERE {predicate}", parameters)
    connection.execute(f"DELETE FROM decision_events WHERE {predicate}", parameters)
    connection.execute(f"DELETE FROM account_actions WHERE {predicate}", parameters)
    connection.execute(f"DELETE FROM scenario_runs WHERE {predicate}", parameters)
    connection.execute(f"DELETE FROM risk_assessments WHERE {predicate}", parameters)


def ingest(source_directory: Path = DEFAULT_SOURCE_DIR, database_path: Path = DEFAULT_DATABASE_PATH, approve_warnings: bool = False, approved_by: str | None = None) -> dict[str, object]:
    """Validate all extracts, then load all tables or none of them."""
    create_database(database_path)
    extracts = read_extracts(source_directory)
    received = sum(len(frame) for frame in extracts.values())
    run_id = str(uuid4())

    with connect(database_path) as connection:
        connection.execute(
            "INSERT INTO ingestion_runs (ingestion_run_id, started_at, run_status, source_directory, records_received) VALUES (?, ?, 'RUNNING', ?, ?)",
            (run_id, utc_timestamp(), str(source_directory.resolve()), received),
        )
        issues = validate_extracts(extracts)
        errors = [issue for issue in issues if issue.severity == "ERROR"]
        warnings = [issue for issue in issues if issue.severity == "WARNING"]
        if errors or (warnings and not approve_warnings):
            _record_issues(connection, run_id, issues)
            connection.execute(
                "UPDATE ingestion_runs SET completed_at = ?, run_status = 'FAILED_VALIDATION', records_rejected = ? WHERE ingestion_run_id = ?",
                (utc_timestamp(), len(errors) + len(warnings), run_id),
            )
            return {"run_id": run_id, "status": "FAILED_VALIDATION", "issues": len(issues), "loaded": 0}

        try:
            checksums = source_checksums(source_directory, extracts)
            previous_rows = connection.execute("""SELECT source_file, sha256 FROM source_file_manifest
                WHERE ingestion_run_id = (SELECT ingestion_run_id FROM ingestion_runs WHERE run_status = 'COMPLETED' ORDER BY started_at DESC LIMIT 1)""").fetchall()
            previous = {row["source_file"]: row["sha256"] for row in previous_rows}
            changed_files = [name for name in LOAD_ORDER if previous.get(name) != checksums[name]]
            unchanged = bool(previous) and not changed_files
            connection.executemany(
                "INSERT INTO source_file_manifest (ingestion_run_id, source_file, sha256, row_count) VALUES (?, ?, ?, ?)",
                [(run_id, name, checksums[name], len(frame)) for name, frame in extracts.items()],
            )
            if warnings:
                _record_issues(connection, run_id, warnings)
                connection.execute("INSERT INTO data_quality_warning_approvals (ingestion_run_id, approved_by, approved_at) VALUES (?, ?, ?)", (run_id, approved_by or "command-line approval", utc_timestamp()))
            if not unchanged:
                if "customers.csv" in changed_files:
                    _remove_workflow_for_deleted_customers(connection, extracts["customers.csv"])
                for filename in changed_files:
                    _upsert_extract(connection, filename, extracts[filename])
                for filename in reversed(changed_files):
                    _delete_records_missing_from_snapshot(connection, filename, extracts[filename])
        except Exception:
            connection.execute(
                "UPDATE ingestion_runs SET completed_at = ?, run_status = 'FAILED_LOAD' WHERE ingestion_run_id = ?",
                (utc_timestamp(), run_id),
            )
            raise

        connection.execute(
            "UPDATE ingestion_runs SET completed_at = ?, run_status = 'COMPLETED', records_loaded = ? WHERE ingestion_run_id = ?",
            (utc_timestamp(), 0 if unchanged else sum(len(extracts[name]) for name in changed_files), run_id),
            )
    loaded = 0 if unchanged else sum(len(extracts[name]) for name in changed_files)
    return {"run_id": run_id, "status": "SKIPPED_UNCHANGED" if unchanged else "COMPLETED", "issues": len(warnings), "loaded": loaded, "changed_files": changed_files}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and ingest source CSV extracts into SQLite.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE_PATH)
    parser.add_argument("--approve-warnings", action="store_true")
    parser.add_argument("--approved-by")
    args = parser.parse_args()
    result = ingest(args.source_dir, args.database, args.approve_warnings, args.approved_by)
    print(f"Ingestion {result['status']}: {result['loaded']} rows loaded, {result['issues']} issues, run ID {result['run_id']}")


if __name__ == "__main__":
    main()
