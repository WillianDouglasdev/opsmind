# Auditoria e entrega — Fase 01

Data: 10/09/2026. Escopo: leitura do código e configurações locais, organização,
comentários e proteção incremental. Sem redesign, novos endpoints, migrations,
dependências, ETL ou deploy. Não houve consulta a dados do Supabase nem uso real do
Gemini; a tentativa inicial de conexão da suíte foi bloqueada pelo ambiente.

## 1. Estado atual

Frontend React/Vite com cinco páginas, React Router, Bootstrap, CSS global, Lucide e
Chart.js. O cliente HTTP é centralizado; estado e carregamento ficam nas páginas.
Backend Django/DRF com apps `core` e `operations`, oito models, duas migrations
próprias, consultas analíticas, quatro tipos de alerta, investigação e recomendações
determinísticas, ações persistidas e IA por mock/Gemini. Banco SQLite local ou
PostgreSQL/Supabase por ambiente. Não existem repositories separados, pipeline ou
persistência de alertas/investigações/recomendações.

O comando `seed_demo` gera a empresa fictícia em uma transação, com seed 42 e data
29/08/2026. A API recalcula métricas a partir dos models; o frontend não contém
dataset operacional próprio. Detalhes de rotas, entidades, exclusões, variáveis e
fluxos estão nos [guias](ARCHITECTURE.md).

## 2. Pontos fortes

- Separação útil entre consultas, regras, investigação, geração textual e persistência.
- Regras determinísticas e evidências estruturadas independentes do texto do LLM.
- Constraints, Decimal para valores monetários, transações e proteção de ações abertas.
- API pequena, funções de domínio no cliente e formatadores PT-BR compartilhados.
- Cenário reproduzível e testes de modelos, analytics, endpoints, IA e ações.
- Cancelamento de leituras, estados de erro/vazio e layout responsivo já presentes.

## 3. Dívidas técnicas e evidências

| Prioridade / momento | Achado | Encaminhamento |
| --- | --- | --- |
| Alta, antes de ampliar períodos | `branch_delay_rates` passa datetimes com fuso diretamente ao SQL; em SQLite difere do recorte ORM | Normalizar parâmetros pelo backend de banco e testar limites de período nos dois bancos |
| Alta, antes de ingestão | `_delivery_context` e `_branch_context` usam `max()` sem caso vazio | Definir resposta sem dados e testar todos os contextos; não confundir ausência com operação saudável |
| Alta, antes de ingestão | Mock e recomendações formatam algumas variações `None` como float | Tratar “sem base” em texto e proteger cenários com apenas um período |
| Alta, antes de ingestão | Atrasos dependem de status; total do pedido não é derivado automaticamente dos itens | Contrato explícito de normalização e testes para cargas externas |
| Média, antes de persistir investigações | Chave de alerta por filial deriva de nome via slug; colisões/renomeações afetam origem das ações | Definir identidade estável e migração compatível das chaves |
| Média, antes de cargas concorrentes | Dashboard/alertas/IA repetem consultas; não há snapshot comum ou orçamento de queries | Medir consultas e definir publicação consistente de lotes antes de introduzir cache |
| Média, frontend V2 | Troca de `alertKey` não reinicia todos os estados; assistente pode mostrar resposta anterior durante nova consulta | Testar navegação entre chaves e transições de loading/erro antes da extração de componentes |
| Média, frontend V2 | Fetch/loading/erro repetidos; ordenação de ações e enumerações duplicadas entre cliente e servidor | Compartilhar só padrões comprovados, mantendo contrato explícito |
| Média, frontend V2 | Chart.js tem estilo próprio e eixo 60–100; opções do gráfico sem ação | Integrar identidade visual e revisar escala antes de dados externos |
| Média, crescimento do domínio | `queries.py` (453 linhas antes), seed (599), investigação (260) e serviço IA (269) concentram leitura/composição | Separar por domínio conforme crescer; seed mantém geração e catálogo juntos por ora |
| Baixa, manutenção | `_pt_number`, `_currency` e construção de métricas repetidos; conversão monetária difere entre módulos | Unificar quando houver testes de apresentação/sem base; evitar alteração silenciosa de arredondamento |
| Antes de uso além da demo | API pública, sem isolamento por usuário, limites de uso ou autorização de ações | Definir requisitos de acesso e consumo da IA antes de ampliar o público |

