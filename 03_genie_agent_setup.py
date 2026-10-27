# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Genie Agent (referência + criação opcional por API)
# MAGIC
# MAGIC Dois espaços Genie, para mostrar a diferença na demo:
# MAGIC
# MAGIC | Espaço | Dados | Contexto | Para quê |
# MAGIC |---|---|---|---|
# MAGIC | **Faturamento e Glosas — Rede Américas** | só as 3 Metric Views certificadas | instruções, perguntas e SQL de exemplo | a resposta governada |
# MAGIC | **Faturamento — sem contexto (baseline)** | 13 tabelas do **bronze** (cópia crua da origem) | nenhum | a resposta "antes" da ontologia |
# MAGIC
# MAGIC O caminho padrão é pela UI: **Genie One → Create Agent**, com os textos abaixo. A célula opcional no fim cria ou
# MAGIC atualiza os dois espaços pela API REST de Genie spaces (`/api/2.0/genie/spaces`). Ela é idempotente: procura cada
# MAGIC espaço pelo título antes de criar.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Agente governado
# MAGIC
# MAGIC ### Nome
# MAGIC ```
# MAGIC Faturamento e Glosas — Rede Américas
# MAGIC ```
# MAGIC
# MAGIC ### Descrição
# MAGIC ```
# MAGIC Faturamento hospitalar, glosas e recuperação em recurso da Rede Américas, a partir de três Metric Views certificadas
# MAGIC (mv_faturamento, mv_glosas, mv_recuperacao). Recortes por operadora, plano, unidade, médico, especialidade,
# MAGIC procedimento e período. Dados sintéticos, nov/2025 a out/2026.
# MAGIC ```
# MAGIC
# MAGIC ### Fontes de dados
# MAGIC Anexe **só** as três Metric Views de `ontologia_ouro`: `mv_faturamento`, `mv_glosas` e `mv_recuperacao`. Não anexe
# MAGIC tabelas: a demo mostra o Genie preferindo a camada governada a junções ad hoc.
# MAGIC
# MAGIC ### Instruções
# MAGIC ```
# MAGIC Você é o assistente de faturamento e glosas da Rede Américas (hospitais, centro oncológico e ambulatório).
# MAGIC Responda em português do Brasil.
# MAGIC
# MAGIC - Use sempre as Metric Views com MEASURE(): mv_faturamento (faturado, contas, ticket médio), mv_glosas (glosado,
# MAGIC   taxa de glosa, motivos) e mv_recuperacao (recuperado em recurso, taxa de recuperação). Não recalcule indicadores.
# MAGIC - Taxa de glosa = valor glosado ÷ valor faturado das contas JÁ ANALISADAS pela operadora (conta_analisada = true).
# MAGIC   Nunca divida pelo faturado total.
# MAGIC - Os últimos ~2 meses estão incompletos: parte das contas ainda não foi analisada. Diga isso explicitamente e nunca
# MAGIC   reporte que a glosa "caiu" nesses meses.
# MAGIC - Para explicar uma variação, compare o período com a média dos 3 meses anteriores e decomponha por motivo e
# MAGIC   categoria de glosa.
# MAGIC - Motivos principais: 1801 = procedimento sem autorização prévia; 1705 = valor acima do preço contratado;
# MAGIC   1909 = acomodação incompatível com o plano.
# MAGIC - Taxa de recuperação = valor recuperado em recurso ÷ valor glosado. Use para dizer onde vale a pena recorrer.
# MAGIC - Valores em reais (R$ 1.234.567,89) e taxas em percentual com uma casa decimal. Sem período na pergunta, use os
# MAGIC   últimos 12 meses e diga qual foi.
# MAGIC - Nunca mostre nome, CPF ou carteirinha de paciente.
# MAGIC ```
# MAGIC
# MAGIC ### Perguntas de exemplo
# MAGIC 1. Qual a taxa de glosa da rede nos últimos 12 meses?
# MAGIC 2. Como evoluiu a taxa de glosa mês a mês?
# MAGIC 3. Qual operadora tem a maior taxa de glosa e qual o principal motivo?
# MAGIC 4. Por que a glosa da Beta Assistência Médica subiu a partir de maio de 2026?
# MAGIC 5. Quais médicos geram glosa por preço acima do contratado e vale a pena recorrer?
# MAGIC
# MAGIC ### Consultas SQL de exemplo (*SQL queries* do agente)
# MAGIC As mesmas da célula de criação abaixo, com o catálogo e o schema do `00_config`:
# MAGIC - Q1: taxa de glosa da rede (`mv_glosas`).
# MAGIC - Q4: Beta antes × depois de mai/2026, por categoria (`mv_glosas`).
# MAGIC - Q5: glosa por preço por médico (`mv_glosas`); a taxa de recuperação da categoria PRECO vem de `mv_recuperacao`.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Baseline sem contexto
# MAGIC - **Nome:** `Faturamento — sem contexto (baseline)`
# MAGIC - **Dados:** do `ontologia_bronze`: `contas`, `itens_conta`, `glosas`, `recursos_glosa`, `operadoras`, `planos`,
# MAGIC   `beneficiarios`, `atendimentos`, `medicos`, `especialidades`, `unidades`, `procedimentos`, `motivos_glosa`.
# MAGIC - **Instruções, perguntas e SQL de exemplo:** nenhum.
# MAGIC
# MAGIC Na demo, faça as mesmas 5 perguntas nos dois espaços. O baseline tende a dividir a glosa pelo faturado total e a
# MAGIC mostrar "queda" nos meses ainda não analisados.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

