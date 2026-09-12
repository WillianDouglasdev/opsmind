# Fase 03.5 — identidade OpsMind2 e cor semântica

Entrega local em 12/09/2026. Esta etapa refinou a apresentação do estado atual das
Fases 01–04. Backend, APIs, models, pipeline, regras, rotas e funcionalidades foram
preservados.

## Resumo

A interface agora se apresenta como **OpsMind2**. O shell possui temas claro e escuro,
alternância acessível, persistência e escolha inicial pelo sistema. Saúde, KPIs,
mudanças e pipeline receberam acentos semânticos, mantendo whitespace, tipografia e
composição editorial da Fase 02.

O único gráfico novo é o donut **válidos × rejeitados** da Pipeline V1, exibido na Home
e em Pipelines. Ele representa uma relação parte-do-todo comprovada pelo contrato e
repete valor e percentual em texto. Não foi criado donut “no prazo × atrasados” porque
os pedidos restantes incluem cancelados e estados em andamento; chamá-los de “no
prazo” seria incorreto.

## Tema e persistência

`tokens.css` define papéis estáveis para background, superfícies, textos, bordas,
primary, success, warning, danger, info, neutral e gráficos. O bloco
`[data-theme="dark"]` troca valores sem mudar o significado: verde continua saudável,
âmbar continua atenção e vermelho continua crítico.

`ThemeToggle` aplica e persiste `opsmind-theme`. Na ausência de escolha salva,
`prefers-color-scheme` decide o tema. O script no `<head>` de `index.html` define o
atributo antes do CSS e do React, evitando um primeiro frame claro no modo escuro.
Falhas de `localStorage` têm fallback seguro.

## Gráficos

`useChartPalette` observa `data-theme` e relê a tradução central de `utils/charts.js`.
Os dois gráficos de linha e o donut recebem cores de série, labels, grid, tooltip,
superfície e fonte pelos mesmos tokens da interface. A troca de tema redesenha canvas
sem reload.

O donut desativa a legenda interna do Chart.js e usa uma legenda HTML com “Válidos” e
“Rejeitados”, contagens e percentuais. O canvas tem nome acessível e o tooltip repete
essas informações. Na execução real validada: 12 válidos, 4 rejeitados e 75,0%.

## Cor como informação

- Saúde usa status textual, ponto, barra e cor semântica.
- Faturamento, pedidos, atrasos e chamados usam pequenos accents e números em tons
  success, info, danger e warning.
- “O que mudou” combina ícone, direção, texto e cor; nenhum estado depende só da cor.
- Pipeline combina labels, ícones, bordas, números e donut para sucesso, rejeição,
  execução e falha.
- Hardcodes de cor nos estilos de páginas foram substituídos por tokens centralizados.

## Identidade

Título, descrição, sidebar, breadcrumb, ARIA e assistente exibem OpsMind2/OpsMind2 AI.
Identificadores internos, pacote, apps Django, URLs, chaves de log e storage continuam
com seus nomes existentes quando a troca não traria benefício funcional.

## Testes

| Verificação | Resultado final |
| --- | --- |
| `python -m pytest -q` | **90 passaram** |
| `python manage.py check --settings=config.test_settings` | **0 problemas** |
| `python manage.py makemigrations --check --dry-run --settings=config.test_settings` | **Nenhuma alteração detectada** |
| `npm test` | **24 passaram, 0 falharam** |
| `npm run lint` | **Aprovado**, sem warnings |
| `npm run build` | **Aprovado**, Vite 7.3.6, 1.724 módulos |

Os seis testes frontend novos cobrem prioridade do tema salvo, preferência do sistema,
armazenamento indisponível, aplicação/persistência, labels do controle, paleta de
Chart.js e conteúdo textual do donut. O teste de navegador cobriu interação real do
tooltip e atualização dos canvas.

## Validação visual

Chrome headless local foi executado contra Vite, Django, seed completo e Pipeline V1.
Foram verificadas 30 combinações principais: Home, Pipelines e Operação × claro/escuro
× 320/375/768/1024/1440 px. Outras 20 combinações cobriram Alertas, Ações, Assistente,
Atrasos e filial em 375/1440 px nos dois temas. Resultado: nenhum overflow horizontal
e nenhum erro JavaScript.

Dez pares críticos de texto/fundo foram medidos. As razões ficaram entre **4,84:1** e
**16,13:1**, acima do mínimo de 4,5:1 adotado para texto comum. O ambiente bloqueou
Google Fonts; os fallbacks de sistema foram conferidos e a restrição não afetou o QA.
Resultado estruturado: [phase035-browser.json](validation/phase035-browser.json).

Capturas revisadas:

- [Home clara — desktop](screenshots/phase035-home-light-desktop.png)
- [Home escura — desktop](screenshots/phase035-home-dark-desktop.png)
- [Home clara — mobile](screenshots/phase035-home-light-mobile.png)
- [Home escura — mobile](screenshots/phase035-home-dark-mobile.png)
- [Pipelines clara — desktop](screenshots/phase035-pipelines-light-desktop.png)
- [Pipelines escura — desktop](screenshots/phase035-pipelines-dark-desktop.png)

## Arquivos criados

Foram criados 15 arquivos:

- `frontend/src/components/charts/DataQualityDonut.jsx`
- `frontend/src/components/layout/ThemeToggle.jsx`
- `frontend/src/hooks/useChartPalette.js`
- `frontend/src/styles/charts.css`
- `frontend/src/utils/charts.js`
- `frontend/src/utils/theme.js`
- `frontend/src/utils/theme.test.js`
- `docs/PHASE035_REPORT.md`
- `docs/validation/phase035-browser.json`
- seis capturas `docs/screenshots/phase035-*.png`

## Arquivos alterados

Foram alterados 24 arquivos: `README.md`, `docs/FRONTEND_GUIDE.md`,
`docs/ROADMAP_V2.md`, `frontend/index.html`, `frontend/package.json`, sete arquivos
CSS existentes (`tokens`, `theme`, `base`, `dashboard`, `pipelines`, `operation` e
`responsive`), quatro folhas de áreas (`actions`, `alerts`, `assistant` e `shared`),
`Topbar.jsx`, `Sidebar.jsx`, `DataFlow.jsx`, `TrendChart.jsx`,
`BranchDelayTrend.jsx`, `PipelinesPage.jsx`, `AssistantPage.jsx` e
`operation.test.js`.

Não houve alteração de backend, migration, contrato HTTP, dependência ou lockfile.

## Limitações

- O QA automatizado visual usou Chrome headless; não substitui teste em dispositivo
  físico, leitor de tela ou outros motores de navegador.
- A fonte remota foi bloqueada pelo ambiente de validação. As fontes do sistema são
  fallback explícito, mas a aparência com Google Fonts depende de acesso externo.
- O contraste medido cobre elementos críticos e não constitui auditoria WCAG completa.
- Alertas não receberam donut: as barras e labels atuais permitem comparação mais
  precisa com o pequeno conjunto de severidades da demo.
