# Retail DataSecOps Platform

End-to-end **DataSecOps** platform for Retail Sales Management: enter business data
through a web UI, persist to a relational database, process it through an Azure
Databricks **ELT pipeline with Medallion Architecture** (Bronze / Silver / Gold),
apply **security & governance** (Unity Catalog, PII masking, RBAC, audit), and
visualize results on dashboards.

## Tech Stack

| Area | Technology |
|------|-----------|
| Frontend | React, Material UI, Axios, Recharts |
| Backend | Python FastAPI, SQLAlchemy, Pydantic |
| Database | Azure SQL Database (SQLite for local DEV) |
| Data Platform | Azure Databricks, Unity Catalog, Delta Lake, Workflows, Asset Bundles |
| Storage | Azure Data Lake Storage Gen2 |
| Security | Azure Key Vault, Unity Catalog RBAC, PII Masking, Audit Logging |
| CI/CD | Azure DevOps, Databricks Asset Bundles, Git |
| Monitoring | Databricks Job Monitoring, Audit Logs, Data Quality Reports |

## Repository Structure

```
data-pipeline/
├── frontend/                  React + MUI app (Customers, Orders, Dashboard)
├── backend/                   FastAPI service (+ tests, seed data)
├── sql/                       Azure SQL schema & sample data
├── databricks/
│   ├── bronze/                Raw ingestion notebook
│   ├── silver/                Cleansing + quarantine notebook
│   ├── gold/                  Business metrics notebook
│   ├── quality/               Data quality framework notebook
│   ├── audit/                 Audit report notebook
│   ├── setup/                 Unity Catalog governance SQL
│   └── dashboard/             Databricks SQL dashboard queries
├── resources/jobs/            Workflow (job) definition
├── tests/                     Pipeline unit tests
├── terraform/                 Azure infrastructure as code
├── docs/                      Architecture + deployment guide
├── databricks.yml             Databricks Asset Bundle
├── azure-pipelines.yml        Azure DevOps CI/CD
└── README.md
```

## Quick Start (Local DEV)

```powershell
# Backend
cd backend
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed_data.py
uvicorn app.main:app --reload      # http://localhost:8000/docs

# Frontend (new terminal)
cd frontend
copy .env.example .env
npm install
npm run dev                        # http://localhost:5173
```

The backend defaults to a local SQLite database so the entire UI -> API ->
DB -> Dashboard loop runs with **no cloud setup**. Switch to Azure SQL by setting
`DATABASE_URL` in `backend/.env`.

### Run with Docker (one command)

```bash
docker compose up --build
# Frontend http://localhost:3000  |  Backend http://localhost:8000/docs
```

Spins up Azure SQL Edge + FastAPI + the React build (nginx). The backend
auto-creates tables and seeds demo users on startup.

### Demo Accounts (DEV)

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| `admin` | `admin123` | admin | Full access + Audit Log |
| `engineer` | `engineer123` | data_engineer | Read + write customers/orders |
| `analyst` | `analyst123` | analyst | Read-only |

## Authentication & RBAC

- **JWT login** at `POST /auth/login`; token attached by the React Axios interceptor.
- **Role-based access**: writes restricted to `admin`/`data_engineer`; `analyst` is read-only (write buttons hidden in UI, `403` enforced by API).
- **Audit logging**: every login and write is persisted to `audit_logs` and viewable by admins at `/auth/audit` (and the **Audit Log** UI page).
- These app roles mirror the **Unity Catalog** governance roles.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/customers` | Create customer (validates unique email) |
| GET  | `/customers` | List customers |
| PUT  | `/customers/{id}` | Update customer |
| POST | `/orders` | Create order (validates customer + amount) |
| GET  | `/orders` | List orders |
| GET  | `/dashboard/metrics` | Aggregated dashboard metrics |
| POST | `/auth/login` | Obtain JWT (OAuth2 password flow) |
| GET  | `/auth/me` | Current user |
| GET  | `/auth/audit` | Audit log (admin only) |
| GET  | `/health` | Health check |

OpenAPI docs at `/docs`.

## Medallion Pipeline

`Bronze -> Silver -> Gold -> Data Quality -> Audit` orchestrated by the
Databricks Workflow in `resources/jobs/retail_pipeline_job.yml`.

- **Bronze**: JDBC extract from Azure SQL into raw Delta + ingestion timestamp.
- **Silver**: dedupe, email validation, null handling, standardization, quarantine.
- **Gold**: `customer_sales`, `city_revenue`, `daily_revenue`.
- **Quality**: critical checks (email not null, unique IDs, amount > 0, FK exists).
- **Audit**: row counts + DQ outcomes into `gold.audit_log`.

## Security & Governance

- Secrets in **Azure Key Vault** (Databricks secret scope `retail-kv`).
- **Unity Catalog RBAC** for `data_engineers`, `analysts`, `admins`.
- **PII masking** of email/phone + **row-level security** by city.
- See `databricks/setup/unity_catalog_governance.sql`.

## Documentation

- Architecture (Mermaid): `docs/architecture.md`
- Rendered architecture diagram: `docs/architecture.svg`
- Full deployment / end-to-end guide: `docs/DEPLOYMENT.md`
- Power BI dashboard guide: `docs/POWERBI.md`
- Databricks Lakeview dashboard: `databricks/dashboard/retail_dashboard.lvdash.json`

## Testing

```powershell
cd backend && python -m pytest -q   # API + auth + RBAC + audit tests (14)
python -m pytest tests -q           # data-quality rule tests (6)
```
