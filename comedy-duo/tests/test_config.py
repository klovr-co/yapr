import pytest
from comedy_duo.config import load_settings, load_bot_config, load_all_configs


class TestLoadSettings:
    def test_loads_from_yaml(self, sample_settings_yaml):
        settings = load_settings(sample_settings_yaml)
        assert settings.cooldown_seconds == 30
        assert settings.tts_provider == "say"
        assert settings.websocket_port == 3003

    def test_missing_file_uses_defaults(self, tmp_path):
        missing = tmp_path / "nope.yaml"
        settings = load_settings(missing)
        assert settings.cooldown_seconds == 30


class TestLoadBotConfig:
    def test_loads_bot_from_yaml(self, sample_bot_yaml):
        bot = load_bot_config(sample_bot_yaml)
        assert bot.name == "TestBot"
        assert bot.role == "cheerleader"
        assert len(bot.example_lines) == 2

    def test_missing_file_raises(self, tmp_path):
        missing = tmp_path / "nope.yaml"
        with pytest.raises(FileNotFoundError):
            load_bot_config(missing)


class TestLoadAllConfigs:
    def test_loads_settings_and_bots(self, tmp_path):
        settings_yaml = tmp_path / "settings.yaml"
        settings_yaml.write_text("cooldown_seconds: 10\nmodel_name: 'openai:gpt-4o-mini'\n")

        bot_yaml = tmp_path / "carra.yaml"
        bot_yaml.write_text(
            'name: "Carra"\nrole: "cheerleader"\npersonality: "test"\nexample_lines:\n  - "hi"\n'
        )

        settings, bots = load_all_configs(tmp_path)
        assert settings.cooldown_seconds == 10
        assert "carra" in bots
        assert bots["carra"].name == "Carra"
