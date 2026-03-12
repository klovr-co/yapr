import pytest
from comedy_duo.models import (
    EventTier,
    SessionEvent,
    BotConfig,
    Settings,
    Commentary,
    CommentaryLine,
)


class TestEventTier:
    def test_hot_tier_exists(self):
        assert EventTier.HOT.value == "hot"

    def test_warm_tier_exists(self):
        assert EventTier.WARM.value == "warm"

    def test_cold_tier_exists(self):
        assert EventTier.COLD.value == "cold"


class TestSessionEvent:
    def test_create_event(self):
        event = SessionEvent(
            tier=EventTier.HOT,
            event_type="error",
            summary="TypeError in main.py",
            raw_data={"type": "assistant", "message": {"content": "error"}},
        )
        assert event.tier == EventTier.HOT
        assert event.event_type == "error"

    def test_manual_event(self):
        event = SessionEvent(
            tier=EventTier.HOT,
            event_type="manual",
            summary="she just mass-deleted 400 lines",
            raw_data={},
            is_manual=True,
        )
        assert event.is_manual is True


class TestBotConfig:
    def test_create_bot_config(self):
        config = BotConfig(
            name="Carra",
            role="cheerleader",
            personality="You are Carra",
            example_lines=["GET IN!"],
        )
        assert config.name == "Carra"

    def test_voice_id_optional(self):
        config = BotConfig(
            name="Carra",
            role="cheerleader",
            personality="You are Carra",
            example_lines=[],
        )
        assert config.voice_id is None


class TestSettings:
    def test_defaults(self):
        settings = Settings()
        assert settings.cooldown_seconds == 30
        assert settings.tts_provider == "say"

    def test_custom_values(self):
        settings = Settings(cooldown_seconds=60, tts_provider="elevenlabs")
        assert settings.cooldown_seconds == 60


class TestCommentary:
    def test_duo_commentary(self):
        lines = [
            CommentaryLine(bot_name="Carra", text="GET IN!"),
            CommentaryLine(bot_name="Nev", text="Calm down."),
        ]
        c = Commentary(lines=lines, is_duo=True)
        assert c.is_duo is True
        assert len(c.lines) == 2

    def test_solo_commentary(self):
        lines = [CommentaryLine(bot_name="Carra", text="Lovely stuff")]
        c = Commentary(lines=lines, is_duo=False)
        assert c.is_duo is False
