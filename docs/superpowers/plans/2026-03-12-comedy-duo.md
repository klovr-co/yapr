# Comedy Duo (Carra & Nev) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two AI-powered Twitch bots (Carra and Nev) that provide live pundit-style commentary on a vibe coding livestream by watching Claude Code session logs.

**Architecture:** A Python asyncio application with five subsystems: a session watcher that tails Claude Code JSONL logs and classifies events, a Pydantic AI commentary engine with two configurable bot personalities, and three output channels (Twitch IRC chat, OBS WebSocket overlay, TTS). A FastAPI control panel provides manual event injection and runtime toggles.

**Tech Stack:** Python 3.14, Pydantic AI, FastAPI, uvicorn, websockets, watchfiles, httpx, PyYAML, python-dotenv

**Design doc:** `docs/plans/2026-03-12-comedy-duo-design.md`

---

## File Structure

```
comedy-duo/
├── pyproject.toml                    # Package config, dependencies, entry point
├── .env.example                      # Template for secrets
├── config/
│   ├── settings.yaml                 # Global settings (cooldowns, ports, toggles)
│   ├── carra.yaml                    # Carra personality + voice config
│   └── nev.yaml                      # Nev personality + voice config
├── src/
│   └── comedy_duo/
│       ├── __init__.py               # Package init
│       ├── __main__.py               # Entry point: python -m comedy_duo
│       ├── models.py                 # Pydantic models: Event, BotConfig, Settings, Commentary
│       ├── config.py                 # Load YAML configs + .env, hot-reload support
│       ├── watcher.py                # Tail JSONL logs, classify events into tiers
│       ├── engine.py                 # Pydantic AI agents, generate commentary
│       ├── twitch_chat.py            # Twitch IRC WebSocket client (two accounts)
│       ├── tts.py                    # TTS provider abstraction (ElevenLabs / macOS say)
│       ├── overlay_server.py         # WebSocket server pushing messages to OBS overlay
│       ├── control_panel.py          # FastAPI app: manual events, toggles, kill switch
│       └── orchestrator.py           # Main async loop: watcher -> engine -> fan-out
├── overlay/
│   ├── index.html                    # OBS browser source
│   ├── style.css                     # Ticker styling, bot colours, animations
│   └── script.js                     # WebSocket client, message rendering, auto-scroll
└── tests/
    ├── conftest.py                   # Shared fixtures
    ├── test_models.py                # Model validation tests
    ├── test_config.py                # Config loading tests
    ├── test_watcher.py               # Event classification tests
    ├── test_engine.py                # Commentary generation tests
    ├── test_tts.py                   # TTS provider tests
    ├── test_twitch_chat.py           # IRC message formatting tests
    ├── test_overlay_server.py        # WebSocket broadcast tests
    ├── test_control_panel.py         # API endpoint tests
    └── test_orchestrator.py          # Cooldown + fan-out tests
```

---

## Chunk 1: Project Setup + Models + Config

### Task 1: Project scaffolding

**Files:**
- Create: `comedy-duo/pyproject.toml`
- Create: `comedy-duo/.env.example`
- Create: `comedy-duo/src/comedy_duo/__init__.py`
- Create: `comedy-duo/tests/__init__.py`
- Create: `comedy-duo/tests/conftest.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "comedy-duo"
version = "0.1.0"
description = "Carra & Nev: AI-powered live coding commentary bots"
requires-python = ">=3.12"
dependencies = [
    "pydantic-ai>=1.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "fastapi>=0.100",
    "uvicorn>=0.20",
    "websockets>=12.0",
    "watchfiles>=0.20",
    "httpx>=0.25",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23", "pytest-httpx>=0.30"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/comedy_duo"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Create `.env.example`**

```env
# Twitch Bot Accounts
CARRA_TWITCH_TOKEN=oauth:xxx
CARRA_TWITCH_USERNAME=carra_bot
NEV_TWITCH_TOKEN=oauth:xxx
NEV_TWITCH_USERNAME=nev_bot
TWITCH_CHANNEL=your_channel

# LLM (used by Pydantic AI - set whichever provider you use)
OPENAI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx

