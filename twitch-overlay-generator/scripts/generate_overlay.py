#!/usr/bin/env python3
"""
Twitch Overlay Generator — one command, zero setup.

Generates a complete set of cute stream overlays using Gemini image generation,
then assembles them into OBS-ready HTML browser sources.

Usage:
  python3 generate_overlay.py                  # Interactive mode
  python3 generate_overlay.py --theme "cozy cat cafe" --style kawaii
"""

import json
import os
import random
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Auto-install dependencies
# ---------------------------------------------------------------------------
def ensure_deps():
    missing = []
    try:
        from google import genai  # noqa: F401
    except ImportError:
        missing.append("google-genai")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        missing.append("Pillow")
    try:
        from rembg import remove  # noqa: F401
    except ImportError:
        missing.append("rembg[cpu]")

    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "-q"])
        print("Done!\n")


ensure_deps()

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MODEL = "gemini-3.1-flash-image-preview"

PALETTES = {
    "pastel":  {"primary": "#FFB5E8", "secondary": "#B5D8FF", "accent": "#BFFCC6", "background": "#FFF5BA"},
    "dark":    {"primary": "#2D1B69", "secondary": "#1B3A4B", "accent": "#FF6B9D", "background": "#0D0D0D"},
    "neon":    {"primary": "#FF00FF", "secondary": "#00FFFF", "accent": "#FFFF00", "background": "#1A0A2E"},
    "earth":   {"primary": "#8B7355", "secondary": "#556B2F", "accent": "#DAA520", "background": "#F5F0E8"},
}

STYLES = {
    "kawaii":     "cute kawaii style, round soft edges, pastel shading, big sparkly eyes on decorative elements, adorable and cheerful",
    "chibi":      "chibi anime style, exaggerated cute proportions, bold clean outlines, cell shading, playful expressions",
    "pixel-art":  "16-bit pixel art style, crisp edges, dithered shading, retro game aesthetic, clean pixel grid",
    "watercolor": "soft watercolor painting style, bleeding edges, gentle color washes, subtle paper texture, dreamy feel",
}

DENSITIES = {
    "minimal":    "thin elegant border, subtle accents, clean and simple",
    "decorated":  "medium border with floral or star accents, small character peeking from corner",
    "maximalist": "ornate thick border covered in decorations, characters, sparkles, and themed elements",
}

STREAM_PIECES = {
    "gaming":       ["webcam-frame", "alert-box", "starting-soon", "brb", "chat-box-frame", "decorations"],
    "just-chatting": ["webcam-frame", "alert-box", "starting-soon", "brb", "lower-third", "decorations"],
    "art":          ["webcam-frame-small", "alert-box", "canvas-frame", "starting-soon", "brb", "decorations"],
    "music":        ["webcam-frame", "alert-box", "starting-soon", "brb", "now-playing-frame", "decorations"],
}

PIECE_PROMPTS = {
    "webcam-frame":      "decorative frame border for a webcam overlay, rectangular with rounded corners, ornamental {theme} along the edges, inner cutout for video feed",
    "webcam-frame-small": "small decorative frame border for a webcam overlay, compact rectangular with rounded corners, ornamental {theme} along the edges, inner cutout for video feed",
    "alert-box":         "notification popup frame for stream alerts, rectangular banner shape, space for text in center, {theme} decorating the edges, celebratory feel",
    "starting-soon":     'full screen "Starting Soon" splash graphic, centered text area reading "Starting Soon", {theme} filling the composition, inviting and warm mood',
    "brb":               'full screen "Be Right Back" splash graphic, centered text area reading "BRB", {theme} in a relaxed calm arrangement, cozy mood',
    "chat-box-frame":    "decorative border frame for a chat widget, tall rectangular shape, {theme} along the top and sides, readable and not too busy inside",
    "lower-third":       "horizontal banner for streamer name, lower third overlay style, {theme} as accents, space for name text on left side",
    "canvas-frame":      "decorative picture frame for an art canvas area, large rectangular cutout, {theme} as frame decoration, artistic and inspiring",
    "now-playing-frame": "small decorative frame for a now-playing music widget, horizontal shape, musical notes and {theme} as accents",
    "decorations":       "set of small isolated cute decorative elements: stars, hearts, sparkles, and {theme}, each element separate, works as floating overlay pieces",
}

