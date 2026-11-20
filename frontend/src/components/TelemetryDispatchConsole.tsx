import React, { useState, useEffect } from 'react';
import { Customer, DispatchActionRecord } from '../types/simulator';
import {
  ingestTelemetryEvent,
  dispatchAutomatedAction,
  fetchDispatchHistory,
  fetchDispatchChannels,
} from '../services/api';
import { Radio, Send, CheckCircle, AlertOctagon, RefreshCw, MessageSquare, Database, Globe } from 'lucide-react';

interface TelemetryDispatchConsoleProps {
  customers: Customer[];
  selectedCustomerId?: string;
  onSelectCustomer: (id: string) => void;
}

export const TelemetryDispatchConsole: React.FC<TelemetryDispatchConsoleProps> = ({
  customers,
  selectedCustomerId = 'CUS-020',
  onSelectCustomer,
}) => {
  const [activeCustomer, setActiveCustomer] = useState<string>(selectedCustomerId);
  const [channels, setChannels] = useState<any[]>([]);
  const [history, setHistory] = useState<DispatchActionRecord[]>([]);
  const [eventType, setEventType] = useState<'usage' | 'ticket' | 'contract'>('ticket');
  const [selectedChannel, setSelectedChannel] = useState<string>('slack');
  const [customActionText, setCustomActionText] = useState<string>('Escalation Alert: Critical support backlog exceeding 48h SLA');
  const [latestIngestStatus, setLatestIngestStatus] = useState<any | null>(null);
  const [latestDispatchStatus, setLatestDispatchStatus] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    fetchDispatchChannels().then(setChannels);
    fetchDispatchHistory().then(setHistory);
  }, []);

  const handleSimulateTelemetry = async () => {
    setLoading(true);
    let payload: any = { customer_id: activeCustomer };
    if (eventType === 'ticket') {
      payload = {
        customer_id: activeCustomer,
        priority: 'Critical',
        ticket_status: 'Open',
        ticket_category: 'API Rate Limits',
        ticket_summary: 'Webhook delivery timeouts blocking customer billing cycle'
      };
    } else if (eventType === 'usage') {
      payload = {
        customer_id: activeCustomer,
        event_date: new Date().toISOString().split('T')[0],
        active_users: 14,
        seats_purchased: 50,
        sessions: 120,
        feature_adoption_pct: 35.0
      };
    } else {
      payload = {
        customer_id: activeCustomer,
        annual_contract_value: 140000,
        renewal_date: '2026-10-15',
        auto_renew: 0
      };
    }

    const res = await ingestTelemetryEvent(eventType, payload);
    setLatestIngestStatus(res);
    setLoading(false);
  };

  const handleDispatchAction = async () => {
    setLoading(true);
    const res = await dispatchAutomatedAction({
      customer_id: activeCustomer,
      channel: selectedChannel,
      action_text: customActionText,
      simulate: true,
    });
    setLatestDispatchStatus(res);
    fetchDispatchHistory().then(setHistory);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 bg-stone-900 text-stone-100 rounded-2xl shadow-lg border border-stone-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Radio className="w-5 h-5 text-amber-400" />
            <span className="text-xs font-mono uppercase tracking-widest text-amber-400 font-semibold">
              Live Ingestion & Multi-Channel Dispatch
            </span>
          </div>
          <h2 className="text-2xl font-bold font-['Outfit']">Real-Time Telemetry Stream & Action Dispatch Hub</h2>
          <p className="text-stone-400 text-sm mt-1 max-w-2xl">
            Simulate operational telemetry arrival (tickets, usage drops, contract amendments). Instantly trigger automated interventions to Slack, Salesforce/CRM, or custom event webhooks.
          </p>
        </div>

        {/* Customer Selector */}
        <div className="bg-stone-800/80 p-2.5 rounded-xl border border-stone-700/80 flex items-center gap-3">
          <label className="text-xs text-stone-400 font-medium">Target Account:</label>
          <select
            value={activeCustomer}
            onChange={(e) => {
              setActiveCustomer(e.target.value);
              onSelectCustomer(e.target.value);
            }}
            className="bg-stone-900 border border-stone-700 text-stone-200 text-sm rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-amber-500 outline-none"
          >
            {customers.map((c) => (
              <option key={c.customer_id} value={c.customer_id}>
                {c.customer_id} - {c.customer_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Col: Telemetry Ingest Simulator */}
        <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-stone-200/80 shadow-sm space-y-4">
          <h3 className="font-bold text-stone-900 text-base flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-amber-700" />
            Simulate Incoming Operational Telemetry
          </h3>
          <p className="text-xs text-stone-500">
            Push real-time payload events into the decision engine to trigger immediate Bayesian risk recalculation.
          </p>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-stone-600 block mb-1">Telemetry Event Type</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'ticket', label: 'Support Ticket (Sev-1)' },
                  { id: 'usage', label: 'Usage Drop Event' },
                  { id: 'contract', label: 'Contract Auto-Renew Off' },
                ].map((type) => (
                  <button
                    key={type.id}
                    onClick={() => setEventType(type.id as any)}
                    className={`py-2 px-3 text-xs rounded-xl font-medium border text-center transition-all ${
                      eventType === type.id
                        ? 'bg-amber-600 text-white border-amber-600 font-bold shadow-sm'
                        : 'bg-stone-50 text-stone-700 border-stone-200 hover:bg-stone-100'
                    }`}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleSimulateTelemetry}
              disabled={loading}
              className="w-full py-2.5 bg-stone-900 hover:bg-stone-800 text-stone-100 font-semibold rounded-xl text-xs flex items-center justify-center gap-2 transition-all"
            >
              <Radio className="w-4 h-4 text-amber-400" />
              Ingest Telemetry Event for {activeCustomer}
            </button>

            {latestIngestStatus && (
              <div className="p-3.5 bg-stone-50 rounded-xl border border-stone-200 text-xs font-mono space-y-1">
                <div className="flex items-center gap-2 text-emerald-700 font-bold">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  Event Ingested: {latestIngestStatus.event_id}
                </div>
                <div className="text-stone-600">
                  Dynamic Recalculation: <span className="font-bold text-stone-900">{latestIngestStatus.recalculated_risk_score} pts</span>
                  {' '}(Delta: <span className="text-rose-600 font-bold">{latestIngestStatus.risk_delta} pts</span>)
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Action Dispatch Trigger */}
        <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-stone-200/80 shadow-sm space-y-4">
          <h3 className="font-bold text-stone-900 text-base flex items-center gap-2">
            <Send className="w-5 h-5 text-amber-700" />
            Dispatch Automated Intervention Action
          </h3>
          <p className="text-xs text-stone-500">
            Route programmatic alerts and actionable mitigation tasks to downstream enterprise workflow channels.
          </p>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-stone-600 block mb-1">Target Channel</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'slack', label: 'Slack Webhook', icon: MessageSquare },
                  { id: 'crm', label: 'CRM Task API', icon: Database },
                  { id: 'webhook', label: 'Custom HTTP', icon: Globe },
                ].map((ch) => {
                  const Icon = ch.icon;
                  return (
                    <button
                      key={ch.id}
                      onClick={() => setSelectedChannel(ch.id)}
                      className={`py-2 px-3 text-xs rounded-xl font-medium border flex items-center justify-center gap-1.5 transition-all ${
                        selectedChannel === ch.id
                          ? 'bg-amber-600 text-white border-amber-600 font-bold shadow-sm'
                          : 'bg-stone-50 text-stone-700 border-stone-200 hover:bg-stone-100'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {ch.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-stone-600 block mb-1">Action Text Payload</label>
              <input
                type="text"
                value={customActionText}
                onChange={(e) => setCustomActionText(e.target.value)}
                className="w-full text-xs p-2.5 rounded-xl border border-stone-300 focus:ring-2 focus:ring-amber-500 outline-none"
              />
            </div>

            <button
              onClick={handleDispatchAction}
              disabled={loading}
              className="w-full py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 transition-all shadow-sm"
            >
              <Send className="w-4 h-4" />
              Dispatch Action via {selectedChannel.toUpperCase()}
            </button>

            {latestDispatchStatus && (
              <div className="p-3.5 bg-emerald-50 rounded-xl border border-emerald-200 text-xs font-mono space-y-1">
                <div className="flex items-center gap-2 text-emerald-800 font-bold">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  Dispatched: {latestDispatchStatus.dispatch_id} ({latestDispatchStatus.status})
                </div>
                <div className="text-emerald-700">Destination: {latestDispatchStatus.recipient_target}</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dispatch Ledger Audit Table */}
      <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-stone-200/80 shadow-sm">
        <h3 className="font-bold text-stone-900 text-base mb-4 flex items-center gap-2">
          <Database className="w-5 h-5 text-amber-700" />
          Immutable Dispatch Ledger (Audit Log)
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-stone-200 text-stone-500 font-mono">
                <th className="pb-2">Timestamp</th>
                <th className="pb-2">Account</th>
                <th className="pb-2">Channel</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Target Destination</th>
                <th className="pb-2">Action Summary</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100 font-mono">
              {history.map((record) => (
                <tr key={record.dispatch_id} className="hover:bg-stone-50/70 transition-colors">
                  <td className="py-2.5 text-stone-500">{record.created_at}</td>
                  <td className="py-2.5 font-sans font-medium text-stone-900">{record.customer_id}</td>
                  <td className="py-2.5">
                    <span className="bg-stone-100 text-stone-700 px-2 py-0.5 rounded uppercase text-[10px] font-bold">
                      {record.channel}
                    </span>
                  </td>
                  <td className="py-2.5">
                    <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded font-bold text-[10px]">
                      {record.status}
                    </span>
                  </td>
                  <td className="py-2.5 text-stone-600">{record.recipient_target}</td>
                  <td className="py-2.5 text-stone-800 font-sans truncate max-w-xs">{record.action_text}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
