import React, { useState, useEffect } from 'react';
import { Customer, ReplayCheckpoint, CounterfactualBranch } from '../types/simulator';
import { fetchCustomerReplay, runReplayBranch } from '../services/api';
import { Clock, GitBranch, Play, CheckCircle2, AlertTriangle, ArrowRight, RotateCcw } from 'lucide-react';

interface TimeTravelReplayProps {
  customers: Customer[];
  selectedCustomerId?: string;
  onSelectCustomer: (id: string) => void;
}

export const TimeTravelReplay: React.FC<TimeTravelReplayProps> = ({
  customers,
  selectedCustomerId = 'CUS-020',
  onSelectCustomer,
}) => {
  const [activeCustomer, setActiveCustomer] = useState<string>(selectedCustomerId);
  const [checkpoints, setCheckpoints] = useState<ReplayCheckpoint[]>([]);
  const [selectedCheckpointIndex, setSelectedCheckpointIndex] = useState<number>(0);
  const [branchResult, setBranchResult] = useState<CounterfactualBranch | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (activeCustomer) {
      fetchCustomerReplay(activeCustomer).then((res) => {
        setCheckpoints(res);
        setSelectedCheckpointIndex(res.length > 0 ? res.length - 1 : 0);
        setBranchResult(null);
      });
    }
  }, [activeCustomer]);

  const activeCheckpoint = checkpoints[selectedCheckpointIndex] || null;

  const handleSimulateBranch = async () => {
    if (!activeCheckpoint) return;
    setLoading(true);
    const branch = await runReplayBranch({
      customer_id: activeCustomer,
      branch_date: activeCheckpoint.checkpoint_date,
      intervention_type: 'resolve_critical_tickets',
      intervention_params: { target_active_users_boost: 15 },
    });
    setBranchResult(branch);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 bg-stone-900 text-stone-100 rounded-2xl shadow-lg border border-stone-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-5 h-5 text-amber-400" />
            <span className="text-xs font-mono uppercase tracking-widest text-amber-400 font-semibold">
              Deterministic Event Replay Engine
            </span>
          </div>
          <h2 className="text-2xl font-bold font-['Outfit']">Point-in-Time State Reconstruction & Counterfactual Branching</h2>
          <p className="text-stone-400 text-sm mt-1 max-w-2xl">
            Reconstruct exact customer state as of any historical timestamp with zero lookahead bias. Fork counterfactual timeline branches to prove what would have happened if an intervention occurred earlier.
          </p>
        </div>

        {/* Customer Selector */}
        <div className="bg-stone-800/80 p-2.5 rounded-xl border border-stone-700/80 flex items-center gap-3">
          <label className="text-xs text-stone-400 font-medium">Account:</label>
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

      {/* Interactive Timeline Scrubber */}
      <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-stone-200/80 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-stone-900 text-base flex items-center gap-2">
            <Play className="w-4 h-4 text-amber-700 fill-amber-700" />
            Historical Replay Checkpoints
          </h3>
          <span className="text-xs font-mono text-stone-500 bg-stone-100 px-3 py-1 rounded-full border border-stone-200">
            {checkpoints.length} Checkpoints Available
          </span>
        </div>

        {/* Timeline dots / bar */}
        <div className="relative pt-4 pb-2">
          <div className="absolute top-1/2 left-0 right-0 h-1 bg-stone-200 -translate-y-1/2 rounded-full" />
          <div className="relative flex justify-between">
            {checkpoints.map((cp, idx) => {
              const isSelected = idx === selectedCheckpointIndex;
              return (
                <button
                  key={idx}
                  onClick={() => setSelectedCheckpointIndex(idx)}
                  className={`flex flex-col items-center group focus:outline-none transition-all`}
                >
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center font-mono text-[10px] font-bold border-2 transition-all ${
                      isSelected
                        ? 'bg-amber-600 border-amber-500 text-white shadow-md scale-125'
                        : cp.risk_band === 'HIGH'
                        ? 'bg-rose-100 border-rose-400 text-rose-800'
                        : 'bg-stone-100 border-stone-300 text-stone-600 group-hover:border-amber-400'
                    }`}
                  >
                    {idx + 1}
                  </div>
                  <span className={`text-[11px] font-mono mt-2 font-medium ${isSelected ? 'text-amber-900 font-bold' : 'text-stone-500'}`}>
                    {cp.checkpoint_date}
                  </span>
                  <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded mt-0.5 ${
                    cp.risk_band === 'HIGH' ? 'text-rose-700 bg-rose-50' : 'text-stone-600 bg-stone-100'
                  }`}>
                    {cp.risk_score.toFixed(0)} pts
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Checkpoint Details & Branching Action */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Reconstructed Historical Snapshot */}
        <div className="lg:col-span-1 bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-stone-200/80 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-stone-100 pb-3">
            <div>
              <span className="text-[10px] font-mono uppercase text-stone-400 tracking-wider">Point-in-Time State</span>
              <h4 className="text-base font-bold text-stone-900 font-mono">{activeCheckpoint?.checkpoint_date}</h4>
            </div>
            <span className={`text-xs font-mono font-bold px-2.5 py-1 rounded-full ${
              activeCheckpoint?.risk_band === 'HIGH'
                ? 'bg-rose-100 text-rose-800 border border-rose-200'
                : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
            }`}>
              {activeCheckpoint?.risk_band} RISK
            </span>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between items-center text-xs py-1.5 border-b border-stone-100">
              <span className="text-stone-600">Calculated Risk Score</span>
              <span className="font-mono font-bold text-stone-900 text-sm">{activeCheckpoint?.risk_score.toFixed(1)} / 100</span>
            </div>
            <div className="flex justify-between items-center text-xs py-1.5 border-b border-stone-100">
              <span className="text-stone-600">Active Users</span>
              <span className="font-mono font-semibold text-stone-900">{activeCheckpoint?.active_users}</span>
            </div>
            <div className="flex justify-between items-center text-xs py-1.5 border-b border-stone-100">
              <span className="text-stone-600">Seat Utilization</span>
              <span className="font-mono font-semibold text-stone-900">
                {activeCheckpoint ? (activeCheckpoint.seat_utilization * 100).toFixed(1) : 0}%
              </span>
            </div>
            <div className="flex justify-between items-center text-xs py-1.5 border-b border-stone-100">
              <span className="text-stone-600">Critical Open Tickets</span>
              <span className={`font-mono font-bold ${
                (activeCheckpoint?.critical_tickets || 0) > 0 ? 'text-rose-600' : 'text-stone-900'
              }`}>
                {activeCheckpoint?.critical_tickets}
              </span>
            </div>
            <div className="flex justify-between items-center text-xs py-1.5">
              <span className="text-stone-600">Days to Contract Renewal</span>
              <span className="font-mono font-semibold text-stone-900">{activeCheckpoint?.days_to_renewal} days</span>
            </div>
          </div>

          <button
            onClick={handleSimulateBranch}
            disabled={loading || !activeCheckpoint}
            className="w-full mt-4 py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 transition-all shadow-sm"
          >
            <GitBranch className="w-4 h-4" />
            Branch Counterfactual from This Date
          </button>
        </div>

        {/* Right 2 Cols: Factual Trajectory vs Counterfactual Branch */}
        <div className="lg:col-span-2 bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-stone-200/80 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-stone-100 pb-3">
            <h4 className="font-bold text-stone-900 text-base flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-amber-700" />
              Counterfactual Branch Divergence Comparison
            </h4>
            {branchResult && (
              <span className="text-xs font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                Churn Avoidance Confirmed
              </span>
            )}
          </div>

          {!branchResult ? (
            <div className="p-12 text-center text-stone-500 border border-dashed border-stone-300 rounded-xl space-y-2">
              <RotateCcw className="w-8 h-8 text-stone-400 mx-auto" />
              <p className="text-sm font-medium text-stone-700">Select a checkpoint date and click "Branch Counterfactual"</p>
              <p className="text-xs text-stone-400">
                The simulator will replay subsequent event telemetry under the counterfactual intervention condition.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Factual Trajectory */}
                <div className="bg-rose-50/70 border border-rose-200 rounded-xl p-4 space-y-3">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-rose-800 uppercase font-mono">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    Factual Observed Trajectory (No Action)
                  </div>
                  <div className="space-y-2">
                    {branchResult.factual_trajectory.map((t, idx) => (
                      <div key={idx} className="flex justify-between items-center text-xs p-2 bg-white/80 rounded-lg border border-rose-100 font-mono">
                        <span className="text-stone-700 font-medium">{t.date}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-rose-700">{t.risk_score.toFixed(1)} pts</span>
                          <span className="text-[10px] bg-rose-100 text-rose-800 px-1.5 py-0.5 rounded">{t.risk_band}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Counterfactual Trajectory */}
                <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-4 space-y-3">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-800 uppercase font-mono">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Counterfactual Branch ({branchResult.branch_date} Intervention)
                  </div>
                  <div className="space-y-2">
                    {branchResult.counterfactual_trajectory.map((t, idx) => (
                      <div key={idx} className="flex justify-between items-center text-xs p-2 bg-white/80 rounded-lg border border-emerald-100 font-mono">
                        <span className="text-stone-700 font-medium">{t.date}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-emerald-700">{t.risk_score.toFixed(1)} pts</span>
                          <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded">{t.risk_band}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Summary Delta Metric */}
              <div className="p-4 bg-stone-900 text-stone-100 rounded-xl flex items-center justify-between font-mono text-xs">
                <span>Branch Intervention Delta at Renewal:</span>
                <span className="text-emerald-400 font-bold text-sm">
                  {branchResult.risk_delta.toFixed(1)} pts Risk Reduction
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
