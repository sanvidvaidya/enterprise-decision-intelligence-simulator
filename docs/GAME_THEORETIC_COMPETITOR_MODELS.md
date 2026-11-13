# Game-Theoretic Competitor Counter-Moves & Market Equilibrium

Traditional SaaS pricing, renewal, and retention models assume passive markets: they assume that when an enterprise hikes pricing by 15% or restricts discounting, competitors stand idle.

In reality, enterprise SaaS markets behave as dynamic oligopolies. Competitors actively track renewal cycles, identify disaffected accounts, and deploy migration buyout credits to poach vulnerable clients.

The **Game-Theoretic Competitor Counter-Moves & Dynamic Market Equilibrium Engine** (`src/decision_intelligence/gametheory.py`) replaces static assumptions with Stackelberg/Nash strategic interaction matrices and deterministic account-level vulnerability scoring.

---

## 1. Competitive Vulnerability Index (CVI)

The CVI scores account poaching vulnerability from 0 to 100 based on four deterministic pillars:

1. **Renewal Proximity (Max 30 pts):** Accounts within 30 or 90 days of contract renewal are prime targets for competitor migration campaigns.
2. **Dissatisfaction Deficit (Max 35 pts):** Inverted health score reflecting engagement and product satisfaction.
3. **Operational Friction (Max 25 pts):** Open Critical support tickets and sub-70% seat adoption.
4. **Target Attractiveness (Max 10 pts):** High-ACV accounts attract disproportionate rival poaching investment and executive sponsorship.

### Vulnerability Tiers & Recommended Defenses
- **CRITICAL (CVI >= 75):** Immediate executive sponsor intervention + proactive multi-year price lock with migration parity protection.
- **HIGH (50 <= CVI < 75):** Technical TAM dispatch to resolve open tickets and execute CS adoption review.
- **MEDIUM (25 <= CVI < 50):** Standard automated renewal sequence with early-bird renewal incentive.
- **LOW (CVI < 25):** Account is stable; pursue expansion cross-sell.

---

## 2. Strategic Payoff Matrix (4x4)

The engine models strategic interactions across 4 Vendor Strategies and 4 Competitor Counter-Moves:

| Vendor Strategy | Competitor Counter-Move | Projected NRR | Gross Churn | Lost ACV |
| :--- | :--- | :--- | :--- | :--- |
| **HOLD_BASELINE** | PASSIVE_HOLD | 99.6% | 0.4% | Baseline attrition |
| **HOLD_BASELINE** | AGGRESSIVE_UNDERCUT | 99.1% | 0.9% | Rivals offer 40% discount |
| **PRICE_INCREASE** | PASSIVE_HOLD (Naive) | 113.3% | 1.5% | Naive static assumption |
| **PRICE_INCREASE** | AGGRESSIVE_UNDERCUT | 109.4% | 4.9% | Retaliatory migration buyout |
| **DEFENSIVE_DISCOUNT** | FEATURE_MATCH_BUNDLE | 89.6% | 0.5% | Margin compression |
| **WHITE_GLOVE_EXPANSION** | TARGETED_ACCOUNT_POACH | 104.3% | 0.7% | Minimax Nash Equilibrium |

---

## 3. Nash & Minimax Equilibrium Solver

The solver evaluates the payoff matrix to determine whether a pure Nash equilibrium exists where neither player can unilaterally improve their payoff. When pure equilibria are absent, it calculates the **Minimax-Robust Equilibrium**, identifying the strategy that maximizes portfolio enterprise value against the rival's worst-case counter-move.

### Exposing Naive Model Blindspots
Financial planning models frequently forecast that a +15% price hike delivers pure expansion with 0.5% baseline churn. The Game-Theoretic Simulator exposes that rational rivals counter with aggressive migration subsidies, driving churn to 4.9% and leaving hundreds of thousands of dollars in unmodeled at-risk revenue.

---

## 4. REST API Endpoints

- `GET /api/gametheory/competitors`: Lists competitor profiles and behavioral archetypes (Price Disruptor, Suite Bundler, Cloud Challenger).
- `GET /api/gametheory/vulnerability?id=CUS-020`: Detailed CVI analysis, renewal proximity, threat competitor, and defensive playbook.
- `GET /api/gametheory/equilibrium`: Full portfolio equilibrium report comparing naive static projections vs game-theoretic reality.
- `POST /api/gametheory/simulate`: Evaluates strategic payoff scenarios across custom market conditions.
