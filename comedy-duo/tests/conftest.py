import pytest
from pathlib import Path

@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def sample_settings_yaml(tmp_path):
    content = """
cooldown_seconds: 30
hot_events_override_cooldown: true
tts_enabled: false
twitch_chat_enabled: false
overlay_enabled: true
duo_delay_seconds: 4
overlay_message_ttl_seconds: 15
overlay_max_visible: 5
tts_provider: "say"
control_panel_port: 3001
overlay_port: 3002
websocket_port: 3003
model_name: "openai:gpt-4o-mini"
"""
    p = tmp_path / "settings.yaml"
    p.write_text(content)
    return p

@pytest.fixture
def sample_bot_yaml(tmp_path):
    content = """
name: "TestBot"
role: "cheerleader"
voice_id: "test-voice"
personality: |
  You are TestBot, a test commentary bot.
example_lines:
  - "Test line one"
  - "Test line two"
"""
    p = tmp_path / "testbot.yaml"
    p.write_text(content)
    return p