# TTS (optional - falls back to macOS say)
ELEVENLABS_API_KEY=xxx
```

- [ ] **Step 3: Create empty `__init__.py` files**

Create `comedy-duo/src/comedy_duo/__init__.py` and `comedy-duo/tests/__init__.py` as empty files.

- [ ] **Step 4: Create `conftest.py` with shared fixtures**

```python
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
```

- [ ] **Step 5: Install the package in dev mode**

Run: `cd comedy-duo && pip install -e ".[dev]"`

- [ ] **Step 6: Commit**

```bash
git add comedy-duo/pyproject.toml comedy-duo/.env.example comedy-duo/src/ comedy-duo/tests/
git commit -m "feat(comedy-duo): scaffold project with dependencies and test config"
```

---

### Task 2: Pydantic models

**Files:**
- Create: `comedy-duo/src/comedy_duo/models.py`
- Create: `comedy-duo/tests/test_models.py`

- [ ] **Step 1: Write failing tests for models**

```python
# tests/test_models.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd comedy-duo && python -m pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'comedy_duo.models'`

- [ ] **Step 3: Implement models**

```python
# src/comedy_duo/models.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd comedy-duo && python -m pytest tests/test_models.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add comedy-duo/src/comedy_duo/models.py comedy-duo/tests/test_models.py
git commit -m "feat(comedy-duo): add pydantic models for events, bots, settings, commentary"
```

---

### Task 3: Config loading

**Files:**
- Create: `comedy-duo/src/comedy_duo/config.py`
- Create: `comedy-duo/config/settings.yaml`
- Create: `comedy-duo/config/carra.yaml`
- Create: `comedy-duo/config/nev.yaml`
- Create: `comedy-duo/tests/test_config.py`

- [ ] **Step 1: Create the YAML config files**

`config/settings.yaml`:
```yaml
cooldown_seconds: 30
hot_events_override_cooldown: true
tts_enabled: true
twitch_chat_enabled: true
overlay_enabled: true
duo_delay_seconds: 4
overlay_message_ttl_seconds: 15
overlay_max_visible: 5
tts_provider: "say"
control_panel_port: 3001
overlay_port: 3002
websocket_port: 3003
model_name: "openai:gpt-4o-mini"
```

`config/carra.yaml`:
```yaml
name: "Carra"
role: "cheerleader"
voice_id: null
personality: |
  You are Carra, a passionate football pundit commentating on a live coding stream.
  You defend every coding decision like it's a last-minute tackle.
  You get personally invested, devastated by errors, celebrate hard when tests pass.
  Style: emotional, loyal, uses football metaphors frequently.
  Keep responses to 1-2 short sentences. Be punchy and entertaining.
example_lines:
  - "She KNOWS what she's doing here, that's class"
  - "Oh no... no no no... that's heartbreaking that"
  - "GET IN! Tests passing, every single one, you love to see it!"
```

`config/nev.yaml`:
```yaml
name: "Nev"
role: "critic"
voice_id: null
personality: |
  You are Nev, an analytical football pundit commentating on a live coding stream.
  You are measured, tactical, and slightly smug. You love pointing out flaws.
  You're a wind-up merchant who always predicted the bug before it happened.
  You give grudging respect when something is genuinely well done.
  Keep responses to 1-2 short sentences. Be dry and witty.
example_lines:
  - "See what she's done there? Interesting choice. Very interesting."
  - "I said ten minutes ago that import was gonna cause problems, Carra. I said it."
  - "Fair play. That's a clean refactor. I'll give her that."
```

- [ ] **Step 2: Write failing tests for config loading**

```python
# tests/test_config.py
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd comedy-duo && python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'comedy_duo.config'`

- [ ] **Step 4: Implement config loading**

```python
# src/comedy_duo/config.py
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd comedy-duo && python -m pytest tests/test_config.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add comedy-duo/src/comedy_duo/config.py comedy-duo/tests/test_config.py comedy-duo/config/
git commit -m "feat(comedy-duo): add YAML config loading with bot personalities and settings"
```

---

## Chunk 2: Session Watcher + Event Classification

### Task 4: Session watcher and event classifier

**Files:**
- Create: `comedy-duo/src/comedy_duo/watcher.py`
- Create: `comedy-duo/tests/test_watcher.py`
- Create: `comedy-duo/tests/fixtures/sample_session.jsonl`

The watcher needs to understand Claude Code's JSONL format. Each line is a JSON object with a `type` field (values: `user`, `assistant`, `system`, `progress`, `file-history-snapshot`). The `assistant` type has a `message.content` that is a list of blocks. Each block has a `type` (e.g., `text`, `tool_use`, `tool_result`, `thinking`). Tool use blocks have a `name` field (e.g., `Bash`, `Read`, `Edit`, `Write`).

