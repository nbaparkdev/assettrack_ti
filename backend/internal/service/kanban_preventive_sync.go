package service

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

// SyncPreventiveOrderToKanban mirrors the operational state of one preventive
// order into every enabled Kanban project linked to its plan. It is deliberately
// called from the OS workflow so field technicians never need to open Kanban.
func SyncPreventiveOrderToKanban(db *gorm.DB, orderID, actorID uint) error {
	var order models.MaintenanceOrder
	if err := db.Preload("Plan").Preload("Asset").Preload("Tecnico").
		Preload("Checklists.Items").Preload("Executions").Preload("History").First(&order, orderID).Error; err != nil {
		return err
	}

	var projects []models.KanbanProject
	query := db.Preload("Colunas").Where("related_to_preventive = ? AND preventive_automation_enabled = ?", true, true)
	if order.PlanID != nil {
		query = query.Where("preventive_plan_id IS NULL OR preventive_plan_id = ?", *order.PlanID)
	}
	if err := query.Find(&projects).Error; err != nil {
		return err
	}

	checklistJSON := maintenanceChecklistAsKanbanJSON(order)
	for index := range projects {
		project := &projects[index]
		if err := ensurePreventiveColumns(db, project); err != nil {
			return err
		}
		column := preventiveStatusColumn(project, order.Status)
		if column == nil {
			continue
		}

		var card models.KanbanCard
		err := db.Where("project_id = ? AND preventive_order_id = ?", project.ID, order.ID).First(&card).Error
		if err == nil {
			description := preventiveCardDescription(order)
			if err := db.Model(&models.KanbanCard{}).Where("id = ?", card.ID).Update("column_id", column.ID).Error; err != nil {
				return err
			}
			if err := db.Model(&models.KanbanCard{}).Where("id = ?", card.ID).Updates(map[string]interface{}{
				"descricao": description, "checklist_json": checklistJSON, "responsavel_id": order.TecnicoID, "data_entrega": order.DataAgendada,
			}).Error; err != nil {
				return err
			}
			continue
		}
		if err != gorm.ErrRecordNotFound {
			return err
		}

		// New cycles remain visible above history in the same status column.
		if err := db.Model(&models.KanbanCard{}).Where("project_id = ? AND column_id = ?", project.ID, column.ID).UpdateColumn("ordem", gorm.Expr("ordem + 1")).Error; err != nil {
			return err
		}
		description := preventiveCardDescription(order)
		card = models.KanbanCard{
			ProjectID: project.ID, ColumnID: column.ID, Ordem: 0,
			Titulo:            fmt.Sprintf("Preventiva %s - %s", order.Numero, preventiveTarget(order)),
			Descricao:         &description,
			ChecklistJSON:     checklistJSON,
			PreventiveOrderID: &order.ID,
			CriadorID:         actorID,
			ResponsavelID:     order.TecnicoID,
			Prioridade:        preventiveCardPriority(order.Prioridade),
			Cor:               "#06B6D4",
			DataEntrega:       order.DataAgendada,
		}
		if err := db.Create(&card).Error; err != nil {
			return err
		}
		if order.AssetID != nil {
			_ = db.Model(&card).Association("Ativos").Replace([]models.Asset{{ID: *order.AssetID}})
		}
		if order.TecnicoID != nil {
			_ = db.Model(&card).Association("Participantes").Replace([]models.User{{ID: *order.TecnicoID}})
		}
	}
	return nil
}

type syncChecklistItem struct {
	ID        string `json:"id"`
	Titulo    string `json:"titulo"`
	Concluido bool   `json:"concluido"`
}

func maintenanceChecklistAsKanbanJSON(order models.MaintenanceOrder) *string {
	executed := make(map[uint]bool, len(order.Executions))
	for _, execution := range order.Executions {
		executed[execution.ChecklistItemID] = execution.Concluido
	}
	items := make([]syncChecklistItem, 0)
	for _, checklist := range order.Checklists {
		for _, item := range checklist.Items {
			items = append(items, syncChecklistItem{ID: fmt.Sprintf("pm-%d", item.ID), Titulo: item.Descricao, Concluido: executed[item.ID]})
		}
	}
	if len(items) == 0 {
		return nil
	}
	payload, err := json.Marshal(items)
	if err != nil {
		return nil
	}
	value := string(payload)
	return &value
}

