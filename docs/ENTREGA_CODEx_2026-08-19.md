# AssetTrack TI — Documentação da Entrega Recente

**Data de referência:** 19/08/2026  
**Status:** entregue e publicada em ambiente local  
**Escopo:** consolidação das melhorias recentes realizadas na aplicação, com foco principal em UX global, Ativos & Inventário, Backup & Restore e ERP de Compras.

---

## 1. Visão geral

Esta entrega evoluiu o AssetTrack TI em duas frentes principais:

1. padronização visual e comportamental da aplicação, aproximando a experiência do estilo já aplicado no board/kanban;
2. ampliação funcional dos módulos operacionais, principalmente **Ativos & Inventário**, **Backup & Restore** e **Compras**.

O resultado prático é uma aplicação mais consistente visualmente, com fluxos mais completos de gestão interna e melhor capacidade de controle administrativo.

---

## 2. Melhorias visuais e de experiência global

Foram aplicados ajustes de interface para tornar a aplicação mais coesa, leve e utilizável no dia a dia.

### 2.1. Padronização visual inspirada no estilo do board/kanban

- expansão do estilo visual tipo “board” para outras áreas da aplicação;
- refinamento de cards, botões, opacidades, bordas e superfícies;
- adoção consistente de cantos arredondados em botões e elementos interativos;
- uniformização de feedback visual para ações e alertas.

### 2.2. Sidebar e layout estrutural

- implementação de **auto-recolhimento da sidebar**;
- revisão de altura e comportamento do menu lateral para melhor encaixe com o viewport;
- remoção/movimentação de elemento de marcação visual para o rodapé em formato de direitos autorais/copyright.

### 2.3. Modais

- aplicação de **blur escurecido leve no fundo** para modais em toda a aplicação;
- reforço visual de foco no conteúdo modal;
- padronização de raio de borda de botões dentro de modais e em áreas correlatas.

### 2.4. Alertas, avisos e estados de sucesso

- padronização visual de mensagens de sucesso/feedback;
- adequação de cor, transparência e raio de borda em avisos globais;
- melhoria na percepção visual de ações concluídas.

---

## 3. Ativos & Inventário

O módulo de ativos recebeu melhorias funcionais e administrativas importantes.

### 3.1. Exportação e importação CSV

- criação de fluxo para **exportar ativos existentes em CSV**;
- criação de fluxo para **importar ativos via CSV**;
- disponibilização de modelo compatível para importação;
- manutenção do padrão de download direto pela interface.

### 3.2. Cadastros auxiliares dentro de `/assets`

- criação de tela para **Categoria** e **Localização**;
- suporte a:
  - criação;
  - edição;
  - exclusão;
- centralização desses cadastros na própria área de ativos.

### 3.3. Correção de visibilidade de ativo em manutenção

- correção do caso em que um ativo em manutenção não exibia corretamente onde estava;
- ajuste de backend e frontend para mostrar:
  - local anterior;
  - armazenamento anterior;
  - contexto de origem do ativo quando ele está em manutenção.

### 3.4. Integrações indiretas com compras

O módulo de ativos também passou a se beneficiar do ciclo de compras:

- recebimentos de itens do tipo equipamento podem gerar ativos automaticamente;
- o fluxo foi preservado e ampliado junto com a evolução do módulo de compras.

---

## 4. Backup & Restore

O módulo de backup/restauração recebeu evolução importante para uso administrativo real.

### 4.1. Restauração a partir de backup legado

- análise de backup legado enviado para reaproveitamento dos dados;
- ajustes para lidar com diferenças estruturais entre base antiga e base atual;
- correções incrementais em erros de restauração envolvendo tabelas e colunas divergentes.

### 4.2. Estrutura para uso futuro

- criação de caminho de uso para restauração futura pelo próprio sistema;
- melhoria da experiência do fluxo de upload/restauração;
- preparação para seleção parcial do que restaurar.

### 4.3. Restauração seletiva

Foi introduzida a direção funcional para permitir restauração seletiva por módulos, com foco nas necessidades reais do sistema.

