# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Metric Views (faturamento, glosas e recuperação)
# MAGIC
# MAGIC Cria 3 Metric Views do Unity Catalog sobre o fato do ouro `fato_itens_faturados` (grão: item da conta):
# MAGIC
# MAGIC | Metric View | Medidas | Perguntas típicas |
# MAGIC |---|---|---|
# MAGIC | `mv_faturamento` | valor faturado, faturado analisado, contas, itens, ticket médio | Quanto faturamos por operadora, unidade, médico, mês? |
# MAGIC | `mv_glosas` | valor glosado, **taxa de glosa**, itens e contas glosadas, sobrepreço | Qual a taxa de glosa? Qual o principal motivo? |
# MAGIC | `mv_recuperacao` | glosado, recuperado, **taxa de recuperação**, taxa de recurso, taxa de aceite | Onde vale a pena recorrer? |
# MAGIC
# MAGIC Dimensões comuns: período (mês, trimestre, ano), operadora, plano, acomodação, unidade, médico, especialidade,
# MAGIC procedimento, grupo do procedimento, tipo de atendimento e status da conta.
# MAGIC
# MAGIC **Regra de negócio:** a taxa de glosa só considera **contas já analisadas** pela operadora (status PAGA ou
# MAGIC GLOSADA_PARCIAL). Os últimos ~2 meses ainda não foram analisados; dividir pelo faturado total subestima a taxa
# MAGIC e faz a glosa "cair" nos meses recentes. A validação no fim mostra a diferença com números.
# MAGIC
# MAGIC Cada dimensão e medida tem `display_name`, `comment` e `synonyms` (YAML 1.1): é o contexto modelado que a Genie
# MAGIC Ontology lê. Idempotente (`CREATE OR REPLACE VIEW`).

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

DIMS_COMUNS = """
  - name: mes
    expr: mes_execucao
    display_name: Mês
    comment: "Mês de execução do item (1º dia do mês)."
    synonyms: [mês, competência, período, mes de execução]
  - name: trimestre
    expr: trimestre_execucao
    display_name: Trimestre
    comment: "Trimestre de execução (1º dia do trimestre)."
    synonyms: [trimestre, quarter]
  - name: ano
    expr: ano_execucao
    display_name: Ano
    synonyms: [ano, exercício]
  - name: operadora
    expr: operadora
    display_name: Operadora
    comment: "Operadora de plano de saúde cobrada na conta (fonte pagadora)."
    synonyms: [convênio, fonte pagadora, plano de saúde, pagador]
  - name: plano
    expr: plano
    display_name: Plano
    comment: "Plano do beneficiário na carteirinha usada no atendimento."
    synonyms: [produto, plano do beneficiário]
  - name: acomodacao_plano
    expr: acomodacao_plano
    display_name: Acomodação do plano
    comment: "ENFERMARIA ou APARTAMENTO: a acomodação a que o beneficiário tem direito."
    synonyms: [acomodação, tipo de quarto]
  - name: unidade
    expr: unidade
    display_name: Unidade
    synonyms: [hospital, unidade hospitalar, estabelecimento]
  - name: medico
    expr: medico_responsavel
    display_name: Médico responsável
    synonyms: [médico, profissional, prestador]
  - name: especialidade
    expr: especialidade
    display_name: Especialidade
    synonyms: [especialidade médica]
  - name: procedimento
    expr: procedimento
    display_name: Procedimento
    comment: "Procedimento, material, OPME, medicamento, diária ou taxa cobrado no item (código TUSS fictício)."
    synonyms: [item, código TUSS, serviço]
  - name: grupo_procedimento
    expr: grupo_procedimento
    display_name: Grupo do procedimento
    comment: "CONSULTA, EXAME, PROCEDIMENTO, MATERIAL, OPME, MEDICAMENTO, DIARIA ou TAXA."
    synonyms: [grupo, tipo de item]
  - name: tipo_atendimento
    expr: tipo_atendimento
    display_name: Tipo de atendimento
    comment: "PS, AMBULATORIAL, INTERNACAO ou ONCOLOGIA."
    synonyms: [tipo de atendimento, linha de cuidado]
  - name: status_conta
    expr: status_conta
    display_name: Status da conta
    comment: "ABERTA, ENVIADA, PAGA ou GLOSADA_PARCIAL."
  - name: conta_analisada
    expr: conta_analisada
    display_name: Conta já analisada
    comment: "true quando a operadora já analisou a conta (status PAGA ou GLOSADA_PARCIAL)."
"""

