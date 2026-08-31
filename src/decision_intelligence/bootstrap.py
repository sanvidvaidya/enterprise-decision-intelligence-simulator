"""One-command local setup for a fresh clone."""

from decision_intelligence.database import DEFAULT_DATABASE_PATH, create_database
from decision_intelligence.generate_data import REFERENCE_DATE, generate_data
from decision_intelligence.ingestion import ingest
from decision_intelligence.policy import ensure_default_policy
from decision_intelligence.workflow import snapshot_portfolio


def bootstrap() -> dict[str, object]:
    create_database()
    ensure_default_policy()
    generate_data()
    ingestion = ingest()
    snapshot = snapshot_portfolio(REFERENCE_DATE)
    return {"database": str(DEFAULT_DATABASE_PATH), "ingestion": ingestion, "snapshot": snapshot}


def main() -> None:
    result = bootstrap()
    print(f"Ready: {result['database']}")
    print(f"Ingestion: {result['ingestion']['status']}")
    print(f"Portfolio snapshot: {result['snapshot']['customers_assessed']} customers")


if __name__ == "__main__":
    main()
