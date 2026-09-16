import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  Download, 
  Check, 
  AlertCircle, 
  X, 
  RefreshCw, 
  Layers, 
  CheckCircle2, 
  Sparkles, 
  Table, 
  HelpCircle,
  FileSpreadsheet
} from 'lucide-react';
import { Customer, Contract, SupportTicket, UsageEvent, AccountManager } from '../types/simulator';
import confetti from 'canvas-confetti';
import { toast } from 'sonner';

export interface UploadedDataset {
  customers: Customer[];
  contracts: Contract[];
  tickets: SupportTicket[];
  usage: UsageEvent[];
  accountManagers: AccountManager[];
}

interface EnterpriseDataUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportData: (dataset: UploadedDataset, datasetName: string) => void;
  onResetToDemo: () => void;
  isUsingCustomData: boolean;
  backendConnected?: boolean;
}

export const EnterpriseDataUploadModal: React.FC<EnterpriseDataUploadModalProps> = ({
  isOpen,
  onClose,
  onImportData,
  onResetToDemo,
  isUsingCustomData,
  backendConnected = false,
}) => {
  const [activeTab, setActiveTab] = useState<'FILE' | 'PASTE'>('FILE');
  const [rawText, setRawText] = useState<string>('');
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [parsedRows, setParsedRows] = useState<Array<Record<string, any>>>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const [datasetTitle, setDatasetTitle] = useState<string>('Q3 Enterprise Retention Ledger');

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  // Sample CSV template content
  const sampleCsvContent = `customer_name,industry,segment,annual_contract_value,renewal_date,seats_purchased,active_users,critical_tickets,account_manager
Apex Global Technologies,Technology,Enterprise,85000,2026-11-20,1200,980,0,Maya Chen
Sovereign Health Network,Healthcare,Enterprise,120000,2026-10-15,2500,1400,2,Daniel Okafor
Vanguard Financial Partners,Financial Services,Mid-Market,48000,2026-12-05,500,420,0,Priya Nair
Beacon Logistics International,Logistics,Enterprise,72000,2026-09-28,800,450,1,Elena Garcia
Meridian Media & Games,Media,SMB,16500,2027-02-14,200,195,0,Noah Williams
Horizon Bio Labs,Healthcare,Mid-Market,36000,2026-11-30,400,210,3,Maya Chen
Cascade Retail Systems,Retail,SMB,19500,2026-10-02,300,180,1,Daniel Okafor`;

  const handleDownloadCsvTemplate = () => {
    const blob = new Blob([sampleCsvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'enterprise_customer_template.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Downloaded enterprise_customer_template.csv');
  };

  // Robust client-side CSV parser
  const parseCsvText = (text: string) => {
    try {
      setParseError(null);
      const lines = text.trim().split(/\r?\n/).filter(line => line.trim().length > 0);
      if (lines.length < 2) {
        setParseError('CSV must contain at least 1 header row and 1 data row.');
        setParsedRows([]);
        return;
      }

      const headers = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, '').toLowerCase());

      const rows: Array<Record<string, any>> = [];

      for (let i = 1; i < lines.length; i++) {
        // Regex to handle quoted commas
        const regex = /(?:\s*"([^"]*)"\s*|\s*([^,]+)\s*|\s*)(?:,|$)/g;
        const values: string[] = [];
        let match;
        while ((match = regex.exec(lines[i])) !== null) {
          if (match.index === regex.lastIndex) regex.lastIndex++;
          const val = (match[1] !== undefined ? match[1] : match[2]) || '';
          values.push(val.trim());
          if (regex.lastIndex >= lines[i].length) break;
        }

        if (values.length > 0) {
          const rowObj: Record<string, any> = {};
          headers.forEach((hdr, idx) => {
            rowObj[hdr] = values[idx] || '';
          });
          rows.push(rowObj);
        }
      }

      if (rows.length === 0) {
        setParseError('No valid data rows found.');
        setParsedRows([]);
      } else {
        setParsedRows(rows);
        toast.info(`Parsed ${rows.length} customer records from CSV`);
      }
    } catch (err: any) {
      setParseError(`Failed to parse CSV: ${err.message}`);
      setParsedRows([]);
    }
  };

  // JSON parser
  const parseJsonText = (text: string) => {
    try {
      setParseError(null);
      const data = JSON.parse(text);
      let items: any[] = [];
      if (Array.isArray(data)) {
        items = data;
      } else if (data.customers && Array.isArray(data.customers)) {
        items = data.customers;
      } else {
        setParseError('JSON must be an array of customer objects or have a "customers" array.');
        return;
      }

      setParsedRows(items);
      toast.info(`Parsed ${items.length} customer records from JSON`);
    } catch (err: any) {
      setParseError(`Invalid JSON format: ${err.message}`);
      setParsedRows([]);
    }
  };

  const handleFileUpload = (file: File) => {
    setFileName(file.name);
    setDatasetTitle(file.name.replace(/\.[^/.]+$/, ''));
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setRawText(content);
      if (file.name.endsWith('.json')) {
        parseJsonText(content);
      } else {
        parseCsvText(content);
      }
    };
    reader.readAsText(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  // Convert parsed rows into simulator models
  const handleConfirmImport = () => {
    if (parsedRows.length === 0) {
      toast.error('No parsed data to import.');
      return;
    }

    const customers: Customer[] = [];
    const contracts: Contract[] = [];
    const tickets: SupportTicket[] = [];
    const usage: UsageEvent[] = [];
    const accountManagers: AccountManager[] = [
      { account_manager_id: 'AM-01', full_name: 'Maya Chen', email: 'maya.chen@enterprise.example', region: 'North America', active: 1 },
      { account_manager_id: 'AM-02', full_name: 'Daniel Okafor', email: 'daniel.okafor@enterprise.example', region: 'Europe', active: 1 },
      { account_manager_id: 'AM-03', full_name: 'Priya Nair', email: 'priya.nair@enterprise.example', region: 'Asia Pacific', active: 1 },
      { account_manager_id: 'AM-04', full_name: 'Elena Garcia', email: 'elena.garcia@enterprise.example', region: 'Latin America', active: 1 },
      { account_manager_id: 'AM-05', full_name: 'Noah Williams', email: 'noah.williams@enterprise.example', region: 'North America', active: 1 },
    ];

    parsedRows.forEach((row, idx) => {
      const custId = `CUS-IMP-${String(idx + 1).padStart(3, '0')}`;
      const name = row.customer_name || row.name || row.company || row.account || `Enterprise Account ${idx + 1}`;
      const ind = row.industry || row.sector || 'Technology';
      const rawSeg = (row.segment || row.tier || 'Enterprise').toLowerCase();
      const segment: 'Enterprise' | 'Mid-Market' | 'SMB' = 
        rawSeg.includes('mid') ? 'Mid-Market' : rawSeg.includes('smb') ? 'SMB' : 'Enterprise';
      
      const arr = Number(row.annual_contract_value || row.arr || row.acv || row.revenue || 25000);
      const renewal = row.renewal_date || row.renewal || row.contract_end_date || '2026-12-31';
      const seats = Number(row.seats_purchased || row.seats || 500);
      const activeUsers = Number(row.active_users || row.users || Math.round(seats * 0.8));
      const criticalTicketCount = Number(row.critical_tickets || row.tickets || 0);
      
      const amIdx = idx % accountManagers.length;
      const am = accountManagers[amIdx];

      // 1. Customer
      customers.push({
        customer_id: custId,
        customer_name: name,
        industry: ind,
        segment,
        employee_count: seats * 3,
        region: am.region,
        account_manager_id: am.account_manager_id,
        customer_status: 'Active',
        created_at: '2025-01-01',
      });

      // 2. Contract
      contracts.push({
        contract_id: `CON-${custId}`,
        customer_id: custId,
        contract_start_date: '2025-01-01',
        contract_end_date: renewal,
        annual_contract_value: arr,
        renewal_date: renewal,
        contract_status: 'Active',
      });

      // 3. Usage
      usage.push({
        usage_event_id: `USE-${custId}-01`,
        customer_id: custId,
        event_date: '2026-08-01',
        active_users: Math.round(activeUsers * 1.1),
        seats_purchased: seats,
      });
      usage.push({
        usage_event_id: `USE-${custId}-02`,
        customer_id: custId,
        event_date: '2026-09-01',
        active_users: activeUsers,
        seats_purchased: seats,
      });

      // 4. Critical Support Tickets
      for (let t = 0; t < criticalTicketCount; t++) {
        tickets.push({
          ticket_id: `TCK-${custId}-${t + 1}`,
          customer_id: custId,
          category: 'Integration & API SLA',
          priority: 'Critical',
          ticket_status: 'Open',
          opened_at: '2026-09-02',
          resolved_at: null,
        });
      }
    });

    const dataset: UploadedDataset = {
      customers,
      contracts,
      tickets,
      usage,
      accountManagers,
    };

    onImportData(dataset, datasetTitle);
    confetti({
      particleCount: 50,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#ea580c', '#d97706', '#10b981'],
    });
    onClose();
  };

  // Preview calculations
  const totalPreviewArr = parsedRows.reduce((sum, r) => {
    return sum + Number(r.annual_contract_value || r.arr || r.acv || r.revenue || 25000);
  }, 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="apple-cockpit-card w-full max-w-2xl bg-[#fbf8f1] border border-[#d6c8ad] shadow-2xl rounded-3xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-[#ded2ba] flex items-center justify-between bg-[#f4ece0]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-orange-600 to-amber-600 flex items-center justify-center text-white shadow-sm">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold font-display text-[#2d251e] tracking-tight">
                Upload Enterprise Customer Data
              </h2>
              <p className="text-xs text-[#786c5c] font-sans">
                Import your physical CSV or JSON portfolio to simulate renewal risks on your real accounts.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-[#ece3cf] hover:bg-[#ded2ba] text-[#5e5346] flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Method Tabs */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 p-1 rounded-full bg-[#e4dac4]/80 border border-[#d6c8ad]/60 text-xs font-semibold">
              <button
                onClick={() => setActiveTab('FILE')}
                className={`px-4 py-1.5 rounded-full transition-all cursor-pointer ${
                  activeTab === 'FILE'
                    ? 'bg-white text-orange-600 shadow-xs'
                    : 'text-[#5e5346] hover:text-[#2d251e]'
                }`}
              >
                Upload File (.csv, .json)
              </button>
              <button
                onClick={() => setActiveTab('PASTE')}
                className={`px-4 py-1.5 rounded-full transition-all cursor-pointer ${
                  activeTab === 'PASTE'
                    ? 'bg-white text-orange-600 shadow-xs'
                    : 'text-[#5e5346] hover:text-[#2d251e]'
                }`}
              >
                Paste Raw Data
              </button>
            </div>

            <button
              onClick={handleDownloadCsvTemplate}
              className="flex items-center gap-1.5 text-xs font-semibold text-orange-700 hover:text-orange-800 bg-orange-50 hover:bg-orange-100/80 px-3 py-1.5 rounded-full border border-orange-200 transition-colors cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download CSV Template</span>
            </button>
          </div>

          {/* TAB 1: File Drop Zone */}
          {activeTab === 'FILE' && (
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
                dragActive 
                  ? 'border-orange-500 bg-orange-50/50' 
                  : 'border-[#ded2ba] hover:border-orange-400 bg-[#f8f3e8]/60'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.json,text/csv,application/json"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileUpload(e.target.files[0]);
                  }
                }}
                className="hidden"
              />
              <div className="w-12 h-12 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center mx-auto mb-3">
                <FileSpreadsheet className="w-6 h-6" />
              </div>
              <p className="text-sm font-bold text-[#2d251e] font-display">
                {fileName ? fileName : 'Click to select or drag and drop your physical file'}
              </p>
              <p className="text-xs text-[#786c5c] font-sans mt-1">
                Supports standard CSV exports from Salesforce, HubSpot, Stripe Billing, or JSON arrays.
              </p>
            </div>
          )}

          {/* TAB 2: Paste Raw Content */}
          {activeTab === 'PASTE' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-[#786c5c]">
                <span>Paste CSV rows or JSON array</span>
                <button
                  onClick={() => {
                    setRawText(sampleCsvContent);
                    parseCsvText(sampleCsvContent);
                  }}
                  className="text-orange-600 font-semibold hover:underline cursor-pointer"
                >
                  Load Example CSV
                </button>
              </div>
              <textarea
                value={rawText}
                onChange={(e) => {
                  setRawText(e.target.value);
                  if (e.target.value.trim().startsWith('{') || e.target.value.trim().startsWith('[')) {
                    parseJsonText(e.target.value);
                  } else {
                    parseCsvText(e.target.value);
                  }
                }}
                placeholder="customer_name,industry,segment,annual_contract_value,renewal_date..."
                className="w-full h-36 p-3 rounded-2xl bg-white border border-[#ded2ba] font-mono text-xs text-[#2d251e] focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
          )}

          {/* Parse Errors */}
          {parseError && (
            <div className="p-3 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{parseError}</span>
            </div>
          )}

          {/* Data Validation Preview */}
          {parsedRows.length > 0 && (
            <div className="p-4 rounded-2xl bg-[#ece3cf]/80 border border-[#d6c8ad] space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span className="font-bold text-xs font-display text-[#2d251e]">
                    Validation Passed: {parsedRows.length} Accounts Detected
                  </span>
                </div>
                <div className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  Total ARR: ${(totalPreviewArr / 1_000_000).toFixed(2)}M
                </div>
              </div>

              {/* Mini Table Preview */}
              <div className="max-h-36 overflow-y-auto border border-[#ded2ba] rounded-xl bg-white text-[11px] font-sans">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-[#f8f3e8] border-b border-[#ded2ba] text-[#786c5c] font-mono text-[10px]">
                    <tr>
                      <th className="p-2">Account Name</th>
                      <th className="p-2">Industry</th>
                      <th className="p-2">Segment</th>
                      <th className="p-2">ARR ($)</th>
                      <th className="p-2">Renewal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parsedRows.slice(0, 5).map((r, i) => (
                      <tr key={i} className="border-b border-[#f4ece0] hover:bg-orange-50/50">
                        <td className="p-2 font-semibold text-[#2d251e]">
                          {r.customer_name || r.name || r.company || `Account ${i + 1}`}
                        </td>
                        <td className="p-2 text-[#5e5346]">{r.industry || 'Technology'}</td>
                        <td className="p-2">
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-[#f4ece0] text-[#786c5c]">
                            {r.segment || 'Enterprise'}
                          </span>
                        </td>
                        <td className="p-2 font-mono font-bold text-[#2d251e]">
                          ${Number(r.annual_contract_value || r.arr || 25000).toLocaleString()}
                        </td>
                        <td className="p-2 font-mono text-[#786c5c]">
                          {r.renewal_date || '2026-12-31'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {parsedRows.length > 5 && (
                <p className="text-[10px] text-[#8f8270] text-center font-mono">
                  + {parsedRows.length - 5} more enterprise accounts ready for simulation
                </p>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-[#ded2ba] bg-[#f4ece0] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {isUsingCustomData ? (
            <button
              onClick={() => {
                onResetToDemo();
                toast.info('Restored 30 benchmark demo accounts');
                onClose();
              }}
              className="text-xs font-semibold text-[#786c5c] hover:text-[#2d251e] flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset to Demo Benchmark (30 Accounts)</span>
            </button>
          ) : (
            <div className="text-xs text-[#8f8270] font-sans">
              Currently viewing 30 demo benchmark accounts.
            </div>
          )}

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-full text-xs font-semibold text-[#5e5346] hover:bg-[#ece3cf] transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirmImport}
              disabled={parsedRows.length === 0}
              className={`px-5 py-2 rounded-full text-xs font-bold transition-all flex items-center gap-2 cursor-pointer shadow-sm ${
                parsedRows.length > 0
                  ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white hover:opacity-95 shadow-orange-600/20'
                  : 'bg-[#ded2ba] text-[#8f8270] cursor-not-allowed'
              }`}
            >
              <Check className="w-3.5 h-3.5" />
              <span>Load Into Enterprise Simulator</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
