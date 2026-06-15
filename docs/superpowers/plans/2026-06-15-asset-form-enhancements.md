# Asset Form Enhancements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add location dropdown, free-text "em posse de" field, and make supplier/invoice non-required with warning to the asset registration/edit forms.

**Architecture:** Extend the existing Asset model with a new `em_posse_de` string column (free-text, not FK). Expose existing `current_local_id` FK as an optional dropdown. Create a location management page using the same pattern as the existing categories admin page. All changes are additive — no existing behavior is altered.

**Tech Stack:** Python/FastAPI, SQLAlchemy async, Jinja2 templates, TailwindCSS, SQLite

---

### Task 1: Add `em_posse_de` column to Asset model and auto-migration

**Files:**
- Modify: `app/models/asset.py`
- Modify: `app/main.py`

- [ ] **Step 1: Add `em_posse_de` column to the Asset model**

In `app/models/asset.py`, add the new column after the existing `numero_serie` column (line 30):

```python
# After numero_serie line:
em_posse_de: Mapped[str | None] = mapped_column(String, nullable=True)
```

Edit using:
- File: `app/models/asset.py`
- Old: `    numero_serie: Mapped[str | None] = mapped_column(String, index=True, nullable=True)\n\n    # Categoria`
- New: `    numero_serie: Mapped[str | None] = mapped_column(String, index=True, nullable=True)\n    em_posse_de: Mapped[str | None] = mapped_column(String, nullable=True)\n\n    # Categoria`

- [ ] **Step 2: Add auto-migration for the new column**

In `app/main.py`, add a migration block in the `lifespan` function after the existing `categoria_id` migration block (after line 47):

```python
    # Asset - em_posse_de column
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE assets ADD COLUMN em_posse_de VARCHAR(255)"))
        except Exception:
            pass
```

Edit using:
- File: `app/main.py`
- Old: `    # Asset Categories - FK column\n    async with engine.begin() as conn:\n        try:\n            await conn.execute(text("ALTER TABLE assets ADD COLUMN categoria_id INTEGER REFERENCES asset_categories(id)"))\n        except Exception:\n            pass\n\n    yield`
- New: `    # Asset Categories - FK column\n    async with engine.begin() as conn:\n        try:\n            await conn.execute(text("ALTER TABLE assets ADD COLUMN categoria_id INTEGER REFERENCES asset_categories(id)"))\n        except Exception:\n            pass\n\n    # Asset - em_posse_de column\n    async with engine.begin() as conn:\n        try:\n            await conn.execute(text("ALTER TABLE assets ADD COLUMN em_posse_de VARCHAR(255)"))\n        except Exception:\n            pass\n\n    yield`

- [ ] **Step 3: Commit**

```bash
git add app/models/asset.py app/main.py
git commit -m "feat: add em_posse_de column to Asset model with auto-migration"
```

---

### Task 2: Add `em_posse_de` to Asset schemas

**Files:**
- Modify: `app/schemas/asset.py`

- [ ] **Step 1: Add `em_posse_de` to AssetBase**

In `app/schemas/asset.py`, add `em_posse_de` after `numero_serie` (line 23):

```python
    em_posse_de: Optional[str] = None
```

Edit using:
- File: `app/schemas/asset.py`
- Old: `    numero_serie: Optional[str] = None\n\n    categoria_id: Optional[int] = None`
- New: `    numero_serie: Optional[str] = None\n    em_posse_de: Optional[str] = None\n\n    categoria_id: Optional[int] = None`

- [ ] **Step 2: Add `em_posse_de` to AssetUpdate**

In `app/schemas/asset.py`, add after `numero_serie` in `AssetUpdate` (line 45):

```python
    em_posse_de: Optional[str] = None
```

Edit using:
- File: `app/schemas/asset.py`
- Old: `    numero_serie: Optional[str] = None\n    fornecedor_id: Optional[int] = None`
- New: `    numero_serie: Optional[str] = None\n    em_posse_de: Optional[str] = None\n    fornecedor_id: Optional[int] = None`

- [ ] **Step 3: Commit**

```bash
git add app/schemas/asset.py
git commit -m "feat: add em_posse_de to AssetCreate and AssetUpdate schemas"
```

---

### Task 3: Update asset form HTML — supplier/invoice warning + new fields

**Files:**
- Modify: `app/templates/assets/form.html`

