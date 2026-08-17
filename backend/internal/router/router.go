package router

import (
	"github.com/assettrack/backend/internal/config"
	"github.com/assettrack/backend/internal/handler"
	"github.com/assettrack/backend/internal/middleware"
	"github.com/assettrack/backend/internal/repository"
	"github.com/assettrack/backend/internal/service"
	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
	"gorm.io/gorm"
)

func Setup(db *gorm.DB, rdb *redis.Client, cfg *config.Config) *gin.Engine {
	if cfg.GinMode == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	r := gin.New()
	r.Use(gin.Logger())
	r.Use(gin.Recovery())
	r.Use(middleware.CORSMiddleware())
	r.Use(middleware.SecurityHeaders())
	r.Use(middleware.ProcessTime())

	// Repositories
	userRepo := repository.NewUserRepository(db)
	qrLogRepo := repository.NewQRLogRepository(db)
	categoryRepo := repository.NewAssetCategoryRepository(db)
	assetRepo := repository.NewAssetRepository(db)
	serviceDeskRepo := repository.NewServiceDeskRepository(db)
	maintRepo := repository.NewMaintenanceRepository(db)
	txRepo := repository.NewTransactionRepository(db)

	// Services
	authSvc := service.NewAuthService(userRepo, cfg)
	qrSvc := service.NewQRService()
	qrLogSvc := service.NewQRLogService(qrLogRepo)

	// Rate limiter
	rateLimiter := middleware.NewRateLimiter(rdb)

	// Handlers
	authHandler := handler.NewAuthHandler(authSvc)
	userHandler := handler.NewUserHandler(userRepo, authSvc)
	qrHandler := handler.NewQRHandler(userRepo, authSvc, qrSvc, qrLogSvc, txRepo, maintRepo, assetRepo)
	assetHandler := handler.NewAssetHandler(assetRepo, categoryRepo)
	serviceDeskHandler := handler.NewServiceDeskHandler(serviceDeskRepo)
	maintenanceHandler := handler.NewMaintenanceHandler(maintRepo, assetRepo, txRepo)
	transactionHandler := handler.NewTransactionHandler(txRepo, assetRepo)

	// Auth middleware helper
	authMW := middleware.AuthMiddleware(authSvc, userRepo)
	rActive := middleware.RequireActive()
	rAdmin := middleware.RequireAdmin()
	rManager := middleware.RequireManagerOrAbove()

	// Health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok"})
	})

	// API v1
	v1 := r.Group("/api/v1")
	{
		// Auth routes (public)
		auth := v1.Group("/auth")
		{
			auth.POST("/login", rateLimiter.Limit("login"), authHandler.Login)
			auth.POST("/register", authMW, rActive, rAdmin, authHandler.Register)
			auth.GET("/me", authMW, rActive, authHandler.Me)
		}

		// User routes (protected)
		users := v1.Group("/users", authMW, rActive)
		{
			users.GET("", rManager, userHandler.List)
			users.POST("", rAdmin, userHandler.Create)
			users.GET("/:id", userHandler.GetByID)
			users.PUT("/:id", rAdmin, userHandler.Update)
		}

		// Asset routes (protected)
		assets := v1.Group("/assets", authMW, rActive)
		{
			assets.GET("/referencias", assetHandler.GetReferences)
			assets.GET("", assetHandler.List)
			assets.POST("", rManager, assetHandler.Create)
			assets.POST("/bulk", rManager, assetHandler.BulkDuplicate)
			assets.GET("/:id", assetHandler.GetByID)
			assets.PUT("/:id", rManager, assetHandler.Update)
			assets.DELETE("/:id", rAdmin, assetHandler.Delete)
			assets.GET("/:id/qrcode", assetHandler.GetQRCode)
			assets.POST("/scan-qr", assetHandler.ScanQRCode)
		}

		// Service Desk routes (protected)
		servicos := v1.Group("/servicos", authMW, rActive)
		{
			servicos.GET("/categorias", serviceDeskHandler.ListCategories)
			servicos.POST("/categorias", rManager, serviceDeskHandler.CreateCategory)
			servicos.GET("/definicoes", serviceDeskHandler.ListDefinitions)
			servicos.POST("/definicoes", rManager, serviceDeskHandler.CreateDefinition)
			servicos.GET("/chamados", serviceDeskHandler.ListTickets)
			servicos.POST("/chamados", serviceDeskHandler.CreateTicket)
			servicos.GET("/chamados/:id", serviceDeskHandler.GetTicketByID)
			servicos.PUT("/chamados/:id", serviceDeskHandler.UpdateTicket)
			servicos.POST("/chamados/:id/interacoes", serviceDeskHandler.CreateInteraction)
		}

		// Maintenance routes (protected)
		maint := v1.Group("/solicitacoes-manutencao", authMW, rActive)
		{
			maint.GET("", maintenanceHandler.ListRequests)
			maint.POST("", maintenanceHandler.CreateRequest)
			maint.GET("/:id", maintenanceHandler.GetRequestByID)
			maint.POST("/:id/aceitar", rManager, maintenanceHandler.AcceptRequest)
			maint.POST("/:id/rejeitar", rManager, maintenanceHandler.RejectRequest)
			maint.POST("/:id/concluir", rManager, maintenanceHandler.ConcludeRequest)
			maint.POST("/:id/confirmar-recebimento", maintenanceHandler.ConfirmReceipt)
		}

		// Borrowing requests routes (protected)
		sols := v1.Group("/solicitacoes", authMW, rActive)
		{
			sols.GET("", transactionHandler.ListSolicitacoes)
			sols.POST("", transactionHandler.CreateSolicitacao)
			sols.PUT("/:id/approve", rManager, transactionHandler.ApproveSolicitacao)
			sols.PUT("/:id/reject", rManager, transactionHandler.RejectSolicitacao)
		}

		// Movimentacoes routes (protected)
		movs := v1.Group("/movimentacoes", authMW, rActive)
		{
			movs.POST("/devolver/:asset_id", transactionHandler.DevolverAsset)
		}

		// QR routes
		qr := v1.Group("/qr")
		{
			// Public: QR login
			qr.POST("/login", rateLimiter.Limit("qr_login"), qrHandler.LoginWithQR)

			// Protected: own QR management
			qrMe := qr.Group("", authMW, rActive)
			{
				qrMe.GET("/me", qrHandler.GetMyQR)
				qrMe.POST("/me/generate", rateLimiter.Limit("qr_regenerate"), qrHandler.GenerateQRToken)
				qrMe.GET("/me/badge", qrHandler.GetMyBadge)
				qrMe.POST("/me/pin", rateLimiter.Limit("pin_setup"), qrHandler.SetPIN)

				// Admin/Manager: lookup by QR token
				qrMe.GET("/user/:token", rateLimiter.Limit("qr_public_profile"), qrHandler.GetUserByQR)

				// Delivery confirm
				qrMe.POST("/delivery/confirm", rateLimiter.Limit("delivery_confirm"), qrHandler.DeliveryConfirm)
			}
		}
	}

	return r
}
