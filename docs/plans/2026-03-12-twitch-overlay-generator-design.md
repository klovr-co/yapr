# Twitch Overlay Generator Skill — Design

## Goal

A skill that generates complete, cohesive Twitch stream overlay packages. User provides a theme prompt + customization options, and gets OBS-ready HTML browser sources with AI-generated art via Google Gemini API (nanobanana).

## Customization Controls

- **Color palette** — predefined presets (pastel, dark, neon, earth) or custom hex codes
- **Art style** — kawaii, chibi, pixel art, watercolor
- **Layout density** — minimal, decorated, maximalist
- **Stream type** — gaming, just chatting, art, music

## Overlay Pieces by Stream Type

| Stream Type  | Pieces                                                                                  |
|--------------|-----------------------------------------------------------------------------------------|
| Gaming       | Webcam frame, alerts (follow/sub/donation), Starting Soon, BRB, chat box frame, decorations |
| Just Chatting| Webcam frame, alerts, Starting Soon, BRB, lower-third nameplate, decorative borders     |
| Art          | Webcam frame (small), alerts, canvas frame, tool palette decoration, Starting Soon, BRB |
| Music        | Webcam frame, alerts, Starting Soon, BRB, now-playing widget frame, visualizer border   |

## Workflow

1. User provides theme prompt + customization choices
2. Skill builds optimized image generation prompts per overlay piece
3. `generate_assets.py` calls Gemini API → saves transparent PNGs
4. `assemble_overlay.py` injects PNGs into HTML/CSS templates → outputs OBS-ready folder

## Skill Structure

```
twitch-overlay-generator/
├── SKILL.md
├── scripts/
│   ├── generate_assets.py        # Gemini API calls → PNGs
│   └── assemble_overlay.py       # PNGs + templates → HTML browser sources
├── references/
│   ├── prompt-templates.md       # Per-piece, per-style prompt templates
│   └── overlay-specs.md          # Dimensions, OBS requirements, animation specs
└── assets/
    └── html-templates/
        ├── webcam-frame.html
        ├── alert-box.html
        ├── scene-screen.html
        └── decorations.html
```

## Output

```
my-stream-overlay/
├── assets/               # Generated PNGs
├── webcam-frame.html     # OBS browser source
├── alerts.html           # OBS browser source
├── starting-soon.html    # OBS scene
├── brb.html              # OBS scene
├── decorations.html      # OBS browser source
└── config.json           # Settings for regeneration
```

## Prompt Strategy

Base prompt per piece, modified by art style:

- **Kawaii**: "cute chibi style, round soft edges, pastel shading, big sparkly eyes on decorative elements"
- **Pixel art**: "16-bit pixel art style, crisp edges, dithered shading, retro game aesthetic"
- **Watercolor**: "soft watercolor painting, bleeding edges, gentle color washes, paper texture"
- **Chibi**: "chibi anime style, exaggerated proportions, bold outlines, cell shading"

All prompts include: `"transparent background, PNG, overlay asset for streaming, [COLOR PALETTE]"`

## Layout Density

- **Minimal**: thin frame, small alerts, no floating decorations
- **Decorated**: medium frame with accents, standard alerts, 3-5 floating elements
- **Maximalist**: ornate frame, large alerts, 10+ floating elements, border decorations

## Animations (pure CSS)

- Floating elements: `@keyframes float` with randomized delays
- Alert pop-ins: scale + fade with bounce easing
- Scene screens: gentle text pulse, slow-rotating decorations
- Sparkle effects: opacity keyframes on star/dot elements
