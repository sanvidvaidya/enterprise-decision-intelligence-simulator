import React, { useState, useMemo } from 'react';
import { CustomerAssessment, RiskFactor } from '../types/simulator';
import { SimulatorTab } from './AppleCockpitHeader';
import { 
  LayoutDashboard, 
  Sliders, 
  Users, 
  Settings, 
  ArrowRight, 
  Sparkles, 
  ShieldCheck, 
  DollarSign, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  Check, 
  ChevronRight,
  ShieldAlert,
  Clock,
  Layers,
  Zap,
  Building2,
  MapPin,
  Mail,
  PieChart as PieIcon,
  Activity,
  ArrowUpRight,
  Filter,
  Search,
  UploadCloud,
  Compass
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { Enterprise3DOrbitCanvas, AstrolabePreset, PlaybookManeuvers } from './3d/Enterprise3DOrbitCanvas';
import { Enterprise3DPlaybookHUD } from './3d/Enterprise3DPlaybookHUD';

interface SimulatorLandingPageProps {
  assessments: CustomerAssessment[];
  onNavigateTab: (tab: SimulatorTab) => void;
  onStartScenario: (assessment: CustomerAssessment) => void;
  totalArr: number;
  avgRiskScore: number;
  highRiskCount: number;
  onOpenUpload?: () => void;
  isUsingCustomData?: boolean;
}

// Helper to calculate SVG donut pie segments for a company
interface PieSlice {
  label: string;
  points: number;
  percent: number;
  color: string;
  dashArray: string;
  dashOffset: number;
}

function computeCompanyPie(factors: RiskFactor[], riskScore: number): PieSlice[] {
  const circum = 2 * Math.PI * 40; // radius = 40, circum ≈ 251.32

  let usagePts = 0;
  let supportPts = 0;
  let renewalPts = 0;
  let otherPts = 0;

  factors.forEach((f) => {
    const n = f.name.toLowerCase();
    if (n.includes('usage') || n.includes('seat')) usagePts += f.points;
    else if (n.includes('support') || n.includes('ticket')) supportPts += f.points;
    else if (n.includes('renewal')) renewalPts += f.points;
    else otherPts += f.points;
  });

  const healthyPts = Math.max(15, 100 - riskScore);
  const total = usagePts + supportPts + renewalPts + otherPts + healthyPts;

  const rawSlices = [
    { label: 'Healthy Baseline', points: healthyPts, color: '#10b981' }, // Emerald
    { label: 'Usage Decline', points: usagePts, color: '#d97706' },     // Blue
    { label: 'Critical Support', points: supportPts, color: '#c2410c' },// Violet
    { label: 'Renewal Horizon', points: renewalPts, color: '#f59e0b' }, // Amber
    { label: 'Commercial ACV', points: otherPts, color: '#ef4444' },    // Rose
  ].filter(s => s.points > 0);

  let currentOffset = 0;
  return rawSlices.map((s) => {
    const pct = s.points / total;
    const strokeLen = pct * circum;
    const dashArray = `${strokeLen} ${circum - strokeLen}`;
    const dashOffset = -currentOffset;
    currentOffset += strokeLen;
    return {
      label: s.label,
      points: s.points,
      percent: Math.round(pct * 100),
      color: s.color,
      dashArray,
      dashOffset,
    };
  });
}

export const SimulatorLandingPage: React.FC<SimulatorLandingPageProps> = ({
  assessments,
  onNavigateTab,
  onStartScenario,
  totalArr,
  avgRiskScore,
  highRiskCount,
  onOpenUpload,
  isUsingCustomData,
}) => {
  // Filter state for company showcase
  const [verdictFilter, setVerdictFilter] = useState<'ALL' | 'GOOD' | 'WATCHLIST' | 'NOT_GOOD'>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Active story section indicator
  const [activeStoryChapter, setActiveStoryChapter] = useState<string>('chapter-hero');

  // Spotlight account for hero sandbox
  const spotlight = assessments.find(a => a.customer.customer_name === 'Juniper Labs') || assessments[0];

  // Interactive Hero Playground State
  const [interventionLevel, setInterventionLevel] = useState<number>(0);
  const [hasCelebrated, setHasCelebrated] = useState<boolean>(false);

  // 3D Celestial Orbit & Revenue Gravity State
  const [sandboxMode, setSandboxMode] = useState<'3D_ORBIT' | 'CLASSIC'>('3D_ORBIT');
  const [orbitIntensity, setOrbitIntensity] = useState<number>(40);
  const [orbitManeuvers, setOrbitManeuvers] = useState<PlaybookManeuvers>({
    execSponsor: true,
    architect: false,
    discount: false,
    featureFreeze: false,
  });
  const [orbitPreset, setOrbitPreset] = useState<AstrolabePreset>('PERSPECTIVE');
  const [selectedOrbitCustomer, setSelectedOrbitCustomer] = useState<CustomerAssessment | undefined>(spotlight);

  const handleToggleOrbitManeuver = (key: keyof PlaybookManeuvers) => {
    setOrbitManeuvers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const initialPoints = spotlight ? spotlight.risk_score : 75;
  const simulatedScore = Math.max(20, Math.round(initialPoints - (interventionLevel * 0.55)));
  const isProtected = simulatedScore <= 35;
  const protectedArr = spotlight?.contract?.annual_contract_value || 142000;

  const handleSliderChange = (val: number) => {
    setInterventionLevel(val);
    if (val >= 75 && !hasCelebrated) {
      setHasCelebrated(true);
      confetti({
        particleCount: 60,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#d97706', '#c2410c', '#15803d', '#2d251e']
      });
    } else if (val < 75) {
      setHasCelebrated(false);
    }
  };

  // Group assessments into verdicts
  const goodToGo = useMemo(() => assessments.filter(a => a.risk_level === 'Low'), [assessments]);
  const watchlist = useMemo(() => assessments.filter(a => a.risk_level === 'Medium'), [assessments]);
  const notGoodToGo = useMemo(() => assessments.filter(a => a.risk_level === 'High'), [assessments]);

  // Filtered companies
  const displayedCompanies = useMemo(() => {
    let list = assessments;
    if (verdictFilter === 'GOOD') list = goodToGo;
    if (verdictFilter === 'WATCHLIST') list = watchlist;
    if (verdictFilter === 'NOT_GOOD') list = notGoodToGo;

    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      list = list.filter(a => 
        a.customer.customer_name.toLowerCase().includes(q) ||
        a.customer.industry.toLowerCase().includes(q) ||
        a.customer.segment.toLowerCase().includes(q) ||
        (a.customer.account_manager_name && a.customer.account_manager_name.toLowerCase().includes(q))
      );
    }
    return list;
  }, [assessments, verdictFilter, goodToGo, watchlist, notGoodToGo, searchTerm]);

  return (
    <div className="relative min-h-screen pt-10 pb-28 space-y-28 overflow-hidden">
      {/* ============================================================ */}
      {/* 4-SIDE AMBIENT PERIMETER & TELEMETRY RAILS                   */}
      {/* ============================================================ */}

      {/* Left Edge: Floating Vertical Story Navigation Rail */}
      <aside className="fixed left-4 top-1/2 -translate-y-1/2 z-40 hidden 2xl:flex flex-col items-center gap-3 p-2 rounded-full apple-dynamic-island shadow-lg">
        <a 
          href="#chapter-hero" 
          title="01 Overview"
          className="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-mono font-bold text-[#5e5346] hover:text-orange-600 hover:bg-orange-50 transition-all"
        >
          01
        </a>
        <div className="w-2 h-px bg-[#ded2ba]" />
        <a 
          href="#chapter-sandbox" 
          title="02 60fps Sandbox"
          className="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-mono font-bold text-[#5e5346] hover:text-orange-600 hover:bg-orange-50 transition-all"
        >
          02
        </a>
        <div className="w-2 h-px bg-[#ded2ba]" />
        <a 
          href="#chapter-companies" 
          title="03 Company Dossiers & Pie Charts"
          className="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-mono font-bold text-[#5e5346] hover:text-orange-600 hover:bg-orange-50 transition-all"
        >
          03
        </a>
        <div className="w-2 h-px bg-[#ded2ba]" />
        <a 
          href="#chapter-modules" 
          title="04 Executive Modules"
          className="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-mono font-bold text-[#5e5346] hover:text-orange-600 hover:bg-orange-50 transition-all"
        >
          04
        </a>
      </aside>

      {/* Right Edge: Live Portfolio Fleet Pulse Badge */}
      <aside className="fixed right-4 top-1/2 -translate-y-1/2 z-40 hidden 2xl:flex flex-col gap-2 p-3 rounded-2xl apple-dynamic-island shadow-xl text-[11px] font-mono">
        <div className="text-[10px] font-bold text-[#8f8270] uppercase tracking-wider mb-1">
          Fleet Health Pulse
        </div>
        <div className="flex items-center justify-between gap-3 text-emerald-700 bg-emerald-50 px-2 py-1 rounded-lg">
          <span className="flex items-center gap-1.5 font-bold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Good to Go
          </span>
          <span className="font-bold">{goodToGo.length}</span>
        </div>
        <div className="flex items-center justify-between gap-3 text-amber-700 bg-amber-50 px-2 py-1 rounded-lg">
          <span className="flex items-center gap-1.5 font-bold">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            Watchlist
          </span>
          <span className="font-bold">{watchlist.length}</span>
        </div>
        <div className="flex items-center justify-between gap-3 text-rose-700 bg-rose-50 px-2 py-1 rounded-lg">
          <span className="flex items-center gap-1.5 font-bold">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            Not Good
          </span>
          <span className="font-bold">{notGoodToGo.length}</span>
        </div>
        <div className="pt-2 border-t border-[#d6c8ad]/60 text-[#786c5c] text-[10px] text-center">
          ${(totalArr / 1_000_000).toFixed(2)}M Monitored
        </div>
      </aside>

      {/* ============================================================ */}
      {/* 1. HERO SECTION (Apple Luminous & Google Stitch)             */}
      {/* ============================================================ */}
      <section id="chapter-hero" className="text-center max-w-4xl mx-auto space-y-8 px-4">
        {/* Status Capsule */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full apple-dynamic-island text-xs font-mono font-semibold text-orange-600 border border-orange-200/80 shadow-[0_2px_15px_rgba(217,119,6,0.15)]">
          <span className="w-2 h-2 rounded-full bg-orange-600 animate-pulse" />
          <span>ENTERPRISE DECISION SIMULATOR • REVENUE RETENTION INTELLIGENCE</span>
          <span className="text-slate-300">|</span>
          <span className="text-[#786c5c] font-sans">30 Accounts Monitored</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black font-display tracking-tight text-[#1f1a16] leading-[1.08]">
          Spot customer cancellations{' '}
          <span className="apple-title-gradient block mt-1">
            months before they happen.
          </span>
        </h1>

        {/* Hero Subtitle */}
        <p className="text-base sm:text-xl text-[#5e5346] max-w-2xl mx-auto font-sans leading-relaxed">
          Track health signals across 30 enterprise accounts. See why customers are unhappy, test turnaround playbooks on an interactive slider, and protect revenue before renewals come due.
        </p>

        {/* Dual Primary Actions */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <button
            onClick={() => onNavigateTab('COCKPIT')}
            className="px-8 py-4 rounded-full bg-gradient-to-r from-[#241e19] via-[#451a03] to-[#78350f] text-white font-bold text-sm flex items-center gap-2.5 hover:shadow-[0_4px_25px_rgba(217,119,6,0.35)] active:scale-[0.96] transition-all cursor-pointer"
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Open Executive Cockpit</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <a
            href="#chapter-companies"
            className="px-7 py-4 rounded-full apple-dynamic-island hover:bg-[#e4dac4] text-[#3b3229] font-semibold text-sm flex items-center gap-2 border border-[#d6c8ad] active:scale-[0.96] transition-all cursor-pointer"
          >
            <PieIcon className="w-4 h-4 text-orange-600" />
            <span>Explore Company Risk Charts</span>
          </a>

          {onOpenUpload && (
            <button
              onClick={onOpenUpload}
              className="px-7 py-4 rounded-full bg-[#f4ece0] hover:bg-[#e4dac4] text-[#2d251e] font-bold text-sm flex items-center gap-2 border border-[#d6c8ad] active:scale-[0.96] transition-all cursor-pointer shadow-xs"
            >
              <UploadCloud className="w-4 h-4 text-orange-600" />
              <span>{isUsingCustomData ? 'Custom Data Active (Upload More)' : 'Upload Physical Data (.csv / .json)'}</span>
            </button>
          )}
        </div>
      </section>

      {/* ============================================================ */}
      {/* 2. INTERACTIVE HERO SANDBOX & 3D EXECUTIVE DECISION ORBIT     */}
      {/* ============================================================ */}
      <section id="chapter-sandbox" className="max-w-6xl mx-auto px-4 space-y-4">
        {/* Section Header with Segmented View Switcher */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 border border-orange-200/90 text-orange-700 text-xs font-mono font-bold tracking-wider uppercase shadow-xs">
              <Sparkles className="w-3.5 h-3.5 text-orange-600" />
              <span>Chapter 02 • Real-Time Retention Simulation</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-display font-extrabold text-[#2d251e] tracking-tight mt-1.5">
              {sandboxMode === '3D_ORBIT' ? '3D Executive Decision Orbit & Revenue Gravity' : 'Live 60 FPS Simulation Sandbox'}
            </h2>
            <p className="text-xs text-[#786c5c] mt-0.5">
              {sandboxMode === '3D_ORBIT'
                ? 'Deterministic celestial astrolabe: 30 enterprise accounts orbiting customer retention gravity with real-time recovery physics.'
                : `Interactive model turnaround for ${spotlight?.customer.customer_name} ($${protectedArr.toLocaleString()} ARR).`}
            </p>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center p-1 rounded-2xl bg-[#e4dac4] border border-[#d6c8ad] shadow-inner text-xs font-mono shrink-0">
            <button
              onClick={() => setSandboxMode('3D_ORBIT')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-bold transition-all cursor-pointer ${
                sandboxMode === '3D_ORBIT'
                  ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-md'
                  : 'text-[#5e5346] hover:text-[#2d251e]'
              }`}
            >
              <Compass className="w-4 h-4" />
              <span>3D Decision Orbit</span>
            </button>
            <button
              onClick={() => setSandboxMode('CLASSIC')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-bold transition-all cursor-pointer ${
                sandboxMode === 'CLASSIC'
                  ? 'bg-[#f8f3e8] text-[#2d251e] shadow-md'
                  : 'text-[#5e5346] hover:text-[#2d251e]'
              }`}
            >
              <Sliders className="w-4 h-4" />
              <span>Classic Sandbox</span>
            </button>
          </div>
        </div>

        {sandboxMode === '3D_ORBIT' ? (
          <div className="space-y-4">
            {/* 3D WebGL Canvas Card */}
            <div className="apple-cockpit-card p-3 shadow-2xl relative overflow-hidden border border-[#d6c8ad]/90 bg-[#1c1917] rounded-3xl">
              <div className="relative w-full h-[520px] rounded-2xl overflow-hidden">
                <Enterprise3DOrbitCanvas
                  assessments={assessments}
                  selectedCustomerId={selectedOrbitCustomer?.customer.customer_id}
                  onSelectCustomer={(a) => {
                    setSelectedOrbitCustomer(a);
                  }}
                  playbookIntensity={orbitIntensity}
                  maneuvers={orbitManeuvers}
                  astrolabePreset={orbitPreset}
                  onPresetChange={setOrbitPreset}
                  className="w-full h-full"
                />
              </div>

              {/* Selected account quick-bar */}
              {selectedOrbitCustomer && (
                <div className="mt-3 px-4 py-3 rounded-xl bg-stone-900/95 border border-amber-900/40 flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-stone-300">
                  <div className="flex items-center gap-3">
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
                    <div>
                      <span className="text-stone-400">Selected Node: </span>
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

                  <button
                    onClick={() => onStartScenario(selectedOrbitCustomer)}
                    className="px-3.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs flex items-center gap-1.5 transition-colors cursor-pointer shadow-sm"
                  >
                    <span>Launch Scenario Lab</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>

            {/* Playbook Turnaround Levers HUD */}
            <Enterprise3DPlaybookHUD
              assessments={assessments}
              playbookIntensity={orbitIntensity}
              onIntensityChange={setOrbitIntensity}
              maneuvers={orbitManeuvers}
              onToggleManeuver={handleToggleOrbitManeuver}
            />
          </div>
        ) : (
          <div className="apple-cockpit-card p-6 sm:p-8 text-left shadow-2xl relative overflow-hidden border border-[#d6c8ad]/90 bg-gradient-to-br from-[#f8f3e8]/95 via-amber-50/30 to-orange-50/20">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#dfd3bc] pb-5">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-orange-600 to-amber-600 text-white flex items-center justify-center shadow-[0_4px_14px_rgba(217,119,6,0.35)]">
                  <Sliders className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-[11px] font-mono font-bold text-orange-600 uppercase tracking-wider">
                    Live 60 FPS Simulation Sandbox
                  </div>
                  <div className="text-base font-bold text-[#2d251e] font-display">
                    Model Turnaround for {spotlight?.customer.customer_name} (${protectedArr.toLocaleString()} ARR)
                  </div>
                </div>
              </div>

              {/* Live Status Pill */}
              <div className="flex items-center gap-3 bg-[#f8f3e8] px-4 py-2 rounded-2xl border border-[#d6c8ad]/80 shadow-sm">
                <div className="text-right">
                  <div className="text-[10px] font-mono text-[#8f8270] uppercase">Simulated Risk</div>
                  <div className={`text-lg font-black font-mono ${
                    simulatedScore > 50 ? 'text-rose-600' : simulatedScore > 35 ? 'text-amber-600' : 'text-emerald-600'
                  }`}>
                    {simulatedScore} PTS
                  </div>
                </div>
                <div className={`w-3.5 h-3.5 rounded-full ${
                  simulatedScore > 50 ? 'bg-rose-500 animate-ping' : simulatedScore > 35 ? 'bg-amber-500' : 'bg-emerald-500'
                }`} />
              </div>
            </div>

            {/* Slider Controls */}
            <div className="py-6 space-y-6">
              <div className="space-y-3">
                <div className="flex justify-between items-baseline">
                  <label className="text-xs font-bold text-[#3b3229] font-sans flex items-center gap-2">
                    <span>Executive Playbook Intensity</span>
                    <span className="font-mono text-orange-600 font-semibold text-[11px]">
                      ({interventionLevel}%)
                    </span>
                  </label>
                  <span className="text-[11px] font-mono text-[#8f8270]">
                    Slide right for instant 60fps recovery
                  </span>
                </div>

                <input
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  value={interventionLevel}
                  onChange={(e) => handleSliderChange(Number(e.target.value))}
                  className="w-full accent-orange-600 cursor-pointer h-2.5 bg-[#ded2ba]/80 rounded-lg appearance-none"
                />

                <div className="flex justify-between text-[10px] font-mono text-[#786c5c]">
                  <span>0% (Status Quo: P1 Outage &amp; -42% Usage)</span>
                  <span>50% (P1 Incident Resolved)</span>
                  <span>100% (Full Seat Adoption + SLA Buffer)</span>
                </div>
              </div>

              {/* Impact Banner */}
              <div className={`p-4 rounded-2xl border transition-all duration-300 flex items-center justify-between ${
                isProtected
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-950 shadow-sm'
                  : 'bg-[#f8f3e8] border-[#d6c8ad] text-[#3b3229]'
              }`}>
                <div className="flex items-center gap-3">
                  {isProtected ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                  ) : (
                    <Zap className="w-5 h-5 text-orange-600 shrink-0" />
                  )}
                  <div className="text-xs font-sans">
                    {isProtected ? (
                      <span>
                        🎉 <strong>VERDICT: GOOD TO GO!</strong> High-risk churn neutralized. Protected <strong>${protectedArr.toLocaleString()} ARR</strong> with zero server latency.
                      </span>
                    ) : (
                      <span>
                        Drag intensity beyond 70% to trigger <strong>Good to Go</strong> status.
                      </span>
                    )}
                  </div>
                </div>

                {spotlight && (
                  <button
                    onClick={() => onStartScenario(spotlight)}
                    className="text-xs font-mono font-bold text-orange-600 hover:text-orange-700 flex items-center gap-1 cursor-pointer shrink-0 ml-3 bg-orange-50 hover:bg-orange-100 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    <span>Open Full Lab</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </section>

      {/* ============================================================ */}
      {/* 3. METRICS STRIP ACROSS PORTFOLIO                            */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="apple-cockpit-card p-6 border border-[#d6c8ad]/80 grid grid-cols-2 md:grid-cols-4 gap-6 text-center divide-y md:divide-y-0 md:divide-x divide-slate-100 bg-[#f8f3e8]/80">
          <div className="pt-4 md:pt-0">
            <div className="text-3xl lg:text-4xl font-black font-mono text-[#1f1a16]">
              ${(totalArr / 1_000_000).toFixed(2)}M
            </div>
            <div className="text-xs font-bold text-[#786c5c] uppercase font-sans mt-1">Total Monitored ARR</div>
            <div className="text-[11px] text-[#8f8270] font-mono">30 Enterprise SaaS Accounts</div>
          </div>

          <div className="pt-4 md:pt-0">
            <div className="text-3xl lg:text-4xl font-black font-mono text-emerald-600">
              {goodToGo.length}
            </div>
            <div className="text-xs font-bold text-[#786c5c] uppercase font-sans mt-1">Good to Go Accounts</div>
            <div className="text-[11px] text-[#8f8270] font-mono">Zero Critical Blockers</div>
          </div>

          <div className="pt-4 md:pt-0">
            <div className="text-3xl lg:text-4xl font-black font-mono text-amber-500">
              {watchlist.length}
            </div>
            <div className="text-xs font-bold text-[#786c5c] uppercase font-sans mt-1">Watchlist Accounts</div>
            <div className="text-[11px] text-[#8f8270] font-mono">Approaching Renewal Horizon</div>
          </div>

          <div className="pt-4 md:pt-0">
            <div className="text-3xl lg:text-4xl font-black font-mono text-rose-600">
              {notGoodToGo.length}
            </div>
            <div className="text-xs font-bold text-[#786c5c] uppercase font-sans mt-1">Not Good to Go</div>
            <div className="text-[11px] text-[#8f8270] font-mono">Requires Immediate Executive Action</div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 4. COMPANY DOSSIERS WITH CIRCULAR PIE CHARTS (USER REQUEST)   */}
      {/* ============================================================ */}
      <section id="chapter-companies" className="max-w-6xl mx-auto px-4 space-y-10">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-orange-50 text-orange-600 text-[11px] font-bold font-mono border border-orange-200">
              <PieIcon className="w-3.5 h-3.5" />
              <span>COMPANY RISK DOSSIERS &amp; PIE CHARTS</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-black font-display text-[#1f1a16] tracking-tight">
              Is Each Company Good to Go?
            </h2>
            <p className="text-xs sm:text-sm text-[#786c5c] font-sans max-w-xl">
              Inspect circular risk breakdowns, team ownership, and mathematical health verdicts across your entire customer portfolio.
            </p>
          </div>

          {/* Verdict Filter Controls */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setVerdictFilter('ALL')}
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                verdictFilter === 'ALL'
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-[#f8f3e8] text-[#5e5346] hover:bg-[#e4dac4] border border-[#d6c8ad]'
              }`}
            >
              All ({assessments.length})
            </button>
            <button
              onClick={() => setVerdictFilter('GOOD')}
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                verdictFilter === 'GOOD'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
              }`}
            >
              🟢 Good to Go ({goodToGo.length})
            </button>
            <button
              onClick={() => setVerdictFilter('WATCHLIST')}
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                verdictFilter === 'WATCHLIST'
                  ? 'bg-amber-500 text-white shadow-sm'
                  : 'bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200'
              }`}
            >
              🟡 Watchlist ({watchlist.length})
            </button>
            <button
              onClick={() => setVerdictFilter('NOT_GOOD')}
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                verdictFilter === 'NOT_GOOD'
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200'
              }`}
            >
              🔴 Not Good ({notGoodToGo.length})
            </button>

            {onOpenUpload && (
              <button
                onClick={onOpenUpload}
                className="px-3.5 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 bg-gradient-to-r from-orange-600 to-amber-600 hover:opacity-95 text-white shadow-xs"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                <span>Upload .CSV / .JSON</span>
              </button>
            )}
          </div>
        </div>

        {/* Company Cards Grid with Circular Pie Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayedCompanies.map((assessment) => {
            const { customer, contract, risk_score, risk_level, factors, recommended_actions } = assessment;
            const isGood = risk_level === 'Low';
            const isWatch = risk_level === 'Medium';
            const isNotGood = risk_level === 'High';

            const pieSlices = computeCompanyPie(factors, risk_score);

            return (
              <div
                key={customer.customer_id}
                className="apple-cockpit-card p-6 space-y-5 border border-[#d6c8ad]/90 hover:border-orange-300 transition-all flex flex-col justify-between group"
              >
                {/* Top Company Info & Verdict Stamp */}
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="font-mono text-[10px] font-bold text-[#8f8270] bg-[#e4dac4] px-2 py-0.5 rounded">
                        {customer.customer_id} • {customer.segment}
                      </span>
                      <h3 className="text-lg font-black text-[#2d251e] font-display mt-1">
                        {customer.customer_name}
                      </h3>
                      <div className="text-[11px] text-[#786c5c] flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-[#8f8270]" />
                        <span>{customer.industry}</span>
                        <span>•</span>
                        <span>{customer.region}</span>
                      </div>
                    </div>

                    {/* Verdict Stamp */}
                    <span
                      className={`px-3 py-1 rounded-full text-[11px] font-mono font-bold shrink-0 border shadow-xs ${
                        isGood
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : isWatch
                          ? 'bg-amber-50 text-amber-700 border-amber-200'
                          : 'bg-rose-50 text-rose-700 border-rose-200 animate-pulse'
                      }`}
                    >
                      {isGood ? '🟢 GOOD TO GO' : isWatch ? '🟡 WATCHLIST' : '🔴 NOT GOOD'}
                    </span>
                  </div>

                  {/* Circular Pie Chart & Factor Breakdown */}
                  <div className="p-4 rounded-2xl bg-[#ece3cf]/90 border border-[#d6c8ad]/70 flex items-center gap-4">
                    {/* SVG Donut / Pie Chart */}
                    <div className="relative w-24 h-24 shrink-0 flex items-center justify-center">
                      <svg viewBox="0 0 100 100" className="w-24 h-24 -rotate-90">
                        {/* Background track circle */}
                        <circle
                          cx="50"
                          cy="50"
                          r="40"
                          fill="transparent"
                          stroke="#e2e8f0"
                          strokeWidth="14"
                        />
                        {/* Render individual slices */}
                        {pieSlices.map((slice, idx) => (
                          <circle
                            key={idx}
                            cx="50"
                            cy="50"
                            r="40"
                            fill="transparent"
                            stroke={slice.color}
                            strokeWidth="14"
                            strokeDasharray={slice.dashArray}
                            strokeDashoffset={slice.dashOffset}
                            className="pie-segment"
                          />
                        ))}
                      </svg>
                      {/* Center Score */}
                      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                        <span className={`text-base font-black font-mono ${
                          isGood ? 'text-emerald-600' : isWatch ? 'text-amber-600' : 'text-rose-600'
                        }`}>
                          {risk_score}
                        </span>
                        <span className="text-[9px] font-mono text-[#8f8270] uppercase">PTS</span>
                      </div>
                    </div>

                    {/* Slice Legend */}
                    <div className="flex-1 text-[11px] space-y-1">
                      <div className="font-bold text-[#4d4236] text-[10px] uppercase font-mono mb-1">
                        Risk &amp; Health Pie:
                      </div>
                      {pieSlices.slice(0, 3).map((s, idx) => (
                        <div key={idx} className="flex items-center justify-between text-[#5e5346]">
                          <span className="flex items-center gap-1.5 truncate">
                            <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
                            <span className="truncate">{s.label}</span>
                          </span>
                          <span className="font-mono font-bold text-[#3b3229] ml-1">{s.percent}%</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Financial Runway & People Stats */}
                  <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                    <div className="p-2.5 rounded-xl bg-[#f8f3e8] border border-[#dfd3bc]">
                      <span className="text-[10px] font-mono text-[#8f8270] uppercase">Contract ARR</span>
                      <div className="font-mono font-bold text-[#2d251e] mt-0.5">
                        ${contract ? contract.annual_contract_value.toLocaleString() : 'N/A'}
                      </div>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[#f8f3e8] border border-[#dfd3bc]">
                      <span className="text-[10px] font-mono text-[#8f8270] uppercase">Renewal Date</span>
                      <div className="font-mono font-bold text-[#2d251e] mt-0.5">
                        {contract ? contract.renewal_date : 'Active'}
                      </div>
                    </div>
                  </div>

                  {/* Account Lead Info */}
                  <div className="flex items-center justify-between text-[11px] text-[#786c5c] pt-1 border-t border-[#dfd3bc]">
                    <div className="flex items-center gap-1.5">
                      <div className="w-5 h-5 rounded-full bg-orange-100 text-orange-700 flex items-center justify-center font-bold text-[9px]">
                        {customer.account_manager_name ? customer.account_manager_name.charAt(0) : 'A'}
                      </div>
                      <span className="font-medium text-[#4d4236] truncate">
                        {customer.account_manager_name || 'Assigned Lead'}
                      </span>
                    </div>
                    <span className="font-mono text-[#8f8270]">
                      {customer.employee_count.toLocaleString()} seats
                    </span>
                  </div>
                </div>

                {/* Card Action */}
                <button
                  onClick={() => onStartScenario(assessment)}
                  className="w-full mt-4 py-2.5 px-4 rounded-xl bg-[#e4dac4] hover:bg-orange-600 hover:text-white text-[#4d4236] text-xs font-semibold flex items-center justify-center gap-2 transition-all apple-spring-press cursor-pointer"
                >
                  <Sliders className="w-3.5 h-3.5" />
                  <span>Simulate This Account in Lab</span>
                  <ArrowUpRight className="w-3 h-3 opacity-60" />
                </button>
              </div>
            );
          })}
        </div>
      </section>

      {/* ============================================================ */}
      {/* 5. 4-STAGE BENTO GRID SHOWCASE                                */}
      {/* ============================================================ */}
      <section id="chapter-modules" className="max-w-6xl mx-auto px-4 space-y-10">
        <div className="text-center space-y-3">
          <div className="text-xs font-mono font-bold text-orange-600 uppercase tracking-wider">
            Decision Intelligence Architecture
          </div>
          <h2 className="text-3xl sm:text-5xl font-black font-display text-[#1f1a16] tracking-tight">
            Designed for Revenue Operations &amp; C-Suite
          </h2>
          <p className="text-sm sm:text-base text-[#786c5c] max-w-2xl mx-auto font-sans">
            Four specialized modules that transform reactive spreadsheet reviews into an interactive, real-time mathematical cockpit.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 1: Executive Cockpit */}
          <div 
            onClick={() => onNavigateTab('COCKPIT')}
            className="apple-cockpit-card p-8 rounded-3xl space-y-5 group cursor-pointer hover:border-orange-400/60 relative overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 rounded-2xl bg-orange-50 text-orange-600 border border-orange-200 flex items-center justify-center">
                <LayoutDashboard className="w-6 h-6" />
              </div>
              <span className="font-mono text-xs font-bold text-[#8f8270] group-hover:text-orange-600 transition-colors flex items-center gap-1">
                <span>Open Cockpit</span>
                <ChevronRight className="w-4 h-4" />
              </span>
            </div>

            <div className="space-y-2">
              <h3 className="text-2xl font-bold font-display text-[#1f1a16] group-hover:text-orange-600 transition-colors">
                Executive Bento Cockpit
              </h3>
              <p className="text-xs text-[#786c5c] leading-relaxed font-sans">
                Priority account spotlight on Juniper Labs, 3D concentric risk dial, and frosted metric tiles showing total portfolio exposure at a glance.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#ece3cf] border border-[#dfd3bc] font-mono text-[11px] text-[#5e5346] space-y-1">
              <div className="flex justify-between text-[#3b3229]">
                <span>Spotlight: Juniper Labs</span>
                <span className="text-rose-600 font-bold">$142k ARR at Risk</span>
              </div>
              <div className="text-[#8f8270]">Includes Concentric Risk Donut &amp; Quick Playbook Rail</div>
            </div>
          </div>

          {/* Card 2: 60fps Scenario Lab */}
          <div 
            onClick={() => onNavigateTab('SCENARIO_LAB')}
            className="apple-cockpit-card p-8 rounded-3xl space-y-5 group cursor-pointer hover:border-amber-400/60 relative overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center">
                <Sliders className="w-6 h-6" />
              </div>
              <span className="font-mono text-xs font-bold text-[#8f8270] group-hover:text-amber-700 transition-colors flex items-center gap-1">
                <span>Enter Lab</span>
                <ChevronRight className="w-4 h-4" />
              </span>
            </div>

            <div className="space-y-2">
              <h3 className="text-2xl font-bold font-display text-[#1f1a16] group-hover:text-amber-700 transition-colors">
                60 FPS Client-Side Scenario Lab
              </h3>
              <p className="text-xs text-[#786c5c] leading-relaxed font-sans">
                Experiment with user adoption recovery, support incident turnaround, and contract extension buffers. Immediate sub-millisecond math.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#ece3cf] border border-[#dfd3bc] font-mono text-[11px] text-[#5e5346] space-y-1">
              <div className="flex justify-between text-[#3b3229]">
                <span>Tactile Physics Sliders</span>
                <span className="text-amber-700 font-bold">0ms Server Lag</span>
              </div>
              <div className="text-[#8f8270]">Features "Commit Playbook &amp; Save ARR" Confetti Action</div>
            </div>
          </div>

          {/* Card 3: Portfolio Matrix */}
          <div 
            onClick={() => onNavigateTab('PORTFOLIO')}
            className="apple-cockpit-card p-8 rounded-3xl space-y-5 group cursor-pointer hover:border-emerald-400/60 relative overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-100 flex items-center justify-center">
                <Users className="w-6 h-6" />
              </div>
              <span className="font-mono text-xs font-bold text-[#8f8270] group-hover:text-emerald-600 transition-colors flex items-center gap-1">
                <span>View Accounts</span>
                <ChevronRight className="w-4 h-4" />
              </span>
            </div>

            <div className="space-y-2">
              <h3 className="text-2xl font-bold font-display text-[#1f1a16] group-hover:text-emerald-600 transition-colors">
                Account Portfolio Matrix
              </h3>
              <p className="text-xs text-[#786c5c] leading-relaxed font-sans">
                Spatial cards replacing plain tables. Instant search and segment filtering across Enterprise, Mid-Market, and SMB tiers.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#ece3cf] border border-[#dfd3bc] font-mono text-[11px] text-[#5e5346] space-y-1">
              <div className="flex justify-between text-[#3b3229]">
                <span>30 Monitored Accounts</span>
                <span className="text-emerald-600 font-bold">1-Click Customer 360</span>
              </div>
              <div className="text-[#8f8270]">Micro health bars &amp; instant playbook assignment</div>
            </div>
          </div>

          {/* Card 4: Policy Governance */}
          <div 
            onClick={() => onNavigateTab('GOVERNANCE')}
            className="apple-cockpit-card p-8 rounded-3xl space-y-5 group cursor-pointer hover:border-amber-400/60 relative overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 border border-amber-100 flex items-center justify-center">
                <Settings className="w-6 h-6" />
              </div>
              <span className="font-mono text-xs font-bold text-[#8f8270] group-hover:text-amber-600 transition-colors flex items-center gap-1">
                <span>Tune Policy</span>
                <ChevronRight className="w-4 h-4" />
              </span>
            </div>

            <div className="space-y-2">
              <h3 className="text-2xl font-bold font-display text-[#1f1a16] group-hover:text-amber-600 transition-colors">
                Dual-Custody Policy Governance
              </h3>
              <p className="text-xs text-[#786c5c] leading-relaxed font-sans">
                Tune risk band thresholds and telemetry penalty weights. Real-time portfolio impact simulation with cryptographic audit hash.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#ece3cf] border border-[#dfd3bc] font-mono text-[11px] text-[#5e5346] space-y-1">
              <div className="flex justify-between text-[#3b3229]">
                <span>Maker-Checker Audit Trail</span>
                <span className="text-amber-600 font-bold">Policy v2.4 Active</span>
              </div>
              <div className="text-[#8f8270]">Mathematically reproducible scoring across entire fleet</div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 6. BOTTOM BANNER & LIVE TICKER                                */}
      {/* ============================================================ */}
      <section className="max-w-4xl mx-auto px-4 text-center space-y-6">
        <div className="apple-cockpit-card p-8 sm:p-12 border border-orange-300 relative overflow-hidden space-y-6 shadow-xl bg-gradient-to-r from-orange-50/50 via-amber-50/30 to-[#ede4d0]">
          <div className="space-y-3">
            <h2 className="text-3xl sm:text-4xl font-black font-display text-[#1f1a16]">
              Eliminate Enterprise Churn Surprises Today
            </h2>
            <p className="text-sm text-[#5e5346] max-w-xl mx-auto font-sans">
              Enter the full executive cockpit to model risk distributions, simulate playbooks, and secure high-risk customer renewals.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <button
              onClick={() => onNavigateTab('COCKPIT')}
              className="px-8 py-4 rounded-full bg-orange-600 text-white font-bold text-sm flex items-center gap-2 hover:bg-orange-700 active:scale-[0.96] shadow-[0_4px_20px_rgba(217,119,6,0.35)] transition-all cursor-pointer"
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Enter Executive Cockpit</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Perimeter Bottom Ticker */}
        <div className="apple-dynamic-island py-2 px-4 rounded-full max-w-2xl mx-auto flex items-center justify-between text-[11px] font-mono text-[#786c5c]">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>PORTFOLIO FEED: 30 ACCOUNTS SYNCHRONIZED</span>
          </div>
          <div className="hidden sm:block text-[#8f8270]">
            AUDIT HASH: 0x9B4...F2A
          </div>
        </div>
      </section>
    </div>
  );
};
