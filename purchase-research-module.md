# Módulo de Cotação/Pesquisa de Compra (Purchase Research Module)

## Goal
Implement a Purchase Research module inside the Procurement (Compras) module. Users can search for products, add photos, links, prices, and quantities. Upon approval, these items automatically convert into an approved Purchase Request and are registered as internal products (either Consumables or Fixed Assets).

## Tasks

### Phase 1: Database Models & Migrations
- [ ] **Task 1: Add Database Models** → Create `PurchaseResearch` and `PurchaseResearchItem` models in `app/models/procurement.py`. Verify: Fields like `nome_produto`, `link_produto`, `imagem_path`, `valor_estimado`, `quantidade`, `tipo_produto` ("Consumo" vs "Imobilizado") and `aprovado` are defined.
- [ ] **Task 2: Update database initialization & migration** → Run `python run_postgres_migration.py` or verify db connection. Verify: Tables `purchase_researches` and `purchase_research_items` are created in PostgreSQL database.

### Phase 2: Schemas & CRUD
- [ ] **Task 3: Create Pydantic Schemas** → Create schemas for `PurchaseResearch` and `PurchaseResearchItem` in `app/schemas/procurement.py` (for creation and responses). Verify: Schemas compile without errors.
- [ ] **Task 4: Implement CRUD operations** → Add CRUD functions in `app/crud/procurement.py` for creating a research request, listing research requests, and finding a research by ID. Verify: Functions correctly execute queries on the database.

### Phase 3: Business Logic (Conversion Service)
- [ ] **Task 5: Implement approved research conversion** → Create a function `convert_research_to_purchase_request` in `app/services/procurement_service.py` that, when a research is approved:
  1. Generates a new `PurchaseProduct` for each approved research item (Consumo vs Imobilizado).
  2. For Consumo items, inserts/initializes a `MaterialStock` record.
  3. Creates a new `PurchaseRequest` in `PurchaseRequestStatus.APROVADA` status, populated with the newly created products as `PurchaseRequestItem`s.
  Verify: Tests or database state verifies products and pre-approved purchase requests are successfully generated.

### Phase 4: Web Endpoints
- [ ] **Task 6: Create endpoints in procurement router** → In `app/web/endpoints/procurement.py`, add routes for:
  - `GET /compras/pesquisas` (list all researches)
  - `GET /compras/pesquisas/new` (render creation form)
  - `POST /compras/pesquisas/new` (save research, handling file upload for product photos)
  - `GET /compras/pesquisas/{id}` (detail view of research, with approve/reject actions for managers)
  - `POST /compras/pesquisas/{id}/decidir` (manager decides and triggers conversion)
  Verify: Routes exist and return HTTP 200/303 responses.

### Phase 5: UI & Templates (Neo-Brutalism)
- [ ] **Task 7: Create frontend templates** → Design and create:
  - `app/templates/procurement/researches_list.html` (lists researches)
  - `app/templates/procurement/research_form.html` (allows dynamic list of products with photo upload, link, and price using JS)
  - `app/templates/procurement/research_detail.html` (shows research items, links, photos, and approval toggles/actions)
  Verify: Templates load and adhere to the existing Neo-Brutalism system styles.
- [ ] **Task 8: Update menus and dashboards** → Add navigation links to the new module in `app/templates/procurement/dashboard.html` and layout files. Verify: Users can navigate to the new module.

### Phase 6: System Verification
- [ ] **Task 9: Run checklists and test flows** → Start the server, create a research with 2 items (1 Consumo, 1 Imobilizado), upload photos, approve it, and verify that the purchase request was created as "Aprovada" and the products were added to internal products. Verify: No errors are thrown, files are uploaded to `static/uploads`, and database state is consistent.

## Done When
- [ ] Users can create a research request with multiple items (name, link, photo upload, price, type).
- [ ] Managers can approve/reject the research request, selecting which items to approve.
- [ ] Approved researches automatically generate a `PurchaseRequest` with status `APROVADA`.
- [ ] Approved items automatically create products in the internal database (`purchase_products`), with `material_stocks` initialized for consumable items.
