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
# MAGIC **Não coloque dados sensíveis** em nome, sinônimos, descrição ou corpo: nada de paciente, CPF ou carteirinha.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 1: Glosa
# MAGIC
# MAGIC | Campo | Valor |
# MAGIC |---|---|
# MAGIC | Domain | Faturamento e Glosa |
# MAGIC | Name | Glosa |
# MAGIC | Owner | você |
# MAGIC | Synonyms | glosa hospitalar, recusa de pagamento, valor glosado, taxa de glosa |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Valor de um item da conta hospitalar que a operadora se recusa a pagar, com motivo no padrão TISS. A taxa de
# MAGIC glosa oficial considera só contas já analisadas pela operadora.
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definição
# MAGIC Glosa é a recusa, total ou parcial, de um item da conta (procedimento, material, OPME, medicamento, diária ou
# MAGIC taxa) pela operadora. Cada glosa tem um motivo TISS agrupado em categoria:
# MAGIC - AUTORIZACAO — 1801: procedimento sem autorização prévia
# MAGIC - PRECO — 1705: valor acima do preço contratado (@precos_contratados)
# MAGIC - ELEGIBILIDADE — 1909: acomodação incompatível com o plano; 1301: beneficiário fora da vigência
# MAGIC - TECNICA — 1602: falta de justificativa técnica
# MAGIC - ADMINISTRATIVA — 2001: duplicidade; 2010: documentação incompleta
# MAGIC
# MAGIC Fórmulas oficiais (@mv_faturamento_glosa)
# MAGIC - Taxa de glosa = valor glosado ÷ valor faturado das contas já analisadas (status PAGA ou GLOSADA_PARCIAL).
# MAGIC   Os últimos ~2 meses ainda não foram analisados; não compare a taxa desses meses.
# MAGIC - Taxa de recuperação = valor recuperado em recurso ÷ valor glosado.
# MAGIC
# MAGIC Indicador entre visões
# MAGIC "Quanto da glosa vem de guias negadas" combina @mv_faturamento_glosa (glosa do motivo 1801) com
# MAGIC @mv_autorizacoes (taxa de negativa e glosa_sem_autorizacao, mesma operadora e período).
# MAGIC
# MAGIC Uso no negócio
# MAGIC Glosa de autorização e de preço quase nunca é revertida em recurso: o mais barato é evitá-la antes do envio
# MAGIC (checar guia, preço vigente e acomodação). Veja @Autorização prévia e @Acomodação do plano.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `mv_faturamento_glosa`, `mv_autorizacoes`, `fato_itens_faturados`, `glosas`, `motivos_glosa`, `recursos_glosa`
# MAGIC
# MAGIC **Sources (optional):** Padrão TISS (ANS); sistema de faturamento (schema `faturamento` da origem).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 2: Autorização prévia
# MAGIC
# MAGIC | Campo | Valor |
# MAGIC |---|---|
# MAGIC | Domain | Autorização Prévia |
# MAGIC | Name | Autorização prévia |
# MAGIC | Owner | você |
# MAGIC | Synonyms | guia, guia de autorização, senha, pré-autorização, negativa, taxa de negativa |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Pedido do hospital à operadora para executar um procedimento que exige aprovação antes. Guia negada e
# MAGIC executada vira glosa 1801.
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definição
# MAGIC Procedimentos com exige_autorizacao = true em @procedimentos (ressonância, cirurgias, OPME, quimioterapia) só
# MAGIC podem ser executados com guia aprovada (@autorizacoes). Status da guia: APROVADA, NEGADA ou PENDENTE.
# MAGIC
# MAGIC Fórmulas oficiais (@mv_autorizacoes)
# MAGIC - Taxa de negativa = guias negadas ÷ guias respondidas (pendentes ficam fora).
# MAGIC - Tempo de resposta = horas entre a solicitação e a resposta da operadora.
# MAGIC
# MAGIC Caminhos
# MAGIC - Até o dinheiro: guia → atendimento (autorizacao_id) → conta → itens → glosa 1801.
# MAGIC - Até a experiência: guia → protocolo da central (autorizacao_id) → pesquisa de satisfação.
# MAGIC
# MAGIC Uso no negócio
# MAGIC Uma alta de negativa numa operadora gera, em sequência, glosa por falta de autorização e reclamação na
# MAGIC central e na ouvidoria. Veja @Glosa e @Protocolo da central.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `mv_autorizacoes`, `fato_autorizacoes`, `autorizacoes`, `procedimentos`, `protocolos`
# MAGIC
# MAGIC **Sources (optional):** Sistema hospitalar (schema `assistencial` da origem).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 3: Acomodação do plano
# MAGIC
# MAGIC | Campo | Valor |
# MAGIC |---|---|
# MAGIC | Domain | Cadastro e Assistencial |
# MAGIC | Name | Acomodação do plano |
# MAGIC | Owner | você |
# MAGIC | Synonyms | acomodação, tipo de quarto, enfermaria, apartamento, diferença de acomodação |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Tipo de quarto (enfermaria ou apartamento) a que o beneficiário tem direito pelo plano. Diária de apartamento
# MAGIC em plano de enfermaria é glosada (1909).
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definição
# MAGIC Cada plano (@planos) define a acomodação: ENFERMARIA ou APARTAMENTO. Na internação o hospital cobra uma diária
# MAGIC por dia em @itens_conta: 80000101 = enfermaria, 80000102 = apartamento, 80000103 = UTI.
# MAGIC
# MAGIC Regra
# MAGIC Beneficiário de plano de enfermaria em apartamento, sem termo de diferença, gera glosa 1909 da diferença entre
# MAGIC as diárias. O hospital tenta cobrar a diferença do paciente, que reclama na central (assunto "Cobrança indevida
# MAGIC ao paciente").
# MAGIC
# MAGIC Como achar a acomodação de um atendimento
# MAGIC atendimento → beneficiário (a carteirinha usada no atendimento) → plano. O paciente pode ter trocado de plano:
# MAGIC use a carteirinha do atendimento, não a atual (@beneficiarios tem a vigência).
# MAGIC
# MAGIC Uso no negócio
# MAGIC Conferir a acomodação na admissão evita a glosa e a reclamação. Veja @Glosa e @Protocolo da central.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `planos`, `beneficiarios`, `itens_conta`, `mv_faturamento_glosa`, `mv_central`
# MAGIC
# MAGIC **Sources (optional):** Cadastro de planos e beneficiários (schema `cadastro` da origem).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 4: Protocolo da central
# MAGIC
# MAGIC | Campo | Valor |
# MAGIC |---|---|
# MAGIC | Domain | Central de Atendimento |
# MAGIC | Name | Protocolo da central |
# MAGIC | Owner | você |
# MAGIC | Synonyms | protocolo, contato, chamado, atendimento da central, SAC, FCR, CSAT, NPS |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Registro de um contato do paciente com a central da rede. Pode citar a guia, o atendimento ou a conta de que o
# MAGIC paciente está falando.
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definição
# MAGIC Todo contato (telefone, WhatsApp, chat, e-mail ou presencial) gera um protocolo em @protocolos, com assunto
# MAGIC (@assuntos) e área responsável. Os campos autorizacao_id, atendimento_id e conta_id ligam a experiência do
# MAGIC paciente ao hospital e ao faturamento. Parte dos protocolos resolvidos recebe pesquisa (@pesquisas_satisfacao).
# MAGIC
# MAGIC Atenção
# MAGIC "Atendimento" na central é o protocolo. "Atendimento" no hospital é @atendimentos (PS, ambulatório, internação,
# MAGIC oncologia). São coisas diferentes.
# MAGIC
# MAGIC Fórmulas oficiais (@mv_central)
# MAGIC - FCR = protocolos resolvidos no primeiro contato ÷ protocolos.
# MAGIC - CSAT = média da nota de 1 a 5.
# MAGIC - NPS = % de promotores (9–10) menos % de detratores (0–6).
# MAGIC
# MAGIC Uso no negócio
# MAGIC Reclamações de "Negativa de autorização" e "Cobrança indevida" têm o pior CSAT da central e quase sempre
# MAGIC apontam para um problema de faturamento. Veja @Autorização prévia e @Acomodação do plano.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `mv_central`, `fato_protocolos`, `protocolos`, `pesquisas_satisfacao`, `assuntos`
# MAGIC
# MAGIC **Sources (optional):** Plataforma da central (schema `relacionamento` da origem).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Page 5: Agente Ciclo de Receita
# MAGIC
# MAGIC | Campo | Valor |
# MAGIC |---|---|
# MAGIC | Domain | Faturamento e Glosa |
# MAGIC | Name | Agente Ciclo de Receita |
# MAGIC | Owner | você |
# MAGIC | Synonyms | genie do ciclo de receita, genie de faturamento, assistente de glosa |
# MAGIC
# MAGIC **Description:**
# MAGIC ```
# MAGIC Página de apresentação do Genie Agent "Ciclo de Receita — Rede Américas": o que ele responde e de quais Metric
# MAGIC Views certificadas ele parte.
# MAGIC ```
# MAGIC
# MAGIC **Body:**
# MAGIC ```
# MAGIC Definição
# MAGIC @Ciclo de Receita — Rede Américas é o Genie Agent de faturamento, glosa, autorização prévia e central de
# MAGIC atendimento. Ele responde a partir de três Metric Views certificadas: @mv_faturamento_glosa,
# MAGIC @mv_autorizacoes e @mv_central.
# MAGIC
# MAGIC Uso no negócio
# MAGIC Pergunte, por exemplo:
# MAGIC - "Por que a glosa subiu na Beta Assistência Médica?"
# MAGIC - "Quais médicos geram mais glosa por preço acima do contratado?"
# MAGIC - "Os pacientes que reclamaram de cobrança na central tinham qual plano?"
# MAGIC
# MAGIC Definições: @Glosa, @Autorização prévia, @Acomodação do plano, @Protocolo da central.
# MAGIC ```
# MAGIC
# MAGIC **Related assets:** `Ciclo de Receita — Rede Américas`, `mv_faturamento_glosa`, `mv_autorizacoes`, `mv_central`
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