- [ ] **Step 1: Create test fixture - sample JSONL lines**

Create `comedy-duo/tests/fixtures/sample_session.jsonl` with representative lines:

```jsonl
{"type":"user","message":{"role":"user","content":"fix the auth bug"},"timestamp":"2026-03-12T10:00:00Z"}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"I'll fix the auth bug."}]},"timestamp":"2026-03-12T10:00:05Z"}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","name":"Bash","input":{"command":"pytest tests/ -v"}}]},"timestamp":"2026-03-12T10:00:10Z"}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_result","content":"FAILED tests/test_auth.py::test_login - AssertionError"}]},"timestamp":"2026-03-12T10:00:15Z"}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","name":"Write","input":{"file_path":"src/new_module.py","content":"# new file"}}]},"timestamp":"2026-03-12T10:00:25Z"}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"I apologize for the confusion. Let me fix that."}]},"timestamp":"2026-03-12T10:00:30Z"}
{"type":"progress","message":null,"timestamp":"2026-03-12T10:00:35Z"}
```

- [ ] **Step 2: Write failing tests for event classification**

```python
# tests/test_watcher.py
import json
import time
import pytest
from comedy_duo.watcher import classify_jsonl_line, find_latest_session
from comedy_duo.models import EventTier


class TestClassifyLine:
    def test_test_failure_is_hot(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "tool_result", "content": "FAILED tests/test_auth.py - AssertionError"}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is not None
        assert event.tier == EventTier.HOT
        assert "fail" in event.event_type.lower()

    def test_apology_is_hot(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "text", "text": "I apologize for the confusion."}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is not None
        assert event.tier == EventTier.HOT

    def test_new_file_is_warm(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "src/new.py", "content": "x"}}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is not None
        assert event.tier == EventTier.WARM

    def test_file_read_is_cold(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Read", "input": {"file_path": "src/main.py"}}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is None

    def test_progress_line_is_cold(self):
        line = json.dumps({"type": "progress", "message": None})
        event = classify_jsonl_line(line)
        assert event is None

    def test_user_correction_is_hot(self):
        line = json.dumps({
            "type": "user",
            "message": {"role": "user", "content": "no that's wrong, do it this way instead"},
        })
        event = classify_jsonl_line(line)
        assert event is not None
        assert event.tier == EventTier.HOT

    def test_bash_error_is_hot(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "tool_result", "content": "Error: command not found\nexit code: 127"}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is not None
        assert event.tier == EventTier.HOT

    def test_edit_is_cold(self):
        line = json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Edit", "input": {"file_path": "x.py", "old_string": "a", "new_string": "b"}}
            ]},
        })
        event = classify_jsonl_line(line)
        assert event is None


class TestFindLatestSession:
    def test_finds_most_recent_jsonl(self, tmp_path):
        old = tmp_path / "old.jsonl"
        old.write_text("{}\n")
        time.sleep(0.05)
        new = tmp_path / "new.jsonl"
        new.write_text("{}\n")
        result = find_latest_session(tmp_path)
        assert result == new

    def test_returns_none_if_empty(self, tmp_path):
        result = find_latest_session(tmp_path)
        assert result is None
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd comedy-duo && python -m pytest tests/test_watcher.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'comedy_duo.watcher'`

- [ ] **Step 4: Implement watcher**

