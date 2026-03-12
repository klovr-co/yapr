---
name: cute-terminal
description: Use when customizing iTerm2 appearance, theming a terminal, making a terminal cute or aesthetic, setting up pastel colors for shell/prompt/iTerm2, or beautifying a macOS terminal setup
---

# Cute Terminal — Pastel Mint & Sky

Guide the user step-by-step through transforming their iTerm2 + Zsh into a soft pastel mint & sky aesthetic. No new tools — just configuration. Ask for confirmation before each change.

## Workflow

Walk through these 4 steps in order. For each step: explain what changes, show the config, ask for confirmation, then apply.

### Step 1: iTerm2 Color Profile

Import the bundled color profile:

```bash
open "cute-terminal/assets/pastel-mint-sky.itermcolors"
```

This opens iTerm2's color import dialog. Tell the user:
1. iTerm2 will ask to import the profile — click "Yes"
2. Go to **iTerm2 > Settings > Profiles > Colors**
3. In the "Color Presets" dropdown at bottom-right, select **pastel-mint-sky**

If the user wants to tweak individual colors, see `references/color-palette.md` for all hex values.

### Step 2: Font & Window

Guide the user through iTerm2 Settings:

**Font** (Settings > Profiles > Text):
- Recommend **SF Mono** or **Menlo** at 13-14pt (already installed on macOS)
- Enable "Use ligatures" if using a font that supports them
- Set line spacing to 110-120% for breathing room

**Window** (Settings > Profiles > Window):
- Transparency: 5-8% for a subtle soft effect
- Blur: 10-15 for gentle frosted glass
- Columns: 120, Rows: 35 (comfortable default)

**Tab bar** (Settings > Appearance):
- Theme: "Minimal" for a clean look
- Tab bar location: Top or Bottom (user preference)

### Step 3: Zsh Prompt

Add to `~/.zshrc`:

```zsh
# Cute pastel prompt
PROMPT='%F{cyan}%~%f %F{green}~>%f '
```

This gives: `~/Projects ~> ` in aqua directory + mint arrow.

**Alternative prompts to offer the user:**

```zsh
# With git branch
PROMPT='%F{cyan}%~%f %F{magenta}$(git branch --show-current 2>/dev/null | sed "s/^/ /")%f %F{green}~>%f '

# Two-line with username
PROMPT=$'\n''%F{blue}%n%f %F{cyan}%~%f'$'\n''%F{green}~>%f '

# Minimal with dot
PROMPT='%F{cyan}%1~%f %F{green}.%f '
```

After editing, run `source ~/.zshrc` to apply.

### Step 4: Shell Colors

Add to `~/.zshrc`:

```zsh
# Pastel LS colors
export LS_COLORS='di=34:ln=36:ex=32:*.md=35:*.json=33:*.py=34:*.js=33:*.ts=34:*.txt=37:*.log=90'
alias ls='ls --color=auto'

# Colored completions
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
autoload -Uz compinit && compinit
```

On macOS with default `ls`, use `LSCOLORS` instead:
```zsh
export CLICOLOR=1
export LSCOLORS='Exfxcxdxbxegedabagacad'
```

Or recommend `brew install coreutils` for GNU ls with `LS_COLORS` support.

Run `source ~/.zshrc` and `ls` to verify.

## Common Mistakes

- **Colors look wrong**: Make sure the color preset is actually selected in iTerm2, not just imported
- **Prompt not updating**: Forgot `source ~/.zshrc` — or there's a conflicting PROMPT line later in the file
- **ls colors not working**: macOS uses `LSCOLORS` (BSD), not `LS_COLORS` (GNU) — need coreutils or the BSD format
