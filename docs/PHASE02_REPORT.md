# Fase 02 — identidade visual e Home do OpsMind

Entrega local em 10/09/2026. Escopo: frontend, preservando a base da Fase 01.

## 1. Resumo

O OpsMind passou a apresentar a operação com uma base clara e quente, texto grafite,
sidebar discreta, títulos em Manrope e uso pontual de cor. Saúde e prioridades têm
pesos próprios; separadores e espaço substituem a repetição de cards. Os fluxos
existentes de alertas, investigação, recomendações, ações e assistente permanecem.

A composição segue os princípios descritos no pedido. Nenhuma imagem de referência
foi anexada. Django, DRF, React, Vite, Chart.js, PostgreSQL/Supabase, Gemini e Vercel
foram preservados. Nenhum endpoint, regra analítica, modelo ou migration foi alterado
nesta fase; nenhuma dependência foi adicionada ao projeto.

Capturas finais revisadas:
[desktop, 1440px](screenshots/phase02-home-desktop.png),
[tablet, 820px](screenshots/phase02-home-tablet.png) e
[mobile, 390px](screenshots/phase02-home-mobile.png).

## 2. Home

A abertura identifica a operação e separa a referência analítica do horário da
consulta. A leitura segue esta ordem:

1. **Saúde operacional:** score grande, classificação, barra e explicação dos seis
   componentes da fórmula. Sem pedidos no período, apresenta ausência de base em
   vez de interpretar o score 100 retornado pela fórmula como operação saudável.
2. **Precisa de atenção:** quantidade real de alertas, prioridade principal, evidência
   e acesso à investigação/lista. Âmbar indica atenção; tom crítico depende de alerta
   crítico. Zero alertas e falha de consulta têm apresentações distintas.
3. **Indicadores complementares:** faturamento, pedidos, atrasos e chamados ativos em
   uma faixa com separadores. Clientes impactados aparecem na prioridade e estoque no
   feed, conforme os endpoints disponíveis, sem fabricar agregados.
4. **O que mudou:** comparativos e descrições reais, com valores destacados. Não é um
   histórico de eventos: não recebe horários inventados. Estoque é condição da base.
5. **Dados da operação:** origem sintética, referência e qualidade ainda não medida.
6. **Entregas e filiais:** série mensal com meta, tabela acessível e taxas de atraso
   das filiais com alerta ativo, comparadas à média geral.

No seed completo usado em QA, a tela apresentou score **69**, **4 alertas**, **431
pedidos**, **60 atrasados**, **207 chamados ativos** e Contagem com **21,2%** de atraso
contra média de **13,9%**, respeitando o arredondamento já usado nos formatadores.
O backend não fornece ranking REST de todas as filiais: a seção explicita esse limite
em “Filiais em atenção” e liga à investigação existente. Não há score fictício por unidade.

## 3. Design system

| Grupo | Decisão implementada |
| --- | --- |
| Base | `--background: #fafaf7`, sidebar `#f3f4ef`, superfície branca e texto `#252d29` |
| Identidade | Primária verde-azulada (`--primary-600: #346c6e`); aliases existentes mantidos |
| Status | Verde `#376547`, âmbar `#825418`, vermelho `#a63e35`; superfícies de atenção e criticidade próprias |
| Tipografia | `--font-body` Inter e `--font-heading` Manrope, com fallback de sistema |
| Escala | `sm/md/lg` preservados; novos `section`, `title` e `display`, títulos/números com `clamp()` |
| Espaçamento | `--space-1..6` preservados; `--space-7: 48px` e `--space-8: 64px` |
| Contornos | Bordas claras, sombra de baixa intensidade e raios de 4/8/12px |
| Shell | Sidebar de 220px e topbar desktop de 70px |
| Gráfico | Mesmos tokens CSS lidos no canvas, grid discreto, eixo 0–100%, lacunas sem base |

A ordem dos arquivos CSS da Fase 01 foi preservada. Os estilos de alertas, ações e
assistente receberam compatibilidade visual, texto auxiliar mais legível, badges
compartilhados e correção da altura do campo do assistente no celular. Não houve
reorganização funcional dessas páginas.

## 4. Componentes

Criados: `SectionState`, `DataFlow` e `BranchPerformance`. O hook `useDashboardData`
coordena as leituras da Home; `utils/dashboard.js` adapta unidades e evidências;
`demoMetadata.js` concentra os metadados demonstrativos.

Reutilizados e evoluídos: `HealthScore`, `KpiCard`, `TrendChart`, `ChangesPanel`,
`AlertPreview`, `AppLayout`, `Sidebar` e `Topbar`. `AlertPreview` agora recebe a lista
por props, compartilhando a mesma consulta que seleciona as investigações de filiais.
O cliente HTTP, os formatadores e as rotas existentes foram preservados.

As leituras têm cancelamento por rodada e estados independentes. Uma falha não oculta
as seções que responderam. Atualizar/Tentar novamente reinicia a rodada; logs de
falha permanecem no desenvolvimento, com mensagens simples para o usuário.

