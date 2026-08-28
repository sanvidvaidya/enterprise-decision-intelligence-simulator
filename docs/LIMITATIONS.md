# Limitations

- All data is synthetic and designed for demonstration, not forecasting real customers.
- The weighted policy model is transparent but not statistically calibrated or causal.
- Usage data is monthly rather than event-level; the generator intentionally keeps the project small.
- SQLite is appropriate for a portfolio project but not concurrent enterprise production workloads.
- The app has no authentication, role-based access, PII handling, or audit retention policy.
- Warning approval is an explicit command-line governance mechanism, not an enterprise workflow engine.
- Incremental ingestion currently detects unchanged files and skips no-op reloads. A production system would add CDC, source timestamps, and conflict resolution.
- Recommendations are operational prompts, not legal, financial, or contractual advice.