-- Camada OURO (mesmo pipeline da prata, publicada no schema ${ouro}). Três fatos desnormalizados, base das Metric Views.
-- Configuration do pipeline: catalogo, prata, ouro.

-- Grão: item da conta. Liga faturamento, glosa e recurso ao paciente, plano, operadora, unidade e médico.
CREATE OR REFRESH MATERIALIZED VIEW ${catalogo}.${ouro}.fato_itens_faturados
COMMENT 'Um registro por item de conta faturado, com glosa e recurso. Base da Metric View mv_faturamento_glosa.'
AS
WITH glosa_item AS (
  SELECT g.item_id, SUM(g.valor_glosado) AS valor_glosado, MAX_BY(g.motivo_glosa_id, g.valor_glosado) AS motivo_glosa_id,
         MIN(g.data_glosa) AS data_glosa, SUM(COALESCE(r.valor_recuperado, 0)) AS valor_recuperado,
         COUNT(r.recurso_id) AS recursos, MAX(r.status) AS status_recurso
  FROM ${catalogo}.${prata}.glosas g
  LEFT JOIN ${catalogo}.${prata}.recursos_glosa r ON r.glosa_id = g.glosa_id
  GROUP BY g.item_id
)
SELECT i.item_id, i.conta_id, c.atendimento_id, a.paciente_id, a.beneficiario_id,
       b.plano_id, pl.nome AS plano, pl.acomodacao AS acomodacao_plano,
       c.operadora_id, op.nome AS operadora,
       a.unidade_id, u.nome AS unidade,
       a.medico_responsavel_id, m.nome AS medico_responsavel, e.nome AS especialidade,
       a.tipo AS tipo_atendimento, a.cid_principal,
       i.procedimento_id, pr.descricao AS procedimento, pr.grupo AS grupo_procedimento, pr.exige_autorizacao,
       a.autorizacao_id, au.status AS status_autorizacao,
       i.data_execucao, DATE_TRUNC('MONTH', i.data_execucao)::DATE AS mes_execucao,
       c.status AS status_conta, c.status IN ('PAGA', 'GLOSADA_PARCIAL') AS conta_analisada,
       i.quantidade, i.valor_unitario, pc.valor AS valor_unitario_contratado, i.valor_total AS valor_faturado,
       COALESCE(gi.valor_glosado, 0) AS valor_glosado, gi.motivo_glosa_id, mg.descricao AS motivo_glosa,
       mg.categoria AS categoria_glosa, gi.data_glosa,
       COALESCE(gi.valor_recuperado, 0) AS valor_recuperado, gi.recursos > 0 AS recursado, gi.status_recurso
FROM ${catalogo}.${prata}.itens_conta i
JOIN ${catalogo}.${prata}.contas c ON c.conta_id = i.conta_id
JOIN ${catalogo}.${prata}.atendimentos a ON a.atendimento_id = c.atendimento_id
JOIN ${catalogo}.${prata}.beneficiarios b ON b.beneficiario_id = a.beneficiario_id
JOIN ${catalogo}.${prata}.planos pl ON pl.plano_id = b.plano_id
JOIN ${catalogo}.${prata}.operadoras op ON op.operadora_id = c.operadora_id
JOIN ${catalogo}.${prata}.unidades u ON u.unidade_id = a.unidade_id
JOIN ${catalogo}.${prata}.medicos m ON m.medico_id = a.medico_responsavel_id
JOIN ${catalogo}.${prata}.especialidades e ON e.especialidade_id = m.especialidade_id
JOIN ${catalogo}.${prata}.procedimentos pr ON pr.procedimento_id = i.procedimento_id
LEFT JOIN ${catalogo}.${prata}.autorizacoes au ON au.autorizacao_id = a.autorizacao_id
LEFT JOIN ${catalogo}.${prata}.precos_contratados pc
       ON pc.operadora_id = c.operadora_id AND pc.procedimento_id = i.procedimento_id
      AND i.data_execucao >= pc.vigencia_inicio AND (pc.vigencia_fim IS NULL OR i.data_execucao <= pc.vigencia_fim)
LEFT JOIN glosa_item gi ON gi.item_id = i.item_id
LEFT JOIN ${catalogo}.${prata}.motivos_glosa mg ON mg.motivo_glosa_id = gi.motivo_glosa_id;

