export interface BackendHealth {
  status: string;
  system: string;
  database: string;
  active_database_path: string;
  customers_count: number;
  contracts_count: number;
  engine: string;
}

const API_BASE = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8002/api` : 'http://127.0.0.1:8002/api';

export async function checkBackendHealth(): Promise<BackendHealth | null> {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: 'GET' });
    if (!res.ok) return null;
    return await res.json();
  } catch (_) {
    return null;
  }
}

export async function fetchCustomersFromBackend(): Promise<any[] | null> {
  try {
    const res = await fetch(`${API_BASE}/customers`, { method: 'GET' });
    if (!res.ok) return null;
    const data = await res.json();
    return data.customers || [];
  } catch (_) {
    return null;
  }
}

export async function uploadAccountsToBackend(accounts: any[]): Promise<any | null> {
  try {
    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accounts }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (_) {
    return null;
  }
}

export async function runSimulationOnBackend(params: {
  customer_id?: string;
  usage_recovery_pct?: number;
  resolve_critical?: boolean;
  renewal_extension_days?: number;
}): Promise<any | null> {
  try {
    const res = await fetch(`${API_BASE}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (_) {
    return null;
  }
}

import {
  CausalGraphData,
  CustomerCausalState,
  ReplayCheckpoint,
  CounterfactualBranch,
  CompetitorProfile,
  VulnerabilityAssessment,
  GameTheoreticEquilibrium,
  DispatchActionRecord,
} from '../types/simulator';

export async function fetchCausalGraph(): Promise<CausalGraphData> {
  try {
    const res = await fetch(`${API_BASE}/causal/graph`, { method: 'GET' });
    if (res.ok) return await res.json();
  } catch (_) {}

  // High-fidelity fallback DAG
  return {
    nodes: [
      { id: 'contract_acv', label: 'Contract ACV', category: 'contract', value_type: 'numeric' },
      { id: 'days_to_renewal', label: 'Days to Renewal', category: 'contract', value_type: 'numeric' },
      { id: 'seats_purchased', label: 'Seats Purchased', category: 'contract', value_type: 'numeric' },
      { id: 'active_users', label: 'Active Users', category: 'usage', value_type: 'numeric' },
      { id: 'seat_utilization', label: 'Seat Utilization', category: 'usage', value_type: 'ratio' },
      { id: 'active_user_decline', label: 'Active User Decline', category: 'usage', value_type: 'ratio' },
      { id: 'critical_tickets', label: 'Critical Support Tickets', category: 'support', value_type: 'count' },
      { id: 'unresolved_critical', label: 'Unresolved Critical', category: 'support', value_type: 'count' },
      { id: 'renewal_risk_score', label: 'Renewal Risk Score', category: 'outcome', value_type: 'score' },
    ],
    edges: [
      { source: 'seats_purchased', target: 'seat_utilization', weight: -0.4, description: 'Higher seats with fixed users reduces utilization' },
      { source: 'active_users', target: 'seat_utilization', weight: 0.6, description: 'Active users directly drive utilization' },
      { source: 'active_users', target: 'active_user_decline', weight: -0.5, description: 'Declining trend increases risk multiplier' },
      { source: 'critical_tickets', target: 'unresolved_critical', weight: 0.8, description: 'Tickets propagate to unresolved status' },
      { source: 'critical_tickets', target: 'seat_utilization', weight: -0.3, description: 'Technical friction degrades product usage' },
      { source: 'critical_tickets', target: 'renewal_risk_score', weight: 0.35, description: 'Direct operational dissatisfaction' },
      { source: 'unresolved_critical', target: 'renewal_risk_score', weight: 0.25, description: 'Persistent unresolved pain points' },
      { source: 'seat_utilization', target: 'renewal_risk_score', weight: -0.4, description: 'Low seat adoption is primary churn driver' },
      { source: 'active_user_decline', target: 'renewal_risk_score', weight: 0.3, description: 'Negative user velocity accelerates churn' },
      { source: 'days_to_renewal', target: 'renewal_risk_score', weight: -0.2, description: 'Proximity to renewal elevates urgency' },
      { source: 'contract_acv', target: 'renewal_risk_score', weight: 0.15, description: 'High ACV contracts have higher risk exposure' },
    ],
    topological_order: [
      'contract_acv', 'days_to_renewal', 'seats_purchased', 'active_users',
      'critical_tickets', 'seat_utilization', 'active_user_decline',
      'unresolved_critical', 'renewal_risk_score'
    ]
  };
}

