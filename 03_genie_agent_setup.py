# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Genie Agent setup (manual, reference only)
# MAGIC
# MAGIC This notebook creates nothing - Genie Agent creation is a UI flow. Copy the
# MAGIC text below into the Genie One "Create Agent" form.
# MAGIC
# MAGIC ## Name
# MAGIC ```
# MAGIC Retail Analytics Genie
# MAGIC ```
# MAGIC
# MAGIC ## Description
# MAGIC ```
# MAGIC Answers natural-language questions about Northwind Retail sales performance,
# MAGIC customer returns, and inventory health using certified metric views. Covers
# MAGIC revenue, units sold, orders, average order value, returns and return volume,
# MAGIC and stock-on-hand, sliced by date, product category/brand, customer
# MAGIC segment/region, and store region/channel.
# MAGIC ```
# MAGIC
# MAGIC ## Data sources to attach
# MAGIC Add these three metric views as the agent's tables/data sources (created in
# MAGIC `02_create_metric_views`):
# MAGIC - `mv_sales_performance`
# MAGIC - `mv_customer_returns`
# MAGIC - `mv_inventory_health`
# MAGIC
# MAGIC Do **not** attach the raw fact/dimension tables directly - the point of the demo
# MAGIC is to show Genie preferring the governed metric views over ad hoc joins.
# MAGIC
# MAGIC ## Custom instructions (agent-level, not workspace-level)
# MAGIC ```
# MAGIC You are a retail analytics assistant for Northwind Retail.
# MAGIC
# MAGIC - Always prefer the metric views (mv_sales_performance, mv_customer_returns,
# MAGIC   mv_inventory_health) over querying raw tables directly.
# MAGIC - "Revenue" or "sales" means the total_revenue measure in mv_sales_performance,
# MAGIC   not list price or unit cost.
# MAGIC - "Return rate" is not a stored measure - compute it as
# MAGIC   mv_customer_returns.return_amount / mv_sales_performance.total_revenue for the
# MAGIC   same time period and dimension slice, and say so when you do.
# MAGIC - All monetary figures are in USD.
# MAGIC - When a question is ambiguous about time range, default to the trailing 12
# MAGIC   months and state the range you used.
# MAGIC ```
# MAGIC
# MAGIC ## Sample / benchmark questions to add in the agent's setup screen
# MAGIC - What was total revenue last quarter by product category?
# MAGIC - What's our customer return rate this year vs last year?
# MAGIC - Which region has the highest revenue but also high returns?
# MAGIC - What is the average order value by customer segment?
# MAGIC - Which products have the lowest average stock on hand?
# MAGIC
# MAGIC ## After creating the agent
# MAGIC 1. Certify it: kebab menu on the agent -> **Assign certification** -> Certified.
# MAGIC 2. Assign it to the **Sales** domain (created manually in step 4).
# MAGIC 3. Come back and run `04_apply_certification_and_domains` for everything else
# MAGIC    (tables + metric views) - it's safe to also certify/tag the metric view you
# MAGIC    did by hand again; the script is idempotent.
