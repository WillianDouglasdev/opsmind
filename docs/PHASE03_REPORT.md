# Fase 03 — Pipeline V1 de pedidos

Entrega local em 11/09/2026. Escopo: uma pipeline real e manual de pedidos,
monitoramento no backend e integração com a Home e a nova página Pipelines.

## 1. Arquitetura

A fonte é a exportação JSON demonstrativa em `backend/data/source/orders.json`.
O Management Command `run_data_pipeline orders` chama o orquestrador em
`operations/ingestion/runner.py`, que atravessa quatro módulos pequenos:
`extract`, `validate`, `transform` e `load`.

RAW e CLEAN existem como estruturas em memória; BUSINESS são `Order` e `OrderItem`
no banco existente. Não foram criados schemas ou bancos intermediários. Python
padrão foi suficiente; nenhuma dependência, Pandas ou infraestrutura foi adicionada.
Analytics, alertas e IA continuam lendo os models operacionais e não conhecem o ETL.

Cada fronteira atualiza `PipelineRun`. Rejeições tornam a execução `warning`;
falha de leitura, transformação ou carga torna-a `failed`. A publicação de pedidos
e itens ocorre em uma única transação. O monitoramento permanece gravado fora dessa
transação para que uma falha seja observável.

## 2. Fluxo

1. **Extract:** abre JSON UTF-8 e retorna a lista RAW sem consultar o domínio.
2. **Validate:** carrega os catálogos uma vez, verifica cada pedido e separa válidos
   e rejeições, sem gravar e sem interromper o lote por uma linha inválida.
3. **Transform:** converte datas, decimais, referências e itens em dataclasses CLEAN
   imutáveis, já compatíveis com o domínio.
4. **Load:** faz upsert de cada pedido, substitui seus itens e publica todo o lote
   BUSINESS em `transaction.atomic()`.
5. O orquestrador marca a publicação, duração, contagens e status final.
6. A API lê o monitoramento; nenhum `GET` dispara a pipeline.

O contrato e o diagrama estão em [DATA_PIPELINE.md](DATA_PIPELINE.md).

## 3. Modelos

`Order` recebeu `source_system` e `external_id`. Ambos preservam os 2.500 pedidos do
seed, cujo ID externo continua nulo. A restrição condicional
`unique_order_source_external_id` protege somente pedidos vindos de fonte.

`PipelineRun` registra chave e fonte, `running/success/warning/failed`, estados das
quatro etapas em JSON, início, fim, publicação, duração, recebidos, válidos,
rejeitados, carregados e mensagem operacional. A propriedade de qualidade não é
persistida porque deriva diretamente das contagens.

`PipelineIssue` referencia a execução e guarda identificador, código, mensagem e
instante da detecção. Dois models são suficientes. Um model por etapa traria quatro
linhas extras por execução sem acrescentar informação ao fluxo síncrono atual; o JSON
preserva inclusive a etapa que falhou. A migration criada é `0003`.

O admin permite observar execuções e rejeições, sem criar registros de monitoramento
manualmente. `seed_demo --reset` também limpa essas tabelas para não manter freshness
de pedidos que foram removidos.

## 4. Validações

- ID externo obrigatório e único dentro da fonte.
- Filial existente por nome e cliente resolvido de forma única por nome.
- Status pertencente a `Order.Status`.
- Datas ISO 8601 com fuso; promessa posterior à criação; entrega não anterior à
  criação; pedido entregue exige `delivered_at`.
- Ao menos um item; SKU existente e não repetido dentro do pedido.
- Quantidade inteira positiva e preço unitário finito e não negativo.
- Total declarado finito, não negativo e igual à soma dos itens em `Decimal`.

O dataset contém quatro rejeições deliberadas: ID duplicado (`ERP-ORDER-0001`),
filial desconhecida, preço negativo e data de entrega incoerente. Status de atraso
não é inferido das datas: a pipeline respeita o contrato existente do domínio.

## 5. Idempotência

A chave é `source_system="demo_erp"` + `external_id`. `update_or_create` sincroniza
o cabeçalho e os itens são substituídos dentro da mesma transação. A primeira e a
segunda execução carregaram 12 registros cada; depois das duas, o banco continha
exatamente 12 pedidos externos, duas execuções e oito rejeições históricas.

Uma nova execução representa um novo processamento e deve existir no histórico;
idempotência se aplica aos dados BUSINESS, não ao log de execução.

## 6. Qualidade

