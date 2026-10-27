-- Camada PRATA (Lakeflow Spark Declarative Pipelines). GERADO por scripts/gerar_prata.py — não editar à mão.
-- Uma materialized view por tabela da origem, com tipos explícitos, comentários, PK/FK informativas (as mesmas da
-- origem) e expectations. Configuration do pipeline: catalogo, bronze, prata.

-- assistencial.atendimentos
CREATE OR REFRESH MATERIALIZED VIEW atendimentos (
  atendimento_id BIGINT NOT NULL COMMENT 'Identificador do atendimento hospitalar.',
  paciente_id BIGINT NOT NULL COMMENT 'Paciente atendido.',
  beneficiario_id BIGINT NOT NULL COMMENT 'Carteirinha usada no atendimento (define plano e operadora).',
  unidade_id STRING NOT NULL COMMENT 'Unidade do atendimento.',
  medico_responsavel_id INT NOT NULL COMMENT 'Médico responsável pelo atendimento.',
  autorizacao_id BIGINT COMMENT 'Guia que autorizou o atendimento (nula em PS e consultas).',
  cid_principal STRING NOT NULL COMMENT 'Diagnóstico principal (CID-10).',
  tipo STRING NOT NULL COMMENT 'PS, AMBULATORIAL, INTERNACAO ou ONCOLOGIA.',
  data_entrada TIMESTAMP NOT NULL COMMENT 'Data e hora de entrada.',
  data_alta TIMESTAMP COMMENT 'Data e hora da alta (nula se o paciente ainda está internado).',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT alta_apos_entrada EXPECT (data_alta IS NULL OR data_alta >= data_entrada),
  CONSTRAINT pk_atendimentos PRIMARY KEY (atendimento_id),
  CONSTRAINT fk_atendimentos_autorizacao FOREIGN KEY (autorizacao_id) REFERENCES ${catalogo}.${prata}.autorizacoes (autorizacao_id),
  CONSTRAINT fk_atendimentos_beneficiario FOREIGN KEY (beneficiario_id) REFERENCES ${catalogo}.${prata}.beneficiarios (beneficiario_id),
  CONSTRAINT fk_atendimentos_cid FOREIGN KEY (cid_principal) REFERENCES ${catalogo}.${prata}.cids (cid),
  CONSTRAINT fk_atendimentos_medico FOREIGN KEY (medico_responsavel_id) REFERENCES ${catalogo}.${prata}.medicos (medico_id),
  CONSTRAINT fk_atendimentos_paciente FOREIGN KEY (paciente_id) REFERENCES ${catalogo}.${prata}.pacientes (paciente_id),
  CONSTRAINT fk_atendimentos_unidade FOREIGN KEY (unidade_id) REFERENCES ${catalogo}.${prata}.unidades (unidade_id)
)
COMMENT 'Atendimento hospitalar (PS, ambulatorial, internação ou oncologia). Gera uma conta.'
AS SELECT CAST(b.atendimento_id AS BIGINT) AS atendimento_id,
       CAST(b.paciente_id AS BIGINT) AS paciente_id,
       CAST(b.beneficiario_id AS BIGINT) AS beneficiario_id,
       CAST(b.unidade_id AS STRING) AS unidade_id,
       CAST(b.medico_responsavel_id AS INT) AS medico_responsavel_id,
       CAST(b.autorizacao_id AS BIGINT) AS autorizacao_id,
       CAST(b.cid_principal AS STRING) AS cid_principal,
       CAST(b.tipo AS STRING) AS tipo,
       CAST(b.data_entrada AS TIMESTAMP) AS data_entrada,
       CAST(b.data_alta AS TIMESTAMP) AS data_alta,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.atendimentos b
WHERE (b.autorizacao_id IS NULL OR EXISTS (SELECT 1 FROM ${catalogo}.${prata}.autorizacoes r WHERE r.autorizacao_id = CAST(b.autorizacao_id AS BIGINT)))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.beneficiarios r WHERE r.beneficiario_id = CAST(b.beneficiario_id AS BIGINT))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.cids r WHERE r.cid = CAST(b.cid_principal AS STRING))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.medicos r WHERE r.medico_id = CAST(b.medico_responsavel_id AS INT))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.pacientes r WHERE r.paciente_id = CAST(b.paciente_id AS BIGINT))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.unidades r WHERE r.unidade_id = CAST(b.unidade_id AS STRING));

