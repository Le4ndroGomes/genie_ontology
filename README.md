# Genie Ontology - Making Genie One Answers more Reliable

> **Fork com um segundo caso:** [`rede_americas/`](rede_americas/) aplica a mesma estrutura (notebooks 00–06) a um
> caso de ciclo de receita hospitalar (Rede Américas, dados sintéticos). A origem é um banco relacional (Azure SQL),
> ingerido com Lakeflow Connect e tratado num medalhão SDP com PK/FK. Veja `rede_americas/README.md` e
> `rede_americas/ROTEIRO.md`.

A working demo of Databricks **Genie One** backed by a hand-modeled **Genie
Ontology** (Unity Catalog semantics: metric views, domains, pages, certification)
on top of a small star-schema retail dataset.

The notebooks build a self-contained "Northwind Retail" sales & customer
analytics use case, then walk you through pointing Genie One at it so you can
see, question by question, how certified metric views, domains, and pages
change the quality and traceability of Genie's answers.

## How the pieces fit

- **Genie One** is Databricks' full-screen natural-language chat. On a
  question it searches, in order: (1) existing **Genie Agents**, then (2)
  dashboards/queries/metric views — answering using the **Genie Ontology**:
  - *Modeled context* — metric views, domains, pages — curated and certified
    by humans (what this demo builds).
  - *Inferred context* — metadata, usage, freshness — pulled automatically
    from existing assets.
  - Every answer snippet gets an authority score (source, usage, freshness),
    and responses are permission-gated to what the asking user can see.
- **Metric views** define measures once (revenue, order count, …), separate
  from dimensions, and are queried like tables from SQL, notebooks,
  dashboards, and Genie.
- **Domains** are a browsing layer backed by a governed tag — assets get
  tagged into a domain so they show up on the Discover page grouped by
  business purpose.
- **Pages** are governed definitions of a business term/KPI/concept, with
  related-asset links and a rich-text body. Genie One reads published pages
  as authoritative context, ahead of inferred context.
- **Certification** (`certified` / `deprecated`) applies to catalogs, schemas,
  tables, views, volumes, functions, models, dashboards, Genie Agents, apps,
  and notebooks. Certified assets rank higher in Genie One's answers.

