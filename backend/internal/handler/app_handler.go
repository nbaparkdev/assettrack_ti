package handler

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"
)

type AppHandler struct{}

func NewAppHandler() *AppHandler {
	return &AppHandler{}
}

type AppVersionResponse struct {
	VersionCode       int    `json:"version_code"`
	VersionName       string `json:"version_name"`
	ReleaseDate       string `json:"release_date"`
	DownloadURL       string `json:"download_url"`
	APKSizeBytes      int64  `json:"apk_size_bytes"`
	APKSizeFormatted  string `json:"apk_size_formatted"`
	MinAndroidVersion string `json:"min_android_version"`
	ReleaseNotes      string `json:"release_notes"`
}

const (
	CurrentVersionCode = 2
	CurrentVersionName = "1.2.0"
	MinAndroidVersion  = "Android 7.0 (Nougat) ou superior"
	ReleaseNotesText   = "Novidades da Versão 1.2.0:\n• Suporte a Comunicados e Avisos do Sistema com Vídeos (YouTube/MP4) e Imagens na Dashboard.\n• Visualizador em Modal amplo para todos os usuários com suporte a reprodução multimídia.\n• Arquitetura Offline-First no Android com fila automática de sincronização ao reconectar.\n• Central de Chamados otimizada para dispositivos móveis com início rápido de atendimento.\n• Melhorias gerais de performance e estabilidade."
)

func findAPKPath() string {
	candidates := []string{
		"uploads/app-debug.apk",
		"/app/uploads/app-debug.apk",
		"uploads/AssetTrack-TI.apk",
		"/app/uploads/AssetTrack-TI.apk",
		"../app-debug.apk",
		"./app-debug.apk",
		"../frontend/android/app/build/outputs/apk/debug/app-debug.apk",
	}

	for _, p := range candidates {
		if info, err := os.Stat(p); err == nil && !info.IsDir() && info.Size() > 0 {
			return p
		}
	}
	return ""
}

func (h *AppHandler) GetAppVersion(c *gin.Context) {
	apkPath := findAPKPath()
	var sizeBytes int64 = 5872025
	sizeFormatted := "5.6 MB"
	releaseDate := time.Now().Format(time.RFC3339)

	if apkPath != "" {
		if info, err := os.Stat(apkPath); err == nil {
			sizeBytes = info.Size()
			sizeFormatted = fmt.Sprintf("%.1f MB", float64(sizeBytes)/(1024*1024))
			releaseDate = info.ModTime().Format(time.RFC3339)
		}
	}

	c.JSON(http.StatusOK, AppVersionResponse{
		VersionCode:       CurrentVersionCode,
		VersionName:       CurrentVersionName,
		ReleaseDate:       releaseDate,
		DownloadURL:       "/api/v1/app/download",
		APKSizeBytes:      sizeBytes,
		APKSizeFormatted:  sizeFormatted,
		MinAndroidVersion: MinAndroidVersion,
		ReleaseNotes:      ReleaseNotesText,
	})
}

func (h *AppHandler) DownloadAPK(c *gin.Context) {
	apkPath := findAPKPath()
	if apkPath == "" {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "Arquivo APK não encontrado no servidor. Por favor, solicite a compilação ao administrador.",
		})
		return
	}

	cleanPath := filepath.Clean(apkPath)
	c.Header("Content-Description", "File Transfer")
	c.Header("Content-Transfer-Encoding", "binary")
	c.Header("Content-Disposition", "attachment; filename=\"AssetTrack-TI-v1.2.0.apk\"")
	c.Header("Content-Type", "application/vnd.android.package-archive")
	c.File(cleanPath)
}