import json

dbutils.widgets.dropdown("criar_genie", "nao", ["nao", "sim"], "Criar/atualizar espaços Genie")
dbutils.widgets.text("warehouse_id", "", "SQL warehouse (id)")

TITULO_AGENTE = "Faturamento e Glosas — Rede Américas"
TITULO_BASELINE = "Faturamento — sem contexto (baseline)"

ESPACOS = {
    TITULO_AGENTE: {
        "description": "Faturamento hospitalar, glosas e recuperação em recurso a partir de três Metric Views "
                       "certificadas. Dados sintéticos, nov/2025 a out/2026.",
        "metric_views": [f"{FQ_OURO}.{m}" for m in ("mv_faturamento", "mv_glosas", "mv_recuperacao")],
        "tables": [],
        "perguntas": [
            "Qual a taxa de glosa da rede nos últimos 12 meses?",
            "Como evoluiu a taxa de glosa mês a mês?",
            "Qual operadora tem a maior taxa de glosa e qual o principal motivo?",
            "Por que a glosa da Beta Assistência Médica subiu a partir de maio de 2026?",
            "Quais médicos geram glosa por preço acima do contratado e vale a pena recorrer?",
        ],
        "texto": [
            "Você é o assistente de faturamento e glosas da Rede Américas (hospitais, centro oncológico e ambulatório). "
            "Responda em português do Brasil.\n",
            "Use sempre as Metric Views com MEASURE(): mv_faturamento (faturado, contas, ticket médio), mv_glosas "
            "(glosado, taxa de glosa, motivos) e mv_recuperacao (recuperado em recurso, taxa de recuperação). "
            "Não recalcule indicadores.\n",
            "Taxa de glosa = valor glosado ÷ valor faturado das contas JÁ ANALISADAS pela operadora "
            "(conta_analisada = true). Nunca divida pelo faturado total.\n",
            "Os últimos ~2 meses estão incompletos: parte das contas ainda não foi analisada. Diga isso explicitamente "
            "e nunca reporte que a glosa caiu nesses meses.\n",
            "Para explicar uma variação, compare o período com a média dos 3 meses anteriores e decomponha por motivo "
            "e categoria de glosa.\n",
            "Motivos principais: 1801 = procedimento sem autorização prévia; 1705 = valor acima do preço contratado; "
            "1909 = acomodação incompatível com o plano.\n",
            "Taxa de recuperação = valor recuperado em recurso ÷ valor glosado. Use para dizer onde vale a pena "
            "recorrer.\n",
            "Valores em reais (R$ 1.234.567,89) e taxas em percentual com uma casa decimal. Sem período na pergunta, "
            "use os últimos 12 meses e diga qual foi.\n",
            "Nunca mostre nome, CPF ou carteirinha de paciente.",
        ],
        "exemplos": [
            ("Qual a taxa de glosa da rede nos últimos 12 meses?",
             f"SELECT MEASURE(valor_glosado) AS valor_glosado, MEASURE(valor_faturado_analisado) AS faturado_analisado, "
             f"MEASURE(taxa_glosa) AS taxa_glosa FROM {FQ_OURO}.mv_glosas"),
            ("Por que a glosa da Beta Assistência Médica subiu a partir de maio de 2026?",
             f"SELECT mes >= DATE'2026-05-01' AS a_partir_de_maio, categoria_glosa, MEASURE(valor_glosado) AS valor_glosado, "
             f"MEASURE(taxa_glosa) AS taxa_glosa FROM {FQ_OURO}.mv_glosas "
             f"WHERE operadora = 'Beta Assistência Médica' AND conta_analisada GROUP BY ALL ORDER BY a_partir_de_maio, valor_glosado DESC"),
            ("Quais médicos geram glosa por preço acima do contratado e vale a pena recorrer?",
             f"SELECT medico, especialidade, unidade, MEASURE(valor_glosado) AS glosa_preco, "
             f"MEASURE(sobrepreco) AS cobrado_acima FROM {FQ_OURO}.mv_glosas WHERE categoria_glosa = 'PRECO' "
             f"GROUP BY ALL ORDER BY glosa_preco DESC"),
        ],
    },
    TITULO_BASELINE: {
        "description": "Baseline da demo: tabelas cruas do bronze, sem Metric Views, instruções ou exemplos.",
        "metric_views": [],
        "tables": [f"{FQ_BRONZE}.{t}" for t in ("contas", "itens_conta", "glosas", "recursos_glosa", "operadoras",
                                                "planos", "beneficiarios", "atendimentos", "medicos", "especialidades",
                                                "unidades", "procedimentos", "motivos_glosa")],
        "perguntas": [],
        "texto": [],
        "exemplos": [],
    },
}


