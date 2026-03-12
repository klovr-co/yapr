import asyncio
import logging

import websockets

logger = logging.getLogger(__name__)

TWITCH_IRC_URL = "wss://irc-ws.chat.twitch.tv:443"


def format_irc_message(channel: str, text: str) -> str:
    channel = channel.lstrip("#")
    return f"PRIVMSG #{channel} :{text}\r\n"


class TwitchChatClient:
    def __init__(self, username: str, token: str, channel: str):
        self.username = username
        self.token = token
        self.channel = channel.lstrip("#")
        self._ws = None
        self._connected = False

    async def connect(self) -> None:
        self._ws = await websockets.connect(TWITCH_IRC_URL)
        await self._ws.send(f"PASS {self.token}\r\n")
        await self._ws.send(f"NICK {self.username}\r\n")
        await self._ws.send(f"JOIN #{self.channel}\r\n")
        self._connected = True
        logger.info(f"[{self.username}] Connected to #{self.channel}")
        asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        try:
            async for message in self._ws:
                if message.startswith("PING"):
                    await self._ws.send("PONG :tmi.twitch.tv\r\n")
        except websockets.ConnectionClosed:
            self._connected = False
            logger.warning(f"[{self.username}] Disconnected from Twitch")

    async def send(self, text: str) -> None:
        if not self._connected or not self._ws:
            logger.warning(f"[{self.username}] Not connected, skipping message")
            return
        msg = format_irc_message(self.channel, text)
        await self._ws.send(msg)

    async def disconnect(self) -> None:
        if self._ws:
            await self._ws.close()
            self._connected = False
