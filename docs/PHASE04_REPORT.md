# Fase 04 — Operação e drill-down

Entrega local em 12/09/2026. Escopo: tornar atrasos, filiais e pedidos navegáveis,
com regras calculadas no backend, filtros previsíveis e preservação da identidade da
Fase 02. Esta fase localiza o problema; não tenta explicar causalidade.

## 1. Resumo

`/operation` deixou de ser uma intenção da sidebar e passou a ser uma visão operacional
com resumo, comparação das cinco filiais, pontos de atenção e pedidos paginados. O KPI
de atrasos da Home abre uma página dedicada, cada filial abre seu próprio detalhe e o
contexto de período/filtros permanece na URL ao navegar e usar voltar/avançar.

O trabalho não criou model, migration, pipeline, provider de IA ou dependência. O
backend entrega as regras; React formata, ordena apenas para apresentação e navega.

## 2. Arquitetura da área Operação

O pacote `operations/operation/` contém um serviço de leitura independente da
ingestão. `operation_views.py` valida query params com serializers explícitos, traduz
entrada inválida em 400 e filial ausente em 404. `operation_urls.py` isola as rotas.

O serviço consulta `Branch`, `Order`, `Customer`, `Ticket` e `Inventory` em agregações
por lote. A página consome funções de `services/api.js` por `useApiResource`, que
uniformiza carregamento, erro, retry e cancelamento. Nenhum cálculo operacional foi
copiado para componentes.

## 3. Drill-down implementado

O caminho principal ficou:

```text
Home · Atrasos
  → /operation/delays?days=30
  → contribuição por filial
  → /operation/branches/:id?days=30&delivery=late
  → pedidos atrasados e clientes afetados
```

A sidebar abre `/operation`. A visão geral também liga a maior taxa ao detalhe e cada
linha da comparação abre a filial. Links preservam período, status e situação de
entrega quando esses valores são relevantes.

## 4. Filiais

A visão geral lista todas as filiais, inclusive unidades sem pedidos, com saúde,
volume, taxa e quantidade de atrasos, receita e chamados. Uma filial sem denominador
recebe saúde `null` e “Sem base”, sem nota artificial.

O detalhe apresenta identidade, seis métricas, tendência diária, comparação com a
média, quatro sinais do recorte e pedidos. Saúde por filial reutiliza a fórmula já
existente. A interface avisa que pedidos, clientes, tickets e estoque aparecem juntos
como sinais e não como prova causal.

## 5. Pedidos

Pedidos aparecem na Operação e dentro de filial com identificador externo ou ID local,
cliente, filial, criação, valor, status e situação de entrega. A API ordena por data e
ID decrescentes, usa `select_related` e limita `page_size` a 50; a interface solicita
15 linhas na visão geral e 12 no detalhe.

A situação de entrega descreve pedido atrasado no KPI, cancelado, entregue no prazo,
entregue após a promessa, prazo vencido no status atual ou em andamento. Essa descrição
não reclassifica a métrica oficial.

## 6. Filtros

Os períodos permitidos são 7, 30 e 90 dias. A lista de pedidos aceita filial, status,
`delivery=all|late`, página e tamanho. Campos desconhecidos, valores fora do domínio,
páginas inválidas e tamanho acima de 50 retornam 400.

`utils/operation.js` normaliza a URL, omite valores padrão e reinicia a página após
uma mudança de filtro. `setSearchParams` lê a versão atual da query de forma funcional;
isso evita que duas alterações rápidas façam a segunda apagar a primeira.

## 7. Agregações

O recorte temporal usa início inclusivo e fim exclusivo no fuso configurado. A taxa
de atraso é `pedidos com status=delayed ÷ todos os pedidos`, inclusive cancelados no
denominador. Faturamento exclui cancelados e clientes usam contagem distinta.

A média é aritmética por filial. Pedidos, receita e chamados incluem todas as unidades;
taxa e saúde excluem filiais sem pedidos. Chamados de uma filial são ativos vinculados
a pedidos daquela unidade. Chamados gerais, estoque e saúde derivada desses sinais
usam o snapshot atual. A consolidação histórica por filial de `analytics/queries.py`
foi migrada do SQL manual para ORM e ganhou teste de fronteira de fuso.

