# Guia do frontend

## Rotas, dados e componentes

React + Vite usam React Router, Bootstrap 5, Lucide React e Chart.js por
`react-chartjs-2`. Não há store global nem biblioteca de cache de consultas.
A Fase 02 evoluiu o shell e a Home; a Fase 04 acrescentou o drill-down operacional.
A Fase 03.5, aplicada sobre o estado atual, apresenta a interface como OpsMind2 e
acrescenta tokens semânticos, tema escuro e gráficos responsivos ao tema.

| Rota | Página | Dados e estado |
| --- | --- | --- |
| `/` | `DashboardPage` | `useDashboardData`: resumo, tendências, mudanças, alertas, filiais e pipeline; estados independentes |
| `/operation` | `OperationPage` | Resumo, comparação de filiais, atenção e pedidos paginados com filtros em URL |
| `/operation/delays` | `OperationDelaysPage` | Taxa geral e contribuição das filiais, com links já filtrados por atraso |
| `/operation/branches/:branchId` | `OperationBranchPage` | Saúde, tendência, comparação, sinais e pedidos da filial |
| `/alerts` | `AlertsPage` | Lista e filtro local por severidade; loading, erro e vazio |
| `/alerts/:alertKey` | `AlertInvestigationPage` | Investigação e recomendações em cargas independentes; 404 específico; criação de ação |
| `/actions` | `ActionsPage` | Lista, contagens e filtros locais; PATCH de status e reordenação após resposta |
| `/assistant` | `AssistantPage` | Pergunta/resumo executivo, loading e erro; somente interação atual |
| `/pipelines` | `PipelinesPage` | Estado real, etapas, contagens, histórico e rejeições de pedidos |

`AppLayout` contém sidebar, topbar, menu móvel e `<Outlet>`. O título da Home fica na
própria página; os demais estão no layout. O indicador “API disponível” consulta
`/api/health/` ao montar: não significa banco, Gemini ou dados atualizados.

A sidebar agrupa Hoje, Decisões, Dados e IA. Operação e Pipelines são rotas funcionais.
Investigações (futura lista), Qualidade e Fontes permanecem “Em breve”. As
investigações atuais continuam acessíveis pelos alertas e pela filial da Home.
Não registrar uma rota sem uma entrega real ou placeholder explicitamente acordado.

## Composição da Home

`HealthScore`, `KpiCard`, `TrendChart`, `ChangesPanel` e `AlertPreview` foram
reaproveitados e recebem dados por props. `AlertPreview` deixou de fazer sua própria
requisição: a lista alimenta prioridades e a seleção de investigações de filiais.
`DataFlow` apresenta a origem demonstrativa; `BranchPerformance` usa o ranking real
de `/api/operation/overview/` e abre a filial correspondente. O KPI de atrasos abre
`/operation/delays?days=30`. `SectionState` padroniza carregamento, falha com retry e ausência de base.
`MetricGrid` e `EvidenceSection` continuam locais à investigação, sem extração prematura.

`useDashboardData` coordena leituras com um `AbortController` por rodada. Falhas de
uma seção preservam as outras; o botão Atualizar e os retries iniciam nova rodada,
limpam o retrato anterior e cancelam respostas pendentes. Cada seção tem
`{ status, data }`. Isso não cria consistência transacional entre endpoints.

`utils/dashboard.js` adapta apresentação, sem recalcular regras:

- Indicadores preservam unidades, valores monetários serializados e comparação sem base.
- “O que mudou” é um feed de comparativos, sem horários de eventos inventados. Estoque
  é condição da base; chamados ativos abrangem toda a base, independentemente da janela.
- Filiais vêm do contrato completo de Operação. A Home só ordena/apresenta as linhas;
  score, taxa, volume, receita e comparações permanecem no backend.
- A Home omite a interpretação de saúde quando não há pedidos no período, mesmo que
  a fórmula atual da API devolva 100. Isso é uma decisão de apresentação, não de cálculo.

`TrendChart` mantém Chart.js, lê cores e fonte dos tokens CSS após montagem e usa
0–100%. Meses sem pedidos elegíveis viram lacunas, não desempenho zero. “Ver dados”
expõe tabela com mês, percentual e denominador; gráficos e tabela usam o mesmo payload.

## Consumir a API e criar uma página