-- assistencial.autorizacoes
CREATE OR REFRESH MATERIALIZED VIEW autorizacoes (
  autorizacao_id BIGINT NOT NULL COMMENT 'Número da guia de autorização prévia.',
  beneficiario_id BIGINT NOT NULL COMMENT 'Beneficiário (carteirinha) para quem a guia foi pedida.',
  medico_solicitante_id INT NOT NULL COMMENT 'Médico que pediu a autorização.',
  unidade_id STRING NOT NULL COMMENT 'Unidade onde o procedimento seria feito.',
  procedimento_id STRING NOT NULL COMMENT 'Procedimento principal da guia.',
  data_solicitacao TIMESTAMP NOT NULL COMMENT 'Data e hora do pedido à operadora.',
  data_resposta TIMESTAMP COMMENT 'Data e hora da resposta da operadora (nula se pendente).',
  status STRING NOT NULL COMMENT 'APROVADA, NEGADA ou PENDENTE.',
  motivo_negativa STRING COMMENT 'Justificativa da operadora quando a guia é negada.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT status_valido EXPECT (status IN ('APROVADA', 'NEGADA', 'PENDENTE')),
  CONSTRAINT resposta_apos_pedido EXPECT (data_resposta IS NULL OR data_resposta >= data_solicitacao),
  CONSTRAINT pk_autorizacoes PRIMARY KEY (autorizacao_id),
  CONSTRAINT fk_autorizacoes_beneficiario FOREIGN KEY (beneficiario_id) REFERENCES ${catalogo}.${prata}.beneficiarios (beneficiario_id),
  CONSTRAINT fk_autorizacoes_medico FOREIGN KEY (medico_solicitante_id) REFERENCES ${catalogo}.${prata}.medicos (medico_id),
  CONSTRAINT fk_autorizacoes_procedimento FOREIGN KEY (procedimento_id) REFERENCES ${catalogo}.${prata}.procedimentos (procedimento_id),
  CONSTRAINT fk_autorizacoes_unidade FOREIGN KEY (unidade_id) REFERENCES ${catalogo}.${prata}.unidades (unidade_id)
)
COMMENT 'Guias de autorização prévia pedidas à operadora.'
AS SELECT CAST(b.autorizacao_id AS BIGINT) AS autorizacao_id,
       CAST(b.beneficiario_id AS BIGINT) AS beneficiario_id,
       CAST(b.medico_solicitante_id AS INT) AS medico_solicitante_id,
       CAST(b.unidade_id AS STRING) AS unidade_id,
       CAST(b.procedimento_id AS STRING) AS procedimento_id,
       CAST(b.data_solicitacao AS TIMESTAMP) AS data_solicitacao,
       CAST(b.data_resposta AS TIMESTAMP) AS data_resposta,
       CAST(b.status AS STRING) AS status,
       CAST(b.motivo_negativa AS STRING) AS motivo_negativa,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.autorizacoes b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.beneficiarios r WHERE r.beneficiario_id = CAST(b.beneficiario_id AS BIGINT))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.medicos r WHERE r.medico_id = CAST(b.medico_solicitante_id AS INT))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.procedimentos r WHERE r.procedimento_id = CAST(b.procedimento_id AS STRING))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.unidades r WHERE r.unidade_id = CAST(b.unidade_id AS STRING));

-- cadastro.beneficiarios
CREATE OR REFRESH MATERIALIZED VIEW beneficiarios (
  beneficiario_id BIGINT NOT NULL COMMENT 'Identificador do vínculo paciente × plano.',
  paciente_id BIGINT NOT NULL COMMENT 'Paciente titular da carteirinha.',
  plano_id STRING NOT NULL COMMENT 'Plano contratado.',
  numero_carteirinha STRING NOT NULL COMMENT 'Número da carteirinha do plano.',
  vigencia_inicio DATE NOT NULL COMMENT 'Início da vigência do vínculo.',
  vigencia_fim DATE COMMENT 'Fim da vigência (nulo = vigente).',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT vigencia_coerente EXPECT (vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio),
  CONSTRAINT pk_beneficiarios PRIMARY KEY (beneficiario_id),
  CONSTRAINT fk_beneficiarios_paciente FOREIGN KEY (paciente_id) REFERENCES ${catalogo}.${prata}.pacientes (paciente_id),
  CONSTRAINT fk_beneficiarios_plano FOREIGN KEY (plano_id) REFERENCES ${catalogo}.${prata}.planos (plano_id)
)
COMMENT 'Vínculo do paciente com um plano (carteirinha) num período de vigência.'
AS SELECT CAST(b.beneficiario_id AS BIGINT) AS beneficiario_id,
       CAST(b.paciente_id AS BIGINT) AS paciente_id,
       CAST(b.plano_id AS STRING) AS plano_id,
       CAST(b.numero_carteirinha AS STRING) AS numero_carteirinha,
       CAST(b.vigencia_inicio AS DATE) AS vigencia_inicio,
       CAST(b.vigencia_fim AS DATE) AS vigencia_fim,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.beneficiarios b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.pacientes r WHERE r.paciente_id = CAST(b.paciente_id AS BIGINT))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.planos r WHERE r.plano_id = CAST(b.plano_id AS STRING));