## 8. Endpoints

| Método e caminho | Resposta |
| --- | --- |
| `GET /api/operation/overview/` | Período, métricas, média, filiais e atenção |
| `GET /api/operation/delays/` | Taxa geral, clientes afetados e contribuição por filial |
| `GET /api/operation/branches/{id}/` | Filial, métricas, diferenças e tendência diária |
| `GET /api/operation/orders/` | Página de pedidos e metadados de paginação |

Overview, delays e detalhe aceitam `days`. Orders aceita também `branch`, `status`,
`delivery`, `page` e `page_size`. O objeto `metric_definition` associa atraso a
`orders.status`, regra `status = delayed` e pipeline `orders`, preparando lineage
sem implementar um sistema de linhagem.

## 9. Componentes frontend

- `PeriodSelector`: período único para as três telas.
- `OperationMetrics`: faixa de indicadores sem transformar tudo em cards.
- `BranchTable`: comparação completa e navegação para filial.
- `BranchDelayTrend`: linha Chart.js para responder se a taxa diária mudou.
- `BranchComparison`: filial, média aritmética e diferença calculada no backend.
- `OrderFilters` e `OrderTable`: filtros rotulados, estados e paginação.
- `OperationPage`, `OperationDelaysPage` e `OperationBranchPage`: composição das rotas.

No mobile, linhas de tabela viram blocos verticais e cabeçalhos de coluna ficam como
labels locais. Métricas, comparação, filtros e gráfico empilham sem tabela horizontal.

## 10. Testes

| Verificação | Resultado final |
| --- | --- |
| `python -m pytest -q` | **90 passaram**, 14,02s |
| `python manage.py check --settings=config.test_settings` | **0 problemas** |
| `python manage.py makemigrations --check --dry-run --settings=config.test_settings` | **Nenhuma alteração detectada** |
| `npm test` | **18 passaram, 0 falharam**, 1,70s |
| `npm run lint` | **Aprovado**, sem warnings |
| `npm run build` | **Aprovado**, Vite 7.3.6, 1.719 módulos, 8,15s |
| Chrome headless local | **20 combinações responsivas**, 0 overflow e 0 erros JavaScript |

O backend cobre lista e vazio de filiais, métricas exatas, detalhe, média, tendência,
404, atraso e contribuição, paginação, situação de entrega, filtros combinados,
período e sete formas de parâmetro inválido. O frontend cobre normalização de query,
render real, loading, erro, vazio, controles, links, drill-down, tabela e comparação.

Build final: CSS 292,96 kB (42,00 kB gzip) e JavaScript 469,39 kB
(152,08 kB gzip).

## 11. Validação visual

Foi usado Chrome headless local contra Django, seed completo, Pipeline V1 executada e
Vite. O fluxo Home → Operação → Contagem → voltar → Atrasos → Contagem confirmou 443
pedidos, 62 atrasos, 14,0%, 50 clientes afetados e taxa de 22,43% em Contagem. O filtro
`branch=2&delivery=late` permaneceu no histórico e retornou somente pedidos atrasados.

As rotas `/`, `/operation`, `/operation/delays` e `/operation/branches/2` foram
verificadas em 320, 375, 768, 1024 e 1440 px sem overflow. Não houve erro JavaScript.
O ambiente bloqueou Google Fonts e usou os fallbacks de sistema; uma requisição de
recurso estático respondeu 404 sem afetar o fluxo. Evidência estruturada:
[phase04-browser.json](validation/phase04-browser.json).

Capturas revisadas: [Operação desktop](screenshots/phase04-operation-desktop.png),
[Operação mobile](screenshots/phase04-operation-mobile.png),
[filial desktop](screenshots/phase04-branch-desktop.png),
[filial mobile](screenshots/phase04-branch-mobile.png),
[atrasos desktop](screenshots/phase04-delays-desktop.png) e
[atrasos mobile](screenshots/phase04-delays-mobile.png).

