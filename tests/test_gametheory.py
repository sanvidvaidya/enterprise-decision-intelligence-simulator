"""Tests for Game-Theoretic Competitor Counter-Moves & Market Equilibrium."""

from datetime import date
from pathlib import Path
import io
import json
import sys

import pytest

from decision_intelligence.gametheory import (
    GameTheoreticSimulator,
    DEFAULT_COMPETITORS,
    VendorStrategy,
    CompetitorCounterMove,
)
from tests.test_causal_and_replay import execute_api_call


def test_cvi_calculation_boundaries():
    """Verify CVI calculation produces bounded, monotonic risk metrics."""
    sim = GameTheoreticSimulator()

    # Low risk account: healthy, 250 days out, 0 tickets, full utilization
    cvi_low, tier_low, prob_low = sim.calculate_cvi(
        health_score=95.0,
        days_to_renewal=250,
        open_critical_tickets=0,
        seat_utilization=0.95,
        acv=25000.0,
    )
    assert cvi_low < 30.0
    assert tier_low in ("LOW", "MEDIUM")
    assert prob_low < 0.25

    # Critical risk account: unhealthy, 20 days out, 2 critical tickets, low adoption, high ACV
    cvi_crit, tier_crit, prob_crit = sim.calculate_cvi(
        health_score=25.0,
        days_to_renewal=20,
        open_critical_tickets=2,
        seat_utilization=0.40,
        acv=150000.0,
    )
    assert cvi_crit >= 75.0
    assert tier_crit == "CRITICAL"
    assert prob_crit >= 0.85


def test_customer_vulnerability_assessment():
    """Verify customer vulnerability assessment for known customer CUS-020."""
    sim = GameTheoreticSimulator()
    vuln = sim.assess_customer_vulnerability("CUS-020", as_of_date=date(2026, 8, 1))
    assert vuln is not None
    assert vuln.customer_id == "CUS-020"
    assert vuln.acv > 0
    assert vuln.vulnerability_tier in ("CRITICAL", "HIGH", "MEDIUM")
    assert vuln.primary_threat_competitor in [c.name for c in DEFAULT_COMPETITORS]
    assert len(vuln.recommended_defense) > 10


def test_payoff_matrix_generation():
    """Payoff matrix must cover all 16 strategy-countermove pairs."""
    sim = GameTheoreticSimulator()
    payoffs = sim.evaluate_payoff_matrix(baseline_acv=1_000_000.0, vulnerable_acv=300_000.0, avg_cvi=55.0)
    assert len(payoffs) == 16  # 4 vendor strategies * 4 competitor counter-moves

    # Price increase facing aggressive undercut must suffer higher churn than baseline
    pi_undercut = next(
        p for p in payoffs
        if p.vendor_strategy == VendorStrategy.PRICE_INCREASE
        and p.competitor_counter_move == CompetitorCounterMove.AGGRESSIVE_UNDERCUT
    )
    hold_passive = next(
        p for p in payoffs
        if p.vendor_strategy == VendorStrategy.HOLD_BASELINE
        and p.competitor_counter_move == CompetitorCounterMove.PASSIVE_HOLD
    )
    assert pi_undercut.projected_gross_churn_pct > hold_passive.projected_gross_churn_pct


def test_nash_equilibrium_solution():
    """Nash equilibrium solver must return a stable strategic response."""
    sim = GameTheoreticSimulator()
    payoffs = sim.evaluate_payoff_matrix(baseline_acv=1_000_000.0, vulnerable_acv=350_000.0, avg_cvi=60.0)
    nash = sim.solve_nash_equilibrium(payoffs)

    assert "optimal_vendor_strategy" in nash
    assert "expected_competitor_counter_move" in nash
    assert nash["projected_nrr_pct"] > 0
    assert "strategic_rationale" in nash


def test_portfolio_simulation_naive_vs_game_theoretic_gap():
    """Verify portfolio simulation exposes unmodeled competitor churn gap."""
    sim = GameTheoreticSimulator()
    result = sim.run_portfolio_simulation(as_of_date=date(2026, 8, 1))

    assert result.assessed_accounts_count == 30
    assert result.total_pipeline_acv > 0
    assert sum(result.cvi_distribution.values()) == 30

    comp = result.naive_vs_game_theoretic_comparison
    # Naive model assumes zero competitor counter moves
    assert comp["naive_static_nrr_pct"] > comp["game_theoretic_equilibrium_nrr_pct"]
    assert comp["unmodeled_competitor_churn_gap_pct"] > 0
    assert comp["blindspot_revenue_at_risk"] > 0
    assert len(result.high_risk_poaching_targets) > 0


def test_api_gametheory_competitors_endpoint():
    status, payload = execute_api_call("GET", "/api/gametheory/competitors")
    assert status == 200
    assert payload["competitors_count"] == 3
    assert len(payload["competitors"]) == 3


def test_api_gametheory_vulnerability_endpoint():
    status, payload = execute_api_call("GET", "/api/gametheory/vulnerability?id=CUS-020")
    assert status == 200
    assert payload["customer_id"] == "CUS-020"
    assert "cvi_score" in payload
    assert "poaching_probability" in payload


def test_api_gametheory_equilibrium_endpoint():
    status, payload = execute_api_call("GET", "/api/gametheory/equilibrium")
    assert status == 200
    assert payload["assessed_accounts_count"] == 30
    assert "nash_equilibrium" in payload
    assert "naive_vs_game_theoretic_comparison" in payload


def test_api_gametheory_simulate_endpoint():
    status, payload = execute_api_call("POST", "/api/gametheory/simulate", {"strategy": "PRICE_INCREASE"})
    assert status == 200
    assert "payoff_matrix" in payload
    assert len(payload["payoff_matrix"]) == 16
