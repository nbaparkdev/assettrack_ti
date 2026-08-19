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