A fórmula é `registros válidos ÷ registros recebidos × 100`, com duas casas na API.
Na fonte versionada: `12 ÷ 16 × 100 = 75,00%`. Quando recebidos é zero, a API retorna
`null` (“Sem base” no frontend) em vez de qualidade perfeita. IA não participa.

`published_at` é gravado somente após a carga atômica. `last_published_at` busca a
publicação mais recente; se a última tentativa falhar, a freshness continua apontando
para a última publicação real.

## 7. API

- `GET /api/data/pipelines/`: catálogo, execução mais recente e última publicação.
- `GET /api/data/pipelines/orders/`: retrato de pedidos e dez execuções recentes.
- `GET /api/data/pipelines/orders/runs/{id}/`: execução com rejeições.

Os contratos DRF expõem apenas campos de monitoramento. Pipeline ou execução
inexistente responde 404 com mensagem simples. A mensagem de falha não contém
traceback nem caminho completo da fonte. Os endpoints anteriores não mudaram.

## 8. Frontend

A Home acrescentou a pipeline como uma seção independente de `useDashboardData`.
`DataFlow` mostra status, quatro etapas, fonte, publicação real, qualidade e contagens;
sem execução, mostra “Nunca executado”. O rodapé da sidebar consulta o catálogo e
diferencia publicação, warning e falha.

`/pipelines` usa a identidade da Fase 02: um resumo editorial, faixa de etapas,
contagens separadas por linhas, qualidade em destaque e tabela integrada. “Ver
detalhes” consulta a execução escolhida e lista suas rejeições. O frontend não possui
botão de execução nem valores simulados.

Em telas pequenas, etapas e contagens ficam em 2×2, metadados empilham e o histórico
reduz colunas secundárias. Home e Pipelines foram verificadas em 320, 390, 820, 1280
e 1440px sem overflow. Capturas revisadas:
[Pipelines desktop](screenshots/phase03-pipelines-desktop.png),
[Pipelines mobile](screenshots/phase03-pipelines-mobile.png),
[Home desktop](screenshots/phase03-home-desktop.png) e
[Home mobile](screenshots/phase03-home-mobile.png).

## 9. Testes

| Verificação | Resultado final |
| --- | --- |
| `python -m pytest -q` | **74 passaram**, 12,47s |
| `python manage.py check --settings=config.test_settings` | **0 problemas** |
| `python manage.py makemigrations --check --dry-run --settings=config.test_settings` | **Nenhuma alteração detectada** |
| `npm test` | **12 passaram, 0 falharam**, 221ms |
| `npm run lint` | **Aprovado**, sem warnings |
| `npm run build` | **Aprovado**, Vite 7.3.6, 1707 módulos, 11,56s |
| Chrome headless local | **10 combinações responsivas**, 0 overflow e 0 erros JavaScript |

Build final: CSS 279,96 kB (40,04 kB gzip) e JavaScript 447,50 kB
(146,84 kB gzip). A suíte ganhou 11 testes backend e quatro frontend.

`test_pipeline.py` cobre execução válida, rejeição individual, warning, ID duplicado,
falha real, qualidade, idempotência, rollback atômico, API vazia, API/histórico/detalhe,
Management Command, fonte versionada e preservação da última publicação após falha.
Alguns requisitos relacionados aparecem no mesmo teste, totalizando 11 casos.

Os quatro testes frontend cobrem etapas ausentes, estados reais parciais, duração,
labels e freshness calculada. A sessão de navegador conferiu 16/12/4/12, 75%, quatro
rejeições, duas linhas de histórico e integração real da Home. Resultado estruturado:
[phase03-browser.json](validation/phase03-browser.json).

## 10. Teste manual

Em SQLite descartável, foram executados migrations, `seed_demo --reset`, o comando
de pipeline e um servidor Django. Primeira execução:

```text
Pipeline: orders
Fonte: orders.json
Extract: 16 recebidos
Validate: 12 válidos · 4 rejeitados
Transform: 12 processados
Load: 12 carregados
Status: warning
Qualidade: 75.00%
Duração: 0.247s
Execução: #1
```

A segunda execução retornou as mesmas contagens, duração de 1,145s e ID #2. O banco
confirmou 12 pedidos externos, duas execuções e oito issues. A API da execução #2
retornou os mesmos números e quatro issues. O dashboard, após a publicação, apresentou
443 pedidos, 62 atrasados, taxa 14,0%, faturamento R$ 4.110.586,75 e score 69;
Pipelines apresentou 16/12/4/12 e 75,0%. Esses valores foram lidos no frontend.