- [ ] **Step 1: Add warning banner below the header**

After the error block (`{% endif %}` on line 24) and before `<form>` tag (line 26), add:

```html
        <div class="bg-amber-50 border-l-4 border-amber-500 text-amber-800 p-4 m-6 mb-0" role="alert">
            <span class="font-bold block uppercase text-xs mb-1">Aviso</span>
            <span class="block text-xs">Fornecedor e Nota Fiscal são recomendados para rastreabilidade fiscal, mas não são obrigatórios.</span>
        </div>
```

Edit using:
- File: `app/templates/assets/form.html`
- Old: `        {% endif %}\n\n        <form action="{% if asset %}/assets/{{ asset.id }}/edit`
- New: `        {% endif %}\n\n        <div class="bg-amber-50 border-l-4 border-amber-500 text-amber-800 p-4 m-6 mb-0" role="alert">\n            <span class="font-bold block uppercase text-xs mb-1">Aviso</span>\n            <span class="block text-xs">Fornecedor e Nota Fiscal são recomendados para rastreabilidade fiscal, mas não são obrigatórios.</span>\n        </div>\n\n        <form action="{% if asset %}/assets/{{ asset.id }}/edit`

- [ ] **Step 2: Change supplier/invoice labels to remove "required" indicators**

Change the supplier label from:
```html
<label for="fornecedor_id" class="block text-xs font-bold uppercase text-gray-900 mb-2 text-blue-600">1. Selecione o Fornecedor</label>
```
To:
```html
<label for="fornecedor_id" class="block text-xs font-bold uppercase text-gray-900 mb-2">Fornecedor</label>
```

Edit using:
- File: `app/templates/assets/form.html`
- Old: `<label for="fornecedor_id" class="block text-xs font-bold uppercase text-gray-900 mb-2 text-blue-600">1. Selecione o Fornecedor</label>`
- New: `<label for="fornecedor_id" class="block text-xs font-bold uppercase text-gray-900 mb-2">Fornecedor</label>`

Change the invoice label from:
```html
<label for="nota_fiscal_id" class="block text-xs font-bold uppercase text-gray-900 mb-2 text-blue-600">2. Vincule a Nota Fiscal</label>
```
To:
```html
<label for="nota_fiscal_id" class="block text-xs font-bold uppercase text-gray-900 mb-2">Nota Fiscal</label>
```

Edit using:
- File: `app/templates/assets/form.html`
- Old: `<label for="nota_fiscal_id" class="block text-xs font-bold uppercase text-gray-900 mb-2 text-blue-600">2. Vincule a Nota Fiscal</label>`
- New: `<label for="nota_fiscal_id" class="block text-xs font-bold uppercase text-gray-900 mb-2">Nota Fiscal</label>`

- [ ] **Step 3: Add "Localização & Responsabilidade" section before the Actions div**

Add a new section block between the closing `</div>` of Section 3 (Photo, line 251) and the `<!-- Actions -->` comment (line 254):

```html
    <!-- Section 4: Location & Responsibility -->
    <div>
        <h3 class="font-mono text-xs font-bold text-gray-400 uppercase tracking-widest mb-6 border-b border-gray-200 pb-2">
            Localização & Responsabilidade</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <label for="current_local_id" class="block text-xs font-bold uppercase text-gray-900 mb-2">Localização do Equipamento</label>
                <div class="flex gap-2">
                    <select name="current_local_id" id="current_local_id"
                        class="block w-full px-4 py-3 bg-white border-2 border-gray-200 rounded-none focus:border-black focus:ring-0 transition">
                        <option value="">Não definida</option>
                        {% for local in locais %}
                        <option value="{{ local.id }}" {% if asset and asset.current_local_id == local.id %}selected{% endif %}>{{ local.nome }}</option>
                        {% endfor %}
                    </select>
                    <a href="/assets/admin/localizacoes" target="_blank"
                        class="bg-white border-2 border-gray-200 hover:border-black hover:bg-black hover:text-white px-3 transition rounded-none flex items-center justify-center"
                        title="Gerenciar localizações">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                        </svg>
                    </a>
                </div>
            </div>
            <div>
                <label for="em_posse_de" class="block text-xs font-bold uppercase text-gray-900 mb-2">Em Posse de</label>
                <input type="text" name="em_posse_de" id="em_posse_de"
                    value="{{ asset.em_posse_de if asset and asset.em_posse_de else '' }}"
                    class="block w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-none focus:border-black focus:ring-0 transition"
                    placeholder="Nome da pessoa utilizando este equipamento">
            </div>
        </div>
    </div>
```

