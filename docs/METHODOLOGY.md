# Methodology

## Explainable renewal-risk model

The model is deterministic: the same integrated records and evaluation date always produce the same result. It sums factor points, caps the total at 100, and classifies risk as Low (0–29), Medium (30–54), or High (55–100).

| Factor | Condition | Points |
| --- | --- | ---: |
| Declining product usage | Active users decline at least 30% month-over-month | 30 |
| Declining product usage | Active users decline 15–29% | 18 |
| Low seat engagement | Latest active users are below 40% of purchased seats | 15 |
| Low seat engagement | Latest active users are 40–59% of seats | 8 |
| Unresolved critical support | One or more critical tickets are Open/In Progress | 30 |
| Renewal approaching | Renewal in ≤30 / ≤60 / ≤90 days | 20 / 12 / 6 |
| High contract value | ACV ≥$100k / ≥$50k | 10 / 5 |

Every factor includes its points, human-readable explanation, evidence record IDs, and recommended account-manager action. The model is policy, not prediction; thresholds and weights are deliberately easy to review and change.