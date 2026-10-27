# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Create metric views
# MAGIC
# MAGIC Creates 3 Unity Catalog metric views on top of the star schema from
# MAGIC `01_create_catalog_schema_tables`:
# MAGIC
# MAGIC | Metric view | Fact source | Joined dimensions |
# MAGIC |---|---|---|
# MAGIC | `mv_sales_performance` | `fact_sales` | `dim_date`, `dim_product`, `dim_customer`, `dim_store` |
# MAGIC | `mv_customer_returns` | `fact_returns` | `dim_date`, `dim_product`, `dim_customer` |
# MAGIC | `mv_inventory_health` | `fact_inventory` | `dim_date`, `dim_product`, `dim_store` |
# MAGIC
# MAGIC Each dimension and measure carries the "agentic metadata" Genie One's modeled
# MAGIC context layer reads: `display_name`, `description`, `synonyms`, and (for numeric
# MAGIC measures) a `format` hint such as currency or percentage.
# MAGIC
# MAGIC **A note on accuracy:** `display_name` / `description` / `synonyms` are stable,
# MAGIC documented metric-view metadata fields. The `format` block's exact keys have
# MAGIC moved between Databricks releases - if `CREATE VIEW` fails on the `format:`
# MAGIC lines, delete them, re-run, and add formatting afterward from the metric
# MAGIC view's YAML editor in Catalog Explorer (it has autocomplete/validation against
# MAGIC your workspace's current schema version).
# MAGIC
# MAGIC Cross-fact metrics (e.g. "return rate" = returns / sales) are **intentionally
# MAGIC not** defined as measures here - a metric view's measures can only aggregate
# MAGIC its own source + joined dimensions, not another fact table. Genie One can still
# MAGIC answer cross-metric-view questions like "what's our return rate" by querying
# MAGIC both `mv_sales_performance` and `mv_customer_returns` and combining them; the
# MAGIC "Total Revenue" and "Customer Return Rate" Pages (see `05_pages_content`)
# MAGIC document that formula explicitly so Genie has an authoritative definition to cite.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.1 `mv_sales_performance`

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {FQ_SCHEMA}.mv_sales_performance
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1

source: {FQ_SCHEMA}.fact_sales

joins:
  - name: date
    source: {FQ_SCHEMA}.dim_date
    on: source.date_key = date.date_key
  - name: product
    source: {FQ_SCHEMA}.dim_product
    on: source.product_key = product.product_key
  - name: customer
    source: {FQ_SCHEMA}.dim_customer
    on: source.customer_key = customer.customer_key
  - name: store
    source: {FQ_SCHEMA}.dim_store
    on: source.store_key = store.store_key

dimensions:
  - name: order_date
    expr: date.calendar_date
    display_name: "Order Date"
    synonyms: ["sale date", "purchase date"]
  - name: year
    expr: date.year
    display_name: "Year"
    synonyms: ["calendar year"]
  - name: quarter
    expr: date.quarter
    display_name: "Quarter"
    synonyms: ["fiscal quarter", "Q"]
  - name: month_name
    expr: date.month_name
    display_name: "Month"
    synonyms: ["calendar month"]
  - name: product_category
    expr: product.category
    display_name: "Product Category"
    synonyms: ["category", "merchandise category"]
  - name: product_brand
    expr: product.brand
    display_name: "Brand"
    synonyms: ["product brand", "manufacturer"]
  - name: customer_segment
    expr: customer.segment
    display_name: "Customer Segment"
    synonyms: ["segment", "customer type"]
  - name: customer_region
    expr: customer.region
    display_name: "Customer Region"
    synonyms: ["customer's region"]
  - name: store_region
    expr: store.region
    display_name: "Store Region"
    synonyms: ["region", "sales region"]
  - name: sales_channel
    expr: store.channel
    display_name: "Sales Channel"
    synonyms: ["channel", "online vs in-store"]