```python
# src/comedy_duo/watcher.py
import json
import re
from pathlib import Path

from comedy_duo.models import EventTier, SessionEvent

CORRECTION_PATTERNS = re.compile(
    r"(no[,.]?\s+(that's|thats)\s+wrong|don't do|instead\s+do|not\s+that|wrong\s+approach|"
    r"stop|undo\s+that|revert|that's\s+not\s+what\s+I)",
    re.IGNORECASE,
)

ERROR_PATTERNS = re.compile(
    r"(FAILED|Error:|error:|Traceback|exception|exit\s+code:\s+[1-9]|"
    r"ModuleNotFoundError|ImportError|SyntaxError|TypeError|ValueError|"
    r"command\s+not\s+found|Permission\s+denied)",
    re.IGNORECASE,
)

APOLOGY_PATTERNS = re.compile(
    r"(I\s+apologize|I'm\s+sorry|my\s+mistake|let\s+me\s+fix\s+that|"
    r"I\s+was\s+wrong|that\s+was\s+incorrect)",
    re.IGNORECASE,
)


def classify_jsonl_line(line: str) -> SessionEvent | None:
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    msg_type = data.get("type")
    message = data.get("message")

    if msg_type in ("progress", "file-history-snapshot", "system"):
        return None

    if not message:
        return None

    if msg_type == "user":
        content = message.get("content", "")
        if isinstance(content, str) and CORRECTION_PATTERNS.search(content):
            return SessionEvent(
                tier=EventTier.HOT,
                event_type="user_correction",
                summary=content[:200],
                raw_data=data,
            )
        return None

    if msg_type == "assistant":
        content = message.get("content", [])
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]

        for block in content:
            if not isinstance(block, dict):
                continue

            block_type = block.get("type", "")

            if block_type == "tool_result":
                result_text = block.get("content", "")
                if isinstance(result_text, str) and ERROR_PATTERNS.search(result_text):
                    return SessionEvent(
                        tier=EventTier.HOT,
                        event_type="error",
                        summary=result_text[:200],
                        raw_data=data,
                    )

            if block_type == "text":
                text = block.get("text", "")
                if APOLOGY_PATTERNS.search(text):
                    return SessionEvent(
                        tier=EventTier.HOT,
                        event_type="apology",
                        summary=text[:200],
                        raw_data=data,
                    )

            if block_type == "tool_use":
                tool_name = block.get("name", "")

                if tool_name == "Write":
                    file_path = block.get("input", {}).get("file_path", "")
                    return SessionEvent(
                        tier=EventTier.WARM,
                        event_type="new_file",
                        summary=f"Created {file_path}",
                        raw_data=data,
                    )

                if tool_name == "Bash":
                    cmd = block.get("input", {}).get("command", "")
                    if any(kw in cmd for kw in ("pip install", "npm install", "brew install")):
                        return SessionEvent(
                            tier=EventTier.WARM,
                            event_type="dependency_install",
                            summary=f"Installing: {cmd[:100]}",
                            raw_data=data,
                        )
                    if "git commit" in cmd:
                        return SessionEvent(
                            tier=EventTier.WARM,
                            event_type="commit",
                            summary=f"Committing: {cmd[:100]}",
                            raw_data=data,
                        )

                if tool_name in ("Read", "Edit", "Glob", "Grep"):
                    return None

    return None


def find_latest_session(sessions_dir: Path) -> Path | None:
    jsonl_files = list(sessions_dir.glob("*.jsonl"))
    if not jsonl_files:
        return None
    return max(jsonl_files, key=lambda f: f.stat().st_mtime)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd comedy-duo && python -m pytest tests/test_watcher.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add comedy-duo/src/comedy_duo/watcher.py comedy-duo/tests/test_watcher.py comedy-duo/tests/fixtures/
git commit -m "feat(comedy-duo): add session watcher with event classification (HOT/WARM/COLD)"
```

---

## Chunk 3: Commentary Engine (Pydantic AI)

### Task 5: Commentary engine with Pydantic AI agents

**Files:**
- Create: `comedy-duo/src/comedy_duo/engine.py`
- Create: `comedy-duo/tests/test_engine.py`

The engine creates two Pydantic AI agents (one per bot personality). It takes a `SessionEvent` plus recent conversation history and generates a `Commentary` object. The LLM decides whether to produce a solo or duo response.

- [ ] **Step 1: Write failing tests for the engine**

```python
# tests/test_engine.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd comedy-duo && python -m pytest tests/test_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'comedy_duo.engine'`

- [ ] **Step 3: Implement the commentary engine**

