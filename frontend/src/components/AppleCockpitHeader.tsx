import React from 'react';
import {
  Sparkles,
  LayoutDashboard,
  Sliders,
  Users,
  Settings,
  DollarSign,
  AlertTriangle,
  UploadCloud,
  Network,
  Clock,
  Swords,
  Radio,
} from 'lucide-react';
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
    { id: 'PORTFOLIO', label: 'Portfolio', icon: Users },
    { id: 'SCENARIO_LAB', label: 'Scenario Lab', icon: Sliders },
    { id: 'CAUSAL_GRAPH', label: 'Causal DAG', icon: Network },
    { id: 'TIME_TRAVEL', label: 'Event Replay', icon: Clock },
    { id: 'GAME_THEORY', label: 'Game Theory', icon: Swords },
    { id: 'DISPATCH_STREAM', label: 'Dispatch Hub', icon: Radio },
    { id: 'GOVERNANCE', label: 'Governance', icon: Settings },
  ];

  return (
    <div className="fixed top-3 inset-x-0 z-50 flex justify-center px-2 pointer-events-none">
      <div className="pointer-events-auto apple-dynamic-island p-1.5 rounded-full flex items-center gap-1 sm:gap-2 shadow-xl transition-all duration-300 max-w-[98vw] overflow-x-auto scrollbar-none">
        {/* Brand Logo */}
        <button
          onClick={() => onSelectTab('LANDING')}
          className="flex items-center gap-2 pl-2 pr-1.5 py-1 text-left cursor-pointer hover:opacity-90 transition-opacity flex-shrink-0"
        >
          <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-amber-600 to-orange-600 flex items-center justify-center text-white text-xs shadow-sm font-bold">
            ∆
          </div>
          <span className="font-display font-extrabold text-xs tracking-tight text-[#2d251e] uppercase hidden xl:inline">
            Enterprise Decision Simulator
          </span>
        </button>

        <div className="h-4 w-px bg-[#ded2ba] hidden sm:block flex-shrink-0" />

        {/* Tab Segment Switcher */}
        <div className="flex items-center bg-[#e4dac4]/80 p-0.5 sm:p-1 rounded-full border border-[#d6c8ad]/50 flex-shrink-0">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onSelectTab(tab.id)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold transition-all duration-200 apple-spring-press cursor-pointer flex-shrink-0 ${
                  isActive
                    ? 'bg-[#f8f3e8] text-amber-800 shadow-[0_2px_8px_rgba(0,0,0,0.06)] border border-[#d6c8ad]/60 font-bold'
                    : 'text-[#5e5346] hover:text-[#2d251e] hover:bg-[#f8f3e8]/50'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-amber-700' : 'text-[#786c5c]'}`} />
                <span className="hidden lg:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="h-4 w-px bg-[#ded2ba] hidden sm:block flex-shrink-0" />

        {/* Quick Portfolio Pulse Metrics */}
        <div className="flex items-center gap-1.5 pr-1.5 text-xs font-mono flex-shrink-0">
          <div className="hidden 2xl:flex items-center gap-1 text-[#5e5346] bg-[#ece3cf] px-2 py-0.5 rounded-full border border-[#d6c8ad]/60">
            <DollarSign className="w-3.5 h-3.5 text-amber-700" />
            <span className="font-bold text-[#2d251e]">${(totalArr / 1000000).toFixed(2)}M</span>
          </div>

          <div className="flex items-center gap-1 bg-[#ece3cf] px-2 py-0.5 rounded-full border border-[#d6c8ad]/60">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-bold text-[#2d251e]">{avgRiskScore}</span>
            <span className="text-[10px] text-[#8f8270] hidden sm:inline">risk</span>
          </div>

          {highRiskCount > 0 && (
            <div className="hidden sm:flex items-center gap-1 bg-rose-50 text-rose-700 px-2 py-0.5 rounded-full border border-rose-200/80 font-bold">
              <AlertTriangle className="w-3 h-3 text-rose-600" />
              <span>{highRiskCount}</span>
            </div>
          )}

          {onOpenUpload && (
            <button
              onClick={onOpenUpload}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold transition-all cursor-pointer shadow-xs ${
                isUsingCustomData
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                  : 'bg-gradient-to-r from-amber-700 to-orange-600 hover:opacity-90 text-white'
              }`}
              title="Upload physical enterprise data (.csv, .json)"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{isUsingCustomData ? 'Custom' : 'Upload'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
