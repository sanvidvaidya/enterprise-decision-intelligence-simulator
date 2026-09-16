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

export type SimulatorTab = 'LANDING' | 'COCKPIT' | 'PORTFOLIO' | 'SCENARIO_LAB' | 'GOVERNANCE';
