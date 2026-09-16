import React, { useState, useMemo, useEffect } from 'react';
import {
  CustomerAssessment,
  PolicyParameters,
  UsageEvent,
  SupportTicket,
} from '../types/simulator';
import { evaluateCustomerRisk } from '../lib/riskEngine';
import { Sliders, RotateCcw, CheckCircle2, ArrowRight, Sparkles, ShieldCheck, DollarSign } from 'lucide-react';
import confetti from 'canvas-confetti';
import { toast } from 'sonner';

interface AppleScenarioLabProps {
  assessments: CustomerAssessment[];
  policy: PolicyParameters;
  allUsage: UsageEvent[];
  allTickets: SupportTicket[];
  initialSelectedCustomer?: CustomerAssessment | null;
}

export const AppleScenarioLab: React.FC<AppleScenarioLabProps> = ({
  assessments,
  policy,
  allUsage,
  allTickets,
  initialSelectedCustomer,
}) => {
  const defaultCustomer =
    initialSelectedCustomer ||
    [...assessments].sort((a, b) => b.risk_score - a.risk_score)[0] ||
    assessments[0];

  const [selectedCustomerId, setSelectedCustomerId] = useState<string>(
    defaultCustomer?.customer.customer_id || ''
  );

  const currentAssessment =
    assessments.find((a) => a.customer.customer_id === selectedCustomerId) || defaultCustomer;

  const customerUsage = useMemo(
    () => allUsage.filter((u) => u.customer_id === selectedCustomerId),
    [allUsage, selectedCustomerId]
  );

  const customerTickets = useMemo(
    () => allTickets.filter((t) => t.customer_id === selectedCustomerId),
    [allTickets, selectedCustomerId]
  );

  const latestUsage = customerUsage[0];
  const baseActiveUsers = latestUsage?.active_users || 100;
  const purchasedSeats = latestUsage?.seats_purchased || 200;

  // 60fps Scenario Sliders State
  const [activeUsersSlider, setActiveUsersSlider] = useState<number>(baseActiveUsers);
  const [resolveCriticalTickets, setResolveCriticalTickets] = useState<boolean>(false);
  const [extensionDays, setExtensionDays] = useState<number>(0);

  useEffect(() => {
    setActiveUsersSlider(baseActiveUsers);
    setResolveCriticalTickets(false);
    setExtensionDays(0);
  }, [selectedCustomerId, baseActiveUsers]);

  // Client-side instantaneous 60fps risk calculation
  const simulatedAssessment = useMemo(() => {
    if (!currentAssessment) return null;
    return evaluateCustomerRisk(
      currentAssessment.customer,
      currentAssessment.contract,
      customerUsage,
      customerTickets,
      policy,
      {
        latestActiveUsers: activeUsersSlider,
        resolveCritical: resolveCriticalTickets,
        renewalExtensionDays: extensionDays,
      }
    );
  }, [
    currentAssessment,
    customerUsage,
    customerTickets,
    policy,
    activeUsersSlider,
    resolveCriticalTickets,
    extensionDays,
  ]);

  const baseScore = currentAssessment?.risk_score || 0;
  const simScore = simulatedAssessment?.risk_score || 0;
  const scoreDelta = simScore - baseScore;
  const isReduced = scoreDelta < 0;

  const handleCommitIntervention = () => {
    confetti({
      particleCount: 75,
      spread: 80,
      origin: { y: 0.6 },
      colors: ['#c2410c', '#10b981', '#38bdf8'],
    });
    toast.success(
      `Turnaround playbook deployed for ${currentAssessment.customer.customer_name}! Risk reduced by ${Math.abs(
        scoreDelta
      )} points.`
    );
  };

  const handleReset = () => {
    setActiveUsersSlider(baseActiveUsers);
    setResolveCriticalTickets(false);
    setExtensionDays(0);
  };

  if (!currentAssessment || !simulatedAssessment) return null;

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16 pt-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 border border-orange-200 text-orange-700 text-xs font-semibold tracking-wide uppercase mb-2">
            <Sliders className="w-3.5 h-3.5 text-orange-600" />
            <span>60FPS Turnaround Engine</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-display font-extrabold text-[#2d251e] tracking-tight">
            Intervention Simulation Lab
          </h2>
          <p className="text-xs text-[#786c5c] mt-1">
            Tactile, zero-lag browser simulation. Drag sliders to model customer success playbooks and protect ARR.
          </p>
        </div>

        {/* Customer Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-[#5e5346]">Simulate Account:</span>
          <select
            value={selectedCustomerId}
            onChange={(e) => setSelectedCustomerId(e.target.value)}
            className="px-4 py-2 rounded-2xl bg-[#f8f3e8] border border-[#d6c8ad] text-xs font-bold text-[#2d251e] shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500 cursor-pointer"
          >
            {assessments.map((a) => (
              <option key={a.customer.customer_id} value={a.customer.customer_id}>
                {a.customer.customer_name} ({a.risk_score} pts • {a.risk_level} Risk)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Grid: Hardware Sliders (Col 1) + Live Impact Projection (Col 2) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sliders Card */}
        <div className="lg:col-span-2 apple-cockpit-card p-6 md:p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-[#dfd3bc] pb-4">
            <div>
              <h3 className="text-lg font-display font-bold text-[#2d251e]">
                Operational Turnaround Levers
              </h3>
              <p className="text-xs text-[#786c5c]">
                Simulating interventions for {currentAssessment.customer.customer_name}
              </p>
            </div>

            <button
              onClick={handleReset}
              className="p-2 rounded-xl text-[#8f8270] hover:text-[#3b3229] hover:bg-[#e4dac4] flex items-center gap-1.5 text-xs font-semibold transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          </div>

          {/* Lever 1: Adoption & Seat Utilization */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#3b3229]">
                1. Adoption Recovery (Active User Seats):
              </span>
              <span className="font-bold text-orange-600 mono-num">
                {activeUsersSlider} / {purchasedSeats} active seats (
                {((activeUsersSlider / purchasedSeats) * 100).toFixed(0)}% utilization)
              </span>
            </div>
            <input
              type="range"
              min={Math.max(10, Math.floor(baseActiveUsers * 0.5))}
              max={purchasedSeats}
              value={activeUsersSlider}
              onChange={(e) => setActiveUsersSlider(Number(e.target.value))}
              className="w-full accent-orange-600 cursor-pointer h-2 bg-[#ded2ba] rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-[#8f8270] mono-num">
              <span>Baseline: {baseActiveUsers} active</span>
              <span>100% Target: {purchasedSeats} seats</span>
            </div>
          </div>

          {/* Lever 2: Critical Support Escalation */}
          <div className="space-y-2 pt-3 border-t border-[#dfd3bc]">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-bold text-xs text-[#3b3229]">
                  2. Priority Support Escalation Resolution:
                </span>
                <p className="text-[11px] text-[#786c5c]">
                  Deploy senior engineering taskforce to resolve open P1 escalations
                </p>
              </div>

              {/* iOS Toggle Switch */}
              <button
                type="button"
                onClick={() => setResolveCriticalTickets(!resolveCriticalTickets)}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  resolveCriticalTickets ? 'bg-orange-600' : 'bg-[#ded2ba]'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-[#f8f3e8] shadow ring-0 transition duration-200 ease-in-out ${
                    resolveCriticalTickets ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </div>

          {/* Lever 3: Contract Extension Runway */}
          <div className="space-y-2.5 pt-3 border-t border-[#dfd3bc]">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#3b3229]">
                3. Commercial Buffer Extension Runway:
              </span>
              <span className="font-bold text-emerald-600 mono-num">
                +{extensionDays} days extension
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="90"
              step="15"
              value={extensionDays}
              onChange={(e) => setExtensionDays(Number(e.target.value))}
              className="w-full accent-emerald-600 cursor-pointer h-2 bg-[#ded2ba] rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-[#8f8270] mono-num">
              <span>0 days (Original contract date)</span>
              <span>+90 days (Full quarter runway)</span>
            </div>
          </div>

          {/* Action to Deploy Strategy */}
          <div className="pt-6 border-t border-[#dfd3bc] flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-xs text-[#786c5c]">
              Contract ARR Protected:{' '}
              <strong className="text-[#2d251e] mono-num">
                ${((currentAssessment.contract?.annual_contract_value || 0) / 1000).toFixed(0)}k ARR
              </strong>
            </div>

            <button
              onClick={handleCommitIntervention}
              className="w-full sm:w-auto px-6 py-3 rounded-2xl bg-orange-600 text-white font-semibold text-xs flex items-center justify-center gap-2 hover:bg-orange-700 apple-spring-press shadow-[0_4px_14px_rgba(37,99,235,0.3)] transition-all"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Deploy Turnaround Strategy & Protect ARR</span>
            </button>
          </div>
        </div>

        {/* Live Score Ticker Card */}
        <div className="apple-cockpit-card p-6 md:p-8 flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-[#2d251e] border-b border-[#dfd3bc] pb-3">
              Live Score Impact Ticker
            </h3>

            {/* Before vs After Scoreboard */}
            <div className="flex items-center justify-around p-4 rounded-2xl bg-[#ece3cf] border border-[#d6c8ad]/80">
              <div className="text-center space-y-1">
                <span className="text-[10px] font-bold text-[#8f8270] uppercase tracking-wider">
                  Baseline
                </span>
                <div className="text-3xl font-display font-bold text-[#4d4236] mono-num">
                  {baseScore} pts
                </div>
                <span className="text-[10px] font-bold text-rose-600">
                  {currentAssessment.risk_level} Risk
                </span>
              </div>

              <div className="flex flex-col items-center justify-center">
                <ArrowRight className="w-5 h-5 text-orange-600" />
                {scoreDelta !== 0 && (
                  <span
                    className={`text-xs font-bold mono-num mt-1 ${
                      isReduced ? 'text-emerald-600' : 'text-rose-600'
                    }`}
                  >
                    {scoreDelta > 0 ? `+${scoreDelta}` : scoreDelta} pts
                  </span>
                )}
              </div>

              <div className="text-center space-y-1">
                <span className="text-[10px] font-bold text-orange-600 uppercase tracking-wider">
                  Simulated
                </span>
                <div className="text-3xl font-display font-bold text-orange-600 mono-num">
                  {simScore} pts
                </div>
                <span
                  className={`text-[10px] font-bold ${
                    simulatedAssessment.risk_level === 'High'
                      ? 'text-rose-600'
                      : simulatedAssessment.risk_level === 'Medium'
                      ? 'text-amber-600'
                      : 'text-emerald-600'
                  }`}
                >
                  {simulatedAssessment.risk_level} Risk
                </span>
              </div>
            </div>

            {/* Factor Waterfall */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-[#786c5c] uppercase tracking-wide">
                Simulated Factor Breakdown:
              </span>
              <div className="space-y-1.5 max-h-56 overflow-y-auto">
                {simulatedAssessment.factors.map((f, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-xl bg-[#f8f3e8] border border-[#d6c8ad] flex items-center justify-between text-xs"
                  >
                    <span className="text-[#4d4236] font-medium truncate max-w-[180px]">
                      {f.name}
                    </span>
                    <span className="font-bold text-[#2d251e] mono-num">+{f.points} pts</span>
                  </div>
                ))}

                {simulatedAssessment.factors.length === 0 && (
                  <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-center space-y-1">
                    <CheckCircle2 className="w-6 h-6 text-emerald-600 mx-auto" />
                    <div className="text-xs font-bold text-emerald-700">
                      Zero Risk Factors Active
                    </div>
                    <p className="text-[11px] text-emerald-600">
                      Turnaround plan eliminates all risk triggers.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-orange-50/80 border border-orange-200 text-[11px] text-orange-950 font-medium leading-relaxed">
            ⚡ 60fps continuous evaluation in client memory. All scores backed by immutable audit records.
          </div>
        </div>
      </div>
    </div>
  );
};
