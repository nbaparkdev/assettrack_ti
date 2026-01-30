# app/core/rate_limit.py
"""
Rate Limiting para proteção de endpoints sensíveis.
Usa slowapi para limitar requisições por IP.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Limiter global - usa IP como identificador
limiter = Limiter(key_func=get_remote_address)

# Configurações de rate limit por tipo de endpoint
RATE_LIMITS = {
    # Login endpoints - mais restritivos
    "login": "5/minute",           # 5 tentativas por minuto
    "qr_login": "10/minute",       # 10 tentativas de login QR por minuto
    "pin_verify": "5/minute",      # 5 verificações de PIN por minuto
    
    # Token endpoints - moderados
    "qr_regenerate": "3/hour",     # 3 regenerações de QR por hora
    "pin_setup": "5/hour",         # 5 configurações de PIN por hora
    
    # Consultas - mais permissivos
    "qr_public_profile": "30/minute",  # 30 consultas por minuto
    "delivery_confirm": "20/minute",   # 20 confirmações por minuto
}

def get_rate_limit(endpoint_type: str) -> str:
    """Retorna o rate limit para um tipo de endpoint"""
    return RATE_LIMITS.get(endpoint_type, "60/minute")
