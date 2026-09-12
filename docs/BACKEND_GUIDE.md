# Guia do backend

## Responsabilidades

`config` configura ambiente e rotas; `core` contém health check; `operations` é o
app de domínio. Apps padrão do Django atendem admin, usuários e sessões, mas a API
DRF não tem autenticação configurada. Todos os dez models estão registrados no admin.

| Onde trabalhar | Responsabilidade |
| --- | --- |
| `operations/models.py` | Campos, relacionamentos e invariantes persistidas |
| `operations/analytics/queries.py` | Leituras ORM compartilhadas pelo dashboard e alertas |
| `operations/analytics/dashboard.py` | Composição dos indicadores e score |
| `operations/operation/service.py` | Períodos, agregações, comparações, tendência e paginação da Operação |
| `operations/operation_views.py` | Endpoints somente leitura e tradução de erros da Operação |
| `operations/alerts/rules.py` | Critérios e severidades; recebe métricas prontas |
| `operations/alerts/engine.py` | Aplica regras e ordena alertas ativos |
| `operations/alerts/investigations.py` | Impacto e evidências por tipo de alerta |
| `operations/actions/recommendations.py` | Recomendações com chaves estáveis |
| `operations/actions/service.py` | Criação, duplicidade, listagem e atualização de ações |
| `operations/ai/` | Intenções, contextos permitidos, prompts e adaptadores de IA |
| `operations/serializers.py` | Contratos públicos de entrada e saída |
| `operations/views.py` | HTTP, chamadas aos serviços e tradução de erros |

Não há pacote `repositories`. Regras novas devem ficar no domínio correspondente;
extraia uma consulta para `analytics/queries.py` quando for compartilhada. Evite
adicionar cálculo ao serializer ou ao React. Ao incluir endpoint, registre a rota
no arquivo `*_urls.py` do domínio e teste payload e erros, além do serviço.

## Dados e integridade

| Model | Relações e cuidados para manutenção/ingestão |
| --- | --- |
| `Branch` | Filial; não tem identificador externo nem unicidade de nome |
| `Customer` | Segmento/status e localização; referenciado por pedidos e chamados |
| `Product` | SKU único e preço atual não negativo |
| `Inventory` | FK para filial/produto, combinação única, quantidades não negativas; snapshot |
| `Order` | FKs protegidas para cliente/filial, promessa após criação, entrega opcional, total não negativo |
| `OrderItem` | FK para pedido com cascade e produto protegido; quantidade positiva e preço da venda |
| `Ticket` | Cliente protegido, pedido opcional com `SET_NULL`, fechamento após criação |
| `ActionItem` | Origem por chaves, textos persistidos, prioridade/status e timestamps reais |

Remover um pedido apaga itens e preserva o chamado com `order=None`. Estoque é
apagado com filial/produto. Não existem models `Alert`, `Recommendation` ou
`Investigation`: são dicionários calculados. `ActionItem.save()` cuida de
`completed_at`; atualizações em lote não executam esse método.

A restrição `unique_open_action_recommendation` impede duas ações `pending` ou
`in_progress` para a mesma origem/recomendação. Ações concluídas podem ser repetidas;
reabertura também deve respeitar a unicidade. O service usa transações, bloqueios
e trata conflitos de integridade. Concorrência real em PostgreSQL ainda precisa de
testes; SQLite não comprova a semântica desses bloqueios.

## API atual

Todas as rotas abaixo têm prefixo `/api/` e barra final.

| Método e caminho | Contrato principal |
| --- | --- |
| `GET health/` | `{status, service}`; disponibilidade HTTP, sem consulta de dependências |
| `GET dashboard/summary/` | `reference_date`, saúde, faturamento, pedidos, atrasos e chamados |
| `GET dashboard/trends/` | Data, métrica, meta e seis pontos mensais |
| `GET dashboard/changes/` | Data e lista de mudanças/snapshot de estoque |
| `GET alerts/` | Lista de alertas calculados, ordenada por severidade e chave |
| `GET alerts/{alert_key}/investigation/` | Alerta, contexto, impacto, sinais e evidências; 404 se inativo/inexistente |
| `GET alerts/{alert_key}/recommendations/` | Catálogo e `is_added`; 404 se alerta inativo/inexistente |
| `GET actions/` | Lista ordenada por status, prioridade e criação decrescente |
| `POST actions/` | Entrada: `alert_key`, `recommendation_key`; 201, 400, 404 ou 409 com ação existente |
| `PATCH actions/{id}/` | Entrada: `status`; 200, 400, 404 ou 409 na reabertura conflitante |
| `POST assistant/query/` | `question` não vazia, até 500 caracteres; resposta com intenção, confiança, texto, evidências e provider |
| `POST assistant/executive-summary/` | Resumo não persistido; sem pergunta; mesmo formato de resposta |
| `GET operation/overview/` | Resumo, todas as filiais, média aritmética e pontos de atenção; query `days` |
| `GET operation/delays/` | Taxa geral, clientes afetados e contribuição por filial; query `days` |
| `GET operation/branches/{id}/` | Métricas, comparação com a média e tendência diária; query `days` |
| `GET operation/orders/` | Pedidos paginados; `days`, `branch`, `status`, `delivery`, `page` e `page_size` |