```python
# src/comedy_duo/engine.py
from pydantic_ai import Agent

from comedy_duo.models import (
    BotConfig,
    Commentary,
    CommentaryLine,
    EventTier,
    SessionEvent,
    Settings,
)


def build_commentary_prompt(
    event: SessionEvent,
    recent_history: list[tuple[str, str]],
) -> str:
    parts = [
        f"EVENT TYPE: {event.event_type}",
        f"EVENT TIER: {event.tier.value}",
        f"WHAT HAPPENED: {event.summary}",
    ]

    if recent_history:
        parts.append("\nRECENT COMMENTARY:")
        for name, text in recent_history[-5:]:
            parts.append(f"  {name}: {text}")

    parts.append("\nRespond with a short, punchy commentary line (1-2 sentences max).")
    return "\n".join(parts)


class CommentaryEngine:
    def __init__(self, bots: dict[str, BotConfig], settings: Settings):
        self.bots = bots
        self.settings = settings
        self._agents: dict[str, Agent] = {}

        for key, bot in bots.items():
            system_prompt = (
                f"{bot.personality}\n\n"
                f"Example lines for tone reference:\n"
                + "\n".join(f"- {line}" for line in bot.example_lines)
            )
            self._agents[key] = Agent(
                settings.model_name,
                system_prompt=system_prompt,
            )

    async def _run_agent(self, bot_key: str, prompt: str) -> str:
        result = await self._agents[bot_key].run(prompt)
        return result.output

    async def generate(
        self,
        event: SessionEvent,
        recent_history: list[tuple[str, str]],
        force_duo: bool = False,
    ) -> Commentary:
        prompt = build_commentary_prompt(event, recent_history)

        is_duo = force_duo or event.tier == EventTier.HOT

        bot_keys = sorted(self.bots.keys())
        first_key = bot_keys[0]
        second_key = bot_keys[1] if len(bot_keys) > 1 else first_key

        first_text = await self._run_agent(first_key, prompt)
        lines = [CommentaryLine(bot_name=self.bots[first_key].name, text=first_text)]

        if is_duo and len(bot_keys) > 1:
            duo_prompt = (
                prompt
                + f'\n\n{self.bots[first_key].name} just said: "{first_text}"\n\nNow respond to them.'
            )
            second_text = await self._run_agent(second_key, duo_prompt)
            lines.append(CommentaryLine(bot_name=self.bots[second_key].name, text=second_text))

        return Commentary(lines=lines, is_duo=is_duo)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd comedy-duo && python -m pytest tests/test_engine.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add comedy-duo/src/comedy_duo/engine.py comedy-duo/tests/test_engine.py
git commit -m "feat(comedy-duo): add Pydantic AI commentary engine with duo/solo generation"
```

---

## Chunk 4: Output Channels (TTS, Twitch Chat, Overlay)

### Task 6: TTS provider abstraction

**Files:**
- Create: `comedy-duo/src/comedy_duo/tts.py`
- Create: `comedy-duo/tests/test_tts.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_tts.py
import pytest
from unittest.mock import AsyncMock, patch
from comedy_duo.tts import MacSayProvider, ElevenLabsProvider, get_tts_provider
from comedy_duo.models import Settings


class TestMacSayProvider:
    @pytest.mark.asyncio
    async def test_speak_calls_subprocess(self):
        provider = MacSayProvider()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_sub:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_sub.return_value = mock_process
            await provider.speak("Hello world", voice="Daniel")
            mock_sub.assert_called_once()
            args = mock_sub.call_args[0]
            assert "say" in args
            assert "Hello world" in args


class TestGetTTSProvider:
    def test_returns_mac_say_by_default(self):
        settings = Settings(tts_provider="say")
        provider = get_tts_provider(settings)
        assert isinstance(provider, MacSayProvider)

    def test_returns_elevenlabs_when_configured(self):
        settings = Settings(tts_provider="elevenlabs")
        with patch.dict("os.environ", {"ELEVENLABS_API_KEY": "test-key"}):
            provider = get_tts_provider(settings)
            assert isinstance(provider, ElevenLabsProvider)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd comedy-duo && python -m pytest tests/test_tts.py -v`
Expected: FAIL

- [ ] **Step 3: Implement TTS providers**

```python
# src/comedy_duo/tts.py
import asyncio
import os
from abc import ABC, abstractmethod

import httpx

from comedy_duo.models import Settings

DEFAULT_VOICES = {
    "carra": "Daniel",
    "nev": "Oliver",
}


class TTSProvider(ABC):
    @abstractmethod
    async def speak(self, text: str, voice: str | None = None) -> None: ...


class MacSayProvider(TTSProvider):
    async def speak(self, text: str, voice: str | None = None) -> None:
        cmd = ["say"]
        if voice:
            cmd.extend(["-v", voice])
        cmd.append(text)
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()


class ElevenLabsProvider(TTSProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"

    async def speak(self, text: str, voice: str | None = None) -> None:
        if not voice:
            return
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech/{voice}",
                headers={"xi-api-key": self.api_key},
                json={"text": text, "model_id": "eleven_monolingual_v1"},
                timeout=30.0,
            )
            response.raise_for_status()
            process = await asyncio.create_subprocess_exec(
                "afplay", "-",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate(input=response.content)


def get_tts_provider(settings: Settings) -> TTSProvider:
    if settings.tts_provider == "elevenlabs":
        api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        return ElevenLabsProvider(api_key)
    return MacSayProvider()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd comedy-duo && python -m pytest tests/test_tts.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add comedy-duo/src/comedy_duo/tts.py comedy-duo/tests/test_tts.py
git commit -m "feat(comedy-duo): add TTS abstraction with ElevenLabs + macOS say fallback"
```

