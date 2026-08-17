package handler

import (
	"archive/zip"
	"bytes"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/assettrack/backend/internal/config"
	"github.com/gin-gonic/gin"
)

type BackupHandler struct {
	cfg *config.Config
}

func NewBackupHandler(cfg *config.Config) *BackupHandler {
	// Ensure backups dir exists
	os.MkdirAll("backups", os.ModePerm)
	return &BackupHandler{cfg: cfg}
}

// Struct for status response
type BackupJobStatus struct {
	IsRunning bool   `json:"is_running"`
	Progress  string `json:"progress"`
	Error     string `json:"error,omitempty"`
}

var (
	backupMutex   sync.Mutex
	backupRunning bool
	backupMsg     string
)

func setStatus(running bool, msg string) {
	backupMutex.Lock()
	defer backupMutex.Unlock()
	backupRunning = running
	backupMsg = msg
}

func getStatus() (bool, string) {
	backupMutex.Lock()
	defer backupMutex.Unlock()
	return backupRunning, backupMsg
}

// GenerateBackup triggers an async pg_dump + zip
func (h *BackupHandler) GenerateBackup(c *gin.Context) {
	running, _ := getStatus()
	if running {
		c.JSON(http.StatusConflict, gin.H{"error": "Um backup já está em andamento."})
		return
	}

	setStatus(true, "Iniciando geração de backup...")

	go func() {
		defer setStatus(false, "Concluído")

		timestamp := time.Now().Format("20060102_150405")
		zipFileName := fmt.Sprintf("backups/backup_assettrack_%s.zip", timestamp)

		// Create zip file
		zipFile, err := os.Create(zipFileName)
		if err != nil {
			setStatus(false, "Erro ao criar arquivo ZIP: "+err.Error())
			return
		}
		defer zipFile.Close()

		zipWriter := zip.NewWriter(zipFile)
		defer zipWriter.Close()

		setStatus(true, "Gerando dump do banco de dados (pg_dump)...")
		
		// Run pg_dump
		// Note: Requires postgresql-client to be installed in the server/docker environment
		cmd := exec.Command("pg_dump", "--clean", "--if-exists", "--no-owner", "--no-privileges", "--inserts", h.cfg.DatabaseURL)
		
		var out bytes.Buffer
		var stderr bytes.Buffer
		cmd.Stdout = &out
		cmd.Stderr = &stderr
		
		if err := cmd.Run(); err != nil {
			setStatus(false, "Erro no pg_dump: "+err.Error()+"\nDetails: "+stderr.String())
			os.Remove(zipFileName)
			return
		}

		// Add database.sql to zip
		setStatus(true, "Adicionando dump ao ZIP...")
		dbWriter, err := zipWriter.Create("database.sql")
		if err != nil {
			setStatus(false, "Erro ao adicionar SQL no ZIP: "+err.Error())
			return
		}
		dbWriter.Write(out.Bytes())

		// Zip uploads folder
		setStatus(true, "Comprimindo arquivos de mídia (uploads/)...")
		err = filepath.Walk("uploads", func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return nil // skip errors if folder missing
			}
			if info.IsDir() {
				return nil
			}

			// Add file to zip
			relPath := strings.Replace(path, "\\", "/", -1)
			fileWriter, err := zipWriter.Create(relPath)
			if err != nil {
				return err
			}

			srcFile, err := os.Open(path)
			if err != nil {
				return err
			}
			defer srcFile.Close()

			_, err = io.Copy(fileWriter, srcFile)
			return err
		})

		if err != nil {
			fmt.Printf("[BACKUP] Aviso: Falha ao incluir alguns arquivos de upload: %v\n", err)
		}

		setStatus(false, "Backup concluído com sucesso!")
	}()

	c.JSON(http.StatusAccepted, gin.H{"message": "Geração de backup iniciada em background."})
}

// GetStatus returns the current backup generation status
func (h *BackupHandler) GetStatus(c *gin.Context) {
	running, msg := getStatus()
	c.JSON(http.StatusOK, BackupJobStatus{
		IsRunning: running,
		Progress:  msg,
	})
}

type BackupFile struct {
	Filename string `json:"filename"`
	Size     int64  `json:"size"`
	Date     string `json:"date"`
}

