package service

import (
	"encoding/base64"

	qrcode "github.com/skip2/go-qrcode"
)

type QRService struct{}

func NewQRService() *QRService { return &QRService{} }

// GenerateQRBase64 generates a QR code image and returns it as base64 string
// Mirrors Python's QRService.generate_qr_base64()
func (s *QRService) GenerateQRBase64(data string) (string, error) {
	png, err := qrcode.Encode(data, qrcode.Medium, 256)
	if err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(png), nil
}