-- cadastro.cids
CREATE OR REFRESH MATERIALIZED VIEW cids (
  cid STRING NOT NULL COMMENT 'Código CID-10.',
  descricao STRING NOT NULL COMMENT 'Descrição.',
  capitulo STRING NOT NULL COMMENT 'Capítulo da CID-10.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_cids PRIMARY KEY (cid)
)
COMMENT 'Classificação Internacional de Doenças (subconjunto).'
AS SELECT CAST(b.cid AS STRING) AS cid,
       CAST(b.descricao AS STRING) AS descricao,
       CAST(b.capitulo AS STRING) AS capitulo,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.cids b;

-- cadastro.especialidades
CREATE OR REFRESH MATERIALIZED VIEW especialidades (
  especialidade_id STRING NOT NULL COMMENT 'Código da especialidade médica.',
  nome STRING NOT NULL COMMENT 'Nome.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_especialidades PRIMARY KEY (especialidade_id)
)
COMMENT 'Especialidades médicas.'
AS SELECT CAST(b.especialidade_id AS STRING) AS especialidade_id,
       CAST(b.nome AS STRING) AS nome,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.especialidades b;

-- cadastro.medicos
CREATE OR REFRESH MATERIALIZED VIEW medicos (
  medico_id INT NOT NULL COMMENT 'Identificador do médico no corpo clínico.',
  nome STRING NOT NULL COMMENT 'Nome.',
  crm STRING NOT NULL COMMENT 'Número do CRM (fictício).',
  uf_crm STRING NOT NULL COMMENT 'UF do conselho regional do CRM.',
  especialidade_id STRING NOT NULL COMMENT 'Especialidade principal do médico.',
  unidade_id STRING NOT NULL COMMENT 'Unidade onde o médico atua principalmente.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_medicos PRIMARY KEY (medico_id),
  CONSTRAINT fk_medicos_especialidade FOREIGN KEY (especialidade_id) REFERENCES ${catalogo}.${prata}.especialidades (especialidade_id),
  CONSTRAINT fk_medicos_unidade FOREIGN KEY (unidade_id) REFERENCES ${catalogo}.${prata}.unidades (unidade_id)
)
COMMENT 'Corpo clínico: um médico tem uma especialidade e uma unidade principal.'
AS SELECT CAST(b.medico_id AS INT) AS medico_id,
       CAST(b.nome AS STRING) AS nome,
       CAST(b.crm AS STRING) AS crm,
       CAST(b.uf_crm AS STRING) AS uf_crm,
       CAST(b.especialidade_id AS STRING) AS especialidade_id,
       CAST(b.unidade_id AS STRING) AS unidade_id,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.medicos b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.especialidades r WHERE r.especialidade_id = CAST(b.especialidade_id AS STRING))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.unidades r WHERE r.unidade_id = CAST(b.unidade_id AS STRING));

-- cadastro.operadoras
CREATE OR REFRESH MATERIALIZED VIEW operadoras (
  operadora_id STRING NOT NULL COMMENT 'Código da operadora de plano de saúde (fonte pagadora).',
  nome STRING NOT NULL COMMENT 'Nome.',
  registro_ans STRING NOT NULL COMMENT 'Registro da operadora na ANS (fictício).',
  prazo_pagamento_dias INT NOT NULL COMMENT 'Prazo contratual de pagamento, em dias após o envio da conta.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_operadoras PRIMARY KEY (operadora_id)
)
COMMENT 'Operadoras de plano de saúde (fontes pagadoras).'
AS SELECT CAST(b.operadora_id AS STRING) AS operadora_id,
       CAST(b.nome AS STRING) AS nome,
       CAST(b.registro_ans AS STRING) AS registro_ans,
       CAST(b.prazo_pagamento_dias AS INT) AS prazo_pagamento_dias,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.operadoras b;

-- cadastro.pacientes
CREATE OR REFRESH MATERIALIZED VIEW pacientes (
  paciente_id BIGINT NOT NULL COMMENT 'Identificador único do paciente na rede.',
  nome STRING NOT NULL COMMENT 'Nome do paciente (sintético).',
  cpf STRING NOT NULL COMMENT 'CPF do paciente (sintético, com dígitos válidos).',
  data_nascimento DATE NOT NULL COMMENT 'Data de nascimento.',
  sexo STRING NOT NULL COMMENT 'F ou M.',
  cidade STRING NOT NULL COMMENT 'Cidade.',
  uf STRING NOT NULL COMMENT 'Unidade da federação (sigla).',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_pacientes PRIMARY KEY (paciente_id)
)
COMMENT 'Pessoa física atendida pela rede (dados sintéticos). Um paciente pode ter mais de um beneficiário (troca de plano).'
AS SELECT CAST(b.paciente_id AS BIGINT) AS paciente_id,
       CAST(b.nome AS STRING) AS nome,
       CAST(b.cpf AS STRING) AS cpf,
       CAST(b.data_nascimento AS DATE) AS data_nascimento,
       CAST(b.sexo AS STRING) AS sexo,
       CAST(b.cidade AS STRING) AS cidade,
       CAST(b.uf AS STRING) AS uf,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.pacientes b;