-- Grão: guia de autorização. Mostra o que aconteceu depois da resposta da operadora.
CREATE OR REFRESH MATERIALIZED VIEW ${catalogo}.${ouro}.fato_autorizacoes
COMMENT 'Um registro por guia de autorização prévia: resposta da operadora, se o paciente foi atendido, glosa por falta de autorização e contatos na central. Base da Metric View mv_autorizacoes.'
AS
WITH atend AS (
  SELECT a.autorizacao_id, COUNT(*) AS atendimentos, SUM(COALESCE(g.valor, 0)) AS glosa_sem_autorizacao
  FROM ${catalogo}.${prata}.atendimentos a
  LEFT JOIN ${catalogo}.${prata}.contas c ON c.atendimento_id = a.atendimento_id
  LEFT JOIN (SELECT i.conta_id, SUM(g.valor_glosado) AS valor
             FROM ${catalogo}.${prata}.glosas g JOIN ${catalogo}.${prata}.itens_conta i ON i.item_id = g.item_id
             WHERE g.motivo_glosa_id = '1801' GROUP BY i.conta_id) g ON g.conta_id = c.conta_id
  WHERE a.autorizacao_id IS NOT NULL
  GROUP BY a.autorizacao_id
),
central AS (
  SELECT autorizacao_id, COUNT(*) AS protocolos,
         COUNT_IF(assunto_id IN ('AUT02', 'OUV01')) AS reclamacoes
  FROM ${catalogo}.${prata}.protocolos WHERE autorizacao_id IS NOT NULL GROUP BY autorizacao_id
)
SELECT au.autorizacao_id, au.beneficiario_id, b.paciente_id, b.plano_id, pl.nome AS plano,
       pl.operadora_id, op.nome AS operadora,
       au.procedimento_id, pr.descricao AS procedimento, pr.grupo AS grupo_procedimento,
       au.medico_solicitante_id, m.nome AS medico_solicitante, e.nome AS especialidade,
       au.unidade_id, u.nome AS unidade,
       au.data_solicitacao, DATE_TRUNC('MONTH', au.data_solicitacao)::DATE AS mes_solicitacao,
       au.data_resposta, au.status, au.motivo_negativa,
       (unix_timestamp(au.data_resposta) - unix_timestamp(au.data_solicitacao)) / 3600.0 AS horas_resposta,
       COALESCE(at.atendimentos, 0) > 0 AS paciente_atendido,
       COALESCE(at.glosa_sem_autorizacao, 0) AS glosa_sem_autorizacao,
       COALESCE(ce.protocolos, 0) AS protocolos_central, COALESCE(ce.reclamacoes, 0) AS reclamacoes_central
FROM ${catalogo}.${prata}.autorizacoes au
JOIN ${catalogo}.${prata}.beneficiarios b ON b.beneficiario_id = au.beneficiario_id
JOIN ${catalogo}.${prata}.planos pl ON pl.plano_id = b.plano_id
JOIN ${catalogo}.${prata}.operadoras op ON op.operadora_id = pl.operadora_id
JOIN ${catalogo}.${prata}.procedimentos pr ON pr.procedimento_id = au.procedimento_id
JOIN ${catalogo}.${prata}.medicos m ON m.medico_id = au.medico_solicitante_id
JOIN ${catalogo}.${prata}.especialidades e ON e.especialidade_id = m.especialidade_id
JOIN ${catalogo}.${prata}.unidades u ON u.unidade_id = au.unidade_id
LEFT JOIN atend at ON at.autorizacao_id = au.autorizacao_id
LEFT JOIN central ce ON ce.autorizacao_id = au.autorizacao_id;

-- Grão: protocolo da central, com o plano vigente do paciente na data do contato e o que o contato cita.
CREATE OR REFRESH MATERIALIZED VIEW ${catalogo}.${ouro}.fato_protocolos
COMMENT 'Um registro por protocolo da central de atendimento, com pesquisa de satisfação, plano e operadora do paciente na data do contato e a guia ou conta citada. Base da Metric View mv_central.'
AS
SELECT p.protocolo_id, p.paciente_id, p.canal_id, ca.nome AS canal, p.assunto_id, s.nome AS assunto, s.area,
       p.data_abertura, DATE_TRUNC('MONTH', p.data_abertura)::DATE AS mes_abertura, p.data_fechamento, p.status,
       p.resolvido_primeiro_contato,
       (unix_timestamp(p.data_fechamento) - unix_timestamp(p.data_abertura)) / 3600.0 AS horas_ate_fechamento,
       b.plano_id, pl.nome AS plano, pl.acomodacao AS acomodacao_plano, pl.operadora_id, op.nome AS operadora,
       p.autorizacao_id, au.status AS status_autorizacao, p.atendimento_id, p.conta_id,
       ps.csat, ps.nps
FROM ${catalogo}.${prata}.protocolos p
JOIN ${catalogo}.${prata}.canais ca ON ca.canal_id = p.canal_id
JOIN ${catalogo}.${prata}.assuntos s ON s.assunto_id = p.assunto_id
LEFT JOIN ${catalogo}.${prata}.beneficiarios b
       ON b.paciente_id = p.paciente_id AND CAST(p.data_abertura AS DATE) >= b.vigencia_inicio
      AND (b.vigencia_fim IS NULL OR CAST(p.data_abertura AS DATE) <= b.vigencia_fim)
LEFT JOIN ${catalogo}.${prata}.planos pl ON pl.plano_id = b.plano_id
LEFT JOIN ${catalogo}.${prata}.operadoras op ON op.operadora_id = pl.operadora_id
LEFT JOIN ${catalogo}.${prata}.autorizacoes au ON au.autorizacao_id = p.autorizacao_id
LEFT JOIN ${catalogo}.${prata}.pesquisas_satisfacao ps ON ps.protocolo_id = p.protocolo_id;
