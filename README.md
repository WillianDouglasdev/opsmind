# OpsMind

**Inteligência Operacional apoiada por IA**

> **Current Stage: Production Ready / Pre-Deploy**

OpsMind é uma prova de conceito de uma plataforma de inteligência operacional. O
estágio atual combina analytics, investigações determinísticas e IA explicativa com
recomendações controladas e um plano de ação persistido, sem transferir cálculos ou
decisões operacionais para o modelo generativo.

A demonstração representa a empresa fictícia **Vértice Operações**, com cinco
filiais em Minas Gerais. Todos os nomes, valores e eventos são sintéticos.

## Stack

- Backend: Python 3.12+, Django, Django REST Framework, Django ORM e pytest;
- IA: SDK oficial `google-genai`, com providers Gemini e mock;
- Banco local: SQLite;
- Banco hospedado: PostgreSQL no Supabase por `DATABASE_URL`;
- Frontend: React, Vite, Bootstrap 5, Chart.js e Lucide React.

## Analytics do dashboard

O app `operations` calcula os indicadores diretamente dos models operacionais, sem
models extras de analytics e sem persistir resultados calculados.

| Endpoint | Conteúdo |
| --- | --- |
| `GET /api/dashboard/summary/` | Saúde operacional, faturamento, pedidos, atrasos e chamados ativos |
| `GET /api/dashboard/trends/` | Taxa mensal de entregas no prazo nos últimos seis meses e meta |
| `GET /api/dashboard/changes/` | Comparativos de 30 dias e condição atual do estoque crítico |
| `GET /api/alerts/` | Alertas ativos calculados e ordenados por severidade |
| `GET /api/alerts/{alert_key}/investigation/` | Impacto, evidências e fatores associados |
| `GET /api/alerts/{alert_key}/recommendations/` | Recomendações determinísticas baseadas na investigação |
| `GET /api/actions/` | Action Items ordenadas por status e prioridade |
| `POST /api/actions/` | Criação de ação a partir de alerta e recomendação oficiais |
| `PATCH /api/actions/{id}/` | Alteração exclusiva do status da ação |
| `POST /api/assistant/query/` | Consulta operacional em linguagem natural |
| `POST /api/assistant/executive-summary/` | Resumo executivo não persistido |
| `GET /api/health/` | Disponibilidade da API |

Regras de cálculo:

- a data de referência fixa da demo é `2026-08-29`;
- os comparativos usam os 30 dias mais recentes contra os 30 dias imediatamente
  anteriores;
- faturamento desconsidera pedidos cancelados;
- chamados ativos incluem os status `open` e `in_progress`;
- atraso considera pedidos entregues depois da promessa ou ainda não entregues após
  a data prometida;
- estoque crítico é um snapshot atual e, portanto, aparece como condição vigente,
  não como uma variação histórica inventada;
- a tendência mensal representa entregas no prazo, e não um histórico artificial do
  score de saúde.

O score de saúde operacional parte de 100 e aplica penalidades limitadas para taxa e
crescimento dos atrasos, estoque crítico, chamados ativos, clientes estratégicos
afetados e desvio da filial com pior atraso. O resultado é limitado entre 0 e 100 e
classificado em `Saudável`, `Atenção`, `Risco moderado` ou `Risco alto`. Os componentes
e impactos são devolvidos pela API para manter o cálculo explicável.

As consultas usam o Django ORM, exceto a consolidação da taxa de atraso por filial,
que utiliza SQL explícito parametrizado e compatível com SQLite e PostgreSQL.

## Alertas e investigação

Os alertas são recalculados a partir do estado atual dos dados. Não existe model
`Alert`, persistência ou lifecycle nesta fase. As quatro regras ativas são:

| Regra | Critério principal |
| --- | --- |
| `DELIVERY_DELAY_INCREASE` | Taxa recente ≥ 10% e crescimento relativo ≥ 15% |
| `BRANCH_PERFORMANCE` | Ao menos 50 pedidos e atraso ≥ 5 p.p. acima da média |
| `INVENTORY_RISK` | Uma ou mais combinações de filial/produto abaixo do mínimo |
| `STRATEGIC_CUSTOMER_RISK` | Cliente estratégico com 2+ atrasos ou 2+ chamados recentes |

As severidades usam thresholds simples e centralizados. Crescimento de atrasos a
partir de 20% e desvio de filial a partir de 7 p.p. são classificados como altos. O
estoque torna-se alto com quatro ocorrências ou forte relação com pedidos atrasados;
cinco clientes estratégicos afetados também caracterizam severidade alta.

