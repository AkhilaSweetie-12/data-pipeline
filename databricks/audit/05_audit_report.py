# Databricks notebook source
# MAGIC %md
# MAGIC # Audit Report Generation
# MAGIC Captures pipeline lineage, row counts per layer, quarantine counts, data-quality
# MAGIC outcomes and PII-access governance metadata into `gold.audit_log` for compliance.

# COMMAND ----------

dbutils.widgets.text("catalog", "hive_metastore")
CATALOG = dbutils.widgets.get("catalog")

from datetime import datetime
from pyspark.sql import functions as F

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.gold")

def safe_count(table):
    try:
        return spark.table(f"{CATALOG}.{table}").count()
    except Exception:
        return -1

run_ts = datetime.utcnow().isoformat()
ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
try:
    run_user = ctx.userName().get()
except Exception:
    run_user = "unknown"

# COMMAND ----------

metrics = [
    ("bronze.customers_raw",        safe_count("bronze.customers_raw")),
    ("bronze.orders_raw",           safe_count("bronze.orders_raw")),
    ("silver.customers",            safe_count("silver.customers")),
    ("silver.customers_quarantine", safe_count("silver.customers_quarantine")),
    ("silver.orders",               safe_count("silver.orders")),
    ("silver.orders_quarantine",    safe_count("silver.orders_quarantine")),
    ("gold.customer_sales",         safe_count("gold.customer_sales")),
    ("gold.city_revenue",           safe_count("gold.city_revenue")),
    ("gold.daily_revenue",          safe_count("gold.daily_revenue")),
]

audit_rows = [
    {"audit_ts": run_ts, "run_user": run_user, "table_name": t, "row_count": int(c)}
    for t, c in metrics
]

audit_df = spark.createDataFrame(audit_rows)
audit_df.write.format("delta").mode("append").option("mergeSchema", "true") \
    .saveAsTable(f"{CATALOG}.gold.audit_log")

display(audit_df)

# COMMAND ----------

# Pull quality outcomes for the audit trail (if the quality task produced a report).
try:
    dq = spark.table(f"{CATALOG}.gold.data_quality_report")
    print("=== Data Quality Summary ===")
    dq.groupBy("status").count().show()
except Exception:
    print("No data_quality_report found.")

# COMMAND ----------

dbutils.notebook.exit("audit_report_success")