PIECE_DIMS = {
    "webcam-frame": (480, 480), "webcam-frame-small": (320, 320),
    "alert-box": (400, 250), "starting-soon": (1920, 1080), "brb": (1920, 1080),
    "chat-box-frame": (400, 600), "lower-third": (500, 100),
    "canvas-frame": (1200, 800), "now-playing-frame": (350, 100), "decorations": (800, 800),
}

PIECE_ASPECT = {
    "webcam-frame": "1:1", "webcam-frame-small": "1:1",
    "alert-box": "16:9", "starting-soon": "16:9", "brb": "16:9",
    "chat-box-frame": "9:16", "lower-third": "16:9",
    "canvas-frame": "16:9", "now-playing-frame": "16:9", "decorations": "1:1",
}

DECO_COUNT = {"minimal": 0, "decorated": 5, "maximalist": 12}


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------
def pick(label: str, options: list[str], default: str = None) -> str:
    print(f"\n{label}")
    for i, opt in enumerate(options, 1):
        marker = " (default)" if opt == default else ""
        print(f"  {i}. {opt}{marker}")
    while True:
        raw = input(f"Pick [1-{len(options)}]: ").strip()
        if not raw and default:
            return default
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            if raw in options:
                return raw
        print("  Invalid choice, try again.")


def interactive_config() -> dict:
    print("=== Twitch Overlay Generator ===\n")

    theme = input("Describe your stream theme (e.g. 'cozy cat cafe with plants'): ").strip()
    if not theme:
        theme = "cute cozy stream"

    style = pick("Art style:", list(STYLES.keys()), "kawaii")
    palette = pick("Color palette:", list(PALETTES.keys()), "pastel")
    density = pick("Layout density:", list(DENSITIES.keys()), "decorated")
    stream_type = pick("Stream type:", list(STREAM_PIECES.keys()), "gaming")

    output = input(f"\nOutput folder [./my-overlay]: ").strip() or "./my-overlay"

    return {
        "theme": theme, "style": style, "palette": palette,
        "density": density, "stream_type": stream_type, "output": output,
    }


# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------
def get_api_key() -> str:
    # Check env
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if key:
        return key

    # Check .env file in current dir
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("GOOGLE_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if key:
                    return key

    # Ask user
    print("\nNo GOOGLE_API_KEY found.")
    print("Get one free at: https://aistudio.google.com/apikey\n")
    key = input("Paste your API key: ").strip()
    if not key:
        print("Cannot continue without an API key.")
        sys.exit(1)

    save = input("Save to .env for next time? [Y/n]: ").strip().lower()
    if save != "n":
        with open(".env", "a") as f:
            f.write(f"\nGOOGLE_API_KEY={key}\n")
        print("Saved to .env")

    return key


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------
def build_prompt(piece: str, theme: str, style: str, palette: dict, density: str) -> str:
    style_mod = STYLES[style]
    density_detail = DENSITIES[density]
    piece_prompt = PIECE_PROMPTS[piece].format(theme=theme)
    palette_str = ", ".join(f"{k}: {v}" for k, v in palette.items())
    return (
        f"{style_mod}, {piece_prompt}, {density_detail}, "
        f"color palette: {palette_str}, "
        f"transparent background, PNG, overlay asset for streaming, isolated element, no background scene"
    )


def generate_image(client, prompt: str, piece: str) -> bool:
    """Generate image and save using PIL. Returns path or None."""
    aspect = PIECE_ASPECT.get(piece, "1:1")
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect,
                ),
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return part.inline_data.data
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