Edit using:
- File: `app/templates/assets/form.html`
- Old: `    <!-- Actions -->`
- New: `    <!-- Section 4: Location & Responsibility -->\n    <div>\n        <h3 class="font-mono text-xs font-bold text-gray-400 uppercase tracking-widest mb-6 border-b border-gray-200 pb-2">\n            Localização & Responsabilidade</h3>\n        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">\n            <div>\n                <label for="current_local_id" class="block text-xs font-bold uppercase text-gray-900 mb-2">Localização do Equipamento</label>\n                <div class="flex gap-2">\n                    <select name="current_local_id" id="current_local_id"\n                        class="block w-full px-4 py-3 bg-white border-2 border-gray-200 rounded-none focus:border-black focus:ring-0 transition">\n                        <option value="">Não definida</option>\n                        {% for local in locais %}\n                        <option value="{{ local.id }}" {% if asset and asset.current_local_id == local.id %}selected{% endif %}>{{ local.nome }}</option>\n                        {% endfor %}\n                    </select>\n                    <a href="/assets/admin/localizacoes" target="_blank"\n                        class="bg-white border-2 border-gray-200 hover:border-black hover:bg-black hover:text-white px-3 transition rounded-none flex items-center justify-center"\n                        title="Gerenciar localizações">\n                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">\n                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>\n                        </svg>\n                    </a>\n                </div>\n            </div>\n            <div>\n                <label for="em_posse_de" class="block text-xs font-bold uppercase text-gray-900 mb-2">Em Posse de</label>\n                <input type="text" name="em_posse_de" id="em_posse_de"\n                    value="{{ asset.em_posse_de if asset and asset.em_posse_de else '' }}"\n                    class="block w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-none focus:border-black focus:ring-0 transition"\n                    placeholder="Nome da pessoa utilizando este equipamento">\n            </div>\n        </div>\n    </div>\n\n\n    <!-- Actions -->`

- [ ] **Step 4: Commit**

```bash
git add app/templates/assets/form.html
git commit -m "feat: add location/posse fields and supplier/invoice warning to asset form"
```

---

### Task 4: Update asset endpoints to handle new fields

**Files:**
- Modify: `app/web/endpoints/assets.py`

- [ ] **Step 1: Import location CRUD and load locais in GET /new**

In the imports section (around line 21), add:
```python
from app.crud import location
```

Edit using:
- File: `app/web/endpoints/assets.py`
- Old: `from app.crud import asset_category as asset_category_crud`
- New: `from app.crud import asset_category as asset_category_crud\nfrom app.crud import location`

- [ ] **Step 2: Pass locais to template in GET /new**

In the `new_asset_form` function (lines 147-161), add `locais` fetch and pass it:

```python
@router.get("/new", response_class=HTMLResponse)
async def new_asset_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    fornecedores = await crud_supplier.get_fornecedores(db)
    categories = await asset_category_crud.category.get_multi(db)
    locais = await location.localizacao.get_multi(db)
    return templates.TemplateResponse("assets/form.html", {
        "request": request,
        "user": current_user,
        "fornecedores": fornecedores,
        "categories": categories,
        "locais": locais,
        "title": "Novo Ativo"
    })
```

Edit using:
- File: `app/web/endpoints/assets.py`
- Old: `    fornecedores = await crud_supplier.get_fornecedores(db)\n    categories = await asset_category_crud.category.get_multi(db)\n    return templates.TemplateResponse("assets/form.html", {\n        "request": request,\n        "user": current_user,\n        "fornecedores": fornecedores,\n        "categories": categories,\n        "title": "Novo Ativo"\n    })`
- New: `    fornecedores = await crud_supplier.get_fornecedores(db)\n    categories = await asset_category_crud.category.get_multi(db)\n    locais = await location.localizacao.get_multi(db)\n    return templates.TemplateResponse("assets/form.html", {\n        "request": request,\n        "user": current_user,\n        "fornecedores": fornecedores,\n        "categories": categories,\n        "locais": locais,\n        "title": "Novo Ativo"\n    })`