## 12. Arquivos criados

Lista completa da Fase 04 (**27 arquivos**):

- `backend/operations/operation/__init__.py`
- `backend/operations/operation/service.py`
- `backend/operations/operation_urls.py`
- `backend/operations/operation_views.py`
- `backend/operations/tests/test_operation.py`
- `frontend/src/hooks/useApiResource.js`
- `frontend/src/components/operation/BranchComparison.jsx`
- `frontend/src/components/operation/BranchDelayTrend.jsx`
- `frontend/src/components/operation/BranchTable.jsx`
- `frontend/src/components/operation/OperationMetrics.jsx`
- `frontend/src/components/operation/OrderFilters.jsx`
- `frontend/src/components/operation/OrderTable.jsx`
- `frontend/src/components/operation/PeriodSelector.jsx`
- `frontend/src/pages/OperationBranchPage.jsx`
- `frontend/src/pages/OperationDelaysPage.jsx`
- `frontend/src/pages/OperationPage.jsx`
- `frontend/src/styles/operation.css`
- `frontend/src/utils/operation.js`
- `frontend/src/utils/operation.test.js`
- `docs/PHASE04_REPORT.md`
- `docs/validation/phase04-browser.json`
- `docs/screenshots/phase04-operation-desktop.png`
- `docs/screenshots/phase04-operation-mobile.png`
- `docs/screenshots/phase04-branch-desktop.png`
- `docs/screenshots/phase04-branch-mobile.png`
- `docs/screenshots/phase04-delays-desktop.png`
- `docs/screenshots/phase04-delays-mobile.png`

## 13. Arquivos alterados

Lista completa da Fase 04 (**20 arquivos**):

- `README.md`
- `backend/config/urls.py`
- `backend/operations/analytics/queries.py`
- `backend/operations/serializers.py`
- `backend/operations/tests/test_analytics_boundaries.py`
- `docs/ARCHITECTURE.md`
- `docs/BACKEND_GUIDE.md`
- `docs/FRONTEND_GUIDE.md`
- `docs/ROADMAP_V2.md`
- `frontend/package.json`
- `frontend/src/App.jsx`
- `frontend/src/components/dashboard/BranchPerformance.jsx`
- `frontend/src/components/dashboard/KpiCard.jsx`
- `frontend/src/components/layout/AppLayout.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/hooks/useDashboardData.js`
- `frontend/src/services/api.js`
- `frontend/src/styles/responsive.css`
- `frontend/src/styles/theme.css`
- `frontend/src/utils/dashboard.js`

Alterações ainda não commitadas das Fases 01–03 e o `package-lock.json` da raiz foram
preservados. Nenhuma migration ou dependência foi criada nesta fase.

## 14. Limitações

- A data de referência continua fixa em 29/08/2026 e os snapshots não reconstroem o
  estado histórico de chamados ou estoque.
- Não há página própria de cliente ou produto; o fluxo atual chega a pedidos e mostra
  clientes afetados e produtos críticos como agregados.
- A média de filial é aritmética e inclui a própria filial; é contexto descritivo,
  não benchmark estatístico nem meta.
- A suíte e o QA usaram SQLite e Chrome headless. PostgreSQL/Supabase, dispositivo
  físico, leitor de tela e outros navegadores não foram executados.
- Fontes remotas foram bloqueadas no ambiente de QA; fallbacks de sistema mantiveram
  a interface utilizável.

## 15. Preparação para Fase 05

Filtros compartilháveis, identidade estável da filial, semântica documentada de atraso,
pedidos paginados e `metric_definition` fornecem o contexto que uma investigação pode
preservar. A próxima fase pode vincular um sinal a filial, período, conjunto de pedidos
e evidências sem reconstruir a navegação.

Antes de persistir investigações, definir lifecycle e identidade do alerta, política de
snapshot e quais filtros fazem parte do vínculo histórico. Causalidade, explicação por
IA e recomendações devem consumir evidências calculadas, sem alterar as regras desta
área ou atribuir causa a sinais correlacionados.
