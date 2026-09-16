import React from 'react';
import { Sparkles, LayoutDashboard, Sliders, Users, Settings, DollarSign, AlertTriangle, UploadCloud } from 'lucide-react';
import { SimulatorTab } from '../types/simulator';

export type { SimulatorTab } from '../types/simulator';

interface AppleCockpitHeaderProps {
  currentTab: SimulatorTab;
  onSelectTab: (tab: SimulatorTab) => void;
  totalArr: number;
  avgRiskScore: number;
  highRiskCount: number;
  onOpenUpload?: () => void;
  isUsingCustomData?: boolean;
  backendConnected?: boolean;
}

export const AppleCockpitHeader: React.FC<AppleCockpitHeaderProps> = ({
  currentTab,
  onSelectTab,
  totalArr,
  avgRiskScore,
  highRiskCount,
  onOpenUpload,
  isUsingCustomData,
  backendConnected = false,
}) => {
  const tabs: Array<{ id: SimulatorTab; label: string; icon: React.ElementType }> = [
    { id: 'LANDING', label: 'Overview', icon: Sparkles },
    { id: 'COCKPIT', label: 'Cockpit', icon: LayoutDashboard },
    { id: 'SCENARIO_LAB', label: 'Scenario Lab', icon: Sliders },
    { id: 'PORTFOLIO', label: 'Portfolio', icon: Users },
    { id: 'GOVERNANCE', label: 'Governance', icon: Settings },
  ];

  return (
    <div className="fixed top-5 inset-x-0 z-50 flex justify-center px-4 pointer-events-none">
      <div className="pointer-events-auto apple-dynamic-island p-1.5 rounded-full flex items-center gap-2 sm:gap-4 shadow-xl transition-all duration-300">
        {/* Brand Logo */}
        <button
          onClick={() => onSelectTab('LANDING')}
          className="flex items-center gap-2 pl-3 pr-2 py-1 text-left cursor-pointer hover:opacity-90 transition-opacity"
        >
          <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-orange-600 to-amber-600 flex items-center justify-center text-white text-xs shadow-[0_2px_8px_rgba(37,99,235,0.4)]">
            
          </div>
          <span className="font-display font-extrabold text-xs sm:text-sm tracking-tight text-[#2d251e] uppercase">
            Enterprise Decision Simulator
          </span>
        </button>

        <div className="h-4 w-px bg-[#ded2ba] hidden sm:block" />

        {/* Tab Segment Switcher */}
        <div className="flex items-center bg-[#e4dac4]/80 p-1 rounded-full border border-[#d6c8ad]/50">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onSelectTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 apple-spring-press cursor-pointer ${
                  isActive
                    ? 'bg-[#f8f3e8] text-orange-600 shadow-[0_2px_8px_rgba(0,0,0,0.06)] border border-[#d6c8ad]/60'
                    : 'text-[#5e5346] hover:text-[#2d251e] hover:bg-[#f8f3e8]/50'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-orange-600' : 'text-[#786c5c]'}`} />
                <span className="hidden md:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="h-4 w-px bg-[#ded2ba] hidden sm:block" />

        {/* Quick Portfolio Pulse Metrics */}
        <div className="flex items-center gap-2 pr-2 text-xs font-mono">
          <div className="hidden lg:flex items-center gap-1 text-[#5e5346] bg-[#ece3cf] px-2.5 py-1 rounded-full border border-[#d6c8ad]/60">
            <DollarSign className="w-3.5 h-3.5 text-orange-600" />
            <span className="font-bold text-[#2d251e]">${(totalArr / 1000000).toFixed(2)}M</span>
            <span className="text-[10px] text-[#8f8270]">ARR</span>
          </div>

          <div className="flex items-center gap-1 bg-[#ece3cf] px-2.5 py-1 rounded-full border border-[#d6c8ad]/60">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-bold text-[#2d251e]">{avgRiskScore}</span>
            <span className="text-[10px] text-[#8f8270] hidden sm:inline">avg risk</span>
          </div>

          {highRiskCount > 0 && (
            <div className="hidden sm:flex items-center gap-1 bg-rose-50 text-rose-700 px-2.5 py-1 rounded-full border border-rose-200/80 font-bold">
              <AlertTriangle className="w-3 h-3 text-rose-600" />
              <span>{highRiskCount} HIGH</span>
            </div>
          )}

          {onOpenUpload && (
            <button
              onClick={onOpenUpload}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold transition-all cursor-pointer shadow-xs ${
                isUsingCustomData
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                  : 'bg-gradient-to-r from-orange-600 to-amber-600 hover:opacity-90 text-white'
              }`}
              title="Upload physical enterprise data (.csv, .json)"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{isUsingCustomData ? 'Custom Data' : 'Upload Data'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
