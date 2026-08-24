package handler

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

type AppHandler struct{}

func NewAppHandler() *AppHandler {
	return &AppHandler{}
}

type AppPublishStatus struct {
	IsRunning bool   `json:"is_running"`
	Progress  string `json:"progress"`
	Error     string `json:"error,omitempty"`
}

type AppVersionResponse struct {
	VersionCode       int    `json:"version_code"`
	VersionName       string `json:"version_name"`
	ReleaseDate       string `json:"release_date"`
	DownloadURL       string `json:"download_url"`
	APKFilename       string `json:"apk_filename"`
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

const releaseManifestFilename = "mobile-release.json"

var (
	appPublishMutex   sync.Mutex
	appPublishRunning bool
	appPublishMsg     string
	appPublishErr     string
)

type MobileReleaseManifest struct {
	VersionCode       int    `json:"version_code"`
	VersionName       string `json:"version_name"`
	ReleaseDate       string `json:"release_date"`
	APKFilename       string `json:"apk_filename"`
	APKSizeBytes      int64  `json:"apk_size_bytes"`
	APKSizeFormatted  string `json:"apk_size_formatted"`
	MinAndroidVersion string `json:"min_android_version"`
	ReleaseNotes      string `json:"release_notes"`
}

func locateUploadsDir() string {
	candidates := []string{
		"uploads",
		"/app/uploads",
		"../backend/uploads",
	}

	for _, p := range candidates {
		if info, err := os.Stat(p); err == nil && info.IsDir() {
			return p
		}
	}

	return ""
}

func loadReleaseManifest() (*MobileReleaseManifest, string) {
	uploadsDir := locateUploadsDir()
	if uploadsDir == "" {
		return nil, ""
	}

	manifestPath := filepath.Join(uploadsDir, releaseManifestFilename)
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return nil, uploadsDir
	}

	var manifest MobileReleaseManifest
	if err := json.Unmarshal(data, &manifest); err != nil {
		return nil, uploadsDir
	}

	return &manifest, uploadsDir
}

func setPublishStatus(running bool, msg string, errMsg string) {
	appPublishMutex.Lock()
	defer appPublishMutex.Unlock()
	appPublishRunning = running
	appPublishMsg = msg
	appPublishErr = errMsg
}

func getPublishStatus() (bool, string, string) {
	appPublishMutex.Lock()
	defer appPublishMutex.Unlock()
	return appPublishRunning, appPublishMsg, appPublishErr
}

func findPublishScript() string {
	candidates := []string{
		"/workspace/scripts/publish_mobile_apk.sh",
		"../scripts/publish_mobile_apk.sh",
		"scripts/publish_mobile_apk.sh",
	}
	for _, p := range candidates {
		if info, err := os.Stat(p); err == nil && !info.IsDir() {
			return p
		}
	}
	return ""
}