DIMS_GLOSA = """
  - name: motivo_glosa
    expr: motivo_glosa
    display_name: Motivo da glosa
    comment: "Motivo TISS informado pela operadora (ex.: sem autorização prévia, acima do preço contratado)."
    synonyms: [motivo, razão da glosa, código TISS]
  - name: categoria_glosa
    expr: categoria_glosa
    display_name: Categoria da glosa
    comment: "AUTORIZACAO, PRECO, ELEGIBILIDADE, TECNICA ou ADMINISTRATIVA."
    synonyms: [categoria, tipo de glosa]
"""

VIEWS = {
"mv_faturamento": """
version: 1.1
source: __OURO__.fato_itens_faturados
comment: "Faturamento hospitalar por item de conta. Valores em R$. Faturado analisado = itens de contas já analisadas pela operadora (denominador oficial da taxa de glosa)."
dimensions:
__DIMS__
measures:
  - name: valor_faturado
    expr: SUM(valor_faturado)
    display_name: Valor faturado (R$)
    comment: "Soma do valor cobrado nos itens das contas, em R$."
    synonyms: [faturamento, receita bruta, valor cobrado, produção]
  - name: valor_faturado_analisado
    expr: SUM(valor_faturado) FILTER (WHERE conta_analisada)
    display_name: Faturado já analisado (R$)
    comment: "Faturado só das contas já analisadas pela operadora (status PAGA ou GLOSADA_PARCIAL)."
    synonyms: [faturado analisado]
  - name: contas
    expr: COUNT(DISTINCT conta_id)
    display_name: Contas
    synonyms: [quantidade de contas, número de contas]
  - name: itens
    expr: COUNT(1)
    display_name: Itens faturados
    synonyms: [itens, linhas da conta]
  - name: ticket_medio_conta
    expr: SUM(valor_faturado) / NULLIF(COUNT(DISTINCT conta_id), 0)
    display_name: Ticket médio por conta (R$)
    synonyms: [ticket médio, valor médio da conta]
""",
"mv_glosas": """
version: 1.1
source: __OURO__.fato_itens_faturados
comment: "Glosas hospitalares por item de conta. REGRA: taxa de glosa = valor glosado / valor faturado das contas já analisadas (status PAGA ou GLOSADA_PARCIAL). Nunca divida pelo faturado total: os meses recentes ainda não foram analisados."
dimensions:
__DIMS__
__DIMS_GLOSA__
measures:
  - name: valor_glosado
    expr: SUM(valor_glosado)
    display_name: Valor glosado (R$)
    comment: "Valor recusado pela operadora, em R$."
    synonyms: [glosa, glosado, valor recusado, perda por glosa]
  - name: valor_faturado_analisado
    expr: SUM(valor_faturado) FILTER (WHERE conta_analisada)
    display_name: Faturado já analisado (R$)
    comment: "Denominador oficial da taxa de glosa."
  - name: taxa_glosa
    expr: SUM(valor_glosado) / NULLIF(SUM(valor_faturado) FILTER (WHERE conta_analisada), 0)
    display_name: Taxa de glosa
    comment: "Valor glosado / valor faturado das contas já analisadas (0 a 1). Meses sem contas analisadas retornam nulo, não zero."
    synonyms: [índice de glosa, percentual de glosa, % de glosa]
  - name: itens_glosados
    expr: COUNT(1) FILTER (WHERE valor_glosado > 0)
    display_name: Itens glosados
  - name: contas_glosadas
    expr: COUNT(DISTINCT conta_id) FILTER (WHERE valor_glosado > 0)
    display_name: Contas glosadas
  - name: sobrepreco
    expr: SUM(GREATEST(valor_unitario - valor_unitario_contratado, 0) * quantidade)
    display_name: Cobrado acima do contratado (R$)
    comment: "Diferença entre o valor unitário cobrado e o preço contratado vigente, vezes a quantidade."
    synonyms: [sobrepreço, cobrança acima da tabela]
""",
"mv_recuperacao": """
version: 1.1
source: __OURO__.fato_itens_faturados
filter: valor_glosado > 0
comment: "Recuperação financeira de glosas: só itens glosados. Taxa de recuperação = valor recuperado em recurso / valor glosado."
dimensions:
__DIMS__
__DIMS_GLOSA__
  - name: status_recurso
    expr: status_recurso
    display_name: Status do recurso
    comment: "EM_ANALISE, ACEITO ou NEGADO; nulo quando a glosa não foi recorrida."
    synonyms: [situação do recurso]
measures:
  - name: valor_glosado
    expr: SUM(valor_glosado)
    display_name: Valor glosado (R$)
    synonyms: [glosa, glosado]
  - name: valor_recuperado
    expr: SUM(valor_recuperado)
    display_name: Valor recuperado (R$)
    comment: "Valor revertido a favor do hospital em recurso aceito, em R$."
    synonyms: [recuperado, recuperação, valor revertido]
  - name: taxa_recuperacao
    expr: SUM(valor_recuperado) / NULLIF(SUM(valor_glosado), 0)
    display_name: Taxa de recuperação
    comment: "Valor recuperado / valor glosado (0 a 1)."
    synonyms: [índice de recuperação, % recuperado]
  - name: itens_recursados
    expr: COUNT(1) FILTER (WHERE recursado)
    display_name: Itens recorridos
    synonyms: [recursos, glosas recorridas]
  - name: taxa_recurso
    expr: COUNT(1) FILTER (WHERE recursado) / COUNT(1)
    display_name: Taxa de recurso
    comment: "Itens glosados que foram recorridos / itens glosados (0 a 1)."
  - name: taxa_aceite
    expr: COUNT(1) FILTER (WHERE status_recurso = 'ACEITO') / NULLIF(COUNT(1) FILTER (WHERE status_recurso IN ('ACEITO', 'NEGADO')), 0)
    display_name: Taxa de aceite do recurso
    comment: "Recursos aceitos / recursos já decididos (0 a 1)."
""",
}

