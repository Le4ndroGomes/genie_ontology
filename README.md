# Genie Ontology — Rede Américas (ciclo de receita)

Demo do **Genie One** apoiado numa **Genie Ontology** modelada à mão: Metric Views, domínios, Pages e certificação,
camadas de semântica do Unity Catalog. A base é um banco relacional de verdade, um Azure SQL com 22 tabelas e 33 FKs,
ingerido com **Lakeflow Connect** e tratado num medalhão SDP. O caso é o ciclo de receita da Rede Américas:
faturamento, glosa, autorização prévia e central de atendimento. Os dados são 100% sintéticos, e as histórias
plantadas só aparecem cruzando domínios. A estrutura é adaptada de
[databeli/genie_ontology](https://github.com/databeli/genie_ontology): os notebooks 00–06 têm o mesmo papel; só o 01
muda, porque aqui os dados vêm da origem relacional em vez de serem gerados no notebook.

## Como as peças se encaixam

- **Genie One** é o chat de linguagem natural em tela cheia da Databricks. A cada pergunta ele procura primeiro nos
  **Genie Agents** e depois em dashboards, queries e Metric Views, respondendo com a **Genie Ontology**:
  - *Contexto modelado*: Metric Views, domínios e Pages, curados e certificados por pessoas. É o que esta demo constrói.
  - *Contexto inferido*: metadados, uso e frescor, extraídos automaticamente dos ativos existentes.
  - Cada trecho de resposta recebe um *authority score* (origem, uso, frescor), e as respostas respeitam as
    permissões de quem pergunta.
- **Metric Views** definem as medidas uma vez (taxa de glosa, taxa de negativa, CSAT…), separadas das dimensões, e
  são consultadas como tabelas no SQL, em notebooks, dashboards e no Genie.
- **Domínios** são uma camada de navegação apoiada num governed tag: os ativos marcados aparecem agrupados por
  finalidade de negócio na página Discover.
- **Pages** são definições governadas de um termo, KPI ou conceito, com ativos relacionados e corpo em rich text.
  O Genie One lê as Pages publicadas como contexto autoritativo, à frente do contexto inferido.
- **Certificação** (`certified` / `deprecated`) vale para tabelas, views, Genie Agents e outros objetos. Ativos
  certificados sobem no ranking das respostas do Genie One.
- **PK/FK informativas e comentários** na prata dizem ao Genie como as 22 tabelas se ligam e o que cada coluna significa.

Documentação: [Genie One chat](https://docs.databricks.com/aws/en/genie-one/chat) ·
[Genie Ontology](https://docs.databricks.com/aws/en/genie/genie-ontology) ·
[UC semantics](https://docs.databricks.com/aws/en/uc-semantics/) ·
[Metric Views](https://docs.databricks.com/aws/en/uc-semantics/metric-views/) ·
[Domínios](https://docs.databricks.com/aws/en/uc-semantics/domains) ·
[Pages](https://docs.databricks.com/aws/en/uc-semantics/pages) ·
[Certificação](https://docs.databricks.com/aws/en/data-governance/unity-catalog/certify-deprecate-data)

## Pré-requisitos

- Workspace `<seu-workspace>`. Com compute clássico, use o gateway do Lakeflow Connect (UI). Em workspace **só
  serverless**, use o **Integrated CDC** (sem gateway, criado por API na célula B'.1 do notebook 01; precisa do recurso
  habilitado e do IP de saída do serverless no firewall do SQL).
- Catálogo de destino **sem Default Storage**: o Lakeflow Connect recusa catálogos com Default Storage. Em workspace
  serverless, crie o catálogo com `MANAGED LOCATION` numa external location.
- Catálogo `rede_americas_demo`, com `USE CATALOG` e `CREATE SCHEMA`. Os schemas são criados pelo notebook 01.
- Na conexão: `CREATE CONNECTION` no metastore (ou `USE CONNECTION` numa conexão existente para o mesmo servidor).
- SQL warehouse serverless, com `CAN USE` para quem vai usar o Genie One.
- **Pages** estão em Beta: um account admin habilita em *Account console → Previews*. A **Genie Ontology** está em
  Public Preview, sem custo de curadoria hoje.
- Para criar domínios: `MANAGE DISCOVER` na conta (admins têm) ou `MANAGE` no domínio.

## Conteúdo do repo

| Arquivo | O que faz | Como roda |
|---|---|---|
| [`00_config.py`](00_config.py) | Widgets de catálogo e prefixo dos schemas (`ontologia_staging/bronze/prata/ouro`), lidos pelos outros notebooks com `%run` | Não roda sozinho |
| [`01_ingestao_e_medalhao.py`](01_ingestao_e_medalhao.py) | Passos de UI do Lakeflow Connect e do pipeline do medalhão, mais células que criam os schemas e conferem bronze, prata (PK/FK, comentários) e ouro | **Databricks**, junto com a UI |
| [`02_create_metric_views.py`](02_create_metric_views.py) | Cria as 3 Metric Views (YAML 1.1 com `display_name`, `synonyms` e `comment`) e valida as três histórias | **Databricks** |
| [`03_genie_agent_setup.py`](03_genie_agent_setup.py) | Nome, descrição, instruções, perguntas e SQL de exemplo para o formulário *Create Agent* | Só leitura |
| [`04_apply_certification_and_domains.py`](04_apply_certification_and_domains.py) | Certifica e marca o domínio de 28 ativos (22 tabelas da prata, 3 fatos e 3 Metric Views) via `SET TAGS` / `SET TAG` | **Databricks** |
| [`05_pages_content.py`](05_pages_content.py) | Conteúdo das 5 Pages, nos campos do formulário da UI | Só leitura |
| [`06_cleanup_delete_all_assets.py`](06_cleanup_delete_all_assets.py) | Apaga os 4 schemas `ontologia_*`, com a trava `DELETE`. Não apaga o catálogo, que é compartilhado | **Databricks** |
| [`pipeline/01_prata_so_pk.sql`](pipeline/01_prata_so_pk.sql) | Prata, **fase 1**: 22 materialized views com PK, sem FK | Código do pipeline `ont_medalhao` |
| [`pipeline/01_prata.sql`](pipeline/01_prata.sql) | Prata, **fase 2**: as mesmas 22, com as 33 FKs | Código do pipeline (substitui o da fase 1) |
| [`pipeline/02_ouro.sql`](pipeline/02_ouro.sql) | Ouro: `fato_itens_faturados`, `fato_autorizacoes`, `fato_protocolos` | Código do pipeline (nas duas fases) |
| [`scripts/gerar_prata.py`](scripts/gerar_prata.py) + `scripts/origem_metadados.json` | Gera os dois `01_prata*.sql` a partir do catálogo da origem (tipos, PK, FK, descrições) | Local: `python3 gerar_prata.py [--sem-fk]` |
| `azure_sql/01_ddl.sql` | 4 schemas, 22 tabelas, 33 FKs, descrições em `MS_Description` | `sqlcmd` como administrador |
| `azure_sql/gerar_dados.py` → `02_dados.sql` | Dados sintéticos (seed 42, nov/2025–out/2026), cerca de 90 mil linhas | Local: `python3 gerar_dados.py`, depois `sqlcmd` |
| `azure_sql/lakeflow_utility_script.sql` + `03_preparar_lakeflow_connect.sql` | Utility script v1.7, USER `dbx_ingest`, change tracking e permissões | `sqlcmd` como administrador |

A pasta `azure_sql/` cria a origem do zero (passo 0 do `ROTEIRO.md`). Rode `azure_sql/00_login_master.sql` no `master` antes do resto.

## A origem

| Item | Valor |
|---|---|
| Servidor | `<seu-servidor>.database.windows.net` (testado em Azure SQL Database; qualquer SQL Server com change tracking serve) |
| Banco | `rede_americas_ontologia`: GP serverless 1 vCore, pausa sozinho após 60 min (a primeira conexão depois disso leva ~1 min) |
| Usuário de ingestão | `dbx_ingest`: login do servidor com USER em `master` e no banco (`00_login_master.sql` + `03_preparar_lakeflow_connect.sql`). Guarde a senha num cofre |
| Change tracking | ligado nas 22 tabelas, retenção de 7 dias, com objetos de DDL do utility script v1.7 (`dbo.lakeflowDdlAudit_1_7`) |
| Firewall | libere o IP de saída (NAT) do compute clássico do workspace e o IP da sua máquina |

| Schema (sistema de origem) | Tabelas |
|---|---|
| `cadastro` (mestre) | unidades (4), especialidades (8), medicos (61), operadoras (5), planos (10), pacientes (4.000), beneficiarios (4.364), procedimentos (31), precos_contratados (186), cids (22) |
| `assistencial` (hospital) | autorizacoes (2.312), atendimentos (8.528) |
| `faturamento` | contas (8.443), itens_conta (34.010), motivos_glosa (7), glosas (664), recursos_glosa (372), pagamentos (7.502) |
| `relacionamento` (central) | canais (5), assuntos (8), protocolos (8.848), pesquisas_satisfacao (2.080) |

Os nomes de tabela não se repetem entre os schemas, então as 22 cabem num único schema de destino.

O caminho que a ontologia precisa percorrer:

```
paciente ─┬─ beneficiario ── plano ── operadora ── precos_contratados ── procedimento
          ├─ atendimento ── conta ── itens_conta ── glosa ── recurso_glosa
          │        └─ autorizacao (guia)            └─ motivo_glosa
          └─ protocolo (central) ── cita autorizacao | atendimento | conta ── pesquisa_satisfacao
```

<details><summary>As 33 chaves estrangeiras da origem</summary>

| Tabela | Coluna | Referencia |
|---|---|---|
| assistencial.atendimentos | autorizacao_id | assistencial.autorizacoes |
| assistencial.atendimentos | beneficiario_id | cadastro.beneficiarios |
| assistencial.atendimentos | cid_principal | cadastro.cids |
| assistencial.atendimentos | medico_responsavel_id | cadastro.medicos |
| assistencial.atendimentos | paciente_id | cadastro.pacientes |
| assistencial.atendimentos | unidade_id | cadastro.unidades |
| assistencial.autorizacoes | beneficiario_id | cadastro.beneficiarios |
| assistencial.autorizacoes | medico_solicitante_id | cadastro.medicos |
| assistencial.autorizacoes | procedimento_id | cadastro.procedimentos |
| assistencial.autorizacoes | unidade_id | cadastro.unidades |
| cadastro.beneficiarios | paciente_id | cadastro.pacientes |
| cadastro.beneficiarios | plano_id | cadastro.planos |
| cadastro.medicos | especialidade_id | cadastro.especialidades |
| cadastro.medicos | unidade_id | cadastro.unidades |
| cadastro.planos | operadora_id | cadastro.operadoras |
| cadastro.precos_contratados | operadora_id | cadastro.operadoras |
| cadastro.precos_contratados | procedimento_id | cadastro.procedimentos |
| faturamento.contas | atendimento_id | assistencial.atendimentos |
| faturamento.contas | operadora_id | cadastro.operadoras |
| faturamento.glosas | item_id | faturamento.itens_conta |
| faturamento.glosas | motivo_glosa_id | faturamento.motivos_glosa |
| faturamento.itens_conta | conta_id | faturamento.contas |
| faturamento.itens_conta | medico_executante_id | cadastro.medicos |
| faturamento.itens_conta | procedimento_id | cadastro.procedimentos |
| faturamento.pagamentos | conta_id | faturamento.contas |
| faturamento.recursos_glosa | glosa_id | faturamento.glosas |
| relacionamento.pesquisas_satisfacao | protocolo_id | relacionamento.protocolos |
| relacionamento.protocolos | assunto_id | relacionamento.assuntos |
| relacionamento.protocolos | atendimento_id | assistencial.atendimentos |
| relacionamento.protocolos | autorizacao_id | assistencial.autorizacoes |
| relacionamento.protocolos | canal_id | relacionamento.canais |
| relacionamento.protocolos | conta_id | faturamento.contas |
| relacionamento.protocolos | paciente_id | cadastro.pacientes |

`precos_contratados` tem PK composta: `(operadora_id, procedimento_id, vigencia_inicio)`.
</details>

## Camadas no Unity Catalog

| Schema | Conteúdo | Quem cria |
|---|---|---|
| `ontologia_staging` | Volume de staging e event log da ingestão | Lakeflow Connect |
| `ontologia_bronze` | Cópia fiel das 22 tabelas (SCD tipo 1) | Lakeflow Connect |
| `ontologia_prata` | 22 materialized views tipadas, com `NOT NULL`, `COMMENT` de tabela e coluna, PK/FK informativas, expectations e filtro de integridade referencial | Pipeline `ont_medalhao` |
| `ontologia_ouro` | 3 fatos desnormalizados e 3 Metric Views | Pipeline `ont_medalhao` + notebook 02 |

### Metric Views

1. **`mv_faturamento_glosa`**, sobre `fato_itens_faturados` (grão: item da conta). Medidas: faturado,
   faturado já analisado, glosado, `taxa_glosa` (só contas analisadas), itens glosados, recuperado,
   `taxa_recuperacao`, `sobrepreco` (cobrado acima do preço contratado vigente) e contas. Dimensões: mês, operadora,
   plano, acomodação, unidade, médico, especialidade, tipo de atendimento, grupo e procedimento, motivo e categoria
   da glosa.
2. **`mv_autorizacoes`**, sobre `fato_autorizacoes` (grão: guia). Medidas: guias, guias negadas, `taxa_negativa`,
   tempo médio de resposta, negadas e atendidas mesmo assim, glosa por falta de autorização e reclamações na central.
3. **`mv_central`**, sobre `fato_protocolos` (grão: protocolo). Medidas: protocolos, `taxa_fcr`, `csat_medio`, `nps`,
   pesquisas respondidas e tempo médio até fechar. Dimensões: mês, canal, assunto, área, operadora, plano e
   acomodação do paciente na data do contato.

> **Indicadores entre fatos não viram medida.** "Quanto da glosa vem de guias negadas" precisa de
> `mv_faturamento_glosa` e `mv_autorizacoes` juntas, e uma Metric View só agrega a própria fonte. A combinação está
> documentada na Page "Glosa" e nas instruções do agente. É o mesmo padrão do "Customer Return Rate" do repo original.

### Genie Agent

**`Ciclo de Receita — Rede Américas`**: um agente com **só as 3 Metric Views** como fontes, mais instruções e
perguntas de exemplo. O texto para colar está em [`03_genie_agent_setup.py`](03_genie_agent_setup.py).

### Domínios (4, sem subdomínios)

O governed tag de cada domínio é um tag sem valor cuja chave é o nome exato do domínio, acentos incluídos. Crie os 4
na UI com estes nomes, e o notebook 04 marca o resto.

| Domínio | Ativos |
|---|---|
| `Faturamento e Glosa` | prata: operadoras, planos, procedimentos, precos_contratados, contas, itens_conta, motivos_glosa, glosas, recursos_glosa, pagamentos · ouro: fato_itens_faturados, fato_autorizacoes, mv_faturamento_glosa, mv_autorizacoes · Genie Agent (à mão) |
| `Autorização Prévia` | prata: procedimentos, autorizacoes · ouro: fato_autorizacoes, mv_autorizacoes |
| `Central de Atendimento` | prata: canais, assuntos, protocolos, pesquisas_satisfacao · ouro: fato_protocolos, mv_central |
| `Cadastro e Assistencial` | prata: unidades, especialidades, medicos, pacientes, cids, operadoras, planos, beneficiarios, procedimentos, atendimentos |

Um ativo pode estar em mais de um domínio; `procedimentos`, por exemplo, está em três.

### Pages (5)

O conteúdo completo, nos campos do formulário, está em [`05_pages_content.py`](05_pages_content.py):

| Page | Domínio | Para que serve |
|---|---|---|
| Glosa | Faturamento e Glosa | Motivos TISS por categoria, fórmula oficial da taxa de glosa (só contas analisadas), indicador entre visões |
| Autorização prévia | Autorização Prévia | Taxa de negativa, caminho guia → glosa 1801 e guia → central |
| Acomodação do plano | Cadastro e Assistencial | Enfermaria × apartamento, glosa 1909, usar a carteirinha do atendimento |
| Protocolo da central | Central de Atendimento | FCR, CSAT, NPS; "atendimento" da central ≠ atendimento hospitalar |
| Agente Ciclo de Receita | Faturamento e Glosa | Apresentação do agente, perguntas de exemplo, links para as Metric Views |

### Certificação

As 22 tabelas da prata, os 3 fatos e as 3 Metric Views recebem `system.certification_status = certified` via SQL
no notebook 04. O Genie Agent é certificado à mão (menu ⋮ → **Assign certification**), porque não há alvo SQL para
esse objeto. O bronze não é certificado: é a cópia da origem, não a camada de consumo.

## Histórias plantadas (validadas em 26/10/2026)

Nenhuma se responde com uma tabela só.

| # | História | Caminho | Números |
|---|---|---|---|
| O1 | A Beta passa a negar RM de joelho, artroscopia e artroplastia a partir de mai/2026; parte dos pacientes é atendida mesmo assim | protocolo → autorizacao → beneficiario → plano → operadora; atendimento → conta → item → glosa | Negativa da Beta: 3,0% → 37,8% (demais operadoras ≤ 5,2%). Glosa 1801 "sem autorização": 70 itens, R$ 381,9 mil, o maior motivo. Na central: 98 protocolos "Negativa de autorização" (CSAT 1,70) e 30 na ouvidoria (CSAT 1,50) |
| O2 | Dr. Ricardo Menezes Prado (ortopedia, Américas Sul) cobra OPME 25% acima do contratado desde fev/2026 | medico → atendimento → item → precos_contratados → glosa | Único médico com glosa 1705 "acima do contratado": 49 glosas, R$ 152,4 mil, igual ao sobrepreço medido pela Metric View |
| O3 | Plano Delta Essencial (enfermaria) internado no Américas Centro recebe diária de apartamento | paciente → beneficiario → plano (acomodação) → item → glosa → protocolo | Diária de apartamento em 46,8% dessas internações (demais combinações ≤ 4,4%). Glosa 1909: 65 itens, R$ 123,2 mil. 66 protocolos "Cobrança indevida", 36 deles do Delta Essencial (CSAT 2,13) |

Totais: R$ 36,9 mi faturados e R$ 1,06 mi glosados. Taxa de glosa por operadora, nas contas analisadas:
Delta 4,7%, Beta 3,7%, Gama 3,0%, Alfa 2,5% e Épsilon 1,7%. As glosas de fundo (1301, 1602, 2001 e 2010,
cerca de 1,5% dos itens) são ruído aleatório.

## Ordem de construção

O clique a clique está em [`ROTEIRO.md`](ROTEIRO.md).

1. **Importe esta pasta** como pasta do workspace ou Git folder.
2. **Notebook 01, célula B.1**: cria os schemas.
3. **Lakeflow Connect na UI**: conexão, gateway `ont_gateway` e pipeline `ont_ingestao` → `ontologia_bronze`.
   Depois rode a célula **B.2**, que confere as 22 contagens.
4. **Pipeline `ont_medalhao` na UI, em duas fases**:
   - fase 1 com `01_prata_so_pk.sql` + `02_ouro.sql`;
   - fase 2 trocando para `01_prata.sql`.
   
   Rode a célula **C.1** depois de cada fase. O esperado é 22 PKs na fase 1, e 22 PKs + 33 FKs na fase 2.
5. **Notebook 02**: cria as Metric Views e valida as histórias.
6. **Crie os 4 domínios na UI** (Discover → Create domain), com os nomes exatos `Faturamento e Glosa`,
   `Autorização Prévia`, `Central de Atendimento` e `Cadastro e Assistencial`.
7. **Crie o Genie Agent** com o texto do notebook 03. Certifique-o e coloque-o no domínio `Faturamento e Glosa` à mão.
8. **Notebook 04**: certificação e domínio de todas as tabelas e Metric Views.
9. **Crie e publique as 5 Pages** com o conteúdo do notebook 05.
10. **Abra o Genie One** e siga o roteiro da demo abaixo.
11. Para recomeçar: apague os pipelines na UI e rode o **notebook 06**. Agente, domínios e Pages saem à mão.

## O que é scriptável e o que é só UI

| Item | Automatizável? |
|---|---|
| Banco de origem (DDL, dados, change tracking, permissões) | Sim: `azure_sql/` |
| Conexão, gateway e pipeline do Lakeflow Connect | Workspace com compute clássico: UI (gateway). Workspace só serverless: Integrated CDC por API (célula B'.1 do notebook 01); a UI ainda não cria esse tipo |
| Pipeline do medalhão | Criação na UI; o SQL está em `pipeline/` (gerado por `scripts/gerar_prata.py`) |
| Schemas e conferências | Sim: notebook 01 |
| Metric Views com metadados semânticos | Sim: notebook 02 |
| Certificação e domínio das tabelas e Metric Views | Sim: notebook 04 |
| Domínio em si (criar e publicar no Discover) | Não: UI |
| Genie Agent (criar e anexar fontes) | Não: UI |
| Certificação e domínio do Genie Agent | Não: UI, sem alvo SQL |
| Pages | Não: UI, sem API pública confirmada |
| Apagar ativos SQL | Sim: notebook 06 |
| Apagar pipelines, agente, domínios e Pages | Não: UI |

## Roteiro da demo

No Genie One, faça as perguntas abaixo e confira o painel de fontes de cada resposta:

| Pergunta | Resposta esperada | Camada da ontologia |
|---|---|---|
| Por que a glosa subiu na Beta? | Negativa de RM, artroscopia e artroplastia da Beta foi de ~3,0% a ~37,8% desde mai/2026; a glosa 1801 é o maior motivo (R$ 381,9 mil) | Agente + `mv_faturamento_glosa` + `mv_autorizacoes`; Page "Glosa" (indicador entre visões) |
| Quais médicos geram mais glosa por preço? | Dr. Ricardo Menezes Prado (ortopedia, Américas Sul): 49 glosas, R$ 152,4 mil, OPME 25% acima do contratado | `mv_faturamento_glosa` (medida `sobrepreco`) |
| Os pacientes que reclamaram de cobrança na central tinham qual plano? | Delta Essencial (enfermaria): 36 dos 66 protocolos, internados no Américas Centro com diária de apartamento | `mv_central` + Page "Acomodação do plano" |
| O que é taxa de glosa? | A definição da Page "Glosa": glosado ÷ faturado das contas já analisadas | **Page** + Metric View |
| Qual o CSAT de quem reclamou de negativa de autorização? | 1,70 (e 1,50 na ouvidoria), contra 4,26–4,29 nos agendamentos | `mv_central` + Page "Protocolo da central" |

Faça uma das perguntas **antes** de certificar e marcar os domínios e repita **depois**. A diferença no ranking das
fontes mostra o efeito do *authority score*.

## Lições (testadas em 26/10/2026)

- **O SDP grava PK e FK de todas as materialized views em paralelo, no fim do update.**
  - Se a FK chega antes da PK da tabela-pai, o update falha com `UC_REFERENTIAL_CONSTRAINT_DOES_NOT_EXIST`.
  - O `WHERE EXISTS` da prata ordena os flows, mas não resolve isso.
  - A solução é rodar em duas fases: a primeira só com PK (`01_prata_so_pk.sql`), a segunda com as FKs.
  - Depois disso, execuções normais e *full refresh* ficam estáveis.
- **`EXPECT` vem antes de `PRIMARY KEY` / `FOREIGN KEY`** na lista do schema da MV. Na ordem inversa, dá `PARSE_SYNTAX_ERROR`.
- **`ALTER TABLE ... ADD CONSTRAINT` não funciona em MV de pipeline** ("expects a table but ... is a view"). As
  chaves têm de estar na definição da MV.
- **`SET TAGS` e `SET TAG` funcionam** em MVs do pipeline e em Metric Views, inclusive com acento no nome do domínio,
  e os tags sobrevivem ao refresh do pipeline.
- **Recriar o pipeline sem apagar as tabelas do anterior** dá "table is already managed by pipeline". Apague os
  schemas prata e ouro antes.
- **Metric View YAML 1.1** aceitou `display_name`, `synonyms` e `comment` em dimensões e medidas.
- **Workspace só serverless não sobe o gateway** ("Only serverless compute is supported in the workspace"). O
  caminho é o **Integrated CDC** (`connector_type: "CDC"`, `serverless: true`), criado só por API, CLI, notebook ou bundle.
- **Lakeflow Connect recusa catálogo com Default Storage** ("Default Storage for Unity Catalog is not supported on
  LakeFlow Connect pipelines"). Crie o catálogo com `MANAGED LOCATION` numa external location.
- **Integrated CDC em serverless precisa do IP de saída do serverless no firewall do SQL.** Descubra-o com um
  notebook serverless lendo `https://api.ipify.org`; ele pode mudar.

## Custos e cuidados

- **Gateway (`ont_gateway`):** roda em compute clássico, ligado direto.
  - A doc recomenda não parar o gateway manualmente, porque mudanças podem se perder e as tabelas podem precisar de full refresh.
  - Como esta origem não muda, é seguro pará-lo depois da primeira carga. Se parar, religue antes de 7 dias, que é a retenção do change tracking.
- **Pipelines `ont_ingestao` e `ont_medalhao`:** são serverless e triggered, então não custam parados.
- **Banco de origem:** pausa sozinho em 60 min. Para apagá-lo:
  `az sql db delete -g <seu-resource-group> -s <seu-servidor> -n rede_americas_ontologia`.
- **Recriar o banco do zero:** rode como administrador `00_login_master.sql` (no `master`), depois `01_ddl.sql`,
  `02_dados.sql`, `lakeflow_utility_script.sql` e `03_preparar_lakeflow_connect.sql`.
