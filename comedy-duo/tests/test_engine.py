import pytest
from unittest.mock import AsyncMock, patch
from comedy_duo.engine import CommentaryEngine, build_commentary_prompt
from comedy_duo.models import (
    BotConfig,
    Settings,
    SessionEvent,
    EventTier,
    Commentary,
)


@pytest.fixture
def carra_config():
    return BotConfig(
        name="Carra",
        role="cheerleader",
        personality="You are Carra, passionate pundit.",
        example_lines=["GET IN!", "That's class!"],
    )


@pytest.fixture
def nev_config():
    return BotConfig(
        name="Nev",
        role="critic",
        personality="You are Nev, analytical wind-up merchant.",
        example_lines=["Interesting choice.", "I said it."],
    )


@pytest.fixture
def settings():
    return Settings(model_name="openai:gpt-4o-mini")


@pytest.fixture
def hot_event():
    return SessionEvent(
        tier=EventTier.HOT,
        event_type="error",
        summary="FAILED test_auth.py - AssertionError",
        raw_data={},
    )


@pytest.fixture
def warm_event():
    return SessionEvent(
        tier=EventTier.WARM,
        event_type="new_file",
        summary="Created src/utils.py",
        raw_data={},
    )


class TestBuildPrompt:
    def test_includes_event_summary(self, hot_event):
        prompt = build_commentary_prompt(hot_event, recent_history=[])
        assert "FAILED test_auth.py" in prompt

    def test_includes_recent_history(self, hot_event):
        history = [("Carra", "That's brilliant!"), ("Nev", "Is it though?")]
        prompt = build_commentary_prompt(hot_event, recent_history=history)
        assert "That's brilliant!" in prompt
        assert "Is it though?" in prompt

    def test_includes_event_type(self, hot_event):
        prompt = build_commentary_prompt(hot_event, recent_history=[])
        assert "error" in prompt.lower()


class TestCommentaryEngine:
    def test_engine_init(self, carra_config, nev_config, settings):
        engine = CommentaryEngine(
            bots={"carra": carra_config, "nev": nev_config},
            settings=settings,
        )
        assert engine.bots["carra"].name == "Carra"

    @pytest.mark.asyncio
    async def test_generate_returns_commentary(self, carra_config, nev_config, settings, hot_event):
        engine = CommentaryEngine(
            bots={"carra": carra_config, "nev": nev_config},
            settings=settings,
        )
        with patch.object(engine, "_run_agent", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = [
                "Oh no, that's heartbreaking!",
                "I said it was coming.",
            ]
            result = await engine.generate(hot_event, recent_history=[], force_duo=True)

        assert isinstance(result, Commentary)
        assert len(result.lines) == 2
        assert result.lines[0].bot_name == "Carra"
        assert result.lines[1].bot_name == "Nev"
        assert result.is_duo is True
