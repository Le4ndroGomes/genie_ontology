# Databricks notebook source
# MAGIC %md
# MAGIC # 00 - Configuração compartilhada
# MAGIC
# MAGIC Os outros notebooks começam com `%run ./00_config` para ler os nomes abaixo. Mude os defaults aqui (ou
# MAGIC sobrescreva na barra de widgets) e todos ficam em sincronia.
# MAGIC
# MAGIC Parte da demo **Genie Ontology — faturamento hospitalar e glosas** (Rede Américas), adaptada de
# MAGIC [databeli/genie_ontology](https://github.com/databeli/genie_ontology). Dados 100% sintéticos.
# MAGIC
# MAGIC | Schema | Conteúdo | Quem cria |
# MAGIC |---|---|---|
# MAGIC | `ontologia_staging` | Volume de staging e event log da ingestão | Lakeflow Connect |
# MAGIC | `ontologia_bronze` | Cópia fiel das 22 tabelas do Azure SQL | Lakeflow Connect |
# MAGIC | `ontologia_prata` | 22 materialized views tipadas, com PK/FK, comentários e qualidade | Pipeline `ont_medalhao` |
# MAGIC | `ontologia_ouro` | 1 fato (`fato_itens_faturados`) + 3 Metric Views (`mv_faturamento`, `mv_glosas`, `mv_recuperacao`) | Pipeline `ont_medalhao` + `02_create_metric_views` |

# COMMAND ----------

dbutils.widgets.text("catalog_name", "rede_americas", "Catálogo")
dbutils.widgets.text("prefixo_schema", "ontologia", "Prefixo dos schemas")

CATALOG = dbutils.widgets.get("catalog_name").strip()
PREFIXO = dbutils.widgets.get("prefixo_schema").strip()
S_STAGING, S_BRONZE, S_PRATA, S_OURO = (f"{PREFIXO}_{c}" for c in ("staging", "bronze", "prata", "ouro"))
FQ_BRONZE, FQ_PRATA, FQ_OURO = (f"{CATALOG}.{s}" for s in (S_BRONZE, S_PRATA, S_OURO))

print(f"CATALOG = {CATALOG}")
print(f"BRONZE  = {FQ_BRONZE}\nPRATA   = {FQ_PRATA}\nOURO    = {FQ_OURO}")