-- cadastro.planos
CREATE OR REFRESH MATERIALIZED VIEW planos (
  plano_id STRING NOT NULL COMMENT 'Código do plano.',
  operadora_id STRING NOT NULL COMMENT 'Operadora dona do plano.',
  nome STRING NOT NULL COMMENT 'Nome.',
  segmentacao STRING NOT NULL COMMENT 'Segmentação ANS: AMBULATORIAL, HOSPITALAR ou REFERENCIA.',
  acomodacao STRING NOT NULL COMMENT 'ENFERMARIA ou APARTAMENTO: diária de apartamento em plano de enfermaria é glosada.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_planos PRIMARY KEY (plano_id),
  CONSTRAINT fk_planos_operadora FOREIGN KEY (operadora_id) REFERENCES ${catalogo}.${prata}.operadoras (operadora_id)
)
COMMENT 'Planos de cada operadora; a acomodação define se o beneficiário tem direito a enfermaria ou apartamento.'
AS SELECT CAST(b.plano_id AS STRING) AS plano_id,
       CAST(b.operadora_id AS STRING) AS operadora_id,
       CAST(b.nome AS STRING) AS nome,
       CAST(b.segmentacao AS STRING) AS segmentacao,
       CAST(b.acomodacao AS STRING) AS acomodacao,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.planos b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.operadoras r WHERE r.operadora_id = CAST(b.operadora_id AS STRING));

-- cadastro.precos_contratados
CREATE OR REFRESH MATERIALIZED VIEW precos_contratados (
  operadora_id STRING NOT NULL COMMENT 'Operadora do contrato.',
  procedimento_id STRING NOT NULL COMMENT 'Procedimento precificado.',
  vigencia_inicio DATE NOT NULL COMMENT 'Início da vigência do preço.',
  vigencia_fim DATE COMMENT 'Fim da vigência (nulo = vigente).',
  valor DECIMAL(12,2) NOT NULL COMMENT 'Preço unitário contratado, em R$.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT preco_positivo EXPECT (valor > 0),
  CONSTRAINT pk_precos_contratados PRIMARY KEY (operadora_id, procedimento_id, vigencia_inicio),
  CONSTRAINT fk_precos_operadora FOREIGN KEY (operadora_id) REFERENCES ${catalogo}.${prata}.operadoras (operadora_id),
  CONSTRAINT fk_precos_procedimento FOREIGN KEY (procedimento_id) REFERENCES ${catalogo}.${prata}.procedimentos (procedimento_id)
)
COMMENT 'Preço negociado por operadora e procedimento, com vigência.'
AS SELECT CAST(b.operadora_id AS STRING) AS operadora_id,
       CAST(b.procedimento_id AS STRING) AS procedimento_id,
       CAST(b.vigencia_inicio AS DATE) AS vigencia_inicio,
       CAST(b.vigencia_fim AS DATE) AS vigencia_fim,
       CAST(b.valor AS DECIMAL(12,2)) AS valor,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.precos_contratados b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.operadoras r WHERE r.operadora_id = CAST(b.operadora_id AS STRING))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.procedimentos r WHERE r.procedimento_id = CAST(b.procedimento_id AS STRING));

-- cadastro.procedimentos
CREATE OR REFRESH MATERIALIZED VIEW procedimentos (
  procedimento_id STRING NOT NULL COMMENT 'Código do procedimento no padrão TUSS (fictício).',
  descricao STRING NOT NULL COMMENT 'Descrição.',
  grupo STRING NOT NULL COMMENT 'CONSULTA, EXAME, PROCEDIMENTO, MATERIAL, OPME, MEDICAMENTO, DIARIA ou TAXA.',
  exige_autorizacao BOOLEAN NOT NULL COMMENT '1 = a operadora exige guia aprovada antes da execução.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_procedimentos PRIMARY KEY (procedimento_id)
)
COMMENT 'Catálogo de procedimentos, materiais, OPME, medicamentos, diárias e taxas (códigos TUSS fictícios).'
AS SELECT CAST(b.procedimento_id AS STRING) AS procedimento_id,
       CAST(b.descricao AS STRING) AS descricao,
       CAST(b.grupo AS STRING) AS grupo,
       CAST(b.exige_autorizacao AS BOOLEAN) AS exige_autorizacao,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.procedimentos b;

