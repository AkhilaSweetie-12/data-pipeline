-- =====================================================================
-- Databricks SQL Dashboard queries (Gold layer)
-- Create a dashboard in Databricks SQL and add each query as a widget.
-- =====================================================================

-- Widget: Revenue Trends (line chart)  X=order_date  Y=revenue
SELECT order_date, revenue, order_count
FROM retail_dev.gold.daily_revenue
ORDER BY order_date;

-- Widget: Top Customers (bar chart)  X=name  Y=total_revenue
SELECT name, total_revenue, order_count
FROM retail_dev.gold.customer_sales
ORDER BY total_revenue DESC
LIMIT 10;

-- Widget: Revenue by City (bar / map)  X=city  Y=revenue
SELECT city, revenue, order_count
FROM retail_dev.gold.city_revenue
ORDER BY revenue DESC;

-- Widget: Data Quality Metrics (counter/table)
SELECT check_name, entity, status, failed_records, severity, run_ts
FROM retail_dev.gold.data_quality_report
ORDER BY status DESC, check_name;

-- Widget: Failed / Quarantined Records (counters)
SELECT 'customers_quarantine' AS source, COUNT(*) AS failed_records
FROM retail_dev.silver.customers_quarantine
UNION ALL
SELECT 'orders_quarantine' AS source, COUNT(*) AS failed_records
FROM retail_dev.silver.orders_quarantine;

-- Widget: KPI summary counters
SELECT
  (SELECT COALESCE(SUM(revenue),0) FROM retail_dev.gold.daily_revenue) AS total_revenue,
  (SELECT COALESCE(SUM(order_count),0) FROM retail_dev.gold.daily_revenue) AS total_orders,
  (SELECT COUNT(*) FROM retail_dev.silver.customers) AS total_customers;
