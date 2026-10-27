-- Camada OURO (mesmo pipeline da prata, publicada no schema ${ouro}). Um fato desnormalizado, base das três Metric Views
-- (faturamento, glosas e recuperação).
-- Configuration do pipeline: catalogo, prata, ouro.

-- Grão: item da conta. Liga faturamento, glosa e recurso ao paciente, plano, operadora, unidade e médico.
CREATE OR REFRESH MATERIALIZED VIEW ${catalogo}.${ouro}.fato_itens_faturados
COMMENT 'Um registro por item de conta faturado, com glosa, recurso e preço contratado vigente. Base das Metric Views mv_faturamento, mv_glosas e mv_recuperacao. Regra: taxa de glosa usa só contas analisadas (conta_analisada = true).'
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
       DATE_TRUNC('QUARTER', i.data_execucao)::DATE AS trimestre_execucao, YEAR(i.data_execucao) AS ano_execucao,
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
