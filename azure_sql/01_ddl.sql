/* Rede Américas · Banco relacional para a demo de Genie Ontology (Azure SQL Database: rede_americas_ontologia)
   Dados 100% sintéticos. Modelo normalizado que liga as entidades de quatro sistemas de origem:
     cadastro       — mestre: pacientes, beneficiários, planos, operadoras, médicos, unidades, procedimentos, CID
     assistencial   — autorizações (guias) e atendimentos hospitalares
     faturamento    — contas, itens, glosas, recursos e pagamentos
     relacionamento — central de atendimento: protocolos e pesquisas de satisfação
   Toda tabela tem PRIMARY KEY (exigência do change tracking do Lakeflow Connect), FKs declaradas e atualizado_em.
   Os nomes de tabela são únicos entre os schemas, para caberem num único schema de destino no Unity Catalog.
   Descrições de tabela e coluna ficam em extended properties (MS_Description). */

IF SCHEMA_ID('cadastro') IS NULL EXEC('CREATE SCHEMA cadastro');
IF SCHEMA_ID('assistencial') IS NULL EXEC('CREATE SCHEMA assistencial');
IF SCHEMA_ID('faturamento') IS NULL EXEC('CREATE SCHEMA faturamento');
IF SCHEMA_ID('relacionamento') IS NULL EXEC('CREATE SCHEMA relacionamento');
GO

