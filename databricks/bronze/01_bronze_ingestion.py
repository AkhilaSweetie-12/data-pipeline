# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer - Raw Ingestion
# MAGIC Extracts `customers` and `orders` from Azure SQL Database and lands them as raw Delta
# MAGIC tables in `retail_dev.bronze`. An ingestion timestamp and source-system column are added.
# MAGIC Secrets are read from the Key Vault-backed secret scope (no hard-coded credentials).

# COMMAND ----------

dbutils.widgets.text("catalog", "hive_metastore")
dbutils.widgets.text("secret_scope", "retail-kv")

CATALOG = dbutils.widgets.get("catalog")
SCOPE = dbutils.widgets.get("secret_scope")

# COMMAND ----------

from pyspark.sql.functions import current_timestamp, lit

# hive_metastore always exists; only the schema needs to be created.
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.bronze")

# COMMAND ----------

# Azure SQL connection details sourced from the Key Vault-backed scope.
jdbc_host = dbutils.secrets.get(SCOPE, "sql-server-host")      # e.g. myserver.database.windows.net
jdbc_db   = dbutils.secrets.get(SCOPE, "sql-database")          # e.g. retail
jdbc_user = dbutils.secrets.get(SCOPE, "sql-username")
jdbc_pwd  = dbutils.secrets.get(SCOPE, "sql-password")

jdbc_url = (
    f"jdbc:sqlserver://{jdbc_host}:1433;database={jdbc_db};"
    "encrypt=true;trustServerCertificate=false;loginTimeout=30;"
)
common_opts = {
    "url": jdbc_url,
    "user": jdbc_user,
    "password": jdbc_pwd,
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
}

# COMMAND ----------

def ingest(table_name: str, target: str):
    df = (
        spark.read.format("jdbc")
        .options(**common_opts)
        .option("dbtable", f"dbo.{table_name}")
        .load()
        .withColumn("_ingested_at", current_timestamp())
        .withColumn("_source_system", lit("azure_sql"))
    )
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{CATALOG}.bronze.{target}")
    )
    print(f"Ingested {df.count()} rows into {CATALOG}.bronze.{target}")

ingest("customers", "customers_raw")
ingest("orders", "orders_raw")

# COMMAND ----------

dbutils.notebook.exit("bronze_ingestion_success")