-- cadastro.unidades
CREATE OR REFRESH MATERIALIZED VIEW unidades (
  unidade_id STRING NOT NULL COMMENT 'Código da unidade da rede (U01 a U04).',
  nome STRING NOT NULL COMMENT 'Nome.',
  tipo STRING NOT NULL COMMENT 'HOSPITAL, ONCOLOGIA ou AMBULATORIO.',
  cidade STRING NOT NULL COMMENT 'Cidade.',
  uf STRING NOT NULL COMMENT 'Unidade da federação (sigla).',
  leitos INT COMMENT 'Leitos operacionais (nulo no ambulatório).',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_unidades PRIMARY KEY (unidade_id)
)
COMMENT 'Unidades da rede (hospitais, centro oncológico e ambulatório).'
AS SELECT CAST(b.unidade_id AS STRING) AS unidade_id,
       CAST(b.nome AS STRING) AS nome,
       CAST(b.tipo AS STRING) AS tipo,
       CAST(b.cidade AS STRING) AS cidade,
       CAST(b.uf AS STRING) AS uf,
       CAST(b.leitos AS INT) AS leitos,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.unidades b;

-- faturamento.contas
CREATE OR REFRESH MATERIALIZED VIEW contas (
  conta_id BIGINT NOT NULL COMMENT 'Identificador da conta hospitalar.',
  atendimento_id BIGINT NOT NULL COMMENT 'Atendimento faturado (uma conta por atendimento).',
  operadora_id STRING NOT NULL COMMENT 'Operadora cobrada.',
  data_fechamento DATE NOT NULL COMMENT 'Data de fechamento da conta pelo faturamento.',
  data_envio DATE COMMENT 'Data de envio à operadora (nula se a conta ainda está aberta).',
  valor_total DECIMAL(14,2) NOT NULL COMMENT 'Valor total cobrado, em R$.',
  status STRING NOT NULL COMMENT 'ABERTA, ENVIADA, PAGA ou GLOSADA_PARCIAL (já analisada, com glosa).',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT valor_nao_negativo EXPECT (valor_total >= 0),
  CONSTRAINT pk_contas PRIMARY KEY (conta_id),
  CONSTRAINT fk_contas_atendimento FOREIGN KEY (atendimento_id) REFERENCES ${catalogo}.${prata}.atendimentos (atendimento_id),
  CONSTRAINT fk_contas_operadora FOREIGN KEY (operadora_id) REFERENCES ${catalogo}.${prata}.operadoras (operadora_id)
)
COMMENT 'Conta hospitalar enviada à operadora; uma por atendimento.'
AS SELECT CAST(b.conta_id AS BIGINT) AS conta_id,
       CAST(b.atendimento_id AS BIGINT) AS atendimento_id,
       CAST(b.operadora_id AS STRING) AS operadora_id,
       CAST(b.data_fechamento AS DATE) AS data_fechamento,
       CAST(b.data_envio AS DATE) AS data_envio,
       CAST(b.valor_total AS DECIMAL(14,2)) AS valor_total,
       CAST(b.status AS STRING) AS status,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.contas b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.atendimentos r WHERE r.atendimento_id = CAST(b.atendimento_id AS BIGINT))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.operadoras r WHERE r.operadora_id = CAST(b.operadora_id AS STRING));

-- faturamento.glosas
CREATE OR REFRESH MATERIALIZED VIEW glosas (
  glosa_id BIGINT NOT NULL COMMENT 'Identificador da glosa.',
  item_id BIGINT NOT NULL COMMENT 'Item da conta glosado.',
  motivo_glosa_id STRING NOT NULL COMMENT 'Motivo informado pela operadora.',
  data_glosa DATE NOT NULL COMMENT 'Data em que a operadora comunicou a glosa.',
  valor_glosado DECIMAL(14,2) NOT NULL COMMENT 'Valor recusado pela operadora, em reais.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT glosa_positiva EXPECT (valor_glosado > 0),
  CONSTRAINT pk_glosas PRIMARY KEY (glosa_id),
  CONSTRAINT fk_glosas_item FOREIGN KEY (item_id) REFERENCES ${catalogo}.${prata}.itens_conta (item_id),
  CONSTRAINT fk_glosas_motivo FOREIGN KEY (motivo_glosa_id) REFERENCES ${catalogo}.${prata}.motivos_glosa (motivo_glosa_id)
)
COMMENT 'Valor recusado pela operadora num item da conta.'
AS SELECT CAST(b.glosa_id AS BIGINT) AS glosa_id,
       CAST(b.item_id AS BIGINT) AS item_id,
       CAST(b.motivo_glosa_id AS STRING) AS motivo_glosa_id,
       CAST(b.data_glosa AS DATE) AS data_glosa,
       CAST(b.valor_glosado AS DECIMAL(14,2)) AS valor_glosado,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.glosas b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.itens_conta r WHERE r.item_id = CAST(b.item_id AS BIGINT))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.motivos_glosa r WHERE r.motivo_glosa_id = CAST(b.motivo_glosa_id AS STRING));