- [ ] **Step 3: Accept new fields in POST /new**

Modify the `create_asset` function signature to add `current_local_id` and `em_posse_de` parameters:

```python
@router.post("/new", response_class=HTMLResponse)
async def create_asset(
    request: Request,
    nome: Annotated[str, Form()],
    modelo: Annotated[str, Form()],
    e_patrimonio: Annotated[str, Form()],
    descricao: Annotated[Optional[str], Form()] = None,
    data_aquisicao: Annotated[Optional[str], Form()] = None,
    valor_aquisicao: Annotated[Optional[str], Form()] = None,
    numero_serie: Annotated[Optional[str], Form()] = None,
    fornecedor_id: Annotated[Optional[int], Form()] = None,
    nota_fiscal_id: Annotated[Optional[int], Form()] = None,
    categoria_id: Annotated[Optional[int], Form()] = None,
    current_local_id: Annotated[Optional[int], Form()] = None,
    em_posse_de: Annotated[Optional[str], Form()] = None,
    foto: Annotated[Optional[UploadFile], File()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
```

Use multiple edits:

Edit 1 — add params:
- File: `app/web/endpoints/assets.py`
- Old: `    categoria_id: Annotated[Optional[int], Form()] = None,\n    foto: Annotated[Optional[UploadFile], File()] = None,`
- New: `    categoria_id: Annotated[Optional[int], Form()] = None,\n    current_local_id: Annotated[Optional[int], Form()] = None,\n    em_posse_de: Annotated[Optional[str], Form()] = None,\n    foto: Annotated[Optional[UploadFile], File()] = None,`

Edit 2 — add fields to AssetCreate and pass locais on error:
- File: `app/web/endpoints/assets.py`
- Old: `        asset_in = AssetCreate(\n            nome=nome,\n            modelo=modelo,\n            e_patrimonio=e_patrimonio,\n            descricao=descricao,\n            data_aquisicao=dt_aquisicao,\n            valor=val_aquisicao,\n            numero_serie=numero_serie,\n            fornecedor_id=fornecedor_id,\n            nota_fiscal_id=nota_fiscal_id,\n            categoria_id=categoria_id,\n            foto_path=foto_path,\n            created_by_id=current_user.id if current_user else None,\n            status=AssetStatus.DISPONIVEL\n        )`
- New: `        asset_in = AssetCreate(\n            nome=nome,\n            modelo=modelo,\n            e_patrimonio=e_patrimonio,\n            descricao=descricao,\n            data_aquisicao=dt_aquisicao,\n            valor=val_aquisicao,\n            numero_serie=numero_serie,\n            fornecedor_id=fornecedor_id,\n            nota_fiscal_id=nota_fiscal_id,\n            categoria_id=categoria_id,\n            current_local_id=current_local_id,\n            em_posse_de=em_posse_de,\n            foto_path=foto_path,\n            created_by_id=current_user.id if current_user else None,\n            status=AssetStatus.DISPONIVEL\n        )`

Edit 3 — error handler pass locais:
- File: `app/web/endpoints/assets.py`
- Old: `        fornecedores = await crud_supplier.get_fornecedores(db)\n        categories = await asset_category_crud.category.get_multi(db)\n        return templates.TemplateResponse("assets/form.html", {\n            "request": request,\n            "user": current_user,\n            "fornecedores": fornecedores,\n            "categories": categories,\n            "error": f"Erro ao criar ativo: {str(e)}",\n            "title": "Novo Ativo"\n        })`
- New: `        fornecedores = await crud_supplier.get_fornecedores(db)\n        categories = await asset_category_crud.category.get_multi(db)\n        locais = await location.localizacao.get_multi(db)\n        return templates.TemplateResponse("assets/form.html", {\n            "request": request,\n            "user": current_user,\n            "fornecedores": fornecedores,\n            "categories": categories,\n            "locais": locais,\n            "error": f"Erro ao criar ativo: {str(e)}",\n            "title": "Novo Ativo"\n        })`

- [ ] **Step 4: Pass locais to template in GET /{asset_id}/edit**

In `edit_asset_form` (lines 607-632), add locais:

```python
    fornecedores = await crud_supplier.get_fornecedores(db)
    categories = await asset_category_crud.category.get_multi(db)
    locais = await location.localizacao.get_multi(db)

    return templates.TemplateResponse("assets/form.html", {
        ...
        "locais": locais,
        ...
    })
```

