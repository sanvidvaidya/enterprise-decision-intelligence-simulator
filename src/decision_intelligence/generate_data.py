"""Create deterministic, fictional extracts for the source systems."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
from random import Random

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
REFERENCE_DATE = date(2026, 8, 28)
RANDOM_SEED = 20260828

ACCOUNT_MANAGERS = [
    ("AM-001", "Maya Chen", "maya.chen@northstar.example", "North America"),
    ("AM-002", "Daniel Okafor", "daniel.okafor@northstar.example", "Europe"),
    ("AM-003", "Priya Nair", "priya.nair@northstar.example", "Asia Pacific"),
    ("AM-004", "Elena Garcia", "elena.garcia@northstar.example", "Latin America"),
    ("AM-005", "Noah Williams", "noah.williams@northstar.example", "North America"),
]

COMPANIES = [
    "Acme Systems", "Bluebird Health", "Cedar Finance", "Delta Logistics", "Evergreen Retail",
    "Fjord Manufacturing", "Granite Energy", "Harbor Education", "Indigo Media", "Juniper Labs",
    "Keystone Analytics", "Lighthouse Foods", "Meridian Travel", "Northwind Security", "Orchid Bio",
    "Pioneer Legal", "Quartz Mobility", "Redwood Telecom", "Summit Hospitality", "Tidal Commerce",
    "Umber Construction", "Vertex Insurance", "Willow Software", "Xenon Aerospace", "Yellowtail Foods",
    "Zenith Consulting", "Atlas Public Sector", "Beacon Properties", "Cascade Robotics", "Driftwood Apparel",
]
INDUSTRIES = ["Technology", "Healthcare", "Financial Services", "Logistics", "Retail", "Manufacturing"]
REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America"]
CATEGORIES = ["Billing", "Integration", "Performance", "User access", "Reporting"]


def iso(value: date) -> str:
    return value.isoformat()


def write_csv(output_dir: Path, filename: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write an empty extract: {filename}")
    destination = output_dir / filename
    with destination.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def profile_for(customer_index: int) -> str:
    if customer_index % 5 == 0:
        return "high_risk"
    if customer_index % 3 == 0:
        return "watch"
    return "healthy"


def build_extracts() -> dict[str, list[dict[str, object]]]:
    """Return consistent fictional CRM, contract, usage, and ticket extracts."""
    rng = Random(RANDOM_SEED)
    managers = [
        {"account_manager_id": manager_id, "full_name": name, "email": email, "region": region, "active": 1}
        for manager_id, name, email, region in ACCOUNT_MANAGERS
    ]
    customers: list[dict[str, object]] = []
    contracts: list[dict[str, object]] = []
    usage_events: list[dict[str, object]] = []
    tickets: list[dict[str, object]] = []

    for index, company in enumerate(COMPANIES, start=1):
        customer_id = f"CUS-{index:03d}"
        profile = profile_for(index)
        segment = ("Enterprise", "Mid-Market", "SMB")[index % 3]
        seats = {"Enterprise": rng.randint(350, 900), "Mid-Market": rng.randint(80, 260), "SMB": rng.randint(20, 75)}[segment]
        manager = ACCOUNT_MANAGERS[(index - 1) % len(ACCOUNT_MANAGERS)]
        region = REGIONS[(index - 1) % len(REGIONS)]
        customers.append({
            "customer_id": customer_id,
            "customer_name": company,
            "industry": INDUSTRIES[(index - 1) % len(INDUSTRIES)],
            "segment": segment,
            "employee_count": seats * rng.randint(4, 18),
            "region": region,
            "account_manager_id": manager[0],
            "customer_status": "At Risk" if profile == "high_risk" else "Active",
            "created_at": iso(REFERENCE_DATE - timedelta(days=rng.randint(400, 1500))),
        })

        renewal_days = {
            "high_risk": rng.randint(10, 35),
            "watch": rng.randint(36, 90),
            "healthy": rng.randint(91, 210),
        }[profile]
        renewal_date = REFERENCE_DATE + timedelta(days=renewal_days)
        acv = round(seats * rng.randint(90, 210), 2)
        contracts.append({
            "contract_id": f"CON-{index:03d}",
            "customer_id": customer_id,
            "contract_start_date": iso(renewal_date - timedelta(days=365)),
            "contract_end_date": iso(renewal_date),
            "renewal_date": iso(renewal_date),
            "annual_contract_value": acv,
            "currency": "USD",
            "contract_status": "Pending Renewal" if renewal_days <= 90 else "Active",
            "auto_renew": 0 if profile == "high_risk" else 1,
        })

        current_active_users = {"high_risk": int(seats * rng.uniform(0.20, 0.42)), "watch": int(seats * rng.uniform(0.48, 0.66)), "healthy": int(seats * rng.uniform(0.70, 0.90))}[profile]
        for month_offset in range(6):
            event_date = date(2026, 3 + month_offset, 1)
            if profile == "high_risk":
                active_users = min(seats, current_active_users + (5 - month_offset) * rng.randint(5, 14))
                adoption = max(8.0, 45.0 - month_offset * rng.uniform(3.0, 5.5))
            elif profile == "watch":
                active_users = min(seats, current_active_users + (5 - month_offset) * rng.randint(1, 5))
                adoption = max(20.0, 61.0 - month_offset * rng.uniform(1.0, 2.5))
            else:
                active_users = min(seats, current_active_users + rng.randint(-4, 5))
                adoption = min(95.0, 72.0 + month_offset * rng.uniform(-1.0, 1.8))
            usage_events.append({
                "usage_event_id": f"USE-{index:03d}-{month_offset + 1:02d}",
                "customer_id": customer_id,
                "event_date": iso(event_date),
                "active_users": active_users,
                "seats_purchased": seats,
                "sessions": max(0, active_users * rng.randint(5, 16)),
                "feature_adoption_pct": round(adoption, 1),
                "source_system": "product_analytics",
            })

        ticket_count = {"high_risk": rng.randint(3, 5), "watch": rng.randint(1, 3), "healthy": rng.randint(0, 2)}[profile]
        for ticket_number in range(1, ticket_count + 1):
            is_unresolved = profile == "high_risk" and ticket_number == 1
            priority = "Critical" if is_unresolved else rng.choice(["Low", "Normal", "High"])
            status = "Open" if is_unresolved else rng.choice(["Resolved", "Closed"])
            opened = REFERENCE_DATE - timedelta(days=rng.randint(2, 120))
            tickets.append({
                "ticket_id": f"TKT-{index:03d}-{ticket_number:02d}",
                "customer_id": customer_id,
                "opened_at": f"{iso(opened)}T09:00:00",
                "resolved_at": "" if is_unresolved else f"{iso(opened + timedelta(days=rng.randint(1, 8)))}T16:00:00",
                "priority": priority,
                "ticket_status": status,
                "ticket_category": rng.choice(CATEGORIES),
                "csat_score": "" if is_unresolved else rng.randint(2 if profile == "watch" else 3, 5),
                "ticket_summary": f"Synthetic {priority.lower()} {rng.choice(CATEGORIES).lower()} request for {company}.",
                "source_system": "support_desk",
            })

    return {
        "account_managers.csv": managers,
        "customers.csv": customers,
        "contracts.csv": contracts,
        "product_usage_events.csv": usage_events,
        "support_tickets.csv": tickets,
    }


def generate_data(output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
    """Write all source extracts using the fixed seed and reference date."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, rows in build_extracts().items():
        write_csv(output_dir, filename, rows)
        print(f"Wrote {len(rows):3d} rows to {output_dir / filename}")


def main() -> None:
    generate_data()


if __name__ == "__main__":
    main()