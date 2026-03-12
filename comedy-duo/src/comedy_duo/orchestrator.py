import asyncio
import logging
import time
from pathlib import Path

from comedy_duo.engine import CommentaryEngine
from comedy_duo.models import (
    BotConfig,
    Commentary,
    EventTier,
    SessionEvent,
    Settings,
)
from comedy_duo.overlay_server import OverlayServer
from comedy_duo.tts import TTSProvider, get_tts_provider, DEFAULT_VOICES
from comedy_duo.twitch_chat import TwitchChatClient
from comedy_duo.watcher import classify_jsonl_line, find_latest_session

logger = logging.getLogger(__name__)


class CooldownManager:
    def __init__(self, cooldown_seconds: int):
        self.cooldown_seconds = cooldown_seconds
        self._last_fire: float = 0

    def is_ready(self, hot_override: bool = False) -> bool:
        if hot_override:
            return True
        return (time.time() - self._last_fire) >= self.cooldown_seconds

    def fire(self) -> None:
        self._last_fire = time.time()


class Orchestrator:
    def __init__(self, settings: Settings, bots: dict[str, BotConfig]):
        self.settings = settings
        self.bots = bots
        self.engine = CommentaryEngine(bots=bots, settings=settings)
        self.cooldown = CooldownManager(settings.cooldown_seconds)
        self.overlay = OverlayServer(port=settings.websocket_port)
        self.tts: TTSProvider = get_tts_provider(settings)
        self.twitch_clients: dict[str, TwitchChatClient] = {}
        self.recent_history: list[tuple[str, str]] = []
        self._event_queue: asyncio.Queue[SessionEvent] = asyncio.Queue()

    def inject_event(self, event: SessionEvent) -> None:
        self._event_queue.put_nowait(event)

    async def handle_event(self, event: SessionEvent) -> None:
        is_hot = event.tier == EventTier.HOT
        if not self.cooldown.is_ready(hot_override=is_hot):
            logger.debug("Cooldown active, skipping event")
            return

        commentary = await self.engine.generate(
            event,
            recent_history=self.recent_history,
        )
        self.cooldown.fire()

        for line in commentary.lines:
            self.recent_history.append((line.bot_name, line.text))
        self.recent_history = self.recent_history[-10:]

        await self._fan_out(commentary)

    async def _fan_out(self, commentary: Commentary) -> None:
        for i, line in enumerate(commentary.lines):
            if i > 0:
                await asyncio.sleep(self.settings.duo_delay_seconds)

            tasks = []

            if self.settings.overlay_enabled:
                tasks.append(
                    self.overlay.broadcast({"bot": line.bot_name, "text": line.text})
                )

            if self.settings.twitch_chat_enabled:
                bot_key = line.bot_name.lower()
                if bot_key in self.twitch_clients:
                    tasks.append(self.twitch_clients[bot_key].send(line.text))

            if self.settings.tts_enabled:
                bot_key = line.bot_name.lower()
                voice = self.bots.get(bot_key, None)
                voice_id = voice.voice_id if voice else DEFAULT_VOICES.get(bot_key)
                tasks.append(self.tts.speak(line.text, voice=voice_id))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _watch_session(self, session_path: Path) -> None:
        logger.info(f"Watching session: {session_path}")
        last_pos = session_path.stat().st_size

        while True:
            current_size = session_path.stat().st_size
            if current_size > last_pos:
                with open(session_path) as f:
                    f.seek(last_pos)
                    for raw_line in f:
                        raw_line = raw_line.strip()
                        if not raw_line:
                            continue
                        event = classify_jsonl_line(raw_line)
                        if event:
                            await self.handle_event(event)
                    last_pos = f.tell()
            await asyncio.sleep(1)

    async def _process_manual_events(self) -> None:
        while True:
            event = await self._event_queue.get()
            await self.handle_event(event)

    async def run(self, sessions_dir: Path) -> None:
        session_path = find_latest_session(sessions_dir)
        if not session_path:
            logger.error(f"No session files found in {sessions_dir}")
            return

        tasks = [
            asyncio.create_task(self.overlay.start()),
            asyncio.create_task(self._watch_session(session_path)),
            asyncio.create_task(self._process_manual_events()),
        ]

        await asyncio.gather(*tasks)