O teste não alterou o SQLite de desenvolvimento nem o Supabase: usou arquivo temporário
definido por `OPSMIND_TEST_DATABASE`. Os processos locais foram encerrados ao final.

## 11. Arquivos criados

Lista completa da Fase 03 (**25 arquivos**):

- `backend/data/source/orders.json`
- `backend/operations/ingestion/__init__.py`
- `backend/operations/ingestion/extract.py`
- `backend/operations/ingestion/load.py`
- `backend/operations/ingestion/runner.py`
- `backend/operations/ingestion/transform.py`
- `backend/operations/ingestion/types.py`
- `backend/operations/ingestion/validate.py`
- `backend/operations/management/commands/run_data_pipeline.py`
- `backend/operations/migrations/0003_pipelineissue_pipelinerun_order_external_id_and_more.py`
- `backend/operations/pipeline_urls.py`
- `backend/operations/pipelines/__init__.py`
- `backend/operations/pipelines/service.py`
- `backend/operations/tests/test_pipeline.py`
- `frontend/src/pages/PipelinesPage.jsx`
- `frontend/src/styles/pipelines.css`
- `frontend/src/utils/pipelines.js`
- `frontend/src/utils/pipelines.test.js`
- `docs/DATA_PIPELINE.md`
- `docs/PHASE03_REPORT.md`
- `docs/screenshots/phase03-home-desktop.png`
- `docs/screenshots/phase03-home-mobile.png`
- `docs/screenshots/phase03-pipelines-desktop.png`
- `docs/screenshots/phase03-pipelines-mobile.png`
- `docs/validation/phase03-browser.json`

## 12. Arquivos alterados

Lista completa da Fase 03 (**26 arquivos**):

- `README.md`
- `backend/config/test_settings.py`
- `backend/config/urls.py`
- `backend/operations/admin.py`
- `backend/operations/management/commands/seed_demo.py`
- `backend/operations/models.py`
- `backend/operations/serializers.py`
- `backend/operations/views.py`
- `docs/ARCHITECTURE.md`
- `docs/BACKEND_GUIDE.md`
- `docs/FRONTEND_GUIDE.md`
- `docs/ROADMAP_V2.md`
- `frontend/package.json`
- `frontend/src/App.jsx`
- `frontend/src/components/dashboard/DataFlow.jsx`
- `frontend/src/components/layout/AppLayout.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/data/demoMetadata.js`
- `frontend/src/hooks/useDashboardData.js`
- `frontend/src/pages/DashboardPage.jsx`
- `frontend/src/services/api.js`
- `frontend/src/styles/base.css`
- `frontend/src/styles/dashboard.css`
- `frontend/src/styles/responsive.css`
- `frontend/src/styles/theme.css`
- `frontend/src/utils/formatters.js`

Alterações ainda não commitadas das Fases 01 e 02 foram preservadas. `package-lock.json`,
dependências, providers de IA, regras analíticas e contratos anteriores não foram
alterados por esta fase.

## 13. Limitações

- Uma pipeline (`orders`) e uma fonte JSON demonstrativa local; sem integração ERP,
  upload, scheduler, autenticação, paginação ou retenção configurável.
- Filial e cliente são resolvidos por nome. Product já usa SKU; as demais entidades
  precisam de IDs externos antes de integrar uma fonte mutável.
- A publicação é atômica, mas não há lock global contra dois comandos simultâneos.
- Steps em JSON atendem ao comando síncrono; execução distribuída exigiria outra modelagem.
- Não houve teste em PostgreSQL/Supabase, deploy Vercel, dispositivo físico, leitor
  de tela ou navegador além do Chrome headless.
- A integração de navegador da aplicação não disponibilizou sessão; a inspeção usou
  Chrome local isolado. O Playwright permaneceu temporário e não entrou nas dependências.
- As dívidas da Fase 01 sobre fronteiras de fuso e IA com base vazia/parcial continuam.

## 14. Próxima fase — Operação e drill-down

Antes da tela, corrigir e testar as fronteiras de período/fuso em SQLite e PostgreSQL.
Depois criar endpoints paginados de pedidos e filiais com período, status e identidade
explícitos. A página Operação pode usar esses contratos para abrir um indicador,
filial ou alerta e manter filtros ao navegar.

Preservar a pipeline de pedidos e evitar ampliar ingestão no mesmo trabalho. Quando
houver necessidade real de uma segunda fonte, evoluir IDs externos dos catálogos e
adicionar locking de execução. Automatização por GitHub Actions deve usar conexão
administrativa, segredo protegido e concorrência máxima de uma carga; continua apenas
uma proposta, sem workflow nesta fase.
