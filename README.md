# Genie Ontology para faturamento hospitalar e gestão de glosas — Rede Américas

Demo de **Genie One** sobre uma **Genie Ontology** governada: Metric Views, domínios, Pages e certificação no Unity
Catalog. A origem é um SQL Server ingerido com **Lakeflow Connect**. O caso é o faturamento hospitalar e a gestão de
glosas da Rede Américas, com **dados 100% sintéticos**.

A demo mostra a diferença entre a mesma pergunta feita a um Genie **sem contexto semântico** (tabelas cruas) e a um
agente **apoiado na ontologia** (definições oficiais, regras de negócio, ativos certificados e citações).

Adaptado de [databeli/genie_ontology](https://github.com/databeli/genie_ontology): mesma sequência `00_config` →
`06_cleanup`, com o mesmo papel em cada notebook. A diferença está no 01: aqui os dados vêm de uma origem relacional,
em vez de serem gerados no notebook.

## Objetivo e contexto

A glosa é o valor que a operadora se recusa a pagar numa conta hospitalar. Medir glosa parece trivial e não é:

- A **taxa de glosa** só faz sentido sobre contas **já analisadas** pela operadora. Contas recentes ainda não tiveram
  glosa aplicada; incluí-las no denominador puxa a taxa para baixo e cria uma "queda" falsa nos últimos meses.
- A causa está em outros domínios: a guia de autorização negada, o preço contratado vigente, a acomodação do plano.

A ontologia carrega essas regras uma vez (Metric Views + Pages) e o Genie passa a responder com a definição oficial,
citando a fonte.

## Arquitetura e modelo de dados

```
SQL Server (Azure SQL, 22 tabelas, 33 FKs, change tracking)
   │  Lakeflow Connect: gateway (workspace clássico) ou Integrated CDC (workspace só serverless)
   ▼
ontologia_bronze ── cópia fiel, SCD1
   │  pipeline SDP ont_medalhao
   ▼
ontologia_prata ─── 22 MVs tipadas: PK/FK informativas, COMMENT em tabelas e colunas, 13 expectations,
   │                integridade referencial
   ▼
ontologia_ouro ──── fato_itens_faturados (grão: item da conta)
   │
   ├── mv_faturamento ─┐
   ├── mv_glosas ──────┼── Genie Agent "Faturamento e Glosas — Rede Américas" ── Genie One
   └── mv_recuperacao ─┘         + domínios, Pages e certificação (contexto modelado)
```

Relacionamentos principais da prata (FKs declaradas):

| De | Para |
|---|---|
| `itens_conta.conta_id` | `contas` |
| `contas.atendimento_id` | `atendimentos` |
| `atendimentos.beneficiario_id` → `beneficiarios.plano_id` | `planos` → `operadoras` |
| `atendimentos.medico_responsavel_id` | `medicos` → `especialidades`, `unidades` |
| `itens_conta.procedimento_id` | `procedimentos` |
| `glosas.item_id` / `glosas.motivo_glosa_id` | `itens_conta` / `motivos_glosa` |
| `recursos_glosa.glosa_id` | `glosas` |
| `precos_contratados (operadora_id, procedimento_id, vigencia_inicio)` | preço vigente por item |

As outras tabelas da origem (autorizações e central de atendimento) são ingeridas e ficam na prata, mas estão fora do
escopo desta demo.

### Metric Views (fonte: `fato_itens_faturados`)

| Metric View | Medidas | Regra de negócio |
|---|---|---|
| `mv_faturamento` | `valor_faturado`, `valor_faturado_analisado`, `contas`, `itens`, `ticket_medio_conta` | Faturado analisado = contas com status PAGA ou GLOSADA_PARCIAL |
| `mv_glosas` | `valor_glosado`, `taxa_glosa`, `itens_glosados`, `contas_glosadas`, `sobrepreco` | **taxa_glosa = glosado ÷ faturado das contas analisadas** |
| `mv_recuperacao` | `valor_recuperado`, `taxa_recuperacao`, `itens_recursados`, `taxa_recurso`, `taxa_aceite` | taxa_recuperacao = recuperado ÷ glosado |

Dimensões comuns: `mes`, `trimestre`, `ano`, `operadora`, `plano`, `acomodacao_plano`, `unidade`, `medico`,
`especialidade`, `procedimento`, `grupo_procedimento`, `tipo_atendimento`. Nas Metric Views de glosa e de
recuperação também há `motivo_glosa`, `categoria_glosa`, `status_recurso` e `conta_analisada`. Todas trazem
`display_name`, `comment` e `synonyms` (YAML 1.1).

### Ontologia

| Camada | O que é criado |
|---|---|
| Genie Agent | "Faturamento e Glosas — Rede Américas": as 3 Metric Views + instruções. Também o baseline "Faturamento — sem contexto (baseline)", só com tabelas do bronze, para o antes × depois |
| Domínios | `Faturamento Hospitalar`, `Glosas e Recuperação`, `Cadastro Assistencial` |
| Pages | "Taxa de glosa", "Glosa hospitalar", "Taxa de recuperação", "Agente Faturamento e Glosas" |
| Certificação | Prata, fato e Metric Views via `SET TAGS` (notebook 04). O agente é certificado à mão |
| Metadados | Comentários de tabela e coluna, sinônimos nas Metric Views, PK/FK na prata |

## Estrutura do repositório

| Arquivo | O que faz | Como roda |
|---|---|---|
| `00_config.py` | Widgets `catalog_name` (padrão `rede_americas`) e `prefixo_schema` (`ontologia`) | `%run` pelos demais |
| `01_ingestao_e_medalhao.py` | Roteiro do Lakeflow Connect (UI no clássico; célula B'.1 com Integrated CDC no serverless), criação dos schemas e conferência de bronze, prata e ouro | Databricks |
| `02_create_metric_views.py` | Cria as 3 Metric Views e valida as 5 respostas da demo contra SQL determinístico na prata | Databricks |
| `03_genie_agent_setup.py` | Textos do agente e do baseline (nome, descrição, instruções, perguntas) | Referência para a UI |
| `04_apply_certification_and_domains.py` | Certificação e tags de domínio via SQL (idempotente) | Databricks |
| `05_pages_content.py` | Conteúdo das 4 Pages, campo a campo | Referência para a UI |
| `06_cleanup_delete_all_assets.py` | Apaga os schemas `ontologia_*` (exige `DELETE` no widget) | Databricks |
| `pipeline/01_prata_so_pk.sql`, `pipeline/01_prata.sql` | Prata, fase 1 (só PK) e fase 2 (PK + FK) | Pipeline SDP |
| `pipeline/02_ouro.sql` | `fato_itens_faturados` | Pipeline SDP |
| `azure_sql/` | DDL, gerador de dados (seed 42), login, utility script v1.7 e preparo de change tracking | `sqlcmd` |
| `scripts/gerar_prata.py` | Gera os `01_prata*.sql` a partir dos metadados da origem | Local |

## Pré-requisitos e implantação

**Origem (uma vez, ~30 min).** Serve qualquer SQL Server com change tracking; a demo foi testada num Azure SQL
Database serverless.

```bash
az sql server create -g <seu-resource-group> -n <seu-servidor> -l <regiao> -u <admin> -p '<senha-admin>'
az sql db create -g <seu-resource-group> -s <seu-servidor> -n rede_americas_ontologia \
  --edition GeneralPurpose --compute-model Serverless --family Gen5 --capacity 1 --auto-pause-delay 60
az sql server firewall-rule create -g <seu-resource-group> -s <seu-servidor> -n workspace \
  --start-ip-address <IP de saída do workspace> --end-ip-address <IP de saída do workspace>

cd azure_sql && python3 gerar_dados.py            # gera 02_dados.sql (~90 mil linhas, determinístico)
S="-S tcp:<seu-servidor>.database.windows.net,1433 -U <admin>"
sqlcmd $S -d master -i 00_login_master.sql        # troque a senha no arquivo antes
for f in 01_ddl.sql 02_dados.sql lakeflow_utility_script.sql 03_preparar_lakeflow_connect.sql; do
  sqlcmd $S -d rede_americas_ontologia -i $f; done # o último deve listar 22 tabelas
```

**Workspace:**
- Unity Catalog e um SQL warehouse serverless. Permissões `CREATE CONNECTION` (ou `USE CONNECTION`), `CREATE SCHEMA` e
  `CREATE MATERIALIZED VIEW`.
- **Catálogo de destino com storage próprio.** O Lakeflow Connect recusa catálogos com Default Storage. Se o padrão do
  workspace for Default Storage, crie um catálogo com storage próprio:
  `CREATE CATALOG rede_americas MANAGED LOCATION 's3://<bucket-da-external-location>/rede_americas'`.
- **Rede.**
  - Workspace clássico: libere no firewall o IP de saída (NAT) do compute clássico.
  - Workspace só serverless: libere o IP de saída do serverless. Para descobrir, rode um notebook serverless que lê
    `https://api.ipify.org`. Ele pode variar dentro de um bloco, então libere o `/24`.
- **Pages** está em Beta e precisa ser habilitada por um account admin em *Account console → Previews*.

## Passo a passo (~1h, com a origem pronta)

| # | Passo | Tempo |
|---|---|---|
| 1 | Clone o repo como **Git folder**. Em todos os notebooks, `catalog_name = rede_americas` (o widget guarda o último valor) | 2 min |
| 2 | `01`, célula **B.1**: cria os schemas `ontologia_staging`, `_bronze`, `_prata` e `_ouro` | 1 min |
| 3 | **Ingestão.** No clássico, pela UI: **Data Ingestion → SQL Server** → conexão → gateway `ont_gateway` + pipeline `ont_ingestao` (staging em `ontologia_staging`, destino `ontologia_bronze`, schemas `cadastro`, `assistencial`, `faturamento`, `relacionamento`, sem `dbo`). No serverless: célula **B'.1** (Integrated CDC por API). Depois, célula **B.2**: 22 tabelas OK | 15 min |
| 4 | **Medalhão.** **Jobs & Pipelines → Create → ETL pipeline** `ont_medalhao`, serverless. Catálogo padrão = `rede_americas`, schema `ontologia_prata`. Configuration: `catalogo=rede_americas`, `bronze=ontologia_bronze`, `prata=ontologia_prata`, `ouro=ontologia_ouro` | 5 min |
| 5 | **Fase 1:** source `01_prata_so_pk.sql` + `02_ouro.sql` → Run → célula **C.1** (22 PKs) | 5 min |
| 6 | **Fase 2:** troque por `01_prata.sql` e **apague o `_so_pk` da pasta do pipeline** → Run → **C.1** (22 PKs + 33 FKs) | 5 min |
| 7 | `02_create_metric_views`: cria as 3 Metric Views; as células de validação precisam passar | 3 min |
| 8 | Crie na UI os 2 Genie spaces (baseline e agente), com os textos do `03` | 8 min |
| 9 | Faça as 5 perguntas no **baseline** e anote as respostas | 5 min |
| 10 | Crie os 3 domínios (**Discover → Create domain**, nomes exatos) → rode o `04` → certifique o agente à mão e coloque-o em `Faturamento Hospitalar` | 5 min |
| 11 | Crie as 4 Pages do `05` (use `@` para ligar os ativos) e publique | 10 min |
| 12 | Repita as 5 perguntas no agente e no **Genie One**, conferindo as citações | 10 min |

## Configurações manuais (só UI)

| Item | Onde |
|---|---|
| Conexão SQL Server | Catalog → External data → Connections |
| Gateway + pipeline de ingestão (clássico) | Data Ingestion → SQL Server. No serverless, a célula B'.1 usa a API |
| Pipeline do medalhão | Jobs & Pipelines → Create → ETL pipeline |
| Genie spaces (agente e baseline) | Genie → New, ou Genie One → Create Agent |
| Domínios (criar e publicar) | Discover → Create domain |
| Certificação e domínio do agente | ⋮ do agente → Assign certification |
| Pages | Discover → Pages → Create page |

O resto é SQL nos notebooks: schemas, Metric Views, certificação e tags das tabelas, validações e cleanup.

## Perguntas da demo e resultados esperados

Os números vêm de dados sintéticos com seed fixa e são conferidos pelo notebook `02` contra SQL determinístico.

| # | Pergunta | Resposta governada (agente) | O que o baseline costuma errar | Camada citada |
|---|---|---|---|---|
| 1 | Qual a taxa de glosa da rede nos últimos 12 meses? | **3,21%** (R$ 1,06 mi glosados ÷ R$ 32,9 mi de faturado analisado) | ~2,86%: divide pelo faturado total, incluindo contas não analisadas | Page "Taxa de glosa" + `mv_glosas` |
| 2 | Como evoluiu a taxa de glosa mês a mês? | Sobe de 1,75% (nov/25) a 4,69% (ago/26). Set/26: 6,05%, com só 51% das contas analisadas. Out/26: sem contas analisadas, não é 0% | Mostra queda falsa: 2,87% em set e 0% em out | `mv_glosas` (`conta_analisada`) + Page |
| 3 | Qual operadora tem a maior taxa de glosa e qual o principal motivo? | **Delta Assistência, 4,66%**, motivo acomodação incompatível com o plano (R$ 78,9 mil). A Beta tem o maior valor glosado (R$ 468,5 mil), motivo sem autorização prévia | Confunde maior taxa com maior valor; não acha o motivo sem juntar 4 tabelas | `mv_glosas` + Page "Glosa hospitalar" |
| 4 | Por que a glosa da Beta subiu a partir de maio de 2026? | Taxa de 2,82% → **5,08%** (contas analisadas). Glosa por falta de autorização de R$ 78,8 mil → **R$ 151,0 mil** | Compara meses com contas não analisadas; não separa por categoria | `mv_glosas` (`categoria_glosa`) |
| 5 | Quais médicos geram glosa por preço acima do contratado, e vale a pena recorrer? | Só o **Dr. Ricardo Menezes Prado** (Ortopedia, Américas Sul): 49 itens, R$ 152,4 mil, igual ao sobrepreço medido. Recuperação de PREÇO é 13,2% contra 35,5% da ADMINISTRATIVA: corrigir a cobrança na origem | Não cruza com o preço contratado vigente; não conhece a taxa de recuperação | `mv_glosas` (`sobrepreco`) + `mv_recuperacao` + Page "Taxa de recuperação" |

### Roteiro de 1 hora

| Tempo | Bloco |
|---|---|
| 0–10 min | Contexto do negócio (o que é glosa e por que a taxa engana) e arquitetura (Lakeflow Connect → medalhão com PK/FK) |
| 10–20 min | Baseline: perguntas 1, 2 e 4 no Genie sem contexto; mostrar as respostas divergentes |
| 20–35 min | Ontologia: Metric Views (YAML, regra das contas analisadas), Page "Taxa de glosa", domínios e certificação (rodar o `04` ao vivo) |
| 35–50 min | As 5 perguntas no agente e no Genie One, abrindo as citações de cada resposta |
| 50–60 min | Perguntas e próximos passos |

## Lições e problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `Only serverless compute is supported in the workspace` | O gateway exige compute clássico. Use Integrated CDC (célula B'.1) |
| `Default Storage for Unity Catalog is not supported on LakeFlow Connect pipelines` | Use um catálogo com `MANAGED LOCATION` |
| `PERMISSION_DENIED: Can not move tables across arclight catalogs` | O pipeline foi criado com catálogo padrão em Default Storage. Recrie com catálogo padrão igual à chave `catalogo` |
| `UC_REFERENTIAL_CONSTRAINT_DOES_NOT_EXIST` | O SDP grava PK e FK em paralelo. Rode as duas fases (só PK, depois PK + FK) |
| `PARSE_SYNTAX_ERROR` perto de `EXPECT` | A `EXPECT` precisa vir antes de `PRIMARY KEY` e `FOREIGN KEY` na lista do schema |
| `PARSE_SYNTAX_ERROR` perto de `.` | Falta a Configuration do pipeline (`catalogo`, `bronze`, `prata`, `ouro`) |
| Integrated CDC: `Client with IP address ... is not allowed` | O IP de saída do serverless mudou dentro do bloco. Libere o `/24` no firewall |
| Conferência mostra `NÃO EXISTE` | Widget `catalog_name` errado: use `rede_americas` |
| `Table ... is already managed by pipeline` | Pipeline recriado sem apagar as tabelas do anterior: apague o pipeline antigo ou os schemas |

## Cleanup

1. Apague na UI os pipelines `ont_medalhao`, `ont_ingestao` e `ont_gateway`, se houver.
2. Rode o `06_cleanup_delete_all_assets` com `DELETE` no widget: ele apaga os 4 schemas `ontologia_*`, sem apagar o
   catálogo.
3. Apague à mão os 2 Genie spaces, as 4 Pages e, se quiser, os 3 domínios.
4. Origem: `az sql db delete -g <seu-resource-group> -s <seu-servidor> -n rede_americas_ontologia`.