Exemplos de escopo trabalhado:

- Ativos & Inventário;
- Kanban;
- outros módulos operacionais.

### 4.4. Tratamento de falhas de compatibilidade

Durante essa frente, foram tratados casos como:

- tabelas ausentes;
- nomes divergentes entre versões antigas e novas;
- campos inexistentes em estruturas restauradas;
- falhas durante scripts SQL de restore.

---

## 5. Módulo de Compras — consolidação em ERP interno

O maior bloco desta entrega foi a evolução de `/compras` para um módulo muito mais próximo de um ERP de compras interno.

---

## 5.1. Base cadastral do compras

Foi criada uma nova área de **Cadastros** dentro do módulo.

### Entidades cobertas

- **Centros de Custo**
- **Categorias de Compra**
- **Produtos de Compra**

### Funcionalidades entregues

- criação;
- edição;
- exclusão;
- validações básicas;
- bloqueios para impedir exclusão de registros já vinculados a fluxos de negócio.

### Centro de custo

Cada centro de custo passou a suportar:

- código;
- nome;
- departamento;
- responsável;
- orçamento mensal;
- orçamento anual;
- alerta de limite;
- bloqueio ao ultrapassar orçamento.

---

## 5.2. Solicitações de compra

O fluxo de solicitações foi fortalecido com visão operacional e gerencial.

### Melhorias aplicadas

- criação de solicitação com itens;
- valor estimado total calculado;
- filtro por centro de custo;
- exibição de:
  - alçada sugerida;
  - situação orçamentária;
  - urgência;
  - status;
- integração com regras de orçamento do centro de custo.

### Situação orçamentária da solicitação

Cada solicitação passa a refletir situações como:

- dentro do orçamento;
- em alerta;
- acima do orçamento;
- bloqueio por orçamento;
- sem orçamento mensal definido.

---

## 5.3. Aprovação automática e alçadas

Uma evolução importante desta entrega foi retirar a dependência de decisões totalmente manuais e fixas.

### Fase 1

- implementação de sugestão automática de alçada baseada em:
  - valor;
  - urgência.

### Fase 2

- remoção da necessidade de digitar manualmente o nível de aprovação em cada ação;
- aprovação automática avançando conforme o nível exigido.

### Fase 3

- criação de **alçadas configuráveis por faixa de valor**;
- configuração dessas faixas diretamente na aba `Cadastros` do módulo de compras;
- persistência das faixas usando `system_settings`;
- comportamento final:
  - até Gestor;
  - até Gerente;
  - até Financeiro;
  - acima disso, Diretoria.

Isso deixou o fluxo mais aderente a políticas internas reais.

---

## 5.4. Cotações

O módulo já possuía o fluxo de cotação, mas ele foi conectado de forma mais prática ao restante da operação.

### Capacidades disponíveis

- geração de cotação a partir de solicitação;
- múltiplos fornecedores por cotação;
- comparação entre fornecedores;
- escolha de vencedor;
- emissão automática de pedido a partir da cotação vencedora.

---

## 5.5. Pedidos de compra

O fluxo de pedidos ganhou um ciclo operacional mais claro.

### Estados e operação

Foram reforçados e operacionalizados estados como:

- Aberto
- Enviado
- Aceito
- Em transporte
- Recebido parcialmente
- Recebido totalmente
- Cancelado

### Ações diretas na interface

- enviar pedido;
- aceitar pedido;
- marcar em transporte;
- registrar recebimento.

### Regras

- transições inválidas de status são bloqueadas;
- a trilha fica mais próxima de um fluxo real de suprimentos.

---

## 5.6. Recebimento, estoque e integração patrimonial

### Recebimento

- suporte a recebimento total ou parcial;
- validação de quantidade recebida contra o pedido;
- atualização de status do pedido com base no recebimento.

### Geração automática de ativos

Quando o item recebido é do tipo equipamento:

- o sistema pode gerar ativos automaticamente;
- herda dados do contexto da compra;
- reforça integração entre Compras e Ativos.

