# Databricks notebook source
# MAGIC %md
# MAGIC # 00 - Shared config
# MAGIC
# MAGIC Every other notebook in this folder starts with `%run ./00_config` to pick up
# MAGIC the catalog/schema names below. Change the widget defaults once here (or
# MAGIC override them at run time in the widget bar) and every notebook stays in sync.
# MAGIC
# MAGIC Part of the **Genie One + Genie Ontology demo**. See `agents.md` at the repo
# MAGIC root for the full plan.

# COMMAND ----------

dbutils.widgets.text("catalog_name", "genie_ontology_demo", "Catalog name")
dbutils.widgets.text("schema_name", "retail_demo", "Schema name")

CATALOG = dbutils.widgets.get("catalog_name")
SCHEMA = dbutils.widgets.get("schema_name")
FQ_SCHEMA = f"{CATALOG}.{SCHEMA}"

print(f"CATALOG    = {CATALOG}")
print(f"SCHEMA     = {SCHEMA}")
print(f"FQ_SCHEMA  = {FQ_SCHEMA}")