## 5. Pipelines

`DataFlow` introduz a origem “Dados sintéticos → Base operacional → Indicadores”.
Não afirma execução de ERP, validação, transformação ou carga inexistentes.
`demoMetadata.js` registra “Atualização não monitorada” e “Ainda não medida”.

A sidebar reserva Pipelines, Qualidade e Fontes como “Em breve”. O componente e o
rodapé estão preparados para receber metadados reais na Fase 03. O horário de consulta
é do navegador, a referência é da API e a última publicação ainda não existe como
métrica: esses conceitos permaneceram separados.

## 6. Responsividade

| Faixa | Comportamento |
| --- | --- |
| A partir de 1200px | Sidebar fixa, blocos assimétricos, indicadores em faixa e espaçamento amplo |
| 992–1199px | Menor espaçamento, proporções ajustadas e sidebar fixa |
| 768–991px | Drawer, conteúdo usa a largura disponível e mantém duas colunas na Home |
| 576–767px | Home em coluna única, indicadores 2×2 e blocos secundários reorganizados |
| Até 575px | Margens de 20px, feed com valores abaixo do texto, atualização por ícone e topbar compacta |

Foram verificadas Home, Alertas, Investigação, Ações e Assistente em **320, 390, 820,
1280 e 1440px**: **25 combinações sem overflow horizontal**. Capturas da Home em
três larguras e do menu/assistente móvel foram inspecionadas visualmente. O menu
rola internamente quando necessário, bloqueia o fundo e fecha ao navegar.

## 7. Acessibilidade

- Skip link, landmarks e títulos por seção; ícones decorativos ocultos dos leitores.
- Botões com nomes acessíveis, foco visível e filtros com `aria-pressed`.
- Drawer com nome, `role="dialog"`, `aria-modal`, fundo e skip link inertes, Tab e
  Shift+Tab contidos, Escape para fechar e retorno do foco ao botão de abertura.
- Visibilidade imediata na abertura do drawer evita perder o foco durante a transição.
- Score com semântica de medidor; status e severidade também expressos em texto.
- Tabela alternativa ao Chart.js, com caption, cabeçalhos, valores e denominadores.
- Erro/loading/vazio com mensagens e papéis de anúncio; movimento reduzido respeitado.

Teclado foi exercitado no Chrome. Não foi realizada auditoria completa WCAG, medição
exaustiva de contraste, teste com leitor de tela ou dispositivos físicos.

## 8. Arquivos criados

Lista da Fase 02, sem incluir os arquivos já criados na Fase 01 (**12 arquivos**):

- `frontend/src/components/common/SectionState.jsx`
- `frontend/src/components/dashboard/BranchPerformance.jsx`
- `frontend/src/components/dashboard/DataFlow.jsx`
- `frontend/src/data/demoMetadata.js`
- `frontend/src/hooks/useDashboardData.js`
- `frontend/src/utils/dashboard.js`
- `frontend/src/utils/dashboard.test.js`
- `docs/PHASE02_REPORT.md`
- `docs/screenshots/phase02-home-desktop.png`
- `docs/screenshots/phase02-home-tablet.png`
- `docs/screenshots/phase02-home-mobile.png`
- `docs/validation/phase02-browser.json`

## 9. Arquivos alterados

