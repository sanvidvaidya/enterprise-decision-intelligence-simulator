import React, { useState } from 'react';
import { PolicyParameters, CustomerAssessment } from '../types/simulator';
import { Settings, ShieldCheck, CheckCircle2, RotateCcw, Save } from 'lucide-react';
import { toast } from 'sonner';

interface PolicyGovernanceProps {
  policy: PolicyParameters;
  onUpdatePolicy: (newPolicy: PolicyParameters) => void;
  onResetPolicy: () => void;
  assessments: CustomerAssessment[];
}

export const PolicyGovernance: React.FC<PolicyGovernanceProps> = ({
  policy,
  onUpdatePolicy,
  onResetPolicy,
  assessments,
}) => {
  const [draft, setDraft] = useState<PolicyParameters>({ ...policy });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdatePolicy(draft);
    toast.success('Governance policy parameters updated across portfolio!');
  };

  const handleReset = () => {
    onResetPolicy();
    setDraft({ ...policy });
    toast.info('Restored default governance policy');
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-orange-50 text-orange-700 text-[11px] font-semibold mb-2 border border-orange-200">
            <Settings className="w-3.5 h-3.5" />
            <span>POLICY MAKER-CHECKER GOVERNANCE</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-[#2d251e] tracking-tight">
            Deterministic Scoring Policy Parameters
          </h2>
          <p className="text-xs text-[#786c5c] mt-1">
            Audit-traceable rules engine tuning. All changes require dual-custody verification.
          </p>
        </div>

        <button
          onClick={handleReset}
          className="px-3.5 py-1.5 rounded-xl bg-[#e4dac4] hover:bg-[#ded2ba] text-[#4d4236] font-semibold text-xs flex items-center gap-1.5 transition-all self-start"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Defaults</span>
        </button>
      </div>

      {/* Policy Form */}
      <form onSubmit={handleSave} className="cockpit-card p-6 md:p-8 space-y-6">
        <h3 className="text-base font-bold text-[#2d251e] border-b border-[#dfd3bc] pb-3">
          1. Risk Band Classification Thresholds
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#4d4236]">
              High-Risk Threshold (pts):
            </label>
            <input
              type="number"
              min="40"
              max="90"
              value={draft.high_risk_threshold}
              onChange={(e) =>
                setDraft({ ...draft, high_risk_threshold: Number(e.target.value) })
              }
              className="w-full px-3.5 py-2 rounded-xl bg-[#ece3cf] border border-[#d6c8ad] text-xs font-semibold text-[#2d251e] focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
            <p className="text-[11px] text-[#8f8270]">Scores &ge; this value trigger High-Risk playbook</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#4d4236]">
              Medium-Risk Threshold (pts):
            </label>
            <input
              type="number"
              min="20"
              max="50"
              value={draft.medium_risk_threshold}
              onChange={(e) =>
                setDraft({ ...draft, medium_risk_threshold: Number(e.target.value) })
              }
              className="w-full px-3.5 py-2 rounded-xl bg-[#ece3cf] border border-[#d6c8ad] text-xs font-semibold text-[#2d251e] focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
            <p className="text-[11px] text-[#8f8270]">Scores &ge; this value trigger Watchlist</p>
          </div>
        </div>

        <h3 className="text-base font-bold text-[#2d251e] border-b border-[#dfd3bc] pb-3 pt-4">
          2. Telemetry & Support Penalty Weights
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#4d4236]">
              Usage Decline High Points:
            </label>
            <input
              type="number"
              min="10"
              max="50"
              value={draft.usage_decline_high_points}
              onChange={(e) =>
                setDraft({ ...draft, usage_decline_high_points: Number(e.target.value) })
              }
              className="w-full px-3.5 py-2 rounded-xl bg-[#ece3cf] border border-[#d6c8ad] text-xs font-semibold text-[#2d251e] focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
            <p className="text-[11px] text-[#8f8270]">Penalty for &gt;30% seat usage drop</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#4d4236]">
              Critical Support Points:
            </label>
            <input
              type="number"
              min="10"
              max="50"
              value={draft.critical_support_points}
              onChange={(e) =>
                setDraft({ ...draft, critical_support_points: Number(e.target.value) })
              }
              className="w-full px-3.5 py-2 rounded-xl bg-[#ece3cf] border border-[#d6c8ad] text-xs font-semibold text-[#2d251e] focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
            <p className="text-[11px] text-[#8f8270]">Penalty for open P1 tickets</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#4d4236]">
              Near Renewal (&le;30d) Points:
            </label>
            <input
              type="number"
              min="10"
              max="40"
              value={draft.renewal_near_points}
              onChange={(e) =>
                setDraft({ ...draft, renewal_near_points: Number(e.target.value) })
              }
              className="w-full px-3.5 py-2 rounded-xl bg-[#ece3cf] border border-[#d6c8ad] text-xs font-semibold text-[#2d251e] focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
            <p className="text-[11px] text-[#8f8270]">Urgency penalty inside 30d window</p>
          </div>
        </div>

        {/* Submit Action */}
        <div className="pt-4 border-t border-[#dfd3bc] flex items-center justify-between">
          <span className="text-xs text-[#786c5c]">
            Current version: <strong className="text-[#3b3229]">Policy v2.4 (Active)</strong>
          </span>
          <button
            type="submit"
            className="px-6 py-2.5 rounded-xl bg-orange-600 text-white font-semibold text-xs flex items-center gap-2 hover:bg-orange-700 apple-pressable shadow-[0_2px_10px_rgba(37,99,235,0.25)] transition-all"
          >
            <Save className="w-4 h-4" />
            <span>Apply Policy Parameters</span>
          </button>
        </div>
      </form>
    </div>
  );
};
