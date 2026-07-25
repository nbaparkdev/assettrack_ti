# Resoluções Técnicas e Correções Críticas

Este documento registra as resoluções arquiteturais e correções críticas aplicadas para estabilizar o processo de inicialização do sistema (`init_app.py`) e o fluxo de aprovação do módulo de Compras (Pesquisa e Cotação Prévia).

## 1. Correções no Fluxo de Pesquisa e Cotação Prévia (Compras)

### 1.1 Exceção `MissingGreenlet` e Renderização 500
* **Problema:** Ao aprovar ou rejeitar uma Pesquisa de Cotação Prévia, ocorria um Erro 500 Interno do Servidor causado por `MissingGreenlet`.
* **Causa:** O SQLAlchemy assíncrono perde a sessão ativa dos relacionamentos (lazy load) após um comando `await db.rollback()`. Quando o Jinja2 tentava ler `research.items` na renderização HTML do retorno, o erro estourava.
* **Resolução:** Refatorado o bloco `try/except` no endpoint `decide_research` para recarregar explicitamente a pesquisa (`get_purchase_research`) no banco de dados após qualquer tentativa de persistência falha, mantendo as associações carregadas.

### 1.2 Limite de Caracteres em URL (`StringDataRightTruncationError`)
* **Problema:** Erro 500 ao gerar a Solicitação de Compra a partir da pesquisa devido a estouro do tamanho limite `VARCHAR(255)` na tabela `purchase_request_items`.
* **Causa:** Links de produtos com parâmetros de rastreamento (ex. Amazon, Mercado Livre) e UTMs frequentemente excedem 255 caracteres. O sistema os armazenava na coluna `observacao`.
* **Resolução:** 
  1. Alterado o esquema SQLAlchemy `PurchaseRequestItem.observacao` de `String(255)` para `Text`.
  2. Inserido o comando de migração direta `ALTER TABLE purchase_request_items ALTER COLUMN observacao TYPE TEXT` nos ciclos automáticos.

### 1.3 Alinhamento de Fluxo Padrão de Compras (Status)
* **Problema:** Ao aprovar uma "Pesquisa de Cotação Prévia", a "Solicitação de Compra" (SC) gerada já nascia com o status `APROVADA`.
* **Resolução:** Modificado o gerador para criar a SC com o status `PENDENTE`. Desta forma, a solicitação entra naturalmente no funil do *Workflow* de aprovação e cotações formalizadas (`PurchaseRequestStatus.PENDENTE`), seguindo o padrão de arquitetura do sistema.
* **Complemento:** O registro no histórico (`log_history`) foi atualizado para "Converteu Pesquisa em Solicitação de Compra", removendo a confusão semântica de "aprovou".

### 1.4 Colisões de Sequência (Unique Constraint)
* **Problema:** Possibilidade de violações de constraint em códigos da aplicação ao rodar funções do tipo `generate_request_number`.
* **Resolução:** Refatorados os geradores de ID (`app/crud/procurement.py`) para iterar ativamente num laço `while`, verificando a existência real no banco de dados antes de registrar, blindando a função contra códigos duplicados.

---

## 2. Correções na Infraestrutura e Inicialização (`init_app.py` / `main.py`)

### 2.1 Isolamento de Transações DDL (PostgreSQL)
* **Problema:** O script de inicialização `init_app.py` falhava ao instalar o sistema do zero com `UndefinedTableError: relation "users" does not exist`, revertendo toda a base de dados.
* **Causa:** Todos os comandos de migração (`create_all` e `ALTER TABLE`) estavam aninhados dentro da mesma transação `async with engine.begin()`. No dialeto do PostgreSQL, quando um `ALTER TABLE` falha (por exemplo, ao tentar criar uma coluna que já existe em versões novas da tabela), ele coloca **toda a transação** em estado de aborto, revertendo inclusive a criação primária das tabelas (`create_all`).
* **Resolução:** O script de inicialização e o lifespan (`app/main.py`) foram totalmente refatorados. O `create_all` foi posicionado em um bloco autônomo, e cada declaração subsequente de migração condicional (`ALTER TABLE`) foi empacotada individualmente em um escopo exclusivo `async with engine.begin(): try/except`. Dessa forma, o fracasso programado de um "ALTER" não contamina o ciclo de vida do PostgreSQL.

### 2.2 Uvicorn Hot-Reloading no Docker
* **Problema:** Mudanças feitas no repositório de arquivos local não refletiam no container, obrigando o mantenedor a destruir e construir novamente os containers (`update_docker.sh`) a cada teste.
* **Resolução:** Adicionada a flag `--reload` no comando base do uvicorn no arquivo `docker-compose.yml`. Agora, as mudanças no código-fonte Python refletem de forma imediata na aplicação em execução.

## 3. Gerenciamento Dinâmico de Tipos de Contrato

* **Problema:** Os tipos de contrato eram mantidos em uma lista estática (hardcoded) no template HTML do formulário de contratos, limitando a flexibilidade e escalabilidade do sistema.
* **Resolução:**
  1. **Modelo de Banco de Dados:** Criado o modelo `ContractType` no banco de dados e adicionada a relação `tipo_contrato` (via chave estrangeira `tipo_id`) na tabela `purchase_contracts`.
  2. **Inicialização & Migrações:** Atualizado o arquivo `init_app.py` para criar a tabela `contract_types` e adicionar dinamicamente a coluna `tipo_id` nas instalações existentes do banco de dados, além de garantir a sincronização de sequências para prevenir conflitos de chaves primárias.
  3. **Interface de Administração:** Criados endpoints administrativos (`/compras/contratos/tipos/*`) permitindo cadastrar, listar, editar, ativar/desativar e excluir tipos de contrato, respeitando o controle de acesso de papéis (RBAC).
  4. **Formulário Dinâmico:** Atualizados os endpoints e os templates do formulário de contrato para carregar dinamicamente os tipos do banco de dados e sincronizar os IDs/nomes via JavaScript, preservando a retrocompatibilidade com contratos legados que não possuem `tipo_id`.

## Data da Intervenção
* **Data:** Julho de 2026
* **Módulos Afetados:** Procurement (Compras), Database Initialization (Core), Front-end templates, Admin routes.
