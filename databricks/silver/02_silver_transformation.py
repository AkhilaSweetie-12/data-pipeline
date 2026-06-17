# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer - Cleansing, Validation & Quarantine
# MAGIC Reads Bronze raw tables, deduplicates, validates emails, handles nulls, standardizes
# MAGIC formats, and routes invalid records to quarantine tables.
# MAGIC
# MAGIC Outputs:
# MAGIC - `silver.customers`, `silver.customers_quarantine`
# MAGIC - `silver.orders`, `silver.orders_quarantine`

# COMMAND ----------

dbutils.widgets.text("catalog", "hive_metastore")
CATALOG = dbutils.widgets.get("catalog")

from pyspark.sql import functions as F
from pyspark.sql.window import Window

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.silver")

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

# COMMAND ----------

# MAGIC %md ### Customers

# COMMAND ----------

cust_raw = spark.table(f"{CATALOG}.bronze.customers_raw")

# Deduplicate keeping the most recent ingestion per customer_id.
w = Window.partitionBy("customer_id").orderBy(F.col("_ingested_at").desc())
cust_dedup = (
    cust_raw.withColumn("_rn", F.row_number().over(w))
    .filter(F.col("_rn") == 1)
    .drop("_rn")
)

# Standardize formats.
cust_std = (
    cust_dedup
    .withColumn("name", F.initcap(F.trim(F.col("name"))))
    .withColumn("email", F.lower(F.trim(F.col("email"))))
    .withColumn("city", F.initcap(F.trim(F.col("city"))))
    .withColumn("phone", F.regexp_replace(F.col("phone"), r"[^0-9]", ""))
)

# Validation rules: email not null AND valid format AND customer_id not null.
valid_cond = (
    F.col("email").isNotNull()
    & F.col("email").rlike(EMAIL_REGEX)
    & F.col("customer_id").isNotNull()
)

cust_valid = cust_std.filter(valid_cond).withColumn(
    "city", F.when(F.col("city").isNull() | (F.col("city") == ""), F.lit("Unknown")).otherwise(F.col("city"))
)
cust_invalid = cust_std.filter(~valid_cond).withColumn(
    "_quarantine_reason",
    F.when(F.col("email").isNull(), "email_null")
     .when(~F.col("email").rlike(EMAIL_REGEX), "email_invalid_format")
     .when(F.col("customer_id").isNull(), "customer_id_null")
     .otherwise("unknown"),
).withColumn("_quarantined_at", F.current_timestamp())

cust_valid.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{CATALOG}.silver.customers")
cust_invalid.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{CATALOG}.silver.customers_quarantine")

print(f"silver.customers={cust_valid.count()} quarantine={cust_invalid.count()}")

# COMMAND ----------

# MAGIC %md ### Orders

# COMMAND ----------

ord_raw = spark.table(f"{CATALOG}.bronze.orders_raw")
valid_customer_ids = cust_valid.select("customer_id").distinct()

w2 = Window.partitionBy("order_id").orderBy(F.col("_ingested_at").desc())
ord_dedup = (
    ord_raw.withColumn("_rn", F.row_number().over(w2))
    .filter(F.col("_rn") == 1)
    .drop("_rn")
    .withColumn("product_name", F.trim(F.col("product_name")))
)

ord_join = ord_dedup.join(
    valid_customer_ids.withColumnRenamed("customer_id", "_valid_cid"),
    ord_dedup.customer_id == F.col("_valid_cid"),
    "left",
)

order_valid_cond = (
    F.col("amount").isNotNull() & (F.col("amount") > 0)
    & F.col("quantity").isNotNull() & (F.col("quantity") > 0)
    & F.col("_valid_cid").isNotNull()
)

ord_valid = ord_join.filter(order_valid_cond).drop("_valid_cid")
ord_invalid = ord_join.filter(~order_valid_cond).withColumn(
    "_quarantine_reason",
    F.when(F.col("amount").isNull() | (F.col("amount") <= 0), "amount_not_positive")
     .when(F.col("quantity").isNull() | (F.col("quantity") <= 0), "quantity_not_positive")
     .when(F.col("_valid_cid").isNull(), "customer_id_not_found")
     .otherwise("unknown"),
).drop("_valid_cid").withColumn("_quarantined_at", F.current_timestamp())

ord_valid.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{CATALOG}.silver.orders")
ord_invalid.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{CATALOG}.silver.orders_quarantine")

print(f"silver.orders={ord_valid.count()} quarantine={ord_invalid.count()}")

# COMMAND ----------

dbutils.notebook.exit("silver_transformation_success")
