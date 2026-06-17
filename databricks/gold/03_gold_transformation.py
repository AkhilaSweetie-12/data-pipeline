# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer - Business Metrics
# MAGIC Builds aggregated, analytics-ready tables from the Silver layer.
# MAGIC
# MAGIC Outputs:
# MAGIC - `gold.customer_sales` - revenue & order counts per customer
# MAGIC - `gold.city_revenue`   - revenue per city
# MAGIC - `gold.daily_revenue`  - revenue per day

# COMMAND ----------

dbutils.widgets.text("catalog", "hive_metastore")
CATALOG = dbutils.widgets.get("catalog")

from pyspark.sql import functions as F

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.gold")

customers = spark.table(f"{CATALOG}.silver.customers")
orders = spark.table(f"{CATALOG}.silver.orders")

# COMMAND ----------

# customer_sales
customer_sales = (
    orders.groupBy("customer_id")
    .agg(
        F.sum("amount").alias("total_revenue"),
        F.count("order_id").alias("order_count"),
        F.avg("amount").alias("avg_order_value"),
    )
    .join(customers.select("customer_id", "name", "city"), "customer_id", "left")
    .withColumn("_built_at", F.current_timestamp())
)
customer_sales.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{CATALOG}.gold.customer_sales")

# COMMAND ----------

# city_revenue
city_revenue = (
    orders.join(customers.select("customer_id", "city"), "customer_id", "left")
    .withColumn("city", F.coalesce(F.col("city"), F.lit("Unknown")))
    .groupBy("city")
    .agg(
        F.sum("amount").alias("revenue"),
        F.count("order_id").alias("order_count"),
    )
    .withColumn("_built_at", F.current_timestamp())
)
city_revenue.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{CATALOG}.gold.city_revenue")

# COMMAND ----------

# daily_revenue
daily_revenue = (
    orders.groupBy("order_date")
    .agg(
        F.sum("amount").alias("revenue"),
        F.count("order_id").alias("order_count"),
    )
    .orderBy("order_date")
    .withColumn("_built_at", F.current_timestamp())
)
daily_revenue.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{CATALOG}.gold.daily_revenue")

print("gold tables built: customer_sales, city_revenue, daily_revenue")

# COMMAND ----------

dbutils.notebook.exit("gold_transformation_success")