---

### Task 7: Twitch chat client

**Files:**
- Create: `comedy-duo/src/comedy_duo/twitch_chat.py`
- Create: `comedy-duo/tests/test_twitch_chat.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_twitch_chat.py
import pytest
from unittest.mock import AsyncMock
from comedy_duo.twitch_chat import TwitchChatClient, format_irc_message


class TestFormatIRCMessage:
    def test_privmsg_format(self):
        msg = format_irc_message("testchannel", "Hello world!")
        assert msg == "PRIVMSG #testchannel :Hello world!\r\n"

    def test_strips_channel_hash(self):
        msg = format_irc_message("#testchannel", "Hello!")
        assert msg == "PRIVMSG #testchannel :Hello!\r\n"


class TestTwitchChatClient:
    def test_init(self):
        client = TwitchChatClient(
            username="bot_name",
            token="oauth:xxx",
            channel="testchannel",
        )
        assert client.username == "bot_name"
        assert client.channel == "testchannel"

    @pytest.mark.asyncio
    async def test_send_message(self):
        client = TwitchChatClient(
            username="bot_name",
            token="oauth:xxx",
            channel="testchannel",
        )
        mock_ws = AsyncMock()
        client._ws = mock_ws
        client._connected = True
        await client.send("Hello chat!")
        mock_ws.send.assert_called_once_with("PRIVMSG #testchannel :Hello chat!\r\n")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd comedy-duo && python -m pytest tests/test_twitch_chat.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Twitch IRC client**

```python
# src/comedy_duo/twitch_chat.py
import asyncio
import logging

import websockets

logger = logging.getLogger(__name__)

TWITCH_IRC_URL = "wss://irc-ws.chat.twitch.tv:443"


def format_irc_message(channel: str, text: str) -> str:
    channel = channel.lstrip("#")
    return f"PRIVMSG #{channel} :{text}\r\n"


class TwitchChatClient:
    def __init__(self, username: str, token: str, channel: str):
        self.username = username
        self.token = token
        self.channel = channel.lstrip("#")
        self._ws = None
        self._connected = False

    async def connect(self) -> None:
        self._ws = await websockets.connect(TWITCH_IRC_URL)
        await self._ws.send(f"PASS {self.token}\r\n")
        await self._ws.send(f"NICK {self.username}\r\n")
        await self._ws.send(f"JOIN #{self.channel}\r\n")
        self._connected = True
        logger.info(f"[{self.username}] Connected to #{self.channel}")
        asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        try:
            async for message in self._ws:
                if message.startswith("PING"):
                    await self._ws.send("PONG :tmi.twitch.tv\r\n")
        except websockets.ConnectionClosed:
            self._connected = False
            logger.warning(f"[{self.username}] Disconnected from Twitch")

    async def send(self, text: str) -> None:
        if not self._connected or not self._ws:
            logger.warning(f"[{self.username}] Not connected, skipping message")
            return
        msg = format_irc_message(self.channel, text)
        await self._ws.send(msg)

    async def disconnect(self) -> None:
        if self._ws:
            await self._ws.close()
            self._connected = False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd comedy-duo && python -m pytest tests/test_twitch_chat.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add comedy-duo/src/comedy_duo/twitch_chat.py comedy-duo/tests/test_twitch_chat.py
