# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - Certify + domain-tag all remaining tables and metric views
# MAGIC
# MAGIC This notebook applies two things to every table and metric view via SQL, so
# MAGIC you don't have to click through all of them by hand:
# MAGIC - `system.certification_status = certified`
# MAGIC - the domain governed tag for each domain the asset belongs to
# MAGIC
# MAGIC It's idempotent: re-running it just re-sets the same tags.
# MAGIC
# MAGIC ## How domain tagging actually works here
# MAGIC
# MAGIC Confirmed empirically against a live workspace (2026-08-19): when you create a
# MAGIC domain in Catalog Explorer -> Discover -> Domains named e.g. `Sales`, it maps to
# MAGIC a governed tag whose **key is that exact domain name and whose value is empty**
# MAGIC (a key-only tag) - not `domain_sales = true` or any other made-up key. Querying
# MAGIC `<catalog>.information_schema.table_tags` after manually assigning an asset to a
# MAGIC domain in the UI showed rows like `tag_name='Sales', tag_value=''`. Since any
# MAGIC user with tagging permission can set a tag by name (it doesn't have to be
# MAGIC created through the Domains UI first), this notebook applies the domain tag
# MAGIC directly via `SET TAG ON TABLE/VIEW ... `<domain name>`` using the literal
# MAGIC domain names below - no manual "open each domain and copy its tag key" step
# MAGIC needed, as long as you created the 4 domains with these exact names.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# Must exactly match the 4 domain names you created in Catalog Explorer -> Discover
# -> Domains. The domain governed tag's key IS this name (key-only, no value).
DOMAIN_NAMES = ["Sales", "Customer", "Supply Chain", "Finance"]

# Which domain(s) each table / metric view belongs to. Assets can list more than one.
ASSET_DOMAINS = {
    "dim_product":            ["Sales"],
    "dim_store":               ["Sales", "Supply Chain"],
    "dim_customer":            ["Customer"],
    "dim_date":                [],  # shared conformed dimension, no single domain
    "fact_sales":               ["Sales", "Finance"],
    "fact_returns":              ["Customer"],
    "fact_inventory":            ["Supply Chain"],
    "mv_sales_performance":      ["Sales", "Finance"],
    "mv_customer_returns":       ["Customer"],
    "mv_inventory_health":       ["Supply Chain"],
}

METRIC_VIEWS = {"mv_sales_performance", "mv_customer_returns", "mv_inventory_health"}

# COMMAND ----------

def object_kind(asset_name: str) -> str:
    return "VIEW" if asset_name in METRIC_VIEWS else "TABLE"


def run(stmt: str):
    try:
        spark.sql(stmt)
        print(f"OK    {stmt}")
    except Exception as e:
        print(f"ERROR {stmt} -> {e}")


def set_tags(asset_name: str, domains: list):
    kind = object_kind(asset_name)
    fq_asset = f"{FQ_SCHEMA}.{asset_name}"

    # Certification (unchanged, key=value tag) - already known to work.
    run(f"ALTER {kind} {fq_asset} SET TAGS ('system.certification_status' = 'certified')")

    # Domain governed tags: key-only, key == domain name exactly.
    for domain in DOMAIN_NAMES:
        stmt = f"{'SET' if domain in domains else 'UNSET'} TAG ON {kind} {fq_asset} `{domain}`"
        run(stmt)


for asset_name, domains in ASSET_DOMAINS.items():
    set_tags(asset_name, domains)

print("\nDone. Verify tags in Catalog Explorer: each asset should show the")
print("'certified' badge and appear under its domain(s) on the Discover page.")
print("Remember: the Genie Agent itself still needs certification + domain")
print("assignment done manually in the UI (no SQL target for it).")
