# Enterprise Decision Intelligence Simulator

A compact, local-first decision-support application for a fictional enterprise SaaS company. It integrates CRM, contract, product-usage, and support data to answer:

> Which customers are at the highest risk of not renewing, why, and what should the account manager do?

The application uses deterministic business rules—not an LLM or machine-learning model—and attaches each recommendation to exact supporting source records.

## Highlights

- Fully local: no cloud services, API keys, paid APIs, Docker, or model downloads.
- Reproducible synthetic data: fixed seed, fixed reference date, and versioned generator.
- Governed integration: validation, row-level quality issues, warning approvals, ingestion history, and SHA-256 file manifests.
- Explainable decisions: a weighted 0–100 risk score with factor-level evidence and actions.
- Portable: SQLite database plus Python, pandas, Streamlit, and pytest.

## Quick start

Requires Python 3.11+ and Git.

```bash
git clone <YOUR-REPOSITORY-URL>
cd enterprise-decision-intelligence-simulator
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

Install and run:

```bash
python -m pip install -r requirements.txt
# Windows PowerShell: $env:PYTHONPATH = "$PWD/src"
# macOS/Linux: export PYTHONPATH="$PWD/src"
python -m decision_intelligence.generate_data
python -m decision_intelligence.ingestion
streamlit run src/decision_intelligence/app.py
```

Run tests:

```bash
python -m pytest
```

## Sample questions

- Which customers have the highest renewal risk?
- What source records caused this customer’s risk score?
- Which unresolved critical tickets should be escalated before renewal?
- Which accounts need an adoption-recovery plan this week?

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Data model](docs/DATA_MODEL.md)
- [Data ingestion and quality](docs/INGESTION_AND_DATA_QUALITY.md)
- [Risk methodology](docs/METHODOLOGY.md)
- [Limitations](docs/LIMITATIONS.md)

## Screenshots

Add Streamlit dashboard screenshots here after launching the app locally. Suggested captures: the high-risk customer view, factor evidence expanders, usage trend, and support-history table.

## Future AI integration

A future optional LLM could consume a structured context object containing the customer summary, risk score, triggered factors, evidence IDs, and approved recommended actions. The SQLite records and deterministic risk engine would remain the system of record; an LLM would only turn that governed context into narrative.

## License

MIT. See [LICENSE](LICENSE).