-- faturamento.itens_conta
CREATE OR REFRESH MATERIALIZED VIEW itens_conta (
  item_id BIGINT NOT NULL COMMENT 'Identificador do item da conta.',
  conta_id BIGINT NOT NULL COMMENT 'Conta a que o item pertence.',
  procedimento_id STRING NOT NULL COMMENT 'Procedimento, material, medicamento, diária ou taxa cobrado.',
  medico_executante_id INT COMMENT 'Médico que executou o procedimento (nulo para materiais, diárias e taxas).',
  data_execucao DATE NOT NULL COMMENT 'Data de execução.',
  quantidade DECIMAL(8,2) NOT NULL COMMENT 'Quantidade cobrada (diárias, doses ou unidades).',
  valor_unitario DECIMAL(12,2) NOT NULL COMMENT 'Valor unitário cobrado, em R$ (compare com precos_contratados).',
  valor_total DECIMAL(14,2) NOT NULL COMMENT 'Quantidade × valor unitário, em R$.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT quantidade_positiva EXPECT (quantidade > 0),
  CONSTRAINT total_confere EXPECT (abs(valor_total - quantidade * valor_unitario) <= 0.05),
  CONSTRAINT pk_itens_conta PRIMARY KEY (item_id),
  CONSTRAINT fk_itens_conta FOREIGN KEY (conta_id) REFERENCES ${catalogo}.${prata}.contas (conta_id),
  CONSTRAINT fk_itens_medico FOREIGN KEY (medico_executante_id) REFERENCES ${catalogo}.${prata}.medicos (medico_id),
  CONSTRAINT fk_itens_procedimento FOREIGN KEY (procedimento_id) REFERENCES ${catalogo}.${prata}.procedimentos (procedimento_id)
)
COMMENT 'Itens cobrados na conta (procedimento, quantidade e valor).'
AS SELECT CAST(b.item_id AS BIGINT) AS item_id,
       CAST(b.conta_id AS BIGINT) AS conta_id,
       CAST(b.procedimento_id AS STRING) AS procedimento_id,
       CAST(b.medico_executante_id AS INT) AS medico_executante_id,
       CAST(b.data_execucao AS DATE) AS data_execucao,
       CAST(b.quantidade AS DECIMAL(8,2)) AS quantidade,
       CAST(b.valor_unitario AS DECIMAL(12,2)) AS valor_unitario,
       CAST(b.valor_total AS DECIMAL(14,2)) AS valor_total,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.itens_conta b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.contas r WHERE r.conta_id = CAST(b.conta_id AS BIGINT))
  AND (b.medico_executante_id IS NULL OR EXISTS (SELECT 1 FROM ${catalogo}.${prata}.medicos r WHERE r.medico_id = CAST(b.medico_executante_id AS INT)))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.procedimentos r WHERE r.procedimento_id = CAST(b.procedimento_id AS STRING));

-- faturamento.motivos_glosa
CREATE OR REFRESH MATERIALIZED VIEW motivos_glosa (
  motivo_glosa_id STRING NOT NULL COMMENT 'Código do motivo de glosa no padrão TISS (fictício).',
  descricao STRING NOT NULL COMMENT 'Descrição.',
  categoria STRING NOT NULL COMMENT 'AUTORIZACAO, PRECO, ELEGIBILIDADE, TECNICA ou ADMINISTRATIVA.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_motivos_glosa PRIMARY KEY (motivo_glosa_id)
)
COMMENT 'Motivos de glosa (códigos TISS fictícios) e sua categoria.'
AS SELECT CAST(b.motivo_glosa_id AS STRING) AS motivo_glosa_id,
       CAST(b.descricao AS STRING) AS descricao,
       CAST(b.categoria AS STRING) AS categoria,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.motivos_glosa b;

-- faturamento.pagamentos
CREATE OR REFRESH MATERIALIZED VIEW pagamentos (
  pagamento_id BIGINT NOT NULL COMMENT 'Identificador do pagamento.',
  conta_id BIGINT NOT NULL COMMENT 'Conta paga.',
  data_pagamento DATE NOT NULL COMMENT 'Data do crédito.',
  valor_pago DECIMAL(14,2) NOT NULL COMMENT 'Valor recebido, em R$ (valor da conta menos glosas).',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pagamento_nao_negativo EXPECT (valor_pago >= 0),
  CONSTRAINT pk_pagamentos PRIMARY KEY (pagamento_id),
  CONSTRAINT fk_pagamentos_conta FOREIGN KEY (conta_id) REFERENCES ${catalogo}.${prata}.contas (conta_id)
)
COMMENT 'Pagamento recebido da operadora por conta.'
AS SELECT CAST(b.pagamento_id AS BIGINT) AS pagamento_id,
       CAST(b.conta_id AS BIGINT) AS conta_id,
       CAST(b.data_pagamento AS DATE) AS data_pagamento,
       CAST(b.valor_pago AS DECIMAL(14,2)) AS valor_pago,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.pagamentos b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.contas r WHERE r.conta_id = CAST(b.conta_id AS BIGINT));

