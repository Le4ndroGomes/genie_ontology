"""Gera pipeline/01_prata.sql a partir dos metadados da origem (origem_metadados.json, extraído do Azure SQL).

Cada tabela da origem vira uma materialized view na prata com: tipos explícitos, NOT NULL, COMMENT de tabela e de
coluna, PRIMARY KEY e FOREIGN KEY informativas (as mesmas 33 FKs da origem) e expectations de qualidade.
Variáveis do pipeline (Configuration): catalogo, bronze, prata.
Uso: python3 gerar_prata.py"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).parent
META = json.loads((AQUI / "origem_metadados.json").read_text(encoding="utf-8"))
SEM_FK = "--sem-fk" in sys.argv          # variante só com PK (primeira execução do pipeline)
SAIDA = AQUI.parent / "pipeline" / ("01_prata_so_pk.sql" if SEM_FK else "01_prata.sql")

TIPO = {"bigint": "BIGINT", "int": "INT", "tinyint": "INT", "bit": "BOOLEAN", "date": "DATE", "datetime2": "TIMESTAMP",
        "char": "STRING", "varchar": "STRING", "nvarchar": "STRING"}

# Comentários de coluna (os da origem têm precedência). Chave: coluna ou tabela.coluna.
COMENTARIO = {
    "atualizado_em": "Data e hora (UTC) da última alteração do registro no sistema de origem.",
    "nome": "Nome.",
    "descricao": "Descrição.",
    "uf": "Unidade da federação (sigla).",
    "cidade": "Cidade.",
    "status": "Situação do registro.",
    "unidades.unidade_id": "Código da unidade da rede (U01 a U04).",
    "unidades.tipo": "HOSPITAL, ONCOLOGIA ou AMBULATORIO.",
    "unidades.leitos": "Leitos operacionais (nulo no ambulatório).",
    "especialidades.especialidade_id": "Código da especialidade médica.",
    "medicos.medico_id": "Identificador do médico no corpo clínico.",
    "medicos.crm": "Número do CRM (fictício).",
    "medicos.uf_crm": "UF do conselho regional do CRM.",
    "medicos.especialidade_id": "Especialidade principal do médico.",
    "medicos.unidade_id": "Unidade onde o médico atua principalmente.",
    "operadoras.operadora_id": "Código da operadora de plano de saúde (fonte pagadora).",
    "operadoras.registro_ans": "Registro da operadora na ANS (fictício).",
    "operadoras.prazo_pagamento_dias": "Prazo contratual de pagamento, em dias após o envio da conta.",
    "planos.plano_id": "Código do plano.",
    "planos.operadora_id": "Operadora dona do plano.",
    "planos.segmentacao": "Segmentação ANS: AMBULATORIAL, HOSPITALAR ou REFERENCIA.",
    "pacientes.paciente_id": "Identificador único do paciente na rede.",
    "pacientes.nome": "Nome do paciente (sintético).",
    "pacientes.cpf": "CPF do paciente (sintético, com dígitos válidos).",
    "pacientes.data_nascimento": "Data de nascimento.",
    "pacientes.sexo": "F ou M.",
    "beneficiarios.beneficiario_id": "Identificador do vínculo paciente × plano.",
    "beneficiarios.paciente_id": "Paciente titular da carteirinha.",
    "beneficiarios.plano_id": "Plano contratado.",
    "beneficiarios.numero_carteirinha": "Número da carteirinha do plano.",
    "beneficiarios.vigencia_inicio": "Início da vigência do vínculo.",
    "beneficiarios.vigencia_fim": "Fim da vigência (nulo = vigente).",
    "procedimentos.procedimento_id": "Código do procedimento no padrão TUSS (fictício).",
    "procedimentos.grupo": "CONSULTA, EXAME, PROCEDIMENTO, MATERIAL, OPME, MEDICAMENTO, DIARIA ou TAXA.",
    "precos_contratados.operadora_id": "Operadora do contrato.",
    "precos_contratados.procedimento_id": "Procedimento precificado.",
    "precos_contratados.vigencia_inicio": "Início da vigência do preço.",
    "precos_contratados.vigencia_fim": "Fim da vigência (nulo = vigente).",
    "precos_contratados.valor": "Preço unitário contratado, em R$.",
    "cids.cid": "Código CID-10.",
    "cids.capitulo": "Capítulo da CID-10.",
    "autorizacoes.autorizacao_id": "Número da guia de autorização prévia.",
    "autorizacoes.beneficiario_id": "Beneficiário (carteirinha) para quem a guia foi pedida.",
    "autorizacoes.medico_solicitante_id": "Médico que pediu a autorização.",
    "autorizacoes.unidade_id": "Unidade onde o procedimento seria feito.",
    "autorizacoes.procedimento_id": "Procedimento principal da guia.",
    "autorizacoes.data_solicitacao": "Data e hora do pedido à operadora.",
    "autorizacoes.data_resposta": "Data e hora da resposta da operadora (nula se pendente).",
    "autorizacoes.status": "APROVADA, NEGADA ou PENDENTE.",
    "autorizacoes.motivo_negativa": "Justificativa da operadora quando a guia é negada.",
    "atendimentos.atendimento_id": "Identificador do atendimento hospitalar.",
    "atendimentos.paciente_id": "Paciente atendido.",
    "atendimentos.beneficiario_id": "Carteirinha usada no atendimento (define plano e operadora).",
    "atendimentos.unidade_id": "Unidade do atendimento.",
    "atendimentos.medico_responsavel_id": "Médico responsável pelo atendimento.",
    "atendimentos.cid_principal": "Diagnóstico principal (CID-10).",
    "atendimentos.tipo": "PS, AMBULATORIAL, INTERNACAO ou ONCOLOGIA.",
    "atendimentos.data_entrada": "Data e hora de entrada.",
    "atendimentos.data_alta": "Data e hora da alta (nula se o paciente ainda está internado).",
    "contas.conta_id": "Identificador da conta hospitalar.",
    "contas.atendimento_id": "Atendimento faturado (uma conta por atendimento).",
    "contas.operadora_id": "Operadora cobrada.",
    "contas.data_fechamento": "Data de fechamento da conta pelo faturamento.",
    "contas.data_envio": "Data de envio à operadora (nula se a conta ainda está aberta).",
    "contas.valor_total": "Valor total cobrado, em R$.",
    "contas.status": "ABERTA, ENVIADA, PAGA ou GLOSADA_PARCIAL (já analisada, com glosa).",
    "itens_conta.item_id": "Identificador do item da conta.",
    "itens_conta.conta_id": "Conta a que o item pertence.",
    "itens_conta.procedimento_id": "Procedimento, material, medicamento, diária ou taxa cobrado.",
    "itens_conta.medico_executante_id": "Médico que executou o procedimento (nulo para materiais, diárias e taxas).",
    "itens_conta.data_execucao": "Data de execução.",
    "itens_conta.quantidade": "Quantidade cobrada (diárias, doses ou unidades).",
    "itens_conta.valor_unitario": "Valor unitário cobrado, em R$ (compare com precos_contratados).",
    "itens_conta.valor_total": "Quantidade × valor unitário, em R$.",
    "motivos_glosa.motivo_glosa_id": "Código do motivo de glosa no padrão TISS (fictício).",
    "motivos_glosa.categoria": "AUTORIZACAO, PRECO, ELEGIBILIDADE, TECNICA ou ADMINISTRATIVA.",
    "glosas.glosa_id": "Identificador da glosa.",
    "glosas.item_id": "Item da conta glosado.",
    "glosas.motivo_glosa_id": "Motivo informado pela operadora.",
    "glosas.data_glosa": "Data em que a operadora comunicou a glosa.",
    "recursos_glosa.recurso_id": "Identificador do recurso.",
    "recursos_glosa.glosa_id": "Glosa contestada.",
    "recursos_glosa.data_recurso": "Data de envio do recurso.",
    "recursos_glosa.status": "EM_ANALISE, ACEITO ou NEGADO.",
    "recursos_glosa.valor_recuperado": "Valor revertido a favor do hospital, em R$.",
    "pagamentos.pagamento_id": "Identificador do pagamento.",
    "pagamentos.conta_id": "Conta paga.",
    "pagamentos.data_pagamento": "Data do crédito.",
    "pagamentos.valor_pago": "Valor recebido, em R$ (valor da conta menos glosas).",
    "canais.canal_id": "Código do canal: TEL, WHATSAPP, CHAT, EMAIL ou PRESENCIAL.",
    "assuntos.assunto_id": "Código do assunto do protocolo.",
    "assuntos.area": "Área responsável: AUTORIZACAO, FATURAMENTO, AGENDAMENTO, RESULTADO ou OUVIDORIA.",
    "protocolos.protocolo_id": "Número do protocolo da central.",
    "protocolos.paciente_id": "Paciente que entrou em contato.",
    "protocolos.canal_id": "Canal do contato.",
    "protocolos.assunto_id": "Assunto do contato.",
    "protocolos.autorizacao_id": "Guia citada no contato (quando houver).",
    "protocolos.atendimento_id": "Atendimento citado no contato (quando houver).",
    "protocolos.conta_id": "Conta citada no contato (quando houver).",
    "protocolos.data_abertura": "Data e hora de abertura do protocolo.",
    "protocolos.data_fechamento": "Data e hora de encerramento (nula se aberto).",
    "protocolos.status": "ABERTO, RESOLVIDO ou ESCALADO.",
    "pesquisas_satisfacao.pesquisa_id": "Identificador da pesquisa.",
    "pesquisas_satisfacao.protocolo_id": "Protocolo avaliado.",
    "pesquisas_satisfacao.data_resposta": "Data e hora da resposta.",
    "pesquisas_satisfacao.csat": "Satisfação de 1 (muito insatisfeito) a 5 (muito satisfeito).",
    "pesquisas_satisfacao.nps": "Probabilidade de recomendar, de 0 a 10 (promotor 9–10, detrator 0–6).",
}
EXPECTATIVAS = {
    "beneficiarios": [("vigencia_coerente", "vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio")],
    "precos_contratados": [("preco_positivo", "valor > 0")],
    "autorizacoes": [("status_valido", "status IN ('APROVADA', 'NEGADA', 'PENDENTE')"),
                     ("resposta_apos_pedido", "data_resposta IS NULL OR data_resposta >= data_solicitacao")],
    "atendimentos": [("alta_apos_entrada", "data_alta IS NULL OR data_alta >= data_entrada")],
    "contas": [("valor_nao_negativo", "valor_total >= 0")],
    "itens_conta": [("quantidade_positiva", "quantidade > 0"),
                    ("total_confere", "abs(valor_total - quantidade * valor_unitario) <= 0.05")],
    "glosas": [("glosa_positiva", "valor_glosado > 0")],
    "recursos_glosa": [("recuperado_nao_negativo", "valor_recuperado >= 0")],
    "pagamentos": [("pagamento_nao_negativo", "valor_pago >= 0")],
    "pesquisas_satisfacao": [("csat_1_a_5", "csat BETWEEN 1 AND 5"), ("nps_0_a_10", "nps BETWEEN 0 AND 10")],
}


def tipo(c):
    return f"DECIMAL({c['p']},{c['s']})" if c["tipo"] == "decimal" else TIPO[c["tipo"]]


def q(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


blocos = ["""-- Camada PRATA (Lakeflow Spark Declarative Pipelines). GERADO por scripts/gerar_prata.py — não editar à mão.
-- Uma materialized view por tabela da origem, com tipos explícitos, comentários, PK/FK informativas (as mesmas da
-- origem) e expectations. Configuration do pipeline: catalogo, bronze, prata. Os nomes são completos
-- (${catalogo}.${prata}.tabela), então o catálogo e o schema padrão do pipeline não importam.
"""]
for t in META:
    nome, cols, pk = t["tabela"], t["colunas"], [c["coluna"] for c in sorted(t["pk"], key=lambda x: x["o"])]
    linhas = []
    for c in cols:
        com = c.get("descricao") or COMENTARIO.get(f"{nome}.{c['coluna']}") or COMENTARIO.get(c["coluna"])
        nn = " NOT NULL" if (not c["nulo"] or c["coluna"] in pk) else ""
        linhas.append(f"  {c['coluna']} {tipo(c)}{nn}" + (f" COMMENT {q(com)}" if com else ""))
    for n, expr in EXPECTATIVAS.get(nome, []):          # expectations antes das chaves (senão: erro de sintaxe)
        linhas.append(f"  CONSTRAINT {n} EXPECT ({expr})")
    linhas.append(f"  CONSTRAINT pk_{nome} PRIMARY KEY ({', '.join(pk)})")
    for fk in ([] if SEM_FK else sorted(t.get("fks", []), key=lambda f: f["nome"])):
        linhas.append(f"  CONSTRAINT {fk['nome']} FOREIGN KEY ({fk['coluna']}) "
                      f"REFERENCES ${{catalogo}}.${{prata}}.{fk['ref']} ({fk['ref_coluna']})")
    sel = ",\n       ".join(f"CAST(b.{c['coluna']} AS {tipo(c)}) AS {c['coluna']}" for c in cols)
    # Integridade referencial: só entram linhas cujo pai já está na prata. Além de regra de qualidade, isso faz o
    # pipeline criar o pai antes do filho; sem essa dependência o SDP grava a FK antes da PK do pai existir
    # (UC_REFERENTIAL_CONSTRAINT_DOES_NOT_EXIST).
    por_col = {c["coluna"]: c for c in cols}
    filtros = []
    for fk in sorted(t.get("fks", []), key=lambda f: f["nome"]):
        c = por_col[fk["coluna"]]
        existe = (f"EXISTS (SELECT 1 FROM ${{catalogo}}.${{prata}}.{fk['ref']} r "
                  f"WHERE r.{fk['ref_coluna']} = CAST(b.{c['coluna']} AS {tipo(c)}))")
        filtros.append(f"(b.{c['coluna']} IS NULL OR {existe})" if c["nulo"] else existe)
    where = ("\nWHERE " + "\n  AND ".join(filtros)) if filtros else ""
    blocos.append(f"-- {t['schema']}.{nome}\nCREATE OR REFRESH MATERIALIZED VIEW ${{catalogo}}.${{prata}}.{nome} (\n" + ",\n".join(linhas)
                  + f"\n)\nCOMMENT {q(t['descricao'])}\nAS SELECT {sel}\nFROM ${{catalogo}}.${{bronze}}.{nome} b{where};\n")

SAIDA.parent.mkdir(exist_ok=True)
SAIDA.write_text("\n".join(blocos), encoding="utf-8")
print(f"{SAIDA} · {len(META)} materialized views")