func findAPKPath() string {
	manifest, uploadsDir := loadReleaseManifest()
	if manifest != nil && manifest.APKFilename != "" && uploadsDir != "" {
		candidate := filepath.Join(uploadsDir, filepath.Base(manifest.APKFilename))
		if info, err := os.Stat(candidate); err == nil && !info.IsDir() && info.Size() > 0 {
			return candidate
		}
	}

	if uploadsDir != "" {
		entries, err := os.ReadDir(uploadsDir)
		if err == nil {
			var newestPath string
			var newestModTime time.Time
			for _, entry := range entries {
				if entry.IsDir() || !strings.HasSuffix(strings.ToLower(entry.Name()), ".apk") {
					continue
				}

				info, err := entry.Info()
				if err != nil || info.Size() <= 0 {
					continue
				}

				if info.ModTime().After(newestModTime) {
					newestModTime = info.ModTime()
					newestPath = filepath.Join(uploadsDir, entry.Name())
				}
			}

			if newestPath != "" {
				return newestPath
			}
		}
	}

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
	manifest, _ := loadReleaseManifest()

	versionCode := CurrentVersionCode
	versionName := CurrentVersionName
	releaseDate := time.Now().Format(time.RFC3339)
	apkFilename := "AssetTrack-TI.apk"
	sizeBytes := int64(5872025)
	sizeFormatted := "5.6 MB"
	minAndroidVersion := MinAndroidVersion
	releaseNotes := ReleaseNotesText

	if manifest != nil {
		if manifest.VersionCode > 0 {
			versionCode = manifest.VersionCode
		}
		if manifest.VersionName != "" {
			versionName = manifest.VersionName
		}
		if manifest.ReleaseDate != "" {
			releaseDate = manifest.ReleaseDate
		}
		if manifest.APKFilename != "" {
			apkFilename = filepath.Base(manifest.APKFilename)
		}
		if manifest.APKSizeBytes > 0 {
			sizeBytes = manifest.APKSizeBytes
		}
		if manifest.APKSizeFormatted != "" {
			sizeFormatted = manifest.APKSizeFormatted
		}
		if manifest.MinAndroidVersion != "" {
			minAndroidVersion = manifest.MinAndroidVersion
		}
		if manifest.ReleaseNotes != "" {
			releaseNotes = manifest.ReleaseNotes
		}
	}

	if apkPath != "" {
		if info, err := os.Stat(apkPath); err == nil {
			if manifest == nil || manifest.APKSizeBytes <= 0 {
				sizeBytes = info.Size()
				sizeFormatted = fmt.Sprintf("%.1f MB", float64(sizeBytes)/(1024*1024))
			}
			if manifest == nil || manifest.ReleaseDate == "" {
				releaseDate = info.ModTime().Format(time.RFC3339)
			}
			if manifest == nil || manifest.APKFilename == "" {
				apkFilename = filepath.Base(apkPath)
			}
		}
	}

	c.JSON(http.StatusOK, AppVersionResponse{
		VersionCode:       versionCode,
		VersionName:       versionName,
		ReleaseDate:       releaseDate,
		DownloadURL:       "/api/v1/app/download",
		APKFilename:       apkFilename,
		APKSizeBytes:      sizeBytes,
		APKSizeFormatted:  sizeFormatted,
		MinAndroidVersion: minAndroidVersion,
		ReleaseNotes:      releaseNotes,
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
	filename := filepath.Base(cleanPath)
	if filename == "." || filename == string(filepath.Separator) || filename == "" {
		filename = "AssetTrack-TI.apk"
	}
	c.Header("Content-Description", "File Transfer")
	c.Header("Content-Transfer-Encoding", "binary")
	c.Header("Content-Disposition", fmt.Sprintf("attachment; filename=%q", filename))
	c.Header("Content-Type", "application/vnd.android.package-archive")
	c.File(cleanPath)
}

func (h *AppHandler) PublishMobileAPK(c *gin.Context) {
	running, _, _ := getPublishStatus()
	if running {
		c.JSON(http.StatusConflict, gin.H{"error": "Uma publicação de APK já está em andamento."})
		return
	}

	scriptPath := findPublishScript()
	if scriptPath == "" {
		c.JSON(http.StatusNotFound, gin.H{"error": "Script de publicação do APK não encontrado no servidor."})
		return
	}

	setPublishStatus(true, "Iniciando publicação do APK...", "")

	go func() {
		defer func() {
			running, msg, errMsg := getPublishStatus()
			if running {
				setPublishStatus(false, msg, errMsg)
			}
		}()

		ctx, cancel := context.WithTimeout(context.Background(), 90*time.Minute)
		defer cancel()

		cmd := exec.CommandContext(ctx, "bash", scriptPath)
		cmd.Dir = filepath.Dir(filepath.Dir(scriptPath))

		var stdout bytes.Buffer
		var stderr bytes.Buffer
		cmd.Stdout = &stdout
		cmd.Stderr = &stderr

		setPublishStatus(true, "Sincronizando frontend e gerando APK...", "")
		if err := cmd.Run(); err != nil {
			errMsg := strings.TrimSpace(stderr.String())
			if errMsg == "" {
				errMsg = err.Error()
			} else {
				errMsg = errMsg + "\n" + err.Error()
			}
			if stdout.Len() > 0 {
				errMsg = errMsg + "\n" + strings.TrimSpace(stdout.String())
			}
			setPublishStatus(false, "Falha na publicação do APK.", errMsg)
			return
		}

		setPublishStatus(false, "APK publicada com sucesso!", "")
	}()

	c.JSON(http.StatusAccepted, gin.H{"message": "Publicação do APK iniciada em background."})
}

func (h *AppHandler) GetPublishStatus(c *gin.Context) {
	running, progress, errMsg := getPublishStatus()
	c.JSON(http.StatusOK, AppPublishStatus{
		IsRunning: running,
		Progress:  progress,
		Error:     errMsg,
	})
}
