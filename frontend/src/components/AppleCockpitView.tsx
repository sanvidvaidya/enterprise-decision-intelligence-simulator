import React from 'react';
import { CustomerAssessment } from '../types/simulator';
import { SimulatorTab } from '../types/simulator';
import { 
  DollarSign, 
  AlertTriangle, 
  ShieldAlert, 
  Clock, 
  Sliders, 
  ArrowRight, 
  Sparkles,
  TrendingUp,
  CheckCircle2
} from 'lucide-react';

interface AppleCockpitViewProps {
  assessments: CustomerAssessment[];
  onSelectCustomer: (assessment: CustomerAssessment) => void;
  onNavigateTab: (tab: SimulatorTab) => void;
  onStartScenario: (assessment: CustomerAssessment) => void;
}

export const AppleCockpitView: React.FC<AppleCockpitViewProps> = ({
  assessments,
  onSelectCustomer,
  onNavigateTab,
  onStartScenario,
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

  const priorityAccount = [...assessments].sort((a, b) => b.risk_score - a.risk_score)[0];

  const criticalTicketsCount = assessments.reduce((count, a) => {
    return count + a.factors.filter((f) => f.name === 'Unresolved critical support').length;
  }, 0);

  const totalCount = assessments.length || 1;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16 pt-16">
      {/* Grand Hero Display */}
      <div className="text-center space-y-3 max-w-3xl mx-auto pt-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 border border-orange-200 text-orange-700 text-xs font-semibold tracking-wide uppercase">
          <Sparkles className="w-3.5 h-3.5 text-orange-600" />
          <span>Evidence-Backed SaaS Retention Engine</span>
        </div>

        <h1 className="text-4xl md:text-6xl font-display font-extrabold tracking-tight apple-title-gradient leading-tight">
          Autonomous Retention. Zero Hallucination.
        </h1>

        <p className="text-[#5e5346] text-sm md:text-base leading-relaxed">
          Deterministic decision intelligence across CRM, warehouse telemetry, and support escalations. 
          Certify early renewal risk 60 days ahead with mathematically explainable factor points.
        </p>
      </div>

      {/* Bento Grid: Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Spotlight Card: Juniper Labs */}
        {priorityAccount && (
          <div className="lg:col-span-2 apple-cockpit-card p-6 md:p-8 flex flex-col justify-between relative overflow-hidden bg-gradient-to-br from-[#f8f3e8] via-[#f5eee0] to-rose-50/20">
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-50 border border-rose-200 text-rose-700 text-xs font-bold uppercase tracking-wider">
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                  <span>HIGHEST EXPOSURE PRIORITY ACCOUNT</span>
                </div>

                <span className="px-3 py-1 rounded-full bg-rose-500 text-white font-bold text-xs mono-num shadow-sm">
                  {priorityAccount.risk_score} PTS HIGH RISK
                </span>
              </div>

              <div>
                <h2 className="text-3xl md:text-4xl font-display font-bold text-[#2d251e] tracking-tight">
                  {priorityAccount.customer.customer_name}
                </h2>
                <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-[#786c5c] font-medium">
                  <span className="font-bold text-[#3b3229]">{priorityAccount.customer.segment}</span>
                  <span>•</span>
                  <span>{priorityAccount.customer.industry}</span>
                  <span>•</span>
                  <span>{priorityAccount.customer.region}</span>
                  <span>•</span>
                  <span className="font-bold text-orange-600 mono-num">
                    ${((priorityAccount.contract?.annual_contract_value || 0) / 1000).toFixed(0)}k ARR
                  </span>
                </div>
              </div>

              {/* Factor Waterfall Chips */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-[#786c5c] uppercase tracking-wide">
                  Active Risk Point Drivers:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {priorityAccount.factors.slice(0, 4).map((f, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-2xl bg-[#ece3cf]/80 border border-[#d6c8ad]/80 space-y-1"
                    >
                      <div className="flex items-center justify-between font-bold text-[#2d251e] text-xs">
                        <span>{f.name}</span>
                        <span className="text-rose-600 mono-num">+{f.points} pts</span>
                      </div>
                      <p className="text-[11px] text-[#786c5c] leading-snug truncate" title={f.explanation}>
                        {f.explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="pt-6 border-t border-[#dfd3bc] mt-6 flex flex-wrap items-center gap-3">
              <button
                onClick={() => onStartScenario(priorityAccount)}
                className="px-6 py-3 rounded-2xl bg-orange-600 text-white font-semibold text-xs flex items-center gap-2 hover:bg-orange-700 apple-spring-press shadow-[0_4px_14px_rgba(37,99,235,0.3)] transition-all"
              >
                <Sliders className="w-4 h-4" />
                <span>Simulate 60fps Intervention in Scenario Lab</span>
              </button>

              <button
                onClick={() => onSelectCustomer(priorityAccount)}
                className="px-4 py-3 rounded-2xl bg-[#e4dac4] hover:bg-[#ded2ba] text-[#3b3229] font-semibold text-xs flex items-center gap-1.5 apple-spring-press transition-all"
              >
                <span>Customer 360</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Triple Concentric Ring Risk Dial */}
        <div className="apple-cockpit-card p-6 md:p-8 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-[#dfd3bc] pb-3">
              <h3 className="text-base font-bold text-[#2d251e]">Portfolio Risk Concentric Rings</h3>
              <span className="text-xs text-[#786c5c] mono-num font-semibold">{assessments.length} Accounts</span>
            </div>

            {/* Concentric Multi-Ring SVG */}
            <div className="relative w-48 h-48 mx-auto my-2 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                {/* Outer Ring: Low Risk */}
                <circle cx="50" cy="50" r="42" stroke="#e2e8f0" strokeWidth="6" fill="transparent" />
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  stroke="#10b981"
                  strokeWidth="6"
                  strokeDasharray={`${(lowRisk.length / totalCount) * 263.9} 263.9`}
                  strokeLinecap="round"
                  fill="transparent"
                />

                {/* Middle Ring: Medium Risk */}
                <circle cx="50" cy="50" r="32" stroke="#e2e8f0" strokeWidth="6" fill="transparent" />
                <circle
                  cx="50"
                  cy="50"
                  r="32"
                  stroke="#f59e0b"
                  strokeWidth="6"
                  strokeDasharray={`${(mediumRisk.length / totalCount) * 201.0} 201.0`}
                  strokeLinecap="round"
                  fill="transparent"
                />

                {/* Inner Ring: High Risk */}
                <circle cx="50" cy="50" r="22" stroke="#e2e8f0" strokeWidth="6" fill="transparent" />
                <circle
                  cx="50"
                  cy="50"
                  r="22"
                  stroke="#ef4444"
                  strokeWidth="6"
                  strokeDasharray={`${(highRisk.length / totalCount) * 138.2} 138.2`}
                  strokeLinecap="round"
                  fill="transparent"
                />
              </svg>

              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="text-3xl font-display font-bold text-[#2d251e] mono-num">
                  {highRisk.length}
                </span>
                <span className="text-[10px] font-bold text-rose-600 uppercase tracking-wider">
                  HIGH RISK
                </span>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="space-y-2 pt-2 border-t border-[#dfd3bc] text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-medium text-[#4d4236]">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                <span>High Risk (&ge;55 pts)</span>
              </div>
              <span className="font-bold text-[#2d251e] mono-num">{highRisk.length} accounts</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-medium text-[#4d4236]">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <span>Medium Risk (30-54 pts)</span>
              </div>
              <span className="font-bold text-[#2d251e] mono-num">{mediumRisk.length} accounts</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-medium text-[#4d4236]">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span>Low Risk (&lt;30 pts)</span>
              </div>
              <span className="font-bold text-[#2d251e] mono-num">{lowRisk.length} accounts</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4 Frosted Specular Bento Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="apple-cockpit-card p-6 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#8f8270] uppercase tracking-wider">
              Total Portfolio ARR
            </span>
            <DollarSign className="w-4 h-4 text-orange-600" />
          </div>
          <div className="text-3xl font-display font-bold text-[#2d251e] mono-num">
            ${(totalArr / 1_000_000).toFixed(2)}M
          </div>
          <p className="text-xs text-[#786c5c]">Across 30 active SaaS customer contracts</p>
        </div>

        <div className="apple-cockpit-card p-6 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#8f8270] uppercase tracking-wider">
              High-Risk ARR Exposure
            </span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-3xl font-display font-bold text-rose-600 mono-num">
            ${(highRiskArr / 1_000).toFixed(0)}k
          </div>
          <p className="text-xs text-[#786c5c]">
            {((highRiskArr / totalArr) * 100).toFixed(1)}% of total enterprise portfolio
          </p>
        </div>

        <div className="apple-cockpit-card p-6 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#8f8270] uppercase tracking-wider">
              Critical Escalations
            </span>
            <ShieldAlert className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-3xl font-display font-bold text-[#2d251e] mono-num">
            {criticalTicketsCount}
          </div>
          <p className="text-xs text-[#786c5c]">Unresolved P1 tickets directly blocking renewal</p>
        </div>

        <div className="apple-cockpit-card p-6 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#8f8270] uppercase tracking-wider">
              Avg Contract Runway
            </span>
            <Clock className="w-4 h-4 text-[#5e5346]" />
          </div>
          <div className="text-3xl font-display font-bold text-[#2d251e] mono-num">
            68 days
          </div>
          <p className="text-xs text-[#786c5c]">Optimal window for turnaround playbooks</p>
        </div>
      </div>
    </div>
  );
};
