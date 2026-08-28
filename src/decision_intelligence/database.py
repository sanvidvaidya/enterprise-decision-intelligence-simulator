"""SQLite schema creation and connections for the local decision store."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "decision_intelligence.db"
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema.sql"


def connect(database_path: Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    """Open a SQLite connection with relational integrity enabled."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_database(
    database_path: Path = DEFAULT_DATABASE_PATH,
    schema_path: Path = SCHEMA_PATH,
) -> None:
    """Create an empty, normalized SQLite database from the versioned schema."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = schema_path.read_text(encoding="utf-8")

    with connect(database_path) as connection:
        connection.executescript(schema_sql)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the SQLite decision-store schema.")
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Destination SQLite database path.",
    )
    args = parser.parse_args()
    create_database(args.database)
    print(f"Created SQLite schema at {args.database}")


if __name__ == "__main__":
    main()