def hx(n):
    return f"{n:032x}"


def serializado(cfg):
    """Mesmo formato já usado com sucesso (version 2, ids hex de 32 dígitos, fontes ordenadas por identifier).
    Seções vazias ficam de fora (o baseline não tem perguntas, instruções nem Metric Views)."""
    ss = {"version": 2}
    if cfg["perguntas"]:
        ss["config"] = {"sample_questions": [{"id": hx(0x100 + i), "question": [q]}
                                             for i, q in enumerate(cfg["perguntas"])]}
    fontes = {}
    if cfg["tables"]:
        fontes["tables"] = sorted([{"identifier": t} for t in cfg["tables"]], key=lambda t: t["identifier"])
    if cfg["metric_views"]:
        fontes["metric_views"] = sorted([{"identifier": m} for m in cfg["metric_views"]], key=lambda t: t["identifier"])
    ss["data_sources"] = fontes
    instr = {}
    if cfg["texto"]:
        instr["text_instructions"] = [{"id": hx(0x200), "content": cfg["texto"]}]
    if cfg["exemplos"]:
        instr["example_question_sqls"] = [{"id": hx(0x300 + i), "question": [q], "sql": [s]}
                                          for i, (q, s) in enumerate(cfg["exemplos"])]
    if instr:
        ss["instructions"] = instr
    return json.dumps(ss, ensure_ascii=False, separators=(",", ":"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Criação opcional pela API
# MAGIC Escolha `criar_genie = sim` e informe o `warehouse_id` (SQL warehouse serverless). Rode a célula: ela cria os espaços
# MAGIC que não existem e atualiza os que já existem, pelo título.

# COMMAND ----------

if dbutils.widgets.get("criar_genie") != "sim":
    print("criar_genie = nao: nada foi criado. Use a UI com os textos acima, ou mude o widget para 'sim'.")
else:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    warehouse = dbutils.widgets.get("warehouse_id").strip()
    assert warehouse, "Informe o widget warehouse_id"

    existentes, token = {}, None
    while True:
        r = w.api_client.do("GET", "/api/2.0/genie/spaces", query={"page_token": token} if token else None)
        for s in r.get("spaces", []):
            existentes[s.get("title")] = s["space_id"]
        token = r.get("next_page_token")
        if not token:
            break

    host = w.config.host.rstrip("/")
    for titulo, cfg in ESPACOS.items():
        body = {"title": titulo, "description": cfg["description"], "warehouse_id": warehouse,
                "serialized_space": serializado(cfg)}
        if titulo in existentes:
            sid = existentes[titulo]
            w.api_client.do("PATCH", f"/api/2.0/genie/spaces/{sid}", body=body)
            acao = "atualizado"
        else:
            sid = w.api_client.do("POST", "/api/2.0/genie/spaces", body=body)["space_id"]
            acao = "criado"
        print(f"{acao:10s} {titulo}\n           {host}/genie/rooms/{sid}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Depois de criar
# MAGIC 1. Certifique o **agente governado** na UI: menu ⋮ do agente → **Assign certification** → Certified. O baseline
# MAGIC    não é certificado.
# MAGIC 2. Adicione o agente ao domínio **Glosas e Recuperação**. É manual: não há alvo SQL para esse tipo de objeto.
# MAGIC 3. Rode `04_apply_certification_and_domains` para as tabelas e Metric Views.
