# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Metric Views
# MAGIC
# MAGIC Cria 3 Metric Views do Unity Catalog sobre os fatos do ouro (`01_ingestao_e_medalhao`):
# MAGIC
# MAGIC | Metric View | Fonte (ouro) | Perguntas típicas |
# MAGIC |---|---|---|
# MAGIC | `mv_faturamento_glosa` | `fato_itens_faturados` | Faturado, glosado, taxa de glosa, recuperado, cobrado acima do contratado |
# MAGIC | `mv_autorizacoes` | `fato_autorizacoes` | Guias, negativas, tempo de resposta, glosa por falta de autorização, reclamações |
# MAGIC | `mv_central` | `fato_protocolos` | Protocolos, FCR, CSAT, NPS por canal, assunto, plano e operadora |
# MAGIC
# MAGIC Cada dimensão e medida tem os metadados que o contexto modelado da Genie Ontology lê: `display_name`,
# MAGIC `comment` e `synonyms` (YAML 1.1, testado em 26/10/2026).
# MAGIC
# MAGIC **Indicadores entre fatos não viram medida.** "Quanto da glosa vem de guias negadas" precisa de
# MAGIC `mv_autorizacoes` e `mv_faturamento_glosa` juntas. Uma Metric View só agrega a própria fonte, então essa
# MAGIC combinação está documentada na Page "Glosa" (`05_pages_content`) e nas instruções do agente
# MAGIC (`03_genie_agent_setup`). É o mesmo padrão do "Customer Return Rate" no repo original.

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC ## `mv_faturamento_glosa`

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE VIEW __OURO__.mv_faturamento_glosa
WITH METRICS LANGUAGE YAML AS $$
version: 1.1
source: __OURO__.fato_itens_faturados
comment: "Faturamento hospitalar e glosas por item de conta. A taxa de glosa só considera contas já analisadas pela operadora (status PAGA ou GLOSADA_PARCIAL); contas dos últimos ~2 meses ainda não foram analisadas."
dimensions:
  - name: mes_execucao
    expr: mes_execucao
    display_name: Mês de execução
    comment: "Mês em que o item foi executado (1º dia do mês)."
  - name: operadora
    expr: operadora
    display_name: Operadora
    synonyms: [convênio, fonte pagadora, plano de saúde]
  - name: plano
    expr: plano
    display_name: Plano
  - name: acomodacao_plano
    expr: acomodacao_plano
    display_name: Acomodação do plano
    comment: "ENFERMARIA ou APARTAMENTO: a acomodação a que o beneficiário tem direito."
  - name: unidade
    expr: unidade
    display_name: Unidade
    synonyms: [hospital, unidade hospitalar]
  - name: medico_responsavel
    expr: medico_responsavel
    display_name: Médico responsável
  - name: especialidade
    expr: especialidade
    display_name: Especialidade
  - name: tipo_atendimento
    expr: tipo_atendimento
    display_name: Tipo de atendimento
  - name: grupo_procedimento
    expr: grupo_procedimento
    display_name: Grupo do procedimento
    comment: "CONSULTA, EXAME, PROCEDIMENTO, MATERIAL, OPME, MEDICAMENTO, DIARIA ou TAXA."
  - name: procedimento
    expr: procedimento
    display_name: Procedimento
  - name: motivo_glosa
    expr: motivo_glosa
    display_name: Motivo da glosa
  - name: categoria_glosa
    expr: categoria_glosa
    display_name: Categoria da glosa
    comment: "AUTORIZACAO, PRECO, ELEGIBILIDADE, TECNICA ou ADMINISTRATIVA."
  - name: status_autorizacao
    expr: status_autorizacao
    display_name: Status da autorização do atendimento
  - name: conta_analisada
    expr: conta_analisada
    display_name: Conta já analisada
