# app/services/alert_broadcaster.py
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class AlertBroadcaster:
    def __init__(self):
        self._listeners: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self._listeners.add(queue)
        logger.info(f"[ALERT_BROADCASTER] Cliente conectado. Total de ouvintes: {len(self._listeners)}")
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self._listeners:
            self._listeners.remove(queue)
            logger.info(f"[ALERT_BROADCASTER] Cliente desconectado. Total de ouvintes: {len(self._listeners)}")

    async def broadcast(self, alert_data: dict):
        payload = json.dumps(alert_data)
        logger.info(f"[ALERT_BROADCASTER] Transmitindo alerta para {len(self._listeners)} clientes ativos: {alert_data.get('usuario_nome')}")
        
        # Put event into queues
        to_remove = set()
        for queue in list(self._listeners):
            try:
                queue.put_nowait(payload)
            except Exception as e:
                logger.error(f"[ALERT_BROADCASTER] Erro ao enviar para ouvinte: {e}")
                to_remove.add(queue)
                
        for q in to_remove:
            self.unsubscribe(q)

alert_broadcaster = AlertBroadcaster()
