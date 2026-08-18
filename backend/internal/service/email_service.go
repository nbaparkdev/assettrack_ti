package service

import (
	"context"
	"fmt"
	"net/smtp"

	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
)

type EmailService interface {
	SendEmail(ctx context.Context, to string, subject string, body string) error
}

type emailService struct {
	settingsRepo repository.SystemSettingsRepository
	emailLogRepo repository.EmailLogRepository
}

func NewEmailService(settingsRepo repository.SystemSettingsRepository, emailLogRepo repository.EmailLogRepository) EmailService {
	return &emailService{
		settingsRepo: settingsRepo,
		emailLogRepo: emailLogRepo,
	}
}

func (s *emailService) SendEmail(ctx context.Context, to string, subject string, body string) error {
	// Fetch SMTP Settings
	hostSetting, _ := s.settingsRepo.GetSetting(ctx, "smtp_host")
	portSetting, _ := s.settingsRepo.GetSetting(ctx, "smtp_port")
	userSetting, _ := s.settingsRepo.GetSetting(ctx, "smtp_user")
	passSetting, _ := s.settingsRepo.GetSetting(ctx, "smtp_password")
	fromSetting, _ := s.settingsRepo.GetSetting(ctx, "smtp_from")

	host := "smtp.gmail.com"
	if hostSetting != nil && hostSetting.SettingValue != "" {
		host = hostSetting.SettingValue
	}
	port := "587"
	if portSetting != nil && portSetting.SettingValue != "" {
		port = portSetting.SettingValue
	}
	user := ""
	if userSetting != nil {
		user = userSetting.SettingValue
	}
	pass := ""
	if passSetting != nil {
		pass = passSetting.SettingValue
	}
	from := user
	if fromSetting != nil && fromSetting.SettingValue != "" {
		from = fromSetting.SettingValue
	}

	auth := smtp.PlainAuth("", user, pass, host)

	msg := []byte("To: " + to + "\r\n" +
		"Subject: " + subject + "\r\n" +
		"MIME-version: 1.0;\nContent-Type: text/html; charset=\"UTF-8\";\n\n" +
		"\r\n" +
		body + "\r\n")

	// Attempt to send email
	var err error
	if host != "" && user != "" && pass != "" {
		address := host + ":" + port
		err = smtp.SendMail(address, auth, from, []string{to}, msg)
	} else {
		err = fmt.Errorf("SMTP settings not fully configured")
	}

	// Log the attempt
	status := "SUCCESS"
	var errMsg *string
	if err != nil {
		status = "FAILED"
		e := err.Error()
		errMsg = &e
	}

	logEntry := &models.EmailLog{
		Recipient:    to,
		Subject:      subject,
		Body:         body,
		Status:       status,
		ErrorMessage: errMsg,
	}
	
	// Fire and forget log creation
	go func() {
		_ = s.emailLogRepo.Create(context.Background(), logEntry)
	}()

	return err
}