measures:
  - name: valor_faturado
    expr: SUM(valor_faturado)
    display_name: Faturado (R$)
    synonyms: [faturamento, receita bruta, valor cobrado]
  - name: valor_faturado_analisado
    expr: SUM(valor_faturado) FILTER (WHERE conta_analisada)
    display_name: Faturado já analisado (R$)
  - name: valor_glosado
    expr: SUM(valor_glosado)
    display_name: Glosado (R$)
    synonyms: [glosa, valor glosado, valor recusado]
  - name: taxa_glosa
    expr: SUM(valor_glosado) / NULLIF(SUM(valor_faturado) FILTER (WHERE conta_analisada), 0)
    display_name: Taxa de glosa
    comment: "Glosado / faturado das contas já analisadas (0 a 1)."
    synonyms: [índice de glosa, percentual de glosa]
  - name: itens_glosados
    expr: COUNT(1) FILTER (WHERE valor_glosado > 0)
    display_name: Itens glosados
  - name: valor_recuperado
    expr: SUM(valor_recuperado)
    display_name: Recuperado em recurso (R$)
  - name: taxa_recuperacao
    expr: SUM(valor_recuperado) / NULLIF(SUM(valor_glosado), 0)
    display_name: Taxa de recuperação
    comment: "Recuperado em recurso / glosado (0 a 1)."
  - name: sobrepreco
    expr: SUM(GREATEST(valor_unitario - valor_unitario_contratado, 0) * quantidade)
    display_name: Cobrado acima do contratado (R$)
    comment: "Diferença entre o valor unitário cobrado e o preço contratado vigente, vezes a quantidade."
  - name: contas
    expr: COUNT(DISTINCT conta_id)
    display_name: Contas
$$
""".replace("__OURO__", FQ_OURO))
print("OK", f"{FQ_OURO}.mv_faturamento_glosa")

# COMMAND ----------

# MAGIC %md
# MAGIC ## `mv_autorizacoes`

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE VIEW __OURO__.mv_autorizacoes
WITH METRICS LANGUAGE YAML AS $$
version: 1.1
source: __OURO__.fato_autorizacoes
comment: "Guias de autorização prévia: negativas, tempo de resposta e consequências (atendimento mesmo negado, glosa por falta de autorização, reclamações na central)."
dimensions:
  - name: mes_solicitacao
    expr: mes_solicitacao
    display_name: Mês da solicitação
  - name: operadora
    expr: operadora
    display_name: Operadora
    synonyms: [convênio, fonte pagadora]
  - name: plano
    expr: plano
    display_name: Plano
  - name: procedimento
    expr: procedimento
    display_name: Procedimento
  - name: grupo_procedimento
    expr: grupo_procedimento
    display_name: Grupo do procedimento
  - name: medico_solicitante
    expr: medico_solicitante
    display_name: Médico solicitante
  - name: especialidade
    expr: especialidade
    display_name: Especialidade
  - name: unidade
    expr: unidade
    display_name: Unidade
  - name: status
    expr: status
    display_name: Status da guia
    comment: "APROVADA, NEGADA ou PENDENTE."
  - name: motivo_negativa
    expr: motivo_negativa
    display_name: Motivo da negativa
measures:
  - name: guias
    expr: COUNT(1)
    display_name: Guias solicitadas
  - name: guias_negadas
    expr: COUNT(1) FILTER (WHERE status = 'NEGADA')
    display_name: Guias negadas
    synonyms: [negativas]
  - name: taxa_negativa
    expr: COUNT(1) FILTER (WHERE status = 'NEGADA') / NULLIF(COUNT(1) FILTER (WHERE status <> 'PENDENTE'), 0)
    display_name: Taxa de negativa
    comment: "Guias negadas / guias respondidas (0 a 1)."
    synonyms: [índice de negativa, percentual de negativa]
  - name: horas_resposta_media
    expr: AVG(horas_resposta)
    display_name: Tempo médio de resposta (h)
  - name: negadas_atendidas
    expr: COUNT(1) FILTER (WHERE status = 'NEGADA' AND paciente_atendido)
    display_name: Negadas e atendidas mesmo assim
  - name: glosa_sem_autorizacao
    expr: SUM(glosa_sem_autorizacao)
    display_name: Glosa por falta de autorização (R$)
  - name: reclamacoes_central
    expr: SUM(reclamacoes_central)
    display_name: Reclamações na central
$$
""".replace("__OURO__", FQ_OURO))
print("OK", f"{FQ_OURO}.mv_autorizacoes")