1. Acrescente uma função de domínio em `services/api.js`, usando `request` e o endpoint
   existente. Passe `options` para manter suporte a `AbortSignal`.
2. Crie a página em `pages/`. Para leituras em `useEffect`, use `AbortController`,
   trate falhas e cancele no cleanup. Extraia um hook quando a coordenação justificar.
3. Diferencie carregamento, falha e lista vazia. Não substituir indisponibilidade
   por zero, números fictícios ou uma afirmação de normalidade.
4. Registre rota em `App.jsx`, título em `AppLayout` e link em `Sidebar`, quando aplicável.
5. Reutilize formatadores, tokens e estados. Valide teclado, dados e larguras relevantes.

O cliente centraliza URL, headers e erros. `error.status` distingue 404/409/503;
`error.data` preserva o payload, inclusive validação por campo. Nem todas as páginas
apresentam esse detalhe: o assistente mostra erro genérico. Há cancelamento nas
leituras principais, mas não em todas as mutações.

Na criação de ação, envie somente `alert_key` e `recommendation_key`. O backend
resolve conteúdo oficial; 409 significa ação já aberta. No PATCH, envie somente
`status`. A interface aguarda confirmação antes de atualizar o item. A ordenação de
ações também existe no cliente para manter a ordem após atualização; mudanças nela
precisam ser coordenadas com o backend.

`utils/formatters.js` centraliza BRL, números, percentuais e datas. Dinheiro pode
chegar como string; comparação sem base chega como `null`. `utils/alerts.js`
distingue porcentagem, variação relativa e pontos percentuais. Não recalcular
indicadores nas páginas. `formatDate` recebe data sem horário; `formatBrazilDate`
fixa São Paulo; `formatDateTime` usa o fuso do navegador.

`utils/operation.js` lê somente 7/30/90 dias, normaliza página e mantém filial, status
e atraso na query string. Atualizações usam a forma funcional de `setSearchParams`,
evitando que duas mudanças rápidas percam o primeiro filtro. `useApiResource` reúne
loading, erro, sucesso, cancelamento e retry das leituras da área.

## Estilos e tokens

`main.jsx` importa Bootstrap antes de `styles/theme.css`, que mantém os imports:

| Arquivo em `src/styles/` | Responsabilidade |
| --- | --- |
| `tokens.css` | Paleta quente, semântica de status, fontes, escalas, bordas e dimensões |
| `base.css` | HTML, shell, topbar, navegação, controles, foco e estados |
| `dashboard.css` | Composição da Home, indicadores, feed, gráfico, filiais e origem |
| `alerts.css` | Catálogo, investigação, evidências e recomendações |
| `assistant.css` | Perguntas, resposta e evidências do assistente |
| `actions.css` | Resumo, filtros e itens do plano |
| `pipelines.css` | Execução atual, etapas, contagens, histórico e rejeições |
| `operation.css` | Resumo, comparação, tendência, filtros, tabelas e drill-down de Operação |
| `charts.css` | Donut de qualidade, centro, legenda textual e variações responsivas |
| `shared.css` | Animação, classes `feature-*`, badges compartilhados e backdrop padrão |
| `responsive.css` | Sobrescritas por largura e movimento reduzido |

Os seletores são globais, não CSS Modules. A ordem dos imports faz parte da cascata.
Os aliases antigos de cor foram preservados para compatibilidade com outras páginas.
A base usa `--background` quente, texto grafite, primária verde-azulada, verde para
saúde, âmbar para atenção e vermelho para criticidade. A superfície forte de
prioridades só usa tom crítico quando há alerta crítico.

`--space-1..8`: 4/8/12/16/24/32/48/64px. `--font-size-sm/md/lg`:
0,75/0,875/1rem, mais `section`, `title` e `display`. Raios: 4/8/12px.
Sidebar: 220px; topbar desktop: 70px. Manrope nos títulos e Inter no corpo dependem
de Google Fonts, com fontes de sistema como fallback. Nem toda dimensão local virou
token; preserve valores específicos quando expressam a composição de um componente.

Os papéis `--text-primary`, `--text-secondary`, `--primary`, `--success`, `--warning`,
`--danger`, `--info` e `--neutral-500` mantêm o mesmo significado nos dois temas.
`[data-theme="dark"]` troca superfícies, textos, bordas, estados e tokens de gráfico;
componentes não mantêm uma paleta escura própria. Cores fortes remanescentes ficam
somente em `tokens.css`.

