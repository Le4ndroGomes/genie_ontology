# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Ingestão (Lakeflow Connect) e medalhão (pipeline SDP)
# MAGIC
# MAGIC No repo original este notebook gera os dados. Aqui eles vêm de um **banco relacional de verdade**, o Azure SQL
# MAGIC `rede_americas_ontologia` (22 tabelas, 33 FKs, change tracking ligado). Ele simula quatro sistemas de origem:
# MAGIC cadastro, hospitalar (assistencial), faturamento e central de atendimento (relacionamento).
# MAGIC
# MAGIC O caminho é **Lakeflow Connect** (bronze) → **pipeline SDP** (prata com PK/FK + ouro). Os passos de UI estão
# MAGIC abaixo; as células deste notebook criam os schemas e conferem cada etapa.
# MAGIC
# MAGIC ## Passo A — Conexão (UI)
# MAGIC Crie em **Catalog → External data → Connections → Create
# MAGIC connection → SQL Server**:
# MAGIC - host `<seu-servidor>.database.windows.net`, porta `1433`, usuário `dbx_ingest`;
# MAGIC - senha: a definida em `azure_sql/00_login_master.sql` (crie a origem antes; passo 0 do `ROTEIRO.md`).
# MAGIC
# MAGIC ## Passo B — Gateway e pipeline de ingestão (UI)
# MAGIC 1. Rode a célula **B.1** abaixo (cria os schemas).
# MAGIC 2. **Data Ingestion → SQL Server** → escolha a conexão → **Next**.
# MAGIC 3. *Ingestion setup*:
# MAGIC    - pipeline `ont_ingestao`, event log em `ontologia_staging`;
# MAGIC    - gateway `ont_gateway`, staging em `ontologia_staging`.
# MAGIC 4. *Source*: banco `rede_americas_ontologia`, schemas `cadastro`, `assistencial`, `faturamento` e
# MAGIC    `relacionamento` (22 tabelas). Não marque `dbo`. Mantenha os nomes de destino e SCD tipo 1.
# MAGIC 5. *Destination*: `ontologia_bronze`. *Database setup*: **Validate** (deve passar). *Schedule*: pule →
# MAGIC    **Save and run pipeline**.
# MAGIC 6. Espere a carga (~10 min) e rode a célula **B.2**.
# MAGIC
# MAGIC ## Passo B' — Workspace só serverless: Integrated CDC (sem gateway)
# MAGIC O gateway do Passo B roda em compute clássico. Num workspace só serverless, a criação de cluster falha com
# MAGIC "Only serverless compute is supported in the workspace" e o assistente da UI não funciona. A alternativa é o
# MAGIC **Integrated CDC** ([doc](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-integrated-pipeline)):
# MAGIC um único pipeline serverless (`connector_type: "CDC"`) que referencia a conexão do Unity Catalog. A extração
# MAGIC acontece dentro de cada update, sem gateway sempre ligado.
# MAGIC
# MAGIC | Requisito | Como resolver |
# MAGIC |---|---|
# MAGIC | Recurso habilitado no workspace | Peça ao account team. Teste: se a célula B'.1 criar o pipeline, está habilitado |
# MAGIC | Criação só por API, CLI, notebook ou bundle | A UI ainda não cria Integrated CDC. Use a célula **B'.1** |
# MAGIC | Rede: o serverless precisa alcançar o banco | Libere no firewall do SQL o **IP de saída do serverless** do workspace (rode `urllib.request.urlopen("https://api.ipify.org")` num notebook serverless). O IP pode mudar: se a conexão falhar, confira de novo |
# MAGIC | Catálogo de destino **sem Default Storage** | Catálogos com Default Storage são recusados ("Default Storage for Unity Catalog is not supported on LakeFlow Connect pipelines"). Crie um catálogo com `MANAGED LOCATION` numa external location, por exemplo `CREATE CATALOG rede_americas MANAGED LOCATION 's3://<bucket-da-external-location>/rede_americas'`, e use-o no widget `catalog_name` |
# MAGIC | Change tracking | Funciona com SCD tipo 1 (o padrão). SCD tipo 2 exige CDC do SQL Server |
# MAGIC
# MAGIC Roteiro: crie a conexão (Passo A) → rode **B.1** → mude o widget `criar_integrated_cdc` para `sim` e rode
# MAGIC **B'.1** → acompanhe o pipeline `ont_ingestao` em **Jobs & Pipelines** → rode **B.2**.
# MAGIC
# MAGIC ## Passo C — Pipeline do medalhão (UI), em duas fases
# MAGIC Importe a pasta `pipeline/` deste repo para o workspace. Crie em **Jobs & Pipelines → Create → ETL pipeline**:
# MAGIC - nome `ont_medalhao`; catálogo `rede_americas`; schema padrão `ontologia_prata`; compute serverless;
# MAGIC - **Configuration**: `catalogo` = `rede_americas`, `bronze` = `ontologia_bronze`,
# MAGIC   `prata` = `ontologia_prata`, `ouro` = `ontologia_ouro`.
# MAGIC
# MAGIC | Fase | Source code | Por quê |
# MAGIC |---|---|---|
# MAGIC | 1 | `pipeline/01_prata_so_pk.sql` + `pipeline/02_ouro.sql` → **Run** | Cria as 22 tabelas e registra as **PKs** |
# MAGIC | 2 | troque `01_prata_so_pk.sql` por `pipeline/01_prata.sql` → **Run** | Registra as **33 FKs**, agora que todas as PKs existem |
# MAGIC
# MAGIC As duas fases são necessárias porque o SDP grava as chaves de todas as tabelas em paralelo no fim da execução.
# MAGIC Se a FK chega antes da PK da tabela-pai, a execução falha com `UC_REFERENTIAL_CONSTRAINT_DOES_NOT_EXIST`.
# MAGIC Depois da fase 2, execuções normais e *full refresh* ficam estáveis (testado em 26/10/2026). Rode a célula
# MAGIC **C.1** depois de cada fase.
# MAGIC
# MAGIC O que a prata faz, tabela a tabela (o arquivo é gerado por `scripts/gerar_prata.py` a partir do catálogo da origem):
# MAGIC - tipos explícitos e `NOT NULL`;
# MAGIC - `COMMENT` de tabela e de coluna;
# MAGIC - **PRIMARY KEY** e **FOREIGN KEY** informativas, iguais às da origem;
# MAGIC - expectations de qualidade;
# MAGIC - integridade referencial: só entram linhas cujo pai está na prata.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC ### B.1 Schemas