# COMMAND ----------

# MAGIC %md
# MAGIC ## `mv_central`

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE VIEW __OURO__.mv_central
WITH METRICS LANGUAGE YAML AS $$
version: 1.1
source: __OURO__.fato_protocolos
comment: "Central de atendimento: protocolos, resolução no primeiro contato, CSAT e NPS, com o plano do paciente na data do contato."
dimensions:
  - name: mes_abertura
    expr: mes_abertura
    display_name: Mês de abertura
  - name: canal
    expr: canal
    display_name: Canal
  - name: assunto
    expr: assunto
    display_name: Assunto
    synonyms: [motivo do contato]
  - name: area
    expr: area
    display_name: Área
  - name: operadora
    expr: operadora
    display_name: Operadora do paciente
    synonyms: [convênio]
  - name: plano
    expr: plano
    display_name: Plano do paciente
  - name: acomodacao_plano
    expr: acomodacao_plano
    display_name: Acomodação do plano
  - name: status
    expr: status
    display_name: Status do protocolo
measures:
  - name: protocolos
    expr: COUNT(1)
    display_name: Protocolos
    synonyms: [contatos, chamados, atendimentos da central]
  - name: taxa_fcr
    expr: AVG(CASE WHEN resolvido_primeiro_contato THEN 1.0 ELSE 0.0 END)
    display_name: Resolução no primeiro contato
    synonyms: [FCR]
  - name: csat_medio
    expr: AVG(csat)
    display_name: CSAT médio (1 a 5)
    synonyms: [satisfação]
  - name: nps
    expr: (COUNT(1) FILTER (WHERE nps >= 9) - COUNT(1) FILTER (WHERE nps <= 6)) * 100.0 / NULLIF(COUNT(nps), 0)
    display_name: NPS
    comment: "% promotores (9–10) menos % detratores (0–6), de -100 a 100."
  - name: respostas_pesquisa
    expr: COUNT(csat)
    display_name: Pesquisas respondidas
  - name: horas_ate_fechamento_media
    expr: AVG(horas_ate_fechamento)
    display_name: Tempo médio até fechar (h)
$$
""".replace("__OURO__", FQ_OURO))
print("OK", f"{FQ_OURO}.mv_central")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validação: as três histórias pelas Metric Views
# MAGIC Esperado (dados de 26/10/2026):
# MAGIC - **O1:** negativa da Beta para RM, artroscopia e artroplastia sobe de ~3,0% para ~37,8% a partir de mai/2026.
# MAGIC - **O2:** só o Dr. Ricardo Menezes Prado tem glosa por preço: R$ 152.351, igual ao cobrado acima do contratado.
# MAGIC - **O3:** o Delta Essencial lidera as reclamações de cobrança na central (36 de 66).

# COMMAND ----------

display(spark.sql(f"""
  SELECT operadora, mes_solicitacao >= DATE'2026-05-01' AS a_partir_de_maio,
         MEASURE(guias) AS guias, MEASURE(taxa_negativa) AS taxa_negativa
  FROM {FQ_OURO}.mv_autorizacoes
  WHERE procedimento IN ('Ressonância magnética de joelho', 'Artroscopia de joelho (meniscectomia)', 'Artroplastia total de joelho')
  GROUP BY ALL ORDER BY operadora, a_partir_de_maio"""))

# COMMAND ----------

display(spark.sql(f"""
  SELECT medico_responsavel, unidade, MEASURE(valor_glosado) AS glosado, MEASURE(sobrepreco) AS cobrado_acima
  FROM {FQ_OURO}.mv_faturamento_glosa WHERE categoria_glosa = 'PRECO' GROUP BY ALL ORDER BY glosado DESC"""))

# COMMAND ----------

display(spark.sql(f"""
  SELECT plano, acomodacao_plano, MEASURE(protocolos) AS protocolos, MEASURE(csat_medio) AS csat
  FROM {FQ_OURO}.mv_central WHERE assunto = 'Cobrança indevida ao paciente' GROUP BY ALL ORDER BY protocolos DESC"""))
