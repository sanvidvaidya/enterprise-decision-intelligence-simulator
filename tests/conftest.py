"""Global test configuration and auto-initialization fixtures."""

import os
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / 'src'
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

@pytest.fixture(scope='session', autouse=True)
def ensure_test_database():
    """Automatically ensure synthetic data and SQLite database exist before tests run."""
    db_path = PROJECT_ROOT / 'data' / 'decision_intelligence.db'
    raw_dir = PROJECT_ROOT / 'data' / 'raw'
    
    customers_csv = raw_dir / 'customers.csv'
    if not customers_csv.exists():
        from decision_intelligence.generate_data import generate_data
        generate_data(output_dir=raw_dir)
        
    if not db_path.exists():
        from decision_intelligence.ingestion import ingest
        ingest(source_directory=raw_dir, database_path=db_path)