**Diagnóstico de período reproduzido em SQLite em memória:** criar uma filial e dois
pedidos, um `delayed` em 30/07/2026 às 23h e um `delivered` em 29/08/2026 às 23h,
com datetimes em São Paulo. Para a referência 29/08, o ORM conta zero atrasos no
período atual; o SQL por filial conta um. O primeiro pedido deveria estar somente
no período anterior. Este problema já existia e não foi corrigido nesta fase para
não mudar cálculo sem uma entrega específica de regressão nos dois bancos.

**Diagnóstico de base vazia:** com migrations em SQLite em memória e nenhuma filial,
`query_assistant("Qual filial está com pior desempenho?")` levantou `ValueError`.
Falha antes do provider; o fallback não a resolve. Os testes existentes usam
principalmente o cenário completo e não detectavam esse caso.

O health check só verifica HTTP. Hosts/CSRF derivados da Vercel não configuram CORS
automaticamente. O README descrevia dois projetos e “production ready”; foi alinhado
ao arquivo `vercel.json` encontrado, sem afirmar validação do deploy real.

## 4. Frontend V2

Preservar rotas, cliente HTTP, formatadores e contratos dos componentes de dashboard.
O tema original tinha 2.305 linhas; agora é um índice com estilos separados por área.
Foram mantidos Bootstrap, seletores, valores e ordem da cascata. Paleta, bordas,
raios e sombra existentes foram preservados e ganharam escalas mínimas de espaço/fonte.

O novo visual deve começar por shell/home: sidebar discreta, mais espaço em branco,
hierarquia tipográfica e composição menos dependente de cards iguais. A aparência
atual vem de `.panel`, sidebar escura, badges, sombras e gradientes decorativos.
Evidências, cabeçalho de página, estados e tabela operacional são candidatos futuros
a componentes, conforme forem usados. Nenhuma imagem de referência foi recebida.

## 5. Pipelines

Proposta: Python em `operations/ingestion/`, chamado por comando Django próprio;
separar extração, validação, transformação e carga. Views continuam leves e analytics
continuam lendo os models publicados. Definir identificadores externos, enums, fuso,
totais, idempotência, rejeições e publicação transacional antes de monitoramento.

Filiais, clientes, produtos, estoque, pedidos, itens e chamados podem receber dados
externos; ações continuam sendo trabalho registrado pelo usuário. `seed_demo` não
é loader incremental e seu `--reset` não serve à futura ETL. Freshness precisa de
horário de origem/publicação, sem reutilizar a data de criação de um pedido.
RAW → CLEAN → BUSINESS, execuções e lineage mínimo estão propostos no
[guia do backend](BACKEND_GUIDE.md), sem bibliotecas ou infraestrutura instaladas.

## 6. Alterações realizadas

1. Criados quatro guias e este relatório, com arquitetura, contratos, limites e roadmap.
2. README ganhou índice dos guias, correção da definição de atraso, descrição fiel do
   arquivo de deploy e comandos de validação isolada. Alterações locais prévias foram preservadas.
3. Comentários/docstrings PT-BR em 11 módulos de domínio Python e cinco arquivos JS/JSX,
   explicando ingestão, cálculos, transações, API, fallback, estado e Chart.js.
4. `theme.css` dividido em oito arquivos, sem mudar regras anteriores; nove tokens
   novos (seis espaços e três tamanhos de fonte) disponíveis para evolução gradual.
5. `config.test_settings` e seleção no pytest isolam a suíte em SQLite em memória e
   mock, evitando que `.env` direcione fixtures destrutivas a um banco hospedado.
6. Quatro testes sem seed protegem fronteiras dos períodos, cancelamentos, semântica
   de atraso e períodos vazios. Nenhuma regra de negócio foi alterada.

## 7. Arquivos criados nesta fase (15)

- `docs/ARCHITECTURE.md`
- `docs/FRONTEND_GUIDE.md`
- `docs/BACKEND_GUIDE.md`
- `docs/ROADMAP_V2.md`
- `docs/AUDIT_PHASE01.md`
- `backend/config/test_settings.py`
- `backend/operations/tests/test_analytics_boundaries.py`
- `frontend/src/styles/tokens.css`
- `frontend/src/styles/base.css`
- `frontend/src/styles/dashboard.css`
- `frontend/src/styles/alerts.css`
- `frontend/src/styles/assistant.css`
- `frontend/src/styles/actions.css`
- `frontend/src/styles/shared.css`
- `frontend/src/styles/responsive.css`

## 8. Arquivos existentes alterados nesta fase (19)