# ---------------------------------------------------------------------------
# HTML assembly
# ---------------------------------------------------------------------------
CSS_ANIMATIONS = """
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-15px) rotate(3deg); }
  75% { transform: translateY(10px) rotate(-2deg); }
}
@keyframes pop-in {
  0% { transform: scale(0); opacity: 0; }
  60% { transform: scale(1.15); opacity: 1; }
  80% { transform: scale(0.95); }
  100% { transform: scale(1); opacity: 1; }
}
@keyframes sparkle {
  0%, 100% { opacity: 0; transform: scale(0.5); }
  50% { opacity: 1; transform: scale(1.2); }
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
@keyframes slow-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
"""


def html_wrap(title: str, w: int, h: int, body: str, palette: dict, extra_css: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: {w}px; height: {h}px; overflow: hidden;
    background: transparent;
    font-family: 'Segoe UI', 'Noto Sans', sans-serif;
    --primary: {palette.get('primary', '#FFB5E8')};
    --secondary: {palette.get('secondary', '#B5D8FF')};
    --accent: {palette.get('accent', '#BFFCC6')};
    --bg: {palette.get('background', '#FFF5BA')};
  }}
  {CSS_ANIMATIONS}
  {extra_css}
</style>
</head>
<body>
{body}
</body>
</html>"""


def assemble_piece(piece: str, asset_rel: str, palette: dict, density: str) -> str:
    w, h = PIECE_DIMS.get(piece, (400, 400))
    # Full-screen scenes
    if piece in ("starting-soon", "brb"):
        w, h = 1920, 1080
        title = "Starting Soon" if piece == "starting-soon" else "Be Right Back"
        return html_wrap(title, w, h, f"""<div style="width:100%;height:100%;position:relative;display:flex;align-items:center;justify-content:center;">
  <img src="{asset_rel}" style="width:100%;height:100%;object-fit:cover;position:absolute;top:0;left:0;" />
  <div style="position:relative;z-index:1;font-size:64px;font-weight:bold;color:var(--primary);text-shadow:0 4px 8px rgba(0,0,0,0.4);animation:pulse 3s ease-in-out infinite;">{title}</div>
</div>""", palette)

    # Alert box
    if piece == "alert-box":
        return html_wrap("Alert", w, h, f"""<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;position:relative;animation:pop-in .5s cubic-bezier(.68,-.55,.265,1.55) forwards;">
  <img src="{asset_rel}" style="width:100%;height:100%;object-fit:contain;position:absolute;" />
  <div style="position:relative;z-index:1;font-size:24px;font-weight:bold;color:var(--primary);text-shadow:0 2px 4px rgba(0,0,0,.3);text-align:center;">New Follower!</div>
</div>""", palette)

    # Lower third
    if piece == "lower-third":
        return html_wrap("Lower Third", w, h, f"""<div style="width:100%;height:100%;position:relative;display:flex;align-items:center;">
  <img src="{asset_rel}" style="width:100%;height:100%;object-fit:contain;position:absolute;" />
  <div style="position:relative;z-index:1;font-size:28px;font-weight:bold;padding-left:20px;color:var(--primary);text-shadow:0 2px 4px rgba(0,0,0,.3);">StreamerName</div>