# COMMAND ----------

for s, comentario in [(S_STAGING, "Staging e event log do Lakeflow Connect (ontologia)"),
                      (S_BRONZE, "Bronze: cópia fiel do Azure SQL rede_americas_ontologia (Lakeflow Connect)"),
                      (S_PRATA, "Prata: tabelas tipadas com PK/FK, comentários e regras de qualidade"),
                      (S_OURO, "Ouro: fatos e Metric Views do ciclo de receita")]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{s} COMMENT '{comentario}'")
    print("OK", f"{CATALOG}.{s}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### B.2 Conferência do bronze (contagens da origem)

# COMMAND ----------

ESPERADO = {
    "unidades": 4, "especialidades": 8, "medicos": 61, "operadoras": 5, "planos": 10, "pacientes": 4000,
    "beneficiarios": 4364, "procedimentos": 31, "precos_contratados": 186, "cids": 22, "autorizacoes": 2312,
    "atendimentos": 8528, "contas": 8443, "itens_conta": 34010, "motivos_glosa": 7, "glosas": 664,
    "recursos_glosa": 372, "pagamentos": 7502, "canais": 5, "assuntos": 8, "protocolos": 8848,
    "pesquisas_satisfacao": 2080,
}


def conferir(fq_schema):
    linhas = []
    for t, n in ESPERADO.items():
        try:
            real = spark.table(f"{fq_schema}.{t}").count()
        except Exception as e:  # tabela ainda não existe
            real = None
        status = "NÃO EXISTE (confira catalog_name)" if real is None else "OK" if real == n else "DIFERENTE"
        linhas.append((t, n, real, status))
    df = spark.createDataFrame(linhas, "tabela string, esperado long, encontrado long, status string")
    display(df)
    return all(r[3] == "OK" for r in linhas)


print("Bronze completo:", conferir(FQ_BRONZE))

# COMMAND ----------

# MAGIC %md
# MAGIC ### B'.1 (opcional) Integrated CDC por API — só para workspace só serverless
# MAGIC Cria o pipeline `ont_ingestao` (serverless, sem gateway) com os 4 schemas da origem e dispara a primeira
# MAGIC carga. Só roda com o widget `criar_integrated_cdc` = `sim`. Depois que terminar, volte e rode a **B.2**.

# COMMAND ----------

dbutils.widgets.dropdown("criar_integrated_cdc", "nao", ["nao", "sim"], "Criar Integrated CDC?")
dbutils.widgets.text("conexao", "rede_americas_ontologia", "Conexão do UC")
dbutils.widgets.text("banco_origem", "rede_americas_ontologia", "Banco na origem")

if dbutils.widgets.get("criar_integrated_cdc") != "sim":
    print("Pulado: mude o widget criar_integrated_cdc para 'sim' para criar o pipeline.")
else:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    banco = dbutils.widgets.get("banco_origem").strip()
    corpo = {
        "name": "ont_ingestao",
        "catalog": CATALOG,
        "schema": S_BRONZE,
        "serverless": True,
        "continuous": False,
        "ingestion_definition": {
            "connection_name": dbutils.widgets.get("conexao").strip(),
            "connector_type": "CDC",
            "objects": [{"schema": {"source_catalog": banco, "source_schema": s,
                                    "destination_catalog": CATALOG, "destination_schema": S_BRONZE}}
                        for s in ("cadastro", "assistencial", "faturamento", "relacionamento")],
            "data_staging_options": {"catalog_name": CATALOG, "schema_name": S_STAGING},
        },
    }
    pipeline_id = w.api_client.do("POST", "/api/2.0/pipelines", body=corpo)["pipeline_id"]
    update_id = w.api_client.do("POST", f"/api/2.0/pipelines/{pipeline_id}/updates",
                                body={"full_refresh": False})["update_id"]
    print(f"Pipeline {pipeline_id} criado; update {update_id} disparado.")
    print(f"Acompanhe em: {w.config.host}/pipelines/{pipeline_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### C.1 Conferência da prata (linhas, chaves e comentários)
# MAGIC Esperado: as mesmas contagens do bronze; **22 PKs** depois da fase 1 e **22 PKs + 33 FKs** depois da fase 2.

# COMMAND ----------

print("Prata completa:", conferir(FQ_PRATA))
display(spark.sql(f"""
  SELECT constraint_type, COUNT(*) AS n FROM {CATALOG}.information_schema.table_constraints
  WHERE table_schema = '{S_PRATA}' GROUP BY 1 ORDER BY 1"""))
display(spark.sql(f"""
  SELECT COUNT(*) AS colunas, COUNT(comment) AS com_comentario FROM {CATALOG}.information_schema.columns
  WHERE table_schema = '{S_PRATA}' AND table_name NOT LIKE '\\_\\_%' AND table_name NOT LIKE 'event_log%'"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### C.2 Ouro
# MAGIC Três fatos desnormalizados, base das Metric Views:
# MAGIC - `fato_itens_faturados`: grão item da conta (faturado, glosa, recurso, preço contratado vigente);
# MAGIC - `fato_autorizacoes`: grão guia (resposta, atendido mesmo negado, glosa 1801, reclamações);
# MAGIC - `fato_protocolos`: grão protocolo da central (plano vigente na data, CSAT, NPS).

# COMMAND ----------

display(spark.sql(f"""
  SELECT 'fato_itens_faturados' AS fato, COUNT(*) AS linhas FROM {FQ_OURO}.fato_itens_faturados UNION ALL
  SELECT 'fato_autorizacoes', COUNT(*) FROM {FQ_OURO}.fato_autorizacoes UNION ALL
  SELECT 'fato_protocolos', COUNT(*) FROM {FQ_OURO}.fato_protocolos"""))
# esperado: 34.010 · 2.312 · 8.848
