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