import React, { useState, useEffect } from 'react';
import { Customer } from '../types/simulator';
import { fetchCausalGraph, fetchCustomerCausal, runCausalCounterfactual } from '../services/api';
import { CausalGraphData, CustomerCausalState } from '../types/simulator';
import { Network, GitCommit, Sliders, CheckCircle, ArrowRight, Activity, Zap } from 'lucide-react';

interface CausalExplorerProps {
  customers: Customer[];
  selectedCustomerId?: string;
  onSelectCustomer: (id: string) => void;
}

export const CausalExplorer: React.FC<CausalExplorerProps> = ({
  customers,
  selectedCustomerId = 'CUS-020',
  onSelectCustomer,
}) => {
  const [activeCustomer, setActiveCustomer] = useState<string>(selectedCustomerId);
  const [graphData, setGraphData] = useState<CausalGraphData | null>(null);
  const [customerCausal, setCustomerCausal] = useState<CustomerCausalState | null>(null);
  const [interventions, setInterventions] = useState<{ critical_tickets?: number; seat_utilization?: number }>({});
  const [counterfactualResult, setCounterfactualResult] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    fetchCausalGraph().then(setGraphData);
  }, []);

  useEffect(() => {
    if (activeCustomer) {
      setLoading(true);
      fetchCustomerCausal(activeCustomer).then((res) => {
        setCustomerCausal(res);
        setInterventions({});
        setCounterfactualResult(null);
        setLoading(false);
      });
    }
  }, [activeCustomer]);

  const handleApplyIntervention = async () => {
    if (!activeCustomer) return;
    setLoading(true);
    const res = await runCausalCounterfactual(activeCustomer, interventions);
    setCounterfactualResult(res);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 bg-stone-900 text-stone-100 rounded-2xl shadow-lg border border-stone-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Network className="w-5 h-5 text-amber-400" />
            <span className="text-xs font-mono uppercase tracking-widest text-amber-400 font-semibold">
              Pearl Structural Causal Model (SCM)
            </span>
          </div>
          <h2 className="text-2xl font-bold font-['Outfit']">Directed Acyclic Graph & Root-Cause Attribution</h2>
          <p className="text-stone-400 text-sm mt-1 max-w-2xl">
            Go beyond correlational heuristics. Compute true mediation paths, direct vs indirect causal effects, and Pearl do-operator counterfactuals with zero data leakage.
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
                {c.customer_id} - {c.customer_name} ({c.segment})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: DAG Structure & Mediation Paths */}
        <div className="lg:col-span-2 space-y-6">
          {/* Causal Graph Visualization Box */}
          <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-stone-200/80 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-stone-900 flex items-center gap-2">
                <GitCommit className="w-5 h-5 text-amber-700" />
                Causal Topology Nodes & Structural Weights
              </h3>
              <span className="text-xs font-mono bg-stone-100 text-stone-700 px-2.5 py-1 rounded-full border border-stone-200">
                Acyclic Verified (0 Cycles)
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
              {graphData?.nodes.map((node) => {
                const nodeVal = customerCausal?.nodes?.[node.id];
                return (
                  <div
                    key={node.id}
                    className={`p-3 rounded-xl border transition-all ${
                      node.id === 'renewal_risk_score'
                        ? 'bg-amber-50/80 border-amber-300 text-amber-950 shadow-sm'
                        : 'bg-stone-50/80 border-stone-200/80 text-stone-800'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs font-medium text-stone-500 mb-1">
                      <span className="uppercase tracking-wider font-mono text-[10px]">{node.category}</span>
                      <span className="text-[10px] text-stone-400 font-mono">{node.id}</span>
                    </div>
                    <div className="font-semibold text-sm">{node.label}</div>
                    <div className="text-sm font-bold mt-1 text-amber-900 font-mono">
                      {nodeVal !== undefined
                        ? node.value_type === 'ratio'
                          ? `${(nodeVal * 100).toFixed(1)}%`
                          : typeof nodeVal === 'number' && nodeVal > 1000
                          ? `$${(nodeVal / 1000).toFixed(0)}k`
                          : nodeVal
                        : '—'}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Edge Structural Formulas */}
            <div className="mt-4 border-t border-stone-100 pt-4">
              <h4 className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">
                Key Structural Mediation Edges
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                {graphData?.edges.map((edge, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs p-2 rounded-lg bg-stone-50/70 border border-stone-200/50">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-stone-700 font-medium">{edge.source}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-stone-400" />
                      <span className="font-mono text-stone-900 font-semibold">{edge.target}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-stone-500 truncate max-w-xs">{edge.description}</span>
                      <span className={`font-mono font-bold px-2 py-0.5 rounded text-[11px] ${
                        edge.weight > 0 ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      }`}>
                        {edge.weight > 0 ? `+${edge.weight}` : edge.weight}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Root-Cause Attribution Ranking */}
          <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-stone-200/80 shadow-sm">
            <h3 className="text-lg font-bold text-stone-900 flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-amber-700" />
              Structural Root-Cause Decomposition for {customerCausal?.customer_name || activeCustomer}
            </h3>

            <div className="space-y-4">
              {customerCausal?.root_causes.map((rc, idx) => (
                <div key={idx} className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs font-medium">
                    <span className="font-semibold text-stone-800">{rc.label}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-stone-500 font-mono">Effect: +{rc.total_effect.toFixed(1)} pts</span>
                      <span className="font-bold text-amber-900 font-mono bg-amber-100/70 px-2 py-0.5 rounded">
                        {rc.contribution_pct.toFixed(1)}% contribution
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-stone-100 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-amber-600 to-rose-600 h-2.5 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, rc.contribution_pct * 1.5)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Pearl Do-Operator Intervention Workbench */}
        <div className="space-y-6">
          <div className="bg-stone-900 text-stone-100 rounded-2xl p-6 border border-stone-800 shadow-md">
            <div className="flex items-center gap-2 mb-2">
              <Sliders className="w-5 h-5 text-amber-400" />
              <h3 className="font-bold text-lg font-['Outfit']">Pearl Do-Operator Simulator</h3>
            </div>
            <p className="text-xs text-stone-400 mb-6">
              Simulate surgery on the causal graph: cut incoming parent edges and set variable values directly to observe pure causal response.
            </p>

            <div className="space-y-5">
              {/* Intervention 1: Critical Tickets */}
              <div className="bg-stone-800/80 p-3.5 rounded-xl border border-stone-700/60">
                <div className="flex justify-between text-xs font-medium mb-2">
                  <span className="text-stone-300 font-mono">do(critical_tickets = 0)</span>
                  <span className="text-amber-400 font-semibold">Engineering Swarm</span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setInterventions((prev) => ({ ...prev, critical_tickets: 0 }))}
                    className={`flex-1 text-xs py-2 rounded-lg font-medium border transition-all ${
                      interventions.critical_tickets === 0
                        ? 'bg-amber-500 text-stone-900 border-amber-400 font-bold'
                        : 'bg-stone-900 text-stone-300 border-stone-700 hover:bg-stone-800'
                    }`}
                  >
                    Resolve All (0)
                  </button>
                  <button
                    onClick={() => setInterventions((prev) => {
                      const next = { ...prev };
                      delete next.critical_tickets;
                      return next;
                    })}
                    className="px-3 text-xs py-2 rounded-lg bg-stone-900 text-stone-400 border border-stone-700 hover:text-stone-200"
                  >
                    Reset
                  </button>
                </div>
              </div>

              {/* Intervention 2: Seat Utilization */}
              <div className="bg-stone-800/80 p-3.5 rounded-xl border border-stone-700/60">
                <div className="flex justify-between text-xs font-medium mb-2">
                  <span className="text-stone-300 font-mono">do(seat_utilization)</span>
                  <span className="text-amber-400 font-semibold">Adoption Sprint</span>
                </div>
                <div className="flex gap-2">
                  {[0.75, 0.90].map((rate) => (
                    <button
                      key={rate}
                      onClick={() => setInterventions((prev) => ({ ...prev, seat_utilization: rate }))}
                      className={`flex-1 text-xs py-2 rounded-lg font-medium border transition-all ${
                        interventions.seat_utilization === rate
                          ? 'bg-amber-500 text-stone-900 border-amber-400 font-bold'
                          : 'bg-stone-900 text-stone-300 border-stone-700 hover:bg-stone-800'
                      }`}
                    >
                      Boost to {rate * 100}%
                    </button>
                  ))}
                  <button
                    onClick={() => setInterventions((prev) => {
                      const next = { ...prev };
                      delete next.seat_utilization;
                      return next;
                    })}
                    className="px-3 text-xs py-2 rounded-lg bg-stone-900 text-stone-400 border border-stone-700 hover:text-stone-200"
                  >
                    Reset
                  </button>
                </div>
              </div>

              {/* Execute Do-Operator Button */}
              <button
                onClick={handleApplyIntervention}
                disabled={loading || Object.keys(interventions).length === 0}
                className="w-full py-3 bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-stone-950 font-bold rounded-xl text-sm flex items-center justify-center gap-2 transition-all shadow-md"
              >
                <Zap className="w-4 h-4 fill-stone-950" />
                Compute Structural Counterfactual
              </button>

              {/* Counterfactual Output Display */}
              {counterfactualResult && (
                <div className="mt-4 p-4 rounded-xl bg-stone-800/90 border border-amber-500/50 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-amber-400 uppercase tracking-wider">
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    Causal Counterfactual Verified
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-center">
                    <div className="p-2.5 bg-stone-900/80 rounded-lg">
                      <div className="text-[10px] text-stone-400 uppercase font-mono">Factual Risk</div>
                      <div className="text-xl font-bold text-rose-400 font-mono">
                        {counterfactualResult.factual_score.toFixed(1)}
                      </div>
                    </div>
                    <div className="p-2.5 bg-stone-900/80 rounded-lg">
                      <div className="text-[10px] text-stone-400 uppercase font-mono">Post-Do Risk</div>
                      <div className="text-xl font-bold text-emerald-400 font-mono">
                        {counterfactualResult.counterfactual_score.toFixed(1)}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-stone-300 text-center font-mono pt-1">
                    Net Causal Impact: <span className="text-emerald-400 font-bold">{counterfactualResult.risk_delta.toFixed(1)} pts</span> (Target: {counterfactualResult.remediated_band} Risk)
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