### Entrada em estoque

Quando o item é de consumo:

- o sistema gera entrada em estoque simples;
- registra movimentação;
- mantém histórico operacional.

---

## 5.7. Estoque operacional do compras

O módulo passou a suportar melhor o papel de almoxarifado interno.

### Melhorias entregues

- listagem de estoque;
- consumo manual de estoque;
- seleção de centro de custo no consumo;
- justificativa do consumo;
- histórico recente de movimentações;
- distinção visual entre entrada e saída.

Isso fecha o ciclo:

**Compra → Recebimento → Entrada → Consumo/Baixa**

---

## 5.8. Dashboard gerencial de compras

O dashboard do compras foi expandido para entregar leitura executiva e operacional.

### Indicadores gerais

- solicitações pendentes;
- pedidos em aberto;
- itens com estoque baixo;
- uso do orçamento mensal;
- total solicitado;
- total cotado;
- total comprado;
- economia estimada.

### Saúde dos centros de custo

- centros em alerta;
- centros acima do limite;
- barras visuais de uso do orçamento;
- resumo por centro de custo.

### Relatórios gerenciais

Foram adicionadas visões no dashboard para:

- relatório por centro de custo;
- performance de fornecedores;
- ranking de fornecedores com maior volume.

---

## 5.9. SLA de fornecedores

Foi adicionada camada de controle de prazo para fornecedores.

### O que passou a existir

- cálculo de prazo previsto de entrega com base na cotação vencedora;
- comparação entre data prevista e:
  - data atual;
  - data efetiva de recebimento.

### Status possíveis

- Sem SLA
- Dentro do prazo
- Em atraso
- Entregue no prazo
- Entregue em atraso

### Onde aparece

- na lista de pedidos;
- no painel de performance de fornecedores.

### Métricas por fornecedor

- pedidos no prazo;
- pedidos em atraso;
- percentual de SLA;
- ticket médio;
- pedidos ativos;
- pedidos recebidos.

---

## 5.10. Exportação de relatórios de compras

Foi implementada exportação CSV diretamente da tela do módulo.

### Exportações disponíveis

- Resumo
- Solicitações
- Pedidos
- Estoque

### Objetivo

- auditoria;
- prestação de contas;
- análise externa;
- compartilhamento com financeiro, diretoria ou compras.

---

## 6. Relações entre módulos

As melhorias recentes também reforçaram a integração entre áreas do sistema.

### Compras ↔ Ativos

- recebimento de equipamento pode gerar ativo automaticamente.

### Compras ↔ Estoque

- itens de consumo entram no estoque e depois podem ser baixados manualmente.

### Compras ↔ Centro de custo

- solicitações, consumo e relatórios passam a respeitar orçamento e governança.

### Ativos ↔ Manutenção

- localização/origem do ativo em manutenção passou a ser melhor exibida.

### Backups ↔ operação administrativa

- base para restauração futura e seletiva foi fortalecida.

---

## 7. Validação executada

Ao longo desta frente, as entregas foram validadas iterativamente com:

- build do frontend (`npm run build`);
- testes/compilação do backend (`go test ./...`);
- publicação local com Docker Compose;
- checagem visual no navegador.

---

## 8. Arquivos principais impactados

Os arquivos abaixo concentraram boa parte das mudanças recentes:

