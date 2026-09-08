# Databricks notebook source
# MAGIC %md
# MAGIC # 05 - Pages content (manual, reference only)
# MAGIC
# MAGIC This notebook creates nothing - Pages are authored in Catalog Explorer ->
# MAGIC Discover -> Pages. Copy each block below into a new Page. Fields below match
# MAGIC the actual Page creation form in the UI exactly:
# MAGIC Domain (single-select) / Name / Owner / Synonyms / Description / Body
# MAGIC (Definition + Business use) / Related assets / Sources (optional).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 1: Total Revenue
# MAGIC
# MAGIC | Field | Value |
# MAGIC |---|---|
# MAGIC | Domain | Finance |
# MAGIC | Name | Total Revenue |
# MAGIC | Owner | you (databeli13@gmail.com) |
# MAGIC | Synonyms | revenue, sales, gross sales, GMV |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Sum of gross revenue (quantity x unit price) across all order lines, with no
# MAGIC adjustment for returns or discounts.
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definition
# MAGIC Total Revenue is the sum of gross revenue (quantity x unit price) across all
# MAGIC order lines in fact_sales, with no adjustment for returns or discounts.
# MAGIC
# MAGIC Formula: SUM(fact_sales.revenue)
# MAGIC
# MAGIC Business use
# MAGIC Use the total_revenue measure in @mv_sales_performance rather than querying
# MAGIC @fact_sales directly - it carries the certified definition and pre-built
# MAGIC dimension joins (date, product, customer, store).
# MAGIC
# MAGIC See also: @Customer Return Rate for how returns relate to this figure.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `mv_sales_performance`, `fact_sales`, `Retail Analytics Genie`
# MAGIC
# MAGIC **Sources (optional):** none - content authored directly in this Page.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 2: Customer Return Rate
# MAGIC
# MAGIC | Field | Value |
# MAGIC |---|---|
# MAGIC | Domain | Customer |
# MAGIC | Name | Customer Return Rate |
# MAGIC | Owner | you (databeli13@gmail.com) |
# MAGIC | Synonyms | return rate, returns ratio |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Share of revenue that is later refunded: total return amount divided by total
# MAGIC revenue for the same period and dimension slice.
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definition
# MAGIC Customer Return Rate measures what share of revenue is later refunded.
# MAGIC
# MAGIC Formula: SUM(fact_returns.return_amount) / SUM(fact_sales.revenue)
# MAGIC for the same time period and dimension slice.
# MAGIC
# MAGIC This is a cross-fact metric, so it is not a single stored measure - combine
# MAGIC the return_amount measure from @mv_customer_returns with the total_revenue
# MAGIC measure from @mv_sales_performance for the period you're comparing.
# MAGIC
# MAGIC Business use
# MAGIC Use this Page as the authoritative formula whenever someone asks about return
# MAGIC rate - Genie cannot derive the cross-fact ratio on its own from either metric
# MAGIC view alone.
# MAGIC
# MAGIC See also: @Total Revenue.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `mv_customer_returns`, `mv_sales_performance`, `fact_returns`, `Retail Analytics Genie`
# MAGIC
# MAGIC **Sources (optional):** none - content authored directly in this Page.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 3: Retail Analytics Genie Agent
# MAGIC
# MAGIC | Field | Value |
# MAGIC |---|---|
# MAGIC | Domain | Sales |
# MAGIC | Name | Retail Analytics Genie Agent |
# MAGIC | Owner | you (databeli13@gmail.com) |
# MAGIC | Synonyms | retail genie, sales genie, retail analytics assistant |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Onboarding page for the Retail Analytics Genie Agent - what it answers and
# MAGIC which certified metric views it draws from.
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definition
# MAGIC @Retail Analytics Genie is the Genie Agent for Northwind Retail sales,
# MAGIC returns, and inventory questions. It answers from three certified metric
# MAGIC views: @mv_sales_performance, @mv_customer_returns, and @mv_inventory_health.
# MAGIC
# MAGIC Business use
# MAGIC Ask things like:
# MAGIC - "What was total revenue last quarter by product category?"
# MAGIC - "What's our customer return rate this year vs last year?"
# MAGIC - "Which region has the highest revenue but also high returns?"
# MAGIC - "Which products have the lowest average stock on hand?"
# MAGIC
# MAGIC For metric definitions, see @Total Revenue and @Customer Return Rate.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `Retail Analytics Genie`, `mv_sales_performance`, `mv_customer_returns`, `mv_inventory_health`
# MAGIC
# MAGIC **Sources (optional):** none - content authored directly in this Page.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Notes
# MAGIC - The Page's **Domain** field is single-select in the UI (unlike table/view
# MAGIC   domain tagging, which allows more than one) - each Page above lists exactly
# MAGIC   one domain; pick the domain that best matches where someone would browse to
# MAGIC   find that definition.
# MAGIC - **Description** is the short one-line summary shown in Page listings/search;
# MAGIC   **Body** is the full rich-text content, structured here with a "Definition"
# MAGIC   and "Business use" heading each - reproduce that structure with the editor's
# MAGIC   heading/paragraph formatting.
# MAGIC - Use the editor's `@` mention to link each related asset and cross-link the
# MAGIC   other two Pages - that's what makes them show up as "related assets" and
# MAGIC   lets Genie One traverse between them.
# MAGIC - Publish all three (draft Pages are lower priority in Genie's ranking than
# MAGIC   published ones).
