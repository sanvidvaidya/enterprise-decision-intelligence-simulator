import React, { useState } from 'react';
import { PolicyParameters, CustomerAssessment } from '../types/simulator';
import { Settings, ShieldCheck, CheckCircle2, RotateCcw, Save, Sliders, Lock, ArrowUpRight, Scale } from 'lucide-react';
import { toast } from 'sonner';

interface ApplePolicyViewProps {
  policy: PolicyParameters;
  onUpdatePolicy: (newPolicy: PolicyParameters) => void;
  onResetPolicy: () => void;
  assessments: CustomerAssessment[];
}

export const ApplePolicyView: React.FC<ApplePolicyViewProps> = ({
  policy,
  onUpdatePolicy,
  onResetPolicy,
  assessments,
}) => {
  const [draft, setDraft] = useState<PolicyParameters>({ ...policy });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdatePolicy(draft);
    toast.success('Dual-custody policy applied across portfolio!');
  };

  const handleReset = () => {
    onResetPolicy();
    setDraft({ ...policy });
    toast.info('Restored default deterministic policy');
  };

  const highCount = assessments.filter(a => a.risk_level === 'High').length;
  const medCount = assessments.filter(a => a.risk_level === 'Medium').length;
  const lowCount = assessments.filter(a => a.risk_level === 'Low').length;

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-orange-600/10 text-orange-600 text-[11px] font-bold font-mono tracking-wider mb-2 border border-orange-500/20">
            <Lock className="w-3 h-3" />
            <span>DUAL-CUSTODY AUDIT GOVERNANCE</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-[#1f1a16] font-display tracking-tight">
            Scoring Policy Engine
          </h1>
          <p className="text-xs text-[#786c5c] mt-1 font-sans">
            Deterministic risk weights & thresholds. Every tuning parameter is mathematically reproducible with full auditability.
          </p>
        </div>

        <button
          onClick={handleReset}
          className="px-4 py-2 rounded-full apple-glass-pill hover:bg-[#ded2ba]/60 text-[#4d4236] font-semibold text-xs flex items-center gap-1.5 transition-all self-start active:scale-[0.96] cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Defaults</span>
        </button>
      </div>

      {/* Portfolio Impact Preview Pill */}
      <div className="apple-card p-5 bg-gradient-to-r from-orange-50/40 via-amber-50/20 to-[#ede4d0] border-orange-200/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-orange-600 text-white flex items-center justify-center shadow-[0_4px_16px_rgba(37,99,235,0.3)]">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold text-[#2d251e]">Current Portfolio Distribution</div>
            <div className="text-[11px] text-[#786c5c] font-sans">
              Dynamic threshold impact across 30 enterprise accounts
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className="text-xs font-mono font-bold text-rose-600">{highCount}</div>
            <div className="text-[10px] text-[#8f8270] uppercase font-semibold">High Risk</div>
          </div>
          <div className="h-6 w-px bg-[#ded2ba]" />
          <div className="text-center">
            <div className="text-xs font-mono font-bold text-amber-600">{medCount}</div>
            <div className="text-[10px] text-[#8f8270] uppercase font-semibold">Watchlist</div>
          </div>
          <div className="h-6 w-px bg-[#ded2ba]" />
          <div className="text-center">
            <div className="text-xs font-mono font-bold text-emerald-600">{lowCount}</div>
            <div className="text-[10px] text-[#8f8270] uppercase font-semibold">Healthy</div>
          </div>
        </div>
      </div>

      {/* Main Form */}
      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1 */}
        <div className="apple-card p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-[#dfd3bc] pb-4">
            <div>
              <h3 className="text-base font-bold text-[#1f1a16] font-display">
                1. Risk Band Classification Thresholds
              </h3>
              <p className="text-[11px] text-[#8f8270] font-sans">
                Adjust points required to trip automated executive escalation vs. watchlist containment.
              </p>
            </div>
            <span className="font-mono text-[11px] font-bold text-orange-600 bg-orange-50 px-2.5 py-1 rounded-md">
              Step 01
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* High risk threshold */}
            <div className="p-5 rounded-2xl bg-[#ece3cf]/70 border border-[#d6c8ad]/60 space-y-3">
              <div className="flex justify-between items-baseline">
                <label className="text-xs font-bold text-[#3b3229] font-sans">
                  High-Risk Threshold
                </label>
                <span className="font-mono text-sm font-bold text-rose-600 bg-rose-50 px-2.5 py-0.5 rounded-md border border-rose-100">
                  {draft.high_risk_threshold} pts
                </span>
              </div>
              <input
                type="range"
                min="40"
                max="90"
                step="5"
                value={draft.high_risk_threshold}
                onChange={(e) =>
                  setDraft({ ...draft, high_risk_threshold: Number(e.target.value) })
                }
                className="w-full accent-rose-600 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-[#8f8270]">
                <span>40 pts (Strict)</span>
                <span>90 pts (Relaxed)</span>
              </div>
            </div>

            {/* Medium risk threshold */}
            <div className="p-5 rounded-2xl bg-[#ece3cf]/70 border border-[#d6c8ad]/60 space-y-3">
              <div className="flex justify-between items-baseline">
                <label className="text-xs font-bold text-[#3b3229] font-sans">
                  Watchlist / Medium Threshold
                </label>
                <span className="font-mono text-sm font-bold text-amber-600 bg-amber-50 px-2.5 py-0.5 rounded-md border border-amber-100">
                  {draft.medium_risk_threshold} pts
                </span>
              </div>
              <input
                type="range"
                min="20"
                max="50"
                step="5"
                value={draft.medium_risk_threshold}
                onChange={(e) =>
                  setDraft({ ...draft, medium_risk_threshold: Number(e.target.value) })
                }
                className="w-full accent-amber-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-[#8f8270]">
                <span>20 pts</span>
                <span>50 pts</span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Penalty Weights */}
        <div className="apple-card p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-[#dfd3bc] pb-4">
            <div>
              <h3 className="text-base font-bold text-[#1f1a16] font-display">
                2. Telemetry & Support Penalty Weights
              </h3>
              <p className="text-[11px] text-[#8f8270] font-sans">
                Fine-tune additive points injected when customer health anomalies are detected.
              </p>
            </div>
            <span className="font-mono text-[11px] font-bold text-orange-600 bg-orange-50 px-2.5 py-1 rounded-md">
              Step 02
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="p-4 rounded-2xl bg-[#ece3cf]/70 border border-[#d6c8ad]/60 space-y-3">
              <div className="flex justify-between items-baseline">
                <label className="text-xs font-bold text-[#3b3229] font-sans">
                  Usage Decline (&gt;30%)
                </label>
                <span className="font-mono text-xs font-bold text-orange-600">
                  +{draft.usage_decline_high_points} pts
                </span>
              </div>
              <input
                type="range"
                min="10"
                max="50"
                step="5"
                value={draft.usage_decline_high_points}
                onChange={(e) =>
                  setDraft({ ...draft, usage_decline_high_points: Number(e.target.value) })
                }
                className="w-full accent-orange-600 cursor-pointer"
              />
            </div>

            <div className="p-4 rounded-2xl bg-[#ece3cf]/70 border border-[#d6c8ad]/60 space-y-3">
              <div className="flex justify-between items-baseline">
                <label className="text-xs font-bold text-[#3b3229] font-sans">
                  Critical P1 Incident
                </label>
                <span className="font-mono text-xs font-bold text-orange-600">
                  +{draft.critical_support_points} pts
                </span>
              </div>
              <input
                type="range"
                min="10"
                max="50"
                step="5"
                value={draft.critical_support_points}
                onChange={(e) =>
                  setDraft({ ...draft, critical_support_points: Number(e.target.value) })
                }
                className="w-full accent-orange-600 cursor-pointer"
              />
            </div>

            <div className="p-4 rounded-2xl bg-[#ece3cf]/70 border border-[#d6c8ad]/60 space-y-3">
              <div className="flex justify-between items-baseline">
                <label className="text-xs font-bold text-[#3b3229] font-sans">
                  Renewal Runway (&le;30d)
                </label>
                <span className="font-mono text-xs font-bold text-orange-600">
                  +{draft.renewal_near_points} pts
                </span>
              </div>
              <input
                type="range"
                min="10"
                max="40"
                step="5"
                value={draft.renewal_near_points}
                onChange={(e) =>
                  setDraft({ ...draft, renewal_near_points: Number(e.target.value) })
                }
                className="w-full accent-orange-600 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Submit & Audit Memo */}
        <div className="apple-card p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-[#786c5c]">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Dual-custody signatory hash: <code className="font-mono text-[#3b3229] bg-[#e4dac4] px-1.5 py-0.5 rounded">0x7B9...4E1</code></span>
          </div>

          <button
            type="submit"
            className="w-full sm:w-auto px-6 py-3 rounded-full bg-orange-600 text-white font-semibold text-xs flex items-center justify-center gap-2 hover:bg-orange-700 active:scale-[0.96] shadow-[0_4px_16px_rgba(37,99,235,0.3)] transition-all cursor-pointer"
          >
            <Save className="w-4 h-4" />
            <span>Apply & Authorize Policy Changes</span>
          </button>
        </div>
      </form>
    </div>
  );
};