- [backend/internal/handler/procurement_handler.go](/home/humberto/Aplicativos/assettrack_ti/backend/internal/handler/procurement_handler.go)
- [backend/internal/repository/procurement_repo.go](/home/humberto/Aplicativos/assettrack_ti/backend/internal/repository/procurement_repo.go)
- [backend/internal/models/procurement.go](/home/humberto/Aplicativos/assettrack_ti/backend/internal/models/procurement.go)
- [backend/internal/router/router.go](/home/humberto/Aplicativos/assettrack_ti/backend/internal/router/router.go)
- [frontend/src/pages/ProcurementPage.tsx](/home/humberto/Aplicativos/assettrack_ti/frontend/src/pages/ProcurementPage.tsx)
- [frontend/src/api/procurement.ts](/home/humberto/Aplicativos/assettrack_ti/frontend/src/api/procurement.ts)
- [frontend/src/types/procurement.ts](/home/humberto/Aplicativos/assettrack_ti/frontend/src/types/procurement.ts)
- [frontend/src/pages/AssetsPage.tsx](/home/humberto/Aplicativos/assettrack_ti/frontend/src/pages/AssetsPage.tsx)
- [frontend/src/pages/MaintenancePage.tsx](/home/humberto/Aplicativos/assettrack_ti/frontend/src/pages/MaintenancePage.tsx)
- [backend/internal/repository/asset_repo.go](/home/humberto/Aplicativos/assettrack_ti/backend/internal/repository/asset_repo.go)
- [backend/internal/repository/maintenance_repo.go](/home/humberto/Aplicativos/assettrack_ti/backend/internal/repository/maintenance_repo.go)

---

## 9. Próximos passos recomendados

Embora a entrega atual já deixe o módulo de compras bastante robusto, os próximos passos naturais seriam:

- rateio de compra entre múltiplos centros de custo;
- exportação em PDF dos relatórios de compras;
- trilha de auditoria detalhada por solicitação e por pedido;
- melhoria adicional de performance do bundle frontend;
- eventual separação de dashboards analíticos em páginas dedicadas.

---

## 10. Resumo executivo

Até 19/08/2026, esta frente entregou:

- padronização visual relevante da aplicação;
- melhorias administrativas em Ativos & Inventário;
- fortalecimento do fluxo de Backup & Restore;
- consolidação do módulo de Compras como núcleo ERP interno com:
  - cadastros;
  - orçamento;
  - alçadas;
  - cotações;
  - pedidos;
  - recebimento;
  - estoque;
  - consumo;
  - relatórios;
  - exportações;
  - SLA de fornecedores.

Em termos práticos, o AssetTrack TI saiu de um conjunto de telas isoladas para uma operação mais integrada, governável e auditável.

---

## 11. Adendo de continuidade — 20/08/2026

Este documento passa a registrar também os avanços posteriores à consolidação inicial, sempre que novas melhorias relevantes forem aplicadas.

### 11.1. Ajuste de lógica no modal de cotação do módulo Compras

Foi revisado o fluxo de criação de cotação no módulo `/compras`, com foco na relação entre solicitação, itens e fornecedores.

#### Problema identificado

O modal de **Nova Cotação** estava induzindo uma interpretação confusa:

- a interface fazia parecer que cada fornecedor estava vinculado a apenas um item;
- a estrutura visual misturava fornecedor, frete, prazo e itens no mesmo bloco sem deixar claro o papel de cada camada;
- ao abrir a cotação a partir de uma solicitação com múltiplos itens, a experiência não refletia bem a lógica esperada de compras corporativas.

#### Correção aplicada

O fluxo foi reorganizado para refletir a regra de negócio correta:

- a **solicitação** define os itens que precisam ser cotados;
- os **fornecedores** passam a apresentar propostas para os mesmos itens da solicitação;
- a **cotação** deixa de parecer “um fornecedor por item” e passa a funcionar como comparação real entre propostas.

#### Melhorias implementadas

- exibição da solicitação base no topo do modal;
- exibição dos itens da solicitação como referência para a cotação;
- preenchimento inicial dos itens para cada fornecedor com base na solicitação;
- aproveitamento dos fornecedores sugeridos quando existirem;
- inclusão de ação para remover fornecedor da cotação;
- bloqueio de fornecedor duplicado na mesma cotação;
- mensagens mais claras sobre a finalidade do comparativo.

### 11.2. Comparativo visual de fornecedores no próprio modal

Além do ajuste estrutural, foi adicionada uma camada de leitura gerencial dentro da própria tela de cotação.

#### Novos destaques automáticos

Cada fornecedor agora pode receber destaque automático no comparativo:

- **Menor preço**
- **Menor prazo**
- **Melhor custo-benefício**

