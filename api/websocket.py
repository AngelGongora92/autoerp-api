import json
import logging
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("websocket")
logger.setLevel(logging.INFO)

router = APIRouter(tags=["WebSocket"])

class ConnectionManager:
    def __init__(self):
        # Diccionario para mapear company_id (int) -> lista de WebSockets activos
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, company_id: int):
        """Acepta una conexión WebSocket y la asocia a una compañía (taller)."""
        await websocket.accept()
        if company_id not in self.active_connections:
            self.active_connections[company_id] = []
        self.active_connections[company_id].append(websocket)
        logger.info(f"WebSocket conectado para compañía {company_id}. Conexiones activas: {len(self.active_connections[company_id])}")

    def disconnect(self, websocket: WebSocket, company_id: int):
        """Remueve una conexión WebSocket activa."""
        if company_id in self.active_connections:
            if websocket in self.active_connections[company_id]:
                self.active_connections[company_id].remove(websocket)
                logger.info(f"WebSocket desconectado para compañía {company_id}. Conexiones restantes: {len(self.active_connections[company_id])}")
            if not self.active_connections[company_id]:
                del self.active_connections[company_id]

    async def broadcast_to_company(self, company_id: int, message: dict):
        """Envía un mensaje JSON a todos los WebSockets conectados de una compañía específica."""
        if company_id not in self.active_connections:
            return

        message_str = json.dumps(message, default=str)
        disconnected_sockets = []

        for connection in self.active_connections[company_id]:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Fallo al enviar mensaje por WebSocket a compañía {company_id}: {str(e)}")
                disconnected_sockets.append(connection)

        # Limpiar conexiones rotas detectadas durante el envío
        for socket in disconnected_sockets:
            self.disconnect(socket, company_id)

# Instancia global del manejador de conexiones
manager = ConnectionManager()


@router.websocket("/ws/chat/{company_id}")
async def websocket_endpoint(websocket: WebSocket, company_id: int):
    """
    Ruta de WebSocket para el chat de un taller específico.
    El frontend se conectará a 'ws://host/ws/chat/{company_id}'.
    """
    await manager.connect(websocket, company_id)
    try:
        while True:
            # Mantiene la conexión activa escuchando mensajes ping/pong del cliente.
            # Los mensajes salientes (del cliente) son opcionales por este canal,
            # pero recibir texto previene que el servidor cierre la conexión por inactividad.
            data = await websocket.receive_text()
            logger.info(f"Mensaje WebSocket recibido en backend de compañía {company_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, company_id)
    except Exception as e:
        logger.error(f"Error inesperado en WebSocket de compañía {company_id}: {str(e)}")
        manager.disconnect(websocket, company_id)
