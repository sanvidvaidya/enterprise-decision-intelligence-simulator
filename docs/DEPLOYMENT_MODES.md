# Deployment Modes

## Secure default

`EDS_DEPLOYMENT_MODE` controls the application trust boundary. If it is missing, the application selects `public_demo`. An unknown value stops startup instead of guessing.

| Capability | Public Demo | Private Business |
| --- | --- | --- |
| Dataset | Fresh isolated synthetic data | Persistent local SQLite data |
| Portfolio exploration | Enabled | Enabled |
| Customer evidence | Enabled | Enabled |
| What-if calculations | Enabled | Enabled |
| CSV and HTML synthetic exports | Enabled | Not restricted |
| Business-data upload | Disabled | Enabled |
| Saved scenarios and snapshots | Disabled | Enabled |
| Actions and decision logs | Disabled | Enabled |
| Capacity-plan persistence | Disabled | Enabled |
| Policy draft and approval | Disabled | Enabled |
| Intended audience | Public portfolio visitors | Authorized local users |

Public Demo creates its source files and SQLite database in a temporary process directory. It never opens a private installation's database. The interface disables state-changing controls, and the application checks the deployment mode again before executing each persistent operation.

Private Business uses `data/decision_intelligence.db`. This file and uploaded source extracts are ignored by Git. The mode is suitable for an authorized laptop or controlled local environment. It is not a substitute for enterprise identity, authorization, encrypted storage, or tenant isolation.

## Run Public Demo locally

Public Demo is the default:

```powershell
python -m streamlit run streamlit_app.py
```

You can also declare it explicitly:

```powershell
$env:EDS_DEPLOYMENT_MODE = "public_demo"
python -m streamlit run streamlit_app.py
```

## Run Private Business locally

Windows PowerShell:

```powershell
$env:EDS_DEPLOYMENT_MODE = "private_business"
$env:PYTHONPATH = "$PWD\src"
python -m decision_intelligence.bootstrap
python -m streamlit run streamlit_app.py
```

macOS or Linux:

```bash
export EDS_DEPLOYMENT_MODE="private_business"
export PYTHONPATH="$PWD/src"
python -m decision_intelligence.bootstrap
python -m streamlit run streamlit_app.py
```

Close the terminal or remove the environment variable to return to the safe default.

## Publish Public Demo for free

Streamlit Community Cloud describes its community hosting as free and connects deployments directly to GitHub repositories. Current service terms and limits can change, so verify them before deployment.

1. Push the tested repository to GitHub.
2. Sign in at [share.streamlit.io](https://share.streamlit.io/).
3. Choose **Create app** and select the repository and `main` branch.
4. Set the entrypoint to `streamlit_app.py`.
5. Leave `EDS_DEPLOYMENT_MODE` unset so the secure default selects Public Demo.
6. Deploy and verify that the sidebar says **Public Demo mode**.
7. Open **Data Onboarding** and confirm that the uploader is disabled.
8. Open Actions, Policy Studio, Scenario Lab, and Capacity Planner and confirm that persistence buttons are disabled.

Official references:

- [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [Deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Resource limits and hibernation](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app)
- [Local file persistence warning](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data)

Community Cloud does not guarantee local-file persistence. This is acceptable for Public Demo because its database is deliberately disposable. Do not change a public deployment to `private_business` and do not upload confidential data to it.

## Zero-cost boundary

The software, local Private Business mode, GitHub repository, and current Community Cloud public demonstration can all be used without a required payment. A durable worldwide service for multiple businesses cannot be represented as permanently free or production-safe. That future architecture would require authenticated identities, tenant isolation, durable managed storage, transport encryption, monitoring, backups, recovery, and organizational security approval.
