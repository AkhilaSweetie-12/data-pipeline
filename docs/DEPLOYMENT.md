# Deployment & End-to-End Setup Guide

This guide covers running everything locally in a single DEV environment, then
deploying the data platform to Azure.

---

## Part A - Local DEV (zero Azure required)

The backend defaults to **SQLite** so the full UI -> API -> DB -> Dashboard loop
works with no cloud resources.

### 1. Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed_data.py            # optional sample data
uvicorn app.main:app --reload  # http://localhost:8000  (docs at /docs)
```

### 2. Frontend (React)

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev                    # http://localhost:5173
```

Open the app, add customers/orders, and view the Dashboard.

### 3. Tests

```powershell
cd backend && python -m pytest -q   # API + auth + RBAC + audit tests
python -m pytest tests -q           # pipeline quality-rule tests (repo root)
```

### 4. Run everything with Docker (alternative)

```bash
docker compose up --build
# Frontend http://localhost:3000  |  Backend http://localhost:8000/docs
```

Brings up Azure SQL Edge + FastAPI + the React/nginx build. Log in with the
demo accounts (`admin`/`admin123`, `engineer`/`engineer123`, `analyst`/`analyst123`).

---

## Part B - Azure Deployment

### 1. Provision infrastructure (Terraform)

```powershell
cd terraform
copy terraform.tfvars.example terraform.tfvars   # edit password
terraform init
terraform apply
```

Outputs include the SQL FQDN, Key Vault URI, Databricks URL and ADLS account.

### 2. Create Azure SQL schema & data

Connect with Azure Data Studio / sqlcmd and run:

```
sql/01_schema.sql
sql/02_sample_data.sql
```

Point the backend at Azure SQL by setting `DATABASE_URL` in `backend/.env`
(see `.env.example` for the `mssql+pyodbc` format). Requires the
*ODBC Driver 18 for SQL Server*.

### 3. Configure Databricks secrets (Key Vault-backed scope)

```bash
databricks secrets create-scope retail-kv \
  --scope-backend-type AZURE_KEYVAULT \
  --resource-id <key-vault-resource-id> \
  --dns-name <key-vault-uri>
```

Secrets used: `sql-server-host`, `sql-database`, `sql-username`, `sql-password`
(all populated by Terraform).

### 4. Deploy the Asset Bundle

```bash
export DATABRICKS_HOST=<workspace-url>
export DATABRICKS_TOKEN=<pat>
databricks bundle validate -t dev
databricks bundle deploy   -t dev
databricks bundle run retail_medallion_pipeline -t dev
```

### 5. Apply Unity Catalog governance

Run `databricks/setup/unity_catalog_governance.sql` on a UC-enabled SQL warehouse
(RBAC grants, PII masking, row/column security).

### 6. Build the dashboard

Options:
- **Databricks SQL Dashboard** - use the queries in `databricks/dashboard/dashboard_queries.sql`, or import the Lakeview definition `databricks/dashboard/retail_dashboard.lvdash.json` (Dashboards -> Import).
- **Power BI** - follow `docs/POWERBI.md` (connect to the SQL warehouse, add the DAX measures).

### 7. CI/CD (Azure DevOps)

Create a pipeline from `azure-pipelines.yml` and define pipeline variables:
`DATABRICKS_HOST`, `DATABRICKS_TOKEN` (secret).

---

## Verification Checklist

- [ ] UI adds customers/orders and dashboard updates
- [ ] `bronze.*_raw` populated with `_ingested_at`
- [ ] Invalid rows land in `silver.*_quarantine`
- [ ] `gold.*` metrics tables built
- [ ] `gold.data_quality_report` shows PASS for critical checks
- [ ] `gold.audit_log` has per-table row counts
- [ ] Masked email/phone for non-privileged users