#### Critério de custo-benefício

Foi adotada uma regra simples e transparente para o comparativo inicial:

- 70% de peso para preço;
- 30% de peso para prazo.

#### Informações resumidas por fornecedor

Cada card de fornecedor no comparativo passou a exibir:

- valor total da proposta;
- prazo de entrega em dias;
- valor de frete;
- média unitária dos itens cotados.

### 11.3. Matriz comparativa por item × fornecedor

Na continuidade desta melhoria, o modal de cotação recebeu uma visualização mais próxima de um ERP de compras.

#### Evolução aplicada

Foi incluído um **mapa comparativo por item**, no qual:

- cada linha representa um item da solicitação;
- cada coluna de fornecedor representa a proposta daquele fornecedor para o mesmo item;
- o usuário consegue comparar valores unitários e totais por item sem precisar interpretar blocos separados mentalmente.

#### Benefícios operacionais

Essa estrutura melhora a leitura da cotação em situações reais, porque:

- facilita identificar rapidamente qual fornecedor está melhor em cada item;
- reduz a chance de erro na análise manual;
- aproxima o fluxo da prática de compras corporativas baseada em mapa comparativo;
- mantém o resumo final alinhado com a decisão de menor preço, menor prazo e melhor custo-benefício.

#### Destaques da matriz

Na tabela comparativa foram incluídos:

- item solicitado;
- quantidade solicitada;
- valor estimado original;
- valor unitário por fornecedor;
- total por item em cada fornecedor;
- destaque visual para o melhor valor daquele item;
- linha de resumo final por fornecedor com total e prazo.

### 11.4. Seleção guiada do vencedor da cotação

Na etapa seguinte, a listagem de cotações também passou a oferecer apoio direto à decisão de compra.

#### Evolução aplicada

Cada fornecedor listado dentro de uma cotação passou a exibir:

- indicação de **menor preço**;
- indicação de **menor prazo**;
- indicação de **melhor custo-benefício**;
- motivo sugerido para a escolha daquele fornecedor.

#### Confirmação mais clara antes de emitir pedido

O fluxo de escolha do vencedor passou a mostrar, antes da confirmação:

- nome do fornecedor selecionado;
- motivo identificado pela lógica comparativa;
- valor total da proposta;
- prazo de entrega;
- aviso explícito de que o pedido de compra será emitido automaticamente.

#### Benefício operacional

Essa camada reduz ambiguidade no momento mais crítico da cotação:

- ajuda o comprador a justificar a decisão;
- melhora rastreabilidade da escolha;
- deixa o processo mais próximo de uma decisão assistida por critérios objetivos;
- reduz risco de selecionar fornecedor sem avaliar custo e prazo de forma conjunta.

### 11.5. Histórico visível da decisão e vínculo com o pedido gerado

Na sequência, a própria listagem de cotações passou a exibir também o resultado consolidado da decisão.

#### Evolução aplicada

Quando a cotação já possui vencedor definido, a interface agora mostra:

- fornecedor vencedor;
- critério identificado para a escolha;
- valor final vencedor;
- prazo vencedor;
- número do pedido de compra gerado a partir daquela cotação;
- data/hora de emissão do pedido;
- valor do pedido emitido.

#### Benefício operacional

Essa camada transforma a cotação em um registro mais auditável, porque:

- reduz a dependência de memória operacional;
- conecta a decisão da cotação ao pedido efetivamente emitido;
- deixa mais claro o encadeamento entre análise, decisão e execução;
- melhora leitura histórica do processo de compras.

### 11.6. Indicador financeiro de economia versus estimativa

Na continuidade, a cotação passou a mostrar também o efeito financeiro da decisão em relação ao valor originalmente previsto pela solicitação.

#### Evolução aplicada

Quando existe vencedor definido, a interface agora compara:

- valor estimado da solicitação;
- valor efetivamente fechado com o fornecedor vencedor;
- economia obtida, quando o fechamento ficou abaixo da estimativa;
- excesso sobre o estimado, quando o fechamento ficou acima do previsto;
- percentual correspondente dessa diferença.

