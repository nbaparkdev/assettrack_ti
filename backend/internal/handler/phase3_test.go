package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strconv"
	"testing"
	"time"

	"github.com/assettrack/backend/internal/config"
	"github.com/assettrack/backend/internal/dto"
	"github.com/assettrack/backend/internal/middleware"
	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"github.com/assettrack/backend/internal/service"
	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

func setupTestDB(t *testing.T) *gorm.DB {
	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	if err != nil {
		t.Fatalf("Failed to open sqlite db: %v", err)
	}

	err = db.AutoMigrate(
		&models.User{},
		&models.Departamento{},
		&models.Localizacao{},
		&models.Armazenamento{},
		&models.Fornecedor{},
		&models.NotaFiscal{},
		&models.AssetCategory{},
		&models.Asset{},
		&models.ServiceCategory{},
		&models.ServiceDefinition{},
		&models.ServiceTicket{},
		&models.ServiceTicketInteraction{},
		&models.SolicitacaoManutencao{},
		&models.Manutencao{},
		&models.Movimentacao{},
		&models.Solicitacao{},
		&models.TermoResponsabilidade{},
	)
	if err != nil {
		t.Fatalf("Failed to migrate: %v", err)
	}

	return db
}

func TestAtivoFixoMaintenanceLockAndRestore(t *testing.T) {
	db := setupTestDB(t)

	// Repositories
	assetRepo := repository.NewAssetRepository(db)

	// Create test dependencies
	dept := models.Departamento{Nome: "TI"}
	db.Create(&dept)

	loc := models.Localizacao{Nome: "Sala 101"}
	db.Create(&loc)

	cat := models.AssetCategory{Nome: "Notebook"}
	db.Create(&cat)

	// Create locked asset
	asset := models.Asset{
		Nome:                  "Notebook Dell",
		EPatrimonio:           "EP-12345",
		Status:                models.AssetStatusDisponivel,
		Bloqueado:             true,
		CurrentDepartamentoID: &dept.ID,
		CurrentLocalID:        &loc.ID,
		CategoriaID:           &cat.ID,
	}
	err := assetRepo.Create(&asset)
	if err != nil {
		t.Fatalf("Failed to create asset: %v", err)
	}

	// 1. Enter maintenance: status changes to "Manutenção"
	asset.Status = models.AssetStatusManutencao
	err = assetRepo.Update(&asset)
	if err != nil {
		t.Fatalf("Failed to update status to Manutencao: %v", err)
	}

	// Verify snapshot was captured
	updatedAsset, _ := assetRepo.GetByID(asset.ID)
	if updatedAsset.PrevStatus == nil || *updatedAsset.PrevStatus != "Disponível" {
		t.Errorf("Expected PrevStatus to be 'Disponível', got %v", updatedAsset.PrevStatus)
	}
	if updatedAsset.PrevLocalID == nil || *updatedAsset.PrevLocalID != loc.ID {
		t.Errorf("Expected PrevLocalID to be %d, got %v", loc.ID, updatedAsset.PrevLocalID)
	}

	// 2. Try to change location while in maintenance (must fail)
	newLoc := models.Localizacao{Nome: "Sala 202"}
	db.Create(&newLoc)

	asset.CurrentLocalID = &newLoc.ID
	err = assetRepo.Update(&asset)
	if err == nil {
		t.Errorf("Expected update location during maintenance to fail, but it succeeded")
	}

	// 3. Exit maintenance: restore state
	asset.CurrentLocalID = &loc.ID // revert local change for clean update
	asset.Status = models.AssetStatusDisponivel
	err = assetRepo.Update(&asset)
	if err != nil {
		t.Fatalf("Failed to exit maintenance: %v", err)
	}

	restoredAsset, _ := assetRepo.GetByID(asset.ID)
	if restoredAsset.Status != models.AssetStatusDisponivel {
		t.Errorf("Expected Status to be restored to 'Disponível', got %v", restoredAsset.Status)
	}
	if restoredAsset.CurrentLocalID == nil || *restoredAsset.CurrentLocalID != loc.ID {
		t.Errorf("Expected restored CurrentLocalID to be %d, got %v", loc.ID, restoredAsset.CurrentLocalID)
	}
	if restoredAsset.PrevStatus != nil {
		t.Errorf("Expected PrevStatus to be cleared, got %v", restoredAsset.PrevStatus)
	}
}

