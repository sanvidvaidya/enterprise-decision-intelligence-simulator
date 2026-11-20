import React, { useState, useEffect } from 'react';
import { Customer, CompetitorProfile, GameTheoreticEquilibrium } from '../types/simulator';
import { fetchCompetitors, fetchEquilibriumSimulation } from '../services/api';
import { Swords, ShieldAlert, Award, TrendingDown, Target, HelpCircle } from 'lucide-react';

interface GameTheoryCockpitProps {
  customers: Customer[];
  onSelectCustomer: (id: string) => void;
}

export const GameTheoryCockpit: React.FC<GameTheoryCockpitProps> = ({
  customers,
  onSelectCustomer,
}) => {
  const [competitors, setCompetitors] = useState<CompetitorProfile[]>([]);
  const [equilibrium, setEquilibrium] = useState<GameTheoreticEquilibrium | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('PROACTIVE_DISCOUNT_AND_CSM');
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    fetchCompetitors().then(setCompetitors);
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchEquilibriumSimulation(selectedStrategy).then((res) => {
      setEquilibrium(res);
      setLoading(false);
    });
  }, [selectedStrategy]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 bg-stone-900 text-stone-100 rounded-2xl shadow-lg border border-stone-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Swords className="w-5 h-5 text-amber-400" />
            <span className="text-xs font-mono uppercase tracking-widest text-amber-400 font-semibold">
              Game-Theoretic Market Dynamics
            </span>
          </div>
          <h2 className="text-2xl font-bold font-['Outfit']">Nash Equilibrium & Competitor Poaching Simulation</h2>
          <p className="text-stone-400 text-sm mt-1 max-w-2xl">
            Simulate competitor predatory pricing, migration subsidies, and counter-moves. Surface the hidden unmodeled competitor churn gap that static risk models miss.
          </p>
        </div>

        {/* Strategy Selector */}
        <div className="bg-stone-800/80 p-2.5 rounded-xl border border-stone-700/80 flex items-center gap-3">
          <label className="text-xs text-stone-400 font-medium">Vendor Strategy:</label>
          <select
            value={selectedStrategy}
            onChange={(e) => setSelectedStrategy(e.target.value)}
            className="bg-stone-900 border border-stone-700 text-stone-200 text-sm rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-amber-500 outline-none"
          >
            <option value="NO_CHANGE">Status Quo (No Change)</option>
            <option value="PRICE_INCREASE">Contract Price Increase (+8%)</option>
            <option value="PROACTIVE_DISCOUNT_AND_CSM">Proactive Incentive & Dedicated CSM</option>
            <option value="EXECUTIVE_LOCK_IN">Executive Multi-Year Lock-In</option>
          </select>
        </div>
      </div>

      {/* KPI Cards: Naive vs Game-Theoretic Churn Gap */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/90 backdrop-blur-md rounded-2xl p-5 border border-stone-200/80 shadow-sm">
          <div className="flex items-center justify-between text-xs text-stone-500 font-mono mb-2">
            <span>STATIC NAIVE CHURN RISK</span>
            <HelpCircle className="w-3.5 h-3.5 text-stone-400" />
          </div>
          <div className="text-3xl font-bold text-stone-900 font-mono">
            ${((equilibrium?.total_acv_at_risk_naive || 0) / 1000).toFixed(0)}k
          </div>
          <p className="text-xs text-stone-500 mt-1">Based solely on telemetry & usage decline</p>
        </div>

        <div className="bg-white/90 backdrop-blur-md rounded-2xl p-5 border border-stone-200/80 shadow-sm">
          <div className="flex items-center justify-between text-xs text-stone-500 font-mono mb-2">
            <span>GAME-THEORETIC RISK EXPOSURE</span>
            <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
          </div>
          <div className="text-3xl font-bold text-rose-700 font-mono">
            ${((equilibrium?.total_acv_at_risk_game_theoretic || 0) / 1000).toFixed(0)}k
          </div>
          <p className="text-xs text-stone-500 mt-1">Incorporates competitor poaching incentives</p>
        </div>

        <div className="bg-amber-50/80 border border-amber-300 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-xs text-amber-900 font-mono font-semibold mb-2">
            <span>UNMODELED COMPETITOR CHURN GAP</span>
            <TrendingDown className="w-4 h-4 text-amber-700" />
          </div>
          <div className="text-3xl font-bold text-amber-950 font-mono">
            +${((equilibrium?.unmodeled_competitor_churn_gap || 0) / 1000).toFixed(0)}k
          </div>
          <p className="text-xs text-amber-800 mt-1">Hidden exposure invisible to traditional CS dashboards</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Payoff Matrix & Vulnerability Rankings */}
        <div className="lg:col-span-2 space-y-6">
          {/* Strategic Payoff Matrix */}
          <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-stone-200/80 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-stone-900 text-base flex items-center gap-2">
                <Target className="w-5 h-5 text-amber-700" />
                Strategic Game Payoff Matrix (Vendor vs Competitor Moves)
              </h3>
              <span className="text-xs font-mono font-bold bg-amber-100 text-amber-900 px-2.5 py-1 rounded-full">
                Nash Equilibrium Solved
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="border-b border-stone-200 text-stone-500 font-mono bg-stone-50">
                    <th className="p-3">Vendor Strategy</th>
                    <th className="p-3">Competitor: Do Nothing</th>
                    <th className="p-3">Competitor: Price War</th>
                    <th className="p-3">Competitor: Targeted Poach</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100 font-mono">
                  {equilibrium?.payoff_matrix && Object.entries(equilibrium.payoff_matrix).map(([stratKey, moves]) => {
                    const isEquilibrium = stratKey === equilibrium.vendor_equilibrium_strategy;
                    return (
                      <tr key={stratKey} className={`${isEquilibrium ? 'bg-amber-50/70 font-semibold' : 'hover:bg-stone-50/50'}`}>
                        <td className="p-3 font-sans font-medium text-stone-900 flex items-center gap-2">
                          {stratKey.replace(/_/g, ' ')}
                          {isEquilibrium && <Award className="w-4 h-4 text-amber-600 inline" />}
                        </td>
                        <td className={`p-3 ${moves.DO_NOTHING >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                          ${(moves.DO_NOTHING / 1000).toFixed(0)}k
                        </td>
                        <td className={`p-3 ${moves.PRICE_WAR >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                          ${(moves.PRICE_WAR / 1000).toFixed(0)}k
                        </td>
                        <td className={`p-3 ${moves.TARGETED_POACH >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                          ${(moves.TARGETED_POACH / 1000).toFixed(0)}k
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Account Vulnerability Index (CVI) Table */}
          <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-stone-200/80 shadow-sm">
            <h3 className="font-bold text-stone-900 text-base mb-4 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-700" />
              Highest Vulnerability Accounts (Customer Vulnerability Index)
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-stone-200 text-stone-500 font-mono">
                    <th className="pb-2">Account</th>
                    <th className="pb-2">Segment</th>
                    <th className="pb-2">ACV</th>
                    <th className="pb-2">CVI Score</th>
                    <th className="pb-2">Primary Competitor Threat</th>
                    <th className="pb-2">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100 font-mono">
                  {equilibrium?.vulnerable_accounts.map((acc) => (
                    <tr key={acc.customer_id} className="hover:bg-stone-50/70 transition-colors">
                      <td className="py-2.5 font-sans font-medium text-stone-900">{acc.customer_name}</td>
                      <td className="py-2.5 text-stone-500">{acc.segment}</td>
                      <td className="py-2.5 font-semibold text-stone-900">${(acc.annual_contract_value / 1000).toFixed(0)}k</td>
                      <td className="py-2.5">
                        <span className="font-bold text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded">
                          {acc.cvi_score.toFixed(1)} / 100
                        </span>
                      </td>
                      <td className="py-2.5 text-stone-700 font-sans">{acc.top_competitor_threat}</td>
                      <td className="py-2.5">
                        <button
                          onClick={() => onSelectCustomer(acc.customer_id)}
                          className="text-[11px] font-sans font-semibold text-amber-800 hover:text-amber-900 underline"
                        >
                          Inspect & Shield
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Col: Competitor Profiles */}
        <div className="space-y-4">
          <div className="bg-stone-900 text-stone-100 rounded-2xl p-6 border border-stone-800 shadow-md">
            <h3 className="font-bold text-lg font-['Outfit'] mb-2 flex items-center gap-2">
              <Swords className="w-5 h-5 text-amber-400" />
              Active Competitor Threat Profiles
            </h3>
            <p className="text-xs text-stone-400 mb-4">
              Calibrated displacement models based on observed market intelligence and RFP takeout tactics.
            </p>

            <div className="space-y-3">
              {competitors.map((comp) => (
                <div key={comp.id} className="p-3.5 bg-stone-800/80 rounded-xl border border-stone-700/60 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-sm text-stone-100">{comp.name}</span>
                    <span className="text-[10px] font-mono bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded border border-amber-500/30">
                      {comp.tier}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
                    <div className="text-stone-400">
                      Discount: <span className="text-rose-400 font-bold">{comp.pricing_discount_pct}%</span>
                    </div>
                    <div className="text-stone-400">
                      Subsidy: <span className="text-amber-400 font-bold">{comp.migration_subsidy_acv_pct}% ACV</span>
                    </div>
                  </div>
                  <div className="text-[11px] text-stone-400">
                    Targets: <span className="text-stone-300">{comp.target_segments.join(', ')}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