git commit -m "feat(comedy-duo): add Twitch IRC chat client with WebSocket connection"
```

---

### Task 8: OBS overlay (WebSocket server + HTML/CSS/JS)

**Files:**
- Create: `comedy-duo/src/comedy_duo/overlay_server.py`
- Create: `comedy-duo/overlay/index.html`
- Create: `comedy-duo/overlay/style.css`
- Create: `comedy-duo/overlay/script.js`
- Create: `comedy-duo/tests/test_overlay_server.py`

- [ ] **Step 1: Write failing tests for overlay server**

```python
# tests/test_overlay_server.py
import pytest
import json
from unittest.mock import AsyncMock
from comedy_duo.overlay_server import OverlayServer


class TestOverlayServer:
    def test_init(self):
        server = OverlayServer(host="localhost", port=3003)
        assert server.host == "localhost"
        assert server.port == 3003
        assert len(server.clients) == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_clients(self):
        server = OverlayServer(host="localhost", port=3003)
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()
        server.clients = {mock_client1, mock_client2}

        await server.broadcast({"bot": "Carra", "text": "GET IN!"})

        expected = json.dumps({"bot": "Carra", "text": "GET IN!"})
        mock_client1.send.assert_called_once_with(expected)
        mock_client2.send.assert_called_once_with(expected)

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_clients(self):
        server = OverlayServer(host="localhost", port=3003)
        dead_client = AsyncMock()
        dead_client.send.side_effect = Exception("connection closed")
        server.clients = {dead_client}

        await server.broadcast({"bot": "Nev", "text": "Told you."})
        assert dead_client not in server.clients
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd comedy-duo && python -m pytest tests/test_overlay_server.py -v`
Expected: FAIL

- [ ] **Step 3: Implement overlay WebSocket server**

```python
# src/comedy_duo/overlay_server.py
import json
import logging

import websockets

logger = logging.getLogger(__name__)


class OverlayServer:
    def __init__(self, host: str = "localhost", port: int = 3003):
        self.host = host
        self.port = port
        self.clients: set = set()

    async def _handler(self, websocket):
        self.clients.add(websocket)
        logger.info(f"Overlay client connected ({len(self.clients)} total)")
        try:
            async for _ in websocket:
                pass
        finally:
            self.clients.discard(websocket)
            logger.info(f"Overlay client disconnected ({len(self.clients)} total)")

    async def broadcast(self, data: dict) -> None:
        message = json.dumps(data)
        dead = set()
        for client in self.clients:
            try:
                await client.send(message)
            except Exception:
                dead.add(client)
        self.clients -= dead

    async def start(self) -> None:
        server = await websockets.serve(self._handler, self.host, self.port)
        logger.info(f"Overlay WebSocket server on ws://{self.host}:{self.port}")
        await server.wait_closed()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd comedy-duo && python -m pytest tests/test_overlay_server.py -v`
Expected: All PASS

- [ ] **Step 5: Create the OBS overlay HTML/CSS/JS**

`overlay/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carra and Nev</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="ticker"></div>
    <script src="script.js"></script>
</body>
</html>
```

`overlay/style.css`:
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    background: transparent;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    overflow: hidden;
}

#ticker {
    position: fixed;
    right: 20px;
    bottom: 20px;
    width: 360px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 90vh;
    overflow: hidden;
}

.message {
    padding: 12px 16px;
    border-radius: 12px;
    animation: slideIn 0.3s ease-out;
    opacity: 1;
    transition: opacity 0.5s ease-out;
    backdrop-filter: blur(10px);
}

.message.carra {
    background: rgba(220, 38, 38, 0.85);
    color: white;
    border-left: 4px solid #fca5a5;
}

.message.nev {
    background: rgba(37, 99, 235, 0.85);
    color: white;
    border-left: 4px solid #93c5fd;
}

.message .bot-name {
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
    opacity: 0.8;
}

.message .bot-text {
    font-size: 15px;
    line-height: 1.4;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.message.fading {
    opacity: 0;
}
```

`overlay/script.js`:
```javascript
const WS_URL = "ws://localhost:3003";
const MAX_MESSAGES = 5;
const MESSAGE_TTL = 15000;

const ticker = document.getElementById("ticker");

function connect() {
    const ws = new WebSocket(WS_URL);

    ws.onopen = function() {
        console.log("Connected to commentary server");
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        addMessage(data.bot, data.text);
    };

    ws.onclose = function() {
        console.log("Disconnected, reconnecting in 3s...");
        setTimeout(connect, 3000);
    };

    ws.onerror = function(err) {
        console.error("WebSocket error:", err);
    };
}

function addMessage(botName, text) {
    const el = document.createElement("div");
    const cssClass = botName.toLowerCase();
    el.className = "message " + cssClass;
    el.innerHTML =
        '<div class="bot-name">' + escapeHtml(botName) + '</div>' +
        '<div class="bot-text">' + escapeHtml(text) + '</div>';
    ticker.appendChild(el);

    while (ticker.children.length > MAX_MESSAGES) {
        ticker.removeChild(ticker.firstChild);
    }

    setTimeout(function() {
        el.classList.add("fading");
        setTimeout(function() { el.remove(); }, 500);
    }, MESSAGE_TTL);
}

function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

connect();
```