As investigações apresentam impacto mensurável, evidências e fatores associados. A
presença conjunta de estoque crítico, atrasos, chamados e desempenho de filial é
tratada como correlação operacional: o sistema não afirma causalidade sem dados que
a comprovem. Todo texto é determinístico e nenhuma IA participa da detecção,
severidade ou seleção das evidências.

## OpsMind AI

O assistente suporta apenas as intenções `DELIVERY_DELAYS`, `CUSTOMER_RISK`,
`INVENTORY_RISK`, `BRANCH_PERFORMANCE`, `TICKET_ANALYSIS`, `EXECUTIVE_SUMMARY` e
`UNKNOWN`. A pergunta é classificada e validada antes que o backend selecione os
analytics permitidos. O contexto estruturado resultante é enviado ao provider apenas
para produzir a explicação em português brasileiro.

Os cálculos e as evidências permanecem sob responsabilidade do backend. O LLM não
recebe acesso ao banco, schema, ferramentas ou funções de execução, não gera nem
executa SQL e não cria alertas. O campo `evidence` da resposta é sempre montado pelo
backend com dados reais, independentemente do texto produzido pelo provider.

O provider `mock`, padrão do projeto, classifica por palavras-chave e produz respostas
determinísticas usando os valores do contexto. Assim, a demo inteira funciona sem
chave e sem internet. O provider `gemini` usa structured output validado por Pydantic
para a classificação e centraliza todas as chamadas ao SDK em um único módulo. Em
falhas transitórias, a resposta textual usa o fallback local e informa
`provider: "fallback"`; configuração incompleta do Gemini gera erro claro sem derrubar
o servidor.

Para usar o modo local, mantenha:

```dotenv
AI_PROVIDER=mock
GEMINI_API_KEY=
GEMINI_MODEL=
```

Para usar Gemini, defina `AI_PROVIDER=gemini`, informe uma chave válida e escolha o
modelo em `GEMINI_MODEL`. O nome do modelo não está fixado no código e pode ser
alterado somente pela variável de ambiente.

## Recomendações e plano de ação

Cada um dos quatro tipos de alerta possui um catálogo explícito de recomendações.
Títulos, descrições, prioridades e justificativas são calculados pelo backend a partir
da investigação atual. Nomes como filial, produtos e clientes são inseridos com os
dados reais da demo; o Gemini não cria, seleciona ou altera tarefas.

O fluxo é `alerta → investigação → recomendação → ActionItem`. Consultar uma
recomendação não persiste nada. Para criar uma ação, o frontend envia apenas
`alert_key` e `recommendation_key`; o backend resolve novamente o alerta e a
recomendação oficial antes de salvar. Campos de texto, origem e prioridade não podem
ser fornecidos ou editados pelo cliente.

As Action Items usam os estados `pending`, `in_progress` e `completed`, apresentados
como `Pendente`, `Em andamento` e `Concluída`. Ao concluir, `completed_at` recebe o
horário atual; ao reabrir, volta a ser nulo. Uma restrição parcial impede duas ações
abertas para a mesma recomendação e alerta, mas uma recomendação já concluída pode
originar uma nova ação se o sinal voltar a ser relevante.

Não há autenticação ou vínculo com usuário: a aplicação continua como demo
single-user. Os dados empresariais mantêm a data fixa da demonstração, enquanto
`created_at`, `updated_at` e `completed_at` registram o tempo real da interação.

## Dados sintéticos

O comando `seed_demo` utiliza seed aleatória `42` e data-base `2026-08-29`. Ele gera
5 filiais, 250 clientes, 40 produtos, aproximadamente 2.500 pedidos e 500 chamados,
além do inventário atual. O cenário reproduzível contém aumento recente de atrasos,
maior pressão em Contagem, crescimento de chamados de entrega, participação dos
produtos P018 e P027 em pedidos atrasados e clientes estratégicos recorrentes.

Executar o comando sem `--reset` quando os dados já existem não cria duplicatas.

## Configuração local

Requisitos: Python 3.12+, Node.js 20.19+ e npm.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
cd backend
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Com `DATABASE_URL` ausente ou vazia, o Django usa `backend/db.sqlite3`. Para recriar
os dados operacionais e remover todas as Action Items da demonstração, execute:

```powershell
cd backend
python manage.py seed_demo --reset
```

Em outro terminal, inicie o frontend:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

O frontend fica disponível em `http://localhost:5173` e usa por padrão a API em
`http://127.0.0.1:8000`.

## Banco e execução em produção

