package handler

import (
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/assettrack/backend/internal/middleware"
	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"github.com/gin-gonic/gin"
)

type TransactionHandler struct {
	repo      *repository.TransactionRepository
	assetRepo *repository.AssetRepository
}

func NewTransactionHandler(repo *repository.TransactionRepository, assetRepo *repository.AssetRepository) *TransactionHandler {
	return &TransactionHandler{repo: repo, assetRepo: assetRepo}
}

func canProcessBorrowingReturn(role string) bool {
	switch strings.ToLower(role) {
	case models.RoleAdmin, models.RoleGerente, models.RoleGerenteInfra, models.RoleTecnico, models.RoleRH:
		return true
	default:
		return false
	}
}

func (h *TransactionHandler) ListSolicitacoes(c *gin.Context) {
	skip, _ := strconv.Atoi(c.DefaultQuery("skip", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))

	sols, err := h.repo.ListSolicitacoes(skip, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, sols)
}

func (h *TransactionHandler) CreateSolicitacao(c *gin.Context) {
	user := middleware.GetCurrentUser(c)

	var payload struct {
		AssetID               uint       `json:"asset_id" binding:"required"`
		Motivo                string     `json:"motivo" binding:"required"`
		DataPrevistaDevolucao *time.Time `json:"data_prevista_devolucao"`
	}

	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}

	// Verify asset
	asset, err := h.assetRepo.GetByID(payload.AssetID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"detail": "Ativo não encontrado"})
		return
	}

	if asset.Bloqueado {
		c.JSON(http.StatusBadRequest, gin.H{"detail": "Este ativo é fixo da empresa e não pode ser solicitado para empréstimo."})
		return
	}

	if asset.Status != models.AssetStatusDisponivel {
		msg := "Ativo indisponível para solicitação."
		if asset.CurrentUserID != nil && *asset.CurrentUserID == user.ID {
			msg = "Você já possui este ativo (está em seu uso)."
		} else if asset.Status == models.AssetStatusEmUso {
			msg = "Este ativo já está em uso por outro usuário."
		} else if asset.Status == models.AssetStatusManutencao {
			msg = "Este ativo está em manutenção."
		}
		c.JSON(http.StatusBadRequest, gin.H{"detail": msg})
		return
	}

	uid := user.ID
	sol := &models.Solicitacao{
		SolicitanteID:         &uid,
		AssetID:               &payload.AssetID,
		Motivo:                payload.Motivo,
		Status:                models.StatusSolicitacaoPendente,
		DataPrevistaDevolucao: payload.DataPrevistaDevolucao,
	}

	if err := h.repo.CreateSolicitacao(sol); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": err.Error()})
		return
	}

	created, _ := h.repo.GetSolicitacaoByID(sol.ID)
	c.JSON(http.StatusCreated, created)
}

func (h *TransactionHandler) ApproveSolicitacao(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if !isStaff(user.Role) {
		c.JSON(http.StatusForbidden, gin.H{"detail": "Permissão negada"})
		return
	}

	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	sol, err := h.repo.GetSolicitacaoByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Solicitação não encontrada"})
		return
	}

	if sol.Status != models.StatusSolicitacaoPendente {
		c.JSON(http.StatusBadRequest, gin.H{"detail": "Apenas solicitações pendentes podem ser aprovadas"})
		return
	}

	now := time.Now()
	uid := user.ID
	sol.Status = models.StatusSolicitacaoAprovada
	sol.AprovadorID = &uid
	sol.DataAprovacao = &now

	if err := h.repo.UpdateSolicitacao(sol); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": err.Error()})
		return
	}

	// NEW LOGIC: Update Asset and register Movement
	if sol.AssetID != nil {
		asset, err := h.assetRepo.GetByID(*sol.AssetID)
		if err == nil {
			asset.Status = models.AssetStatusEmUso
			asset.CurrentUserID = sol.SolicitanteID
			_ = h.assetRepo.Update(asset)

			mov := &models.Movimentacao{
				AssetID:    asset.ID,
				Tipo:       models.TipoMovimentacaoEmprestimo,
				DeUserID:   &uid,
				ParaUserID: sol.SolicitanteID,
				Observacao: stringPtr("Solicitação de empréstimo aprovada via sistema"),
			}
			_ = h.repo.CreateMovement(mov)
		}
	}

	c.JSON(http.StatusOK, sol)
}

