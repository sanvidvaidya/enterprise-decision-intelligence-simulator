"""
Game-Theoretic Competitor Counter-Moves & Dynamic Market Equilibrium Engine.

Models strategic interactions between the SaaS vendor and rival competitors
during renewal, pricing, and retention maneuvers. Replaces naive static
projections with Nash/Stackelberg equilibrium payoff matrices and account-level
Competitive Vulnerability Index (CVI) scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple

from decision_intelligence.database import connect


class VendorStrategy(str, Enum):
    HOLD_BASELINE = "HOLD_BASELINE"
    PRICE_INCREASE = "PRICE_INCREASE"
    DEFENSIVE_DISCOUNT = "DEFENSIVE_DISCOUNT"
    WHITE_GLOVE_EXPANSION = "WHITE_GLOVE_EXPANSION"


class CompetitorCounterMove(str, Enum):
    PASSIVE_HOLD = "PASSIVE_HOLD"
    AGGRESSIVE_UNDERCUT = "AGGRESSIVE_UNDERCUT"
    FEATURE_MATCH_BUNDLE = "FEATURE_MATCH_BUNDLE"
    TARGETED_ACCOUNT_POACH = "TARGETED_ACCOUNT_POACH"


@dataclass(frozen=True)
class CompetitorProfile:
    competitor_id: str
    name: str
    archetype: str  # Price Disruptor, Enterprise Suite Bundler, Open Challenger
    aggressiveness: float  # 0.0 to 1.0
    migration_subsidy_pct: float  # e.g., 0.35 (offers 35% buyout credit)
    target_acv_tier: str  # Enterprise, Mid-Market, SMB, All
    poaching_effectiveness: float  # Multiplier on vulnerable accounts (0.5 to 1.5)


DEFAULT_COMPETITORS: List[CompetitorProfile] = [
    CompetitorProfile(
        competitor_id="COMP-APEX",
        name="ApexCloud Platform",
        archetype="Aggressive Price Disruptor",
        aggressiveness=0.85,
        migration_subsidy_pct=0.40,
        target_acv_tier="All",
        poaching_effectiveness=1.35,
    ),
    CompetitorProfile(
        competitor_id="COMP-NEXUS",
        name="Nexus Enterprise Suite",
        archetype="Enterprise Suite Bundler",
        aggressiveness=0.65,
        migration_subsidy_pct=0.25,
        target_acv_tier="Enterprise",
        poaching_effectiveness=1.10,
    ),
    CompetitorProfile(
        competitor_id="COMP-VANGUARD",
        name="Vanguard Next-Gen",
        archetype="Modern Cloud Challenger",
        aggressiveness=0.75,
        migration_subsidy_pct=0.30,
        target_acv_tier="Mid-Market",
        poaching_effectiveness=1.20,
    ),
]


@dataclass
class AccountVulnerability:
    customer_id: str
    customer_name: str
    acv: float
    segment: str
    health_score: float
    days_to_renewal: int
    open_critical_tickets: int
    seat_utilization: float
    cvi_score: float  # 0 - 100
    vulnerability_tier: str  # CRITICAL, HIGH, MEDIUM, LOW
    primary_threat_competitor: str
    poaching_probability: float  # 0.0 - 1.0
    recommended_defense: str


@dataclass
class StrategyPayoff:
    vendor_strategy: VendorStrategy
    competitor_counter_move: CompetitorCounterMove
    projected_nrr_pct: float
    projected_gross_churn_pct: float
    retained_acv: float
    lost_acv_to_competitors: float
    vendor_payoff_score: float
    competitor_payoff_score: float


@dataclass
class EquilibriumResult:
    as_of_date: str
    assessed_accounts_count: int
    total_pipeline_acv: float
    cvi_distribution: Dict[str, int]
    payoff_matrix: List[Dict[str, Any]]
    nash_equilibrium: Dict[str, Any]
    naive_vs_game_theoretic_comparison: Dict[str, Any]
    high_risk_poaching_targets: List[Dict[str, Any]]


class GameTheoreticSimulator:
    """Calculates competitive vulnerabilities, simulates counter-moves, and solves Nash equilibria."""

    def __init__(self, competitors: Optional[List[CompetitorProfile]] = None, database_path: Optional[str] = None):
        self.competitors = competitors if competitors is not None else DEFAULT_COMPETITORS
        self.database_path = database_path

    def calculate_cvi(
        self,
        health_score: float,
        days_to_renewal: int,
        open_critical_tickets: int,
        seat_utilization: float,
        acv: float,
    ) -> Tuple[float, str, float]:
        """
        Compute Competitive Vulnerability Index (CVI) from 0 to 100.
        Higher CVI indicates an account primed for competitor poaching.
        """
        # 1. Renewal proximity component (max 30 pts)
        if days_to_renewal <= 30:
            renewal_pts = 30.0
        elif days_to_renewal <= 90:
            renewal_pts = 20.0
        elif days_to_renewal <= 180:
            renewal_pts = 10.0
        else:
            renewal_pts = 3.0

        # 2. Health & Dissatisfaction component (max 35 pts)
        # Health score 0-100 (where 100 is healthy)
        dissatisfaction = max(0.0, 100.0 - health_score)
        health_pts = (dissatisfaction / 100.0) * 35.0

        # 3. Operational friction component: tickets & low adoption (max 25 pts)
        ticket_pts = min(15.0, open_critical_tickets * 7.5)
        util_pts = max(0.0, (0.70 - seat_utilization) * 20.0) if seat_utilization < 0.70 else 0.0
        friction_pts = min(25.0, ticket_pts + util_pts)

        # 4. Target attractiveness: higher ACV attracts greater poaching effort (max 10 pts)
        acv_pts = min(10.0, (acv / 100000.0) * 10.0)

        cvi = min(100.0, max(0.0, renewal_pts + health_pts + friction_pts + acv_pts))

        if cvi >= 75.0:
            tier = "CRITICAL"
        elif cvi >= 50.0:
            tier = "HIGH"
        elif cvi >= 25.0:
            tier = "MEDIUM"
        else:
            tier = "LOW"

        # Baseline probability of competitor swooping in with buyout subsidy
        poaching_prob = round(1.0 / (1.0 + math.exp(-((cvi - 50.0) / 12.0))), 3)
        return round(cvi, 1), tier, poaching_prob

    def assess_customer_vulnerability(
        self, customer_id: str, as_of_date: Optional[date] = None
    ) -> Optional[AccountVulnerability]:
        """Assess a single customer's vulnerability to competitor poaching."""
        ref_date = as_of_date or date(2026, 8, 1)

        conn_kwargs = {"database_path": self.database_path} if self.database_path else {}
        with connect(**conn_kwargs) as conn:
            row = conn.execute(
                """
                SELECT c.customer_id, c.customer_name, c.segment, ct.annual_contract_value,
                       ct.renewal_date, ct.auto_renew
                FROM customers c
                JOIN contracts ct ON c.customer_id = ct.customer_id
                WHERE c.customer_id = ?
                """,
                (customer_id,),
            ).fetchone()

            if not row:
                return None

            acv = float(row["annual_contract_value"])
            end_date_str = str(row["renewal_date"])
            try:
                end_d = date.fromisoformat(end_date_str)
                days_to_renewal = max(0, (end_d - ref_date).days)
            except Exception:
                days_to_renewal = 90

            # Usage & health factors
            usage_row = conn.execute(
                """
                SELECT active_users, seats_purchased, feature_adoption_pct
                FROM product_usage_events
                WHERE customer_id = ? AND event_date <= ?
                ORDER BY event_date DESC LIMIT 1
                """,
                (customer_id, ref_date.isoformat()),
            ).fetchone()

            seat_util = 0.85
            health_score = 75.0
            if usage_row:
                seats = usage_row["seats_purchased"] or 1
                active = usage_row["active_users"] or 0
                seat_util = min(1.0, active / float(seats))
                adoption = usage_row["feature_adoption_pct"] or 50.0
                health_score = (seat_util * 50.0) + (adoption * 0.5)

            # Ticket counts
            ticket_row = conn.execute(
                """
                SELECT COUNT(*) as crit_count
                FROM support_tickets
                WHERE customer_id = ? AND priority = 'Critical' AND ticket_status = 'Open'
                """,
                (customer_id,),
            ).fetchone()
            crit_tickets = ticket_row["crit_count"] if ticket_row else 0

            # Check latest assessment risk score if exists
            assess_row = conn.execute(
                """
                SELECT risk_score FROM risk_assessments
                WHERE customer_id = ? AND as_of_date <= ?
                ORDER BY as_of_date DESC LIMIT 1
                """,
                (customer_id, ref_date.isoformat()),
            ).fetchone()
            if assess_row:
                # Invert risk score (100 is max risk -> 0 health)
                health_score = max(5.0, 100.0 - float(assess_row["risk_score"]))

        cvi, tier, poach_prob = self.calculate_cvi(
            health_score=health_score,
            days_to_renewal=days_to_renewal,
            open_critical_tickets=crit_tickets,
            seat_utilization=seat_util,
            acv=acv,
        )

        # Match primary threat competitor
        if acv > 100000:
            threat_comp = self.competitors[1].name  # Nexus Suite
        else:
            threat_comp = self.competitors[0].name  # ApexCloud

        # Recommend defensive playbook
        if tier == "CRITICAL":
            recom = "Immediate executive sponsor intervention + proactive multi-year price lock with migration parity clause"
        elif tier == "HIGH":
            recom = "Dedicated technical TAM dispatch to resolve open tickets and execute CS adoption review"
        elif tier == "MEDIUM":
            recom = "Standard automated renewal sequence with early-bird renewal incentive"
        else:
            recom = "Account is stable; identify expansion cross-sell opportunities"

        return AccountVulnerability(
            customer_id=customer_id,
            customer_name=row["customer_name"],
            acv=acv,
            segment=row["segment"],
            health_score=round(health_score, 1),
            days_to_renewal=days_to_renewal,
            open_critical_tickets=crit_tickets,
            seat_utilization=round(seat_util, 2),
            cvi_score=cvi,
            vulnerability_tier=tier,
            primary_threat_competitor=threat_comp,
            poaching_probability=poach_prob,
            recommended_defense=recom,
        )

    def evaluate_payoff_matrix(
        self, baseline_acv: float, vulnerable_acv: float, avg_cvi: float
    ) -> List[StrategyPayoff]:
        """
        Evaluate full 4x4 strategic interaction payoff matrix:
        (Vendor Strategies x Competitor Counter-Moves).
        """
        payoffs: List[StrategyPayoff] = []

        # Parameters
        vuln_ratio = min(1.0, vulnerable_acv / max(1.0, baseline_acv))

        for v_strat in VendorStrategy:
            for c_move in CompetitorCounterMove:
                # Base parameters
                base_retention = 0.92
                price_multiplier = 1.0

                if v_strat == VendorStrategy.HOLD_BASELINE:
                    price_multiplier = 1.0
                    loss_prob = 0.08
                elif v_strat == VendorStrategy.PRICE_INCREASE:
                    price_multiplier = 1.15  # +15% expansion
                    # Higher vulnerability to poaching if price raised
                    loss_prob = 0.14 + (avg_cvi / 250.0)
                elif v_strat == VendorStrategy.DEFENSIVE_DISCOUNT:
                    price_multiplier = 0.90  # -10% discount
                    loss_prob = 0.04
                elif v_strat == VendorStrategy.WHITE_GLOVE_EXPANSION:
                    price_multiplier = 1.05
                    loss_prob = 0.05

                # Competitor reaction effect
                if c_move == CompetitorCounterMove.PASSIVE_HOLD:
                    poached_acv_factor = 0.20
                    competitor_cost = 0.0
                elif c_move == CompetitorCounterMove.AGGRESSIVE_UNDERCUT:
                    # Competitor offers 40% subsidy
                    poached_acv_factor = 0.65 if v_strat == VendorStrategy.PRICE_INCREASE else 0.40
                    competitor_cost = 0.15
                elif c_move == CompetitorCounterMove.FEATURE_MATCH_BUNDLE:
                    poached_acv_factor = 0.45
                    competitor_cost = 0.10
                elif c_move == CompetitorCounterMove.TARGETED_ACCOUNT_POACH:
                    # Poachers laser focus on vulnerable accounts
                    poached_acv_factor = 0.80 if avg_cvi > 50 else 0.50
                    competitor_cost = 0.12

                # Calculate outcomes
                actual_lost_acv = vulnerable_acv * loss_prob * poached_acv_factor
                retained_acv = max(0.0, baseline_acv - actual_lost_acv)
                realized_acv = retained_acv * price_multiplier

                nrr = round((realized_acv / max(1.0, baseline_acv)) * 100.0, 1)
                churn_pct = round((actual_lost_acv / max(1.0, baseline_acv)) * 100.0, 1)

                # Payoff utilities
                vendor_utility = (realized_acv / baseline_acv) * 100.0 - (churn_pct * 1.5)
                comp_utility = (actual_lost_acv / baseline_acv) * 100.0 - competitor_cost

                payoffs.append(
                    StrategyPayoff(
                        vendor_strategy=v_strat,
                        competitor_counter_move=c_move,
                        projected_nrr_pct=nrr,
                        projected_gross_churn_pct=churn_pct,
                        retained_acv=round(retained_acv, 2),
                        lost_acv_to_competitors=round(actual_lost_acv, 2),
                        vendor_payoff_score=round(vendor_utility, 2),
                        competitor_payoff_score=round(comp_utility, 2),
                    )
                )

        return payoffs

    def solve_nash_equilibrium(self, payoffs: List[StrategyPayoff]) -> Dict[str, Any]:
        """
        Identify Pure or Minimax Nash Equilibrium from the strategic matrix.
        """
        # Group by vendor strategy to find best response for each player
        vendor_strats = list(VendorStrategy)
        comp_moves = list(CompetitorCounterMove)

        # Build matrix lookup
        payoff_lookup: Dict[Tuple[VendorStrategy, CompetitorCounterMove], StrategyPayoff] = {
            (p.vendor_strategy, p.competitor_counter_move): p for p in payoffs
        }

        # Find competitor best response to each vendor strategy (max comp_utility)
        comp_best_responses: Dict[VendorStrategy, CompetitorCounterMove] = {}
        for vs in vendor_strats:
            best_cm = max(comp_moves, key=lambda cm: payoff_lookup[(vs, cm)].competitor_payoff_score)
            comp_best_responses[vs] = best_cm

        # Find vendor best response to each competitor counter move (max vendor_utility)
        vendor_best_responses: Dict[CompetitorCounterMove, VendorStrategy] = {}
        for cm in comp_moves:
            best_vs = max(vendor_strats, key=lambda vs: payoff_lookup[(vs, cm)].vendor_payoff_score)
            vendor_best_responses[cm] = best_vs

        # Check for pure Nash equilibrium: (vs*, cm*) where vs* is BR to cm* AND cm* is BR to vs*
        pure_nash = None
        for vs in vendor_strats:
            cm = comp_best_responses[vs]
            if vendor_best_responses[cm] == vs:
                pure_nash = payoff_lookup[(vs, cm)]
                break

        # If no pure equilibrium, take Minimax robust strategy
        if not pure_nash:
            # Vendor minimizes worst-case loss across competitor moves
            worst_cases = {}
            for vs in vendor_strats:
                worst_case = min(payoff_lookup[(vs, cm)].vendor_payoff_score for cm in comp_moves)
                worst_cases[vs] = worst_case
            optimal_vs = max(worst_cases, key=worst_cases.get)
            expected_cm = comp_best_responses[optimal_vs]
            pure_nash = payoff_lookup[(optimal_vs, expected_cm)]
            eq_type = "Minimax-Robust Equilibrium"
        else:
            eq_type = "Strict Pure Nash Equilibrium"

        return {
            "equilibrium_type": eq_type,
            "optimal_vendor_strategy": pure_nash.vendor_strategy.value,
            "expected_competitor_counter_move": pure_nash.competitor_counter_move.value,
            "projected_nrr_pct": pure_nash.projected_nrr_pct,
            "projected_gross_churn_pct": pure_nash.projected_gross_churn_pct,
            "expected_lost_acv": pure_nash.lost_acv_to_competitors,
            "strategic_rationale": (
                f"When the vendor chooses '{pure_nash.vendor_strategy.value}', rational competitors respond with "
                f"'{pure_nash.competitor_counter_move.value}'. Any unilateral deviation reduces expected portfolio EV."
            ),
        }

    def run_portfolio_simulation(self, as_of_date: Optional[date] = None) -> EquilibriumResult:
        """Run complete game-theoretic market simulation across all portfolio accounts."""
        ref_date = as_of_date or date(2026, 8, 1)

        conn_kwargs = {"database_path": self.database_path} if self.database_path else {}
        with connect(**conn_kwargs) as conn:
            rows = conn.execute("SELECT customer_id FROM customers").fetchall()
            customer_ids = [r["customer_id"] for r in rows]

        vulnerabilities: List[AccountVulnerability] = []
        for cid in customer_ids:
            vuln = self.assess_customer_vulnerability(cid, ref_date)
            if vuln:
                vulnerabilities.append(vuln)

        total_acv = sum(v.acv for v in vulnerabilities)
        vulnerable_accounts = [v for v in vulnerabilities if v.vulnerability_tier in ("CRITICAL", "HIGH")]
        vulnerable_acv = sum(v.acv for v in vulnerable_accounts)
        avg_cvi = sum(v.cvi_score for v in vulnerabilities) / max(1, len(vulnerabilities))

        cvi_dist = {
            "CRITICAL": sum(1 for v in vulnerabilities if v.vulnerability_tier == "CRITICAL"),
            "HIGH": sum(1 for v in vulnerabilities if v.vulnerability_tier == "HIGH"),
            "MEDIUM": sum(1 for v in vulnerabilities if v.vulnerability_tier == "MEDIUM"),
            "LOW": sum(1 for v in vulnerabilities if v.vulnerability_tier == "LOW"),
        }

        # Calculate strategic payoffs
        payoffs = self.evaluate_payoff_matrix(total_acv, vulnerable_acv, avg_cvi)
        nash = self.solve_nash_equilibrium(payoffs)

        # Naive static projection vs game-theoretic reality
        # Naive model: assumes Price Increase generates pure +15% expansion with zero competitor reaction (0.5% base churn)
        naive_nrr = 115.0
        naive_churn = 0.5
        naive_acv = total_acv * 1.15

        # Find price hike scenario under competitor aggressive undercut
        price_hike_undercut = next(
            p for p in payoffs
            if p.vendor_strategy == VendorStrategy.PRICE_INCREASE
            and p.competitor_counter_move == CompetitorCounterMove.AGGRESSIVE_UNDERCUT
        )

        actual_eq_nrr = nash["projected_nrr_pct"]
        actual_eq_churn = nash["projected_gross_churn_pct"]
        unmodeled_churn_gap = round(price_hike_undercut.projected_gross_churn_pct - naive_churn, 1)
        overestimated_revenue = round(naive_acv - (total_acv * (actual_eq_nrr / 100.0)), 2)

        comparison = {
            "naive_static_nrr_pct": naive_nrr,
            "naive_assumed_churn_pct": naive_churn,
            "price_increase_retaliation_churn_pct": price_hike_undercut.projected_gross_churn_pct,
            "game_theoretic_equilibrium_nrr_pct": actual_eq_nrr,
            "game_theoretic_equilibrium_churn_pct": actual_eq_churn,
            "unmodeled_competitor_churn_gap_pct": unmodeled_churn_gap,
            "blindspot_revenue_at_risk": overestimated_revenue,
            "critical_insight": (
                "Static planning assumes zero rival reaction to pricing moves. "
                "If prices are hiked unilaterally, rival migration subsidies spike churn to "
                f"{price_hike_undercut.projected_gross_churn_pct}%, creating a {unmodeled_churn_gap}% blindspot. "
                f"The minimax Nash equilibrium identifies '{nash['optimal_vendor_strategy']}' as the dominant defense."
            ),
        }

        # High risk targets sorted by CVI
        high_risk_sorted = sorted(vulnerable_accounts, key=lambda v: v.cvi_score, reverse=True)[:5]
        targets_export = [
            {
                "customer_id": t.customer_id,
                "customer_name": t.customer_name,
                "acv": t.acv,
                "cvi_score": t.cvi_score,
                "vulnerability_tier": t.vulnerability_tier,
                "days_to_renewal": t.days_to_renewal,
                "open_critical_tickets": t.open_critical_tickets,
                "primary_threat_competitor": t.primary_threat_competitor,
                "poaching_probability": t.poaching_probability,
                "recommended_defense": t.recommended_defense,
            }
            for t in high_risk_sorted
        ]

        return EquilibriumResult(
            as_of_date=ref_date.isoformat(),
            assessed_accounts_count=len(vulnerabilities),
            total_pipeline_acv=round(total_acv, 2),
            cvi_distribution=cvi_dist,
            payoff_matrix=[
                {
                    "vendor_strategy": p.vendor_strategy.value,
                    "competitor_counter_move": p.competitor_counter_move.value,
                    "projected_nrr_pct": p.projected_nrr_pct,
                    "projected_gross_churn_pct": p.projected_gross_churn_pct,
                    "retained_acv": p.retained_acv,
                    "lost_acv_to_competitors": p.lost_acv_to_competitors,
                    "vendor_payoff_score": p.vendor_payoff_score,
                    "competitor_payoff_score": p.competitor_payoff_score,
                }
                for p in payoffs
            ],
            nash_equilibrium=nash,
            naive_vs_game_theoretic_comparison=comparison,
            high_risk_poaching_targets=targets_export,
        )