`ThemeToggle` alterna claro/escuro, persiste `opsmind-theme` no `localStorage` e anuncia
a ação por texto e `aria-label`. Na primeira visita, usa `prefers-color-scheme`. Um
script pequeno em `index.html` define `data-theme` antes do CSS e da montagem React,
evitando o flash claro para quem prefere escuro. Falha de armazenamento volta à
preferência do sistema sem impedir a aplicação.

Abaixo de 1200px, espaçamento e proporções se ajustam; abaixo de 992px, sidebar vira
drawer; abaixo de 768px, Home fica em uma coluna com indicadores 2×2; abaixo de 576px,
o feed empilha valores e a topbar reduz metadados secundários. O breakpoint do drawer
é compartilhado entre CSS e `matchMedia` em `AppLayout`: altere ambos juntos.

O drawer bloqueia o fundo com `inert`, restringe Tab/Shift+Tab, fecha com Escape e
retorna foco ao botão. Visibilidade muda imediatamente para permitir o foco inicial;
a transição fica apenas no deslocamento. Há skip link, foco visível, labels de botões,
estado `aria-pressed` nos filtros, tabela alternativa e suporte a movimento reduzido.
Isso não equivale a uma certificação completa de acessibilidade.

## Integração com Pipeline V1

`DataFlow`, o rodapé da sidebar e `PipelinesPage` consomem a API real. O objeto
`demoMetadata.js` mantém apenas identidade da organização e rótulo da fonte;
etapas, qualidade e freshness não existem mais como valores locais.

`utils/pipelines.js` traduz status e ordena as quatro etapas para apresentação.
`formatRelativeTime` calcula texto relativo a partir de `last_published_at`.
Referência analítica, horário da consulta e publicação continuam separados. Uma
falha mais recente não apaga a data da última publicação válida.

## Área Operação

`OperationMetrics`, `BranchTable`, `BranchComparison`, `BranchDelayTrend`,
`OrderFilters`, `OrderTable` e `PeriodSelector` recebem contratos já calculados. O
gráfico de linha continua em Chart.js e responde à evolução diária da taxa de atraso.
No mobile, tabelas viram blocos verticais, filtros ocupam uma coluna e a comparação
mantém filial, média e diferença legíveis sem rolagem horizontal.

O detalhe mantém o contexto na URL ao abrir filial, filtrar pedidos e usar voltar ou
avançar. Links representam navegação; seletores e paginação usam controles próprios.
As três telas tratam carregamento, falha e ausência válida de dados.

`useChartPalette` observa a troca de `data-theme` e relê uma única tradução dos tokens
em `utils/charts.js`. Linhas, eixos, grids, labels e tooltips são redesenhados no mesmo
tema da interface. `DataQualityDonut` usa somente a relação válida de parte-do-todo da
Pipeline V1: válidos × rejeitados. Valor e percentual permanecem em legenda textual e
no tooltip, então o gráfico não depende apenas de verde e vermelho.

## Validação

Em `frontend/`:

```powershell
npm test
npm run lint
npm run build
```

`npm test` usa `node:test`, sem dependências novas: 24 testes protegem dashboard,
pipeline, filtros, render, estados, links, tabela, comparação, tema, persistência,
paleta e donut. A Fase 03.5 repetiu a verificação em Chrome headless local contra API,
seed e pipeline reais nos temas claro e escuro;
não há suíte E2E instalada no projeto.

Proteger navegação/reload, filtros, 404/409, adicionar/concluir/reabrir ação,
loading/erro/vazio, retorno da API, tabela de tendências e teclado do drawer.
Resultados e capturas: [Fase 02](PHASE02_REPORT.md), [Fase 03](PHASE03_REPORT.md) e
[Fase 04](PHASE04_REPORT.md).
O refinamento visual e suas capturas estão no [relatório da Fase 03.5](PHASE035_REPORT.md).

Dívidas anteriores permanecem: troca de chave na mesma página não reinicia todos os
estados; o assistente pode manter resposta anterior durante nova consulta. A IA em
base vazia/parcial continua registrada na [auditoria da Fase 01](AUDIT_PHASE01.md).
A divergência conhecida da consulta de filial nas fronteiras de fuso foi corrigida
com ORM e testes; a suíte ainda não foi repetida em PostgreSQL/Supabase.
