import React from 'react';
import { CustomerAssessment, SimulatorTab } from '../types/simulator';
import { 
  TrendingUp, 
  AlertTriangle, 
  ShieldAlert, 
  Clock, 
  ArrowRight, 
  DollarSign, 
  Sliders, 
  CheckCircle2,
  Users
} from 'lucide-react';

interface DashboardViewProps {
  assessments: CustomerAssessment[];
  onSelectCustomer: (assessment: CustomerAssessment) => void;
  onNavigateTab: (tab: SimulatorTab) => void;
  onStartScenarioWithCustomer: (assessment: CustomerAssessment) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  assessments,
  onSelectCustomer,
  onNavigateTab,
  onStartScenarioWithCustomer,
}) => {
  const highRisk = assessments.filter((a) => a.risk_level === 'High');
  const mediumRisk = assessments.filter((a) => a.risk_level === 'Medium');
  const lowRisk = assessments.filter((a) => a.risk_level === 'Low');

  const totalArr = assessments.reduce(
    (sum, a) => sum + (a.contract?.annual_contract_value || 0),
    0
  );

  const highRiskArr = highRisk.reduce(
    (sum, a) => sum + (a.contract?.annual_contract_value || 0),
    0
  );

  // Highest risk priority account
  const priorityAccount = [...assessments].sort((a, b) => b.risk_score - a.risk_score)[0];

  // Critical tickets count
  const criticalTicketsCount = assessments.reduce((count, a) => {
    return count + a.factors.filter((f) => f.name === 'Unresolved critical support').length;
  }, 0);

  // Donut SVG angles
  const totalCount = assessments.length || 1;
  const highAngle = (highRisk.length / totalCount) * 360;
  const medAngle = (mediumRisk.length / totalCount) * 360;
  const lowAngle = (lowRisk.length / totalCount) * 360;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Bento Row: Priority Spotlight (2 cols) + Interactive Donut (1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Priority Account Spotlight Card */}
        {priorityAccount && (
          <div className="lg:col-span-2 cockpit-card p-6 md:p-8 flex flex-col justify-between relative overflow-hidden bg-gradient-to-br from-[#f8f3e8] via-[#f5eee0] to-slate-50/60">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
                  <span className="text-xs font-bold font-mono tracking-wider text-rose-600 uppercase">
                    PRIORITY ACTION REQUIRED
                  </span>
                </div>
                <span className="px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-xs font-bold mono-num">
                  {priorityAccount.risk_score} PTS HIGH RISK
                </span>
              </div>

              <div>
                <h2 className="text-2xl md:text-3xl font-bold text-[#2d251e] tracking-tight">
                  {priorityAccount.customer.customer_name}
                </h2>
                <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-[#786c5c]">
                  <span className="font-semibold text-[#4d4236]">
                    {priorityAccount.customer.segment}
                  </span>
                  <span>•</span>
                  <span>{priorityAccount.customer.industry}</span>
                  <span>•</span>
                  <span>{priorityAccount.customer.region}</span>
                  <span>•</span>
                  <span className="font-bold text-[#2d251e] mono-num">
                    ${((priorityAccount.contract?.annual_contract_value || 0) / 1000).toFixed(0)}k ARR
                  </span>
                </div>
              </div>

              {/* Primary Risk Drivers Waterfall Preview */}
              <div className="space-y-2 pt-2">
                <span className="text-xs font-semibold text-[#786c5c] uppercase tracking-wide">
                  Top Active Risk Drivers:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {priorityAccount.factors.slice(0, 4).map((f, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-[#ece3cf] border border-[#d6c8ad]/80 text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between font-semibold text-[#3b3229]">
                        <span>{f.name}</span>
                        <span className="text-rose-600 font-bold mono-num">+{f.points} pts</span>
                      </div>
                      <p className="text-[11px] text-[#786c5c] leading-snug truncate" title={f.explanation}>
                        {f.explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom Actions */}
            <div className="pt-6 flex flex-wrap items-center gap-3 border-t border-[#dfd3bc] mt-6">
              <button
                onClick={() => onStartScenarioWithCustomer(priorityAccount)}
                className="px-5 py-2.5 rounded-xl bg-orange-600 text-white font-semibold text-xs flex items-center gap-2 hover:bg-orange-700 apple-pressable transition-all shadow-[0_2px_10px_rgba(37,99,235,0.25)]"
              >
                <Sliders className="w-4 h-4" />
                <span>Simulate 60fps Intervention in Scenario Lab</span>
              </button>

              <button
                onClick={() => onSelectCustomer(priorityAccount)}
                className="px-4 py-2.5 rounded-xl bg-[#e4dac4] hover:bg-[#ded2ba] text-[#3b3229] font-semibold text-xs flex items-center gap-1.5 apple-pressable transition-all"
              >
                <span>View Customer 360</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Donut Risk Breakdown Card */}
        <div className="cockpit-card p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#dfd3bc]">
              <h3 className="text-sm font-bold text-[#2d251e]">Portfolio Risk Distribution</h3>
              <span className="text-xs text-[#786c5c] mono-num">{assessments.length} Accounts</span>
            </div>

            {/* Interactive Donut Graphic */}
            <div className="relative w-44 h-44 mx-auto my-6 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="38"
                  stroke="#10b981"
                  strokeWidth="14"
                  strokeDasharray={`${(lowRisk.length / totalCount) * 238.7} 238.7`}
                  strokeDashoffset="0"
                  fill="transparent"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="38"
                  stroke="#f59e0b"
                  strokeWidth="14"
                  strokeDasharray={`${(mediumRisk.length / totalCount) * 238.7} 238.7`}
                  strokeDashoffset={`-${(lowRisk.length / totalCount) * 238.7}`}
                  fill="transparent"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="38"
                  stroke="#ef4444"
                  strokeWidth="14"
                  strokeDasharray={`${(highRisk.length / totalCount) * 238.7} 238.7`}
                  strokeDashoffset={`-${((lowRisk.length + mediumRisk.length) / totalCount) * 238.7}`}
                  fill="transparent"
                />
              </svg>

              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="text-2xl font-bold text-[#2d251e] mono-num">
                  {highRisk.length}
                </span>
                <span className="text-[10px] font-bold text-rose-600 uppercase tracking-wider">
                  At Risk
                </span>
              </div>
            </div>
          </div>

          {/* Breakdown Legend */}
          <div className="space-y-2 pt-2 border-t border-[#dfd3bc] text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                <span className="text-[#4d4236] font-medium">High Risk (&ge;55 pts)</span>
              </div>
              <span className="font-bold text-[#2d251e] mono-num">
                {highRisk.length} ({((highRisk.length / totalCount) * 100).toFixed(0)}%)
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <span className="text-[#4d4236] font-medium">Medium Risk (30-54 pts)</span>
              </div>
              <span className="font-bold text-[#2d251e] mono-num">
                {mediumRisk.length} ({((mediumRisk.length / totalCount) * 100).toFixed(0)}%)
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span className="text-[#4d4236] font-medium">Low Risk (&lt;30 pts)</span>
              </div>
              <span className="font-bold text-[#2d251e] mono-num">
                {lowRisk.length} ({((lowRisk.length / totalCount) * 100).toFixed(0)}%)
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 4 Frosted Metric Cards Bento Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="cockpit-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#786c5c] uppercase tracking-wider">
              Total Portfolio ARR
            </span>
            <DollarSign className="w-4 h-4 text-orange-600" />
          </div>
          <div className="text-2xl md:text-3xl font-bold text-[#2d251e] mono-num">
            ${(totalArr / 1_000_000).toFixed(2)}M
          </div>
          <p className="text-xs text-[#786c5c]">Across 30 active customer contracts</p>
        </div>

        <div className="cockpit-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#786c5c] uppercase tracking-wider">
              High-Risk ARR Exposure
            </span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl md:text-3xl font-bold text-rose-600 mono-num">
            ${(highRiskArr / 1_000).toFixed(0)}k
          </div>
          <p className="text-xs text-[#786c5c]">
            {((highRiskArr / totalArr) * 100).toFixed(1)}% of total enterprise portfolio
          </p>
        </div>

        <div className="cockpit-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#786c5c] uppercase tracking-wider">
              Critical Escalations
            </span>
            <ShieldAlert className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl md:text-3xl font-bold text-[#2d251e] mono-num">
            {criticalTicketsCount}
          </div>
          <p className="text-xs text-[#786c5c]">Open P1 tickets impacting renewal</p>
        </div>

        <div className="cockpit-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#786c5c] uppercase tracking-wider">
              Avg Days to Renewal
            </span>
            <Clock className="w-4 h-4 text-[#5e5346]" />
          </div>
          <div className="text-2xl md:text-3xl font-bold text-[#2d251e] mono-num">
            68d
          </div>
          <p className="text-xs text-[#786c5c]">Earliest renewal in 18 days</p>
        </div>
      </div>
    </div>
  );
};