Edit using:
- File: `app/web/endpoints/assets.py`
- Old: `    fornecedores = await crud_supplier.get_fornecedores(db)\n    categories = await asset_category_crud.category.get_multi(db)\n\n    return templates.TemplateResponse("assets/form.html", {\n        "request": request,\n        "user": current_user,\n        "asset": asset,\n        "fornecedores": fornecedores,\n        "categories": categories,\n        "title": f"Editar Ativo: {asset.nome}"\n    })`
- New: `    fornecedores = await crud_supplier.get_fornecedores(db)\n    categories = await asset_category_crud.category.get_multi(db)\n    locais = await location.localizacao.get_multi(db)\n\n    return templates.TemplateResponse("assets/form.html", {\n        "request": request,\n        "user": current_user,\n        "asset": asset,\n        "fornecedores": fornecedores,\n        "categories": categories,\n        "locais": locais,\n        "title": f"Editar Ativo: {asset.nome}"\n    })`

- [ ] **Step 5: Accept new fields in POST /{asset_id}/edit**

Add `current_local_id` and `em_posse_de` to the `update_asset` function signature:

Edit 1 — params:
- File: `app/web/endpoints/assets.py`
- Old: `    categoria_id: Annotated[Optional[int], Form()] = None,\n    foto: Annotated[Optional[UploadFile], File()] = None,`
  (in the update_asset function context, around line 647)
- Wait — this matches the same pattern as create. Let me use a more specific match.

Edit 1:
- File: `app/web/endpoints/assets.py`
- Old: `    nota_fiscal_id: Annotated[Optional[int], Form()] = None,\n    categoria_id: Annotated[Optional[int], Form()] = None,\n    foto: Annotated[Optional[UploadFile], File()] = None,`
- New: `    nota_fiscal_id: Annotated[Optional[int], Form()] = None,\n    categoria_id: Annotated[Optional[int], Form()] = None,\n    current_local_id: Annotated[Optional[int], Form()] = None,\n    em_posse_de: Annotated[Optional[str], Form()] = None,\n    foto: Annotated[Optional[UploadFile], File()] = None,`

Edit 2 — AssetUpdate:
- File: `app/web/endpoints/assets.py`
- Old: `        asset_update = AssetUpdate(\n            nome=nome,\n            modelo=modelo,\n            e_patrimonio=e_patrimonio,\n            descricao=descricao if descricao else None,\n            data_aquisicao=dt_aquisicao,\n            valor=val_aquisicao,\n            numero_serie=numero_serie,\n            fornecedor_id=fornecedor_id,\n            nota_fiscal_id=nota_fiscal_id,\n            categoria_id=categoria_id,\n            foto_path=foto_path\n        )`
- New: `        asset_update = AssetUpdate(\n            nome=nome,\n            modelo=modelo,\n            e_patrimonio=e_patrimonio,\n            descricao=descricao if descricao else None,\n            data_aquisicao=dt_aquisicao,\n            valor=val_aquisicao,\n            numero_serie=numero_serie,\n            fornecedor_id=fornecedor_id,\n            nota_fiscal_id=nota_fiscal_id,\n            categoria_id=categoria_id,\n            current_local_id=current_local_id,\n            em_posse_de=em_posse_de if em_posse_de else None,\n            foto_path=foto_path\n        )`

Edit 3 — error handler pass locais:
- File: `app/web/endpoints/assets.py`
- Old: (in update_asset error handler) `        fornecedores = await crud_supplier.get_fornecedores(db)\n        categories = await asset_category_crud.category.get_multi(db)\n        return templates.TemplateResponse("assets/form.html", {\n            "request": request,\n            "user": current_user,\n            "asset": asset,\n            "fornecedores": fornecedores,\n            "categories": categories,\n            "error": f"Erro ao atualizar ativo: {str(e)}",\n            "title": f"Editar Ativo: {asset.nome}"\n        })`
- New: `        fornecedores = await crud_supplier.get_fornecedores(db)\n        categories = await asset_category_crud.category.get_multi(db)\n        locais = await location.localizacao.get_multi(db)\n        return templates.TemplateResponse("assets/form.html", {\n            "request": request,\n            "user": current_user,\n            "asset": asset,\n            "fornecedores": fornecedores,\n            "categories": categories,\n            "locais": locais,\n            "error": f"Erro ao atualizar ativo: {str(e)}",\n            "title": f"Editar Ativo: {asset.nome}"\n        })`

