import {
  Customer,
  Contract,
  SupportTicket,
  UsageEvent,
  RiskFactor,
  CustomerAssessment,
  PolicyParameters,
} from '../types/simulator';

export const REFERENCE_DATE = new Date('2026-08-28T00:00:00Z');

export function evaluateCustomerRisk(
  customer: Customer & { account_manager_name?: string; account_manager_email?: string },
  contract: Contract | null,
  usageEvents: UsageEvent[],
  tickets: SupportTicket[],
  policy: PolicyParameters,
  overrides?: {
    latestActiveUsers?: number;
    resolveCritical?: boolean;
    renewalExtensionDays?: number;
  }
): CustomerAssessment {
  const factors: RiskFactor[] = [];
  const latestActiveUsers = overrides?.latestActiveUsers;
  const resolveCritical = overrides?.resolveCritical || false;
  const renewalExtensionDays = overrides?.renewalExtensionDays || 0;

  // Sort usage descending by date
  const sortedUsage = [...usageEvents].sort(
    (a, b) => new Date(b.event_date).getTime() - new Date(a.event_date).getTime()
  );

  // Rule 1 & 2: Usage Decline & Seat Engagement
  if (sortedUsage.length >= 2) {
    const latest = sortedUsage[0];
    const previous = sortedUsage[1];
    const activeUsers = latestActiveUsers !== undefined ? latestActiveUsers : latest.active_users;
    const decline = (previous.active_users - activeUsers) / Math.max(previous.active_users, 1);

    if (decline >= policy.usage_decline_high_threshold) {
      factors.push({
        name: 'Declining product usage',
        points: Math.round(policy.usage_decline_high_points),
        explanation: `Active users declined ${(decline * 100).toFixed(0)}% from ${previous.active_users} to ${activeUsers} in the latest month.`,
        evidence_record_ids: [previous.usage_event_id, latest.usage_event_id],
        recommended_action: 'Schedule a usage-review meeting and agree an adoption recovery plan.',
      });
    } else if (decline >= policy.usage_decline_moderate_threshold) {
      factors.push({
        name: 'Declining product usage',
        points: Math.round(policy.usage_decline_moderate_points),
        explanation: `Active users declined ${(decline * 100).toFixed(0)}% in the latest month.`,
        evidence_record_ids: [previous.usage_event_id, latest.usage_event_id],
        recommended_action: 'Review adoption barriers with the customer administrator.',
      });
    }

    const seats = latest.seats_purchased || 100;
    const penetration = activeUsers / seats;
    if (penetration < policy.seat_engagement_low_threshold) {
      factors.push({
        name: 'Low seat engagement',
        points: Math.round(policy.seat_engagement_low_points),
        explanation: `Only ${(penetration * 100).toFixed(0)}% of purchased seats (${activeUsers}/${seats}) were active in the latest month.`,
        evidence_record_ids: [latest.usage_event_id],
        recommended_action: 'Identify inactive teams and run targeted enablement sessions.',
      });
    } else if (penetration < policy.seat_engagement_medium_threshold) {
      factors.push({
        name: 'Low seat engagement',
        points: Math.round(policy.seat_engagement_medium_points),
        explanation: `Only ${(penetration * 100).toFixed(0)}% of purchased seats were active in the latest month.`,
        evidence_record_ids: [latest.usage_event_id],
        recommended_action: 'Share an adoption dashboard and propose administrator training.',
      });
    }
  }

  // Rule 3: Critical Support Tickets
  const openCriticalTickets = tickets.filter(
    (t) => t.priority === 'Critical' && (t.ticket_status === 'Open' || t.ticket_status === 'In Progress')
  );

  if (openCriticalTickets.length > 0 && !resolveCritical) {
    factors.push({
      name: 'Unresolved critical support',
      points: Math.round(policy.critical_support_points),
      explanation: `${openCriticalTickets.length} critical ticket(s) remain unresolved.`,
      evidence_record_ids: openCriticalTickets.map((t) => t.ticket_id),
      recommended_action: 'Escalate to support leadership, assign an owner, and send the customer a resolution timeline.',
    });
  }

  // Rule 4 & 5: Renewal Window & Contract Value
  if (contract) {
    const rawRenewal = new Date(contract.renewal_date);
    const renewalWithExtension = new Date(
      rawRenewal.getTime() + renewalExtensionDays * 24 * 60 * 60 * 1000
    );
    const diffTime = renewalWithExtension.getTime() - REFERENCE_DATE.getTime();
    const daysToRenewal = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    let renewalPoints = 0;
    if (daysToRenewal <= policy.renewal_near_days) {
      renewalPoints = policy.renewal_near_points;
    } else if (daysToRenewal <= policy.renewal_mid_days) {
      renewalPoints = policy.renewal_mid_points;
    } else if (daysToRenewal <= policy.renewal_far_days) {
      renewalPoints = policy.renewal_far_points;
    }

    if (renewalPoints > 0) {
      factors.push({
        name: 'Renewal approaching',
        points: Math.round(renewalPoints),
        explanation: `Renewal is in ${daysToRenewal} day(s) on ${renewalWithExtension.toISOString().split('T')[0]}.`,
        evidence_record_ids: [contract.contract_id],
        recommended_action: 'Confirm renewal stakeholders, commercial timeline, and success criteria this week.',
      });
    }

    const acv = contract.annual_contract_value || 0;
    let acvPoints = 0;
    if (acv >= policy.high_acv_threshold) {
      acvPoints = policy.high_acv_points;
    } else if (acv >= policy.medium_acv_threshold) {
      acvPoints = policy.medium_acv_points;
    }

    if (acvPoints > 0) {
      factors.push({
        name: 'High contract value',
        points: Math.round(acvPoints),
        explanation: `Annual contract value is $${acv.toLocaleString()}.`,
        evidence_record_ids: [contract.contract_id],
        recommended_action: 'Create an executive account plan and involve the renewal sponsor.',
      });
    }
  }

  const rawScore = factors.reduce((sum, f) => sum + f.points, 0);
  const score = Math.min(100, rawScore);

  let level: 'High' | 'Medium' | 'Low' = 'Low';
  if (score >= policy.high_risk_threshold) {
    level = 'High';
  } else if (score >= policy.medium_risk_threshold) {
    level = 'Medium';
  }

  const uniqueActions = Array.from(new Set(factors.map((f) => f.recommended_action)));

  return {
    customer,
    contract,
    risk_score: score,
    risk_level: level,
    factors,
    recommended_actions: uniqueActions,
  };
}