Comparação por hash com o estado recebido da Fase 01 (**24 arquivos**):

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/FRONTEND_GUIDE.md`
- `docs/ROADMAP_V2.md`
- `frontend/package.json` — somente comando de testes, sem dependências novas.
- `frontend/src/components/dashboard/AlertPreview.jsx`
- `frontend/src/components/dashboard/ChangesPanel.jsx`
- `frontend/src/components/dashboard/HealthScore.jsx`
- `frontend/src/components/dashboard/KpiCard.jsx`
- `frontend/src/components/dashboard/TrendChart.jsx`
- `frontend/src/components/layout/AppLayout.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/components/layout/Topbar.jsx`
- `frontend/src/pages/AlertsPage.jsx` — semântica do filtro selecionado.
- `frontend/src/pages/DashboardPage.jsx`
- `frontend/src/styles/actions.css`
- `frontend/src/styles/alerts.css`
- `frontend/src/styles/assistant.css`
- `frontend/src/styles/base.css`
- `frontend/src/styles/dashboard.css`
- `frontend/src/styles/responsive.css`
- `frontend/src/styles/shared.css`
- `frontend/src/styles/theme.css`
- `frontend/src/styles/tokens.css`

Arquivos Python do backend, migrations, `services/api.js`, `App.jsx`, `main.jsx`,
`package-lock.json` e `vercel.json` permanecem idênticos ao início desta fase. O Git
já continha alterações da Fase 01; elas não foram descartadas nem atribuídas a esta entrega.
Artefatos locais de build e ferramentas temporárias de QA não fazem parte dessa lista.

## 10. Testes

| Verificação executada | Resultado final |
| --- | --- |
| `npm test` | **8 passaram, 0 falharam**, via `node:test` |
| `npm run lint` | **Aprovado**, sem warnings |
| `npm run build` | **Aprovado**, Vite 7.3.6, 1705 módulos, 7,51s |
| `python -m pytest` | **63 passaram**, 12,38s, `config.test_settings` |
| `python manage.py check --settings=config.test_settings` | **0 problemas** |
| `python manage.py makemigrations --check --dry-run --settings=config.test_settings` | **Nenhuma alteração detectada** |
| Chrome headless + Playwright temporário | **11 grupos aprovados**, 25 combinações sem overflow, **0 erros JavaScript não tratados** |

Build final: CSS **270,66 kB** (**38,59 kB gzip**); JavaScript **437,95 kB**
(**144,63 kB gzip**). As verificações do backend foram repetidas como regressão,
embora seus arquivos não tenham sido alterados nesta fase.

`git diff --check` não encontrou erros de whitespace; o Git emitiu apenas avisos
de conversão LF → CRLF do ambiente Windows. As listas de arquivos, links locais
da documentação e leitura UTF-8 também foram conferidos.

Os oito testes do frontend cobrem Decimal serializado, comparação sem base, resumo
ausente, semântica do feed, taxas reais das filiais, ausência de ranking, evidências
incompletas e unidades/valores inválidos, agrupados nos casos de `dashboard.test.js`.

A sessão de navegador verificou:

1. Dados da Home, seis componentes do score e seis linhas da tabela de tendências.
2. Filial → investigação → adicionar ação → concluir → reabrir.
3. Conflito HTTP 409 real, gerado por ação criada após carregar a recomendação.
4. Filtro de severidade e investigação inexistente com 404.
5. Assistente mock, resumo executivo e intenção fora do escopo.
6. Identificação do fallback com payload interceptado (apresentação, não Gemini real).
7. Resumo com HTTP 500, preservação de outros blocos e recuperação por retry.
8. Resposta atrasada, estado de loading e recuperação.
9. Payloads de base vazia, sem score enganoso, alertas ou histórico fabricado.
10. Drawer com Tab/Shift+Tab, Escape, retorno de foco e fechamento ao navegar.
11. Cinco rotas nas cinco larguras, sem overflow horizontal.

Resultado estruturado: [phase02-browser.json](validation/phase02-browser.json).
QA usou Vite em `127.0.0.1:5174`, Django em `127.0.0.1:8001`, SQLite descartável,
`seed_demo` completo e provider mock. As ações do teste foram persistidas somente
nessa base temporária. Playwright foi instalado em diretório temporário, sem
alterar dependências do repositório; essa sessão não constitui uma suíte E2E permanente.

## 11. Limitações

- O navegador integrado não disponibilizou sessão. A renderização e a inspeção
  foram realizadas em Chrome headless local isolado; outros motores não foram testados.
- Não houve imagem de referência anexada, teste em dispositivo físico, leitor de
  tela, Gemini real, Supabase ou deploy na Vercel nesta fase.
- As fontes dependem de Google Fonts, com fallback de sistema. Falhas dessa origem
  podem mudar as métricas tipográficas.
- As filiais exibidas são somente as que têm alerta de desempenho e evidências
  completas. O adaptador depende dos labels/unidades atuais da investigação.
- Não há timestamp de carga, taxa de qualidade, eventos históricos de mudanças,
  histórico do score nem snapshot transacional entre as consultas.
- Os estados vazios do frontend foram testados com respostas interceptadas. Isso
  não resolve as falhas anteriores da IA em base vazia/parcial nem diferenças de
  fronteira de data/fuso entre SQL SQLite e ORM, registradas na Fase 01.
- Troca de investigação sem reiniciar todos os estados e resposta anterior do
  assistente durante nova consulta continuam como dívidas já documentadas.

## 12. Próxima fase — Pipeline V1

Antes de implementar, definir uma fonte pequena, formato, chaves, janela e política
de publicação. Seguir a proposta de [BACKEND_GUIDE.md](BACKEND_GUIDE.md): comando
Django simples, histórico de execução, idempotência, rejeições com motivos e lotes
que só se tornam visíveis quando a publicação termina com sucesso.

O contrato deverá distinguir execução em andamento/falha/sucesso, última publicação
bem-sucedida, referência dos dados, volumes recebidos/aceitos/rejeitados e critérios
de qualidade. A taxa de qualidade precisa de denominador e definição explícitos.

Proteger base vazia/parcial e limites de fuso antes da primeira fonte externa.
Depois conectar `DataFlow` e o rodapé da sidebar ao histórico real e substituir
`demoMetadata` nos pontos apropriados. Preservar os endpoints analíticos existentes;
uma listagem completa de filiais pertence à evolução de Operação. Airflow, Spark,
dbt, WebSockets e novos serviços não são necessários para iniciar essa entrega.