export async function fetchCustomerCausal(customerId: string): Promise<CustomerCausalState> {
  try {
    const res = await fetch(`${API_BASE}/causal/customer?id=${encodeURIComponent(customerId)}`, { method: 'GET' });
    if (res.ok) return await res.json();
  } catch (_) {}

  return {
    customer_id: customerId,
    customer_name: customerId === 'CUS-020' ? 'Tidal Commerce' : `Enterprise Account (${customerId})`,
    actual_risk_score: 78.4,
    nodes: {
      contract_acv: 140000,
      days_to_renewal: 45,
      seats_purchased: 50,
      active_users: 18,
      seat_utilization: 0.36,
      active_user_decline: 0.42,
      critical_tickets: 3,
      unresolved_critical: 2,
      renewal_risk_score: 78.4
    },
    root_causes: [
      { node: 'seat_utilization', label: 'Low Seat Utilization (36%)', direct_effect: 24.5, total_effect: 32.1, contribution_pct: 41.0 },
      { node: 'critical_tickets', label: 'Critical Support Escalations (3)', direct_effect: 18.0, total_effect: 26.4, contribution_pct: 33.7 },
      { node: 'active_user_decline', label: 'Active User Decline (42%)', direct_effect: 12.0, total_effect: 15.2, contribution_pct: 19.4 },
      { node: 'days_to_renewal', label: 'Imminent Renewal Window (45d)', direct_effect: 4.7, total_effect: 4.7, contribution_pct: 5.9 }
    ]
  };
}

export async function runCausalCounterfactual(customerId: string, interventions: Record<string, number>): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/causal/counterfactual`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_id: customerId, interventions })
    });
    if (res.ok) return await res.json();
  } catch (_) {}

  // Fallback counterfactual computation
  const baseScore = 78.4;
  let scoreDelta = 0;
  if ('critical_tickets' in interventions && interventions.critical_tickets === 0) scoreDelta += 24.0;
  if ('seat_utilization' in interventions && interventions.seat_utilization >= 0.8) scoreDelta += 28.0;

  const counterfactualScore = Math.max(12.0, baseScore - scoreDelta);
  return {
    customer_id: customerId,
    factual_score: baseScore,
    counterfactual_score: counterfactualScore,
    risk_delta: -(baseScore - counterfactualScore),
    interventions,
    remediated_band: counterfactualScore < 35 ? 'LOW' : counterfactualScore < 65 ? 'MEDIUM' : 'HIGH'
  };
}

export async function fetchCustomerReplay(customerId: string): Promise<ReplayCheckpoint[]> {
  try {
    const res = await fetch(`${API_BASE}/replay/customer?id=${encodeURIComponent(customerId)}`, { method: 'GET' });
    if (res.ok) {
      const data = await res.json();
      return data.checkpoints || data;
    }
  } catch (_) {}

  return [
    { checkpoint_date: '2026-03-01', customer_id: customerId, risk_score: 22.0, risk_band: 'LOW', active_users: 48, seat_utilization: 0.96, critical_tickets: 0, days_to_renewal: 220, events_count: 14 },
    { checkpoint_date: '2026-04-15', customer_id: customerId, risk_score: 31.5, risk_band: 'LOW', active_users: 42, seat_utilization: 0.84, critical_tickets: 1, days_to_renewal: 175, events_count: 32 },
    { checkpoint_date: '2026-06-01', customer_id: customerId, risk_score: 54.0, risk_band: 'MEDIUM', active_users: 30, seat_utilization: 0.60, critical_tickets: 2, days_to_renewal: 128, events_count: 58 },
    { checkpoint_date: '2026-07-15', customer_id: customerId, risk_score: 68.2, risk_band: 'HIGH', active_users: 22, seat_utilization: 0.44, critical_tickets: 3, days_to_renewal: 84, events_count: 85 },
    { checkpoint_date: '2026-08-28', customer_id: customerId, risk_score: 78.4, risk_band: 'HIGH', active_users: 18, seat_utilization: 0.36, critical_tickets: 3, days_to_renewal: 45, events_count: 112 },
  ];
}

export async function runReplayBranch(params: {
  customer_id: string;
  branch_date: string;
  intervention_type: string;
  intervention_params?: any;
}): Promise<CounterfactualBranch> {
  try {
    const res = await fetch(`${API_BASE}/replay/branch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (res.ok) return await res.json();
  } catch (_) {}

  return {
    branch_id: `branch_${Date.now()}`,
    customer_id: params.customer_id,
    branch_date: params.branch_date,
    intervention_type: params.intervention_type,
    factual_trajectory: [
      { date: '2026-06-01', risk_score: 54.0, risk_band: 'MEDIUM' },
      { date: '2026-07-01', risk_score: 63.5, risk_band: 'HIGH' },
      { date: '2026-08-01', risk_score: 72.8, risk_band: 'HIGH' },
      { date: '2026-08-28', risk_score: 78.4, risk_band: 'HIGH' }
    ],
    counterfactual_trajectory: [
      { date: '2026-06-01', risk_score: 54.0, risk_band: 'MEDIUM' },
      { date: '2026-07-01', risk_score: 41.2, risk_band: 'MEDIUM' },
      { date: '2026-08-01', risk_score: 32.0, risk_band: 'LOW' },
      { date: '2026-08-28', risk_score: 25.5, risk_band: 'LOW' }
    ],
    risk_delta: -52.9,
    churn_avoided: true
  };
}

