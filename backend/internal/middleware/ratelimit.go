package middleware

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
)

// RateLimiter uses Redis for distributed rate limiting
type RateLimiter struct {
	rdb    *redis.Client
	limits map[string]rateConfig
}

type rateConfig struct {
	MaxRequests int
	Window      time.Duration
}

// NewRateLimiter creates a rate limiter with predefined limits matching Python's RATE_LIMITS
func NewRateLimiter(rdb *redis.Client) *RateLimiter {
	return &RateLimiter{
		rdb: rdb,
		limits: map[string]rateConfig{
			"login":             {MaxRequests: 5, Window: time.Minute},
			"qr_login":          {MaxRequests: 10, Window: time.Minute},
			"qr_regenerate":     {MaxRequests: 3, Window: time.Hour},
			"pin_setup":         {MaxRequests: 5, Window: time.Hour},
			"qr_public_profile": {MaxRequests: 30, Window: time.Minute},
			"delivery_confirm":  {MaxRequests: 20, Window: time.Minute},
			"default":           {MaxRequests: 60, Window: time.Minute},
		},
	}
}

// Limit returns a Gin middleware for the given endpoint type
func (rl *RateLimiter) Limit(endpointType string) gin.HandlerFunc {
	cfg, ok := rl.limits[endpointType]
	if !ok {
		cfg = rl.limits["default"]
	}

	return func(c *gin.Context) {
		if rl.rdb == nil {
			c.Next()
			return
		}

		key := fmt.Sprintf("rl:%s:%s", endpointType, c.ClientIP())
		ctx := context.Background()

		count, err := rl.rdb.Incr(ctx, key).Result()
		if err != nil {
			c.Next()
			return
		}

		if count == 1 {
			rl.rdb.Expire(ctx, key, cfg.Window)
		}

		if count > int64(cfg.MaxRequests) {
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"detail": "Muitas tentativas. Aguarde antes de tentar novamente.",
			})
			return
		}

		c.Next()
	}
}
