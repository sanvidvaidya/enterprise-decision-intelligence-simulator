import React from 'react';
import { CustomerAssessment } from '../types/simulator';
import { X, Sliders, Mail, ShieldAlert, Sparkles, Building2, MapPin, Users, Calendar, ArrowUpRight, DollarSign, CheckCircle2 } from 'lucide-react';

interface AppleCustomerSheetProps {
  assessment: CustomerAssessment | null;
  onClose: () => void;
  onOpenScenarioLab: (assessment: CustomerAssessment) => void;
}

export const AppleCustomerSheet: React.FC<AppleCustomerSheetProps> = ({
  assessment,
  onClose,
  onOpenScenarioLab,
}) => {
  if (!assessment) return null;

  const { customer, contract, risk_score, risk_level, factors, recommended_actions } = assessment;
  const isHigh = risk_level === 'High';
  const isMed = risk_level === 'Medium';

  return (
    <div className="fixed inset-0 z-50 flex justify-end animate-in fade-in duration-200">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
      />

      {/* Slide-over panel */}
      <div className="relative w-full max-w-xl bg-[#f8f3e8]/95 backdrop-blur-2xl border-l border-[#d6c8ad] shadow-2xl z-10 flex flex-col h-full animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="p-6 pb-5 border-b border-[#dfd3bc] flex items-start justify-between bg-[#ece3cf]/50">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-mono text-[11px] font-semibold text-[#8f8270] bg-[#e4dac4] px-2 py-0.5 rounded-md">
                {customer.customer_id}
              </span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-bold font-mono border ${
                  isHigh
                    ? 'bg-rose-50 text-rose-700 border-rose-200 shadow-[0_0_12px_rgba(244,63,94,0.15)]'
                    : isMed
                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                }`}
              >
                {risk_score} PTS • {risk_level.toUpperCase()}
              </span>
            </div>
            <h2 className="text-2xl font-black text-[#1f1a16] font-display tracking-tight">
              {customer.customer_name}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full text-[#8f8270] hover:text-[#3b3229] hover:bg-[#e4dac4] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Account Details Tile */}
          <div className="apple-card p-5 space-y-4">
            <div className="text-[11px] font-bold text-[#8f8270] tracking-wider uppercase font-mono">
              Account Overview
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2.5">
                <Building2 className="w-4 h-4 text-[#8f8270]" />
                <div>
                  <div className="text-[10px] text-[#8f8270] font-semibold uppercase">Industry / Tier</div>
                  <div className="text-xs font-bold text-[#3b3229]">{customer.industry} • {customer.segment}</div>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <MapPin className="w-4 h-4 text-[#8f8270]" />
                <div>
                  <div className="text-[10px] text-[#8f8270] font-semibold uppercase">Region</div>
                  <div className="text-xs font-bold text-[#3b3229]">{customer.region}</div>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <Users className="w-4 h-4 text-[#8f8270]" />
                <div>
                  <div className="text-[10px] text-[#8f8270] font-semibold uppercase">Employees</div>
                  <div className="text-xs font-bold text-[#3b3229] font-mono">{customer.employee_count.toLocaleString()}</div>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <Mail className="w-4 h-4 text-orange-600" />
                <div>
                  <div className="text-[10px] text-[#8f8270] font-semibold uppercase">Account Manager</div>
                  <div className="text-xs font-bold text-[#3b3229]">{customer.account_manager_name || 'Assigned Lead'}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Contract Details */}
          {contract && (
            <div className="apple-card p-5 bg-gradient-to-br from-[#f8f3e8] to-amber-50/40 border-orange-200/60">
              <div className="text-[11px] font-bold text-orange-600 tracking-wider uppercase font-mono mb-3">
                Commercial Runway
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-[10px] text-[#8f8270] font-semibold uppercase">Annual Contract Value</div>
                  <div className="text-2xl font-black text-[#2d251e] font-mono tracking-tight">
                    ${contract.annual_contract_value.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-[#8f8270] font-semibold uppercase">Renewal Horizon</div>
                  <div className="text-base font-bold text-[#3b3229] font-mono mt-1">
                    {contract.renewal_date}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Transparent Risk Waterfall */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-[11px] font-bold text-[#8f8270] tracking-wider uppercase font-mono">
                Risk Point Waterfall ({factors.length} Drivers)
              </div>
              <span className="text-xs font-mono font-bold text-rose-600">
                +{risk_score} Total Points
              </span>
            </div>

            <div className="space-y-2.5">
              {factors.length === 0 ? (
                <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-100 text-xs text-emerald-800 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Clean health posture: No penalty risk factors currently active.</span>
                </div>
              ) : (
                factors.map((f, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-[#f8f3e8] border border-[#dfd3bc] shadow-sm hover:border-[#d6c8ad] transition-all space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[#2d251e]">{f.name}</span>
                      <span className="font-mono text-xs font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-100">
                        +{f.points} pts
                      </span>
                    </div>
                    <p className="text-xs text-[#5e5346] leading-relaxed font-sans">{f.explanation}</p>
                    <div className="text-[10px] font-mono text-[#8f8270]">
                      Audit Records: {f.evidence_record_ids.join(', ')}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recommended Playbooks */}
          <div className="space-y-3">
            <div className="text-[11px] font-bold text-[#8f8270] tracking-wider uppercase font-mono">
              Actionable Playbooks
            </div>
            <div className="space-y-2">
              {recommended_actions.map((action, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-2xl bg-orange-50/50 border border-orange-200 text-xs text-[#3b3229] flex items-start gap-3"
                >
                  <Sparkles className="w-4 h-4 text-orange-600 shrink-0 mt-0.5" />
                  <span className="font-medium leading-relaxed">{action}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-[#dfd3bc] bg-[#ece3cf]/80 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-[#5e5346] hover:text-[#2d251e] font-semibold text-xs transition-colors"
          >
            Close
          </button>
          <button
            onClick={() => {
              onClose();
              onOpenScenarioLab(assessment);
            }}
            className="px-5 py-2.5 rounded-full bg-orange-600 text-white font-semibold text-xs flex items-center gap-2 hover:bg-orange-700 active:scale-[0.96] shadow-[0_4px_16px_rgba(37,99,235,0.3)] transition-all cursor-pointer"
          >
            <Sliders className="w-4 h-4" />
            <span>Simulate in Scenario Lab</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
