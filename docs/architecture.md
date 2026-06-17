# Architecture - Retail DataSecOps Platform

## End-to-End Flow

```mermaid
flowchart LR
    subgraph UI["Frontend (React + MUI)"]
        A[Customers] --> B[Orders]
        B --> C[Dashboard]
    end

    subgraph API["Backend (FastAPI + SQLAlchemy)"]
        D[/customers/]
        E[/orders/]
        F[/dashboard/metrics/]
    end

    subgraph DB["Azure SQL Database"]
        G[(customers)]
        H[(orders)]
    end

    subgraph DBX["Azure Databricks - Medallion"]
        I[Bronze: raw Delta]
        J[Silver: clean + quarantine]
        K[Gold: business metrics]
    end

    subgraph GOV["Governance / Security"]
        L[Unity Catalog RBAC]
        M[PII Masking]
        N[Audit Logs]
    end

    UI --> API --> DB
    DB -->|JDBC extract| I --> J --> K
    K --> O[Databricks SQL Dashboard]
    GOV -.-> DBX
    P[Azure Key Vault] -.secrets.-> DBX
    Q[ADLS Gen2] -.storage.-> DBX
```

## Medallion Layers

| Layer  | Tables | Purpose |
|--------|--------|---------|
| Bronze | `customers_raw`, `orders_raw` | Raw ingest + ingestion timestamp |
| Silver | `customers`, `orders`, `*_quarantine` | Dedupe, validate, standardize, quarantine |
| Gold   | `customer_sales`, `city_revenue`, `daily_revenue`, `data_quality_report`, `audit_log` | Business metrics & governance |

## Workflow (Databricks Job)

`Bronze -> Silver -> Gold -> Data Quality -> Audit`

## CI/CD (Azure DevOps)

`Validate -> Unit Tests -> Bundle Validate -> Bundle Deploy -> Run Workflow`

## Security Controls

- **Secrets**: Azure Key Vault-backed secret scope (`retail-kv`).
- **RBAC**: Unity Catalog grants for `data_engineers`, `analysts`, `admins`.
- **PII masking**: `mask_email`, `mask_phone` column masks on `silver.customers`.
- **Row-level security**: `city_row_filter` restricts analyst row visibility.
- **Audit**: row counts + DQ outcomes captured in `gold.audit_log`.
