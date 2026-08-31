# Business Data Onboarding

## What the workflow does

Data Onboarding lets an authorized organization replace the bundled synthetic demonstration with its own governed source snapshots. The interface provides templates, profiles uploads, previews records, runs the same validation service used by command-line ingestion, requests explicit approval for warnings, activates successful data, and records who imported it.

This is a five-domain decision model. It accepts the data needed for renewal decisions, not every file an organization owns.

| Required file | Business purpose |
| --- | --- |
| `account_managers.csv` | Ownership, routing, region, and accountability |
| `customers.csv` | Shared organization identity, segment, status, and customer attributes |
| `contracts.csv` | Renewal dates, commercial exposure, status, and terms |
| `product_usage_events.csv` | Monthly engagement, seats, sessions, and feature adoption |
| `support_tickets.csv` | Service severity, state, satisfaction, and resolution evidence |

## Local onboarding procedure

1. Set `EDS_DEPLOYMENT_MODE=private_business` on an authorized local installation.
2. Launch the application and open **Data Onboarding**.
3. Download the onboarding kit.
4. Review `README.txt`, the blank templates, and the synthetic examples.
5. Map source-system fields to the required headers without changing filenames or headers.
6. Use stable IDs consistently across every file.
7. Aggregate product usage to the monthly customer grain.
8. Remove or pseudonymize personal data that is not required for renewal decisions.
9. Keep each source file below 50 MB and upload all five source snapshots together.
10. Review the file profile, validation results, and source previews.
11. Enter the organization name, data steward, and classification.
12. Approve warning-level exceptions only after review.
13. Confirm replacement and activate the validated dataset.
14. Open **Home** to see the organization's portfolio and **Data Health** to inspect provenance.

## Quality and activation controls

The validation gate checks required files and columns, required nonempty operational sources, stable identifiers, duplicates, required values, numeric ranges, allowed business values, dates, foreign-key relationships, customer coverage, and seat-capacity anomalies. Every customer needs at least one contract and two monthly usage observations so the renewal and trend rules have enough evidence. Errors always block. Warnings block unless a named steward explicitly approves them.

Ingestion uses a transaction, so an unsuccessful load does not partially change the operational dataset. SHA-256 manifests support file-level change detection. A successful activation records the organization, steward, classification, source-file count, total source rows, ingestion run ID, and activation timestamp. Only one organization can be active in a local database.

## Privacy and authorization

- Upload only data that you are authorized to use.
- Remove fields that are not required by the data contract.
- Prefer pseudonymous stable identifiers over personal identifiers.
- Treat the SQLite file, generated exports, screenshots, and backups according to the selected data classification.
- Do not commit imported CSVs or the SQLite database to Git. The repository ignores generated local data by default.
- Do not expose the local Streamlit development server directly to the public internet.

## What worldwide shared access would require

Worldwide account-manager access is a deployment program, not an upload button. Before real confidential data is shared, a production design needs:

- authenticated user identities and session controls;
- role-based access scoped by organization, team, region, and account;
- strict tenant isolation;
- HTTPS and encrypted storage;
- managed secrets and key rotation;
- a production database designed for concurrent users;
- audit logging for views, exports, policy changes, and decisions;
- malware scanning and upload limits;
- retention, deletion, backup, recovery, and incident-response procedures;
- monitoring, rate limiting, security review, and privacy or legal approval.

Those controls are intentionally outside this local-first portfolio release. The current application demonstrates the domain model, governance workflow, and deterministic decision layer that a secured service could place behind an authenticated interface later.