IA sem configuração válida responde 503. Falha de provider pode produzir resposta
200 identificada como `fallback`. Campos extras são rejeitados nos contratos de
escrita de ações. O campo interno `_recommendation_context` da investigação não é
serializado: as recomendações leem os dados estruturados, sem interpretar textos.

## Regras que uma carga precisa respeitar

- A data padrão é `DEMO_REFERENCE_DATE`. Dashboard e alertas preservam 30 dias; a
  área Operação propaga `days=7|30|90` em todos os seus endpoints.
- Cada recorte usa datetimes conscientes do fuso: início inclusivo e fim exclusivo.
  Em 29/08/2026, 30 dias abrangem 31/07–29/08 e o bloco anterior 01/07–30/07.
  A agregação por filial foi migrada de SQL específico para ORM com as mesmas
  fronteiras, eliminando a divergência reproduzida em SQLite na Fase 01.
- Faturamento soma `Order.total_amount` dos status não cancelados. O model não soma
  itens automaticamente; o seed faz isso. Contagem e denominador de atraso incluem
  todos os pedidos do período, inclusive cancelados.
- Atrasos do KPI e das análises relacionadas são `status=delayed`. A regra **não**
  compara datas para atribuir atraso. O seed já marca assim entregas tardias e atrasos
  abertos. Entrega tardia com status `delivered` não entra nesse KPI.
- Tendência mensal tem outro recorte: pedidos criados no mês, com prazo vencido até
  a referência e status `delivered`/`delayed`; entrega no prazo exige `delivered_at`
  preenchida e menor/igual a `promised_at`. Mês sem base atualmente retorna zero.
- Estoque crítico: `current_quantity < minimum_quantity`. Chamados ativos: `open`
  ou `in_progress` em toda a base. Não representam evolução histórica.
- Clientes estratégicos recorrentes: pelo menos dois atrasos ou dois chamados
  recentes. As contagens usam `distinct` para não multiplicar pedidos por joins.
- Score: 100 menos seis penalidades limitadas em `calculate_operational_health`.
  Alertas têm thresholds em `alerts/rules.py`. Estoque associado a atrasos é
  correlação; a soma por item na severidade pode incluir o mesmo pedido mais de uma
  vez, enquanto o impacto de estoque usa contagem distinta de pedidos.

## Operação e drill-down

`operation/service.py` monta quatro contratos de leitura e não depende da camada de
ingestão. A média de filiais é aritmética: pedidos, receita e chamados incluem todas
as filiais; taxa de atraso e saúde excluem unidades sem pedidos, pois não possuem
denominador. A saúde por filial reutiliza `calculate_operational_health`; o frontend
recebe valores e diferenças já calculados.

Pedidos são ordenados por criação e ID decrescentes, usam `select_related` para filial
e cliente e têm página de 1 a N com tamanho máximo 50. O filtro `delivery=late` segue
exatamente `status=delayed`. A coluna de situação pode descrever entrega no prazo,
após a promessa ou prazo vencido, mas não altera o KPI.

O contrato `metric_definition` prepara lineage sem persistir um grafo: identifica a
métrica `order_delay_rate`, a entidade `orders`, o campo `status`, a regra
`status = delayed` e a pipeline `orders`. Estoque e chamados ativos são snapshots;
tickets de filial são apenas os vinculados a pedidos daquela unidade. Ausência de
pedidos ou atrasos produz resposta válida, não erro.

## IA e manutenção

`intents.py` define seis intenções e `UNKNOWN`, com validação Pydantic. O mock usa
palavras-chave. Gemini classifica com saída estruturada; `service.py` escolhe o
contexto pela intenção permitida. `UNKNOWN` encerra antes dos analytics.

`providers.py` é o único ponto de chamadas ao SDK. `GEMINI_MODEL` vem do ambiente;
timeout de 30 segundos é por chamada, e consulta normal pode fazer duas. A explicação
é texto livre; o backend não verifica cada afirmação gerada, mas constrói `evidence`
independentemente. Gemini não tem ORM, ferramentas ou execução SQL.

