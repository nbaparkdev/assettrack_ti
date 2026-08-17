package service

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
)

type WebhookDispatcher struct {
	repo   *repository.WebhookRepository
	client *http.Client
}

func NewWebhookDispatcher(repo *repository.WebhookRepository) *WebhookDispatcher {
	return &WebhookDispatcher{
		repo: repo,
		client: &http.Client{
			Timeout: 10 * time.Second, // Timeout to avoid hanging goroutines
		},
	}
}

// DispatchEvent asynchronously sends the event payload to all matching webhooks
func (s *WebhookDispatcher) DispatchEvent(evento string, payload interface{}) {
	// Execute the entire process in a goroutine so it doesn't block the API
	go func() {
		activeWebhooks, err := s.repo.ListActive()
		if err != nil {
			fmt.Printf("[WEBHOOK][ERRO] Falha ao buscar webhooks ativos: %v\n", err)
			return
		}

		if len(activeWebhooks) == 0 {
			return
		}

		payloadBytes, err := json.Marshal(payload)
		if err != nil {
			fmt.Printf("[WEBHOOK][ERRO] Falha ao serializar payload: %v\n", err)
			return
		}
		payloadStr := string(payloadBytes)

		for _, w := range activeWebhooks {
			// Check if this webhook is subscribed to the event
			var eventosPermitidos []string
			if err := json.Unmarshal([]byte(w.EventosPermitidos), &eventosPermitidos); err != nil {
				continue
			}

			isSubscribed := false
			for _, e := range eventosPermitidos {
				if e == evento {
					isSubscribed = true
					break
				}
			}

			if !isSubscribed {
				continue
			}

			// Send to this specific webhook
			s.sendToWebhook(w, evento, payloadBytes, payloadStr)
		}
	}()
}

func (s *WebhookDispatcher) sendToWebhook(w models.Webhook, evento string, payloadBytes []byte, payloadStr string) {
	logEntry := &models.WebhookLog{
		WebhookID:      w.ID,
		Evento:         evento,
		PayloadEnviado: payloadStr,
		Sucesso:        false,
	}

	req, err := http.NewRequest("POST", w.URL, bytes.NewBuffer(payloadBytes))
	if err != nil {
		logEntry.ResponseBody = fmt.Sprintf("Erro ao criar request: %v", err)
		s.repo.CreateLog(logEntry)
		return
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-AssetTrack-Event", evento)

	// Add HMAC signature if secret key is present
	if w.SecretKey != nil && strings.TrimSpace(*w.SecretKey) != "" {
		h := hmac.New(sha256.New, []byte(*w.SecretKey))
		h.Write(payloadBytes)
		signature := hex.EncodeToString(h.Sum(nil))
		req.Header.Set("X-Hub-Signature", "sha256="+signature)
	}

	resp, err := s.client.Do(req)
	if err != nil {
		logEntry.ResponseBody = fmt.Sprintf("Erro na conexão: %v", err)
		s.repo.CreateLog(logEntry)
		return
	}
	defer resp.Body.Close()

	logEntry.ResponseCode = resp.StatusCode
	
	// Read response body (limited to avoid huge texts)
	buf := new(bytes.Buffer)
	buf.ReadFrom(resp.Body)
	respStr := buf.String()
	if len(respStr) > 2000 {
		respStr = respStr[:2000]
	}
	logEntry.ResponseBody = respStr

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		logEntry.Sucesso = true
	}

	s.repo.CreateLog(logEntry)
}

// TestWebhook sends a test event immediately (sync) and returns the result
func (s *WebhookDispatcher) TestWebhook(w models.Webhook) (bool, string) {
	testPayload := map[string]interface{}{
		"event":        "TEST_WEBHOOK",
		"message":      "Este é um disparo de teste enviado pelo AssetTrack TI em Go.",
		"timestamp":    time.Now().Format(time.RFC3339),
		"webhook_id":   w.ID,
		"webhook_nome": w.Nome,
	}

	payloadBytes, _ := json.Marshal(testPayload)
	payloadStr := string(payloadBytes)

	logEntry := &models.WebhookLog{
		WebhookID:      w.ID,
		Evento:         "TEST_WEBHOOK",
		PayloadEnviado: payloadStr,
		Sucesso:        false,
	}

	req, err := http.NewRequest("POST", w.URL, bytes.NewBuffer(payloadBytes))
	if err != nil {
		logEntry.ResponseBody = fmt.Sprintf("Erro ao criar request: %v", err)
		s.repo.CreateLog(logEntry)
		return false, logEntry.ResponseBody
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-AssetTrack-Event", "TEST_WEBHOOK")

	if w.SecretKey != nil && strings.TrimSpace(*w.SecretKey) != "" {
		h := hmac.New(sha256.New, []byte(*w.SecretKey))
		h.Write(payloadBytes)
		signature := hex.EncodeToString(h.Sum(nil))
		req.Header.Set("X-Hub-Signature", "sha256="+signature)
	}

	resp, err := s.client.Do(req)
	if err != nil {
		logEntry.ResponseBody = fmt.Sprintf("Erro na conexão: %v", err)
		s.repo.CreateLog(logEntry)
		return false, logEntry.ResponseBody
	}
	defer resp.Body.Close()

	logEntry.ResponseCode = resp.StatusCode
	
	buf := new(bytes.Buffer)
	buf.ReadFrom(resp.Body)
	respStr := buf.String()
	if len(respStr) > 2000 {
		respStr = respStr[:2000]
	}
	logEntry.ResponseBody = respStr

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		logEntry.Sucesso = true
		s.repo.CreateLog(logEntry)
		return true, fmt.Sprintf("Teste enviado com sucesso! Status HTTP: %d", resp.StatusCode)
	}

	s.repo.CreateLog(logEntry)
	return false, fmt.Sprintf("Servidor de destino respondeu com erro HTTP %d", resp.StatusCode)
}
