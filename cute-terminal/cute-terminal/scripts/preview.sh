#!/bin/bash
# Preview the cute terminal color palette in your current terminal
# Run this AFTER importing the .itermcolors profile to see how it looks

echo ""
echo "  ╭─────────────────────────────────────────╮"
echo "  │     ✨ Cute Terminal — Color Preview ✨   │"
echo "  ╰─────────────────────────────────────────╯"
echo ""

# Background + foreground basics
echo "  ┌─── Base Colors ───────────────────────┐"
echo "  │                                       │"
echo "  │  Default text on background           │"
printf "  │  \033[1mBold text (Dark charcoal)\033[0m             │\n"
echo "  │                                       │"
echo "  └───────────────────────────────────────┘"
echo ""

# ANSI normal colors
echo "  ┌─── Normal Colors ─────────────────────┐"
printf "  │  \033[30m██ Black (Muted slate)  \033[0m"
printf "  \033[31m██ Red (Soft rose)    \033[0m│\n"
printf "  │  \033[32m██ Green (Mint)       \033[0m"
printf "  \033[33m██ Yellow (Pale gold) \033[0m│\n"
printf "  │  \033[34m██ Blue (Sky)         \033[0m"
printf "  \033[35m██ Magenta (Lavender) \033[0m│\n"
printf "  │  \033[36m██ Cyan (Aqua)        \033[0m"
printf "  \033[37m██ White (Cloud)      \033[0m│\n"
echo "  └───────────────────────────────────────┘"
echo ""

# ANSI bright colors
echo "  ┌─── Bright Colors ────────────────────┐"
printf "  │  \033[90m██ Bright Black       \033[0m"
printf "  \033[91m██ Bright Red        \033[0m│\n"
printf "  │  \033[92m██ Bright Green       \033[0m"
printf "  \033[93m██ Bright Yellow     \033[0m│\n"
printf "  │  \033[94m██ Bright Blue        \033[0m"
printf "  \033[95m██ Bright Magenta    \033[0m│\n"
printf "  │  \033[96m██ Bright Cyan        \033[0m"
printf "  \033[97m██ Bright White      \033[0m│\n"
echo "  └──────────────────────────────────────┘"
echo ""

# Color gradient bar
printf "  "
for color in 31 91 33 93 32 92 36 96 34 94 35 95; do
    printf "\033[${color}m████\033[0m"
done
echo ""
echo ""

# Sample prompt
echo "  ┌─── Sample Prompt ─────────────────────┐"
printf "  │  \033[36m~/Projects/cute-app\033[0m \033[32m~>\033[0m "
printf "\033[37mcurl api.example.com\033[0m │\n"
printf "  │  \033[34mmaxine\033[0m \033[36m~/code\033[0m"
printf " \033[35m main\033[0m \033[32m~>\033[0m "
printf "\033[37mgit status\033[0m    │\n"
echo "  └───────────────────────────────────────┘"
echo ""

# Sample directory listing
echo "  ┌─── Sample ls Output ──────────────────┐"
printf "  │  \033[34m📁 src/\033[0m    \033[34m📁 lib/\033[0m    \033[34m📁 test/\033[0m   │\n"
printf "  │  \033[32m⚡ run.sh\033[0m  \033[35m📝 README.md\033[0m           │\n"
printf "  │  \033[33m📋 package.json\033[0m  \033[34m🐍 main.py\033[0m      │\n"
printf "  │  \033[36m🔗 link -> target\033[0m                  │\n"
echo "  └───────────────────────────────────────┘"
echo ""
echo "  💡 Not looking right? Make sure you selected"
echo "     the 'pastel-mint-sky' color preset in"
echo "     iTerm2 > Settings > Profiles > Colors"
echo ""
