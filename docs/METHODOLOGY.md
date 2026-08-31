# Methodology

## Explainable renewal-risk policy

The engine is deterministic: identical records and an identical evaluation date produce an identical result. It sums triggered factor points, caps the total at 100, and classifies Low (0 to 29), Medium (30 to 54), or High (55 to 100).

| Factor | Condition | Points |
| --- | --- | ---: |
| Declining product usage | Active users decline at least 30% month over month | 30 |
| Declining product usage | Active users decline 15 to 29% | 18 |
| Low seat engagement | Active users below 40% of purchased seats | 15 |
| Low seat engagement | Active users at 40 to 59% of seats | 8 |
| Unresolved critical support | At least one Critical ticket is Open/In Progress | 30 |
| Renewal approaching | Renewal in ≤30 / ≤60 / ≤90 days | 20 / 12 / 6 |
| High contract value | ACV ≥$100k / ≥$50k | 10 / 5 |

High contract value is an exposure multiplier, not a claim that valuable customers are behaviorally more likely to churn. Its purpose is to elevate material renewals in a decision queue.

Every triggered factor contains its name, points, plain-language explanation, evidence record IDs, and a recommended intervention. The Customer 360 resolves those IDs back to complete source rows.

## Scenario methodology

The Scenario Lab applies three explicit assumptions to an in-memory copy of the customer context:

- **Recover inactive seats:** activates the selected percentage of the gap between current active users and purchased seats.
- **Resolve critical tickets:** removes the unresolved-critical rule for the scenario.
- **Extend renewal:** shifts the renewal date by a selected number of days when evaluating urgency.

The same scoring rules evaluate the changed context. Operational records are never edited. A saved scenario retains the assumptions, baseline, simulated score, simulated band, and complete result JSON. Scenarios answer “what would the policy say if these conditions became true?” They do not answer “what will happen?”

## Portfolio prioritization

The command center sorts primarily by risk score and secondarily by commercial exposure. It reports high-risk ACV and near-term renewals separately so leaders can distinguish likelihood signals from business impact.

## Model governance

Changing a threshold or weight is a policy change. Policy Studio persists the complete proposal, author, rationale, and version number. It replays every customer under the proposed parameters and reports score deltas, classification changes, and reclassified ACV. A separate reviewer identity must approve the draft before it replaces the active version; the prior version becomes Retired. Every subsequent snapshot links to the policy used.

## Temporal explanation

For consecutive assessments, the timeline compares factor names and points. It identifies factors added, removed, or reweighted and reports the score delta plus involved evidence IDs. A separate event timeline merges product observations, support openings/resolutions, renewal milestones, scenarios, actions, assessments, and human decisions. This is a deterministic historical comparison, not causal attribution.

## Capacity allocation methodology

The planner creates one candidate for each actionable factor. Each intervention has an explicit delivery team, estimated hours, estimated cost, and specialized slot requirements. It calculates:

```text
decision value = addressable rule points × annual contract value × renewal urgency
                 ÷ estimated hours ÷ 1,000
```

Candidates are sorted by decision value, then allocated while enforcing available hours, budget, support escalation slots, enablement slots, and a per-customer intervention limit. The saved plan includes both selected and deferred candidates with the binding reasons. This is a transparent greedy allocation heuristic, not a forecast of financial return or proof of mathematical optimality.