func TestUpdateAssetPersistsManualLocationForSameAssignedUser(t *testing.T) {
	db := setupTestDB(t)
	assetRepo := repository.NewAssetRepository(db)
	categoryRepo := repository.NewAssetCategoryRepository(db)
	handler := NewAssetHandler(assetRepo, categoryRepo)

	department := models.Departamento{Nome: "TI"}
	firstLocation := models.Localizacao{Nome: "Sala A"}
	secondLocation := models.Localizacao{Nome: "Sala B"}
	user := models.User{Nome: "Técnico", Email: "tecnico@example.com", DepartamentoID: &department.ID}
	db.Create(&department)
	db.Create(&firstLocation)
	db.Create(&secondLocation)
	user.LocalizacaoID = &firstLocation.ID
	db.Create(&user)

	asset := models.Asset{
		Nome:           "Notebook",
		EPatrimonio:    "EP-LOCAL-UPDATE",
		Status:         models.AssetStatusEmUso,
		CurrentUserID:  &user.ID,
		CurrentLocalID: &firstLocation.ID,
		EmPosseDe:      &user.Nome,
	}
	if err := assetRepo.Create(&asset); err != nil {
		t.Fatalf("failed to create asset: %v", err)
	}

	payload, err := json.Marshal(map[string]any{
		"nome":             asset.Nome,
		"e_patrimonio":     asset.EPatrimonio,
		"status":           models.AssetStatusEmUso,
		"current_user_id":  user.ID,
		"current_local_id": secondLocation.ID,
	})
	if err != nil {
		t.Fatalf("failed to marshal payload: %v", err)
	}

	ctx, _ := gin.CreateTestContext(httptest.NewRecorder())
	ctx.Request = httptest.NewRequest(http.MethodPut, "/assets/"+strconv.FormatUint(uint64(asset.ID), 10), bytes.NewReader(payload))
	ctx.Request.Header.Set("Content-Type", "application/json")
	ctx.Params = gin.Params{{Key: "id", Value: strconv.FormatUint(uint64(asset.ID), 10)}}
	handler.Update(ctx)

	updated, err := assetRepo.GetByID(asset.ID)
	if err != nil {
		t.Fatalf("failed to reload asset: %v", err)
	}
	if updated.CurrentLocalID == nil || *updated.CurrentLocalID != secondLocation.ID {
		t.Fatalf("expected manually selected location %d, got %v", secondLocation.ID, updated.CurrentLocalID)
	}
}

func TestServiceDeskTicketAutocode(t *testing.T) {
	db := setupTestDB(t)

	repo := repository.NewServiceDeskRepository(db)

	cat := models.ServiceCategory{Nome: "Infraestrutura"}
	_ = repo.CreateCategory(&cat)

	def := models.ServiceDefinition{Nome: "Sem Internet", CategoriaID: cat.ID}
	_ = repo.CreateDefinition(&def)

	user := models.User{Nome: "John", Email: "john@example.com"}
	db.Create(&user)

	// Create first ticket
	ticket1 := models.ServiceTicket{
		SolicitanteID: user.ID,
		ServicoID:     def.ID,
		Descricao:     "Cabo desconectado",
		Prioridade:    models.ServicePriorityMedia,
		Status:        models.ServiceStatusAberto,
	}
	err := repo.CreateTicket(&ticket1)
	if err != nil {
		t.Fatalf("Failed to create ticket 1: %v", err)
	}

	yearStr := strconv.Itoa(time.Now().Year())
	expectedCode1 := "CH-" + yearStr + "-0001"
	if ticket1.Codigo != expectedCode1 {
		t.Errorf("Expected ticket 1 code to be %s, got %s", expectedCode1, ticket1.Codigo)
	}

	// Create second ticket
	ticket2 := models.ServiceTicket{
		SolicitanteID: user.ID,
		ServicoID:     def.ID,
		Descricao:     "Sem pilhas",
		Prioridade:    models.ServicePriorityBaixa,
		Status:        models.ServiceStatusAberto,
	}
	err = repo.CreateTicket(&ticket2)
	if err != nil {
		t.Fatalf("Failed to create ticket 2: %v", err)
	}

	expectedCode2 := "CH-" + yearStr + "-0002"
	if ticket2.Codigo != expectedCode2 {
		t.Errorf("Expected ticket 2 code to be %s, got %s", expectedCode2, ticket2.Codigo)
	}
}

