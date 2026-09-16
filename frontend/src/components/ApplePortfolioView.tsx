import React, { useState } from 'react';
import { CustomerAssessment } from '../types/simulator';
import { Search, Sliders, ArrowRight, ShieldAlert, CheckCircle2, DollarSign, Mail, Compass, LayoutGrid, Sparkles } from 'lucide-react';
import { Enterprise3DOrbitCanvas, AstrolabePreset, PlaybookManeuvers } from './3d/Enterprise3DOrbitCanvas';
import { Enterprise3DPlaybookHUD } from './3d/Enterprise3DPlaybookHUD';

interface ApplePortfolioViewProps {
  assessments: CustomerAssessment[];
  onSelectCustomer: (assessment: CustomerAssessment) => void;
  onStartScenario: (assessment: CustomerAssessment) => void;
}

export const ApplePortfolioView: React.FC<ApplePortfolioViewProps> = ({
  assessments,
  onSelectCustomer,
  onStartScenario,
}) => {
  const [viewMode, setViewMode] = useState<'3D_ORBIT' | 'GRID'>('3D_ORBIT');
  const [searchQuery, setSearchQuery] = useState('');
  const [segmentFilter, setSegmentFilter] = useState<'ALL' | 'Enterprise' | 'Mid-Market' | 'SMB'>('ALL');
  const [riskFilter, setRiskFilter] = useState<'ALL' | 'High' | 'Medium' | 'Low'>('ALL');

  const [orbitIntensity, setOrbitIntensity] = useState<number>(35);
  const [orbitManeuvers, setOrbitManeuvers] = useState<PlaybookManeuvers>({
    execSponsor: true,
    architect: false,
    discount: false,
    featureFreeze: false,
  });
  const [orbitPreset, setOrbitPreset] = useState<AstrolabePreset>('PERSPECTIVE');
  const [selectedOrbitCustomer, setSelectedOrbitCustomer] = useState<CustomerAssessment | undefined>(assessments[0]);

  const handleToggleOrbitManeuver = (key: keyof PlaybookManeuvers) => {
    setOrbitManeuvers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const filtered = assessments.filter((a) => {
    if (segmentFilter !== 'ALL' && a.customer.segment !== segmentFilter) return false;
    if (riskFilter !== 'ALL' && a.risk_level !== riskFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        a.customer.customer_name.toLowerCase().includes(q) ||
        a.customer.customer_id.toLowerCase().includes(q) ||
        a.customer.industry.toLowerCase().includes(q) ||
        a.customer.region.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16 pt-16">
      {/* Header */}
      <div className="text-center space-y-4 max-w-2xl mx-auto pt-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 border border-orange-200 text-orange-700 text-xs font-semibold tracking-wide uppercase">
          <Sparkles className="w-3.5 h-3.5 text-orange-600" />
          <span>Interactive Enterprise Telemetry</span>
        </div>
        <h2 className="text-3xl md:text-4xl font-display font-extrabold text-[#2d251e] tracking-tight">
          Enterprise Account Portfolio
        </h2>
        <p className="text-xs text-[#786c5c]">
          Continuous telemetry across all 30 B2B enterprise customer accounts.
        </p>

        {/* View Switcher Capsule */}
        <div className="flex justify-center pt-2">
          <div className="inline-flex items-center p-1 rounded-2xl bg-[#e4dac4] border border-[#d6c8ad] shadow-inner text-xs font-mono">
            <button
              onClick={() => setViewMode('3D_ORBIT')}
              className={`flex items-center gap-2 px-5 py-2 rounded-xl font-bold transition-all cursor-pointer ${
                viewMode === '3D_ORBIT'
                  ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-md'
                  : 'text-[#5e5346] hover:text-[#2d251e]'
              }`}
            >
              <Compass className="w-4 h-4" />
              <span>3D Risk Astrolabe</span>
            </button>
            <button
              onClick={() => setViewMode('GRID')}
              className={`flex items-center gap-2 px-5 py-2 rounded-xl font-bold transition-all cursor-pointer ${
                viewMode === 'GRID'
                  ? 'bg-[#f8f3e8] text-[#2d251e] shadow-md'
                  : 'text-[#5e5346] hover:text-[#2d251e]'
              }`}
            >
              <LayoutGrid className="w-4 h-4" />
              <span>3-Column Fleet Grid</span>
            </button>
          </div>
        </div>
      </div>

      {viewMode === '3D_ORBIT' ? (
        <div className="space-y-6">
          <div className="apple-cockpit-card p-3 shadow-2xl relative overflow-hidden border border-[#d6c8ad]/90 bg-[#1c1917] rounded-3xl">
            <div className="relative w-full h-[580px] rounded-2xl overflow-hidden">
              <Enterprise3DOrbitCanvas
                assessments={assessments}
                selectedCustomerId={selectedOrbitCustomer?.customer.customer_id}
                onSelectCustomer={(a) => {
                  setSelectedOrbitCustomer(a);
                  onSelectCustomer(a);
                }}
                playbookIntensity={orbitIntensity}
                maneuvers={orbitManeuvers}
                astrolabePreset={orbitPreset}
                onPresetChange={setOrbitPreset}
                className="w-full h-full"
              />
            </div>

            {selectedOrbitCustomer && (
              <div className="mt-3 px-4 py-3 rounded-xl bg-stone-900/95 border border-amber-900/40 flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-stone-300">
                <div className="flex items-center gap-3">
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
                  <div>
                    <span className="text-stone-400">Inspecting Node: </span>
                    <strong className="text-white font-display text-sm">{selectedOrbitCustomer.customer.customer_name}</strong>
                    <span className="text-stone-400"> • ${(selectedOrbitCustomer.contract?.annual_contract_value || 0).toLocaleString()} ARR • </span>
                    <span className={
                      selectedOrbitCustomer.risk_level === 'High' ? 'text-rose-400 font-bold' :
                      selectedOrbitCustomer.risk_level === 'Medium' ? 'text-amber-400 font-bold' :
                      'text-emerald-400 font-bold'
                    }>
                      {selectedOrbitCustomer.risk_level} Risk ({selectedOrbitCustomer.risk_score} pts)
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onSelectCustomer(selectedOrbitCustomer)}
                    className="px-3 py-1.5 rounded-lg bg-stone-800 hover:bg-stone-700 text-stone-200 font-medium text-xs border border-stone-700 transition cursor-pointer"
                  >
                    View Full Sheet
                  </button>
                  <button
                    onClick={() => onStartScenario(selectedOrbitCustomer)}
                    className="px-3.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs flex items-center gap-1.5 transition-colors cursor-pointer shadow-sm"
                  >
                    <span>Launch Scenario Lab</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>

          <Enterprise3DPlaybookHUD
            assessments={assessments}
            playbookIntensity={orbitIntensity}
            onIntensityChange={setOrbitIntensity}
            maneuvers={orbitManeuvers}
            onToggleManeuver={handleToggleOrbitManeuver}
          />
        </div>
      ) : (
        <>
          {/* Filter Bar */}
          <div className="apple-cockpit-card p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-[#e4dac4]/90 border border-[#d6c8ad]/80 w-full md:w-80">
          <Search className="w-4 h-4 text-[#8f8270] shrink-0" />
          <input
            type="text"
            placeholder="Search account name, industry, or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent text-xs text-[#2d251e] placeholder-slate-400 w-full focus:outline-none font-medium"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Segment Filter */}
          <div className="flex items-center bg-[#e4dac4] p-1 rounded-full border border-[#d6c8ad] text-xs">
            {(['ALL', 'Enterprise', 'Mid-Market', 'SMB'] as const).map((seg) => (
              <button
                key={seg}
                onClick={() => setSegmentFilter(seg)}
                className={`px-3 py-1 rounded-full font-semibold transition-all ${
                  segmentFilter === seg
                    ? 'bg-[#f8f3e8] text-[#2d251e] shadow-sm'
                    : 'text-[#5e5346] hover:text-[#2d251e]'
                }`}
              >
                {seg}
              </button>
            ))}
          </div>

          {/* Risk Level Filter */}
          <div className="flex items-center bg-[#e4dac4] p-1 rounded-full border border-[#d6c8ad] text-xs">
            {(['ALL', 'High', 'Medium', 'Low'] as const).map((rl) => (
              <button
                key={rl}
                onClick={() => setRiskFilter(rl)}
                className={`px-3 py-1 rounded-full font-semibold transition-all ${
                  riskFilter === rl
                    ? 'bg-[#f8f3e8] text-[#2d251e] shadow-sm'
                    : 'text-[#5e5346] hover:text-[#2d251e]'
                }`}
              >
                {rl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Spatial Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filtered.map((a) => {
          const isHigh = a.risk_level === 'High';
          const isMed = a.risk_level === 'Medium';
          const topFactor = a.factors[0];

          return (
            <div
              key={a.customer.customer_id}
              onClick={() => onSelectCustomer(a)}
              className="apple-cockpit-card p-6 flex flex-col justify-between space-y-4 cursor-pointer group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-[#8f8270]">
                    {a.customer.customer_id}
                  </span>

                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold mono-num border ${
                      isHigh
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : isMed
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    }`}
                  >
                    {a.risk_score} PTS {a.risk_level.toUpperCase()}
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-[#2d251e] group-hover:text-orange-600 transition-colors">
                    {a.customer.customer_name}
                  </h3>
                  <div className="flex items-center gap-1.5 text-xs text-[#786c5c] pt-0.5">
                    <span className="font-semibold text-[#4d4236]">{a.customer.segment}</span>
                    <span>•</span>
                    <span>{a.customer.industry}</span>
                  </div>
                </div>

                {/* Score Progress Bar */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px] text-[#786c5c] font-medium">
                    <span>Renewal Risk</span>
                    <span className="mono-num font-bold text-[#3b3229]">{a.risk_score} / 100</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#e4dac4] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        isHigh ? 'bg-rose-500' : isMed ? 'bg-amber-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${a.risk_score}%` }}
                    />
                  </div>
                </div>

                {/* Top Factor Pill */}
                {topFactor ? (
                  <div className="p-2.5 rounded-xl bg-[#ece3cf] border border-[#d6c8ad]/60 text-xs">
                    <span className="font-bold text-[#3b3229]">{topFactor.name}</span>
                    <p className="text-[11px] text-[#786c5c] truncate pt-0.5" title={topFactor.explanation}>
                      {topFactor.explanation}
                    </p>
                  </div>
                ) : (
                  <div className="p-2.5 rounded-xl bg-emerald-50/60 border border-emerald-100 text-xs text-emerald-700 font-medium flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Nominal Health</span>
                  </div>
                )}
              </div>

              {/* Bottom Details & Actions */}
              <div className="pt-3 border-t border-[#dfd3bc] flex items-center justify-between text-xs">
                <div>
                  <span className="text-[#8f8270]">ARR: </span>
                  <span className="font-bold text-[#2d251e] mono-num">
                    ${((a.contract?.annual_contract_value || 0) / 1000).toFixed(0)}k
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onStartScenario(a);
                    }}
                    className="px-3 py-1 rounded-xl bg-orange-50 text-orange-700 hover:bg-orange-100 font-semibold text-xs transition-colors"
                  >
                    Simulate
                  </button>

                  <ArrowRight className="w-4 h-4 text-[#8f8270] group-hover:text-orange-600 transition-colors" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
        </>
      )}
    </div>
  );
};