#### Benefício operacional

Essa camada fortalece a visão gerencial do processo de compras, porque:

- evidencia ganho financeiro real da cotação;
- facilita análise de eficiência da área de compras;
- destaca rapidamente quando a compra superou o orçamento inicialmente previsto;
- melhora a leitura do impacto econômico da decisão tomada.

### 11.7. Alertas visuais de risco operacional na cotação

Na sequência, a cotação passou a sinalizar também situações de atenção operacional já no resultado da decisão.

#### Evolução aplicada

Foram introduzidos alertas visuais para cenários como:

- fechamento acima do valor estimado da solicitação;
- prazo de entrega considerado alto para o fornecedor vencedor.

Esses alertas aparecem junto ao bloco consolidado da decisão, com destaque visual e mensagem objetiva.

#### Benefício operacional

Essa camada ajuda a operação porque:

- antecipa leitura de risco sem depender de análise manual detalhada;
- chama atenção para compras com impacto financeiro negativo;
- destaca fornecedores vencedores com prazo potencialmente problemático;
- melhora a capacidade de acompanhamento gerencial da decisão tomada.

### 11.8. Correção da trava entre aprovação da solicitação e criação da cotação

Foi identificada e corrigida uma inconsistência entre a regra de interface e a regra do backend no fluxo de compras.

#### Problema identificado

A API de criação de cotação já exigia corretamente que a solicitação estivesse com status **Aprovada**.

Porém, na interface, o botão **Cotar** estava sendo exibido apenas para solicitações com status:

- **Pendente**
- **Em aprovação**

Na prática, isso bloqueava o fluxo real:

- quando a solicitação ainda não estava aprovada, a UI deixava tentar cotar;
- quando a solicitação ficava de fato aprovada, a ação desaparecia;
- resultado: o usuário ficava sem conseguir iniciar a cotação no momento correto.

#### Correção aplicada

A lógica da tela foi ajustada para exibir a ação **Cotar** somente quando a solicitação estiver em status:

- **Aprovada**

Com isso, a interface passou a refletir corretamente a mesma regra já exigida pela API.

#### Benefício operacional

Essa correção remove uma trava funcional importante do módulo de compras, porque:

- alinha frontend e backend na mesma regra de negócio;
- evita tentativa de cotação em status inválido;
- libera a cotação no momento exato do fluxo correto;
- reduz confusão operacional durante o processo de aprovação.

### 11.9. Correção da trava entre aprovação parcial e conclusão da aprovação

Foi identificada uma segunda inconsistência no fluxo de solicitações de compra.

#### Problema identificado

Quando uma solicitação saía de **Pendente** para **Em aprovação**, a interface deixava de mostrar os botões de decisão.

Na prática, isso criava um bloqueio:

- a solicitação recebia uma aprovação inicial;
- o status passava para **Em aprovação**;
- a tela escondia os botões **Aprovar** e **Reprovar**;
- a solicitação ficava presa sem conseguir avançar até **Aprovada**.

#### Correção aplicada

A interface foi ajustada para manter as ações de decisão disponíveis também quando a solicitação estiver em:

- **Em aprovação**

Com isso, o fluxo de aprovação pode continuar normalmente até atingir o nível final necessário.

### 11.10. Correção da regressão de status após liberação de orçamento

Também foi corrigida uma inconsistência no backend da liberação de orçamento.

#### Problema identificado

A rotina de liberação de orçamento podia devolver uma solicitação para **Em aprovação** apenas por existir histórico de aprovação, mesmo quando ela já atendia o nível necessário e deveria permanecer **Aprovada**.

#### Correção aplicada

A lógica do backend passou a recalcular corretamente o status após a liberação de orçamento, considerando:

- valor estimado da solicitação;
- nível de aprovação exigido;
- maior nível já aprovado no histórico.

Com isso, solicitações já suficientemente aprovadas permanecem em **Aprovada**, em vez de regredirem indevidamente.

#### Ajuste aplicado na base atual