-- faturamento.recursos_glosa
CREATE OR REFRESH MATERIALIZED VIEW recursos_glosa (
  recurso_id BIGINT NOT NULL COMMENT 'Identificador do recurso.',
  glosa_id BIGINT NOT NULL COMMENT 'Glosa contestada.',
  data_recurso DATE NOT NULL COMMENT 'Data de envio do recurso.',
  status STRING NOT NULL COMMENT 'EM_ANALISE, ACEITO ou NEGADO.',
  valor_recuperado DECIMAL(14,2) NOT NULL COMMENT 'Valor revertido a favor do hospital, em R$.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT recuperado_nao_negativo EXPECT (valor_recuperado >= 0),
  CONSTRAINT pk_recursos_glosa PRIMARY KEY (recurso_id),
  CONSTRAINT fk_recursos_glosa FOREIGN KEY (glosa_id) REFERENCES ${catalogo}.${prata}.glosas (glosa_id)
)
COMMENT 'Recurso do hospital contra uma glosa e o valor recuperado.'
AS SELECT CAST(b.recurso_id AS BIGINT) AS recurso_id,
       CAST(b.glosa_id AS BIGINT) AS glosa_id,
       CAST(b.data_recurso AS DATE) AS data_recurso,
       CAST(b.status AS STRING) AS status,
       CAST(b.valor_recuperado AS DECIMAL(14,2)) AS valor_recuperado,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.recursos_glosa b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.glosas r WHERE r.glosa_id = CAST(b.glosa_id AS BIGINT));

-- relacionamento.assuntos
CREATE OR REFRESH MATERIALIZED VIEW assuntos (
  assunto_id STRING NOT NULL COMMENT 'Código do assunto do protocolo.',
  nome STRING NOT NULL COMMENT 'Nome.',
  area STRING NOT NULL COMMENT 'Área responsável: AUTORIZACAO, FATURAMENTO, AGENDAMENTO, RESULTADO ou OUVIDORIA.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_assuntos PRIMARY KEY (assunto_id)
)
COMMENT 'Assuntos dos protocolos da central, agrupados por área.'
AS SELECT CAST(b.assunto_id AS STRING) AS assunto_id,
       CAST(b.nome AS STRING) AS nome,
       CAST(b.area AS STRING) AS area,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.assuntos b;

-- relacionamento.canais
CREATE OR REFRESH MATERIALIZED VIEW canais (
  canal_id STRING NOT NULL COMMENT 'Código do canal: TEL, WHATSAPP, CHAT, EMAIL ou PRESENCIAL.',
  nome STRING NOT NULL COMMENT 'Nome.',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_canais PRIMARY KEY (canal_id)
)
COMMENT 'Canais da central de atendimento.'
AS SELECT CAST(b.canal_id AS STRING) AS canal_id,
       CAST(b.nome AS STRING) AS nome,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.canais b;

-- relacionamento.pesquisas_satisfacao
CREATE OR REFRESH MATERIALIZED VIEW pesquisas_satisfacao (
  pesquisa_id BIGINT NOT NULL COMMENT 'Identificador da pesquisa.',
  protocolo_id BIGINT NOT NULL COMMENT 'Protocolo avaliado.',
  data_resposta TIMESTAMP NOT NULL COMMENT 'Data e hora da resposta.',
  csat INT NOT NULL COMMENT 'Satisfação de 1 (muito insatisfeito) a 5 (muito satisfeito).',
  nps INT NOT NULL COMMENT 'Probabilidade de recomendar, de 0 a 10 (promotor 9–10, detrator 0–6).',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT csat_1_a_5 EXPECT (csat BETWEEN 1 AND 5),
  CONSTRAINT nps_0_a_10 EXPECT (nps BETWEEN 0 AND 10),
  CONSTRAINT pk_pesquisas_satisfacao PRIMARY KEY (pesquisa_id),
  CONSTRAINT fk_pesquisas_protocolo FOREIGN KEY (protocolo_id) REFERENCES ${catalogo}.${prata}.protocolos (protocolo_id)
)
COMMENT 'Pesquisa respondida após o protocolo (CSAT 1–5 e NPS 0–10).'
AS SELECT CAST(b.pesquisa_id AS BIGINT) AS pesquisa_id,
       CAST(b.protocolo_id AS BIGINT) AS protocolo_id,
       CAST(b.data_resposta AS TIMESTAMP) AS data_resposta,
       CAST(b.csat AS INT) AS csat,
       CAST(b.nps AS INT) AS nps,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.pesquisas_satisfacao b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.protocolos r WHERE r.protocolo_id = CAST(b.protocolo_id AS BIGINT));