- [ ] **Step 6: Commit**

```bash
git add comedy-duo/src/comedy_duo/overlay_server.py comedy-duo/tests/test_overlay_server.py comedy-duo/overlay/
git commit -m "feat(comedy-duo): add OBS overlay with WebSocket server and ticker UI"
```

---

## Chunk 5: Control Panel + Orchestrator + Entry Point

### Task 9: Control panel (FastAPI)

**Files:**
- Create: `comedy-duo/src/comedy_duo/control_panel.py`
- Create: `comedy-duo/tests/test_control_panel.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_control_panel.py
import pytest
from fastapi.testclient import TestClient
from comedy_duo.control_panel import create_app
from comedy_duo.models import Settings


@pytest.fixture
def app():
    settings = Settings()
    return create_app(settings, event_callback=lambda e: None)


@pytest.fixture
def client(app):
    return TestClient(app)


class TestControlPanel:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_inject_event(self, client):
        response = client.post("/event", json={"text": "she dropped the database"})
        assert response.status_code == 200
        assert response.json()["status"] == "injected"

    def test_get_settings(self, client):
        response = client.get("/settings")
        assert response.status_code == 200
        assert "cooldown_seconds" in response.json()

    def test_update_settings(self, client):
        response = client.patch("/settings", json={"cooldown_seconds": 60})
        assert response.status_code == 200
        assert response.json()["cooldown_seconds"] == 60

    def test_kill_switch(self, client):
        response = client.post("/kill")
        assert response.status_code == 200

    def test_control_page_renders(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd comedy-duo && python -m pytest tests/test_control_panel.py -v`
Expected: FAIL

- [ ] **Step 3: Implement the control panel**

```python
# src/comedy_duo/control_panel.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd comedy-duo && python -m pytest tests/test_control_panel.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add comedy-duo/src/comedy_duo/control_panel.py comedy-duo/tests/test_control_panel.py
git commit -m "feat(comedy-duo): add FastAPI control panel with event injection and kill switch"
```

---

### Task 10: Orchestrator

**Files:**
- Create: `comedy-duo/src/comedy_duo/orchestrator.py`
- Create: `comedy-duo/tests/test_orchestrator.py`

The orchestrator is the main loop tying everything together: watches the session log, detects events, applies cooldowns, generates commentary, and fans out to all outputs.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_orchestrator.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd comedy-duo && python -m pytest tests/test_orchestrator.py -v`
Expected: FAIL

- [ ] **Step 3: Implement orchestrator**

```python
# src/comedy_duo/orchestrator.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd comedy-duo && python -m pytest tests/test_orchestrator.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add comedy-duo/src/comedy_duo/orchestrator.py comedy-duo/tests/test_orchestrator.py
git commit -m "feat(comedy-duo): add orchestrator with cooldown, event queue, and fan-out"
```

---

### Task 11: Entry point

**Files:**
- Create: `comedy-duo/src/comedy_duo/__main__.py`

- [ ] **Step 1: Implement the entry point**

```python
# src/comedy_duo/__main__.py
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
```

- [ ] **Step 2: Test it starts without crashing**

Run: `cd comedy-duo && timeout 5 python -m comedy_duo 2>&1 || true`
Expected: Starts up, prints config info, then times out. No crash.

- [ ] **Step 3: Commit**

```bash
git add comedy-duo/src/comedy_duo/__main__.py
git commit -m "feat(comedy-duo): add entry point - python -m comedy_duo"
```

---

### Task 12: Run full test suite and verify

- [ ] **Step 1: Run all tests**

Run: `cd comedy-duo && python -m pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 2: Final commit with any fixes**

If any tests needed fixing, commit the fixes:
```bash
git add -A comedy-duo/
git commit -m "fix(comedy-duo): resolve any test issues from integration"
```