measures:
  - name: total_revenue
    expr: SUM(source.revenue)
    display_name: "Total Revenue"
    comment: "Sum of gross revenue (quantity * unit price) across all order lines"
    synonyms: ["revenue", "sales", "gross sales", "GMV", "total sales"]
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 2
  - name: total_units_sold
    expr: SUM(source.quantity)
    display_name: "Total Units Sold"
    comment: "Sum of units sold across all order lines"
    synonyms: ["units sold", "quantity sold", "volume"]
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
  - name: order_count
    expr: COUNT(DISTINCT source.order_id)
    display_name: "Order Count"
    comment: "Count of distinct order lines"
    synonyms: ["number of orders", "orders", "order volume"]
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
  - name: avg_order_value
    expr: SUM(source.revenue) / COUNT(DISTINCT source.order_id)
    display_name: "Average Order Value"
    comment: "Total revenue divided by order count"
    synonyms: ["AOV", "average order size", "average basket size"]
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 2
$$
""")

print(f"Created {FQ_SCHEMA}.mv_sales_performance")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.2 `mv_customer_returns`

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {FQ_SCHEMA}.mv_customer_returns
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1

source: {FQ_SCHEMA}.fact_returns

joins:
  - name: date
    source: {FQ_SCHEMA}.dim_date
    on: source.date_key = date.date_key
  - name: product
    source: {FQ_SCHEMA}.dim_product
    on: source.product_key = product.product_key
  - name: customer
    source: {FQ_SCHEMA}.dim_customer
    on: source.customer_key = customer.customer_key

dimensions:
  - name: return_date
    expr: date.calendar_date
    display_name: "Return Date"
    synonyms: ["date returned"]
  - name: year
    expr: date.year
    display_name: "Year"
    synonyms: ["calendar year"]
  - name: quarter
    expr: date.quarter
    display_name: "Quarter"
    synonyms: ["fiscal quarter"]
  - name: product_category
    expr: product.category
    display_name: "Product Category"
    synonyms: ["category"]
  - name: return_reason
    expr: source.return_reason
    display_name: "Return Reason"
    synonyms: ["reason", "reason code", "why returned"]
  - name: customer_segment
    expr: customer.segment
    display_name: "Customer Segment"
    synonyms: ["segment", "customer type"]

measures:
  - name: return_count
    expr: COUNT(DISTINCT source.return_id)
    display_name: "Return Count"
    comment: "Count of distinct return lines"
    synonyms: ["number of returns", "returns"]
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
  - name: units_returned
    expr: SUM(source.quantity)
    display_name: "Units Returned"
    comment: "Sum of units returned across all return lines"
    synonyms: ["quantity returned", "return volume"]
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
  - name: return_amount
    expr: SUM(source.return_amount)
    display_name: "Return Amount"
    comment: "Sum of refunded amount across all return lines"
    synonyms: ["refund amount", "amount refunded", "returns value"]
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 2
$$
""")

print(f"Created {FQ_SCHEMA}.mv_customer_returns")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.3 `mv_inventory_health` (optional third metric view)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {FQ_SCHEMA}.mv_inventory_health
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1

source: {FQ_SCHEMA}.fact_inventory

joins:
  - name: date
    source: {FQ_SCHEMA}.dim_date
    on: source.snapshot_date_key = date.date_key
  - name: product
    source: {FQ_SCHEMA}.dim_product
    on: source.product_key = product.product_key
  - name: store
    source: {FQ_SCHEMA}.dim_store
    on: source.store_key = store.store_key

dimensions:
  - name: snapshot_date
    expr: date.calendar_date
    display_name: "Snapshot Date"
    synonyms: ["inventory date", "as-of date"]
  - name: month_name
    expr: date.month_name
    display_name: "Month"
    synonyms: ["calendar month"]
  - name: product_category
    expr: product.category
    display_name: "Product Category"
    synonyms: ["category"]
  - name: store_region
    expr: store.region
    display_name: "Store Region"
    synonyms: ["region"]

measures:
  - name: avg_stock_on_hand
    expr: AVG(source.stock_on_hand)
    display_name: "Average Stock on Hand"
    comment: "Average units on hand across snapshots in scope"
    synonyms: ["avg inventory", "average stock level", "on-hand inventory"]
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
  - name: total_units_received
    expr: SUM(source.stock_received)
    display_name: "Total Units Received"
    comment: "Sum of units received into stock across snapshots in scope"
    synonyms: ["units received", "replenishment volume"]
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
  - name: low_stock_snapshot_count
    expr: SUM(CASE WHEN source.stock_on_hand < 50 THEN 1 ELSE 0 END)
    display_name: "Low Stock Snapshot Count"
    comment: "Count of product/store/month snapshots where stock on hand fell below 50 units"
    synonyms: ["low stock count", "near stockout count"]
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
$$
""")

print(f"Created {FQ_SCHEMA}.mv_inventory_health")
print("\nDone. Validate all three in Catalog Explorer, then continue to step 3 (Genie Agent, manual).")
