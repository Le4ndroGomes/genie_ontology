# Databricks notebook source
# MAGIC %md
# MAGIC # 06 - Limpeza: apagar os ativos SQL da demo
# MAGIC
# MAGIC Diferente do repo original, **não apaga o catálogo**: `rede_americas` é compartilhado com as outras demos
# MAGIC (pode ter outras demos). Apaga só os quatro schemas `ontologia_*`, com tabelas, materialized views e
# MAGIC Metric Views.
# MAGIC
# MAGIC **Antes**, apague na UI (**Jobs & Pipelines**) os pipelines `ont_medalhao` e `ont_ingestao` (e `ont_gateway`, no
# MAGIC caminho com gateway em compute clássico). Se recriar um pipeline sem limpar as tabelas, o SDP recusa com
# MAGIC "table is already managed by pipeline".
# MAGIC
# MAGIC **Não apaga** o que foi criado à mão:
# MAGIC - os 2 Genie spaces: "Faturamento e Glosas — Rede Américas" e "Faturamento — sem contexto (baseline)";
# MAGIC - os 3 domínios (podem ficar: são só governed tags);
# MAGIC - as 4 Pages;
# MAGIC - a conexão, se você criou uma nova.
# MAGIC
# MAGIC Na origem (Azure SQL), se quiser desfazer tudo:
# MAGIC - regra de firewall do IP de saída do workspace:
# MAGIC   `az sql server firewall-rule delete -g <seu-resource-group> -s <seu-servidor> -n <nome-da-regra>`;
# MAGIC - o banco: `az sql db delete -g <seu-resource-group> -s <seu-servidor> -n rede_americas_ontologia`.
# MAGIC
# MAGIC ## Trava de segurança
# MAGIC Destrutivo: digite `DELETE` no widget `confirm` antes de rodar a célula abaixo.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

dbutils.widgets.text("confirm", "", "Digite DELETE para confirmar")
confirm = dbutils.widgets.get("confirm")

if confirm != "DELETE":
    print(f"Cancelado: o widget confirm tem '{confirm}', esperado 'DELETE'. Nada foi apagado.")
else:
    for s in (S_OURO, S_PRATA, S_BRONZE, S_STAGING):
        spark.sql(f"DROP SCHEMA IF EXISTS {CATALOG}.{s} CASCADE")
        print("Apagado", f"{CATALOG}.{s}")
    print("Lembrete: Genie spaces, domínios e Pages continuam; apague na UI se quiser começar do zero.")
