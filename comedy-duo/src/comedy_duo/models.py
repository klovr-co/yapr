from enum import Enum
from pydantic import BaseModel


class EventTier(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class SessionEvent(BaseModel):
    tier: EventTier
    event_type: str
    summary: str
    raw_data: dict
    is_manual: bool = False


class BotConfig(BaseModel):
    name: str
    role: str
    personality: str
    example_lines: list[str]
    voice_id: str | None = None


class Settings(BaseModel):
    cooldown_seconds: int = 30
    hot_events_override_cooldown: bool = True
    tts_enabled: bool = True
    twitch_chat_enabled: bool = True
    overlay_enabled: bool = True
    duo_delay_seconds: int = 4
    overlay_message_ttl_seconds: int = 15
    overlay_max_visible: int = 5
    tts_provider: str = "say"
    control_panel_port: int = 3001
    overlay_port: int = 3002
    websocket_port: int = 3003
    model_name: str = "openai:gpt-4o-mini"


class CommentaryLine(BaseModel):
    bot_name: str
    text: str


class Commentary(BaseModel):
    lines: list[CommentaryLine]
    is_duo: bool
