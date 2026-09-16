import React from 'react';
import { CustomerAssessment } from '../types/simulator';
import { X, Sliders, ExternalLink, Mail, Calendar, DollarSign, CheckCircle2, ShieldAlert } from 'lucide-react';

interface CustomerDrawerProps {
  assessment: CustomerAssessment | null;
  onClose: () => void;
  onOpenScenarioLab: (assessment: CustomerAssessment) => void;
}

export const CustomerDrawer: React.FC<CustomerDrawerProps> = ({
  assessment,
  onClose,
  onOpenScenarioLab,
}) => {
  if (!assessment) return null;

  const { customer, contract, risk_score, risk_level, factors, recommended_actions } = assessment;

  const isHigh = risk_level === 'High';
  const isMed = risk_level === 'Medium';

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-[#f8f3e8] border-l border-[#d6c8ad] shadow-2xl z-50 flex flex-col animate-in slide-in-from-right duration-200">
      {/* Drawer Header */}
      <div className="p-6 border-b border-[#dfd3bc] flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#8f8270] font-bold">
              {customer.customer_id}
            </span>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold mono-num border ${
                isHigh
                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                  : isMed
                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200'
              }`}
            >
              {risk_score} PTS {risk_level.toUpperCase()}
            </span>
          </div>
          <h3 className="text-xl font-bold text-[#2d251e] mt-1">
            {customer.customer_name}
          </h3>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-full text-[#8f8270] hover:text-[#4d4236] hover:bg-[#e4dac4] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs text-[#5e5346]">
        {/* Account Details Tile */}
        <div className="p-4 rounded-2xl bg-[#ece3cf] border border-[#d6c8ad]/80 space-y-2.5">
          <div className="font-semibold text-[#2d251e] text-xs uppercase tracking-wide">
            Enterprise Account Details
          </div>
          <div className="grid grid-cols-2 gap-3 pt-1">
            <div>
              <span className="text-[#8f8270]">Industry:</span>
              <div className="font-semibold text-[#3b3229]">{customer.industry}</div>
            </div>
            <div>
              <span className="text-[#8f8270]">Segment:</span>
              <div className="font-semibold text-[#3b3229]">{customer.segment}</div>
            </div>
            <div>
              <span className="text-[#8f8270]">Region:</span>
              <div className="font-semibold text-[#3b3229]">{customer.region}</div>
            </div>
            <div>
              <span className="text-[#8f8270]">Employees:</span>
              <div className="font-semibold text-[#3b3229] mono-num">
                {customer.employee_count.toLocaleString()}
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-[#d6c8ad]/60 flex items-center justify-between">
            <span className="text-[#8f8270]">Account Manager:</span>
            <div className="font-semibold text-[#3b3229] flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5 text-orange-600" />
              <span>{customer.account_manager_name || 'Assigned Lead'}</span>
            </div>
          </div>
        </div>

        {/* Contract Summary */}
        {contract && (
          <div className="p-4 rounded-2xl bg-[#ece3cf] border border-[#d6c8ad]/80 space-y-2.5">
            <div className="font-semibold text-[#2d251e] text-xs uppercase tracking-wide">
              Contract & Commercial Runway
            </div>
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div>
                <span className="text-[#8f8270]">Annual Contract Value:</span>
                <div className="text-base font-bold text-[#2d251e] mono-num">
                  ${contract.annual_contract_value.toLocaleString()}
                </div>
              </div>
              <div>
                <span className="text-[#8f8270]">Renewal Milestone:</span>
                <div className="text-base font-bold text-[#2d251e] mono-num">
                  {contract.renewal_date}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Transparent Risk Waterfall */}
        <div className="space-y-2">
          <div className="font-semibold text-[#2d251e] text-xs uppercase tracking-wide">
            Transparent Risk Point Waterfall ({factors.length} active factors)
          </div>
          <div className="space-y-2">
            {factors.map((f, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-[#f8f3e8] border border-[#d6c8ad] shadow-sm space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#2d251e]">{f.name}</span>
                  <span className="font-bold text-rose-600 mono-num">+{f.points} pts</span>
                </div>
                <p className="text-[#5e5346] leading-relaxed">{f.explanation}</p>
                <div className="pt-1 text-[11px] text-[#8f8270] font-mono">
                  Evidence IDs: {f.evidence_record_ids.join(', ')}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recommended Action Playbook */}
        <div className="space-y-2">
          <div className="font-semibold text-[#2d251e] text-xs uppercase tracking-wide">
            Prescribed Intervention Actions
          </div>
          <div className="space-y-2">
            {recommended_actions.map((act, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-orange-50/60 border border-orange-200 flex items-start gap-2.5"
              >
                <CheckCircle2 className="w-4 h-4 text-orange-600 shrink-0 mt-0.5" />
                <span className="text-[#3b3229] leading-snug">{act}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Drawer Footer Actions */}
      <div className="p-6 border-t border-[#dfd3bc] bg-[#ece3cf] flex items-center justify-between">
        <button
          onClick={onClose}
          className="px-4 py-2 rounded-xl text-[#5e5346] hover:text-[#2d251e] font-medium text-xs transition-colors"
        >
          Close
        </button>

        <button
          onClick={() => {
            onClose();
            onOpenScenarioLab(assessment);
          }}
          className="px-5 py-2.5 rounded-xl bg-orange-600 text-white font-semibold text-xs flex items-center gap-2 hover:bg-orange-700 apple-pressable shadow-[0_2px_10px_rgba(37,99,235,0.25)] transition-all"
        >
          <Sliders className="w-4 h-4" />
          <span>Launch in Scenario Lab</span>
        </button>
      </div>
    </div>
  );
};
