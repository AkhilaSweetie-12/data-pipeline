# Databricks notebook source
# MAGIC %md
# MAGIC ## Stage 7 — Incident Logger
# MAGIC Runs after ALL tasks complete (success or failure).
# MAGIC Reads DQ results and pipeline health predictions, writes structured
# MAGIC incident records to `gold.incidents` for compliance and alerting.

# COMMAND ----------

dbutils.widgets.text("catalog", "hive_metastore")
CATALOG = dbutils.widgets.get("catalog")

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType, IntegerType,
)
from datetime import datetime

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.gold")

# COMMAND ----------

# --- Ensure incidents table exists ---

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {CATALOG}.gold.incidents (
        incident_id     BIGINT GENERATED ALWAYS AS IDENTITY,
        detected_at     TIMESTAMP,
        severity        STRING,
        source          STRING,
        title           STRING,
        detail          STRING,
        status          STRING,
        risk_score      INT,
        dq_fail_count   INT
    )
    USING DELTA
""")

# COMMAND ----------

# --- Gather DQ failures ---

dq_failures = []
dq_fail_count = 0

try:
    dq_df = spark.table(f"{CATALOG}.gold.data_quality_report")
    failed = dq_df.filter(F.col("status") == "FAIL").orderBy(F.col("run_ts").desc())
    rows = failed.collect()
    dq_fail_count = len(rows)
    for r in rows:
        dq_failures.append(f"{r['check_name']} failed ({r['failed_records']} records)")
except Exception as e:
    print(f"DQ report not available: {e}")

print(f"DQ failures found: {dq_fail_count}")

# COMMAND ----------

# --- Gather predictive maintenance risk ---

risk_level = "LOW"
risk_score = 0

try:
    ph_df = spark.table(f"{CATALOG}.gold.pipeline_health_predictions")
    latest = ph_df.orderBy(F.col("predicted_at").desc()).limit(1).collect()
    if latest:
        risk_level = latest[0]["risk_level"]
        risk_score = int(latest[0]["risk_score"])
except Exception as e:
    print(f"Pipeline health predictions not available: {e}")

print(f"Risk level: {risk_level} | Score: {risk_score}")

# COMMAND ----------

# --- Determine if an incident should be raised ---

incidents_to_log = []
now = datetime.utcnow()

if dq_fail_count > 0:
    severity = "CRITICAL" if dq_fail_count >= 2 else "HIGH"
    incidents_to_log.append((
        now,
        severity,
        "DataQuality",
        f"{dq_fail_count} data quality check(s) failed",
        "; ".join(dq_failures),
        "OPEN",
        risk_score,
        dq_fail_count,
    ))

if risk_level == "HIGH":
    incidents_to_log.append((
        now,
        "HIGH",
        "PredictiveMaintenance",
        f"Pipeline health risk score is {risk_score}/100",
        f"Risk level: {risk_level}. Anomalies or DQ degradation detected. "
        f"Review gold.pipeline_health_predictions for details.",
        "OPEN",
        risk_score,
        dq_fail_count,
    ))

if risk_level == "MEDIUM":
    incidents_to_log.append((
        now,
        "MEDIUM",
        "PredictiveMaintenance",
        f"Pipeline health risk score elevated: {risk_score}/100",
        f"Risk level: MEDIUM. Monitor closely.",
        "OPEN",
        risk_score,
        dq_fail_count,
    ))

print(f"Incidents to log: {len(incidents_to_log)}")

# COMMAND ----------

# --- Write incidents to Delta table ---

if incidents_to_log:
    schema = StructType([
        StructField("detected_at",   TimestampType(), False),
        StructField("severity",      StringType(),    False),
        StructField("source",        StringType(),    False),
        StructField("title",         StringType(),    False),
        StructField("detail",        StringType(),    False),
        StructField("status",        StringType(),    False),
        StructField("risk_score",    IntegerType(),   False),
        StructField("dq_fail_count", IntegerType(),   False),
    ])

    inc_df = spark.createDataFrame(incidents_to_log, schema)

    (
        inc_df.write.format("delta")
        .mode("append")
        .option("mergeSchema", "true")
        .saveAsTable(f"{CATALOG}.gold.incidents")
    )

    for row in incidents_to_log:
        print(f"[{row[1]}] {row[3]} — {row[4]}")

    summary = f"incidents_raised:{len(incidents_to_log)}|severity:{incidents_to_log[0][1]}"
else:
    print("No incidents raised. Pipeline is healthy.")
    summary = "incidents_raised:0|status:HEALTHY"

# COMMAND ----------

# --- Show current open incidents ---

print("\n--- Open Incidents ---")
spark.sql(f"""
    SELECT detected_at, severity, source, title, status
    FROM {CATALOG}.gold.incidents
    WHERE status = 'OPEN'
    ORDER BY detected_at DESC
    LIMIT 10
""").show(truncate=False)

# COMMAND ----------

dbutils.notebook.exit(summary)
