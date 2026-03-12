import pytest
import time
from unittest.mock import AsyncMock, MagicMock
from comedy_duo.orchestrator import Orchestrator, CooldownManager
from comedy_duo.models import (
    Settings,
    BotConfig,
    SessionEvent,
    EventTier,
    Commentary,
    CommentaryLine,
)


@pytest.fixture
def settings():
    return Settings(
        cooldown_seconds=5,
        tts_enabled=False,
        twitch_chat_enabled=False,
        overlay_enabled=False,
    )


@pytest.fixture
def bots():
    return {
        "carra": BotConfig(name="Carra", role="cheerleader", personality="test", example_lines=[]),
        "nev": BotConfig(name="Nev", role="critic", personality="test", example_lines=[]),
    }


class TestCooldownManager:
    def test_initially_ready(self):
        cm = CooldownManager(cooldown_seconds=30)
        assert cm.is_ready() is True

    def test_not_ready_after_fire(self):
        cm = CooldownManager(cooldown_seconds=30)
        cm.fire()
        assert cm.is_ready() is False

    def test_hot_overrides_cooldown(self):
        cm = CooldownManager(cooldown_seconds=30)
        cm.fire()
        assert cm.is_ready(hot_override=True) is True

    def test_ready_after_cooldown_expires(self):
        cm = CooldownManager(cooldown_seconds=0)
        cm.fire()
        assert cm.is_ready() is True


class TestOrchestrator:
    def test_init(self, settings, bots):
        orch = Orchestrator(settings=settings, bots=bots)
        assert orch.settings == settings

    @pytest.mark.asyncio
    async def test_handle_event_generates_commentary(self, settings, bots):
        orch = Orchestrator(settings=settings, bots=bots)
        event = SessionEvent(
            tier=EventTier.HOT,
            event_type="error",
            summary="Test failed",
            raw_data={},
        )
        mock_commentary = Commentary(
            lines=[
                CommentaryLine(bot_name="Carra", text="Oh no!"),
                CommentaryLine(bot_name="Nev", text="Told you."),
            ],
            is_duo=True,
        )
        orch.engine = MagicMock()
        orch.engine.generate = AsyncMock(return_value=mock_commentary)
        orch._fan_out = AsyncMock()

        await orch.handle_event(event)

        orch.engine.generate.assert_called_once()
        orch._fan_out.assert_called_once_with(mock_commentary)
