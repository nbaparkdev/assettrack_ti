# Design: Aprimoramentos no Formulário de Cadastro de Ativo

**Data:** 2026-06-15
**Status:** Aprovado

## Contexto

O formulário `/assets/new` precisa de três melhorias:
1. Adicionar campo de localização do equipamento (dropdown, opcional)
2. Tornar fornecedor e nota fiscal não obrigatórios com aviso
3. Adicionar campo "em posse de" (texto livre, opcional) para ativos de infraestrutura

## Mudanças

### 1. Modelo: nova coluna `em_posse_de`

**Arquivo:** `app/models/asset.py`

Adicionar coluna String nullable:
```python
em_posse_de: Mapped[str | None] = mapped_column(String, nullable=True)
```

O campo `current_user_id` existente **não será usado** para esta funcionalidade — ele faz parte do sistema de empréstimo/devolução e permanece inalterado. `em_posse_de` é um campo de texto livre independente.

### 2. Schema: adicionar `em_posse_de`

**Arquivo:** `app/schemas/asset.py`

Adicionar `em_posse_de: Optional[str] = None` em `AssetBase`, e campo equivalente em `AssetUpdate`.

### 3. Formulário HTML

**Arquivo:** `app/templates/assets/form.html`

**Seção Fornecedor/NF:**
- Remover indicadores "1." e "2." e cor azul dos labels
- Adicionar banner amarelo de aviso: "Fornecedor e Nota Fiscal são recomendados para rastreabilidade fiscal, mas não são obrigatórios."

**Nova seção "Localização & Responsabilidade":**
- Dropdown `current_local_id` populado por `locais` — opcional
- Input texto `em_posse_de` — opcional, placeholder "Nome da pessoa que está utilizando este equipamento"
- Ambos dentro de uma nova seção visual após "Financeiro & Specs"

### 4. Endpoints

**Arquivo:** `app/web/endpoints/assets.py`

- `GET /new`: passar `locais` para o template
- `POST /new`: receber `current_local_id` (Optional[int]) e `em_posse_de` (Optional[str])
- `GET /{asset_id}/edit`: passar `locais` para o template
- `POST /{asset_id}/edit`: receber `current_local_id` e `em_posse_de`

### 5. Página de gerenciamento de localizações (novo)

**Template:** `app/templates/assets/admin/locais.html`
**Rotas:** adicionadas em `app/web/endpoints/assets.py`

Funcionalidade:
- Listar localizações existentes (tabela com nome, departamento)
- Criar nova localização (modal ou formulário inline: nome + departamento opcional)
- Editar localização existente
- Excluir localização (com verificação de ativos vinculados)

## Arquivos alterados

| Arquivo | Tipo de mudança |
|---|---|
| `app/models/asset.py` | Adicionar coluna `em_posse_de` |
| `app/schemas/asset.py` | Adicionar `em_posse_de` nos schemas |
| `app/templates/assets/form.html` | Adicionar localização, posse, aviso; ajustar fornecedor/NF |
| `app/web/endpoints/assets.py` | Receber novos campos; nova rota de localizações |
| `app/templates/assets/admin/locais.html` | Novo — CRUD de localizações |

## Fora do escopo

- Alterar o sistema de empréstimo/devolução (current_user_id)
- Migração do banco — o startup do sistema já cria/atualiza tabelas automaticamente