func TestQRHandoverDeliveryConfirmation(t *testing.T) {
	db := setupTestDB(t)

	// Repositories
	userRepo := repository.NewUserRepository(db)
	txRepo := repository.NewTransactionRepository(db)
	maintRepo := repository.NewMaintenanceRepository(db)
	assetRepo := repository.NewAssetRepository(db)

	// Services
	authSvc := service.NewAuthService(userRepo, &config.Config{SecretKey: "testsecret"})
	qrSvc := service.NewQRService()
	qrLogSvc := service.NewQRLogService(repository.NewQRLogRepository(db))

	// Setup user & admin
	adminHash, _ := bcrypt.GenerateFromPassword([]byte("adminpass"), bcrypt.DefaultCost)
	admin := models.User{
		Nome:           "Admin",
		Email:          "admin@example.com",
		HashedPassword: string(adminHash),
		Role:           models.RoleAdmin,
		IsActive:       true,
	}
	db.Create(&admin)

	// Scanned user
	token := "valid_qr_token"
	pBytes, _ := bcrypt.GenerateFromPassword([]byte("1234"), bcrypt.DefaultCost)
	pinHash := string(pBytes)
	now := time.Now().UTC()
	user := models.User{
		Nome:             "User Test",
		Email:            "user@example.com",
		Role:             models.RoleUsuario,
		IsActive:         true,
		QRToken:          &token,
		QRTokenCreatedAt: &now,
		PINHash:          &pinHash,
	}
	db.Create(&user)

	// Setup asset
	cat := models.AssetCategory{Nome: "Monitores"}
	db.Create(&cat)
	asset := models.Asset{
		Nome:        "Monitor LG",
		EPatrimonio: "EP-4455",
		Status:      models.AssetStatusDisponivel,
		CategoriaID: &cat.ID,
	}
	db.Create(&asset)

	// Setup borrowing request
	sol := models.Solicitacao{
		SolicitanteID: &user.ID,
		AssetID:       &asset.ID,
		Motivo:        "Home office",
		Status:        models.StatusSolicitacaoAprovada,
	}
	db.Create(&sol)

	// Test handler delivery confirm
	h := NewQRHandler(userRepo, authSvc, qrSvc, qrLogSvc, txRepo, maintRepo, assetRepo)

	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)

	// Inject current user into gin context (the admin/technician doing the delivery)
	c.Set(middleware.ContextUserKey, &admin)

	reqPayload := dto.DeliveryConfirmRequest{
		QRToken:       &token,
		PIN:           testStringPtr("1234"),
		SolicitacaoID: &sol.ID,
	}
	jsonBytes, _ := json.Marshal(reqPayload)
	c.Request, _ = http.NewRequest(http.MethodPost, "/api/v1/qr/delivery/confirm", bytes.NewBuffer(jsonBytes))

	h.DeliveryConfirm(c)

	if w.Code != http.StatusOK {
		t.Fatalf("Expected delivery confirm to succeed with 200, got %d. Body: %s", w.Code, w.Body.String())
	}

	// Verify Solicitacao was updated
	updatedSol, _ := txRepo.GetSolicitacaoByID(sol.ID)
	if updatedSol.Status != models.StatusSolicitacaoEntregue {
		t.Errorf("Expected Solicitacao status to be 'Entregue', got %v", updatedSol.Status)
	}

	// Verify Asset ownership
	updatedAsset, _ := assetRepo.GetByID(asset.ID)
	if updatedAsset.Status != models.AssetStatusEmUso {
		t.Errorf("Expected Asset status to be 'Em Uso', got %v", updatedAsset.Status)
	}
	if updatedAsset.CurrentUserID == nil || *updatedAsset.CurrentUserID != user.ID {
		t.Errorf("Expected Asset CurrentUserID to be user %d, got %v", user.ID, updatedAsset.CurrentUserID)
	}
}

