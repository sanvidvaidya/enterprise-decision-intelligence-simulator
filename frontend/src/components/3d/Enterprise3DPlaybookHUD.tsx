import React from 'react';
import { CustomerAssessment } from '../../types/simulator';
import { PlaybookManeuvers } from './Enterprise3DOrbitCanvas';

interface Enterprise3DPlaybookHUDProps {
  assessments: CustomerAssessment[];
  playbookIntensity: number;
  onIntensityChange: (val: number) => void;
  maneuvers: PlaybookManeuvers;
  onToggleManeuver: (key: keyof PlaybookManeuvers) => void;
  className?: string;
}

export const Enterprise3DPlaybookHUD: React.FC<Enterprise3DPlaybookHUDProps> = ({
  assessments,
  playbookIntensity,
  onIntensityChange,
  maneuvers,
  onToggleManeuver,
  className = '',
}) => {
  // Calculate aggregate portfolio ARR stats
  const totalARR = assessments.reduce(
    (sum, a) => sum + (a.contract?.annual_contract_value || 0),
    0
  );

  const highRiskAssessments = assessments.filter(
    (a) => a.risk_level === 'High' || (a.factors && a.factors.length >= 2)
  );

  const highRiskARR = highRiskAssessments.reduce(
    (sum, a) => sum + (a.contract?.annual_contract_value || 0),
    0
  );

  // Intervention boost from specific maneuvers
  const maneuverBoost =
    (maneuvers.execSponsor ? 15 : 0) +
    (maneuvers.architect ? 25 : 0) +
    (maneuvers.discount ? 20 : 0) +
    (maneuvers.featureFreeze ? 20 : 0);

  // Cumulative intervention strength (0 - 100%)
  const totalInterventionPct = Math.min(
    100,
    Math.round(playbookIntensity + maneuverBoost * (1 - playbookIntensity / 100))
  );

  // Protected ARR calculation
  const protectedARR = Math.round(highRiskARR * (totalInterventionPct / 100) * 0.88);
  const accountsSavedCount = Math.round(highRiskAssessments.length * (totalInterventionPct / 100));

  const applyPresetPlan = (plan: 'AGGRESSIVE' | 'BALANCED' | 'CONSERVATIVE' | 'RESET') => {
    if (plan === 'RESET') {
      onIntensityChange(0);
      if (maneuvers.execSponsor) onToggleManeuver('execSponsor');
      if (maneuvers.architect) onToggleManeuver('architect');
      if (maneuvers.discount) onToggleManeuver('discount');
      if (maneuvers.featureFreeze) onToggleManeuver('featureFreeze');
    } else if (plan === 'CONSERVATIVE') {
      onIntensityChange(25);
      if (!maneuvers.execSponsor) onToggleManeuver('execSponsor');
      if (maneuvers.architect) onToggleManeuver('architect');
      if (maneuvers.discount) onToggleManeuver('discount');
      if (maneuvers.featureFreeze) onToggleManeuver('featureFreeze');
    } else if (plan === 'BALANCED') {
      onIntensityChange(50);
      if (!maneuvers.execSponsor) onToggleManeuver('execSponsor');
      if (!maneuvers.architect) onToggleManeuver('architect');
      if (maneuvers.discount) onToggleManeuver('discount');
      if (maneuvers.featureFreeze) onToggleManeuver('featureFreeze');
    } else if (plan === 'AGGRESSIVE') {
      onIntensityChange(85);
      if (!maneuvers.execSponsor) onToggleManeuver('execSponsor');
      if (!maneuvers.architect) onToggleManeuver('architect');
      if (!maneuvers.discount) onToggleManeuver('discount');
      if (!maneuvers.featureFreeze) onToggleManeuver('featureFreeze');
    }
  };

  return (
    <div className={`p-5 rounded-2xl bg-[#292524]/95 border border-stone-800 shadow-2xl backdrop-blur-xl text-stone-200 ${className}`}>
      {/* Header telemetry */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-stone-800/80 pb-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping" />
            <span className="text-xs font-mono tracking-wider uppercase text-amber-400 font-semibold">
              Strategic Turnaround Matrix
            </span>
          </div>
          <h3 className="font-display text-lg font-bold text-white tracking-tight mt-0.5">
            Turnaround Levers & Gravity Shift
          </h3>
        </div>

        {/* Live Saved ARR Badge */}
        <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-stone-900/90 border border-emerald-500/40 shadow-[0_0_20px_rgba(5,150,105,0.15)]">
          <div className="text-right">
            <div className="text-[10px] uppercase font-mono tracking-wider text-emerald-400 font-semibold">
              Protected Revenue
            </div>
            <div className="font-mono text-base font-bold text-white flex items-center gap-1">
              <span className="text-emerald-400">+$</span>
              <span>{(protectedARR || 0).toLocaleString()}</span>
              <span className="text-[10px] text-stone-400 font-normal">ARR</span>
            </div>
          </div>
          <div className="h-7 w-px bg-stone-700/60" />
          <div className="text-left">
            <div className="text-[10px] uppercase font-mono tracking-wider text-stone-400 font-semibold">
              Saved
            </div>
            <div className="font-mono text-sm font-bold text-amber-300">
              {accountsSavedCount} <span className="text-stone-400 text-xs">/ {highRiskAssessments.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Preset Quick Plans */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-[10px] uppercase font-mono text-stone-500 font-medium">Quick Playbooks:</span>
        <button
          onClick={() => applyPresetPlan('RESET')}
          className="px-2.5 py-1 text-[10px] font-mono rounded-lg bg-stone-800/80 text-stone-400 hover:text-stone-200 hover:bg-stone-700 transition cursor-pointer"
        >
          Baseline
        </button>
        <button
          onClick={() => applyPresetPlan('CONSERVATIVE')}
          className="px-2.5 py-1 text-[10px] font-mono rounded-lg bg-stone-800/80 text-amber-300 hover:bg-amber-950/60 hover:border-amber-700/40 border border-transparent transition cursor-pointer"
        >
          Light Touch
        </button>
        <button
          onClick={() => applyPresetPlan('BALANCED')}
          className="px-2.5 py-1 text-[10px] font-mono rounded-lg bg-stone-800/80 text-amber-400 hover:bg-amber-900/40 hover:border-amber-600/40 border border-transparent transition cursor-pointer"
        >
          Targeted Exec
        </button>
        <button
          onClick={() => applyPresetPlan('AGGRESSIVE')}
          className="px-2.5 py-1 text-[10px] font-mono rounded-lg bg-amber-600/90 text-white font-semibold shadow-sm hover:bg-amber-500 transition cursor-pointer"
        >
          Full Red-Alert
        </button>
      </div>

      {/* Master Intervention Slider */}
      <div className="space-y-2 mb-5 p-3.5 rounded-xl bg-stone-900/60 border border-stone-800/80">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-stone-300 font-medium flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Executive Intervention Intensity
          </span>
          <span className="text-amber-400 font-bold font-mono">
            {totalInterventionPct}% Effective Force
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={100}
          value={playbookIntensity}
          onChange={(e) => onIntensityChange(Number(e.target.value))}
          className="w-full h-2 bg-stone-800 rounded-lg appearance-none cursor-pointer accent-amber-500 hover:accent-amber-400 focus:outline-none"
        />
        <div className="flex justify-between text-[10px] font-mono text-stone-500">
          <span>0% (No Executive Action)</span>
          <span>50% (Standard Retention Playbook)</span>
          <span>100% (Maximum Gravitational Pull)</span>
        </div>
      </div>

      {/* 4 Tactile Turnaround Levers */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {/* Lever 1: Executive Sponsor Call */}
        <button
          onClick={() => onToggleManeuver('execSponsor')}
          className={`flex items-start justify-between p-3 rounded-xl border text-left transition-all cursor-pointer ${
            maneuvers.execSponsor
              ? 'bg-amber-950/40 border-amber-500/70 shadow-[0_0_15px_rgba(217,119,6,0.15)] text-amber-100'
              : 'bg-stone-900/40 border-stone-800/80 text-stone-400 hover:border-stone-700 hover:text-stone-300'
          }`}
        >
          <div className="space-y-0.5">
            <div className="flex items-center gap-1.5 font-semibold text-xs text-white">
              <span className={`w-2 h-2 rounded-full ${maneuvers.execSponsor ? 'bg-amber-400' : 'bg-stone-600'}`} />
              Executive Sponsor Call
            </div>
            <div className="text-[10px] text-stone-400 font-mono">
              C-Suite 1-on-1 intervention & alignment
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-stone-800 text-amber-400 border border-stone-700">
            +15%
          </span>
        </button>

        {/* Lever 2: Dedicated Solutions Architect */}
        <button
          onClick={() => onToggleManeuver('architect')}
          className={`flex items-start justify-between p-3 rounded-xl border text-left transition-all cursor-pointer ${
            maneuvers.architect
              ? 'bg-amber-950/40 border-amber-500/70 shadow-[0_0_15px_rgba(217,119,6,0.15)] text-amber-100'
              : 'bg-stone-900/40 border-stone-800/80 text-stone-400 hover:border-stone-700 hover:text-stone-300'
          }`}
        >
          <div className="space-y-0.5">
            <div className="flex items-center gap-1.5 font-semibold text-xs text-white">
              <span className={`w-2 h-2 rounded-full ${maneuvers.architect ? 'bg-amber-400' : 'bg-stone-600'}`} />
              Dedicated Architect
            </div>
            <div className="text-[10px] text-stone-400 font-mono">
              Onsite technical rescue & SLA stabilization
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-stone-800 text-amber-400 border border-stone-700">
            +25%
          </span>
        </button>

        {/* Lever 3: 15% Commercial Concession */}
        <button
          onClick={() => onToggleManeuver('discount')}
          className={`flex items-start justify-between p-3 rounded-xl border text-left transition-all cursor-pointer ${
            maneuvers.discount
              ? 'bg-amber-950/40 border-amber-500/70 shadow-[0_0_15px_rgba(217,119,6,0.15)] text-amber-100'
              : 'bg-stone-900/40 border-stone-800/80 text-stone-400 hover:border-stone-700 hover:text-stone-300'
          }`}
        >
          <div className="space-y-0.5">
            <div className="flex items-center gap-1.5 font-semibold text-xs text-white">
              <span className={`w-2 h-2 rounded-full ${maneuvers.discount ? 'bg-amber-400' : 'bg-stone-600'}`} />
              Commercial Concession
            </div>
            <div className="text-[10px] text-stone-400 font-mono">
              15% strategic discount or free tier add-on
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-stone-800 text-amber-400 border border-stone-700">
            +20%
          </span>
        </button>

        {/* Lever 4: Product Feature Freeze */}
        <button
          onClick={() => onToggleManeuver('featureFreeze')}
          className={`flex items-start justify-between p-3 rounded-xl border text-left transition-all cursor-pointer ${
            maneuvers.featureFreeze
              ? 'bg-amber-950/40 border-amber-500/70 shadow-[0_0_15px_rgba(217,119,6,0.15)] text-amber-100'
              : 'bg-stone-900/40 border-stone-800/80 text-stone-400 hover:border-stone-700 hover:text-stone-300'
          }`}
        >
          <div className="space-y-0.5">
            <div className="flex items-center gap-1.5 font-semibold text-xs text-white">
              <span className={`w-2 h-2 rounded-full ${maneuvers.featureFreeze ? 'bg-amber-400' : 'bg-stone-600'}`} />
              Fast-Track Feature Fix
            </div>
            <div className="text-[10px] text-stone-400 font-mono">
              Emergency sprint commit for blocker bug
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-stone-800 text-amber-400 border border-stone-700">
            +20%
          </span>
        </button>
      </div>

      {/* Physics note */}
      <div className="mt-4 pt-3 border-t border-stone-800/60 flex items-center justify-between text-[11px] font-mono text-stone-400">
        <span>✨ Watch the 3D accounts physically migrate radially outward into the gold orbit ring</span>
        <span className="text-amber-400 font-semibold">Total Portfolio: ${(totalARR / 1_000_000).toFixed(1)}M</span>
      </div>
    </div>
  );
};
