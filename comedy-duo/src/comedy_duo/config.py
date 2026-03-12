from pathlib import Path

import yaml

from comedy_duo.models import BotConfig, Settings


def load_settings(path: Path) -> Settings:
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}
        return Settings(**data)
    return Settings()


def load_bot_config(path: Path) -> BotConfig:
    if not path.exists():
        raise FileNotFoundError(f"Bot config not found: {path}")
    data = yaml.safe_load(path.read_text())
    return BotConfig(**data)


def load_all_configs(config_dir: Path) -> tuple[Settings, dict[str, BotConfig]]:
    settings = load_settings(config_dir / "settings.yaml")

    bots: dict[str, BotConfig] = {}
    for yaml_file in config_dir.glob("*.yaml"):
        if yaml_file.stem == "settings":
            continue
        bot = load_bot_config(yaml_file)
        bots[yaml_file.stem] = bot

    return settings, bots