func (h *TransactionHandler) RejectSolicitacao(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if !isStaff(user.Role) {
		c.JSON(http.StatusForbidden, gin.H{"detail": "Permissão negada"})
		return
	}

	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	sol, err := h.repo.GetSolicitacaoByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Solicitação não encontrada"})
		return
	}

	if sol.Status != models.StatusSolicitacaoPendente {
		c.JSON(http.StatusBadRequest, gin.H{"detail": "Apenas solicitações pendentes podem ser rejeitadas"})
		return
	}

	sol.Status = models.StatusSolicitacaoRejeitada

	if err := h.repo.UpdateSolicitacao(sol); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": err.Error()})
		return
	}

	c.JSON(http.StatusOK, sol)
}

func (h *TransactionHandler) DevolverAsset(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if user == nil || !canProcessBorrowingReturn(user.Role) {
		c.JSON(http.StatusForbidden, gin.H{"detail": "A devolução só pode ser confirmada por Administradores, Gerentes, Técnicos ou RH"})
		return
	}

	var payload struct {
		CondicaoEquipamento   string `json:"condicao_equipamento" binding:"required"`
		AcessoriosDevolvidos  string `json:"acessorios_devolvidos" binding:"required"`
		ObservacoesAdicionais string `json:"observacoes_adicionais"`
	}
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}
	payload.CondicaoEquipamento = strings.TrimSpace(payload.CondicaoEquipamento)
	payload.AcessoriosDevolvidos = strings.TrimSpace(payload.AcessoriosDevolvidos)
	payload.ObservacoesAdicionais = strings.TrimSpace(payload.ObservacoesAdicionais)
	if payload.CondicaoEquipamento == "" || payload.AcessoriosDevolvidos == "" {
		c.JSON(http.StatusBadRequest, gin.H{"detail": "Informe a condição do equipamento e os acessórios devolvidos"})
		return
	}

	assetID, err := strconv.ParseUint(c.Param("asset_id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID de ativo inválido"})
		return
	}

	asset, err := h.assetRepo.GetByID(uint(assetID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ativo não encontrado"})
		return
	}

	if asset.Status == models.AssetStatusManutencao {
		c.JSON(http.StatusBadRequest, gin.H{"detail": "Não é possível devolver um ativo que está em manutenção por este endpoint"})
		return
	}

	sol, err := h.repo.GetActiveSolicitacaoByAssetID(uint(assetID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"detail": "Não existe empréstimo ativo para este equipamento"})
		return
	}

	deUser := asset.CurrentUserID
	now := time.Now()
	receiverID := user.ID
	legacyObservation := []string{
		"Condição do equipamento: " + payload.CondicaoEquipamento,
		"Acessórios devolvidos: " + payload.AcessoriosDevolvidos,
	}
	if payload.ObservacoesAdicionais != "" {
		legacyObservation = append(legacyObservation, "Observações adicionais: "+payload.ObservacoesAdicionais)
	}
	legacyObservationText := strings.Join(legacyObservation, " | ")
	sol.Status = models.StatusSolicitacaoDevolvida
	sol.DataDevolucao = &now
	sol.RecebidoPorID = &receiverID
	sol.CondicaoDevolucao = &payload.CondicaoEquipamento
	sol.AcessoriosDevolvidos = &payload.AcessoriosDevolvidos
	if payload.ObservacoesAdicionais != "" {
		sol.ObservacoesDevolucao = &payload.ObservacoesAdicionais
	} else {
		sol.ObservacoesDevolucao = nil
	}
	sol.ObservacaoDevolucao = &legacyObservationText
	if err := h.repo.UpdateSolicitacao(sol); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": "Erro ao encerrar solicitação de empréstimo: " + err.Error()})
		return
	}

	// Reset ownership and location back to default storage/available
	if asset.Bloqueado {
		asset.Status = models.AssetStatusEmUso
	} else {
		asset.Status = models.AssetStatusDisponivel
	}
	asset.CurrentUserID = nil
	asset.CurrentLocalID = nil
	asset.CurrentDepartamentoID = nil

	if err := h.assetRepo.Update(asset); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": "Erro ao processar devolução do ativo: " + err.Error()})
		return
	}

	// Register Movement
	mov := &models.Movimentacao{
		AssetID:    asset.ID,
		Tipo:       models.TipoMovimentacaoDevolucao,
		DeUserID:   deUser,
		ParaUserID: &receiverID,
		Observacao: &legacyObservationText,
	}
	_ = h.repo.CreateMovement(mov)

	c.JSON(http.StatusOK, gin.H{"message": "Devolução concluída com sucesso e registrada no histórico"})
}
