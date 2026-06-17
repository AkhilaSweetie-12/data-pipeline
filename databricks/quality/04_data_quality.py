# Databricks notebook source
# MAGIC %md
# MAGIC # Data Quality Framework
# MAGIC Runs declarative checks against the Silver layer and writes results to
# MAGIC `gold.data_quality_report`. Fails the task if any **critical** check fails so the
# MAGIC Databricks Workflow surfaces the issue.
# MAGIC
# MAGIC Checks:
# MAGIC - Customer email cannot be null
# MAGIC - Customer ID must be unique
# MAGIC - Order amount > 0
# MAGIC - Order customer_id must exist in silver.customers

# COMMAND ----------

dbutils.widgets.text("catalog", "hive_metastore")
dbutils.widgets.text("fail_on_critical", "true")
CATALOG = dbutils.widgets.get("catalog")
FAIL_ON_CRITICAL = dbutils.widgets.get("fail_on_critical").lower() == "true"

from datetime import datetime
from pyspark.sql import functions as F

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.gold")

customers = spark.table(f"{CATALOG}.silver.customers")
orders = spark.table(f"{CATALOG}.silver.orders")

results = []

def add_result(check, entity, failed_count, severity):
    results.append({
        "check_name": check,
        "entity": entity,
        "failed_records": int(failed_count),
        "status": "PASS" if failed_count == 0 else "FAIL",
        "severity": severity,
        "run_ts": datetime.utcnow().isoformat(),
    })

# COMMAND ----------

# 1. Customer email not null
add_result("email_not_null", "customers",
           customers.filter(F.col("email").isNull()).count(), "critical")

# 2. Customer ID unique
dup_ids = customers.groupBy("customer_id").count().filter(F.col("count") > 1).count()
add_result("customer_id_unique", "customers", dup_ids, "critical")

# 3. Order amount > 0
add_result("amount_positive", "orders",
           orders.filter(F.col("amount") <= 0).count(), "critical")

# 4. Order customer_id exists
valid_ids = customers.select("customer_id").distinct()
orphan = orders.join(valid_ids, "customer_id", "left_anti").count()
add_result("order_customer_exists", "orders", orphan, "critical")

# COMMAND ----------

report_df = spark.createDataFrame(results)
report_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{CATALOG}.gold.data_quality_report")

display(report_df)

failed_critical = [r for r in results if r["status"] == "FAIL" and r["severity"] == "critical"]
print(f"Checks run={len(results)} critical_failures={len(failed_critical)}")

if FAIL_ON_CRITICAL and failed_critical:
    raise Exception(f"Critical data quality checks failed: {[r['check_name'] for r in failed_critical]}")

# COMMAND ----------

dbutils.notebook.exit("data_quality_success")
