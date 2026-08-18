package service

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"net/http"
	"strings"

	"github.com/assettrack/backend/internal/repository"
)

type AIService interface {
	Chat(ctx context.Context, messages []map[string]interface{}) (string, error)
}

type aiService struct {
	settingsRepo repository.SystemSettingsRepository
}

func NewAIService(settingsRepo repository.SystemSettingsRepository) AIService {
	return &aiService{
		settingsRepo: settingsRepo,
	}
}

func (s *aiService) Chat(ctx context.Context, messages []map[string]interface{}) (string, error) {
	// Check if AI is enabled
	enabledSetting, _ := s.settingsRepo.GetSetting(ctx, "ai_enabled")
	if enabledSetting == nil || strings.ToLower(enabledSetting.SettingValue) != "true" {
		return "", errors.New("Assistente IA está desativado")
	}

	providerSetting, _ := s.settingsRepo.GetSetting(ctx, "ai_provider")
	provider := "openai"
	if providerSetting != nil && providerSetting.SettingValue != "" {
		provider = providerSetting.SettingValue
	}

	apiKeySetting, _ := s.settingsRepo.GetSetting(ctx, provider+"_api_key")
	apiKey := ""
	if apiKeySetting != nil {
		apiKey = apiKeySetting.SettingValue
	}

	modelSetting, _ := s.settingsRepo.GetSetting(ctx, provider+"_model")
	model := ""
	if modelSetting != nil {
		model = modelSetting.SettingValue
	}

	if provider == "ollama" {
		baseUrlSetting, _ := s.settingsRepo.GetSetting(ctx, "ollama_base_url")
		baseUrl := "http://localhost:11434"
		if baseUrlSetting != nil && baseUrlSetting.SettingValue != "" {
			baseUrl = baseUrlSetting.SettingValue
		}
		if model == "" {
			model = "llama3"
		}
		return s.chatOllama(ctx, baseUrl, model, messages)
	} else if provider == "gemini" {
		if apiKey == "" {
			return "", errors.New("API Key not configured for Gemini")
		}
		if model == "" {
			model = "gemini-1.5-flash"
		}
		return s.chatGemini(ctx, apiKey, model, messages)
	} else { // default to openai
		if apiKey == "" {
			return "", errors.New("API Key not configured for OpenAI")
		}
		if model == "" {
			model = "gpt-4o-mini"
		}
		return s.chatOpenAI(ctx, apiKey, model, messages)
	}
}

func (s *aiService) chatOpenAI(ctx context.Context, apiKey string, model string, messages []map[string]interface{}) (string, error) {
	url := "https://api.openai.com/v1/chat/completions"
	payload := map[string]interface{}{
		"model":    model,
		"messages": messages,
	}

	body, _ := json.Marshal(payload)
	req, _ := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(body))
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := ioutil.ReadAll(resp.Body)
		return "", fmt.Errorf("OpenAI API error: %s", string(bodyBytes))
	}

	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)

	choices, ok := result["choices"].([]interface{})
	if ok && len(choices) > 0 {
		choice := choices[0].(map[string]interface{})
		message := choice["message"].(map[string]interface{})
		return message["content"].(string), nil
	}

	return "", errors.New("Failed to parse OpenAI response")
}

func (s *aiService) chatGemini(ctx context.Context, apiKey string, model string, messages []map[string]interface{}) (string, error) {
	// Simple mapping from OpenAI format to Gemini format
	url := fmt.Sprintf("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s", model, apiKey)
	
	var geminiContents []map[string]interface{}
	for _, m := range messages {
		role := m["role"].(string)
		content := m["content"].(string)
		gRole := "user"
		if role == "assistant" {
			gRole = "model"
		} else if role == "system" {
			// Gemini handles system differently, but for simplicity we append it to the first user message or keep it as user
			gRole = "user" 
		}

		geminiContents = append(geminiContents, map[string]interface{}{
			"role": gRole,
			"parts": []map[string]interface{}{
				{"text": content},
			},
		})
	}

	payload := map[string]interface{}{
		"contents": geminiContents,
	}

	body, _ := json.Marshal(payload)
	req, _ := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := ioutil.ReadAll(resp.Body)
		return "", fmt.Errorf("Gemini API error: %s", string(bodyBytes))
	}

	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)

	candidates, ok := result["candidates"].([]interface{})
	if ok && len(candidates) > 0 {
		candidate := candidates[0].(map[string]interface{})
		content := candidate["content"].(map[string]interface{})
		parts := content["parts"].([]interface{})
		if len(parts) > 0 {
			part := parts[0].(map[string]interface{})
			return part["text"].(string), nil
		}
	}

	return "", errors.New("Failed to parse Gemini response")
}

func (s *aiService) chatOllama(ctx context.Context, baseUrl string, model string, messages []map[string]interface{}) (string, error) {
	url := strings.TrimRight(baseUrl, "/") + "/api/chat"
	payload := map[string]interface{}{
		"model":    model,
		"messages": messages,
		"stream":   false,
	}

	body, _ := json.Marshal(payload)
	req, _ := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := ioutil.ReadAll(resp.Body)
		return "", fmt.Errorf("Ollama API error: %s", string(bodyBytes))
	}

	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)

	message, ok := result["message"].(map[string]interface{})
	if ok {
		return message["content"].(string), nil
	}

	return "", errors.New("Failed to parse Ollama response")
}
