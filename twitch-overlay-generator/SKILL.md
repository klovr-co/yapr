---
name: twitch-overlay-generator
description: Use when generating Twitch stream overlay packages — webcam frames, alerts, scene screens (Starting Soon, BRB), and decorative elements. Triggers on requests for stream overlays, OBS browser sources, streaming graphics, or Twitch visual assets. Uses Google Gemini API (nanobanana) for AI image generation and assembles into OBS-ready HTML/CSS browser sources.
---

# Twitch Overlay Generator

Generate complete, cohesive Twitch stream overlay packages from a theme prompt. Produces AI-generated art via Gemini API (nanobanana) assembled into OBS-ready HTML browser sources.

## Workflow

1. Run `scripts/generate_overlay.py` — handles everything in one command
2. Interactive mode walks through theme, style, palette, density, stream type
3. Auto-installs dependencies, prompts for API key, saves to `.env`
4. Generates images via Gemini API + assembles OBS-ready HTML files

## Config Options

| Option | Values |
|--------|--------|
| **Color palette** | `pastel`, `dark`, `neon`, `earth`, or custom hex array |
| **Art style** | `kawaii`, `chibi`, `pixel-art`, `watercolor` |
| **Layout density** | `minimal`, `decorated`, `maximalist` |
| **Stream type** | `gaming`, `just-chatting`, `art`, `music` |

## Quick Start

```bash
# Interactive mode — just run it
python3 scripts/generate_overlay.py

# Or pass everything as flags
python3 scripts/generate_overlay.py \
  --theme "cozy coffee shop with a cat mascot" \
  --style kawaii --palette pastel \
  --density decorated --stream-type just-chatting
```

No setup needed — auto-installs `google-genai` and `Pillow`, prompts for API key on first run and saves it to `.env`.

## Overlay Pieces by Stream Type

See [references/overlay-specs.md](references/overlay-specs.md) for full dimensions and animation specs per piece.

| Stream Type   | Pieces |
|---------------|--------|
| Gaming        | Webcam frame, alerts, Starting Soon, BRB, chat box frame, decorations |
| Just Chatting | Webcam frame, alerts, Starting Soon, BRB, lower-third nameplate, borders |
| Art           | Webcam frame (small), alerts, canvas frame, tool palette deco, Starting Soon, BRB |
| Music         | Webcam frame, alerts, Starting Soon, BRB, now-playing frame, visualizer border |

## Prompt Engineering

See [references/prompt-templates.md](references/prompt-templates.md) for curated prompts per piece and style.

Key principles:
- Every prompt ends with `"transparent background, PNG, overlay asset for streaming"`
- Color palette hex codes are injected into every prompt
- Style modifiers are prepended to ensure visual consistency across all pieces
- Request `"isolated element, no background scene"` to keep assets composable

## OBS Setup

Each HTML file is a standalone browser source. In OBS:
1. Add Browser Source
2. Point to the `.html` file (use `file://` path)
3. Set dimensions per the overlay-specs reference
4. Check "Shutdown source when not visible" for performance

## Common Mistakes

- **Opaque backgrounds** — always verify PNGs have transparency; re-prompt with "no background, transparent, isolated element" if needed
- **Inconsistent style** — generate all pieces in one batch to maintain visual coherence
- **Oversized assets** — keep webcam frames under 500x500, alerts under 400x300 for OBS performance
- **Missing API key** — set `GOOGLE_API_KEY` env var before running generate script