O fallback mantém identificação e evidências, sem encobrir configuração incompleta.
Capturas de exceções são amplas e os logs de fallback são genéricos. Dados vazios
podem falhar antes do provider (`max()` sem filiais); variações `None` podem falhar
nos formatadores do mock/recomendações. Resolver com testes de dados incompletos
antes da ingestão real, sem transformar “sem base” em zero artificial.

## Origem da demo e pipeline de pedidos

O comando `seed_demo` contém catálogos Python, usa `random.Random(42)` e 180 dias de história
até 29/08/2026. A geração ocorre em uma transação: filiais → clientes → produtos →
pedidos → itens/totais → estoque → chamados, por operações em lote do ORM.

Dataset completo: 5 filiais, 250 clientes, 40 produtos, 200 estoques, 2.500 pedidos
e 500 chamados; número de itens depende da geração. `--small` usa 40 clientes,
30 produtos, 150 estoques, 100 pedidos e 35 chamados, mantendo 5 filiais. Contagem,
P018/P027 e clientes estratégicos são favorecidos pelo gerador para produzir sinais.
Testes do cenário dependem desses padrões e, em alguns casos, dos números exatos.

Sem `--reset`, qualquer dado operacional existente interrompe a geração. Isso evita
duplicação da demo, mas não completa carga parcial nem faz upsert. `--reset` remove
também ações e o histórico de pipelines, evitando freshness órfã, e só deve ser usado
em banco descartável/de demonstração. Não usar esse
comando como mecanismo de atualização de dados externos.

`data/source/orders.json` é uma exportação demonstrativa versionada. A pipeline em
`operations/ingestion/` usa Python padrão e separa extract, validate, transform e
load. `run_data_pipeline orders` é sua única entrada de execução. O lote de pedidos
e itens é atômico; origem + `external_id` permite upsert idempotente.

`PipelineRun` guarda status, etapas, contagens, duração e publicação. `PipelineIssue`
guarda rejeições por execução. Qualidade é válidos ÷ recebidos; zero recebidos não
tem taxa. A API somente leitura fica em `/api/data/pipelines/`. Consulte contrato,
regras e operação em [DATA_PIPELINE.md](DATA_PIPELINE.md).

Analytics, alertas, recomendações e IA devem continuar lendo os models publicados,
sem importar extratores ou conhecer formatos externos. Evoluir o período de análise
separadamente, mantendo a data da demo como padrão compatível. `ActionItem` continua
sendo trabalho registrado pelo usuário; uma carga operacional não deve recriá-lo.
Sem Airflow, Spark, Pandas, dbt ou infraestrutura nova. A execução continua manual;
GitHub Actions é apenas uma alternativa futura documentada.

## Configuração e testes

Variáveis e setup estão no [README](../README.md). Os arquivos `.env.example` são
modelos públicos; valores reais não devem entrar no Git. `config/environment.py`
normaliza hosts Vercel. CORS do frontend continua explícito, mesmo com hosts da
plataforma derivados automaticamente.

Em `backend/`, com dependências já instaladas:

```powershell
..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe manage.py check --settings=config.test_settings
..\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.test_settings
```

`pytest.ini` seleciona `config.test_settings`: SQLite em memória, debug de teste,
chave fictícia e provider mock, definidos antes de carregar `.env`. Assim fixtures
podem usar `seed_demo --reset`/`flush` sem acessar o Supabase da demonstração.
Não usar esse módulo no deploy ou no runserver da demo. Os comandos de check acima
validam apps/schema nesse ambiente; não certificam a configuração de produção.
Para uma suíte PostgreSQL futura, criar configuração separada com banco descartável
e ambiente explícito, sem reutilizar a conexão hospedada da demo.

`test_models`, `test_seed_demo`, `test_analytics`, `test_alerts`, `test_ai` e
`test_actions` protegem o fluxo existente. `test_analytics_boundaries` acrescenta
casos pequenos sem seed. `core/tests` cobre health e composição dos hosts de deploy.
`test_pipeline` cobre execução, rejeição, falha, qualidade, atomicidade, idempotência,
comando, fonte versionada e API.
`test_operation` cobre filiais, detalhe, métricas, média, atraso, filtros combinados,
paginação, períodos, vazio, 404 e parâmetros inválidos. O teste de fronteiras também
compara a agregação de filial com o ORM geral nas viradas de dia.
Consulte lacunas e resultados em [AUDIT_PHASE01.md](AUDIT_PHASE01.md).