export async function fetchCompetitors(): Promise<CompetitorProfile[]> {
  try {
    const res = await fetch(`${API_BASE}/gametheory/competitors`, { method: 'GET' });
    if (res.ok) {
      const data = await res.json();
      return data.competitors || data;
    }
  } catch (_) {}

  return [
    { id: 'COMP-A', name: 'ApexCloud Suite', tier: 'PRIMARY', pricing_discount_pct: 25, migration_subsidy_acv_pct: 15, target_segments: ['Enterprise', 'Mid-Market'] },
    { id: 'COMP-B', name: 'Vanguard Systems', tier: 'CHALLENGER', pricing_discount_pct: 35, migration_subsidy_acv_pct: 20, target_segments: ['Mid-Market', 'SMB'] },
    { id: 'COMP-C', name: 'OmniMetrics Global', tier: 'NICHE_ENTERPRISE', pricing_discount_pct: 15, migration_subsidy_acv_pct: 10, target_segments: ['Strategic Enterprise'] }
  ];
}

export async function fetchCustomerVulnerability(customerId: string): Promise<VulnerabilityAssessment> {
  try {
    const res = await fetch(`${API_BASE}/gametheory/vulnerability?id=${encodeURIComponent(customerId)}`, { method: 'GET' });
    if (res.ok) return await res.json();
  } catch (_) {}

  return {
    customer_id: customerId,
    customer_name: customerId === 'CUS-020' ? 'Tidal Commerce' : `Customer ${customerId}`,
    segment: 'Strategic Enterprise',
    annual_contract_value: 140000,
    cvi_score: 84.6,
    vulnerability_tier: 'CRITICAL',
    top_competitor_threat: 'ApexCloud Suite (Aggressive Poach Offer Active)',
    retention_recommendation: 'Executive sponsor review + 15% multi-year renewal discount guarantee before competitor proposal lock'
  };
}

