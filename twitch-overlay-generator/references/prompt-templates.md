# Prompt Templates

Curated prompts for generating overlay assets via Gemini API (nanobanana). Each template combines a **piece prompt** with a **style modifier** and **palette injection**.

## Prompt Structure

```
{style_modifier}, {piece_prompt}, color palette: {hex_codes}, transparent background, PNG, overlay asset for streaming, isolated element, no background scene
```

## Style Modifiers

| Style | Modifier |
|-------|----------|
| kawaii | "cute kawaii style, round soft edges, pastel shading, big sparkly eyes on decorative elements, adorable and cheerful" |
| chibi | "chibi anime style, exaggerated cute proportions, bold clean outlines, cell shading, playful expressions" |
| pixel-art | "16-bit pixel art style, crisp edges, dithered shading, retro game aesthetic, clean pixel grid" |
| watercolor | "soft watercolor painting style, bleeding edges, gentle color washes, subtle paper texture, dreamy feel" |

## Piece Prompts

### Webcam Frame
```
decorative frame border for a webcam overlay, rectangular with rounded corners, ornamental {theme_elements} along the edges, inner cutout for video feed, {density_detail}
```

Density details:
- minimal: "thin elegant border, subtle accents"
- decorated: "medium border with floral/star accents, small character peeking from corner"
- maximalist: "ornate thick border covered in decorations, characters, sparkles, and {theme_elements}"

### Alert Box
```
notification popup frame for stream alerts, rectangular banner shape, space for text in center, {theme_elements} decorating the edges, celebratory feel, {density_detail}
```

### Starting Soon Screen
```
full screen "Starting Soon" splash graphic, centered text area, {theme_elements} filling the composition, inviting and warm mood, {density_detail}
```

### BRB Screen
```
full screen "Be Right Back" splash graphic, centered text area, {theme_elements} in a relaxed calm arrangement, cozy mood, {density_detail}
```

### Chat Box Frame
```
decorative border frame for a chat widget, tall rectangular shape, {theme_elements} along the top and sides, readable and not too busy inside, {density_detail}
```

### Lower Third Nameplate
```
horizontal banner for streamer name, lower third overlay style, {theme_elements} as accents, space for name text on left side, {density_detail}
```

### Floating Decorations
```
small isolated decorative element: {specific_element}, cute and simple, works as a floating overlay piece, {density_detail}
```

Generate multiple variations:
- minimal: 0 floating elements
- decorated: 3-5 elements (stars, hearts, small characters, sparkles)
- maximalist: 10+ elements (full set of themed decorations)

### Canvas Frame (Art streams)
```
decorative picture frame for an art canvas area, large rectangular cutout, {theme_elements} as frame decoration, artistic and inspiring, {density_detail}
```

### Now Playing Frame (Music streams)
```
small decorative frame for a now-playing music widget, horizontal shape, musical notes and {theme_elements} as accents, {density_detail}
```

## Palette Injection

Pass hex codes directly in the prompt:

```
color palette: primary #{hex1}, secondary #{hex2}, accent #{hex3}, background #{hex4}
```

### Preset Palettes

| Palette | Primary | Secondary | Accent | Background |
|---------|---------|-----------|--------|------------|
| pastel | #FFB5E8 | #B5D8FF | #BFFCC6 | #FFF5BA |
| dark | #2D1B69 | #1B3A4B | #FF6B9D | #0D0D0D |
| neon | #FF00FF | #00FFFF | #FFFF00 | #1A0A2E |
| earth | #8B7355 | #556B2F | #DAA520 | #F5F0E8 |
