import json
import logging

import websockets

logger = logging.getLogger(__name__)


class OverlayServer:
    def __init__(self, host: str = "localhost", port: int = 3003):
        self.host = host
        self.port = port
        self.clients: set = set()

    async def _handler(self, websocket):
        self.clients.add(websocket)
        logger.info(f"Overlay client connected ({len(self.clients)} total)")
        try:
            async for _ in websocket:
                pass
        finally:
            self.clients.discard(websocket)
            logger.info(f"Overlay client disconnected ({len(self.clients)} total)")

    async def broadcast(self, data: dict) -> None:
        message = json.dumps(data)
        dead = set()
        for client in self.clients:
            try:
                await client.send(message)
            except Exception:
                dead.add(client)
        self.clients -= dead

    async def start(self) -> None:
        server = await websockets.serve(self._handler, self.host, self.port)
        logger.info(f"Overlay WebSocket server on ws://{self.host}:{self.port}")
        await server.wait_closed()