/* ------------------------------------------------------------------ cadastro */
CREATE TABLE cadastro.unidades (
  unidade_id     VARCHAR(4)    NOT NULL CONSTRAINT pk_unidades PRIMARY KEY,
  nome           NVARCHAR(80)  NOT NULL,
  tipo           VARCHAR(20)   NOT NULL,          -- HOSPITAL | ONCOLOGIA | AMBULATORIO
  cidade         NVARCHAR(60)  NOT NULL,
  uf             CHAR(2)       NOT NULL,
  leitos         INT           NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE cadastro.especialidades (
  especialidade_id VARCHAR(6)  NOT NULL CONSTRAINT pk_especialidades PRIMARY KEY,
  nome           NVARCHAR(60)  NOT NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE cadastro.medicos (
  medico_id      INT           NOT NULL CONSTRAINT pk_medicos PRIMARY KEY,
  nome           NVARCHAR(80)  NOT NULL,
  crm            VARCHAR(10)   NOT NULL,
  uf_crm         CHAR(2)       NOT NULL,
  especialidade_id VARCHAR(6)  NOT NULL CONSTRAINT fk_medicos_especialidade REFERENCES cadastro.especialidades,
  unidade_id     VARCHAR(4)    NOT NULL CONSTRAINT fk_medicos_unidade REFERENCES cadastro.unidades,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT uq_medicos_crm UNIQUE (crm, uf_crm)
);
CREATE TABLE cadastro.operadoras (
  operadora_id   VARCHAR(4)    NOT NULL CONSTRAINT pk_operadoras PRIMARY KEY,
  nome           NVARCHAR(80)  NOT NULL,
  registro_ans   VARCHAR(6)    NOT NULL,
  prazo_pagamento_dias INT     NOT NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE cadastro.planos (
  plano_id       VARCHAR(8)    NOT NULL CONSTRAINT pk_planos PRIMARY KEY,
  operadora_id   VARCHAR(4)    NOT NULL CONSTRAINT fk_planos_operadora REFERENCES cadastro.operadoras,
  nome           NVARCHAR(60)  NOT NULL,
  segmentacao    VARCHAR(20)   NOT NULL,          -- AMBULATORIAL | HOSPITALAR | REFERENCIA
  acomodacao     VARCHAR(12)   NOT NULL,          -- ENFERMARIA | APARTAMENTO
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE cadastro.pacientes (
  paciente_id    BIGINT        NOT NULL CONSTRAINT pk_pacientes PRIMARY KEY,
  nome           NVARCHAR(100) NOT NULL,
  cpf            CHAR(11)      NOT NULL CONSTRAINT uq_pacientes_cpf UNIQUE,
  data_nascimento DATE         NOT NULL,
  sexo           CHAR(1)       NOT NULL,          -- F | M
  cidade         NVARCHAR(60)  NOT NULL,
  uf             CHAR(2)       NOT NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE cadastro.beneficiarios (
  beneficiario_id BIGINT       NOT NULL CONSTRAINT pk_beneficiarios PRIMARY KEY,
  paciente_id    BIGINT        NOT NULL CONSTRAINT fk_beneficiarios_paciente REFERENCES cadastro.pacientes,
  plano_id       VARCHAR(8)    NOT NULL CONSTRAINT fk_beneficiarios_plano REFERENCES cadastro.planos,
  numero_carteirinha VARCHAR(20) NOT NULL CONSTRAINT uq_beneficiarios_carteirinha UNIQUE,
  vigencia_inicio DATE         NOT NULL,
  vigencia_fim   DATE          NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE cadastro.procedimentos (
  procedimento_id VARCHAR(10)  NOT NULL CONSTRAINT pk_procedimentos PRIMARY KEY,   -- código no padrão TUSS (fictício)
  descricao      NVARCHAR(120) NOT NULL,
  grupo          VARCHAR(14)   NOT NULL,          -- CONSULTA | EXAME | PROCEDIMENTO | MATERIAL | OPME | MEDICAMENTO | DIARIA | TAXA
  exige_autorizacao BIT        NOT NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE cadastro.precos_contratados (
  operadora_id   VARCHAR(4)    NOT NULL CONSTRAINT fk_precos_operadora REFERENCES cadastro.operadoras,
  procedimento_id VARCHAR(10)  NOT NULL CONSTRAINT fk_precos_procedimento REFERENCES cadastro.procedimentos,
  vigencia_inicio DATE         NOT NULL,
  vigencia_fim   DATE          NULL,
  valor          DECIMAL(12,2) NOT NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT pk_precos_contratados PRIMARY KEY (operadora_id, procedimento_id, vigencia_inicio)
);
CREATE TABLE cadastro.cids (
  cid            VARCHAR(5)    NOT NULL CONSTRAINT pk_cids PRIMARY KEY,
  descricao      NVARCHAR(120) NOT NULL,
  capitulo       NVARCHAR(60)  NOT NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

/* ------------------------------------------------------------------ assistencial */
CREATE TABLE assistencial.autorizacoes (
  autorizacao_id BIGINT        NOT NULL CONSTRAINT pk_autorizacoes PRIMARY KEY,   -- número da guia
  beneficiario_id BIGINT       NOT NULL CONSTRAINT fk_autorizacoes_beneficiario REFERENCES cadastro.beneficiarios,
  medico_solicitante_id INT    NOT NULL CONSTRAINT fk_autorizacoes_medico REFERENCES cadastro.medicos,
  unidade_id     VARCHAR(4)    NOT NULL CONSTRAINT fk_autorizacoes_unidade REFERENCES cadastro.unidades,
  procedimento_id VARCHAR(10)  NOT NULL CONSTRAINT fk_autorizacoes_procedimento REFERENCES cadastro.procedimentos,
  data_solicitacao DATETIME2(0) NOT NULL,
  data_resposta  DATETIME2(0)  NULL,
  status         VARCHAR(10)   NOT NULL,          -- APROVADA | NEGADA | PENDENTE
  motivo_negativa NVARCHAR(120) NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE assistencial.atendimentos (
  atendimento_id BIGINT        NOT NULL CONSTRAINT pk_atendimentos PRIMARY KEY,
  paciente_id    BIGINT        NOT NULL CONSTRAINT fk_atendimentos_paciente REFERENCES cadastro.pacientes,
  beneficiario_id BIGINT       NOT NULL CONSTRAINT fk_atendimentos_beneficiario REFERENCES cadastro.beneficiarios,
  unidade_id     VARCHAR(4)    NOT NULL CONSTRAINT fk_atendimentos_unidade REFERENCES cadastro.unidades,
  medico_responsavel_id INT    NOT NULL CONSTRAINT fk_atendimentos_medico REFERENCES cadastro.medicos,
  autorizacao_id BIGINT        NULL     CONSTRAINT fk_atendimentos_autorizacao REFERENCES assistencial.autorizacoes,
  cid_principal  VARCHAR(5)    NOT NULL CONSTRAINT fk_atendimentos_cid REFERENCES cadastro.cids,
  tipo           VARCHAR(14)   NOT NULL,          -- PS | AMBULATORIAL | INTERNACAO | ONCOLOGIA
  data_entrada   DATETIME2(0)  NOT NULL,
  data_alta      DATETIME2(0)  NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_atendimentos_entrada ON assistencial.atendimentos (data_entrada);
GO

/* ------------------------------------------------------------------ faturamento */
CREATE TABLE faturamento.contas (
  conta_id       BIGINT        NOT NULL CONSTRAINT pk_contas PRIMARY KEY,
  atendimento_id BIGINT        NOT NULL CONSTRAINT fk_contas_atendimento REFERENCES assistencial.atendimentos
                                         CONSTRAINT uq_contas_atendimento UNIQUE,
  operadora_id   VARCHAR(4)    NOT NULL CONSTRAINT fk_contas_operadora REFERENCES cadastro.operadoras,
  data_fechamento DATE         NOT NULL,
  data_envio     DATE          NULL,
  valor_total    DECIMAL(14,2) NOT NULL,
  status         VARCHAR(16)   NOT NULL,          -- ABERTA | ENVIADA | PAGA | GLOSADA_PARCIAL
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE faturamento.itens_conta (
  item_id        BIGINT        NOT NULL CONSTRAINT pk_itens_conta PRIMARY KEY,
  conta_id       BIGINT        NOT NULL CONSTRAINT fk_itens_conta REFERENCES faturamento.contas,
  procedimento_id VARCHAR(10)  NOT NULL CONSTRAINT fk_itens_procedimento REFERENCES cadastro.procedimentos,
  medico_executante_id INT     NULL     CONSTRAINT fk_itens_medico REFERENCES cadastro.medicos,
  data_execucao  DATE          NOT NULL,
  quantidade     DECIMAL(8,2)  NOT NULL,
  valor_unitario DECIMAL(12,2) NOT NULL,
  valor_total    DECIMAL(14,2) NOT NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_itens_conta ON faturamento.itens_conta (conta_id);
CREATE TABLE faturamento.motivos_glosa (
  motivo_glosa_id VARCHAR(4)   NOT NULL CONSTRAINT pk_motivos_glosa PRIMARY KEY,   -- código no padrão TISS (fictício)
  descricao      NVARCHAR(120) NOT NULL,
  categoria      VARCHAR(14)   NOT NULL,          -- ADMINISTRATIVA | TECNICA | AUTORIZACAO | PRECO | ELEGIBILIDADE
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE faturamento.glosas (
  glosa_id       BIGINT        NOT NULL CONSTRAINT pk_glosas PRIMARY KEY,
  item_id        BIGINT        NOT NULL CONSTRAINT fk_glosas_item REFERENCES faturamento.itens_conta,
  motivo_glosa_id VARCHAR(4)   NOT NULL CONSTRAINT fk_glosas_motivo REFERENCES faturamento.motivos_glosa,
  data_glosa     DATE          NOT NULL,
  valor_glosado  DECIMAL(14,2) NOT NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE faturamento.recursos_glosa (
  recurso_id     BIGINT        NOT NULL CONSTRAINT pk_recursos_glosa PRIMARY KEY,
  glosa_id       BIGINT        NOT NULL CONSTRAINT fk_recursos_glosa REFERENCES faturamento.glosas,
  data_recurso   DATE          NOT NULL,
  status         VARCHAR(10)   NOT NULL,          -- EM_ANALISE | ACEITO | NEGADO
  valor_recuperado DECIMAL(14,2) NOT NULL DEFAULT 0,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE faturamento.pagamentos (
  pagamento_id   BIGINT        NOT NULL CONSTRAINT pk_pagamentos PRIMARY KEY,
  conta_id       BIGINT        NOT NULL CONSTRAINT fk_pagamentos_conta REFERENCES faturamento.contas,
  data_pagamento DATE          NOT NULL,
  valor_pago     DECIMAL(14,2) NOT NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

/* ------------------------------------------------------------------ relacionamento (central) */
CREATE TABLE relacionamento.canais (
  canal_id       VARCHAR(10)   NOT NULL CONSTRAINT pk_canais PRIMARY KEY,
  nome           NVARCHAR(40)  NOT NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE relacionamento.assuntos (
  assunto_id     VARCHAR(6)    NOT NULL CONSTRAINT pk_assuntos PRIMARY KEY,
  nome           NVARCHAR(80)  NOT NULL,
  area           VARCHAR(14)   NOT NULL,          -- AUTORIZACAO | FATURAMENTO | AGENDAMENTO | RESULTADO | OUVIDORIA
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE relacionamento.protocolos (
  protocolo_id   BIGINT        NOT NULL CONSTRAINT pk_protocolos PRIMARY KEY,
  paciente_id    BIGINT        NOT NULL CONSTRAINT fk_protocolos_paciente REFERENCES cadastro.pacientes,
  canal_id       VARCHAR(10)   NOT NULL CONSTRAINT fk_protocolos_canal REFERENCES relacionamento.canais,
  assunto_id     VARCHAR(6)    NOT NULL CONSTRAINT fk_protocolos_assunto REFERENCES relacionamento.assuntos,
  autorizacao_id BIGINT        NULL     CONSTRAINT fk_protocolos_autorizacao REFERENCES assistencial.autorizacoes,
  atendimento_id BIGINT        NULL     CONSTRAINT fk_protocolos_atendimento REFERENCES assistencial.atendimentos,
  conta_id       BIGINT        NULL     CONSTRAINT fk_protocolos_conta REFERENCES faturamento.contas,
  data_abertura  DATETIME2(0)  NOT NULL,
  data_fechamento DATETIME2(0) NULL,
  status         VARCHAR(10)   NOT NULL,          -- ABERTO | RESOLVIDO | ESCALADO
  resolvido_primeiro_contato BIT NOT NULL,
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE relacionamento.pesquisas_satisfacao (
  pesquisa_id    BIGINT        NOT NULL CONSTRAINT pk_pesquisas_satisfacao PRIMARY KEY,
  protocolo_id   BIGINT        NOT NULL CONSTRAINT fk_pesquisas_protocolo REFERENCES relacionamento.protocolos
                                         CONSTRAINT uq_pesquisas_protocolo UNIQUE,
  data_resposta  DATETIME2(0)  NOT NULL,
  csat           TINYINT       NOT NULL,          -- 1 a 5
  nps            TINYINT       NOT NULL,          -- 0 a 10
  atualizado_em  DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

/* ------------------------------------------------------------------ descrições (MS_Description) */
CREATE OR ALTER PROCEDURE dbo.descrever @schema SYSNAME, @tabela SYSNAME, @coluna SYSNAME = NULL, @texto NVARCHAR(400)
AS
  IF @coluna IS NULL
    EXEC sys.sp_addextendedproperty 'MS_Description', @texto, 'SCHEMA', @schema, 'TABLE', @tabela;
  ELSE
    EXEC sys.sp_addextendedproperty 'MS_Description', @texto, 'SCHEMA', @schema, 'TABLE', @tabela, 'COLUMN', @coluna;
GO
EXEC dbo.descrever 'cadastro', 'unidades', NULL, N'Unidades da rede (hospitais, centro oncológico e ambulatório).';
EXEC dbo.descrever 'cadastro', 'especialidades', NULL, N'Especialidades médicas.';
EXEC dbo.descrever 'cadastro', 'medicos', NULL, N'Corpo clínico: um médico tem uma especialidade e uma unidade principal.';
EXEC dbo.descrever 'cadastro', 'operadoras', NULL, N'Operadoras de plano de saúde (fontes pagadoras).';
EXEC dbo.descrever 'cadastro', 'planos', NULL, N'Planos de cada operadora; a acomodação define se o beneficiário tem direito a enfermaria ou apartamento.';
EXEC dbo.descrever 'cadastro', 'pacientes', NULL, N'Pessoa física atendida pela rede (dados sintéticos). Um paciente pode ter mais de um beneficiário (troca de plano).';
EXEC dbo.descrever 'cadastro', 'beneficiarios', NULL, N'Vínculo do paciente com um plano (carteirinha) num período de vigência.';
EXEC dbo.descrever 'cadastro', 'procedimentos', NULL, N'Catálogo de procedimentos, materiais, OPME, medicamentos, diárias e taxas (códigos TUSS fictícios).';
EXEC dbo.descrever 'cadastro', 'precos_contratados', NULL, N'Preço negociado por operadora e procedimento, com vigência.';
EXEC dbo.descrever 'cadastro', 'cids', NULL, N'Classificação Internacional de Doenças (subconjunto).';
EXEC dbo.descrever 'assistencial', 'autorizacoes', NULL, N'Guias de autorização prévia pedidas à operadora.';
EXEC dbo.descrever 'assistencial', 'atendimentos', NULL, N'Atendimento hospitalar (PS, ambulatorial, internação ou oncologia). Gera uma conta.';
EXEC dbo.descrever 'faturamento', 'contas', NULL, N'Conta hospitalar enviada à operadora; uma por atendimento.';
EXEC dbo.descrever 'faturamento', 'itens_conta', NULL, N'Itens cobrados na conta (procedimento, quantidade e valor).';
EXEC dbo.descrever 'faturamento', 'motivos_glosa', NULL, N'Motivos de glosa (códigos TISS fictícios) e sua categoria.';
EXEC dbo.descrever 'faturamento', 'glosas', NULL, N'Valor recusado pela operadora num item da conta.';
EXEC dbo.descrever 'faturamento', 'recursos_glosa', NULL, N'Recurso do hospital contra uma glosa e o valor recuperado.';
EXEC dbo.descrever 'faturamento', 'pagamentos', NULL, N'Pagamento recebido da operadora por conta.';
EXEC dbo.descrever 'relacionamento', 'canais', NULL, N'Canais da central de atendimento.';
EXEC dbo.descrever 'relacionamento', 'assuntos', NULL, N'Assuntos dos protocolos da central, agrupados por área.';
EXEC dbo.descrever 'relacionamento', 'protocolos', NULL, N'Contato do paciente com a central; pode citar uma autorização, um atendimento ou uma conta.';
EXEC dbo.descrever 'relacionamento', 'pesquisas_satisfacao', NULL, N'Pesquisa respondida após o protocolo (CSAT 1–5 e NPS 0–10).';
EXEC dbo.descrever 'cadastro', 'planos', 'acomodacao', N'ENFERMARIA ou APARTAMENTO: diária de apartamento em plano de enfermaria é glosada.';
EXEC dbo.descrever 'cadastro', 'procedimentos', 'exige_autorizacao', N'1 = a operadora exige guia aprovada antes da execução.';
EXEC dbo.descrever 'assistencial', 'atendimentos', 'autorizacao_id', N'Guia que autorizou o atendimento (nula em PS e consultas).';
EXEC dbo.descrever 'faturamento', 'glosas', 'valor_glosado', N'Valor recusado pela operadora, em reais.';
EXEC dbo.descrever 'relacionamento', 'protocolos', 'resolvido_primeiro_contato', N'1 = resolvido no primeiro contato (FCR).';
GO
DROP PROCEDURE dbo.descrever;
GO
