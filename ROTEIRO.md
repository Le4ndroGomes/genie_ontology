# Roteiro completo — Genie Ontology na Rede Américas (clique a clique)

Origem relacional (Azure SQL `rede_americas_ontologia`, passo 0) → **Lakeflow Connect** (gateway +
ingestão) → **medalhão** (pipeline SDP: prata com PK/FK, ouro) → **Metric Views** → **domínios**, **certificação** e
**Pages** → **Genie Agent** → perguntas no **Genie One**.

Cada passo indica o notebook do repo que o acompanha (estrutura de
[databeli/genie_ontology](https://github.com/databeli/genie_ontology)).

Workspace: `<seu-workspace>` · catálogo `rede_americas_demo` · warehouse serverless de sua escolha.

| Camada | Schema | Quem cria |
|---|---|---|
| Staging e event log da ingestão | `ontologia_staging` | Lakeflow Connect |
| Bronze (cópia fiel, SCD1) | `ontologia_bronze` | Lakeflow Connect |
| Prata (tipada, PK/FK, comentários, qualidade) | `ontologia_prata` | Pipeline `ont_medalhao` (`pipeline/01_prata_so_pk.sql`, depois `pipeline/01_prata.sql`) |
| Ouro (fatos) + Metric Views | `ontologia_ouro` | Pipeline (`pipeline/02_ouro.sql`) + notebook `02_create_metric_views` |

Tempo total: ~1h30, a maior parte esperando o gateway e o pipeline.

---

## 0. Criar a origem (30 min, uma vez)

Qualquer SQL Server com change tracking serve. O teste foi feito num Azure SQL Database serverless (GP, 1 vCore):

```bash
az sql server create -g <seu-resource-group> -n <seu-servidor> -l <regiao> -u <admin> -p '<senha-admin>'
az sql db create -g <seu-resource-group> -s <seu-servidor> -n rede_americas_ontologia \
  --edition GeneralPurpose --compute-model Serverless --family Gen5 --capacity 1 --auto-pause-delay 60
az sql server firewall-rule create -g <seu-resource-group> -s <seu-servidor> -n workspace-nat \
  --start-ip-address <IP de saída (NAT) do compute clássico do workspace> --end-ip-address <mesmo IP>
az sql server firewall-rule create -g <seu-resource-group> -s <seu-servidor> -n minha-maquina \
  --start-ip-address <IP da sua máquina> --end-ip-address <IP da sua máquina>
```

Depois, de `azure_sql/`:

```bash
python3 gerar_dados.py                    # gera 02_dados.sql (seed 42, ~90 mil linhas)
S="-S tcp:<seu-servidor>.database.windows.net,1433 -U <admin>"   # sqlcmd pede a senha
sqlcmd $S -d master -i 00_login_master.sql          # troque a senha no arquivo antes
sqlcmd $S -d rede_americas_ontologia -i 01_ddl.sql
sqlcmd $S -d rede_americas_ontologia -i 02_dados.sql
sqlcmd $S -d rede_americas_ontologia -i lakeflow_utility_script.sql
sqlcmd $S -d rede_americas_ontologia -i 03_preparar_lakeflow_connect.sql   # deve listar 22 tabelas
```

O gateway do Lakeflow Connect roda em **compute clássico**: o workspace precisa de compute clássico (workspace só
serverless não serve), e o IP de saída dele precisa estar no firewall do banco.

## 0.1 Pré-requisitos no workspace (5 min)

1. **Importe a pasta do repo** para o workspace (Workspace → ⋮ → Import, ou Git folder).
2. **Permissões:**
   - no catálogo `rede_americas_demo`: `USE CATALOG` e `CREATE SCHEMA`;
   - na conexão: `USE CONNECTION`, ou `CREATE CONNECTION` no metastore para criar uma nova.
3. **Schemas:** abra `01_ingestao_e_medalhao` e rode até a célula **B.1**. Ela cria `ontologia_staging`,
   `ontologia_bronze`, `ontologia_prata` e `ontologia_ouro`.
4. **Previews:**
   - **Pages** está em Beta e precisa que um account admin habilite em **Account console → Previews**. Sem isso,
     pule o passo 8; o resto funciona.
   - **Genie Ontology** está em Public Preview: não é preciso habilitar nada, e hoje não há custo de curadoria.
5. **Banco de origem:** pausa depois de 60 min parado. A primeira conexão do dia leva ~1 min para "acordar".

## 1. Conexão (5 min)

Crie em **Catalog → External data → Connections → Create connection**:
- tipo **SQL Server**, nome `ra_ontologia_azure_sql`;
- host `<seu-servidor>.database.windows.net`, porta `1433`;
- usuário `dbx_ingest`, com a senha definida em `00_login_master.sql`;
- **Test connection** → **Create**.

## 2. Gateway e pipeline de ingestão (15 min + ~10 de carga)

1. No menu lateral, **Data Ingestion** → em *Databricks connectors*, **SQL Server**.
2. **Connection**: escolha a conexão do passo 1 → **Next**.
3. **Ingestion setup:**
   - Ingestion pipeline name: `ont_ingestao`
   - Event log: `rede_americas_demo` / `ontologia_staging`
   - Ingestion gateway name: `ont_gateway`
   - Staging location: `rede_americas_demo` / `ontologia_staging`
   - **Create pipeline and continue**
4. **Source:**
   - expanda `rede_americas_ontologia` e marque os schemas `cadastro`, `assistencial`, `faturamento` e
     `relacionamento` (22 tabelas);
   - **não** marque `dbo`, que só tem objetos do utility script;
   - deixe o nome de destino igual ao da origem e *History tracking* em SCD tipo 1;
   - **Next** → **Save and continue**.
5. **Destination**: `rede_americas_demo` / `ontologia_bronze` → **Save and continue**.
6. **Database setup**: **Validate**. Deve passar, porque change tracking, utility script v1.7 e permissões já estão no banco.
7. **Schedules and notifications**: pule (a origem é estática) → **Save and run pipeline**.

O gateway sobe em ~5 min, em compute clássico, e faz o snapshot. Depois o pipeline de ingestão, serverless, grava o bronze.

### 2b. Workspace só serverless: Integrated CDC (sem gateway)

Se o workspace só aceita serverless, o assistente acima falha ao subir o gateway ("Only serverless compute is
supported in the workspace"). Use o **Integrated CDC**: um único pipeline serverless, sem gateway, criado por API
(a UI ainda não cria esse tipo).

1. **Firewall:** descubra o IP de saída do serverless do workspace (num notebook serverless:
   `urllib.request.urlopen("https://api.ipify.org").read()`) e libere no SQL:
   `az sql server firewall-rule create -g <seu-resource-group> -s <seu-servidor> -n workspace-serverless --start-ip-address <IP de saída do serverless> --end-ip-address <IP de saída do serverless>`.
   O IP pode mudar; se a conexão falhar, confira de novo.
2. **Catálogo com storage próprio:** catálogos com Default Storage são recusados como destino ("Default Storage for
   Unity Catalog is not supported on LakeFlow Connect pipelines"). Crie um com `MANAGED LOCATION` numa external location:
   `CREATE CATALOG rede_americas MANAGED LOCATION 's3://<bucket-da-external-location>/rede_americas'` e use esse
   nome no widget `catalog_name` do notebook 00/01.
3. **Conexão:** a mesma do passo 1.
4. **Pipeline:** no notebook `01_ingestao_e_medalhao`, rode **B.1**, mude o widget `criar_integrated_cdc` para `sim`
   e rode **B'.1**. Ela cria `ont_ingestao` (`connector_type: "CDC"`, `serverless: true`) com os 4 schemas e dispara a carga.
   - Equivalente em API: `POST /api/2.0/pipelines` com `ingestion_definition.connection_name`, `connector_type: "CDC"`,
     um objeto `schema` por schema da origem e `data_staging_options` em `ontologia_staging`; depois
     `POST /api/2.0/pipelines/<id>/updates`.
   - O recurso precisa estar habilitado no workspace (account team). Se a criação falhar com erro de recurso não
     disponível, peça a habilitação.
5. Change tracking funciona com SCD tipo 1 (o padrão). SCD tipo 2 exige CDC no SQL Server.
6. Quando o update terminar, siga para o passo 3.

## 3. Conferir o bronze (2 min)

Rode a célula **B.2** do notebook `01_ingestao_e_medalhao`. Ela compara as 22 contagens com a origem, por exemplo:
4.000 pacientes, 8.528 atendimentos, 34.010 itens de conta, 664 glosas e 8.848 protocolos. Todas devem aparecer como
`OK`.

## 4. Medalhão: pipeline SDP prata + ouro, em duas fases (15 min + ~6 por fase)

1. Confirme que a pasta `pipeline/` foi importada junto com o repo, com `01_prata_so_pk.sql`, `01_prata.sql` e
   `02_ouro.sql`.
2. **Jobs & Pipelines → Create → ETL pipeline:**
   - Nome: `ont_medalhao`
   - Default catalog `rede_americas_demo`, default schema `ontologia_prata`
   - Compute **serverless**
3. Em **Settings → Configuration**, cadastre os pares chave/valor que o SQL usa como `${...}`:

   | Chave | Valor |
   |---|---|
   | `catalogo` | `rede_americas_demo` |
   | `bronze` | `ontologia_bronze` |
   | `prata` | `ontologia_prata` |
   | `ouro` | `ontologia_ouro` |
4. **Fase 1, só PK.** Em **Source code / Paths**, adicione `pipeline/01_prata_so_pk.sql` e `pipeline/02_ouro.sql`, e
   clique em **Run pipeline**. O grafo mostra 22 materialized views na prata e 3 no ouro. Rode a célula **C.1** do
   notebook 01: o esperado são as mesmas contagens do bronze e **22 PRIMARY KEY**.
5. **Fase 2, com FKs.** Em **Source code**, troque `01_prata_so_pk.sql` por `pipeline/01_prata.sql`, mantendo o
   `02_ouro.sql`. Rode de novo, sem *full refresh*. Na célula **C.1**, o esperado é **22 PRIMARY KEY e 33 FOREIGN KEY**.
6. **Por que duas fases?**
   - O SDP grava as chaves de todas as tabelas em paralelo, no fim do update. Se a FK de uma tabela chega antes da
     PK da tabela-pai, o update falha com `UC_REFERENTIAL_CONSTRAINT_DOES_NOT_EXIST`.
   - Com todas as PKs já registradas na fase 1, a fase 2 grava as FKs sem erro.
   - Depois disso, execuções normais e *full refresh* ficam estáveis (testado em 26/10/2026).
7. **O que a prata faz:** cada tabela da origem vira uma MV gerada por `scripts/gerar_prata.py`, com:
   - tipos explícitos e `NOT NULL`;
   - `COMMENT` de tabela e de coluna, vindos das descrições da origem;
   - **PRIMARY KEY** e as **33 FOREIGN KEYs** informativas, iguais às da origem;
   - expectations de qualidade (ex.: `valor_glosado > 0`, `csat BETWEEN 1 AND 5`), visíveis na aba *Data quality*;
   - integridade referencial: só entram linhas cujo pai já está na prata (`WHERE EXISTS`). Isso ordena os flows,
     criando o pai antes do filho, mas não dispensa as duas fases.
8. **Conferir no Catalog Explorer:** em `ontologia_prata` → `glosas` → **Overview** aparecem as chaves e os
   comentários. O diagrama de relacionamentos (*View relationships*) mostra o grafo de FKs.
9. **Ouro** (`02_ouro.sql`, conferido na célula **C.2**): três fatos desnormalizados.
   - `fato_itens_faturados`: um registro por item da conta, com faturamento, glosa, recurso e preço contratado vigente.
   - `fato_autorizacoes`: um registro por guia, com resposta, atendido mesmo negado, glosa 1801 e reclamações na central.
   - `fato_protocolos`: um registro por protocolo, com plano vigente do paciente na data, CSAT e NPS.

## 5. Metric Views (5 min)

Rode o notebook `02_create_metric_views`. Ele cria em `ontologia_ouro`:
- as Metric Views `mv_faturamento_glosa`, `mv_autorizacoes` e `mv_central`, em YAML 1.1, com `display_name`,
  `synonyms` e comentários;
- três consultas de validação das histórias.

O esperado na validação:
- **O1:** a negativa da Beta passa de ~3,0% para ~37,8% a partir de mai/2026.
- **O2:** só o Dr. Ricardo Menezes Prado aparece, com R$ 152.351 glosados.
- **O3:** o Delta Essencial lidera as reclamações de cobrança, com 36 de 66.

## 6. Domínios (5 min)

Exige `MANAGE DISCOVER` na conta (admins têm) ou `MANAGE` no domínio.

1. Em **Discover → Create domain**, crie **quatro** domínios com estes nomes exatos, acentos incluídos:
   - `Faturamento e Glosa`
   - `Autorização Prévia`
   - `Central de Atendimento`
   - `Cadastro e Assistencial`

   O governed tag de cada um usa o nome como chave, sem valor, e é ele que o notebook 04 aplica.
2. Preencha subtítulo, descrição curta e *Business owner*, depois **Edit Sections → Publish**.
3. Não precisa adicionar tabelas à mão: o notebook 04 faz isso por tag.

## 7. Genie Agent, certificação e domínios dos ativos (10 min)

1. Crie o agente pelo passo 9 e depois volte aqui. Ou crie o agente agora e faça este passo em seguida.
2. **Agente, à mão:** menu ⋮ → **Assign certification** → Certified, e adicione-o ao domínio `Faturamento e Glosa`.
   Não há alvo SQL para esse tipo de objeto.
3. Rode o notebook `04_apply_certification_and_domains`. Ele aplica `system.certification_status = certified` e os
   tags de domínio em 28 ativos: as 22 tabelas da prata, os 3 fatos e as 3 Metric Views. A última célula lista os
   tags por ativo. É idempotente, então pode rodar de novo.

Certificação puxa o Genie One para esses ativos, e os tags continuam depois de um refresh do pipeline.

## 8. Pages (15 min · Beta)

Em **Discover → Pages → Create page**, crie as **5 Pages** do notebook `05_pages_content`:

| Page | Domínio |
|---|---|
| Glosa | Faturamento e Glosa |
| Autorização prévia | Autorização Prévia |
| Acomodação do plano | Cadastro e Assistencial |
| Protocolo da central | Central de Atendimento |
| Agente Ciclo de Receita | Faturamento e Glosa |

Para cada uma:
- Domain, Name, Owner e Synonyms vão nos campos estruturados; Description e Body, no editor.
- Use `@` para citar tabelas, Metric Views, o agente e as outras Pages: vira link governado e *related asset*.
- Não coloque dados de paciente. A documentação proíbe PII em Pages.
- **Publish**: rascunhos pesam menos no ranking do Genie.

## 9. Genie Agent (10 min)

No Genie One, abra **Create Agent** com o warehouse serverless. Nome, descrição, instruções, perguntas de exemplo e
três consultas SQL testadas estão no notebook `03_genie_agent_setup`.

Anexe **só as 3 Metric Views**, sem as tabelas da prata. A ideia é mostrar o Genie preferindo a camada governada; as
perguntas de detalhe ele ainda encontra pela ontologia, pelas PK/FK e pelos comentários.

Depois de criar, faça o passo 7.2 (certificação e domínio do agente). Teste no próprio agente: "Por que a glosa subiu
na Beta Assistência Médica?".

## 10. Genie One: a pergunta que atravessa domínios (10 min)

Abra o **Genie One** (ícone Genie no topo) e pergunte, nesta ordem:

| Pergunta | Resposta esperada | Caminho que a ontologia percorre |
|---|---|---|
| Por que a glosa subiu na Beta? | Negativa de RM, artroscopia e artroplastia da Beta foi de ~3,0% a ~37,8% desde mai/2026; a glosa 1801 é o maior motivo (R$ 381,9 mil) | operadora → autorização → atendimento → conta → item → glosa |
| Quais médicos geram mais glosa por preço? | Dr. Ricardo Menezes Prado (ortopedia, Américas Sul): 49 glosas, R$ 152,4 mil, OPME 25% acima do contratado | médico → item → preço contratado → glosa |
| Os pacientes que reclamaram de cobrança na central tinham qual plano? | Delta Essencial (enfermaria), 36 dos 66 protocolos (CSAT 2,13), internados no Américas Centro com diária de apartamento | protocolo → paciente → beneficiário → plano → item → glosa 1909 |
| O que é taxa de glosa? | A definição da Page "Glosa": glosado ÷ faturado das contas já analisadas | Page + Metric View |

Clique nos ícones de **citação** de cada resposta: devem aparecer a Metric View certificada, a Page e/ou o Genie
Agent. Se uma resposta vier sem a definição oficial, ajuste a Page ou as instruções do agente e pergunte de novo.
Para ver o efeito do *authority score*, faça uma das perguntas antes do passo 7 e repita depois.

## 11. Desligar e limpar

- **Gateway (`ont_gateway`, compute clássico ligado direto):**
  - A doc recomenda não parar o gateway manualmente, porque mudanças podem se perder e as tabelas podem precisar de full refresh.
  - Como esta origem não muda, é seguro pará-lo depois da carga: **Jobs & Pipelines → ont_gateway → Stop**.
  - Religue antes de 7 dias, que é a retenção do change tracking.
- **Pipelines `ont_ingestao` e `ont_medalhao`:** são serverless e triggered, então não custam parados.
- **Banco de origem:** pausa sozinho em 60 min.
- **Para desfazer tudo:**
  1. Apague os pipelines na UI.
  2. Rode o notebook `06_cleanup_delete_all_assets` com `DELETE` no widget. Ele apaga os 4 schemas `ontologia_*`, mas não o catálogo.
  3. Apague à mão o agente, as Pages e os domínios.
  4. Apague o banco Azure: `az sql db delete -g <seu-resource-group> -s <seu-servidor> -n rede_americas_ontologia`.

## Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| Validate do passo 2 falha com permissão | Rode de novo `azure_sql/03_preparar_lakeflow_connect.sql` como administrador (o utility script já foi aplicado) |
| Gateway não sobe: "Only serverless compute is supported in the workspace" | Workspace só serverless. Use o Integrated CDC (passo 2b) |
| `Default Storage for Unity Catalog is not supported on LakeFlow Connect pipelines` | O catálogo de destino usa Default Storage. Crie um catálogo com `MANAGED LOCATION` numa external location (passo 2b) |
| Integrated CDC não conecta (timeout) | IP de saída do serverless fora do firewall do SQL, ou mudou. Confira o IP de novo (passo 2b) |
| Gateway não conecta ("Login failed" / timeout) | Banco pausado (espere 1 min e tente de novo) ou IP fora do firewall (libere o IP de saída do compute clássico do workspace) |
| Pipeline do medalhão: `UC_REFERENTIAL_CONSTRAINT_DOES_NOT_EXIST` | As FKs foram gravadas antes de todas as PKs existirem. Rode a fase 1 (`01_prata_so_pk.sql`) até completar e só então troque para `01_prata.sql` (passo 4) |
| `PARSE_SYNTAX_ERROR` perto de `EXPECT` | Alguém editou a prata à mão: `EXPECT` precisa vir antes de `PRIMARY KEY`/`FOREIGN KEY`. Regere com `scripts/gerar_prata.py` |
| `Table ... is already managed by pipeline ...` | Você recriou o pipeline sem apagar as tabelas do anterior: `DROP SCHEMA ontologia_prata CASCADE` (e ouro), recrie os schemas (célula B.1) e refaça as duas fases |
| Notebook 04 mostra `ERRO` em `SET TAG` | Permissão para aplicar o tag do domínio, ou ativo ainda não criado (rode os passos 4 e 5 antes) |
| Taxa de glosa "cai" nos últimos meses | Contas ainda não analisadas pela operadora. A Metric View já filtra, mas o agente precisa da instrução (está no notebook 03) |