O desenvolvimento local continua usando SQLite. Em produção, o Django acessa o
PostgreSQL do Supabase exclusivamente pelo ORM e pela variável `DATABASE_URL`; o
projeto não utiliza `supabase-py`.

Para o runtime serverless da Vercel, use a URL do **Transaction Pooler** do Supabase,
normalmente na porta `6543`, com `sslmode=require`. As conexões do Django têm
`CONN_MAX_AGE=0`, portanto o pooling permanece sob responsabilidade do Supabase. O
backend PostgreSQL do Django com psycopg 3 já desativa prepared statements por padrão,
mantendo compatibilidade com o modo transaction.

Migrations, seed e outras tarefas administrativas devem usar temporariamente a
conexão direta ou o **Session Pooler**, normalmente na porta `5432`. Defina essa URL
como `DATABASE_URL` somente no ambiente do comando:

```powershell
cd backend
$env:DATABASE_URL = "<conexão direta ou Session Pooler com sslmode=require>"
python manage.py migrate
python manage.py seed_demo --reset
Remove-Item Env:DATABASE_URL
```

Execute `seed_demo --reset` apenas depois de confirmar que o destino é o banco de
demonstração do OpsMind e que não contém dados que precisem ser preservados. A string
real de conexão nunca deve ser commitada. No runtime da API, configure também
`DJANGO_DEBUG=False`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` e
`CORS_ALLOWED_ORIGINS` com os domínios que serão definidos na Fase 7B. O Django
reconhece o `X-Forwarded-Proto` enviado pela Vercel e exige HTTPS em produção; HSTS
será definido somente após a confirmação do domínio público.

A arquitetura planejada usa dois projetos Vercel apontando para o mesmo repositório:
o frontend com Root Directory `frontend` e a API Django com Root Directory `backend`.
Com essa raiz, `manage.py`, `config/wsgi.py` e `requirements.txt` já ficam nas posições
esperadas pela detecção do Django. Nenhum deploy é executado nesta fase.

## Variáveis de ambiente

| Variável | Uso |
| --- | --- |
| `DJANGO_SECRET_KEY` | Chave interna do Django |
| `DJANGO_DEBUG` | Modo de desenvolvimento |
| `DATABASE_URL` | PostgreSQL; quando ausente, ativa SQLite local |
| `DJANGO_ALLOWED_HOSTS` | Hosts aceitos pelo Django, separados por vírgula |
| `CORS_ALLOWED_ORIGINS` | Origens do frontend autorizadas no backend |
| `CSRF_TRUSTED_ORIGINS` | Origens HTTPS confiáveis, quando necessárias para requisições com CSRF |
| `AI_PROVIDER` | Provider do assistente: `mock` por padrão ou `gemini` |
| `GEMINI_API_KEY` | Chave do Gemini; obrigatória apenas no modo `gemini` |
| `GEMINI_MODEL` | Modelo Gemini configurável; obrigatório no modo `gemini` |
| `VITE_API_URL` | URL-base pública da API usada pelo Vite |

Nunca coloque segredos em variáveis prefixadas por `VITE_`. Quando
`DJANGO_DEBUG=False`, `DJANGO_SECRET_KEY` é obrigatória e conexões PostgreSQL usam
SSL mesmo se `sslmode=require` tiver sido omitido acidentalmente da URL.

## Estrutura principal

```text
opsmind/
├── backend/
│   ├── config/                    # configuração e rotas Django
│   ├── core/                      # health check
│   └── operations/
│       ├── analytics/             # consultas e composição do dashboard
│       ├── alerts/                # regras, engine e investigações determinísticas
│       ├── ai/                    # intents, prompts, providers e serviço do assistente
│       ├── actions/               # catálogo e serviço do plano de ação
│       ├── management/commands/   # seed_demo
│       ├── migrations/            # schema versionado
│       ├── tests/                 # models, analytics, IA e endpoints
│       ├── serializers.py         # contratos de saída da API
│       ├── urls.py
│       └── views.py
└── frontend/
    └── src/                       # dashboard e OpsMind AI conectados à API
```

## Qualidade

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run

cd ..\frontend
npm run lint
npm run build
```

## Limites desta fase

O assistente não mantém histórico, não aceita anexos e não responde fora das seis
categorias operacionais suportadas. Recomendações e Action Items existem somente no
catálogo determinístico e não são criadas livremente pelo Gemini. Não há model
`Alert`, histórico, reconhecimento, resolução ou atribuição de alertas. Também não
há usuários, autenticação, aprovação gerencial, notificações, integrações externas,
jobs, Kanban, workflows ou execução automática das ações.