Reference docs: [Genie One chat](https://docs.databricks.com/aws/en/genie-one/chat) ·
[UC semantics overview](https://docs.databricks.com/aws/en/uc-semantics/) ·
[Metric views](https://docs.databricks.com/aws/en/uc-semantics/metric-views/) ·
[Domains](https://docs.databricks.com/aws/en/uc-semantics/domains) ·
[Pages](https://docs.databricks.com/aws/en/uc-semantics/pages) ·
[Certify/deprecate](https://docs.databricks.com/aws/en/data-governance/unity-catalog/certify-deprecate-data)

## Prerequisites

- A Databricks workspace with Unity Catalog enabled and a SQL warehouse
  (serverless is fine).
- Permission to create a catalog/schema, create metric views, and use Genie
  One / Genie Agents in that workspace.
- No local setup required — everything runs as Databricks notebooks inside
  the workspace. You just need to import this folder as a Workspace/Repo
  folder and open the notebooks from there.

## Repo contents

| File | What it does | How you run it |
|---|---|---|
| [`00_config.py`](00_config.py) | Widgets for catalog/schema name, shared by every other notebook via `%run` | Not run directly |
| [`01_create_catalog_schema_tables.py`](01_create_catalog_schema_tables.py) | Creates the catalog, schema, and 7 tables (with comments + PK/FK constraints); generates and loads a rolling ~2 years of synthetic data | **Run in Databricks** |
| [`02_create_metric_views.py`](02_create_metric_views.py) | Creates 3 metric views with full semantic metadata (display names, synonyms, formats) | **Run in Databricks** |
| [`03_genie_agent_setup.py`](03_genie_agent_setup.py) | Reference only — name/description/instructions/sample questions to paste into the Genie One "Create Agent" UI | Read, don't run |
| [`04_apply_certification_and_domains.py`](04_apply_certification_and_domains.py) | Certifies and domain-tags every table and metric view via SQL `SET TAG`/`SET TAGS` | **Run in Databricks** |
| [`05_pages_content.py`](05_pages_content.py) | Reference only — content for all 3 Pages (Name/Owner/Domain/Synonyms/Description/Body/Related assets/Sources), matching the Page creation UI form fields exactly | Read, don't run |
| [`06_cleanup_delete_all_assets.py`](06_cleanup_delete_all_assets.py) | Drops the demo catalog (schema + tables + metric views) so you can rebuild from scratch; requires typing `DELETE` in a widget as a confirmation guard | **Run in Databricks** |

Both notebook widgets default to catalog `genie_ontology_demo` / schema
`retail_demo` — override them in the widget bar if you want different names.

## Business use case & data model

**"Northwind Retail" sales & customer analytics** — a small, self-contained
star schema so the resulting Genie answers are easy to sanity-check by eye.

Tables (`<catalog>.retail_demo`):

| Table | Type | Key columns |
|---|---|---|
| `dim_date` | dimension | date_key, calendar_date, year, quarter, month, month_name, day_of_week, is_weekend |
| `dim_product` | dimension | product_key, sku, product_name, category, brand, unit_cost |
| `dim_customer` | dimension | customer_key, customer_name, segment, region, signup_date |
| `dim_store` | dimension | store_key, store_name, region, channel (Online/In-Store) |
| `fact_sales` | fact | order_id, date_key, product_key, customer_key, store_key, quantity, unit_price, revenue |
| `fact_returns` | fact | return_id, order_id, date_key, product_key, customer_key, quantity, return_amount, return_reason |
| `fact_inventory` | fact | snapshot_date_key, product_key, store_key, stock_on_hand, stock_received |

Every table and column has a `COMMENT`; PK constraints on every table, and FK
constraints on every fact→dimension relationship (plus
`fact_returns.order_id → fact_sales.order_id`). The date range is computed at
run time (rolling ~2 years ending today), so re-running
`01_create_catalog_schema_tables.py` periodically keeps the data fresh.

### Metric views

1. **`mv_sales_performance`** — `fact_sales` joined to `dim_date`,
   `dim_product`, `dim_customer`, `dim_store`.
   Measures: `total_revenue`, `total_units_sold`, `order_count`,
   `avg_order_value`. Dimensions: order date/year/quarter/month,
   product category/brand, customer segment/region, store region/channel.
2. **`mv_customer_returns`** — `fact_returns` joined to `dim_date`,
   `dim_product`, `dim_customer`.
   Measures: `return_count`, `units_returned`, `return_amount`. Dimensions:
   return date/year/quarter, product category, return reason, customer segment.
3. **`mv_inventory_health`** — `fact_inventory` joined to `dim_date`,
   `dim_product`, `dim_store`.
   Measures: `avg_stock_on_hand`, `total_units_received`,
   `low_stock_snapshot_count`. Dimensions: snapshot date/month, product
   category, store region.

> **Return rate is deliberately not a stored measure.** It needs
> `fact_returns` and `fact_sales` together, and a metric view's measures can
> only aggregate its own source + joined dimensions. Genie answers "what's our
> return rate" by combining `mv_customer_returns.return_amount` with
> `mv_sales_performance.total_revenue` — the formula is documented explicitly
> in the "Customer Return Rate" Page so Genie has an authoritative source to
> cite instead of guessing.

### Genie Agent

**`Retail Analytics Genie`** — one agent given all three metric views as its
data sources, plus custom instructions and sample questions. Exact
name/description/instructions text to paste in is in
[`03_genie_agent_setup.py`](03_genie_agent_setup.py).

### Domains (4, no subdomains)

| Domain | Assigned to |
|---|---|
| `Sales` | `dim_product`, `dim_store`, `fact_sales`, `mv_sales_performance`, `Retail Analytics Genie` |
| `Customer` | `dim_customer`, `fact_returns`, `mv_customer_returns` |
| `Supply Chain` | `dim_store`, `fact_inventory`, `mv_inventory_health` |
| `Finance` | `fact_sales`, `mv_sales_performance` |

Assets can belong to more than one domain (e.g. `dim_store` is both `Sales`
and `Supply Chain`). The domain governed tag is a **key-only tag whose key is
the exact domain name** — create the 4 domains in the UI with these exact
names and `04_apply_certification_and_domains.py` will tag everything
automatically, no manual tag-key lookup needed.

### Pages (3)

Full content for all three, matching the Page creation form fields exactly,
is in [`05_pages_content.py`](05_pages_content.py):

1. **"Total Revenue"** (domain: Finance) — `SUM(fact_sales.revenue)`, links
   to `mv_sales_performance`.
2. **"Customer Return Rate"** (domain: Customer) — cross-metric-view formula,
   links to both metric views.
3. **"Retail Analytics Genie Agent"** (domain: Sales) — onboarding page: what
   it answers, sample questions, links to all 3 metric views and the agent.

### Certification

Every table, every metric view, and the Genie Agent get
`certification_status = certified`. Tables/views are certified via SQL
`SET TAGS` in `04_apply_certification_and_domains.py`; the Genie Agent is
certified by hand (UI kebab menu → **Assign certification** — no SQL target
exists for that object type).

## Build order

1. **Import this folder** into a Databricks Workspace or Repo folder.
2. **Run `01_create_catalog_schema_tables.py`.**
3. **Run `02_create_metric_views.py`.**
4. **Create the Genie Agent** in the UI using the text in
   `03_genie_agent_setup.py`; attach the 3 metric views.
5. **Create the 4 Domains** manually in the UI (Catalog Explorer → Discover →
   Domains), named exactly `Sales`, `Customer`, `Supply Chain`, `Finance`.
6. **Certify + domain-tag the Genie Agent by hand** in the UI, then **run
   `04_apply_certification_and_domains.py`** to cover every table and metric
   view.
7. **Create the 3 Pages** manually (Catalog Explorer → Discover → Pages)
   using the content in `05_pages_content.py`.
8. **Open Genie One** and run the demo script below.
9. To reset and rebuild, **run `06_cleanup_delete_all_assets.py`** (drops the
   SQL-layer assets only — the Genie Agent, Domains, and Pages need manual
   deletion for a fully clean slate).

### What's scriptable vs. UI-only

Anything expressible as SQL DDL is scriptable; anything that only exists as a
Catalog Explorer / Discover / Genie One UI flow (no confirmed public REST
endpoint as of this writing) is manual:

| Item | Automatable? |
|---|---|
| Catalog, schema, tables, constraints, synthetic data | Yes — `01_create_catalog_schema_tables.py` |
| Metric views + semantic metadata | Yes — `02_create_metric_views.py` |
| Certification + domain tags (tables + metric views) | Yes — `04_apply_certification_and_domains.py` |
| Domain object itself (create/publish to Discover) | No — manual, Catalog Explorer UI |
| Genie Agent creation + attaching data sources | No — manual, Genie One UI |
| Genie Agent certification + domain tag | No — manual, no SQL target for this object type |
| Pages (create + body content) | No — manual, no confirmed public API |
| Deleting SQL-layer assets | Yes — `06_cleanup_delete_all_assets.py` |
| Deleting Genie Agent / Domains / Pages | No — manual |

## Demo script

Once everything is built, ask Genie One questions that force it to pull from
different ontology layers, and check the "sources used" panel on each
response:

- *"What was total revenue last quarter by product category?"* → should route
  to `Retail Analytics Genie` / `mv_sales_performance`, citing the certified
  badge.
- *"What's our customer return rate this year vs last?"* → should combine
  `mv_customer_returns` and `mv_sales_performance`, and ideally surface the
  "Customer Return Rate" Page for the formula.
- *"What does 'total revenue' mean here?"* → should surface the **Page**, not
  just the metric view.
- *"Which region has the highest revenue but also high returns?"* → forces a
  join across both metric views, a good test of cross-domain reasoning.
- Ask one question *before* certifying/tagging domains and the same question
  *after*, to see the authority-score / ranking difference in the response
  sources.

## Notes

- Metric-view YAML syntax has evolved across Databricks releases (this demo
  targets metric view spec `1.1`). If `CREATE VIEW ... WITH METRICS` fails on
  a `format:` block, drop those lines, re-run, and add formatting back later
  from the metric view's YAML editor in Catalog Explorer (it has live
  validation).
- Make sure the SQL warehouse has `CAN USE` permission granted to whichever
  user/group will use Genie One chat against this data.
