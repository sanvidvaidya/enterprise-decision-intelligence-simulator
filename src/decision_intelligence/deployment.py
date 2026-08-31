"""Deployment modes and isolated database preparation for safe demonstrations."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from decision_intelligence.database import create_database
from decision_intelligence.generate_data import REFERENCE_DATE, generate_data
from decision_intelligence.ingestion import ingest
from decision_intelligence.policy import ensure_default_policy
from decision_intelligence.workflow import snapshot_portfolio


PUBLIC_DEMO = "public_demo"
PRIVATE_BUSINESS = "private_business"
DEPLOYMENT_ENVIRONMENT_VARIABLE = "EDS_DEPLOYMENT_MODE"


@dataclass(frozen=True)
class DeploymentMode:
    key: str
    label: str
    writes_enabled: bool
    data_uploads_enabled: bool
    description: str

    @property
    def is_public_demo(self) -> bool:
        return self.key == PUBLIC_DEMO

    @property
    def is_private_business(self) -> bool:
        return self.key == PRIVATE_BUSINESS


MODES = {
    PUBLIC_DEMO: DeploymentMode(
        key=PUBLIC_DEMO,
        label="Public Demo",
        writes_enabled=False,
        data_uploads_enabled=False,
        description="Synthetic, isolated, and read-only for public portfolio access.",
    ),
    PRIVATE_BUSINESS: DeploymentMode(
        key=PRIVATE_BUSINESS,
        label="Private Business",
        writes_enabled=True,
        data_uploads_enabled=True,
        description="Persistent local workspace for authorized organizational data.",
    ),
}


def deployment_mode(value: str | None = None) -> DeploymentMode:
    """Resolve a strict deployment mode, defaulting to the safest public behavior."""

    selected = (value if value is not None else os.getenv(DEPLOYMENT_ENVIRONMENT_VARIABLE, PUBLIC_DEMO))
    selected = selected.strip().lower()
    if selected not in MODES:
        allowed = ", ".join(sorted(MODES))
        raise ValueError(
            f"Invalid {DEPLOYMENT_ENVIRONMENT_VARIABLE} value '{selected}'. "
            f"Expected one of: {allowed}."
        )
    return MODES[selected]


def initialize_public_demo_database(directory: str | Path | None = None) -> Path:
    """Create a fresh synthetic database outside the repository for a demo process."""

    if directory is None:
        target_directory = Path(tempfile.mkdtemp(prefix="enterprise-decision-demo-"))
    else:
        target_directory = Path(directory)
        target_directory.mkdir(parents=True, exist_ok=True)
    source_directory = target_directory / "source"
    database_path = target_directory / "public_demo.db"
    generate_data(source_directory)
    create_database(database_path)
    ingestion = ingest(source_directory, database_path)
    if ingestion["status"] != "COMPLETED":
        raise RuntimeError(f"Public demonstration bootstrap failed: {ingestion['status']}")
    ensure_default_policy(database_path)
    snapshot_portfolio(REFERENCE_DATE, database_path)
    return database_path


def require_private_mode(mode: DeploymentMode, operation: str) -> None:
    """Reject state-changing operations outside an explicitly private deployment."""

    if not mode.writes_enabled:
        raise PermissionError(
            f"{operation} is disabled in {mode.label} mode. "
            f"Set {DEPLOYMENT_ENVIRONMENT_VARIABLE}={PRIVATE_BUSINESS} only on an authorized private installation."
        )