-- relacionamento.protocolos
CREATE OR REFRESH MATERIALIZED VIEW protocolos (
  protocolo_id BIGINT NOT NULL COMMENT 'Número do protocolo da central.',
  paciente_id BIGINT NOT NULL COMMENT 'Paciente que entrou em contato.',
  canal_id STRING NOT NULL COMMENT 'Canal do contato.',
  assunto_id STRING NOT NULL COMMENT 'Assunto do contato.',
  autorizacao_id BIGINT COMMENT 'Guia citada no contato (quando houver).',
  atendimento_id BIGINT COMMENT 'Atendimento citado no contato (quando houver).',
  conta_id BIGINT COMMENT 'Conta citada no contato (quando houver).',
  data_abertura TIMESTAMP NOT NULL COMMENT 'Data e hora de abertura do protocolo.',
  data_fechamento TIMESTAMP COMMENT 'Data e hora de encerramento (nula se aberto).',
  status STRING NOT NULL COMMENT 'ABERTO, RESOLVIDO ou ESCALADO.',
  resolvido_primeiro_contato BOOLEAN NOT NULL COMMENT '1 = resolvido no primeiro contato (FCR).',
  atualizado_em TIMESTAMP NOT NULL COMMENT 'Data e hora (UTC) da última alteração do registro no sistema de origem.',
  CONSTRAINT pk_protocolos PRIMARY KEY (protocolo_id),
  CONSTRAINT fk_protocolos_assunto FOREIGN KEY (assunto_id) REFERENCES ${catalogo}.${prata}.assuntos (assunto_id),
  CONSTRAINT fk_protocolos_atendimento FOREIGN KEY (atendimento_id) REFERENCES ${catalogo}.${prata}.atendimentos (atendimento_id),
  CONSTRAINT fk_protocolos_autorizacao FOREIGN KEY (autorizacao_id) REFERENCES ${catalogo}.${prata}.autorizacoes (autorizacao_id),
  CONSTRAINT fk_protocolos_canal FOREIGN KEY (canal_id) REFERENCES ${catalogo}.${prata}.canais (canal_id),
  CONSTRAINT fk_protocolos_conta FOREIGN KEY (conta_id) REFERENCES ${catalogo}.${prata}.contas (conta_id),
  CONSTRAINT fk_protocolos_paciente FOREIGN KEY (paciente_id) REFERENCES ${catalogo}.${prata}.pacientes (paciente_id)
)
COMMENT 'Contato do paciente com a central; pode citar uma autorização, um atendimento ou uma conta.'
AS SELECT CAST(b.protocolo_id AS BIGINT) AS protocolo_id,
       CAST(b.paciente_id AS BIGINT) AS paciente_id,
       CAST(b.canal_id AS STRING) AS canal_id,
       CAST(b.assunto_id AS STRING) AS assunto_id,
       CAST(b.autorizacao_id AS BIGINT) AS autorizacao_id,
       CAST(b.atendimento_id AS BIGINT) AS atendimento_id,
       CAST(b.conta_id AS BIGINT) AS conta_id,
       CAST(b.data_abertura AS TIMESTAMP) AS data_abertura,
       CAST(b.data_fechamento AS TIMESTAMP) AS data_fechamento,
       CAST(b.status AS STRING) AS status,
       CAST(b.resolvido_primeiro_contato AS BOOLEAN) AS resolvido_primeiro_contato,
       CAST(b.atualizado_em AS TIMESTAMP) AS atualizado_em
FROM ${catalogo}.${bronze}.protocolos b
WHERE EXISTS (SELECT 1 FROM ${catalogo}.${prata}.assuntos r WHERE r.assunto_id = CAST(b.assunto_id AS STRING))
  AND (b.atendimento_id IS NULL OR EXISTS (SELECT 1 FROM ${catalogo}.${prata}.atendimentos r WHERE r.atendimento_id = CAST(b.atendimento_id AS BIGINT)))
  AND (b.autorizacao_id IS NULL OR EXISTS (SELECT 1 FROM ${catalogo}.${prata}.autorizacoes r WHERE r.autorizacao_id = CAST(b.autorizacao_id AS BIGINT)))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.canais r WHERE r.canal_id = CAST(b.canal_id AS STRING))
  AND (b.conta_id IS NULL OR EXISTS (SELECT 1 FROM ${catalogo}.${prata}.contas r WHERE r.conta_id = CAST(b.conta_id AS BIGINT)))
  AND EXISTS (SELECT 1 FROM ${catalogo}.${prata}.pacientes r WHERE r.paciente_id = CAST(b.paciente_id AS BIGINT));
