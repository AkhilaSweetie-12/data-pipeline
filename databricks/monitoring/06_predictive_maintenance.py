# Databricks notebook source
# MAGIC %md
# MAGIC ## Stage 6 — Predictive Maintenance
# MAGIC Reads pipeline run history from `gold.audit_log` and `gold.data_quality_report`,
# MAGIC detects anomalies using z-score analysis, calculates a risk score,
# MAGIC and writes predictions to `gold.pipeline_health_predictions`.

# COMMAND ----------

dbutils.widgets.text("catalog", "hive_metastore")
CATALOG = dbutils.widgets.get("catalog")

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType,
    DoubleType, IntegerType, TimestampType,
)
from datetime import datetime

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.gold")

# COMMAND ----------

# --- Read run history ---

try:
    audit_df = spark.table(f"{CATALOG}.gold.audit_log")
    audit_count = audit_df.count()
except Exception:
    audit_count = 0
    audit_df = None

try:
    dq_df = spark.table(f"{CATALOG}.gold.data_quality_report")
    dq_count = dq_df.count()
except Exception:
    dq_count = 0
    dq_df = None

print(f"Audit log rows: {audit_count} | DQ report rows: {dq_count}")

# COMMAND ----------

# --- Row-count anomaly detection (z-score) ---
# Flag tables whose latest row count deviates > 2 std deviations from historical mean.

anomaly_count = 0
anomaly_details = []

if audit_df is not None and audit_count >= 2:
    stats = (
        audit_df
        .groupBy("table_name")
        .agg(
            F.mean("row_count").alias("mean_count"),
            F.stddev("row_count").alias("std_count"),
            F.count("*").alias("run_count"),
        )
    )

    latest = (
        audit_df
        .withColumn(
            "_rn",
            F.row_number().over(
                __import__("pyspark.sql.window", fromlist=["Window"])
                .Window.partitionBy("table_name")
                .orderBy(F.col("audit_ts").desc())
            ),
        )
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )

    checked = (
        latest.join(stats, "table_name")
        .withColumn(
            "z_score",
            F.when(
                F.col("std_count") > 0,
                F.abs(F.col("row_count") - F.col("mean_count")) / F.col("std_count"),
            ).otherwise(F.lit(0.0)),
        )
        .withColumn("is_anomaly", F.col("z_score") > 2.0)
    )

    anomaly_rows = checked.filter(F.col("is_anomaly")).collect()
    anomaly_count = len(anomaly_rows)
    for r in anomaly_rows:
        anomaly_details.append(
            f"{r['table_name']}: count={r['row_count']} z={r['z_score']:.2f}"
        )
        print(f"ANOMALY detected — {anomaly_details[-1]}")

# COMMAND ----------

# --- DQ pass-rate trend ---

dq_pass_rate = 100.0
dq_fail_count = 0

if dq_df is not None and dq_count > 0:
    agg = dq_df.agg(
        (
            F.sum(F.when(F.col("status") == "PASS", 1).otherwise(0))
            / F.count("*")
            * 100
        ).alias("pass_rate"),
        F.sum(F.when(F.col("status") == "FAIL", 1).otherwise(0)).alias("fail_count"),
    ).collect()[0]

    dq_pass_rate = float(agg["pass_rate"] or 100.0)
    dq_fail_count = int(agg["fail_count"] or 0)

print(f"DQ pass rate: {dq_pass_rate:.1f}% | Failures: {dq_fail_count}")

# COMMAND ----------

# --- Composite risk score ---
# Each anomalous table contributes 30 points; each DQ failure contributes 20 points.
# Score is capped at 100.

risk_score = min((anomaly_count * 30) + (dq_fail_count * 20), 100)

if risk_score >= 70:
    risk_level = "HIGH"
    recommendation = (
        "Immediate attention required. "
        + (f"Anomalies: {'; '.join(anomaly_details)}. " if anomaly_details else "")
        + (f"{dq_fail_count} DQ check(s) failing." if dq_fail_count else "")
    )
elif risk_score >= 40:
    risk_level = "MEDIUM"
    recommendation = (
        "Monitor closely. "
        + (f"Anomalies: {'; '.join(anomaly_details)}. " if anomaly_details else "")
        + (f"{dq_fail_count} DQ check(s) failing." if dq_fail_count else "")
    )
else:
    risk_level = "LOW"
    recommendation = "Pipeline health is normal. No action required."

print(f"\nRisk level : {risk_level}")
print(f"Risk score : {risk_score}")
print(f"Recommendation: {recommendation}")

# COMMAND ----------

# --- Persist prediction ---

schema = StructType(
    [
        StructField("predicted_at", TimestampType(), False),
        StructField("risk_score", DoubleType(), False),
        StructField("risk_level", StringType(), False),
        StructField("dq_pass_rate", DoubleType(), False),
        StructField("anomaly_count", IntegerType(), False),
        StructField("dq_fail_count", IntegerType(), False),
        StructField("recommendation", StringType(), False),
    ]
)

pred_df = spark.createDataFrame(
    [
        (
            datetime.utcnow(),
            float(risk_score),
            risk_level,
            dq_pass_rate,
            anomaly_count,
            dq_fail_count,
            recommendation,
        )
    ],
    schema,
)

(
    pred_df.write.format("delta")
    .mode("append")
    .saveAsTable(f"{CATALOG}.gold.pipeline_health_predictions")
)

print(f"\nPrediction written to {CATALOG}.gold.pipeline_health_predictions")

# COMMAND ----------

dbutils.notebook.exit(f"risk:{risk_level}|score:{risk_score}|dq_pass_rate:{dq_pass_rate:.1f}")
