package main

import (
	"fmt"
	"log"

	"github.com/assettrack/backend/internal/config"
	"github.com/assettrack/backend/internal/database"
	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/router"
	"github.com/joho/godotenv"
	"golang.org/x/crypto/bcrypt"
)

func main() {
	// Load .env (ignore error if not present — env vars may come from Docker)
	_ = godotenv.Load()

	cfg := config.Load()

	// Connect databases
	db := database.ConnectPostgres(cfg.DatabaseURL)
	rdb := database.ConnectRedis(cfg.RedisURL)

	// Auto-migrate (safe: doesn't drop columns or tables)
	log.Println("🔄 Running auto-migration...")
	if err := db.AutoMigrate(
		&models.User{},
		&models.QRLog{},
		&models.Departamento{},
		&models.Localizacao{},
		&models.Armazenamento{},
		&models.Fornecedor{},
		&models.NotaFiscal{},
		&models.AssetCategory{},
		&models.Asset{},
		&models.ServiceCategory{},
		&models.ServiceDefinition{},
		&models.ServiceTicket{},
		&models.ServiceTicketInteraction{},
		&models.SolicitacaoManutencao{},
		&models.Manutencao{},
		&models.Movimentacao{},
		&models.Solicitacao{},
	); err != nil {
		log.Printf("⚠️ Auto-migration warning: %v", err)
	}
	log.Println("✅ Migration complete")

	// Seed Admin user
	var count int64
	db.Model(&models.User{}).Where("email = ?", "admin@example.com").Count(&count)
	if count == 0 {
		log.Println("👤 Seeding default admin user...")
		hash, err := bcrypt.GenerateFromPassword([]byte("admin"), bcrypt.DefaultCost)
		if err != nil {
			log.Fatalf("Failed to hash default admin password: %v", err)
		}
		adminMat := "AAAA001"
		adminCargo := "Super Admin"
		admin := &models.User{
			Email:          "admin@example.com",
			Nome:           "Administrador",
			HashedPassword: string(hash),
			Role:           models.RoleAdmin,
			IsActive:       true,
			Matricula:      &adminMat,
			Cargo:          &adminCargo,
		}
		if err := db.Create(admin).Error; err != nil {
			log.Printf("⚠️ Failed to seed admin user: %v", err)
		} else {
			log.Println("✅ Default admin user created (admin@example.com / admin)")
		}
	}

	// Setup router
	r := router.Setup(db, rdb, cfg)

	// Start server
	addr := fmt.Sprintf(":%s", cfg.Port)
	log.Printf("🚀 %s API starting on %s", cfg.ProjectName, addr)
	if err := r.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
