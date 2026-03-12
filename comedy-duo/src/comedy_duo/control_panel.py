import logging
from typing import Callable

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from comedy_duo.models import EventTier, SessionEvent, Settings

logger = logging.getLogger(__name__)


class EventInput(BaseModel):
    text: str


class SettingsUpdate(BaseModel):
    cooldown_seconds: int | None = None
    tts_enabled: bool | None = None
    twitch_chat_enabled: bool | None = None
    overlay_enabled: bool | None = None
    duo_delay_seconds: int | None = None


CONTROL_PAGE_HTML = """<!DOCTYPE html>
<html><head><title>Carra and Nev Control</title>
<style>
body { font-family: system-ui; max-width: 600px; margin: 40px auto; padding: 0 20px; background: #1a1a2e; color: #eee; }
h1 { color: #e94560; }
input, button, textarea { padding: 10px; border-radius: 6px; border: 1px solid #444; background: #16213e; color: #eee; font-size: 14px; }
textarea { width: 100%; height: 60px; }
button { background: #e94560; border: none; cursor: pointer; font-weight: bold; }
button:hover { background: #c73e54; }
button.kill { background: #333; }
.section { margin: 20px 0; padding: 16px; background: #16213e; border-radius: 8px; }
</style></head><body>
<h1>Carra and Nev</h1>
<div class="section">
<h3>Inject Event</h3>
<textarea id="eventText" placeholder="What's happening?"></textarea><br><br>
<button onclick="inject()">Send Event</button>
</div>
<div class="section">
<h3>Kill Switch</h3>
<button class="kill" onclick="kill()">Silence Both Bots</button>
</div>
<script>
async function inject() {
    var text = document.getElementById('eventText').value;
    await fetch('/event', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text: text})});
    document.getElementById('eventText').value = '';
}
async function kill() { await fetch('/kill', {method:'POST'}); }
</script></body></html>"""


def create_app(
    settings: Settings,
    event_callback: Callable[[SessionEvent], None] | None = None,
) -> FastAPI:
    app = FastAPI(title="Carra and Nev Control Panel")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/event")
    async def inject_event(event: EventInput):
        manual_event = SessionEvent(
            tier=EventTier.HOT,
            event_type="manual",
            summary=event.text,
            raw_data={},
            is_manual=True,
        )
        if event_callback:
            event_callback(manual_event)
        return {"status": "injected", "text": event.text}

    @app.get("/settings")
    async def get_settings():
        return settings.model_dump()

    @app.patch("/settings")
    async def update_settings(update: SettingsUpdate):
        for field, value in update.model_dump(exclude_none=True).items():
            setattr(settings, field, value)
        return settings.model_dump()

    @app.post("/kill")
    async def kill_switch():
        settings.tts_enabled = False
        settings.twitch_chat_enabled = False
        settings.overlay_enabled = False
        logger.warning("KILL SWITCH activated - all outputs disabled")
        return {"status": "killed", "message": "All outputs disabled"}

    @app.get("/", response_class=HTMLResponse)
    async def control_page():
        return CONTROL_PAGE_HTML

    return app