</div>""", palette)

    # Floating decorations
    if piece == "decorations":
        w, h = 1920, 1080
        count = DECO_COUNT.get(density, 5)
        if count == 0:
            return html_wrap("Decorations", w, h, "", palette)
        items = ""
        for _ in range(count):
            x, y = random.randint(5, 90), random.randint(5, 90)
            sz = random.randint(40, 80)
            dur = round(random.uniform(3, 6), 1)
            delay = round(random.uniform(0, 5), 1)
            items += f'<img src="{asset_rel}" style="position:absolute;left:{x}%;top:{y}%;width:{sz}px;height:{sz}px;object-fit:contain;animation:float {dur}s ease-in-out {delay}s infinite;opacity:.85;pointer-events:none;" />'
        return html_wrap("Decorations", w, h,
            f'<div style="width:100%;height:100%;position:relative;">{items}</div>', palette)

    # Default frame (webcam, chat, canvas, now-playing)
    return html_wrap(piece.replace("-", " ").title(), w, h, f"""<div style="width:{w}px;height:{h}px;position:relative;">
  <img src="{asset_rel}" style="width:100%;height:100%;object-fit:contain;position:absolute;top:0;left:0;pointer-events:none;" />
</div>""", palette)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Twitch Overlay Generator")
    parser.add_argument("--theme", help="Stream theme description")
    parser.add_argument("--style", choices=list(STYLES.keys()))
    parser.add_argument("--palette", default="pastel")
    parser.add_argument("--density", choices=list(DENSITIES.keys()), default="decorated")
    parser.add_argument("--stream-type", choices=list(STREAM_PIECES.keys()), default="gaming")
    parser.add_argument("--output", default="./my-overlay")
    args = parser.parse_args()

    # Interactive mode if no theme provided
    if not args.theme:
        cfg = interactive_config()
    else:
        cfg = {
            "theme": args.theme, "style": args.style or "kawaii",
            "palette": args.palette, "density": args.density,
            "stream_type": args.stream_type, "output": args.output,
        }

    api_key = get_api_key()
    client = genai.Client(api_key=api_key)

    palette = PALETTES.get(cfg["palette"], PALETTES["pastel"])
    pieces = STREAM_PIECES[cfg["stream_type"]]
    output_dir = Path(cfg["output"])
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*50}")
    print(f"Theme:   {cfg['theme']}")
    print(f"Style:   {cfg['style']}  |  Palette: {cfg['palette']}")
    print(f"Density: {cfg['density']}  |  Type: {cfg['stream_type']}")
    print(f"Pieces:  {', '.join(pieces)}")
    print(f"Output:  {output_dir}")
    print(f"{'='*50}\n")

    # Step 1: Generate images
    print("[1/2] Generating images...\n")
    generated = []
    for piece in pieces:
        print(f"  Creating {piece}...")
        prompt = build_prompt(piece, cfg["theme"], cfg["style"], palette, cfg["density"])
        image_data = generate_image(client, prompt, piece)
        if image_data:
            filepath = assets_dir / f"{piece}.png"
            # Remove background since Gemini can't generate true transparency
            from rembg import remove
            image_data = remove(image_data)
            filepath.write_bytes(image_data)
            generated.append(piece)
            print(f"    Saved {filepath} (background removed)")
        else:
            print(f"    Failed — will skip in assembly")

    # Step 2: Assemble HTML
    print(f"\n[2/2] Assembling HTML overlays...\n")
    for piece in generated:
        html = assemble_piece(piece, f"assets/{piece}.png", palette, cfg["density"])
        html_path = output_dir / f"{piece}.html"
        html_path.write_text(html)
        print(f"  Created {html_path}")

    # Save config for re-generation
    config = {**cfg, "palette_colors": palette, "generated": generated}
    (output_dir / "config.json").write_text(json.dumps(config, indent=2))

    # Summary
    print(f"\n{'='*50}")
    print(f"Done! {len(generated)}/{len(pieces)} overlays ready")
    print(f"\nTo use in OBS:")
    print(f"  1. Add Browser Source")
    print(f"  2. Point to any .html file in {output_dir}/")
    print(f"  3. Set width/height to match the overlay")
    print(f"  4. Check 'Shutdown source when not visible'")
    print(f"{'='*50}")

    if len(generated) < len(pieces):
        missing = set(pieces) - set(generated)
        print(f"\nMissing: {', '.join(missing)}")
        print("Run again to retry.")


if __name__ == "__main__":
    main()
