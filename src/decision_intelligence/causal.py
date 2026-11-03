"""Deterministic Structural Causal Model (SCM) and Causal DAG analysis.

Provides DAG topological reasoning, Pearl do-operator graph surgery,
counterfactual abduction-action-prediction inference, mediation analysis
(total, direct, and indirect effects), and root-cause risk decomposition.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import math
from pathlib import Path
from typing import Any

from decision_intelligence.database import DEFAULT_DATABASE_PATH, connect
from decision_intelligence.policy import DEFAULT_POLICY, get_active_policy


@dataclass(frozen=True)
class CausalNode:
    """A governed variable in the renewal-risk causal network."""

    node_id: str
    name: str
    category: str
    description: str
    min_value: float
    max_value: float
    baseline_default: float
    is_intervention_target: bool


@dataclass(frozen=True)
class CausalEdge:
    """Directed causal link representing structural dependence and mechanism."""

    source: str
    target: str
    direct_weight: float
    mechanism: str
    latency_days: int = 0


@dataclass(frozen=True)
class CausalEffectDecomposition:
    """Mediation breakdown into total, direct, and indirect causal effects."""

    intervention_node: str
    intervention_value: float
    baseline_value: float
    target_node: str
    total_effect: float
    direct_effect: float
    indirect_effect: float
    mediators: list[str]
    mechanism_summary: str


@dataclass(frozen=True)
class RootCauseAttribution:
    """Quantified root driver explaining score elevation above healthy baseline."""

    node_id: str
    node_name: str
    observed_value: float
    healthy_baseline: float
    causal_points: float
    percentage_of_risk: float
    explanation: str


class CausalDAG:
    """Directed Acyclic Graph governing enterprise SaaS renewal dynamics."""

    def __init__(self) -> None:
        self.nodes: dict[str, CausalNode] = {}
        self.edges: list[CausalEdge] = []
        self._build_canonical_graph()

    def _build_canonical_graph(self) -> None:
        node_defs = [
            CausalNode(
                "critical_tickets",
                "Unresolved Critical Tickets",
                "operational",
                "Count of unresolved Sev-1 support tickets",
                0.0,
                10.0,
                0.0,
                True,
            ),
            CausalNode(
                "csat_score",
                "Customer Satisfaction (CSAT)",
                "operational",
                "Reported customer sentiment score from 1.0 (lowest) to 5.0 (highest)",
                1.0,
                5.0,
                4.5,
                False,
            ),
            CausalNode(
                "feature_adoption",
                "Feature Adoption Rate",
                "product",
                "Percentage of licensed enterprise capabilities actively adopted",
                0.0,
                100.0,
                75.0,
                True,
            ),
            CausalNode(
                "seat_utilization",
                "Seat Utilization Rate",
                "product",
                "Ratio of active monthly users to total purchased seats (0.0 to 1.0)",
                0.0,
                1.0,
                0.85,
                True,
            ),
            CausalNode(
                "active_user_decline",
                "Active User Decline Rate",
                "product",
                "Month-over-month contraction in active users (positive indicates decline)",
                -0.5,
                1.0,
                0.0,
                False,
            ),
            CausalNode(
                "days_to_renewal",
                "Days Until Renewal",
                "commercial",
                "Calendar days remaining until contract expiration date",
                -180.0,
                365.0,
                180.0,
                True,
            ),
            CausalNode(
                "contract_acv",
                "Annual Contract Value",
                "commercial",
                "Annual contract revenue tier in dollars",
                5000.0,
                500000.0,
                30000.0,
                False,
            ),
            CausalNode(
                "executive_sponsor_engaged",
                "Executive Sponsor Engagement",
                "relationship",
                "Level of executive sponsorship and quarterly business review alignment (0.0 to 1.0)",
                0.0,
                1.0,
                0.8,
                True,
            ),
            CausalNode(
                "renewal_risk_score",
                "Renewal Risk Score",
                "outcome",
                "Deterministic enterprise renewal risk score between 0 and 100",
                0.0,
                100.0,
                10.0,
                False,
            ),
        ]
        for node in node_defs:
            self.nodes[node.node_id] = node

        edge_defs = [
            CausalEdge(
                "critical_tickets",
                "csat_score",
                -0.85,
                "Service outages and unresolved critical incidents erode user and executive satisfaction.",
                latency_days=3,
            ),
            CausalEdge(
                "critical_tickets",
                "renewal_risk_score",
                30.0,
                "Unresolved critical tickets directly trigger operational risk penalties in governance policy.",
                latency_days=0,
            ),
            CausalEdge(
                "critical_tickets",
                "active_user_decline",
                0.25,
                "Blocked workflows force operational teams to abandon product sessions.",
                latency_days=7,
            ),
            CausalEdge(
                "csat_score",
                "seat_utilization",
                0.12,
                "Satisfied user communities broaden regular seat engagement across departments.",
                latency_days=14,
            ),
            CausalEdge(
                "feature_adoption",
                "seat_utilization",
                0.006,
                "Deeper workflow embedding drives higher daily active seat utilization.",
                latency_days=14,
            ),
            CausalEdge(
                "feature_adoption",
                "active_user_decline",
                -0.003,
                "Sticky feature adoption buffers against team-level user abandonment.",
                latency_days=21,
            ),
            CausalEdge(
                "executive_sponsor_engaged",
                "csat_score",
                0.40,
                "Proactive executive governance stabilizes sentiment during operational friction.",
                latency_days=7,
            ),
            CausalEdge(
                "executive_sponsor_engaged",
                "seat_utilization",
                0.08,
                "Executive mandate encourages cross-functional software deployment.",
                latency_days=14,
            ),
            CausalEdge(
                "seat_utilization",
                "renewal_risk_score",
                -25.0,
                "Higher seat engagement eliminates low seat penetration risk penalties.",
                latency_days=0,
            ),
            CausalEdge(
                "active_user_decline",
                "renewal_risk_score",
                35.0,
                "Contraction in monthly active users triggers severe usage decline risk penalties.",
                latency_days=0,
            ),
            CausalEdge(
                "days_to_renewal",
                "renewal_risk_score",
                -0.12,
                "Proximity to renewal date compresses timeline for intervention and increases urgency.",
                latency_days=0,
            ),
            CausalEdge(
                "contract_acv",
                "renewal_risk_score",
                0.0001,
                "Higher revenue exposure carries enterprise governance points.",
                latency_days=0,
            ),
        ]
        self.edges = edge_defs
        self._validate_acyclic()

    def _validate_acyclic(self) -> None:
        visited: set[str] = set()
        stack: set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            stack.add(node_id)
            for edge in self.get_children(node_id):
                target = edge.target
                if target not in visited:
                    if dfs(target):
                        return True
                elif target in stack:
                    return True
            stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    raise ValueError(f"Cycle detected in causal graph at node {node_id}")

    def get_parents(self, node_id: str) -> list[CausalEdge]:
        return [edge for edge in self.edges if edge.target == node_id]

    def get_children(self, node_id: str) -> list[CausalEdge]:
        return [edge for edge in self.edges if edge.source == node_id]

    def topological_order(self) -> list[str]:
        in_degree = {node_id: 0 for node_id in self.nodes}
        for edge in self.edges:
            in_degree[edge.target] += 1
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        queue.sort()
        order: list[str] = []
        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for edge in self.get_children(curr):
                in_degree[edge.target] -= 1
                if in_degree[edge.target] == 0:
                    queue.append(edge.target)
            queue.sort()
        if len(order) != len(self.nodes):
            raise ValueError("Graph contains cycles, cannot topologically sort")
        return order

    def find_paths(self, source: str, target: str) -> list[list[str]]:
        paths: list[list[str]] = []

        def dfs(current: str, current_path: list[str]) -> None:
            if current == target:
                paths.append(list(current_path))
                return
            for edge in self.get_children(current):
                if edge.target not in current_path:
                    dfs(edge.target, current_path + [edge.target])

        dfs(source, [source])
        return paths

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [asdict(node) for node in self.nodes.values()],
            "edges": [asdict(edge) for edge in self.edges],
            "topological_order": self.topological_order(),
        }


class StructuralCausalModel:
    """Evaluates deterministic equations, do-interventions, and counterfactuals."""

    def __init__(self, dag: CausalDAG | None = None, policy: dict[str, float] | None = None) -> None:
        self.dag = dag or CausalDAG()
        self.policy = policy or DEFAULT_POLICY

    def _clip(self, node_id: str, value: float) -> float:
        node = self.dag.nodes[node_id]
        return max(node.min_value, min(node.max_value, value))

    def evaluate_node(
        self,
        node_id: str,
        state: dict[str, float],
        noise: dict[str, float] | None = None,
    ) -> float:
        u = 0.0 if noise is None else noise.get(node_id, 0.0)

        if node_id == "critical_tickets":
            return self._clip(node_id, state.get("critical_tickets", 0.0) + u)

        if node_id == "csat_score":
            crit = state.get("critical_tickets", 0.0)
            exec_touch = state.get("executive_sponsor_engaged", 0.8)
            val = 4.5 - (0.85 * crit) + (0.40 * (exec_touch - 0.5)) + u
            return self._clip(node_id, val)

        if node_id == "feature_adoption":
            return self._clip(node_id, state.get("feature_adoption", 70.0) + u)

        if node_id == "seat_utilization":
            csat = state.get("csat_score", 4.5)
            fa = state.get("feature_adoption", 70.0)
            exec_touch = state.get("executive_sponsor_engaged", 0.8)
            val = (
                0.20
                + (0.10 * (csat - 1.0) / 4.0)
                + (0.35 * (fa / 100.0))
                + (0.15 * exec_touch)
                + u
            )
            return self._clip(node_id, val)

        if node_id == "active_user_decline":
            crit = state.get("critical_tickets", 0.0)
            csat = state.get("csat_score", 4.5)
            fa = state.get("feature_adoption", 70.0)
            val = (
                (0.20 * crit)
                - (0.08 * (csat - 3.0))
                - (0.003 * (fa - 50.0))
                + u
            )
            return self._clip(node_id, val)

        if node_id in ("days_to_renewal", "contract_acv", "executive_sponsor_engaged"):
            return self._clip(node_id, state.get(node_id, self.dag.nodes[node_id].baseline_default) + u)

        if node_id == "renewal_risk_score":
            score = 0.0
            crit = state.get("critical_tickets", 0.0)
            if crit >= 1.0:
                score += self.policy.get("critical_support_points", 30.0)

            decline = state.get("active_user_decline", 0.0)
            if decline >= self.policy.get("usage_decline_high_threshold", 0.20):
                score += self.policy.get("usage_decline_high_points", 30.0)
            elif decline >= self.policy.get("usage_decline_moderate_threshold", 0.10):
                score += self.policy.get("usage_decline_moderate_points", 15.0)

            util = state.get("seat_utilization", 0.85)
            if util < self.policy.get("seat_engagement_low_threshold", 0.50):
                score += self.policy.get("seat_engagement_low_points", 15.0)
            elif util < self.policy.get("seat_engagement_medium_threshold", 0.70):
                score += self.policy.get("seat_engagement_medium_points", 10.0)

            days = state.get("days_to_renewal", 180.0)
            if days <= self.policy.get("renewal_near_days", 45.0):
                score += self.policy.get("renewal_near_points", 20.0)
            elif days <= self.policy.get("renewal_mid_days", 90.0):
                score += self.policy.get("renewal_mid_points", 15.0)
            elif days <= self.policy.get("renewal_far_days", 180.0):
                score += self.policy.get("renewal_far_points", 10.0)

            acv = state.get("contract_acv", 30000.0)
            if acv >= self.policy.get("high_acv_threshold", 50000.0):
                score += self.policy.get("high_acv_points", 5.0)
            elif acv >= self.policy.get("medium_acv_threshold", 25000.0):
                score += self.policy.get("medium_acv_points", 3.0)

            total = min(100.0, max(0.0, score + u))
            return self._clip(node_id, total)

        return self._clip(node_id, state.get(node_id, 0.0) + u)

    def simulate(
        self,
        base_state: dict[str, float],
        interventions: dict[str, float] | None = None,
        noise: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """Forward-propagate values along the causal graph under Pearl do-surgeries."""
        interventions = interventions or {}
        state = dict(base_state)
        topo_order = self.dag.topological_order()

        for node_id in topo_order:
            if node_id in interventions:
                state[node_id] = self._clip(node_id, interventions[node_id])
            else:
                parents = self.dag.get_parents(node_id)
                if not parents and node_id in base_state:
                    state[node_id] = self._clip(node_id, base_state[node_id])
                else:
                    state[node_id] = self.evaluate_node(node_id, state, noise)

        return state

    def abduce_noise(self, observed: dict[str, float]) -> dict[str, float]:
        """Infer exogenous background noise vectors matching observed reality."""
        noise: dict[str, float] = {}
        for node_id in self.dag.topological_order():
            parents = self.dag.get_parents(node_id)
            if not parents:
                noise[node_id] = 0.0
            else:
                expected = self.evaluate_node(node_id, observed, noise=None)
                obs_val = observed.get(node_id, expected)
                noise[node_id] = obs_val - expected
        return noise

    def counterfactual_query(
        self,
        observed: dict[str, float],
        interventions: dict[str, float],
    ) -> dict[str, Any]:
        """Pearl three-step counterfactual: Abduction -> Action -> Prediction."""
        noise = self.abduce_noise(observed)
        counterfactual_state = self.simulate(observed, interventions=interventions, noise=noise)

        deltas = {
            node_id: counterfactual_state[node_id] - observed.get(node_id, 0.0)
            for node_id in self.dag.nodes
        }
        baseline_score = observed.get("renewal_risk_score", 0.0)
        simulated_score = counterfactual_state.get("renewal_risk_score", 0.0)
        score_reduction = max(0.0, baseline_score - simulated_score)

        return {
            "observed": observed,
            "counterfactual": counterfactual_state,
            "deltas": deltas,
            "abduced_noise": noise,
            "score_reduction": score_reduction,
            "relative_reduction_pct": round(
                (score_reduction / max(1.0, baseline_score)) * 100.0, 1
            ),
        }

    def decompose_effects(
        self,
        observed: dict[str, float],
        intervention_node: str,
        intervention_val: float,
        target_node: str = "renewal_risk_score",
    ) -> CausalEffectDecomposition:
        """Decompose total effect into direct effect and mediator-propagated effects."""
        noise = self.abduce_noise(observed)
        base_target = observed.get(target_node, 0.0)

        # Total Effect: do(X = x*)
        full_do = self.simulate(observed, interventions={intervention_node: intervention_val}, noise=noise)
        total_effect = full_do[target_node] - base_target

        # Direct Effect: hold all downstream mediators fixed at baseline
        paths = self.dag.find_paths(intervention_node, target_node)
        mediators = sorted(
            {node for path in paths for node in path[1:-1]}
        )
        direct_interventions = {intervention_node: intervention_val}
        for med in mediators:
            direct_interventions[med] = observed.get(med, self.dag.nodes[med].baseline_default)

        direct_do = self.simulate(observed, interventions=direct_interventions, noise=noise)
        direct_effect = direct_do[target_node] - base_target
        indirect_effect = total_effect - direct_effect

        summary = (
            f"Intervention on {self.dag.nodes[intervention_node].name} ({observed.get(intervention_node, 0.0):.1f} -> {intervention_val:.1f}) "
            f"yields a total effect of {total_effect:.1f} points on {self.dag.nodes[target_node].name} "
            f"({direct_effect:.1f} direct, {indirect_effect:.1f} mediated across {len(mediators)} intermediate factors)."
        )

        return CausalEffectDecomposition(
            intervention_node=intervention_node,
            intervention_value=intervention_val,
            baseline_value=observed.get(intervention_node, 0.0),
            target_node=target_node,
            total_effect=total_effect,
            direct_effect=direct_effect,
            indirect_effect=indirect_effect,
            mediators=mediators,
            mechanism_summary=summary,
        )

    def attribute_root_causes(self, observed: dict[str, float]) -> list[RootCauseAttribution]:
        """Isolate the marginal causal contribution of each root risk driver."""
        drivers = [
            ("critical_tickets", 0.0, "Critical tickets resolved with zero lingering incidents"),
            ("active_user_decline", 0.0, "Stable usage with zero month-over-month user decline"),
            ("seat_utilization", 0.85, "High seat engagement benchmark (85% active seats)"),
            ("days_to_renewal", 180.0, "Comfortable renewal horizon (180 days buffer)"),
        ]
        base_score = observed.get("renewal_risk_score", 0.0)
        attributions: list[RootCauseAttribution] = []

        total_causal_points = 0.0
        candidate_points = []
        for node_id, healthy_val, explanation in drivers:
            obs_val = observed.get(node_id, self.dag.nodes[node_id].baseline_default)
            # Evaluate what the score would be if this single driver were at healthy benchmark
            cf = self.counterfactual_query(observed, {node_id: healthy_val})
            points = max(0.0, base_score - cf["counterfactual"]["renewal_risk_score"])
            candidate_points.append((node_id, obs_val, healthy_val, points, explanation))
            total_causal_points += points

        denom = max(1.0, total_causal_points)
        for node_id, obs_val, healthy_val, points, explanation in candidate_points:
            pct = round((points / denom) * 100.0, 1) if points > 0 else 0.0
            node = self.dag.nodes[node_id]
            attributions.append(
                RootCauseAttribution(
                    node_id=node_id,
                    node_name=node.name,
                    observed_value=obs_val,
                    healthy_baseline=healthy_val,
                    causal_points=points,
                    percentage_of_risk=pct,
                    explanation=f"{node.name}: observed {obs_val:.2g} vs healthy benchmark {healthy_val:.2g}. {explanation}.",
                )
            )

        return sorted(attributions, key=lambda r: r.causal_points, reverse=True)


def extract_customer_causal_state(
    customer_id: str,
    as_of: date | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    policy: dict[str, float] | None = None,
) -> dict[str, float]:
    """Extract governed numeric causal vector from customer SQLite records."""
    as_of = as_of or date.today()
    if policy is None:
        _, policy = get_active_policy(database_path)

    as_of_iso = as_of.isoformat()

    with connect(database_path) as connection:
        customer = connection.execute(
            "SELECT * FROM customers WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()
        if customer is None:
            raise ValueError(f"Customer not found: {customer_id}")

        contract = connection.execute(
            "SELECT * FROM contracts WHERE customer_id = ? ORDER BY renewal_date LIMIT 1",
            (customer_id,),
        ).fetchone()

        usage_rows = connection.execute(
            """SELECT * FROM product_usage_events
                WHERE customer_id = ? AND event_date <= ?
                ORDER BY event_date DESC LIMIT 2""",
            (customer_id, as_of_iso),
        ).fetchall()

        tickets = connection.execute(
            """SELECT * FROM support_tickets
                WHERE customer_id = ?
                  AND opened_at <= ?
                  AND (resolved_at IS NULL OR resolved_at > ?)
                ORDER BY opened_at DESC""",
            (customer_id, as_of_iso, as_of_iso),
        ).fetchall()

        # Check for executive touch in decision logs or actions
        exec_count = connection.execute(
            """SELECT COUNT(*) FROM decision_events
                WHERE customer_id = ? AND event_at <= ? AND event_type LIKE '%Executive%'""",
            (customer_id, as_of_iso),
        ).fetchone()[0]

    critical_count = sum(1 for t in tickets if t["priority"] == "Critical")
    csat_scores = [t["csat_score"] for t in tickets if t["csat_score"] is not None]
    avg_csat = float(sum(csat_scores) / len(csat_scores)) if csat_scores else (4.5 if critical_count == 0 else 2.5)

    if len(usage_rows) >= 2:
        latest, prev = usage_rows[0], usage_rows[1]
        decline = float((prev["active_users"] - latest["active_users"]) / max(1, prev["active_users"]))
        util = float(latest["active_users"] / max(1, latest["seats_purchased"]))
        fa = float(latest["feature_adoption_pct"])
    elif len(usage_rows) == 1:
        latest = usage_rows[0]
        decline = 0.0
        util = float(latest["active_users"] / max(1, latest["seats_purchased"]))
        fa = float(latest["feature_adoption_pct"])
    else:
        decline = 0.0
        util = 0.5
        fa = 50.0

    if contract:
        renewal = date.fromisoformat(contract["renewal_date"])
        days_to_renewal = float((renewal - as_of).days)
        acv = float(contract["annual_contract_value"])
    else:
        days_to_renewal = 180.0
        acv = 25000.0

    exec_touch = 1.0 if exec_count > 0 else 0.5

    state = {
        "critical_tickets": float(critical_count),
        "csat_score": avg_csat,
        "feature_adoption": fa,
        "seat_utilization": util,
        "active_user_decline": decline,
        "days_to_renewal": days_to_renewal,
        "contract_acv": acv,
        "executive_sponsor_engaged": exec_touch,
    }

    scm = StructuralCausalModel(policy=policy)
    score = scm.evaluate_node("renewal_risk_score", state)
    state["renewal_risk_score"] = score
    return state


def analyze_customer_causality(
    customer_id: str,
    as_of: date | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    policy: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Produce comprehensive causal diagnostic, root causes, and standard interventions."""
    as_of = as_of or date.today()
    if policy is None:
        _, policy = get_active_policy(database_path)

    state = extract_customer_causal_state(customer_id, as_of, database_path, policy)
    scm = StructuralCausalModel(policy=policy)
    dag = scm.dag

    root_causes = scm.attribute_root_causes(state)

    # Standard candidate interventions
    playbooks = [
        {
            "name": "Immediate Critical Escalation",
            "action": "resolve_critical_tickets",
            "description": "Deploy senior support engineer and resolve all open Sev-1 blockers.",
            "intervention": {"critical_tickets": 0.0},
        },
        {
            "name": "Seat Enablement Sprint",
            "action": "boost_seat_engagement",
            "description": "Run targeted department enablement workshops to lift seat utilization to 80%.",
            "intervention": {"seat_utilization": max(state.get("seat_utilization", 0.0), 0.80)},
        },
        {
            "name": "Executive Alignment Session",
            "action": "executive_sponsorship",
            "description": "Conduct Executive Sponsor alignment and QBR review with customer leadership.",
            "intervention": {"executive_sponsor_engaged": 1.0},
        },
        {
            "name": "Commercial Term Extension",
            "action": "extend_renewal_date",
            "description": "Grant a 90-day contract extension to allow adoption recovery before renewal.",
            "intervention": {"days_to_renewal": state.get("days_to_renewal", 0.0) + 90.0},
        },
    ]

    intervention_evaluations = []
    for playbook in playbooks:
        cf = scm.counterfactual_query(state, playbook["intervention"])
        first_node = next(iter(playbook["intervention"]))
        decomp = scm.decompose_effects(
            state,
            first_node,
            playbook["intervention"][first_node],
        )
        intervention_evaluations.append(
            {
                "playbook_name": playbook["name"],
                "action": playbook["action"],
                "description": playbook["description"],
                "interventions": playbook["intervention"],
                "baseline_score": state.get("renewal_risk_score", 0.0),
                "simulated_score": cf["counterfactual"]["renewal_risk_score"],
                "score_reduction": cf["score_reduction"],
                "relative_reduction_pct": cf["relative_reduction_pct"],
                "direct_effect": decomp.direct_effect,
                "indirect_effect": decomp.indirect_effect,
                "mediators": decomp.mediators,
                "mechanism_summary": decomp.mechanism_summary,
            }
        )

    return {
        "customer_id": customer_id,
        "as_of": as_of.isoformat(),
        "baseline_state": state,
        "root_cause_attributions": [asdict(rc) for rc in root_causes],
        "intervention_evaluations": intervention_evaluations,
        "causal_graph": dag.to_dict(),
    }
