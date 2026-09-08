# Databricks notebook source
# MAGIC %md
# MAGIC # 06 - Cleanup: delete SQL-layer demo assets
# MAGIC
# MAGIC Drops the demo catalog (cascades to schema, all tables, and all metric views),
# MAGIC so you can re-run `01_create_catalog_schema_tables` and `02_create_metric_views`
# MAGIC from a clean slate.
# MAGIC
# MAGIC **This does NOT delete the things you created by hand in the UI** - there is no
# MAGIC confirmed public API for these object types, so remove them manually if you
# MAGIC want a fully clean slate before the next demo run:
# MAGIC - The **Genie Agent** (`Retail Analytics Genie`)
# MAGIC - The **4 Domains** (Catalog Explorer -> Discover -> Domains) - or leave them,
# MAGIC   since they're just governed tags and can be reused next run
# MAGIC - The **3 Pages** (Catalog Explorer -> Discover -> Pages)
# MAGIC
# MAGIC ## Safety check
# MAGIC This is destructive. Type `DELETE` in the `confirm` widget before running the
# MAGIC cell below - anything else aborts.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

dbutils.widgets.text("confirm", "", "Type DELETE to confirm")
confirm = dbutils.widgets.get("confirm")

if confirm != "DELETE":
    print(f"Aborted: confirm widget was '{confirm}', expected 'DELETE'. Nothing was deleted.")
else:
    spark.sql(f"DROP CATALOG IF EXISTS {CATALOG} CASCADE")
    print(f"Dropped catalog {CATALOG} (schema, tables, and metric views removed).")
    print("Reminder: Genie Agent, Domains, and Pages still need manual cleanup if desired.")
