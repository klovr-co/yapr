# Comedy Duo: Carra & Nev — Live Coding Commentary Bots

## Overview

Two AI-powered Twitch bots that watch Claude Code sessions and provide live pundit-style commentary on a vibe coding livestream. Inspired by Carragher & Neville's Monday Night Football dynamic.

- **Carra** — the passionate cheerleader. Defends every coding decision, celebrates wins, devastated by failures.
- **Nev** — the analytical wind-up merchant. Measured, tactical, always predicted the bug before it happened.

## Output Channels

Commentary appears in three places simultaneously:

1. **Twitch chat** — two separate bot accounts posting in the stream chat
2. **OBS overlay** — styled ticker feed (browser source) on one side of the screen
3. **Text-to-speech** — two distinct AI voices (ElevenLabs), with macOS `say` as fallback

## Architecture

```
Claude Code JSONL logs
        │
        ▼
┌─────────────┐     ┌──────────────┐
│   Watcher   │────▶│  Orchestrator │◀──── Manual Event Input
│  (tails log)│     │  (cooldowns,  │      (CLI + web form)
└─────────────┘     │   routing)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │    Engine     │
                    │ (Pydantic AI) │
                    │ Carra + Nev  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        Twitch Chat   OBS Overlay      TTS
        (IRC x2)     (WebSocket)   (ElevenLabs/say)
```

## Session Watcher

Tails the active Claude Code JSONL session file and classifies moments by comedy potential.

**Log location:** `~/.claude/projects/<project>/sessions/` (JSONL files)

**Monitoring:** File polling via `watchfiles` (cross-platform, simple)

### Event Tiers

| Tier | Triggers | Response |
|------|----------|----------|
| **HOT** | Errors, test failures, Claude apologizing, user correcting Claude, big deletions, manual events | Full duo exchange |
| **WARM** | New file created, dependency installed, refactor, commit | LLM decides: solo or duo |
| **COLD** | File reads, routine edits, config changes | Ignored |

### Cooldown System

- Minimum 30 seconds between commentary bursts (configurable)
- HOT events override cooldown
- Stacked events during cooldown get batched into one commentary

## Commentary Engine

Two Pydantic AI agents with shared conversation history. Personalities loaded from editable YAML config files.

### Bot Config (`config/carra.yaml`, `config/nev.yaml`)

```yaml
name: "Carra"
role: "cheerleader"
voice_id: "elevenlabs-voice-id-here"
personality: |
  You are Carra, a passionate football pundit commentating on a live coding stream.
  You defend every coding decision like it's a last-minute tackle.
  You get personally invested, devastated by errors, celebrate hard when tests pass.
  Style: emotional, loyal, uses football metaphors.
example_lines:
  - "She KNOWS what she's doing here, that's class"
  - "Oh no... no no no... that's heartbreaking that"
  - "GET IN! Tests passing, every single one!"
```

### Shared Config (`config/settings.yaml`)

```yaml
cooldown_seconds: 30
hot_events_override_cooldown: true
tts_enabled: true
twitch_chat_enabled: true
overlay_enabled: true
duo_delay_seconds: 4
overlay_message_ttl_seconds: 15
overlay_max_visible: 5
tts_provider: "say"  # "elevenlabs" or "say"
control_panel_port: 3001
overlay_port: 3002
websocket_port: 3003
```

### Commentary Flow

1. Event detected -> build context payload (what happened, recent session history, last 5 bot messages)
2. LLM decides: solo (which bot?) or duo exchange
3. If duo: generate Carra first, append to shared context, then generate Nev's response
4. Fan out to all three output channels simultaneously

## Output Layer

### Twitch Chat

- Two separate Twitch bot accounts, each with its own OAuth token
- Connect via WebSocket to `irc-ws.chat.twitch.tv`
- Carra posts first, Nev follows after configurable delay (default 4s)

### OBS Overlay

- Static HTML/CSS/JS served from `overlay/` on configured port
- Added as a Browser Source in OBS
- Connects via WebSocket to the Python backend
- Styled ticker feed: messages slide in, fade out after TTL
- Color-coded per bot (configurable)
- Shows bot name + avatar + message in chat-bubble rows
- Auto-scrolls, keeps last N messages visible

### Text-to-Speech

- **ElevenLabs** (primary): two different voice IDs, one per bot config
- **macOS `say`** (fallback): two different system voices for local testing
- Audio queued sequentially: Carra speaks, then Nev
- Plays through designated audio output for OBS capture
- Toggleable on/off mid-stream

### Manual Control Panel (`localhost:3001`)

- Inject custom events (text input)
- Toggle TTS / chat / overlay on/off independently
- Adjust cooldown in real time
- Reload bot configs without restart
- Kill switch: silence both bots instantly

## Project Structure

```
comedy-duo/
├── config/
│   ├── settings.yaml
│   ├── carra.yaml
│   └── nev.yaml
├── src/
│   ├── __init__.py
│   ├── __main__.py             # Entry point
│   ├── watcher.py              # Tails Claude Code JSONL, classifies events
│   ├── engine.py               # Pydantic AI agents, generates commentary
│   ├── twitch_chat.py          # IRC connection, posts as two bot accounts
│   ├── tts.py                  # TTS provider abstraction (ElevenLabs / say)
│   ├── overlay_server.py       # WebSocket server for OBS overlay
│   ├── control_panel.py        # FastAPI web UI for manual controls
│   └── orchestrator.py         # Main loop: watcher -> engine -> outputs
├── overlay/
│   ├── index.html              # OBS browser source
│   ├── style.css               # Ticker styling, colours, animations
│   └── script.js               # WebSocket client, message rendering
├── pyproject.toml
└── README.md
```

## Dependencies

- `pydantic-ai` — LLM agents (model-agnostic)
- `websockets` — overlay WebSocket connection
- `httpx` — ElevenLabs API calls
- `watchfiles` — file monitoring for session logs
- `fastapi` + `uvicorn` — control panel web server
- `pyyaml` — config loading
- `python-dotenv` — secrets management (API keys, OAuth tokens)

## Twitch Bot Account Setup

1. Create two regular Twitch accounts (separate emails) for Carra and Nev
2. For each account, go to https://dev.twitch.tv/console
3. Register an application (OAuth redirect: `http://localhost:3000`)
4. Generate OAuth tokens with scopes: `chat:read chat:edit`
5. Store credentials in `.env`:
   ```
   CARRA_TWITCH_TOKEN=oauth:xxx
   CARRA_TWITCH_USERNAME=carra_bot
   NEV_TWITCH_TOKEN=oauth:xxx
   NEV_TWITCH_USERNAME=nev_bot
   TWITCH_CHANNEL=your_channel
   ELEVENLABS_API_KEY=xxx  # optional
   ```

## Startup

Single command: `python -m comedy_duo`

1. Loads configs from `config/`
2. Connects to Twitch IRC as both bot accounts
3. Starts WebSocket server for overlay
4. Starts control panel on configured port
5. Begins tailing the active Claude Code session
6. Listens for events and orchestrates commentary
