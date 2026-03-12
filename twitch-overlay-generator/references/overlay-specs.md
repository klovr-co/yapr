# Overlay Specs

Dimensions, OBS browser source settings, and CSS animation specs for each overlay piece.

## Dimensions

All overlays target 1920x1080 stream resolution.

| Piece | Width | Height | OBS Browser Source Size | Notes |
|-------|-------|--------|------------------------|-------|
| Webcam frame | 480 | 480 | 480x480 | Square for standard webcam |
| Alert box | 400 | 250 | 400x250 | Center-screen popup |
| Starting Soon | 1920 | 1080 | 1920x1080 | Full scene |
| BRB | 1920 | 1080 | 1920x1080 | Full scene |
| Chat box frame | 400 | 600 | 400x600 | Tall rectangle |
| Lower third | 500 | 100 | 500x100 | Horizontal banner |
| Floating decoration | 80 | 80 | per element | Individual small elements |
| Canvas frame | 1200 | 800 | 1200x800 | Large center area |
| Now playing | 350 | 100 | 350x100 | Small widget |
| Visualizer border | 1920 | 200 | 1920x200 | Bottom strip |

## CSS Animations

### Float (decorations)
```css
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-15px) rotate(3deg); }
  75% { transform: translateY(10px) rotate(-2deg); }
}
.float { animation: float var(--duration, 4s) ease-in-out infinite; }
```
Randomize `--duration` (3-6s) and `animation-delay` (0-5s) per element.

### Alert Pop-in
```css
@keyframes pop-in {
  0% { transform: scale(0); opacity: 0; }
  60% { transform: scale(1.15); opacity: 1; }
  80% { transform: scale(0.95); }
  100% { transform: scale(1); opacity: 1; }
}
.alert { animation: pop-in 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards; }
```

### Sparkle
```css
@keyframes sparkle {
  0%, 100% { opacity: 0; transform: scale(0.5); }
  50% { opacity: 1; transform: scale(1.2); }
}
.sparkle { animation: sparkle var(--duration, 2s) ease-in-out infinite; }
```

### Gentle Pulse (scene text)
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
.pulse { animation: pulse 3s ease-in-out infinite; }
```

### Slow Rotate (scene decorations)
```css
@keyframes slow-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.rotate { animation: slow-rotate 20s linear infinite; }
```

## Layout Density Specs

### Minimal
- Webcam frame: 2px border, subtle corner accents
- Alerts: simple fade-in, no bounce
- Decorations: none
- Scene screens: centered text only, 1-2 accent elements

### Decorated
- Webcam frame: 8px styled border, corner + edge decorations
- Alerts: pop-in with bounce
- Decorations: 3-5 floating elements
- Scene screens: text with surrounding themed elements, sparkles

### Maximalist
- Webcam frame: 15px+ ornate border, full decoration coverage
- Alerts: pop-in + sparkle burst
- Decorations: 10+ floating elements, border decorations
- Scene screens: full composition with characters, many animated elements