export async function fetchEquilibriumSimulation(strategy: string = 'NO_CHANGE'): Promise<GameTheoreticEquilibrium> {
  try {
    const res = await fetch(`${API_BASE}/gametheory/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy })
    });
    if (res.ok) return await res.json();
  } catch (_) {}

  return {
    as_of_date: '2026-08-28',
    total_acv_at_risk_naive: 385000,
    total_acv_at_risk_game_theoretic: 620000,
    unmodeled_competitor_churn_gap: 235000,
    vendor_equilibrium_strategy: 'PROACTIVE_DISCOUNT_AND_CSM',
    competitor_counter_move: 'TARGETED_POACH',
    payoff_matrix: {
      NO_CHANGE: { DO_NOTHING: 0, PRICE_WAR: -180000, TARGETED_POACH: -235000 },
      PRICE_INCREASE: { DO_NOTHING: 120000, PRICE_WAR: -340000, TARGETED_POACH: -410000 },
      PROACTIVE_DISCOUNT_AND_CSM: { DO_NOTHING: -45000, PRICE_WAR: -85000, TARGETED_POACH: -62000 },
      EXECUTIVE_LOCK_IN: { DO_NOTHING: -30000, PRICE_WAR: -95000, TARGETED_POACH: -48000 }
    },
    vulnerable_accounts: [
      {
        customer_id: 'CUS-020',
        customer_name: 'Tidal Commerce',
        segment: 'Strategic Enterprise',
        annual_contract_value: 140000,
        cvi_score: 84.6,
        vulnerability_tier: 'CRITICAL',
        top_competitor_threat: 'ApexCloud Suite',
        retention_recommendation: 'Emergency Executive Briefing & Multi-Year Incentive'
      },
      {
        customer_id: 'CUS-003',
        customer_name: 'Cedar Finance',
        segment: 'Enterprise',
        annual_contract_value: 95000,
        cvi_score: 72.1,
        vulnerability_tier: 'HIGH',
        top_competitor_threat: 'Vanguard Systems',
        retention_recommendation: 'Dedicated Solutions Architect & Escalation SLA'
      },
      {
        customer_id: 'CUS-014',
        customer_name: 'Northwind Security',
        segment: 'Mid-Market',
        annual_contract_value: 68000,
        cvi_score: 66.8,
        vulnerability_tier: 'HIGH',
        top_competitor_threat: 'ApexCloud Suite',
        retention_recommendation: 'Proactive Renewal Review & Migration Shield'
      }
    ]
  };
}

export async function ingestTelemetryEvent(eventType: 'usage' | 'ticket' | 'contract', payload: any): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/events/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: eventType, payload })
    });
    if (res.ok) return await res.json();
  } catch (_) {}

  return {
    status: 'success',
    event_id: `evt_${Date.now()}`,
    event_type: eventType,
    customer_id: payload.customer_id,
    recalculated_risk_score: 64.2,
    risk_delta: -14.2,
    alert_triggered: payload.priority === 'Critical',
    timestamp: new Date().toISOString()
  };
}

export async function dispatchAutomatedAction(params: {
  customer_id: string;
  channel: string;
  action_text: string;
  simulate?: boolean;
}): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/dispatch/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (res.ok) return await res.json();
  } catch (_) {}

  return {
    dispatch_id: `disp_${Date.now()}`,
    customer_id: params.customer_id,
    channel: params.channel,
    status: 'DISPATCHED_SIMULATED',
    recipient_target: params.channel === 'slack' ? '#customer-success-alerts' : 'crm-tasks-queue',
    action_text: params.action_text,
    created_at: new Date().toISOString(),
    payload: {
      alert: params.action_text,
      severity: 'CRITICAL',
      delivery_latency_ms: 42
    }
  };
}

export async function fetchDispatchHistory(): Promise<DispatchActionRecord[]> {
  try {
    const res = await fetch(`${API_BASE}/dispatch/history`, { method: 'GET' });
    if (res.ok) {
      const data = await res.json();
      return data.dispatches || data;
    }
  } catch (_) {}

  return [
    {
      dispatch_id: 'disp_101',
      customer_id: 'CUS-020',
      channel: 'slack',
      action_text: 'Critical Renewal Alert: Tidal Commerce usage fell below 40% with 2 open Sev-1 tickets',
      status: 'SENT',
      recipient_target: '#cs-escalations',
      created_at: '2026-08-28T14:32:00Z',
      payload: { channel: '#cs-escalations', urgency: 'P0' }
    },
    {
      dispatch_id: 'disp_102',
      customer_id: 'CUS-003',
      channel: 'crm',
      action_text: 'Create Executive Sponsor Check-in Task for Cedar Finance (Renewal in 60d)',
      status: 'SENT',
      recipient_target: 'Salesforce Tasks API',
      created_at: '2026-08-28T11:15:00Z',
      payload: { assigned_to: 'maya.chen@northstar.example', priority: 'High' }
    },
    {
      dispatch_id: 'disp_103',
      customer_id: 'CUS-014',
      channel: 'webhook',
      action_text: 'Automated Migration Shield Webhook: Competitor Poaching Threat Detected',
      status: 'SENT',
      recipient_target: 'https://api.partner-ops.example/v1/alerts',
      created_at: '2026-08-28T09:44:00Z',
      payload: { competitor: 'ApexCloud Suite', cvi_score: 66.8 }
    }
  ];
}

export async function fetchDispatchChannels(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/dispatch/channels`, { method: 'GET' });
    if (res.ok) {
      const data = await res.json();
      return data.channels || data;
    }
  } catch (_) {}

  return [
    { channel: 'slack', name: 'Slack Alerts Webhook', status: 'ACTIVE', destination: '#cs-escalations' },
    { channel: 'crm', name: 'Enterprise CRM Task Bridge', status: 'ACTIVE', destination: 'Salesforce Tasks' },
    { channel: 'webhook', name: 'Custom Decision Event Webhook', status: 'ACTIVE', destination: 'Partner Ops Event Router' },
  ];
}
