import React, { useState } from 'react';
import { CustomerAssessment } from '../types/simulator';
import { Search, Filter, ArrowRight, ShieldAlert, CheckCircle2 } from 'lucide-react';

interface PortfolioMatrixProps {
  assessments: CustomerAssessment[];
  onSelectCustomer: (assessment: CustomerAssessment) => void;
  onStartScenario: (assessment: CustomerAssessment) => void;
}

export const PortfolioMatrix: React.FC<PortfolioMatrixProps> = ({
  assessments,
  onSelectCustomer,
  onStartScenario,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [segmentFilter, setSegmentFilter] = useState<'ALL' | 'Enterprise' | 'Mid-Market' | 'SMB'>('ALL');
  const [riskFilter, setRiskFilter] = useState<'ALL' | 'High' | 'Medium' | 'Low'>('ALL');

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
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Search & Segment Filter Bar */}
      <div className="cockpit-card p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search Bar */}
        <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#e4dac4] border border-[#d6c8ad]/80 w-full md:w-80">
          <Search className="w-4 h-4 text-[#8f8270] shrink-0" />
          <input
            type="text"
            placeholder="Search account name, ID, or industry..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent text-xs text-[#2d251e] placeholder-slate-400 w-full focus:outline-none"
          />
        </div>

        {/* Segment & Risk Pill Selectors */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Segment Selector */}
          <div className="flex items-center bg-[#e4dac4] p-1 rounded-xl border border-[#d6c8ad] text-xs">
            {(['ALL', 'Enterprise', 'Mid-Market', 'SMB'] as const).map((seg) => (
              <button
                key={seg}
                onClick={() => setSegmentFilter(seg)}
                className={`px-3 py-1 rounded-lg font-medium transition-all ${
                  segmentFilter === seg
                    ? 'bg-[#f8f3e8] text-[#2d251e] shadow-sm font-semibold'
                    : 'text-[#5e5346] hover:text-[#2d251e]'
                }`}
              >
                {seg}
              </button>
            ))}
          </div>

          {/* Risk Level Filter */}
          <div className="flex items-center bg-[#e4dac4] p-1 rounded-xl border border-[#d6c8ad] text-xs">
            {(['ALL', 'High', 'Medium', 'Low'] as const).map((rl) => (
              <button
                key={rl}
                onClick={() => setRiskFilter(rl)}
                className={`px-3 py-1 rounded-lg font-medium transition-all ${
                  riskFilter === rl
                    ? 'bg-[#f8f3e8] text-[#2d251e] shadow-sm font-semibold'
                    : 'text-[#5e5346] hover:text-[#2d251e]'
                }`}
              >
                {rl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Account Table */}
      <div className="cockpit-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#ece3cf] text-[#5e5346] font-semibold border-b border-[#d6c8ad]">
              <tr>
                <th className="p-4">ACCOUNT</th>
                <th className="p-4">SEGMENT</th>
                <th className="p-4">ARR</th>
                <th className="p-4">RENEWAL</th>
                <th className="p-4">RISK SCORE</th>
                <th className="p-4">TOP RISK FACTOR</th>
                <th className="p-4 text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((a) => {
                const isHigh = a.risk_level === 'High';
                const isMed = a.risk_level === 'Medium';
                const topFactor = a.factors[0];

                return (
                  <tr
                    key={a.customer.customer_id}
                    className="hover:bg-[#ece3cf]/80 transition-colors group cursor-pointer"
                    onClick={() => onSelectCustomer(a)}
                  >
                    <td className="p-4">
                      <div className="font-bold text-[#2d251e] group-hover:text-orange-600 transition-colors">
                        {a.customer.customer_name}
                      </div>
                      <div className="text-[11px] text-[#8f8270] font-mono">
                        {a.customer.customer_id} • {a.customer.industry}
                      </div>
                    </td>

                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded-full bg-[#e4dac4] text-[#4d4236] font-medium text-[11px]">
                        {a.customer.segment}
                      </span>
                    </td>

                    <td className="p-4 font-bold text-[#2d251e] mono-num">
                      ${((a.contract?.annual_contract_value || 0) / 1000).toFixed(0)}k
                    </td>

                    <td className="p-4 text-[#5e5346] mono-num">
                      {a.contract?.renewal_date || 'N/A'}
                    </td>

                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2.5 py-0.5 rounded-full font-bold mono-num text-[11px] border ${
                            isHigh
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : isMed
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          }`}
                        >
                          {a.risk_score} pts ({a.risk_level})
                        </span>
                      </div>
                    </td>

                    <td className="p-4 text-[#5e5346]">
                      {topFactor ? (
                        <div className="max-w-xs truncate" title={topFactor.explanation}>
                          <span className="font-semibold text-[#3b3229]">{topFactor.name}</span>
                          <span className="text-[#8f8270] ml-1">({topFactor.points} pts)</span>
                        </div>
                      ) : (
                        <span className="text-emerald-600 font-medium">Nominal / Healthy</span>
                      )}
                    </td>

                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onStartScenario(a);
                          }}
                          className="px-2.5 py-1 rounded-lg bg-orange-50 text-orange-700 hover:bg-orange-100 font-semibold text-[11px] transition-colors"
                        >
                          Simulate
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectCustomer(a);
                          }}
                          className="p-1 rounded text-[#8f8270] hover:text-[#4d4236] transition-colors"
                        >
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
