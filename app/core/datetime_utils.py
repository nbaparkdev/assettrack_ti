from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

def now_sp() -> datetime:
    """
    Retorna a data e hora atual no fuso horário America/Sao_Paulo,
    sem info de timezone (naive), para ser salvo no banco como se fosse 'local'.
    """
    try:
        return datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
    except ZoneInfoNotFoundError:
        # Fallback caso o banco de dados de timezone não esteja disponível
        return datetime.now()