- `README.md`
- `backend/pytest.ini`
- `backend/operations/models.py`
- `backend/operations/views.py`
- `backend/operations/serializers.py`
- `backend/operations/analytics/queries.py`
- `backend/operations/analytics/dashboard.py`
- `backend/operations/alerts/rules.py`
- `backend/operations/alerts/investigations.py`
- `backend/operations/actions/service.py`
- `backend/operations/ai/providers.py`
- `backend/operations/ai/service.py`
- `backend/operations/management/commands/seed_demo.py`
- `frontend/src/App.jsx`
- `frontend/src/main.jsx`
- `frontend/src/services/api.js`
- `frontend/src/pages/DashboardPage.jsx`
- `frontend/src/components/dashboard/TrendChart.jsx`
- `frontend/src/styles/theme.css`

**Estado prévio preservado:** `.env.example`, `README.md` e
`backend/config/settings.py` já estavam modificados; `backend/config/environment.py`
e `backend/core/tests/test_deployment_settings.py` já existiam sem rastreamento no Git.
Destes, somente README recebeu alterações adicionais nesta fase. Os outros quatro
não são entregas novas nem foram editados neste trabalho.

## 9. Testes, cobertura e limites

Ambiente usado: Windows, Python 3.13.15, Django 5.2.17, pytest 8.4.2, Vite 7.3.6.

| Verificação | Antes | Depois |
| --- | --- | --- |
| `python -m pytest` | 59 passaram em SQLite explicitamente selecionado | 63 passaram com `config.test_settings` (12,43s) |
| `python manage.py check` | Sem problemas, SQLite local | Sem problemas com `--settings=config.test_settings` |
| `python manage.py makemigrations --check --dry-run` | Nenhuma mudança | Nenhuma mudança com `--settings=config.test_settings` |
| `npm run lint` | Passou | Passou |
| `npm run build` | Passou após liberação do sandbox | Passou, 1.699 módulos; JS 437,44 kB e CSS 261,90 kB |
| Regras CSS recompostas | Arquivo original | Mesmas regras/declarações/ordem, exceto os nove tokens adicionais |
| AST Python de domínio | Código original | Mesma estrutura executável nos 11 arquivos, desconsiderando docstrings |
| AST JS/JSX | Código original | Mesma estrutura nos cinco arquivos, desconsiderando comentários |
| Isolamento de teste | Dependia do ambiente da demo | Confirmado com URL/provider externos fictícios antes de iniciar Django |
| Documentação e diff | — | Links locais e UTF-8 conferidos; `git diff --check` sem problemas |

A primeira tentativa de pytest teve 5 sucessos e 54 erros de conexão ao Supabase:
atribuir string vazia à variável no Windows PowerShell removeu-a, permitindo que o
dotenv recarregasse o valor hospedado. A repetição antes das alterações fixou SQLite
e passou. A nova configuração resolve esse problema para a execução padrão do pytest.
O traceback inicial expôs uma credencial de conexão; o usuário foi informado para
rotacioná-la. Nenhum valor sensível foi copiado para arquivos deste trabalho.

O primeiro build foi bloqueado pelo sandbox na resolução de `vite.config.js`.
Builds anterior e final passaram fora do sandbox; não foi necessário mudar Vite.

Cobertura **funcional**, sem percentual de linhas/branches medido: os testes cobrem
integridade dos models, seed/reset, métricas, thresholds, contratos HTTP, intenção
permitida/UNKNOWN, fallback e ações (duplicação, conclusão, reabertura e campos extras).
Os 59 testes iniciais incluem os cinco testes de deploy que já estavam no workspace.

Antes da V2, acrescentar proteção para:

- Fronteiras SQL/ORM nos dois bancos e bases incompletas para todos os contextos IA.
- Saída inválida/vazia e timeout do adaptador Gemini com SDK simulado; não depender de rede.
- Concorrência de criação/reabertura no PostgreSQL e política de consistência durante cargas.
- Identidade de alertas sob renomeação/colisão e custo de consultas com volume maior.
- Frontend: rotas/reload, filtros, 404/409, criação/status, erro/vazio/loading, troca de
  chave, teclado e responsividade. Não há runner de testes de frontend configurado.

Não foram executados testes reais de PostgreSQL, Gemini, deploy ou comparação visual
no navegador. Os dois diagnósticos de falhas existentes estão descritos na seção 3;
uma suíte verde não significa cobertura desses cenários.

## 10. Próxima etapa

V2.0 em escopo pequeno: proteger o fluxo de navegação e evoluir shell/home com a
referência visual, mantendo contratos e cálculos. Prompt sugerido no
[roadmap](ROADMAP_V2.md). Antes de ligar pipelines ou ampliar períodos, tratar as
divergências temporais e os casos de dados incompletos em uma entrega própria.