func TestQRHandoverPINBypass(t *testing.T) {
	db := setupTestDB(t)

	// Repositories
	userRepo := repository.NewUserRepository(db)
	txRepo := repository.NewTransactionRepository(db)
	maintRepo := repository.NewMaintenanceRepository(db)
	assetRepo := repository.NewAssetRepository(db)

	// Services
	authSvc := service.NewAuthService(userRepo, &config.Config{SecretKey: "testsecret"})
	qrSvc := service.NewQRService()
	qrLogSvc := service.NewQRLogService(repository.NewQRLogRepository(db))

	// Setup admin
	adminHash, _ := bcrypt.GenerateFromPassword([]byte("adminpass"), bcrypt.DefaultCost)
	admin := models.User{
		Nome:           "Admin",
		Email:          "admin@example.com",
		HashedPassword: string(adminHash),
		Role:           models.RoleAdmin,
		IsActive:       true,
	}
	db.Create(&admin)

	// Setup normal user (non-manager)
	userHash, _ := bcrypt.GenerateFromPassword([]byte("userpass"), bcrypt.DefaultCost)
	nonManager := models.User{
		Nome:           "User Common",
		Email:          "common@example.com",
		HashedPassword: string(userHash),
		Role:           models.RoleUsuario,
		IsActive:       true,
	}
	db.Create(&nonManager)

	// Scanned user
	token := "valid_qr_token_bypass"
	pBytes, _ := bcrypt.GenerateFromPassword([]byte("1234"), bcrypt.DefaultCost)
	pinHash := string(pBytes)
	now := time.Now().UTC()
	user := models.User{
		Nome:             "User Scanned",
		Email:            "scanned@example.com",
		Role:             models.RoleUsuario,
		IsActive:         true,
		QRToken:          &token,
		QRTokenCreatedAt: &now,
		PINHash:          &pinHash,
	}
	db.Create(&user)

	// Setup asset
	cat := models.AssetCategory{Nome: "Monitores"}
	db.Create(&cat)
	asset := models.Asset{
		Nome:        "Monitor LG 2",
		EPatrimonio: "EP-9988",
		Status:      models.AssetStatusDisponivel,
		CategoriaID: &cat.ID,
	}
	db.Create(&asset)

	// Setup borrowing request
	sol := models.Solicitacao{
		SolicitanteID: &user.ID,
		AssetID:       &asset.ID,
		Motivo:        "Home office",
		Status:        models.StatusSolicitacaoAprovada,
	}
	db.Create(&sol)

	h := NewQRHandler(userRepo, authSvc, qrSvc, qrLogSvc, txRepo, maintRepo, assetRepo)

	// Case 1: Non-manager trying to bypass PIN validation (must return 403 Forbidden)
	{
		w := httptest.NewRecorder()
		c, _ := gin.CreateTestContext(w)
		c.Set(middleware.ContextUserKey, &nonManager)

		reqPayload := dto.DeliveryConfirmRequest{
			QRToken:       &token,
			BypassPIN:     true,
			SolicitacaoID: &sol.ID,
		}
		jsonBytes, _ := json.Marshal(reqPayload)
		c.Request, _ = http.NewRequest(http.MethodPost, "/api/v1/qr/delivery/confirm", bytes.NewBuffer(jsonBytes))

		h.DeliveryConfirm(c)

		if w.Code != http.StatusForbidden {
			t.Errorf("Expected 403 Forbidden for non-manager PIN bypass, got %d", w.Code)
		}
	}

	// Case 2: Manager/Admin trying to bypass PIN validation (must succeed 200 OK)
	{
		w := httptest.NewRecorder()
		c, _ := gin.CreateTestContext(w)
		c.Set(middleware.ContextUserKey, &admin)

		reqPayload := dto.DeliveryConfirmRequest{
			QRToken:       &token,
			BypassPIN:     true,
			SolicitacaoID: &sol.ID,
		}
		jsonBytes, _ := json.Marshal(reqPayload)
		c.Request, _ = http.NewRequest(http.MethodPost, "/api/v1/qr/delivery/confirm", bytes.NewBuffer(jsonBytes))

		h.DeliveryConfirm(c)

		if w.Code != http.StatusOK {
			t.Fatalf("Expected delivery confirm to succeed with 200 via admin bypass, got %d. Body: %s", w.Code, w.Body.String())
		}

		// Verify Solicitacao was updated to Entregue
		updatedSol, _ := txRepo.GetSolicitacaoByID(sol.ID)
		if updatedSol.Status != models.StatusSolicitacaoEntregue {
			t.Errorf("Expected Solicitacao status to be 'Entregue', got %v", updatedSol.Status)
		}
	}
}

func testStringPtr(s string) *string {
	return &s
}