for nome, yaml in VIEWS.items():
    yaml = yaml.replace("__DIMS__", DIMS_COMUNS.strip("\n")).replace("__DIMS_GLOSA__", DIMS_GLOSA.strip("\n"))
    spark.sql(f"CREATE OR REPLACE VIEW {FQ_OURO}.{nome}\nWITH METRICS\nLANGUAGE YAML\nAS $$\n{yaml.replace('__OURO__', FQ_OURO)}$$")
    print("OK", f"{FQ_OURO}.{nome}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validação determinística das 5 perguntas da demo
# MAGIC
# MAGIC Cada resposta é calculada duas vezes: (a) pela Metric View com `MEASURE()` e (b) por SQL independente direto
# MAGIC na **prata**. As duas precisam bater entre si e com os valores esperados (dados sintéticos, seed 42). Se algum
# MAGIC `assert` falhar, a definição da métrica ou os dados mudaram.

# COMMAND ----------

PRATA_BASE = f"""
WITH g AS (
  SELECT gl.item_id, SUM(gl.valor_glosado) AS valor_glosado,
         MAX_BY(mg.categoria, gl.valor_glosado) AS categoria, MAX_BY(mg.descricao, gl.valor_glosado) AS motivo,
         SUM(COALESCE(r.valor_recuperado, 0)) AS valor_recuperado
  FROM {FQ_PRATA}.glosas gl
  JOIN {FQ_PRATA}.motivos_glosa mg ON mg.motivo_glosa_id = gl.motivo_glosa_id
  LEFT JOIN {FQ_PRATA}.recursos_glosa r ON r.glosa_id = gl.glosa_id
  GROUP BY gl.item_id),
b AS (
  SELECT i.item_id, i.valor_total AS valor_faturado, DATE_TRUNC('MONTH', i.data_execucao)::DATE AS mes,
         c.status IN ('PAGA', 'GLOSADA_PARCIAL') AS analisada, o.nome AS operadora, m.nome AS medico,
         e.nome AS especialidade, u.nome AS unidade, COALESCE(g.valor_glosado, 0) AS valor_glosado,
         g.categoria, g.motivo, COALESCE(g.valor_recuperado, 0) AS valor_recuperado
  FROM {FQ_PRATA}.itens_conta i
  JOIN {FQ_PRATA}.contas c ON c.conta_id = i.conta_id
  JOIN {FQ_PRATA}.atendimentos a ON a.atendimento_id = c.atendimento_id
  JOIN {FQ_PRATA}.operadoras o ON o.operadora_id = c.operadora_id
  JOIN {FQ_PRATA}.medicos m ON m.medico_id = a.medico_responsavel_id
  JOIN {FQ_PRATA}.especialidades e ON e.especialidade_id = m.especialidade_id
  JOIN {FQ_PRATA}.unidades u ON u.unidade_id = a.unidade_id
  LEFT JOIN g ON g.item_id = i.item_id)
"""


def linhas(sql):
    return [r.asDict() for r in spark.sql(sql).collect()]


def pct(x):
    return None if x is None else round(float(x) * 100, 2)


def igual(a, b, nome, tol=0.01):
    ok = (a is None and b is None) or (a is not None and b is not None and abs(float(a) - float(b)) <= tol)
    assert ok, f"{nome}: {a} != {b}"


# COMMAND ----------

# MAGIC %md
# MAGIC ### Q1 — Qual a taxa de glosa da rede? (correta × ingênua)
# MAGIC Esperado: **3,21%** (R$ 1.055.648,91 glosados ÷ R$ 32.929.106,60 faturados em contas analisadas). A conta
# MAGIC ingênua (÷ faturado total, R$ 36,9 mi) dá 2,86%.

# COMMAND ----------

mv = linhas(f"""SELECT MEASURE(taxa_glosa) AS taxa, MEASURE(valor_glosado) AS glosado, MEASURE(valor_faturado_analisado) AS analisado
                FROM {FQ_OURO}.mv_glosas""")[0]
mv_fat = linhas(f"SELECT MEASURE(valor_faturado) AS faturado FROM {FQ_OURO}.mv_faturamento")[0]
pr = linhas(PRATA_BASE + """SELECT SUM(valor_glosado) / SUM(valor_faturado) FILTER (WHERE analisada) AS taxa,
                                   SUM(valor_glosado) / SUM(valor_faturado) AS ingenua FROM b""")[0]
igual(pct(mv["taxa"]), pct(pr["taxa"]), "Q1 MV x prata")
igual(pct(mv["taxa"]), 3.21, "Q1 esperado")
igual(pct(float(mv["glosado"]) / float(mv_fat["faturado"])), pct(pr["ingenua"]), "Q1 ingênua MV x prata")
igual(pct(pr["ingenua"]), 2.86, "Q1 ingênua esperado")
igual(mv["glosado"], 1055648.91, "Q1 glosado")
igual(mv["analisado"], 32929106.60, "Q1 faturado analisado")
display(spark.createDataFrame([("correta (contas analisadas)", pct(mv["taxa"])), ("ingênua (faturado total)", pct(pr["ingenua"]))],
                              "definicao string, taxa_glosa_pct double"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Q2 — Como evoluiu a taxa de glosa mês a mês?
# MAGIC Esperado: set/2026 **6,05%** (correta) × 2,87% (ingênua); out/2026 **nulo** (nenhuma conta analisada) × 0,00%
# MAGIC na conta ingênua, que sugere uma queda que não existe.

# COMMAND ----------

mv = {r["mes"].isoformat(): r for r in linhas(f"""
  SELECT g.mes, g.taxa, g.glosado / f.faturado AS ingenua FROM
    (SELECT mes, MEASURE(taxa_glosa) AS taxa, MEASURE(valor_glosado) AS glosado FROM {FQ_OURO}.mv_glosas GROUP BY mes) g
    JOIN (SELECT mes, MEASURE(valor_faturado) AS faturado FROM {FQ_OURO}.mv_faturamento GROUP BY mes) f ON f.mes = g.mes""")}
pr = {r["mes"].isoformat(): r for r in linhas(PRATA_BASE + """
  SELECT mes, SUM(valor_glosado) / NULLIF(SUM(valor_faturado) FILTER (WHERE analisada), 0) AS taxa,
         SUM(valor_glosado) / SUM(valor_faturado) AS ingenua FROM b GROUP BY mes""")}
assert mv.keys() == pr.keys(), "Q2 meses diferentes"
for m in mv:
    igual(pct(mv[m]["taxa"]), pct(pr[m]["taxa"]), f"Q2 {m} MV x prata")
    igual(pct(mv[m]["ingenua"]), pct(pr[m]["ingenua"]), f"Q2 {m} ingênua MV x prata")
igual(pct(mv["2026-09-01"]["taxa"]), 6.05, "Q2 set/2026 correta")
igual(pct(mv["2026-09-01"]["ingenua"]), 2.87, "Q2 set/2026 ingênua")
igual(pct(mv["2026-10-01"]["taxa"]), None, "Q2 out/2026 correta")
igual(pct(mv["2026-10-01"]["ingenua"]), 0.00, "Q2 out/2026 ingênua")
display(spark.createDataFrame([(m, pct(mv[m]["taxa"]), pct(mv[m]["ingenua"])) for m in sorted(mv)],
                              "mes string, taxa_correta_pct double, taxa_ingenua_pct double"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Q3 — Qual operadora tem a maior taxa de glosa e qual o principal motivo?
# MAGIC Esperado: **Delta Assistência, 4,66%**, puxada por "Acomodação cobrada incompatível com o plano" (R$ 78.936,00).
# MAGIC A Beta tem o maior valor glosado (R$ 468.531,17), mas taxa menor.

# COMMAND ----------

mv = {r["operadora"]: r for r in linhas(f"""SELECT operadora, MEASURE(taxa_glosa) AS taxa, MEASURE(valor_glosado) AS glosado
                                             FROM {FQ_OURO}.mv_glosas GROUP BY operadora""")}
pr = {r["operadora"]: r for r in linhas(PRATA_BASE + """
  SELECT operadora, SUM(valor_glosado) / SUM(valor_faturado) FILTER (WHERE analisada) AS taxa, SUM(valor_glosado) AS glosado
  FROM b GROUP BY operadora""")}
for o in pr:
    igual(pct(mv[o]["taxa"]), pct(pr[o]["taxa"]), f"Q3 {o} MV x prata")
    igual(mv[o]["glosado"], pr[o]["glosado"], f"Q3 {o} glosado MV x prata")
topo = max(mv, key=lambda o: mv[o]["taxa"])
assert topo == "Delta Assistência", f"Q3 operadora com maior taxa: {topo}"
igual(pct(mv[topo]["taxa"]), 4.66, "Q3 taxa Delta")
assert max(mv, key=lambda o: mv[o]["glosado"]) == "Beta Assistência Médica", "Q3 maior valor glosado"
igual(mv["Beta Assistência Médica"]["glosado"], 468531.17, "Q3 glosado Beta")
mot_mv = linhas(f"""SELECT motivo_glosa, MEASURE(valor_glosado) AS glosado FROM {FQ_OURO}.mv_glosas
                    WHERE operadora = 'Delta Assistência' AND motivo_glosa IS NOT NULL GROUP BY motivo_glosa ORDER BY glosado DESC LIMIT 1""")[0]
mot_pr = linhas(PRATA_BASE + """SELECT motivo, SUM(valor_glosado) AS glosado FROM b
                                WHERE operadora = 'Delta Assistência' AND motivo IS NOT NULL GROUP BY motivo ORDER BY glosado DESC LIMIT 1""")[0]
assert mot_mv["motivo_glosa"] == mot_pr["motivo"] == "Acomodação cobrada incompatível com o plano", "Q3 motivo principal"
igual(mot_mv["glosado"], mot_pr["glosado"], "Q3 motivo MV x prata")
igual(mot_mv["glosado"], 78936.00, "Q3 motivo esperado")
display(spark.sql(f"""SELECT operadora, ROUND(MEASURE(taxa_glosa) * 100, 2) AS taxa_glosa_pct, MEASURE(valor_glosado) AS valor_glosado
                      FROM {FQ_OURO}.mv_glosas GROUP BY operadora ORDER BY taxa_glosa_pct DESC"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Q4 — Por que a glosa subiu na Beta a partir de maio de 2026?
# MAGIC Esperado (só contas analisadas): taxa **2,82% → 5,08%**; glosa da categoria AUTORIZACAO (procedimento sem
# MAGIC autorização prévia) **R$ 78.755,00 → R$ 151.002,50**.

# COMMAND ----------

mv = {r["depois"]: r for r in linhas(f"""
  SELECT mes >= DATE'2026-05-01' AS depois, MEASURE(taxa_glosa) AS taxa
  FROM {FQ_OURO}.mv_glosas WHERE operadora = 'Beta Assistência Médica' AND conta_analisada GROUP BY ALL""")}
mv_aut = {r["depois"]: r for r in linhas(f"""
  SELECT mes >= DATE'2026-05-01' AS depois, MEASURE(valor_glosado) AS glosado
  FROM {FQ_OURO}.mv_glosas WHERE operadora = 'Beta Assistência Médica' AND conta_analisada AND categoria_glosa = 'AUTORIZACAO' GROUP BY ALL""")}
pr = {r["depois"]: r for r in linhas(PRATA_BASE + """
  SELECT mes >= DATE'2026-05-01' AS depois, SUM(valor_glosado) / SUM(valor_faturado) AS taxa,
         SUM(valor_glosado) FILTER (WHERE categoria = 'AUTORIZACAO') AS glosa_aut
  FROM b WHERE operadora = 'Beta Assistência Médica' AND analisada GROUP BY ALL""")}
for k in (False, True):
    igual(pct(mv[k]["taxa"]), pct(pr[k]["taxa"]), f"Q4 taxa depois={k} MV x prata")
    igual(mv_aut[k]["glosado"], pr[k]["glosa_aut"], f"Q4 glosa AUTORIZACAO depois={k} MV x prata")
igual(pct(mv[False]["taxa"]), 2.82, "Q4 taxa antes")
igual(pct(mv[True]["taxa"]), 5.08, "Q4 taxa depois")
igual(mv_aut[False]["glosado"], 78755.00, "Q4 glosa AUTORIZACAO antes")
igual(mv_aut[True]["glosado"], 151002.50, "Q4 glosa AUTORIZACAO depois")
display(spark.createDataFrame([("antes de mai/2026", pct(mv[False]["taxa"]), float(mv_aut[False]["glosado"])),
                               ("a partir de mai/2026", pct(mv[True]["taxa"]), float(mv_aut[True]["glosado"]))],
                              "periodo string, taxa_glosa_pct double, glosa_autorizacao double"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Q5 — Quem concentra a glosa por preço e onde vale a pena recorrer?
# MAGIC Esperado: só o **Dr. Ricardo Menezes Prado** (Ortopedia, Hospital Américas Sul) tem glosa de PRECO: 49 itens,
# MAGIC R$ 152.351,00. Taxa de recuperação por categoria: ADMINISTRATIVA 35,5% · TECNICA 18,4% · PRECO 13,2% ·
# MAGIC AUTORIZACAO 10,9% · ELEGIBILIDADE 6,6% — vale recorrer de glosa administrativa; as demais se evitam na origem.

# COMMAND ----------

med_mv = linhas(f"""SELECT medico, especialidade, unidade, MEASURE(itens_glosados) AS itens, MEASURE(valor_glosado) AS glosado
                    FROM {FQ_OURO}.mv_glosas WHERE categoria_glosa = 'PRECO' GROUP BY ALL""")
med_pr = linhas(PRATA_BASE + """SELECT medico, especialidade, unidade, COUNT(1) AS itens, SUM(valor_glosado) AS glosado
                                FROM b WHERE categoria = 'PRECO' GROUP BY ALL""")
assert len(med_mv) == len(med_pr) == 1, f"Q5 médicos com glosa por preço: {med_mv}"
assert (med_mv[0]["medico"], med_mv[0]["especialidade"], med_mv[0]["unidade"]) == \
       (med_pr[0]["medico"], med_pr[0]["especialidade"], med_pr[0]["unidade"]) == \
       ("Ricardo Menezes Prado", "Ortopedia", "Hospital Américas Sul"), "Q5 médico"
assert med_mv[0]["itens"] == med_pr[0]["itens"] == 49, "Q5 itens"
igual(med_mv[0]["glosado"], med_pr[0]["glosado"], "Q5 glosado MV x prata")
igual(med_mv[0]["glosado"], 152351.00, "Q5 glosado esperado")
rec_mv = {r["categoria_glosa"]: r for r in linhas(f"""SELECT categoria_glosa, MEASURE(taxa_recuperacao) AS taxa
                                                    FROM {FQ_OURO}.mv_recuperacao GROUP BY categoria_glosa""")}
rec_pr = {r["categoria"]: r for r in linhas(PRATA_BASE + """SELECT categoria, SUM(valor_recuperado) / SUM(valor_glosado) AS taxa
                                                           FROM b WHERE valor_glosado > 0 GROUP BY categoria""")}
esperado = {"ADMINISTRATIVA": 35.5, "TECNICA": 18.4, "PRECO": 13.2, "AUTORIZACAO": 10.9, "ELEGIBILIDADE": 6.6}
assert rec_mv.keys() == rec_pr.keys() == esperado.keys(), "Q5 categorias"
for c, e in esperado.items():
    igual(pct(rec_mv[c]["taxa"]), pct(rec_pr[c]["taxa"]), f"Q5 recuperação {c} MV x prata")
    igual(round(float(rec_mv[c]["taxa"]) * 100, 1), e, f"Q5 recuperação {c} esperado", tol=0.05)
display(spark.sql(f"""SELECT categoria_glosa, MEASURE(valor_glosado) AS glosado, MEASURE(valor_recuperado) AS recuperado,
                             ROUND(MEASURE(taxa_recuperacao) * 100, 1) AS taxa_recuperacao_pct, MEASURE(itens_recursados) AS recorridos
                      FROM {FQ_OURO}.mv_recuperacao GROUP BY categoria_glosa ORDER BY taxa_recuperacao_pct DESC"""))

# COMMAND ----------

print("Validação OK: as 5 respostas batem entre Metric Views, prata e valores esperados.")
