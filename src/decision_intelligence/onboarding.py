"""Business-data onboarding, templates, profiling, and local dataset registration."""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from decision_intelligence.database import DEFAULT_DATABASE_PATH, connect
from decision_intelligence.generate_data import build_extracts
from decision_intelligence.validation import SOURCE_SPECS

MAX_SOURCE_FILE_BYTES = 50 * 1024 * 1024

FIELD_DESCRIPTIONS = {
    "account_manager_id": "Stable account owner identifier",
    "full_name": "Account manager full name",
    "email": "Business email used for ownership routing",
    "region": "Operating region or territory",
    "active": "One for an active employee, zero otherwise",
    "customer_id": "Stable customer organization identifier",
    "customer_name": "Customer organization name",
    "industry": "Customer industry",
    "segment": "SMB, Mid-Market, or Enterprise",
    "employee_count": "Approximate customer employee count",
    "customer_status": "Active, At Risk, or Churned",
    "created_at": "ISO date when the customer record was created",
    "contract_id": "Stable contract identifier",
    "contract_start_date": "ISO contract start date",
    "contract_end_date": "ISO contract end date",
    "renewal_date": "ISO contractual renewal date",
    "annual_contract_value": "Annual contract value as a positive number",
    "currency": "Three-letter currency code",
    "contract_status": "Active, Pending Renewal, or Expired",
    "auto_renew": "One when auto-renew applies, zero otherwise",
    "usage_event_id": "Stable monthly usage observation identifier",
    "event_date": "ISO date for the usage observation",
    "active_users": "Users active during the observation period",
    "seats_purchased": "Contracted product seats",
    "sessions": "Sessions during the observation period",
    "feature_adoption_pct": "Feature adoption percentage from zero to one hundred",
    "source_system": "Originating system name",
    "ticket_id": "Stable support request identifier",
    "opened_at": "ISO timestamp when the ticket opened",
    "resolved_at": "ISO resolution timestamp, blank while unresolved",
    "priority": "Low, Normal, High, or Critical",
    "ticket_status": "Open, In Progress, Resolved, or Closed",
    "ticket_category": "Support request category",
    "csat_score": "Customer satisfaction score from one to five, or blank",
    "ticket_summary": "Short factual support request summary",
}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _csv_bytes(columns: list[str], rows: list[dict[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows([{column: row.get(column, "") for column in columns} for row in rows])
    return buffer.getvalue().encode("utf-8")


def template_bundle() -> bytes:
    """Return blank contracts, complete synthetic examples, and instructions as ZIP."""

    examples = build_extracts()
    output = io.BytesIO()
    instructions = """Enterprise Decision Simulator data onboarding

1. Keep every required filename and column header unchanged.
2. Replace the synthetic example values with your governed business data.
3. Use stable IDs consistently across every file.
4. Product usage is expected at a monthly customer grain, not raw clickstream grain.
5. Remove or pseudonymize personal data that is not needed for renewal decisions.
6. Upload all five files together. Validation runs before any operational row changes.
7. Keep each source file below 50 MB for this compact local application.

The application stores imported data only in the local SQLite database unless your
organization separately deploys the project to shared infrastructure.
"""
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.txt", instructions)
        for filename, spec in SOURCE_SPECS.items():
            columns = list(spec["required"])
            archive.writestr(f"blank_templates/{filename}", _csv_bytes(columns, []))
            archive.writestr(f"synthetic_examples/{filename}", _csv_bytes(columns, examples[filename]))
    return output.getvalue()


def data_dictionary() -> pd.DataFrame:
    """Return the complete upload contract as a presentation-ready table."""

    examples = build_extracts()
    rows = []
    for filename, spec in SOURCE_SPECS.items():
        example = examples[filename][0] if examples[filename] else {}
        for field in spec["required"]:
            rows.append(
                {
                    "source_file": filename,
                    "field": field,
                    "required": "Yes",
                    "description": FIELD_DESCRIPTIONS.get(field, "Governed source value"),
                    "example": example.get(field, ""),
                }
            )
    return pd.DataFrame(rows)


def profile_extracts(extracts: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Summarize uploaded files without retaining a second copy of their data."""

    profiles = []
    for filename in SOURCE_SPECS:
        frame = extracts.get(filename)
        if frame is None:
            profiles.append(
                {
                    "source_file": filename,
                    "status": "Missing",
                    "rows": 0,
                    "columns": 0,
                    "unique_ids": 0,
                }
            )
            continue
        identifier = SOURCE_SPECS[filename]["id"]
        profiles.append(
            {
                "source_file": filename,
                "status": "Ready",
                "rows": len(frame),
                "columns": len(frame.columns),
                "unique_ids": frame[identifier].nunique(dropna=True) if identifier in frame else 0,
            }
        )
    return profiles


def register_business_dataset(
    organization_name: str,
    imported_by: str,
    data_classification: str,
    ingestion_run_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> str:
    """Activate a successfully ingested dataset and retain its organizational owner."""

    organization_name = organization_name.strip()
    imported_by = imported_by.strip()
    allowed = {"Synthetic demo", "Anonymized", "Confidential internal"}
    if not organization_name or len(organization_name) > 120:
        raise ValueError("Organization name is required and must be 120 characters or fewer")
    if not imported_by:
        raise ValueError("Data steward name is required")
    if data_classification not in allowed:
        raise ValueError("Unknown data classification")
    registration_id = str(uuid4())
    with connect(database_path) as connection:
        run = connection.execute(
            "SELECT run_status FROM ingestion_runs WHERE ingestion_run_id = ?",
            (ingestion_run_id,),
        ).fetchone()
        if not run or run["run_status"] != "COMPLETED":
            raise ValueError("Only a completed governed ingestion can be activated")
        manifest = connection.execute(
            """SELECT COUNT(*) AS file_count, COALESCE(SUM(row_count), 0) AS row_count
                 FROM source_file_manifest WHERE ingestion_run_id = ?""",
            (ingestion_run_id,),
        ).fetchone()
        connection.execute("UPDATE business_data_imports SET active = 0 WHERE active = 1")
        connection.execute(
            """INSERT INTO business_data_imports
               (business_data_import_id, organization_name, imported_at, imported_by,
                data_classification, ingestion_run_id, source_file_count,
                source_row_count, active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (
                registration_id,
                organization_name,
                utc_timestamp(),
                imported_by,
                data_classification,
                ingestion_run_id,
                manifest["file_count"],
                manifest["row_count"],
            ),
        )
    return registration_id


def active_business_dataset(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> dict[str, Any]:
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM business_data_imports WHERE active = 1"
        ).fetchone()
    if row:
        return dict(row)
    return {
        "organization_name": "Synthetic demonstration workspace",
        "imported_at": None,
        "imported_by": "System bootstrap",
        "data_classification": "Synthetic demo",
        "ingestion_run_id": None,
        "source_file_count": len(SOURCE_SPECS),
        "source_row_count": 0,
        "active": 1,
    }


def list_business_datasets(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict[str, Any]]:
    with connect(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM business_data_imports ORDER BY imported_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]
