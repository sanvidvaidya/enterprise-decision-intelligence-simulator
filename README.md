# Enterprise Decision Simulator

Hi, I am Sanvid and I built this renewal decision system for subscription software businesses. It pulls together data from CRMs, contracts, product usage logs, and customer support desks to answer three practical questions:

1. Which enterprise accounts are most likely to cancel their contracts?
2. What specific facts in the data prove they are at risk?
3. What should the customer success team do right now to protect the revenue?

Every score in this app comes from clear, documented formulas. You can click on any number and trace it straight back to the original database row that generated it. There is no guessing and no black-box machine learning model making up numbers.

---

## The Simple Explanation: What This Is and How I Built It

If you run a subscription software company with 100 enterprise customers, your revenue depends on those customers renewing their contracts every year. When a customer leaves, it is called churn. Churn destroys company value faster than almost anything else in business.

Most companies handle renewal risk in one of two flawed ways:
- They ask the account managers. Account managers are naturally optimistic and often report that a client is happy right up until the client cancels.
- They buy a predictive AI tool. The tool shows a dashboard with an alert saying an account has an "82% churn probability." But when the sales director asks why the score is 82% and what specific action will save the account, the tool cannot explain itself. It is finding correlations in the data, not real causes.

### How I built this system to fix that
I wanted a system that works like an aircraft flight simulator for business decisions:

1. **Four real data streams:** The app loads accounts from the CRM, legal contract dates and values, daily product usage numbers (like how many employees actually logged in this month), and open support tickets.
2. **Transparent scoring rules:** Instead of a neural network, the app uses clear business logic. For example: if a customer has an active contract expiring in under 60 days, their daily user logins dropped by more than 30%, and they have two unresolved high-priority bugs, their risk points go up. You can see the math for every single point.
3. **A what-if testing lab:** Before spending time or money, team leads can test interventions in a sandbox. You can simulate what happens to an account risk score if engineering resolves their open tickets this week and the customer agrees to a contract extension.
4. **Causal reasoning:** People often confuse correlation with cause. For example, customers who cancel often submit fewer support tickets simply because they stopped caring, not because having fewer tickets is good. I added a 9-node Causal Graph based on Judea Pearl's do-calculus. It mathematically checks whether a drop in usage actually caused the risk, or if both were caused by an outside event like a company leadership change.
5. **A game room for competitor reactions:** When you offer a customer a discount or extra services, competitors often react with their own counter-offers. The app uses game theory (Nash equilibrium and Minimax math) to help calculate what competitors are likely to do next.

---

## The Business Problem: Why This Matters to a Company

In enterprise software, Net Revenue Retention (NRR) is the single biggest factor that determines what a company is worth to investors. If a company with $50 million in annual subscription revenue loses just 5% more customers each year to preventable churn, it loses millions in recurring cash flow and tens of millions in enterprise valuation.

Here is why this tool solves real operational problems:
- **Staff hours and budgets are limited:** An account team cannot give VIP treatment to every single customer. The simulator includes a Capacity-Aware Planner. You tell it how many hours your team has this week, how many technical escalation slots are open, and what budget you have. It mathematically selects the exact group of accounts to help so you protect the maximum amount of contract revenue.
- **Rules need governance:** You cannot let individual employees quietly change risk formulas to make their accounts look better. The app includes a Policy Studio with maker-checker controls. One person proposes a rule change, the app shows how many millions of dollars across the customer portfolio will shift risk categories, and a second authorized person has to review and approve the change before it goes live.
- **Teams need to replay history:** When an account cancels unexpectedly, executives want a post-mortem. The app includes event time-travel. You can rewind the database to any date in the past, see what the numbers were on that exact day without any hindsight bias, and test what would have happened if the team had stepped in earlier.

---

## What We Added in the Latest Version

Here are the main capabilities in this release:

- **Causal Graph and Root-Cause Modeling:** A 9-node structural causal model that separates direct causes from indirect effects using Pearl's do-calculus, so teams do not waste budget on surface symptoms.
- **Event-Stream Time Travel:** An immutable event engine that reconstructs historical account health at any past date and lets you run counterfactual tests.
- **Live Event Stream and Dispatch Webhooks:** REST endpoints (`/api/stream/usage` and `/api/stream/ticket`) that take live telemetry events from your product and automatically trigger account actions.
- **Competitor Counter-Move Simulation:** Minimax and Nash equilibrium calculations that evaluate account vulnerability to aggressive rival discounts and feature poaching.
- **Governed Policy Studio:** Versioned business rules with dual-party approval workflows to keep risk policies auditable.
- **Capacity-Aware Planner:** A knapsack-style resource optimizer that allocates constrained team hours, budget, and engineering escalations to save the most revenue.

---

## Quick Start

The app requires Python 3.11 or newer and Git.

```bash
git clone https://github.com/sanvidvaidya/enterprise-decision-intelligence-simulator.git
cd enterprise-decision-intelligence-simulator
python -m venv .venv
```

Activate the environment:

On macOS or Linux:
```bash
source .venv/bin/activate
```

On Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies and launch the public demo:
```bash
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Run the automated tests:
```bash
pytest
```

---

## Deployment Modes

The repository has two modes built into the code:
- **Public Demo (Default):** Runs with an isolated synthetic dataset. Uploads and disk saves are disabled so it can safely run on public showcase servers like Streamlit Community Cloud.
- **Private Business Mode:** Set the environment variable `EDS_DEPLOYMENT_MODE="private_business"`. This unlocks the five-file CSV customer data onboarding workflow, persistent SQLite storage, and the policy governance studio.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
