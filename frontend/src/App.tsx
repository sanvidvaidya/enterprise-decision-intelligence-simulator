import React, { useState, useMemo, useEffect } from 'react';
import {
  Customer,
  Contract,
  SupportTicket,
  UsageEvent,
  AccountManager,
  CustomerAssessment,
  PolicyParameters,
  SimulatorTab,
} from './types/simulator';
import {
  DEFAULT_POLICY,
  RAW_CUSTOMERS,
  RAW_CONTRACTS,
  RAW_ACCOUNT_MANAGERS,
  RAW_TICKETS,
  RAW_USAGE,
} from './data/simulatorData';
import { evaluateCustomerRisk } from './lib/riskEngine';
import { AppleCockpitHeader } from './components/AppleCockpitHeader';
import { SimulatorLandingPage } from './components/SimulatorLandingPage';
import { AppleCockpitView } from './components/AppleCockpitView';
import { ApplePortfolioView } from './components/ApplePortfolioView';
import { AppleScenarioLab } from './components/AppleScenarioLab';
import { ApplePolicyView } from './components/ApplePolicyView';
import { AppleCustomerSheet } from './components/AppleCustomerSheet';
import { EnterpriseDataUploadModal, UploadedDataset } from './components/EnterpriseDataUploadModal';
import { checkBackendHealth, uploadAccountsToBackend, BackendHealth } from './services/api';
import { Toaster, toast } from 'sonner';

