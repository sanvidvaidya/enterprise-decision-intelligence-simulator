import React from 'react';
import { SimulatorTab } from '../types/simulator';
import { LayoutDashboard, Users, Sliders, Settings, ShieldCheck, Sparkles } from 'lucide-react';

interface HeaderNavProps {
  currentTab: SimulatorTab;
  onSelectTab: (tab: SimulatorTab) => void;
  totalArr: number;
  avgRiskScore: number;
  highRiskCount: number;
}

export const HeaderNav: React.FC<HeaderNavProps> = ({
  currentTab,
  onSelectTab,
  totalArr,
  avgRiskScore,
  highRiskCount,
}) => {
  const tabs: Array<{ id: SimulatorTab; label: string; icon: React.ElementType }> = [
    { id: 'COCKPIT', label: 'Executive Cockpit', icon: LayoutDashboard },
    { id: 'PORTFOLIO', label: 'Portfolio Matrix', icon: Users },
    { id: 'SCENARIO_LAB', label: '60fps Scenario Lab', icon: Sliders },
    { id: 'GOVERNANCE', label: 'Policy Governance', icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-40 frosted-nav px-6 py-3 flex flex-col md:flex-row items-center justify-between gap-4">
      {/* Left: Branding & Tagline */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center text-white shadow-[0_2px_8px_rgba(37,99,235,0.35)]">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold text-[#2d251e] tracking-tight">ENTERPRISE DECISION SIMULATOR</h1>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-orange-50 text-orange-700 border border-orange-200">
              REVENUE INTELLIGENCE
            </span>
          </div>
          <p className="text-[11px] text-[#786c5c]">
            Factual, evidence-backed B2B renewal risk simulator
          </p>
        </div>
      </div>

      {/* Center: Apple-style Segmented Control */}
      <div className="flex items-center bg-[#e4dac4]/90 p-1 rounded-xl border border-[#d6c8ad]/80 shadow-inner">
        {tabs.map((t) => {
          const Icon = t.icon;
          const isActive = currentTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => onSelectTab(t.id)}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 apple-pressable ${
                isActive
                  ? 'bg-[#f8f3e8] text-[#2d251e] shadow-[0_1px_3px_rgba(0,0,0,0.08)] font-semibold'
                  : 'text-[#5e5346] hover:text-[#2d251e] hover:bg-[#f8f3e8]/50'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-orange-600' : 'text-[#786c5c]'}`} />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* Right: Portfolio Quick Pulse */}
      <div className="hidden lg:flex items-center gap-4 text-xs font-medium text-[#5e5346]">
        <div className="flex items-center gap-1.5">
          <span className="text-[#8f8270]">Total ARR:</span>
          <span className="text-[#2d251e] font-bold mono-num">
            ${(totalArr / 1_000_000).toFixed(2)}M
          </span>
        </div>

        <div className="h-4 w-px bg-[#ded2ba]" />

        <div className="flex items-center gap-1.5">
          <span className="text-[#8f8270]">Avg Risk:</span>
          <span className="text-[#2d251e] font-bold mono-num">{avgRiskScore} pts</span>
        </div>

        <div className="h-4 w-px bg-[#ded2ba]" />

        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
          <span className="text-rose-600 font-bold mono-num">{highRiskCount} High Risk</span>
        </div>
      </div>
    </header>
  );
};
