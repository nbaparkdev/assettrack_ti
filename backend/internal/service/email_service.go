package service

import (
	"context"
	"crypto/tls"
	"fmt"
	"net"
	"net/mail"
	"net/smtp"
	"strings"

	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
)

type EmailService interface {
	SendEmail(ctx context.Context, to string, subject string, body string) error
	IsNotificationEnabled(ctx context.Context, key string, defaultEnabled bool) bool
}

const EmailNotificationRHStatus = "email_notification_rh_status_enabled"

const (
	EmailNotificationKanban      = "email_notification_kanban_enabled"
	EmailNotificationMaintenance = "email_notification_maintenance_enabled"
	EmailNotificationProcurement = "email_notification_procurement_enabled"
	EmailNotificationServiceDesk = "email_notification_service_desk_enabled"
)

const (
	NotificationKanbanEnabled      = "notification_kanban_enabled"
	NotificationMaintenanceEnabled = "notification_maintenance_enabled"
	NotificationProcurementEnabled = "notification_procurement_enabled"
	NotificationServiceDeskEnabled = "notification_service_desk_enabled"
)

// IsNotificationSettingEnabled centralizes persisted notification switches.
// Missing rows remain enabled so existing installations keep their behavior.
func IsNotificationSettingEnabled(ctx context.Context, settingsRepo repository.SystemSettingsRepository, key string, defaultEnabled bool) bool {
	setting, err := settingsRepo.GetSetting(ctx, key)
	if err != nil || setting == nil || strings.TrimSpace(setting.SettingValue) == "" {
		return defaultEnabled
	}
	return !strings.EqualFold(strings.TrimSpace(setting.SettingValue), "false")
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

func (s *emailService) IsNotificationEnabled(ctx context.Context, key string, defaultEnabled bool) bool {
	return IsNotificationSettingEnabled(ctx, s.settingsRepo, key, defaultEnabled)
}

func (s *emailService) SendEmail(ctx context.Context, to string, subject string, body string) error {
	// Fetch SMTP Settings
	hostSetting, _ := s.settingsRepo.GetSetting(ctx, "smtp_host")
	portSetting, _ := s.settingsRepo.GetSetting(ctx, "smtp_port")
	userSetting, _ := s.settingsRepo.GetSetting(ctx, "smtp_user")
	passSetting, _ := s.settingsRepo.GetSetting(ctx, "smtp_password")
	fromSetting, _ := s.settingsRepo.GetSetting(ctx, "smtp_from")
	securitySetting, _ := s.settingsRepo.GetSetting(ctx, "smtp_security")

	host := "smtp.gmail.com"
	if hostSetting != nil && hostSetting.SettingValue != "" {
		host = hostSetting.SettingValue
	}
	port := "587"
	if portSetting != nil && portSetting.SettingValue != "" {
		port = portSetting.SettingValue
	}
	security := defaultSMTPSecurity(port)
	if securitySetting != nil && securitySetting.SettingValue != "" {
		security = strings.ToLower(strings.TrimSpace(securitySetting.SettingValue))
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
		from = strings.TrimSpace(fromSetting.SettingValue)
	}
	// The setting accepts either a full sender address or a display name. When
	// only a name is supplied, use the authenticated mailbox for the SMTP
	// envelope and preserve the configured value as the visible sender name.
	envelopeFrom := user
	fromHeader := (&mail.Address{Address: user}).String()
	if parsed, err := mail.ParseAddress(from); err == nil && strings.Contains(parsed.Address, "@") {
		envelopeFrom = parsed.Address
		fromHeader = parsed.String()
	} else if from != "" {
		fromHeader = (&mail.Address{Name: from, Address: user}).String()
	}

	msg := []byte("From: " + fromHeader + "\r\n" +
		"To: " + to + "\r\n" +
		"Subject: " + subject + "\r\n" +
		"MIME-version: 1.0;\nContent-Type: text/html; charset=\"UTF-8\";\n\n" +
		"\r\n" +
		body + "\r\n")

	var err error
	if host != "" && user != "" && pass != "" {
		if strings.HasPrefix(strings.ToLower(strings.TrimSpace(host)), "imap.") || strings.HasPrefix(strings.ToLower(strings.TrimSpace(host)), "pop.") {
			err = fmt.Errorf("servidor %q é de recebimento; informe um servidor SMTP de saída", host)
		} else {
			err = sendSMTP(host, port, security, user, pass, envelopeFrom, to, msg)
		}
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

const (
	SMTPSecuritySSLTLS   = "ssl_tls"
	SMTPSecuritySTARTTLS = "starttls"
	SMTPSecurityNone     = "none"
)

func defaultSMTPSecurity(port string) string {
	if strings.TrimSpace(port) == "465" {
		return SMTPSecuritySSLTLS
	}
	return SMTPSecuritySTARTTLS
}

// sendSMTP supports implicit TLS, STARTTLS and unencrypted SMTP. Existing
// settings without smtp_security retain their conventional safe defaults:
// implicit TLS for port 465 and STARTTLS for every other port.
func sendSMTP(host, port, security, user, pass, from, to string, msg []byte) error {
	address := net.JoinHostPort(strings.TrimSpace(host), strings.TrimSpace(port))
	tlsConfig := &tls.Config{ServerName: strings.TrimSpace(host), MinVersion: tls.VersionTLS12}

	switch security {
	case SMTPSecuritySSLTLS:
		conn, err := tls.Dial("tcp", address, tlsConfig)
		if err != nil {
			return err
		}
		defer conn.Close()

		client, err := smtp.NewClient(conn, host)
		if err != nil {
			return err
		}
		defer client.Quit()
		return sendWithClient(client, host, security, user, pass, from, to, msg)
	case SMTPSecuritySTARTTLS, SMTPSecurityNone:
		client, err := smtp.Dial(address)
		if err != nil {
			return err
		}
		defer client.Quit()

		if security == SMTPSecuritySTARTTLS {
			if ok, _ := client.Extension("STARTTLS"); !ok {
				return fmt.Errorf("o servidor SMTP não oferece STARTTLS")
			}
			if err := client.StartTLS(tlsConfig); err != nil {
				return err
			}
		}
		return sendWithClient(client, host, security, user, pass, from, to, msg)
	default:
		return fmt.Errorf("modo de segurança SMTP inválido: %q", security)
	}
}

func sendWithClient(client *smtp.Client, host, security, user, pass, from, to string, msg []byte) error {
	if ok, _ := client.Extension("AUTH"); ok {
		var auth smtp.Auth = smtp.PlainAuth("", user, pass, host)
		if security == SMTPSecurityNone {
			// This mode is intentionally opt-in. smtp.PlainAuth refuses remote
			// unencrypted connections, while some isolated internal relays use it.
			auth = insecurePlainAuth{username: user, password: pass}
		}
		if err := client.Auth(auth); err != nil {
			return err
		}
	}
	if err := client.Mail(from); err != nil {
		return err
	}
	if err := client.Rcpt(to); err != nil {
		return err
	}
	writer, err := client.Data()
	if err != nil {
		return err
	}
	if _, err := writer.Write(msg); err != nil {
		_ = writer.Close()
		return err
	}
	return writer.Close()
}

type insecurePlainAuth struct {
	username string
	password string
}

func (a insecurePlainAuth) Start(*smtp.ServerInfo) (string, []byte, error) {
	return "PLAIN", []byte("\x00" + a.username + "\x00" + a.password), nil
}

func (a insecurePlainAuth) Next(_ []byte, _ bool) ([]byte, error) {
	return nil, nil
}
