# Databricks notebook source
# MAGIC %md
# MAGIC # 05 - Conteúdo das Pages (manual, só referência)
# MAGIC
# MAGIC Este notebook não cria nada: Pages são escritas em **Discover → Pages → Create page** (Beta; um account admin
# MAGIC habilita em *Account console → Previews*). Os campos seguem o formulário da UI:
# MAGIC - Domain (seleção única), Name, Owner, Synonyms;
# MAGIC - Description, Body (Definição + Uso no negócio);
# MAGIC - Related assets, Sources.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 1: Taxa de glosa
# MAGIC
# MAGIC | Campo | Valor |
# MAGIC |---|---|
# MAGIC | Domain | Glosas e Recuperação |
# MAGIC | Name | Taxa de glosa |
# MAGIC | Owner | você |
# MAGIC | Synonyms | índice de glosa, percentual de glosa, glosa sobre faturamento |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Valor glosado ÷ valor faturado, considerando apenas contas já analisadas pela operadora.
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definição
# MAGIC Taxa de glosa = SUM(valor_glosado) / SUM(valor_faturado), somente das contas analisadas
# MAGIC (status PAGA ou GLOSADA_PARCIAL; coluna conta_analisada = true em @fato_itens_faturados).
# MAGIC Medida oficial: taxa_glosa em @mv_glosas.
# MAGIC
# MAGIC Por que só contas analisadas
# MAGIC A operadora leva cerca de dois meses para analisar uma conta. Nos meses recentes ainda não há glosa
# MAGIC registrada, então dividir pelo faturamento total derruba a taxa artificialmente: em out/2026 a taxa
# MAGIC "ingênua" dá 0%. Referência da rede (nov/2025–out/2026): 3,21% pela regra oficial, contra 2,86% na
# MAGIC conta ingênua.
# MAGIC
# MAGIC Uso no negócio
# MAGIC Compare períodos e operadoras sempre pela medida oficial. Para entender o motivo, veja @Glosa hospitalar;
# MAGIC para o que volta em recurso, @Taxa de recuperação.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `mv_glosas`, `fato_itens_faturados`, Page "Glosa hospitalar"
# MAGIC
# MAGIC **Sources (optional):** nenhuma; conteúdo escrito direto na Page.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 2: Glosa hospitalar
# MAGIC
# MAGIC | Campo | Valor |
# MAGIC |---|---|
# MAGIC | Domain | Glosas e Recuperação |
# MAGIC | Name | Glosa hospitalar |
# MAGIC | Owner | você |
# MAGIC | Synonyms | glosa, recusa de pagamento, valor glosado, motivo de glosa |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Valor de um item da conta que a operadora se recusa a pagar, com motivo no padrão TISS agrupado em categoria.
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definição
# MAGIC Glosa é a recusa, total ou parcial, de um item da conta (@itens_conta) pela operadora. Cada glosa
# MAGIC (@glosas) tem um motivo TISS (@motivos_glosa) agrupado em categoria:
# MAGIC - AUTORIZACAO — 1801: procedimento sem autorização prévia. Evite: não execute eletivo sem guia aprovada.
# MAGIC - PRECO — 1705: valor acima do preço contratado. Evite: cobre o preço vigente de @precos_contratados.
# MAGIC - ELEGIBILIDADE — 1909: acomodação incompatível com o plano; 1301: beneficiário fora da vigência.
# MAGIC   Evite: confira plano (@planos), acomodação e vigência na admissão.
# MAGIC - TECNICA — 1602: falta de justificativa técnica. Evite: registre a justificativa no prontuário.
# MAGIC - ADMINISTRATIVA — 2001: cobrança em duplicidade; 2010: documentação incompleta. Evite: audite a conta
# MAGIC   antes do envio.
# MAGIC
# MAGIC Uso no negócio
# MAGIC Analise a glosa por categoria e motivo em @mv_glosas. A fórmula oficial está em @Taxa de glosa.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `glosas`, `motivos_glosa`, `itens_conta`, `precos_contratados`, `planos`, `mv_glosas`
# MAGIC
# MAGIC **Sources (optional):** Padrão TISS (ANS); sistema de faturamento (schema `faturamento` da origem).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 3: Taxa de recuperação
# MAGIC
# MAGIC | Campo | Valor |
# MAGIC |---|---|
# MAGIC | Domain | Glosas e Recuperação |
# MAGIC | Name | Taxa de recuperação |
# MAGIC | Owner | você |
# MAGIC | Synonyms | recuperação de glosa, recurso de glosa, reversão de glosa, taxa de aceite |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Valor recuperado em recurso ÷ valor glosado. Mostra quanto da glosa o hospital consegue reverter.
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definição
# MAGIC - Taxa de recuperação = SUM(valor_recuperado) / SUM(valor_glosado).
# MAGIC - Taxa de recurso = itens glosados com recurso ÷ itens glosados.
# MAGIC - Taxa de aceite = recursos ACEITO ÷ recursos decididos (ACEITO + NEGADO; EM_ANALISE fica fora).
# MAGIC Medidas oficiais em @mv_recuperacao; recursos em @recursos_glosa.
# MAGIC
# MAGIC Uso no negócio
# MAGIC Glosa de preço, autorização e elegibilidade quase não volta: 13,2%, 10,9% e 6,6% de recuperação,
# MAGIC contra 35,5% na administrativa. Nessas categorias, o ganho está em corrigir a origem (preço, guia,
# MAGIC acomodação), não em recorrer. Veja @Glosa hospitalar.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `mv_recuperacao`, `recursos_glosa`, Page "Glosa hospitalar"
# MAGIC
# MAGIC **Sources (optional):** nenhuma; conteúdo escrito direto na Page.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 4: Agente Faturamento e Glosas
# MAGIC
# MAGIC | Campo | Valor |
# MAGIC |---|---|
# MAGIC | Domain | Faturamento Hospitalar |
# MAGIC | Name | Agente Faturamento e Glosas |
# MAGIC | Owner | você |
# MAGIC | Synonyms | genie de faturamento, genie de glosa, assistente de faturamento hospitalar |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Apresentação do Genie Agent "Faturamento e Glosas — Rede Américas": o que ele responde e de quais Metric
# MAGIC Views certificadas ele parte.
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definição
# MAGIC @Faturamento e Glosas — Rede Américas é o Genie Agent de faturamento hospitalar, glosa e recuperação.
# MAGIC Responde a partir de três Metric Views certificadas: @mv_faturamento, @mv_glosas e @mv_recuperacao.
# MAGIC Valor faturado = SUM(valor_total dos itens da conta), medida valor_faturado em @mv_faturamento.
# MAGIC
# MAGIC Uso no negócio
# MAGIC Pergunte, por exemplo:
# MAGIC - "Qual a taxa de glosa da rede nos últimos 12 meses?"
# MAGIC - "Como evoluiu a taxa de glosa mês a mês?"
# MAGIC - "Qual operadora tem a maior taxa de glosa e qual o principal motivo?"
# MAGIC - "Por que a glosa da Beta Assistência Médica subiu a partir de maio de 2026?"
# MAGIC - "Quais médicos geram glosa por preço acima do contratado e vale a pena recorrer?"
# MAGIC
# MAGIC Definições: @Taxa de glosa, @Glosa hospitalar, @Taxa de recuperação.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `Faturamento e Glosas — Rede Américas`, `mv_faturamento`, `mv_glosas`, `mv_recuperacao`
# MAGIC
# MAGIC **Sources (optional):** nenhuma; conteúdo escrito direto na Page.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Notas (do repo original)
# MAGIC - O campo **Domain** da Page é de seleção única: escolha onde alguém procuraria a definição.
# MAGIC - Use a menção `@` do editor para ligar os ativos e as outras Pages. É isso que cria os *related assets* e
# MAGIC   deixa o Genie One navegar entre elas.
# MAGIC - **Publique** todas: rascunhos têm prioridade menor no ranking do Genie.
# MAGIC - **Não coloque dados sensíveis** em nome, sinônimos, descrição ou corpo: nada de paciente, CPF ou carteirinha.