// List available backups
func (h *BackupHandler) List(c *gin.Context) {
	var files []BackupFile
	
	entries, err := os.ReadDir("backups")
	if err != nil {
		c.JSON(http.StatusOK, []BackupFile{}) // return empty if folder missing
		return
	}

	for _, e := range entries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".zip") {
			info, err := e.Info()
			if err == nil {
				files = append(files, BackupFile{
					Filename: e.Name(),
					Size:     info.Size(),
					Date:     info.ModTime().Format(time.RFC3339),
				})
			}
		}
	}

	// Sort newest first
	sort.Slice(files, func(i, j int) bool {
		return files[i].Date > files[j].Date
	})

	c.JSON(http.StatusOK, files)
}

// Download stream
func (h *BackupHandler) Download(c *gin.Context) {
	filename := c.Param("filename")
	if strings.Contains(filename, "/") || strings.Contains(filename, "\\") {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Filename inválido"})
		return
	}

	path := filepath.Join("backups", filename)
	if _, err := os.Stat(path); os.IsNotExist(err) {
		c.JSON(http.StatusNotFound, gin.H{"error": "Arquivo não encontrado"})
		return
	}

	c.Header("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s\"", filename))
	c.Header("Content-Type", "application/zip")
	c.File(path)
}

// Delete backup
func (h *BackupHandler) Delete(c *gin.Context) {
	filename := c.Param("filename")
	if strings.Contains(filename, "/") || strings.Contains(filename, "\\") {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Filename inválido"})
		return
	}

	path := filepath.Join("backups", filename)
	if err := os.Remove(path); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao excluir arquivo"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Excluído com sucesso"})
}

// Restore receives a .zip and restores DB and uploads
func (h *BackupHandler) Restore(c *gin.Context) {
	fileHeader, err := c.FormFile("backup_file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Arquivo não fornecido"})
		return
	}

	if !strings.HasSuffix(fileHeader.Filename, ".zip") {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Envie um arquivo .zip válido"})
		return
	}

	// Save zip temporarily
	tmpPath := filepath.Join("backups", "restore_tmp.zip")
	if err := c.SaveUploadedFile(fileHeader, tmpPath); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao salvar arquivo temporário"})
		return
	}
	defer os.Remove(tmpPath)

	// Unzip and restore
	zipReader, err := zip.OpenReader(tmpPath)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao ler arquivo ZIP"})
		return
	}
	defer zipReader.Close()

	// Locate database.sql and run psql
	hasDB := false
	for _, f := range zipReader.File {
		if f.Name == "database.sql" {
			hasDB = true
			
			// Extract to temp file
			tmpSqlPath := filepath.Join("backups", "restore_db.sql")
			dst, err := os.Create(tmpSqlPath)
			if err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro IO sql"})
				return
			}
			src, _ := f.Open()
			io.Copy(dst, src)
			src.Close()
			dst.Close()

			// Run psql to restore
			// Note: Requires psql client installed
			cmd := exec.Command("psql", h.cfg.DatabaseURL, "-f", tmpSqlPath)
			var stderr bytes.Buffer
			cmd.Stderr = &stderr
			if err := cmd.Run(); err != nil {
				os.Remove(tmpSqlPath)
				c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao restaurar banco (psql): " + stderr.String()})
				return
			}
			os.Remove(tmpSqlPath)
		} else if strings.HasPrefix(f.Name, "uploads/") {
			// Extract uploads files
			targetPath := filepath.Join(".", f.Name) // already contains "uploads/" prefix
			if strings.Contains(targetPath, "..") { continue } // Prevent traversal
			
			if f.FileInfo().IsDir() {
				os.MkdirAll(targetPath, os.ModePerm)
				continue
			}
			
			os.MkdirAll(filepath.Dir(targetPath), os.ModePerm)
			dst, err := os.Create(targetPath)
			if err == nil {
				src, _ := f.Open()
				io.Copy(dst, src)
				src.Close()
				dst.Close()
			}
		}
	}

	if !hasDB {
		c.JSON(http.StatusBadRequest, gin.H{"error": "O arquivo ZIP não contém database.sql"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Sistema restaurado com sucesso! Recomendamos reiniciar os serviços."})
}
