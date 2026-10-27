# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Genie Agent (manual, só referência)
# MAGIC
# MAGIC Este notebook não cria nada: o Genie Agent é criado pela UI. Copie os textos abaixo no formulário
# MAGIC **Create Agent** do Genie One, usando um SQL warehouse serverless.
# MAGIC
# MAGIC ## Nome
# MAGIC ```
# MAGIC Ciclo de Receita — Rede Américas
# MAGIC ```
# MAGIC
# MAGIC ## Descrição
# MAGIC ```
# MAGIC Responde perguntas sobre o ciclo de receita da Rede Américas usando Metric Views certificadas: faturamento,
# MAGIC glosas e recursos, autorização prévia (guias e negativas) e central de atendimento (protocolos, FCR, CSAT, NPS).
# MAGIC Recortes por operadora, plano, acomodação, unidade, médico, especialidade, procedimento, canal, assunto e mês.
# MAGIC Dados sintéticos, nov/2025 a out/2026.
# MAGIC ```
# MAGIC
# MAGIC ## Fontes de dados
# MAGIC Anexe **só** as três Metric Views (criadas em `02_create_metric_views`):
# MAGIC - `rede_americas.ontologia_ouro.mv_faturamento_glosa`
# MAGIC - `rede_americas.ontologia_ouro.mv_autorizacoes`
# MAGIC - `rede_americas.ontologia_ouro.mv_central`
# MAGIC
# MAGIC Não anexe as tabelas da prata: a ideia da demo é mostrar o Genie preferindo a camada governada a junções ad hoc.
# MAGIC Para perguntas de detalhe, o Genie One ainda encontra a prata pela ontologia, com as PK/FK e os comentários.
# MAGIC
# MAGIC ## Instruções (do agente)
# MAGIC ```
# MAGIC Você é o assistente de ciclo de receita da Rede Américas (hospitais, centro oncológico e ambulatório).
# MAGIC
# MAGIC - Use sempre as Metric Views (mv_faturamento_glosa, mv_autorizacoes, mv_central) e MEASURE(). Não recalcule
# MAGIC   taxa de glosa, taxa de negativa, FCR, CSAT ou NPS por conta própria.
# MAGIC - Taxa de glosa só vale para contas já analisadas pela operadora. Os últimos ~2 meses ainda não foram
# MAGIC   analisados: não diga que a glosa caiu nesses meses.
# MAGIC - Para explicar uma variação, compare com a média dos 3 meses anteriores, não só com o mês anterior.
# MAGIC - "Por que a glosa subiu?" pede duas visões: o motivo da glosa (mv_faturamento_glosa) e, se o motivo for
# MAGIC   falta de autorização, a taxa de negativa da mesma operadora no mesmo período (mv_autorizacoes). Diga que
# MAGIC   combinou as duas.
# MAGIC - Motivos de glosa: 1801 = sem autorização prévia; 1705 = acima do preço contratado; 1909 = acomodação
# MAGIC   incompatível com o plano.
# MAGIC - "Atendimento" da central é o protocolo (mv_central). "Atendimento" no hospital é PS, ambulatório,
# MAGIC   internação ou oncologia. Se a pergunta for ambígua, pergunte qual dos dois.
# MAGIC - Valores em reais (R$) e taxas em percentual com uma casa decimal. Sem período na pergunta, use os
# MAGIC   últimos 12 meses e diga qual foi.
# MAGIC - Nunca mostre nome, CPF ou carteirinha de paciente.
# MAGIC ```
# MAGIC
# MAGIC ## Perguntas de exemplo (tela de configuração do agente)
# MAGIC - Por que a glosa subiu na Beta Assistência Médica?
# MAGIC - Qual a taxa de negativa de autorização por operadora, antes e depois de maio de 2026?
# MAGIC - Quais médicos geram mais glosa por preço acima do contratado?
# MAGIC - Em quais planos a glosa por acomodação é mais alta?
# MAGIC - Os pacientes que reclamaram de cobrança na central tinham qual plano?
# MAGIC - Qual o CSAT de quem reclamou de negativa de autorização?
# MAGIC
# MAGIC ## Consultas SQL de exemplo (opcional, testadas em 26/10/2026)
# MAGIC ```sql
# MAGIC -- Negativa da Beta antes x depois de mai/2026 (≈ 3,0% → 37,8%)
# MAGIC SELECT operadora, mes_solicitacao >= DATE'2026-05-01' AS a_partir_de_maio, MEASURE(taxa_negativa) AS taxa_negativa
# MAGIC FROM rede_americas.ontologia_ouro.mv_autorizacoes
# MAGIC WHERE procedimento IN ('Ressonância magnética de joelho', 'Artroscopia de joelho (meniscectomia)', 'Artroplastia total de joelho')
# MAGIC GROUP BY ALL ORDER BY operadora, a_partir_de_maio;
# MAGIC
# MAGIC -- Glosa por preço por médico (um médico concentra tudo)
# MAGIC SELECT medico_responsavel, unidade, MEASURE(valor_glosado) AS glosado, MEASURE(sobrepreco) AS cobrado_acima
# MAGIC FROM rede_americas.ontologia_ouro.mv_faturamento_glosa
# MAGIC WHERE categoria_glosa = 'PRECO' GROUP BY ALL ORDER BY glosado DESC;
# MAGIC
# MAGIC -- Reclamações de cobrança na central por plano (Delta Essencial lidera)
# MAGIC SELECT plano, acomodacao_plano, MEASURE(protocolos) AS protocolos, MEASURE(csat_medio) AS csat
# MAGIC FROM rede_americas.ontologia_ouro.mv_central
# MAGIC WHERE assunto = 'Cobrança indevida ao paciente' GROUP BY ALL ORDER BY protocolos DESC;
# MAGIC ```
# MAGIC
# MAGIC ## Depois de criar o agente
# MAGIC 1. Certifique: menu ⋮ do agente → **Assign certification** → Certified.
# MAGIC 2. Adicione-o ao domínio **Faturamento e Glosa** (criado no passo dos domínios).
# MAGIC 3. Rode `04_apply_certification_and_domains` para todo o resto (tabelas e Metric Views).
