# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - Certificação e domínios das tabelas e Metric Views
# MAGIC
# MAGIC Aplica via SQL, em todas as tabelas da prata, nos fatos do ouro e nas Metric Views:
# MAGIC - `system.certification_status = certified`;
# MAGIC - o governed tag de cada domínio a que o ativo pertence.
# MAGIC
# MAGIC É idempotente: rodar de novo só reaplica os mesmos tags.
# MAGIC
# MAGIC Como no repo original, o domínio criado em **Discover → Create domain** vira um tag sem valor cuja chave é o
# MAGIC nome exato do domínio. **Crie os 4 domínios na UI antes, com estes nomes exatos** (acentos incluídos).
# MAGIC
# MAGIC Testado em 26/10/2026:
# MAGIC - `SET TAGS` e `SET TAG ON TABLE` funcionam nas materialized views do pipeline SDP;
# MAGIC - `SET TAG ON VIEW` funciona nas Metric Views;
# MAGIC - os tags continuam depois de um refresh do pipeline.
# MAGIC
# MAGIC Não certificamos o bronze: ele é a cópia fiel da origem, não a camada de consumo.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

DOMAIN_NAMES = ["Faturamento e Glosa", "Autorização Prévia", "Central de Atendimento", "Cadastro e Assistencial"]

FAT, AUT, CEN, CAD = DOMAIN_NAMES
# Domínio(s) de cada ativo. Um ativo pode estar em mais de um domínio.
ASSET_DOMAINS = {
    # prata — cadastro
    (S_PRATA, "unidades"): [CAD], (S_PRATA, "especialidades"): [CAD], (S_PRATA, "medicos"): [CAD],
    (S_PRATA, "pacientes"): [CAD], (S_PRATA, "cids"): [CAD],
    (S_PRATA, "operadoras"): [CAD, FAT], (S_PRATA, "planos"): [CAD, FAT],
    (S_PRATA, "beneficiarios"): [CAD], (S_PRATA, "procedimentos"): [CAD, FAT, AUT],
    (S_PRATA, "precos_contratados"): [FAT],
    # prata — assistencial
    (S_PRATA, "atendimentos"): [CAD], (S_PRATA, "autorizacoes"): [AUT],
    # prata — faturamento
    (S_PRATA, "contas"): [FAT], (S_PRATA, "itens_conta"): [FAT], (S_PRATA, "motivos_glosa"): [FAT],
    (S_PRATA, "glosas"): [FAT], (S_PRATA, "recursos_glosa"): [FAT], (S_PRATA, "pagamentos"): [FAT],
    # prata — central
    (S_PRATA, "canais"): [CEN], (S_PRATA, "assuntos"): [CEN], (S_PRATA, "protocolos"): [CEN],
    (S_PRATA, "pesquisas_satisfacao"): [CEN],
    # ouro
    (S_OURO, "fato_itens_faturados"): [FAT], (S_OURO, "fato_autorizacoes"): [AUT, FAT],
    (S_OURO, "fato_protocolos"): [CEN],
    (S_OURO, "mv_faturamento_glosa"): [FAT], (S_OURO, "mv_autorizacoes"): [AUT, FAT],
    (S_OURO, "mv_central"): [CEN],
}
METRIC_VIEWS = {"mv_faturamento_glosa", "mv_autorizacoes", "mv_central"}

# COMMAND ----------


def run(stmt):
    try:
        spark.sql(stmt)
        print(f"OK    {stmt}")
    except Exception as e:
        print(f"ERRO  {stmt} -> {str(e)[:300]}")


for (schema, nome), domains in ASSET_DOMAINS.items():
    kind = "VIEW" if nome in METRIC_VIEWS else "TABLE"
    fq = f"{CATALOG}.{schema}.{nome}"
    run(f"ALTER {kind} {fq} SET TAGS ('system.certification_status' = 'certified')")
    for d in DOMAIN_NAMES:
        run(f"{'SET' if d in domains else 'UNSET'} TAG ON {kind} {fq} `{d}`")

# COMMAND ----------

display(spark.sql(f"""
  SELECT schema_name, table_name, concat_ws(', ', sort_array(collect_list(tag_name))) AS tags
  FROM {CATALOG}.information_schema.table_tags
  WHERE schema_name IN ('{S_PRATA}', '{S_OURO}') GROUP BY ALL ORDER BY 1, 2"""))

# COMMAND ----------

# MAGIC %md
# MAGIC O Genie Agent precisa de certificação e domínio feitos à mão na UI: não há alvo SQL para esse tipo de objeto.