Além da correção do código, foi regularizada a solicitação existente:

- **SC-2026-000001**

Status final confirmado em **20/08/2026**:

- **Aprovada**

### 11.11. Publicação da correção no ambiente Docker

Após os ajustes de frontend e backend, os serviços da aplicação foram reconstruídos e reiniciados no ambiente Docker para que a correção passasse a valer no sistema em execução.

Serviços atualizados:

- API
- Web

Validação adicional:

- checagem de saúde da API após reinício;
- confirmação do status final da solicitação corrigida na base.

### 11.12. Refino visual dos estados de decisão da cotação

Também foi feito um ajuste fino de cor nos elementos visuais ligados à decisão final da cotação.

#### Evolução aplicada

Foram refinadas as cores dos seguintes elementos:

- selo **Decisão registrada**;
- selo **Vencedor**;
- selo **Acima do estimado**;
- valor financeiro em destaque quando a cotação ficou acima do estimado;
- mensagem resumida de impacto financeiro da decisão;
- mensagem detalhada do risco financeiro.

#### Objetivo

Esse ajuste teve como foco:

- melhorar leitura do estado final da cotação;
- dar mais contraste para situações de risco financeiro;
- deixar os selos positivos e de alerta visualmente mais coerentes entre si;
- manter consistência com a linguagem visual já aplicada no módulo.

### 11.13. Padronização visual das abas em Ativos & Inventário

Foi aplicada uma padronização visual no menu de abas da página `/assets`.

#### Evolução aplicada

O mesmo tratamento de fundo solicitado para:

- **Tabela Geral**
- **Kanban Oficina**

foi estendido para o restante das abas do mesmo grupo, incluindo:

- **Filtros & Relatórios**
- **Cadastros Base**

#### Regra visual adotada

- aba ativa com fundo claro `#ededed`;
- abas inativas com fundo `#e6e6e6`;
- contraste mantido com a borda e a tipografia já existentes;
- hover mais evidente nas abas inativas.

#### Objetivo

Esse ajuste melhora a navegação do módulo porque:

- deixa o conjunto de abas mais uniforme;
- reduz diferença visual inconsistente entre itens do mesmo menu;
- reforça a leitura de estado ativo versus inativo;
- acompanha a linguagem visual já aplicada na aplicação.

### 11.14. Ajuste tipográfico do rodapé global

Foi aplicado um ajuste tipográfico no rodapé compartilhado da aplicação.

#### Evolução aplicada

O texto:

- `© 2026 AssetTrack TI. Todos os direitos reservados.`

passou de:

- `12px`

para:

- `14px`

#### Objetivo

Esse ajuste melhora:

- legibilidade do rodapé;
- equilíbrio visual com o restante da interface;
- consistência do bloco institucional ao final das páginas.

### 11.15. Validação desta rodada

As melhorias acima foram validadas com:

- build do frontend (`npm run build`);
- testes do backend (`go test ./...`);
- revisão de consistência da estrutura de dados enviada para criação da cotação;
- revisão visual da experiência do modal.
- reconstrução e reinício dos serviços Docker.

### 11.16. Arquivos impactados nesta continuidade

- [frontend/src/components/layout/MainLayout.tsx](/home/humberto/Aplicativos/assettrack_ti/frontend/src/components/layout/MainLayout.tsx)
- [frontend/src/pages/AssetsPage.tsx](/home/humberto/Aplicativos/assettrack_ti/frontend/src/pages/AssetsPage.tsx)
- [frontend/src/pages/ProcurementPage.tsx](/home/humberto/Aplicativos/assettrack_ti/frontend/src/pages/ProcurementPage.tsx)
- [backend/internal/handler/procurement_handler.go](/home/humberto/Aplicativos/assettrack_ti/backend/internal/handler/procurement_handler.go)

### 11.17. Regra operacional adotada daqui para frente

A partir desta solicitação, toda mudança relevante implementada nesta frente deverá ser acompanhada de atualização documental correspondente, para manter histórico funcional e técnico do que foi entregue.
