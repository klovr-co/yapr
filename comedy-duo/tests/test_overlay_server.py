import pytest
import json
from unittest.mock import AsyncMock
from comedy_duo.overlay_server import OverlayServer


class TestOverlayServer:
    def test_init(self):
        server = OverlayServer(host="localhost", port=3003)
        assert server.host == "localhost"
        assert server.port == 3003
        assert len(server.clients) == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_clients(self):
        server = OverlayServer(host="localhost", port=3003)
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()
        server.clients = {mock_client1, mock_client2}

        await server.broadcast({"bot": "Carra", "text": "GET IN!"})

        expected = json.dumps({"bot": "Carra", "text": "GET IN!"})
        mock_client1.send.assert_called_once_with(expected)
        mock_client2.send.assert_called_once_with(expected)

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_clients(self):
        server = OverlayServer(host="localhost", port=3003)
        dead_client = AsyncMock()
        dead_client.send.side_effect = Exception("connection closed")
        server.clients = {dead_client}

        await server.broadcast({"bot": "Nev", "text": "Told you."})
        assert dead_client not in server.clients
