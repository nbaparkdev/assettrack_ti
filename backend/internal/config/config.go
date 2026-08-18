package config

import (
	"os"
	"strconv"
	"time"
)

type Config struct {
	// Server
	Port    string
	GinMode string

	// Database
	DatabaseURL string

	// Redis
	RedisURL string

	// JWT
	SecretKey            string
	Algorithm            string
	AccessTokenExpireMin time.Duration

	// App
	ProjectName string
	Timezone    string
}

func Load() *Config {
	return &Config{
		Port:    getEnv("PORT", "8080"),
		GinMode: getEnv("GIN_MODE", "debug"),

		DatabaseURL: getEnv("DATABASE_URL", "postgres://user:password@localhost:5456/assettrack?sslmode=disable"),
		RedisURL:    getEnv("REDIS_URL", "redis://localhost:6380/0"),

		SecretKey:            getEnv("SECRET_KEY", "change_this_to_a_secure_random_string"),
		Algorithm:            getEnv("ALGORITHM", "HS256"),
		AccessTokenExpireMin: time.Duration(getEnvInt("ACCESS_TOKEN_EXPIRE_MINUTES", 480)) * time.Minute,

		ProjectName: getEnv("PROJECT_NAME", "AssetTrack TI"),
		Timezone:    getEnv("TZ", "America/Sao_Paulo"),
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if i, err := strconv.Atoi(v); err == nil {
			return i
		}
	}
	return fallback
}
