export interface Customer {
  customer_id: string;
  customer_name: string;
  industry: string;
  segment: 'Enterprise' | 'Mid-Market' | 'SMB';
  employee_count: number;
  region: string;
  account_manager_id: string;
  customer_status: string;
  created_at: string;
}

export interface Contract {
  contract_id: string;
  customer_id: string;
  contract_start_date: string;
  contract_end_date: string;
  annual_contract_value: number;
  renewal_date: string;
  contract_status: string;
}

export interface AccountManager {
  account_manager_id: string;
  full_name: string;
  email: string;
  region: string;
  active: number;
}

export interface SupportTicket {
  ticket_id: string;
  customer_id: string;
  category: string;
  priority: 'Critical' | 'High' | 'Medium' | 'Low';
  ticket_status: 'Open' | 'In Progress' | 'Resolved' | 'Closed';
  opened_at: string;
  resolved_at: string | null;
}

export interface UsageEvent {
  usage_event_id: string;
  customer_id: string;
  event_date: string;
  active_users: number;
  seats_purchased: number;
}

export interface RiskFactor {
  name: string;
  points: number;
  explanation: string;
  evidence_record_ids: string[];
  recommended_action: string;
}

export interface CustomerAssessment {
  customer: Customer & { account_manager_name?: string; account_manager_email?: string };
  contract: Contract | null;
  risk_score: number;
  risk_level: 'High' | 'Medium' | 'Low';
  factors: RiskFactor[];
  recommended_actions: string[];
}

export interface PolicyParameters {
  medium_risk_threshold: number;
  high_risk_threshold: number;
  usage_decline_moderate_threshold: number;
  usage_decline_moderate_points: number;
  usage_decline_high_threshold: number;
  usage_decline_high_points: number;
  seat_engagement_low_threshold: number;
  seat_engagement_low_points: number;
  seat_engagement_medium_threshold: number;
  seat_engagement_medium_points: number;
  critical_support_points: number;
  renewal_near_days: number;
  renewal_near_points: number;
  renewal_mid_days: number;
  renewal_mid_points: number;
  renewal_far_days: number;
  renewal_far_points: number;
  high_acv_threshold: number;
  high_acv_points: number;
  medium_acv_threshold: number;
  medium_acv_points: number;
}

export type SimulatorTab = 'LANDING' | 'COCKPIT' | 'PORTFOLIO' | 'SCENARIO_LAB' | 'CAUSAL_GRAPH' | 'TIME_TRAVEL' | 'GAME_THEORY' | 'DISPATCH_STREAM' | 'GOVERNANCE';

// Advanced Innovation Types: Causal DAG, Replay, Game Theory, Dispatch
export interface CausalNode {
  id: string;
  label: string;
  category: string;
  value_type: string;
}

export interface CausalEdge {
  source: string;
  target: string;
  weight: number;
  description: string;
}

export interface CausalGraphData {
  nodes: CausalNode[];
  edges: CausalEdge[];
  topological_order: string[];
}

export interface CustomerCausalState {
  customer_id: string;
  customer_name: string;
  actual_risk_score: number;
  nodes: Record<string, number>;
  root_causes: Array<{
    node: string;
    label: string;
    direct_effect: number;
    total_effect: number;
    contribution_pct: number;
  }>;
}

export interface ReplayCheckpoint {
  checkpoint_date: string;
  customer_id: string;
  risk_score: number;
  risk_band: string;
  active_users: number;
  seat_utilization: number;
  critical_tickets: number;
  days_to_renewal: number;
  events_count: number;
}

export interface CounterfactualBranch {
  branch_id: string;
  customer_id: string;
  branch_date: string;
  intervention_type: string;
  factual_trajectory: Array<{ date: string; risk_score: number; risk_band: string }>;
  counterfactual_trajectory: Array<{ date: string; risk_score: number; risk_band: string }>;
  risk_delta: number;
  churn_avoided: boolean;
}

export interface CompetitorProfile {
  id: string;
  name: string;
  tier: string;
  pricing_discount_pct: number;
  migration_subsidy_acv_pct: number;
  target_segments: string[];
}

export interface VulnerabilityAssessment {
  customer_id: string;
  customer_name: string;
  segment: string;
  annual_contract_value: number;
  cvi_score: number;
  vulnerability_tier: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW';
  top_competitor_threat: string;
  retention_recommendation: string;
}

export interface GameTheoreticEquilibrium {
  as_of_date: string;
  total_acv_at_risk_naive: number;
  total_acv_at_risk_game_theoretic: number;
  unmodeled_competitor_churn_gap: number;
  vendor_equilibrium_strategy: string;
  competitor_counter_move: string;
  payoff_matrix: Record<string, Record<string, number>>;
  vulnerable_accounts: VulnerabilityAssessment[];
}

export interface DispatchActionRecord {
  dispatch_id: string;
  customer_id: string;
  channel: string;
  action_text: string;
  status: string;
  recipient_target: string;
  created_at: string;
  payload: Record<string, any>;
}
