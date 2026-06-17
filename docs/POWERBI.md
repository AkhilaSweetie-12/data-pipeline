# Power BI Dashboard (alternative to Databricks SQL Dashboard)

You can visualize the Gold layer in **Power BI** instead of (or in addition to)
the Databricks Lakeview dashboard.

## 1. Connect Power BI to Databricks

1. In Power BI Desktop: **Get Data -> Azure Databricks**.
2. Enter:
   - **Server Hostname**: your workspace host (e.g. `adb-xxxx.azuredatabricks.net`)
   - **HTTP Path**: from your SQL Warehouse connection details
3. Authenticate with Azure AD or a Personal Access Token.
4. Use **DirectQuery** for live metrics or **Import** for snapshots.
5. Select tables from `retail_dev.gold`:
   - `customer_sales`, `city_revenue`, `daily_revenue`,
     `data_quality_report`
   - and `retail_dev.silver.*_quarantine` for failed records.

## 2. Recommended Visuals

| Visual | Source table | Fields |
|--------|--------------|--------|
| Line chart - Revenue Trends | `daily_revenue` | axis `order_date`, value `revenue` |
| Bar chart - Top Customers | `customer_sales` | axis `name`, value `total_revenue` |
| Map / Bar - Revenue by City | `city_revenue` | location `city`, value `revenue` |
| Table - Data Quality Metrics | `data_quality_report` | `check_name`, `status`, `failed_records` |
| Cards - Failed Records | `*_quarantine` | count rows |

## 3. DAX Measures

```DAX
Total Revenue = SUM ( daily_revenue[revenue] )

Total Orders = SUM ( daily_revenue[order_count] )

Total Customers = DISTINCTCOUNT ( customer_sales[customer_id] )

Failed Records =
    COUNTROWS ( customers_quarantine ) + COUNTROWS ( orders_quarantine )

DQ Pass Rate =
DIVIDE (
    CALCULATE ( COUNTROWS ( data_quality_report ), data_quality_report[status] = "PASS" ),
    COUNTROWS ( data_quality_report )
)
```

## 4. Governance Note

Power BI honors **Unity Catalog** row/column-level security and PII masking when
connected via Azure AD pass-through, so analysts see masked email/phone and only
their permitted rows - the same controls defined in
`databricks/setup/unity_catalog_governance.sql`.
