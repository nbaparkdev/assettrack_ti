package handler

import (
	"net/http"
	"strconv"
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

	deUser := asset.CurrentUserID

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
		Observacao: stringPtr("Devolução de ativo registrada via sistema"),
	}
	_ = h.repo.CreateMovement(mov)

	c.JSON(http.StatusOK, gin.H{"message": "Devolução concluída com sucesso"})
}