- [ ] **Step 6: Commit**

```bash
git add app/web/endpoints/assets.py
git commit -m "feat: handle current_local_id and em_posse_de in asset create/update endpoints"
```

---

### Task 5: Create location management template

**Files:**
- Create: `app/templates/assets/admin/locais.html`

- [ ] **Step 1: Create the locais.html template**

```html
{% extends "base.html" %}

{% block content %}
<div class="space-y-8 fade-in">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 border-b-2 border-black pb-4">
        <div>
            <h1 class="text-3xl font-bold text-black uppercase tracking-tighter leading-none">LOCALIZAÇÕES</h1>
            <p class="font-mono text-xs text-gray-500 mt-1 uppercase tracking-widest">Gerenciamento de Localizações de Equipamentos</p>
        </div>
        <div class="flex items-center gap-4">
            <a href="/assets" class="text-xs font-bold uppercase hover:underline">Voltar para Ativos</a>
            <a href="/assets/new" class="text-xs font-bold uppercase hover:underline">Novo Ativo</a>
        </div>
    </div>

    {% if error %}
    <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4" role="alert">
        <span class="font-bold block uppercase text-xs mb-1">Erro</span>
        <span class="block text-sm">{{ error }}</span>
    </div>
    {% endif %}

    {% if success %}
    <div class="bg-green-100 border-l-4 border-green-500 text-green-700 p-4" role="alert">
        <span class="block text-sm">{{ success }}</span>
    </div>
    {% endif %}

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- New Location Form -->
        <div class="lg:col-span-1">
            <div class="bg-white border-2 border-black p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] sticky top-8">
                <h3 class="font-bold text-sm uppercase tracking-widest mb-6 border-b-2 border-black pb-2">Nova Localização</h3>
                <form action="/assets/admin/localizacoes" method="POST" class="space-y-4">
                    <div class="space-y-1">
                        <label class="block text-[10px] font-bold uppercase text-gray-500">Nome da Localização</label>
                        <input type="text" name="nome" required placeholder="Ex: Sala 101, Andar 3, Prédio A"
                            class="w-full border-2 border-black p-2 text-sm font-mono focus:ring-0 focus:border-brand-500">
                    </div>
                    <div class="space-y-1">
                        <label class="block text-[10px] font-bold uppercase text-gray-500">Departamento (Opcional)</label>
                        <select name="departamento_id"
                            class="w-full border-2 border-black p-2 text-sm font-mono focus:ring-0 focus:border-brand-500">
                            <option value="">Nenhum</option>
                            {% for dept in departamentos %}
                            <option value="{{ dept.id }}">{{ dept.nome }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <button type="submit"
                        class="w-full bg-black text-white font-bold uppercase text-xs py-3 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.2)] hover:bg-gray-800 transition">
                        Cadastrar Localização
                    </button>
                </form>
            </div>
        </div>

        <!-- Locations List -->
        <div class="lg:col-span-2">
            <div class="bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-black text-white font-mono text-xs uppercase tracking-widest">
                            <th class="px-6 py-4 border-b border-gray-800">Localização</th>
                            <th class="px-6 py-4 border-b border-gray-800">Departamento</th>
                            <th class="px-6 py-4 border-b border-gray-800 text-right">Ativos</th>
                            <th class="px-6 py-4 border-b border-gray-800 text-right">Ações</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
                        {% for local in locais %}
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-4 font-bold text-sm uppercase">{{ local.nome }}</td>
                            <td class="px-6 py-4 text-xs text-gray-500">{{ local.departamento.nome if local.departamento else '-' }}</td>
                            <td class="px-6 py-4 text-xs text-right font-mono">{{ local.assets|length if local.assets else 0 }}</td>
                            <td class="px-6 py-4 text-right">
                                <form action="/assets/admin/localizacoes/{{ local.id }}/delete" method="POST" onsubmit="return confirm('Excluir localização {{ local.nome }}?')" class="inline">
                                    <button type="submit" class="text-red-600 hover:underline text-[10px] font-bold uppercase">Excluir</button>
                                </form>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="4" class="px-6 py-8 text-center text-gray-400 font-mono text-xs uppercase">Nenhuma localização cadastrada</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

Write file: `app/templates/assets/admin/locais.html`

- [ ] **Step 2: Commit**

```bash
git add app/templates/assets/admin/locais.html
git commit -m "feat: add location management template (CRUD)"
```

---

### Task 6: Add location management routes

**Files:**
- Modify: `app/web/endpoints/assets.py`

- [ ] **Step 1: Add routes for location management**

Append the following routes at the end of `app/web/endpoints/assets.py` (after line 1131, before the end of file):

```python

