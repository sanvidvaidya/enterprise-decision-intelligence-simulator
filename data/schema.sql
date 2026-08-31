PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS account_managers (
    account_manager_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    region TEXT NOT NULL,
    active INTEGER NOT NULL CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL UNIQUE,
    industry TEXT NOT NULL,
    segment TEXT NOT NULL CHECK (segment IN ('SMB', 'Mid-Market', 'Enterprise')),
    employee_count INTEGER NOT NULL CHECK (employee_count > 0),
    region TEXT NOT NULL,
    account_manager_id TEXT NOT NULL,
    customer_status TEXT NOT NULL CHECK (customer_status IN ('Active', 'At Risk', 'Churned')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (account_manager_id) REFERENCES account_managers(account_manager_id)
);

CREATE TABLE IF NOT EXISTS contracts (
    contract_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    contract_start_date TEXT NOT NULL,
    contract_end_date TEXT NOT NULL,
    renewal_date TEXT NOT NULL,
    annual_contract_value REAL NOT NULL CHECK (annual_contract_value > 0),
    currency TEXT NOT NULL DEFAULT 'USD',
    contract_status TEXT NOT NULL CHECK (contract_status IN ('Active', 'Pending Renewal', 'Expired')),
    auto_renew INTEGER NOT NULL CHECK (auto_renew IN (0, 1)),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS product_usage_events (
    usage_event_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    event_date TEXT NOT NULL,
    active_users INTEGER NOT NULL CHECK (active_users >= 0),
    seats_purchased INTEGER NOT NULL CHECK (seats_purchased > 0),
    sessions INTEGER NOT NULL CHECK (sessions >= 0),
    feature_adoption_pct REAL NOT NULL CHECK (feature_adoption_pct BETWEEN 0 AND 100),
    source_system TEXT NOT NULL DEFAULT 'product_analytics',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    UNIQUE (customer_id, event_date)
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    resolved_at TEXT,
    priority TEXT NOT NULL CHECK (priority IN ('Low', 'Normal', 'High', 'Critical')),
    ticket_status TEXT NOT NULL CHECK (ticket_status IN ('Open', 'In Progress', 'Resolved', 'Closed')),
    ticket_category TEXT NOT NULL,
    csat_score INTEGER CHECK (csat_score BETWEEN 1 AND 5),
    ticket_summary TEXT NOT NULL,
    source_system TEXT NOT NULL DEFAULT 'support_desk',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_customers_manager ON customers(account_manager_id);
CREATE INDEX IF NOT EXISTS idx_contracts_customer ON contracts(customer_id);
CREATE INDEX IF NOT EXISTS idx_usage_customer_date ON product_usage_events(customer_id, event_date);
CREATE INDEX IF NOT EXISTS idx_tickets_customer_status ON support_tickets(customer_id, ticket_status);
CREATE TABLE IF NOT EXISTS ingestion_runs (
    ingestion_run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    run_status TEXT NOT NULL CHECK (run_status IN ('RUNNING', 'COMPLETED', 'FAILED_VALIDATION', 'FAILED_LOAD')),
    source_directory TEXT NOT NULL,
    records_received INTEGER NOT NULL DEFAULT 0 CHECK (records_received >= 0),
    records_loaded INTEGER NOT NULL DEFAULT 0 CHECK (records_loaded >= 0),
    records_rejected INTEGER NOT NULL DEFAULT 0 CHECK (records_rejected >= 0)
);

CREATE TABLE IF NOT EXISTS data_quality_issues (
    data_quality_issue_id TEXT PRIMARY KEY,
    ingestion_run_id TEXT NOT NULL,
    source_file TEXT NOT NULL,
    row_number INTEGER,
    source_record_id TEXT,
    field_name TEXT,
    severity TEXT NOT NULL CHECK (severity IN ('ERROR', 'WARNING')),
    rule_name TEXT NOT NULL,
    issue_message TEXT NOT NULL,
    raw_value TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(ingestion_run_id)
);

CREATE INDEX IF NOT EXISTS idx_quality_issues_run ON data_quality_issues(ingestion_run_id);
CREATE TABLE IF NOT EXISTS source_file_manifest (
    ingestion_run_id TEXT NOT NULL,
    source_file TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    PRIMARY KEY (ingestion_run_id, source_file),
    FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(ingestion_run_id)
);
CREATE TABLE IF NOT EXISTS data_quality_warning_approvals (
    ingestion_run_id TEXT PRIMARY KEY,
    approved_by TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(ingestion_run_id)
);

-- Decision-layer tables preserve not only the current answer, but also the
-- history of assessments, hypothetical scenarios, and human follow-through.
CREATE TABLE IF NOT EXISTS risk_assessments (
    assessment_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    assessed_at TEXT NOT NULL,
    as_of_date TEXT NOT NULL,
    risk_score INTEGER NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    risk_level TEXT NOT NULL CHECK (risk_level IN ('Low', 'Medium', 'High')),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS risk_factor_results (
    factor_result_id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    points INTEGER NOT NULL CHECK (points >= 0),
    explanation TEXT NOT NULL,
    evidence_record_ids_json TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES risk_assessments(assessment_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scenario_runs (
    scenario_run_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    baseline_score INTEGER NOT NULL CHECK (baseline_score BETWEEN 0 AND 100),
    simulated_score INTEGER NOT NULL CHECK (simulated_score BETWEEN 0 AND 100),
    simulated_level TEXT NOT NULL CHECK (simulated_level IN ('Low', 'Medium', 'High')),
    assumptions_json TEXT NOT NULL,
    result_json TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS account_actions (
    action_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    action_text TEXT NOT NULL,
    owner TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    due_date TEXT NOT NULL,
    action_status TEXT NOT NULL CHECK (action_status IN ('Open', 'In Progress', 'Blocked', 'Completed')),
    created_at TEXT NOT NULL,
    completed_at TEXT,
    evidence_record_ids_json TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS decision_events (
    decision_event_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_at TEXT NOT NULL,
    actor TEXT NOT NULL,
    notes TEXT NOT NULL,
    related_action_id TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (related_action_id) REFERENCES account_actions(action_id)
);

CREATE INDEX IF NOT EXISTS idx_assessments_customer_date ON risk_assessments(customer_id, as_of_date);
CREATE INDEX IF NOT EXISTS idx_factor_results_assessment ON risk_factor_results(assessment_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_customer_date ON scenario_runs(customer_id, created_at);
CREATE INDEX IF NOT EXISTS idx_actions_customer_status ON account_actions(customer_id, action_status);
CREATE INDEX IF NOT EXISTS idx_decisions_customer_date ON decision_events(customer_id, event_at);

-- Versioned scoring policy separates business governance from application code.
CREATE TABLE IF NOT EXISTS policy_versions (
    policy_version_id TEXT PRIMARY KEY,
    version_number INTEGER NOT NULL UNIQUE CHECK (version_number > 0),
    policy_name TEXT NOT NULL,
    policy_status TEXT NOT NULL CHECK (policy_status IN ('Draft', 'Active', 'Retired', 'Rejected')),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    rationale TEXT NOT NULL,
    activated_at TEXT
);

CREATE TABLE IF NOT EXISTS policy_parameters (
    policy_version_id TEXT NOT NULL,
    parameter_name TEXT NOT NULL,
    parameter_value REAL NOT NULL,
    PRIMARY KEY (policy_version_id, parameter_name),
    FOREIGN KEY (policy_version_id) REFERENCES policy_versions(policy_version_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS policy_approvals (
    policy_approval_id TEXT PRIMARY KEY,
    policy_version_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('Approved', 'Rejected')),
    decided_at TEXT NOT NULL,
    decided_by TEXT NOT NULL,
    decision_notes TEXT NOT NULL,
    FOREIGN KEY (policy_version_id) REFERENCES policy_versions(policy_version_id)
);

CREATE TABLE IF NOT EXISTS assessment_policy_versions (
    assessment_id TEXT PRIMARY KEY,
    policy_version_id TEXT NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES risk_assessments(assessment_id) ON DELETE CASCADE,
    FOREIGN KEY (policy_version_id) REFERENCES policy_versions(policy_version_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_policy
    ON policy_versions(policy_status) WHERE policy_status = 'Active';
CREATE INDEX IF NOT EXISTS idx_policy_parameters_version ON policy_parameters(policy_version_id);

-- Capacity plans preserve both selected and deferred interventions so allocation
-- decisions remain reviewable after constraints or priorities change.
CREATE TABLE IF NOT EXISTS capacity_plans (
    capacity_plan_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    as_of_date TEXT NOT NULL,
    available_hours REAL NOT NULL CHECK (available_hours >= 0),
    available_budget REAL NOT NULL CHECK (available_budget >= 0),
    support_slots INTEGER NOT NULL CHECK (support_slots >= 0),
    enablement_slots INTEGER NOT NULL CHECK (enablement_slots >= 0),
    selected_count INTEGER NOT NULL CHECK (selected_count >= 0),
    hours_allocated REAL NOT NULL CHECK (hours_allocated >= 0),
    budget_allocated REAL NOT NULL CHECK (budget_allocated >= 0),
    acv_covered REAL NOT NULL CHECK (acv_covered >= 0),
    policy_version_id TEXT,
    FOREIGN KEY (policy_version_id) REFERENCES policy_versions(policy_version_id)
);

CREATE TABLE IF NOT EXISTS capacity_plan_items (
    capacity_plan_item_id TEXT PRIMARY KEY,
    capacity_plan_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    priority_rank INTEGER NOT NULL CHECK (priority_rank > 0),
    selected INTEGER NOT NULL CHECK (selected IN (0, 1)),
    factor_name TEXT NOT NULL,
    intervention TEXT NOT NULL,
    delivery_team TEXT NOT NULL,
    estimated_hours REAL NOT NULL CHECK (estimated_hours >= 0),
    estimated_cost REAL NOT NULL CHECK (estimated_cost >= 0),
    support_slots_required INTEGER NOT NULL CHECK (support_slots_required >= 0),
    enablement_slots_required INTEGER NOT NULL CHECK (enablement_slots_required >= 0),
    addressable_points INTEGER NOT NULL CHECK (addressable_points >= 0),
    decision_value REAL NOT NULL CHECK (decision_value >= 0),
    evidence_record_ids_json TEXT NOT NULL,
    deferral_reason TEXT,
    FOREIGN KEY (capacity_plan_id) REFERENCES capacity_plans(capacity_plan_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_capacity_items_plan ON capacity_plan_items(capacity_plan_id, selected, priority_rank);
CREATE INDEX IF NOT EXISTS idx_capacity_items_customer ON capacity_plan_items(customer_id);

-- A local installation has one active business dataset at a time. Historical
-- registrations retain who activated each governed ingestion run.
CREATE TABLE IF NOT EXISTS business_data_imports (
    business_data_import_id TEXT PRIMARY KEY,
    organization_name TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    imported_by TEXT NOT NULL,
    data_classification TEXT NOT NULL CHECK (
        data_classification IN ('Synthetic demo', 'Anonymized', 'Confidential internal')
    ),
    ingestion_run_id TEXT NOT NULL UNIQUE,
    source_file_count INTEGER NOT NULL CHECK (source_file_count >= 0),
    source_row_count INTEGER NOT NULL CHECK (source_row_count >= 0),
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(ingestion_run_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_business_dataset
    ON business_data_imports(active) WHERE active = 1;
