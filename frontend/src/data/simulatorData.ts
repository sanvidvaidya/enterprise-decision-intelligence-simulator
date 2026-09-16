import data from './simulatorData.json';
import {
  Customer,
  Contract,
  AccountManager,
  SupportTicket,
  UsageEvent,
  CustomerAssessment,
  PolicyParameters,
} from '../types/simulator';

export const DEFAULT_POLICY: PolicyParameters = data.default_policy as unknown as PolicyParameters;
export const RAW_CUSTOMERS: Customer[] = data.customers as unknown as Customer[];
export const RAW_CONTRACTS: Contract[] = data.contracts as unknown as Contract[];
export const RAW_ACCOUNT_MANAGERS: AccountManager[] = data.account_managers as unknown as AccountManager[];
export const RAW_TICKETS: SupportTicket[] = data.tickets as unknown as SupportTicket[];
export const RAW_USAGE: UsageEvent[] = data.usage as unknown as UsageEvent[];
export const INITIAL_ASSESSMENTS: CustomerAssessment[] = data.assessments as unknown as CustomerAssessment[];
