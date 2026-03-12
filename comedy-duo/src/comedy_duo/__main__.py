import asyncio
import logging
import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

from comedy_duo.config import load_all_configs
from comedy_duo.control_panel import create_app
from comedy_duo.orchestrator import Orchestrator
from comedy_duo.twitch_chat import TwitchChatClient

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_SESSIONS_DIR = Path.home() / ".claude" / "projects"


def find_project_sessions_dir() -> Path:
    cwd = Path.cwd()
    project_key = "-" + str(cwd).replace("/", "-")
    sessions_dir = DEFAULT_SESSIONS_DIR / project_key
    if sessions_dir.exists():
        return sessions_dir
    for d in DEFAULT_SESSIONS_DIR.iterdir():
        if d.is_dir() and list(d.glob("*.jsonl")):
            return d
    return sessions_dir


async def main():
    config_dir = Path(__file__).parent.parent.parent / "config"
    settings, bots = load_all_configs(config_dir)

    logger.info(f"Loaded {len(bots)} bot(s): {', '.join(b.name for b in bots.values())}")
    logger.info(f"Model: {settings.model_name}")
    logger.info(f"TTS: {settings.tts_provider}")

    orchestrator = Orchestrator(settings=settings, bots=bots)

    channel = os.environ.get("TWITCH_CHANNEL", "")
    for bot_key, bot_config in bots.items():
        env_prefix = bot_config.name.upper()
        token = os.environ.get(f"{env_prefix}_TWITCH_TOKEN", "")
        username = os.environ.get(f"{env_prefix}_TWITCH_USERNAME", "")
        if token and username and channel:
            client = TwitchChatClient(username=username, token=token, channel=channel)
            await client.connect()
            orchestrator.twitch_clients[bot_key] = client
            logger.info(f"Twitch: {username} connected to #{channel}")

    app = create_app(settings, event_callback=orchestrator.inject_event)
    server_config = uvicorn.Config(
        app, host="0.0.0.0", port=settings.control_panel_port, log_level="warning"
    )
    server = uvicorn.Server(server_config)

    sessions_dir = find_project_sessions_dir()
    logger.info(f"Sessions dir: {sessions_dir}")
    logger.info(f"Control panel: http://localhost:{settings.control_panel_port}")
    logger.info(f"Overlay WS: ws://localhost:{settings.websocket_port}")
    logger.info("Starting Carra and Nev...")

    await asyncio.gather(
        server.serve(),
        orchestrator.run(sessions_dir),
    )


if __name__ == "__main__":
    asyncio.run(main())