func ensurePreventiveColumns(db *gorm.DB, project *models.KanbanProject) error {
	definitions := []struct{ name, color string }{
		{"A Fazer", "#6B7280"}, {"Em Andamento", "#2563EB"}, {"Aguardando Peça", "#F59E0B"}, {"Pausada", "#8B5CF6"}, {"Concluído", "#16A34A"},
	}
	for _, definition := range definitions {
		found := false
		for _, column := range project.Colunas {
			name := strings.ToLower(column.Nome)
			if name == strings.ToLower(definition.name) ||
				(definition.name == "Aguardando Peça" && strings.Contains(name, "aguardando") && strings.Contains(name, "compr")) ||
				(definition.name == "Concluído" && strings.Contains(name, "conclu")) {
				found = true
			}
		}
		if !found {
			column := models.KanbanColumn{ProjectID: project.ID, Nome: definition.name, Cor: definition.color, Ordem: len(project.Colunas)}
			if err := db.Create(&column).Error; err != nil {
				return err
			}
			project.Colunas = append(project.Colunas, column)
		}
	}
	return nil
}

func preventiveStatusColumn(project *models.KanbanProject, status string) *models.KanbanColumn {
	needle := "a fazer"
	switch strings.ToLower(status) {
	case strings.ToLower(models.PMStatusEmAndamento):
		needle = "andamento"
	case strings.ToLower(models.PMStatusAguardandoPeca):
		needle = "aguardando"
	case strings.ToLower(models.PMStatusPausada):
		needle = "pausad"
	case strings.ToLower(models.PMStatusConcluida):
		needle = "conclu"
	}
	for index := range project.Colunas {
		name := strings.ToLower(project.Colunas[index].Nome)
		if strings.Contains(name, needle) || (needle == "aguardando" && strings.Contains(name, "compr")) {
			return &project.Colunas[index]
		}
	}
	return nil
}

func preventiveTarget(order models.MaintenanceOrder) string {
	if order.Asset != nil {
		return order.Asset.Nome
	}
	if order.InfraPredialServico != nil && strings.TrimSpace(*order.InfraPredialServico) != "" {
		return strings.TrimSpace(*order.InfraPredialServico)
	}
	return "Infraestrutura"
}

func preventiveCardDescription(order models.MaintenanceOrder) string {
	date := "Sem data"
	if order.DataAgendada != nil {
		date = order.DataAgendada.Format("02/01/2006")
	}
	description := fmt.Sprintf("OS %s programada para %s.\n\nStatus: %s\nTipo: %s\nAtivo/Serviço: %s", order.Numero, date, order.Status, order.Tipo, preventiveTarget(order))
	if order.Status == models.PMStatusPausada {
		if reason := latestPauseReason(order); reason != "" {
			description += fmt.Sprintf("\n\nMotivo da pausa (técnico): %s", reason)
		}
	}
	if order.Status == models.PMStatusConcluida {
		description += "\n\n--- RESUMO DA CONCLUSÃO ---"
		description += fmt.Sprintf("\nConcluída em: %s", conclusionDate(order))
		description += fmt.Sprintf("\nDiagnóstico: %s", optionalText(order.Diagnostico, "Não informado"))
		description += fmt.Sprintf("\nSolução aplicada: %s", optionalText(order.Solucao, "Não informada"))
		description += fmt.Sprintf("\nRecomendações: %s", optionalText(order.Recomendacoes, "Sem recomendações adicionais"))
		description += fmt.Sprintf("\nDestino do ativo: %s", optionalText(order.StatusPosManutencao, "Não informado"))
		if order.TempoTotalMinutos != nil {
			description += fmt.Sprintf("\nTempo total: %dh %02dmin", *order.TempoTotalMinutos/60, *order.TempoTotalMinutos%60)
		}
		if order.CustoTotal != nil {
			description += fmt.Sprintf("\nCusto total: R$ %.2f", *order.CustoTotal)
		}
	}
	return description
}

func optionalText(value *string, fallback string) string {
	if value == nil || strings.TrimSpace(*value) == "" {
		return fallback
	}
	return strings.TrimSpace(*value)
}

func conclusionDate(order models.MaintenanceOrder) string {
	if order.DataConclusao == nil {
		return "Não registrada"
	}
	return order.DataConclusao.Format("02/01/2006 15:04")
}

func latestPauseReason(order models.MaintenanceOrder) string {
	var latest *models.MaintenanceHistory
	for index := range order.History {
		history := &order.History[index]
		if history.Acao != "Ordem Pausada" || !strings.Contains(history.Descricao, "Motivo:") {
			continue
		}
		if latest == nil || history.DataHora.After(latest.DataHora) {
			latest = history
		}
	}
	if latest == nil {
		return ""
	}
	parts := strings.SplitN(latest.Descricao, "Motivo:", 2)
	if len(parts) != 2 {
		return ""
	}
	return strings.TrimSpace(parts[1])
}

func preventiveCardPriority(priority string) string {
	switch strings.ToLower(strings.TrimSpace(priority)) {
	case "baixa":
		return models.CardPriorityBaixa
	case "alta":
		return models.CardPriorityAlta
	case "urgente", "crítica", "critica":
		return models.CardPriorityUrgente
	default:
		return models.CardPriorityMedia
	}
}