export const App: React.FC = () => {
  // Navigation
  const [currentTab, setCurrentTab] = useState<SimulatorTab>('LANDING');
  const [policy, setPolicy] = useState<PolicyParameters>(DEFAULT_POLICY);

  // Dynamic Physical Dataset State (supports local storage persistence)
  const [customers, setCustomers] = useState<Customer[]>(() => {
    try {
      const saved = localStorage.getItem('enterprise_custom_dataset');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.customers && parsed.customers.length > 0) return parsed.customers;
      }
    } catch (_) {}
    return RAW_CUSTOMERS;
  });

  const [contracts, setContracts] = useState<Contract[]>(() => {
    try {
      const saved = localStorage.getItem('enterprise_custom_dataset');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.contracts) return parsed.contracts;
      }
    } catch (_) {}
    return RAW_CONTRACTS;
  });

  const [tickets, setTickets] = useState<SupportTicket[]>(() => {
    try {
      const saved = localStorage.getItem('enterprise_custom_dataset');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.tickets) return parsed.tickets;
      }
    } catch (_) {}
    return RAW_TICKETS;
  });

  const [usage, setUsage] = useState<UsageEvent[]>(() => {
    try {
      const saved = localStorage.getItem('enterprise_custom_dataset');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.usage) return parsed.usage;
      }
    } catch (_) {}
    return RAW_USAGE;
  });

  const [accountManagers, setAccountManagers] = useState<AccountManager[]>(() => {
    try {
      const saved = localStorage.getItem('enterprise_custom_dataset');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.accountManagers) return parsed.accountManagers;
      }
    } catch (_) {}
    return RAW_ACCOUNT_MANAGERS;
  });

  const [isUsingCustomData, setIsUsingCustomData] = useState<boolean>(() => {
    return localStorage.getItem('enterprise_custom_dataset') !== null;
  });

  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(null);
  const backendConnected = backendHealth !== null;

  // Live Backend Ping & Auto-Connect
  useEffect(() => {
    let mounted = true;
    checkBackendHealth().then((health) => {
      if (!mounted) return;
      if (health && health.status === 'ok') {
        setBackendHealth(health);
        console.log('[Decision Simulator] Connected to Python SQLite backend on port 8002');
      }
    });
    return () => { mounted = false; };
  }, []);

  // Modal states
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [selectedCustomerForDrawer, setSelectedCustomerForDrawer] = useState<CustomerAssessment | null>(null);
  const [selectedCustomerForScenario, setSelectedCustomerForScenario] = useState<CustomerAssessment | null>(null);

  // Account Manager lookup map
  const amMap = useMemo(() => {
    return new Map(accountManagers.map((am) => [am.account_manager_id, am]));
  }, [accountManagers]);

  // Contracts lookup map
  const contractMap = useMemo(() => {
    return new Map(contracts.map((c) => [c.customer_id, c]));
  }, [contracts]);

  // Compute live assessments dynamically (<1ms)
  const assessments: CustomerAssessment[] = useMemo(() => {
    return customers.map((cust) => {
      const am = amMap.get(cust.account_manager_id);
      const contract = contractMap.get(cust.customer_id) || null;
      const custUsage = usage.filter((u) => u.customer_id === cust.customer_id);
      const custTickets = tickets.filter((t) => t.customer_id === cust.customer_id);

      const customerWithAm = {
        ...cust,
        account_manager_name: am?.full_name,
        account_manager_email: am?.email,
      };

      return evaluateCustomerRisk(customerWithAm, contract, custUsage, custTickets, policy);
    });
  }, [customers, contracts, usage, tickets, policy, amMap, contractMap]);

  // Aggregate Portfolio Stats
  const totalArr = useMemo(() => {
    return assessments.reduce(
      (sum, a) => sum + (a.contract?.annual_contract_value || 0),
      0
    );
  }, [assessments]);

  const avgRiskScore = useMemo(() => {
    if (assessments.length === 0) return 0;
    const total = assessments.reduce((sum, a) => sum + a.risk_score, 0);
    return Math.round(total / assessments.length);
  }, [assessments]);

  const highRiskCount = useMemo(() => {
    return assessments.filter((a) => a.risk_level === 'High').length;
  }, [assessments]);

  const handleStartScenarioWithCustomer = (assessment: CustomerAssessment) => {
    setSelectedCustomerForScenario(assessment);
    setCurrentTab('SCENARIO_LAB');
  };

  const handleImportData = (dataset: UploadedDataset, datasetName: string) => {
    setCustomers(dataset.customers);
    setContracts(dataset.contracts);
    setTickets(dataset.tickets);
    setUsage(dataset.usage);
    setAccountManagers(dataset.accountManagers);
    setIsUsingCustomData(true);
    try {
      localStorage.setItem('enterprise_custom_dataset', JSON.stringify(dataset));
    } catch (_) {}
    if (backendConnected) {
      uploadAccountsToBackend(dataset.customers).then((res) => {
        if (res && res.status === 'success') {
          toast.success(`Synchronized ${res.imported_count} accounts with Python SQLite Risk Store!`);
        }
      });
    }
    toast.success(`Loaded "${datasetName}" (${dataset.customers.length} accounts) into Enterprise Simulator!`);
  };

  const handleResetToDemo = () => {
    setCustomers(RAW_CUSTOMERS);
    setContracts(RAW_CONTRACTS);
    setTickets(RAW_TICKETS);
    setUsage(RAW_USAGE);
    setAccountManagers(RAW_ACCOUNT_MANAGERS);
    setIsUsingCustomData(false);
    try {
      localStorage.removeItem('enterprise_custom_dataset');
    } catch (_) {}
    toast.info('Restored 30 benchmark demo accounts.');
  };

  return (
    <div className="min-h-screen bg-[#fbfbfd] text-[#2d251e] flex flex-col font-sans selection:bg-orange-600/20 selection:text-orange-950 antialiased">
      <Toaster position="bottom-right" theme="light" richColors />

      {/* Apple Floating Dynamic Island Navigation Header */}
      <AppleCockpitHeader
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        totalArr={totalArr}
        avgRiskScore={avgRiskScore}
        highRiskCount={highRiskCount}
        onOpenUpload={() => setIsUploadOpen(true)}
        isUsingCustomData={isUsingCustomData}
        backendConnected={backendConnected}
      />

      {/* Main Spatial Stage */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-12">
        {currentTab === 'LANDING' && (
          <SimulatorLandingPage
            assessments={assessments}
            onNavigateTab={setCurrentTab}
            onStartScenario={handleStartScenarioWithCustomer}
            totalArr={totalArr}
            avgRiskScore={avgRiskScore}
            highRiskCount={highRiskCount}
            onOpenUpload={() => setIsUploadOpen(true)}
            isUsingCustomData={isUsingCustomData}
          />
        )}

        {currentTab === 'COCKPIT' && (
          <AppleCockpitView
            assessments={assessments}
            onSelectCustomer={setSelectedCustomerForDrawer}
            onNavigateTab={setCurrentTab}
            onStartScenario={handleStartScenarioWithCustomer}
          />
        )}

        {currentTab === 'PORTFOLIO' && (
          <ApplePortfolioView
            assessments={assessments}
            onSelectCustomer={setSelectedCustomerForDrawer}
            onStartScenario={handleStartScenarioWithCustomer}
          />
        )}

        {currentTab === 'SCENARIO_LAB' && (
          <AppleScenarioLab
            assessments={assessments}
            policy={policy}
            allUsage={usage}
            allTickets={tickets}
            initialSelectedCustomer={selectedCustomerForScenario}
          />
        )}

        {currentTab === 'GOVERNANCE' && (
          <ApplePolicyView
            policy={policy}
            onUpdatePolicy={setPolicy}
            onResetPolicy={() => setPolicy(DEFAULT_POLICY)}
            assessments={assessments}
          />
        )}
      </main>

      {/* Apple Slide-over Customer 360 Sheet */}
      <AppleCustomerSheet
        assessment={selectedCustomerForDrawer}
        onClose={() => setSelectedCustomerForDrawer(null)}
        onOpenScenarioLab={handleStartScenarioWithCustomer}
      />

      {/* Physical Enterprise Data Upload Modal (.csv / .json) */}
      <EnterpriseDataUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onImportData={handleImportData}
        onResetToDemo={handleResetToDemo}
        isUsingCustomData={isUsingCustomData}
        backendConnected={backendConnected}
      />
    </div>
  );
};

export default App;
