"""Transparent validation rules for source-system extracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

SOURCE_SPECS = {
    "account_managers.csv": {"table": "account_managers", "id": "account_manager_id", "required": ["account_manager_id", "full_name", "email", "region", "active"]},
    "customers.csv": {"table": "customers", "id": "customer_id", "required": ["customer_id", "customer_name", "industry", "segment", "employee_count", "region", "account_manager_id", "customer_status", "created_at"]},
    "contracts.csv": {"table": "contracts", "id": "contract_id", "required": ["contract_id", "customer_id", "contract_start_date", "contract_end_date", "renewal_date", "annual_contract_value", "currency", "contract_status", "auto_renew"]},
    "product_usage_events.csv": {"table": "product_usage_events", "id": "usage_event_id", "required": ["usage_event_id", "customer_id", "event_date", "active_users", "seats_purchased", "sessions", "feature_adoption_pct", "source_system"]},
    "support_tickets.csv": {"table": "support_tickets", "id": "ticket_id", "required": ["ticket_id", "customer_id", "opened_at", "resolved_at", "priority", "ticket_status", "ticket_category", "csat_score", "ticket_summary", "source_system"]},
}


@dataclass(frozen=True)
class ValidationIssue:
    source_file: str
    row_number: int | None
    source_record_id: str | None
    field_name: str | None
    rule_name: str
    issue_message: str
    raw_value: str | None = None
    severity: str = "ERROR"


def _issue(issues: list[ValidationIssue], source_file: str, row_number: int | None, record_id: str | None, field: str | None, rule: str, message: str, value: object = None, severity: str = "ERROR") -> None:
    issues.append(ValidationIssue(source_file, row_number, record_id, field, rule, message, None if value is None else str(value), severity))


def _nonempty(series: pd.Series) -> pd.Series:
    return series.notna() & series.astype(str).str.strip().ne("")


def _validate_required_and_ids(filename: str, frame: pd.DataFrame, issues: list[ValidationIssue]) -> None:
    spec = SOURCE_SPECS[filename]
    missing = set(spec["required"]) - set(frame.columns)
    for column in sorted(missing):
        _issue(issues, filename, None, None, column, "required_column", f"Required column '{column}' is missing.")
    if missing:
        return
    identifier = spec["id"]
    for index, value in frame.loc[~_nonempty(frame[identifier]), identifier].items():
        _issue(issues, filename, index + 2, None, identifier, "required_value", "Primary identifier must not be blank.", value)
    duplicates = frame.loc[_nonempty(frame[identifier]) & frame[identifier].duplicated(keep=False), identifier]
    for index, value in duplicates.items():
        _issue(issues, filename, index + 2, str(value), identifier, "unique_identifier", "Primary identifier must be unique within its source file.", value)
    optional_values = {"support_tickets.csv": {"resolved_at", "csat_score"}}.get(filename, set())
    for column in spec["required"]:
        if column == identifier or column in optional_values:
            continue
        for index, value in frame.loc[~_nonempty(frame[column]), column].items():
            _issue(issues, filename, index + 2, str(frame.at[index, identifier]), column, "required_value", "Required value must not be blank.", value)


def _validate_numeric(filename: str, frame: pd.DataFrame, column: str, minimum: float, maximum: float | None, issues: list[ValidationIssue]) -> None:
    if column not in frame:
        return
    identifier = SOURCE_SPECS[filename]["id"]
    values = pd.to_numeric(frame[column], errors="coerce")
    invalid = (_nonempty(frame[column]) & values.isna()) | (values < minimum)
    if maximum is not None:
        invalid |= values > maximum
    for index, value in frame.loc[invalid, column].items():
        _issue(issues, filename, index + 2, str(frame.at[index, identifier]), column, "numeric_range", f"Value must be numeric and between {minimum} and {maximum if maximum is not None else 'infinity'}.", value)


def _validate_dates(filename: str, frame: pd.DataFrame, columns: list[str], issues: list[ValidationIssue]) -> None:
    identifier = SOURCE_SPECS[filename]["id"]
    for column in columns:
        if column not in frame:
            continue
        invalid = pd.to_datetime(frame[column], errors="coerce").isna() & _nonempty(frame[column])
        for index, value in frame.loc[invalid, column].items():
            _issue(issues, filename, index + 2, str(frame.at[index, identifier]), column, "valid_date", "Value must be a valid ISO-style date or timestamp.", value)


def _validate_allowed(filename: str, frame: pd.DataFrame, column: str, allowed: set[str], issues: list[ValidationIssue]) -> None:
    if column not in frame:
        return
    identifier = SOURCE_SPECS[filename]["id"]
    invalid = ~frame[column].isin(allowed)
    for index, value in frame.loc[invalid, column].items():
        _issue(issues, filename, index + 2, str(frame.at[index, identifier]), column, "allowed_value", f"Value must be one of: {', '.join(sorted(allowed))}.", value)


def validate_extracts(extracts: dict[str, pd.DataFrame]) -> list[ValidationIssue]:
    """Validate structural, domain, and cross-system integrity rules."""
    issues: list[ValidationIssue] = []
    for filename in SOURCE_SPECS:
        if filename not in extracts:
            _issue(issues, filename, None, None, None, "source_file", "Required source file is missing.")
        else:
            _validate_required_and_ids(filename, extracts[filename], issues)

    for filename, column, minimum, maximum in [
        ("account_managers.csv", "active", 0, 1), ("customers.csv", "employee_count", 1, None),
        ("contracts.csv", "annual_contract_value", 0.01, None), ("contracts.csv", "auto_renew", 0, 1),
        ("product_usage_events.csv", "active_users", 0, None), ("product_usage_events.csv", "seats_purchased", 1, None),
        ("product_usage_events.csv", "sessions", 0, None), ("product_usage_events.csv", "feature_adoption_pct", 0, 100),
        ("support_tickets.csv", "csat_score", 1, 5),
    ]:
        if filename in extracts:
            _validate_numeric(filename, extracts[filename], column, minimum, maximum, issues)

    for filename, columns in [("customers.csv", ["created_at"]), ("contracts.csv", ["contract_start_date", "contract_end_date", "renewal_date"]), ("product_usage_events.csv", ["event_date"]), ("support_tickets.csv", ["opened_at", "resolved_at"])]:
        if filename in extracts:
            _validate_dates(filename, extracts[filename], columns, issues)

    for filename, column, allowed in [
        ("customers.csv", "segment", {"SMB", "Mid-Market", "Enterprise"}), ("customers.csv", "customer_status", {"Active", "At Risk", "Churned"}),
        ("contracts.csv", "contract_status", {"Active", "Pending Renewal", "Expired"}),
        ("support_tickets.csv", "priority", {"Low", "Normal", "High", "Critical"}), ("support_tickets.csv", "ticket_status", {"Open", "In Progress", "Resolved", "Closed"}),
    ]:
        if filename in extracts:
            _validate_allowed(filename, extracts[filename], column, allowed, issues)

    if "account_managers.csv" in extracts and "customers.csv" in extracts:
        manager_ids = set(extracts["account_managers.csv"]["account_manager_id"])
        for index, value in extracts["customers.csv"].loc[~extracts["customers.csv"]["account_manager_id"].isin(manager_ids), "account_manager_id"].items():
            _issue(issues, "customers.csv", index + 2, str(extracts["customers.csv"].at[index, "customer_id"]), "account_manager_id", "foreign_key", "Account manager does not exist in account_managers.csv.", value)
    if "customers.csv" in extracts:
        customer_ids = set(extracts["customers.csv"]["customer_id"])
        for filename in ("contracts.csv", "product_usage_events.csv", "support_tickets.csv"):
            if filename in extracts:
                for index, value in extracts[filename].loc[~extracts[filename]["customer_id"].isin(customer_ids), "customer_id"].items():
                    _issue(issues, filename, index + 2, str(extracts[filename].at[index, SOURCE_SPECS[filename]["id"]]), "customer_id", "foreign_key", "Customer does not exist in customers.csv.", value)
    if "product_usage_events.csv" in extracts:
        frame = extracts["product_usage_events.csv"]
        mask = pd.to_numeric(frame["active_users"], errors="coerce") > pd.to_numeric(frame["seats_purchased"], errors="coerce")
        for index, row in frame.loc[mask].iterrows():
            _issue(issues, "product_usage_events.csv", index + 2, str(row["usage_event_id"]), "active_users", "seat_capacity_anomaly", "Active users exceed purchased seats; review source extract.", row["active_users"], "WARNING")
    return issues