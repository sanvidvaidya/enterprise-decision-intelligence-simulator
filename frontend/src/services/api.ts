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