# --- Location Management ---

@router.get("/admin/localizacoes", response_class=HTMLResponse)
async def list_locais(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        return RedirectResponse(url="/assets", status_code=303)

    locais_list = await location.localizacao.get_multi(db)
    departamentos_list = await location.departamento.get_multi(db)

    # Eager load assets for count
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    result = await db.execute(
        select(Localizacao).options(selectinload(Localizacao.assets), selectinload(Localizacao.departamento))
    )
    locais_list = result.scalars().all()

    return templates.TemplateResponse("assets/admin/locais.html", {
        "request": request,
        "user": current_user,
        "locais": locais_list,
        "departamentos": departamentos_list,
        "title": "Localizações"
    })

from app.models.location import Localizacao

@router.post("/admin/localizacoes")
async def create_local(
    nome: Annotated[str, Form()],
    departamento_id: Annotated[Optional[int], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        return RedirectResponse(url="/assets", status_code=303)

    from app.schemas.location import LocalizacaoCreate
    local_in = LocalizacaoCreate(nome=nome, departamento_id=departamento_id)
    await location.localizacao.create(db, obj_in=local_in)
    return RedirectResponse(url="/assets/admin/localizacoes", status_code=303)


@router.post("/admin/localizacoes/{local_id}/delete")
async def delete_local(
    local_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        return RedirectResponse(url="/assets", status_code=303)

    try:
        await location.localizacao.remove(db, id=local_id)
        return RedirectResponse(url="/assets/admin/localizacoes", status_code=303)
    except Exception as e:
        await db.rollback()
        locais_list = await location.localizacao.get_multi(db)
        departamentos_list = await location.departamento.get_multi(db)

        error_msg = f"Erro ao excluir: {str(e)}"
        if "constraint" in str(e).lower() or "foreign" in str(e).lower():
            error_msg = "Não é possível excluir esta localização pois há ativos vinculados a ela."

        return templates.TemplateResponse("assets/admin/locais.html", {
            "request": request,
            "user": current_user,
            "locais": locais_list,
            "departamentos": departamentos_list,
            "error": error_msg,
            "title": "Localizações"
        })
```

This requires the `Localizacao` import. Edit the existing import at the top:

- Edit 1: Add `Localizacao` to the models import or add a new import.
  The `Localizacao` model is already used via `location.localizacao`. But for the select query in the route, we need the model class. 

Add this import near the top (after the existing imports):
- File: `app/web/endpoints/assets.py`
- Old: `from app.models.asset import AssetStatus`
- New: `from app.models.asset import AssetStatus\nfrom app.models.location import Localizacao`

- [ ] **Step 2: Commit**

```bash
git add app/web/endpoints/assets.py
git commit -m "feat: add location management routes (list, create, delete)"
```

---

### Task 7: Verify the implementation

**Files:**
- None (verification only)

- [ ] **Step 1: Start the application and verify it boots**

Run: `cd /home/instant/assettrack_ti && timeout 10 python -c "from app.main import app; print('App loaded OK')" 2>&1`
Expected: "App loaded OK" without errors

- [ ] **Step 2: Verify the new model column is recognized**

Run: `cd /home/instant/assettrack_ti && python -c "from app.models.asset import Asset; print('em_posse_de' in [c.name for c in Asset.__table__.columns])"`
Expected: `True`

- [ ] **Step 3: Verify the schema accepts the new field**

Run: `cd /home/instant/assettrack_ti && python -c "from app.schemas.asset import AssetCreate; a = AssetCreate(nome='test', e_patrimonio='T-001', em_posse_de='Fulano'); print(a.em_posse_de)"`
Expected: `Fulano`

- [ ] **Step 4: Commit (if any fixes needed)**

```bash
git add -A
git commit -m "chore: verification fixes"
```
