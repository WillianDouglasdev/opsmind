# Roadmap evolutivo da V2

Direção: transformar o OpsMind em uma Central de Inteligência Operacional, cobrindo
**observar → detectar → entender → decidir → agir → medir**, incluindo confiança e
monitoramento dos próprios dados. Este roadmap é evolutivo: ordem, versões e escopo
podem mudar após cada entrega. Não representa funcionalidades já implementadas.

## Fase 01 — base para colaboração

Auditar, documentar arquitetura e contratos, comentar decisões, organizar estilos e
proteger o comportamento atual. Mantém tecnologias, schema, API e aparência da demo.
Os achados e verificações estão em [AUDIT_PHASE01.md](AUDIT_PHASE01.md).

## V2.0 — identidade visual, por tela

**Shell e Home entregues na Fase 02.** Base clara, sidebar discreta, tipografia
hierárquica, saúde e prioridades com pesos diferentes, indicadores sem cards
repetidos, feed de comparativos, gráfico com tabela e contexto de origem dos dados.
As outras páginas receberam os tokens e ajustes de legibilidade, preservando fluxos.
A imagem de referência não foi anexada; a direção seguiu os princípios descritos.

**Validação concluída:** dados e rotas preservados, fluxo de ações, estados parciais,
desktop, celular e teclado. Ver [relatório e capturas](PHASE02_REPORT.md). As outras
telas podem continuar a evolução em entregas próprias, conforme a necessidade.

**Refinamento da Fase 03.5 concluído:** identidade visual OpsMind2, tokens semânticos,
tema escuro persistido sem flash inicial, gráficos ligados ao tema e donut de qualidade
da pipeline. Backend, APIs, rotas e regras permaneceram intactos. Ver
[relatório e capturas](PHASE035_REPORT.md).

## V2.1 — drill-down e operação

**Entregue na Fase 04.** A Home abre atrasos; a visão geral compara todas as filiais;
atrasos abrem a contribuição de cada unidade; e a filial apresenta métricas, tendência,
comparação com a média e pedidos. Período, filial, status, atraso e página ficam na URL.

Os quatro endpoints de leitura calculam regras no backend e paginam pedidos. A semântica
de atraso foi fixada como `Order.status=delayed`; a janela usa início inclusivo e fim
exclusivo no fuso do Django. A consulta de filial foi migrada para ORM e testada em
SQLite. Ver [relatório e capturas](PHASE04_REPORT.md).

Permanecem para evoluções futuras os detalhes próprios de cliente/produto, teste em
PostgreSQL/Supabase e lineage persistido. Esses itens não bloqueiam o drill-down atual.

## V2.2 — pipelines e qualidade de dados

**Pipeline V1 entregue na Fase 03**, antecipada em relação ao
drill-down completo. A numeração V2.x identifica frentes de evolução, não impõe a
ordem de execução. A Home já possui `DataFlow` e metadados demonstrativos centralizados.

Fonte JSON de pedidos, Python padrão, comando Django, idempotência, rejeições com
motivos, freshness e rastreabilidade entre origem e publicação foram implementados.
RAW → CLEAN → BUSINESS ocorre em código e memória, com publicação atômica no banco.
Home e Pipelines consomem a API real. Ver [DATA_PIPELINE.md](DATA_PIPELINE.md).

Próximo passo: evoluir IDs externos de filiais/clientes e validar PostgreSQL antes
de automatizar. Analytics permanece independente da ingestão.

## V2.3 — investigações com continuidade

**Workspace derivado entregue na Fase 05.** A lista e o detalhe de atrasos organizam
resumo, evidências, timeline e próximos passos para a operação ou uma filial. Período
e filial permanecem na URL; os fatos são recalculados a partir da base atual, sem model,
migration, Gemini ou criação de ActionItems. Ver [relatório](PHASE05_REPORT.md).

Persistência, histórico e vínculo imutável com o sinal continuam futuros. Antes de
criar casos persistidos, definir lifecycle de alerta e política de snapshot; chaves
baseadas no nome da filial também precisam de transição compatível com ações existentes.

## V2.4 — IA contextual

Usar página, filtros e investigação selecionada como contexto permitido. Manter
cálculos e evidências no backend, provider configurável e fallback identificado.
Testar ausência de dados, timeout, classificação inválida e limites de contexto.
Não dar ao modelo execução SQL ou criação livre de tarefas como atalho.

## V2.5 — plano de ação e medição

Partir das ActionItems atuais e definir responsável, prazo, resultado esperado e
métrica de acompanhamento conforme o uso exigir. Concluir uma ação hoje só muda
seu status: isso não comprova melhoria operacional. Medição precisa de baseline,
período de observação e cuidado para não atribuir causalidade automaticamente.

## Como dividir o trabalho entre duas pessoas

Combinar contrato e critério de conclusão antes de trabalhar na mesma funcionalidade.
Uma pessoa pode preparar consultas/testes e outra a tela consumidora, mantendo PRs
pequenos por domínio. Toda mudança de regra deve atualizar teste e documentação no
mesmo PR. Não misturar redesenho, ingestão e mudança de indicadores numa única entrega.

Próximo prompt sugerido:

> Leia docs/, incluindo PHASE05_REPORT.md. Integre IA contextual somente sobre o contrato
> estruturado da investigação selecionada, mantendo cálculos e evidências no backend,
> fallback identificado e separação explícita entre hipótese, correlação e causalidade.
