---
name: twitch-cli
description: Use when working with Twitch stream management or querying Twitch channel data via the Twitch CLI. Triggers on: update stream title, change stream category, run ad, check viewer count, get follower count, get clips, check if live, update stream tags, Twitch channel info, broadcaster ID lookup.
---

# Twitch CLI Skill

Wraps the Twitch CLI for stream management and channel data queries. Use this to update your stream, query stats, and interact with the Twitch API from the terminal.

## Quick Start

**First time? Do the full setup below. Already configured? Skip to workflows.**

Check if the CLI is working:
```bash
twitch version
twitch api get users --pretty
```

---

## Setup (First Time Only)

### 1. Install the CLI
```bash
brew install twitchdev/twitch/twitch-cli
twitch version  # Should print version number
```

### 2. Register a Twitch App
1. Go to https://dev.twitch.tv/console
2. Click "Register Your Application"
3. Name: anything (e.g. "My Stream Tools")
4. OAuth Redirect URL: `http://localhost:3000`
5. Category: "Application Integration"
6. Copy the **Client ID**, generate and copy the **Client Secret**

### 3. Configure the CLI
```bash
twitch configure
# Paste Client ID when prompted
# Paste Client Secret when prompted
```

### 4. Get a User Token with Required Scopes
```bash
twitch token -u -s 'channel:manage:broadcast channel:edit:commercial moderator:read:followers user:read:email clips:edit channel:read:subscriptions'
# Browser will open — log in and authorize
# Token is saved automatically
```

### 5. Get Your Broadcaster ID
```bash
BROADCASTER_ID=$(twitch api get users | jq -r '.data[0].id')
echo $BROADCASTER_ID  # Save this value — you'll use it constantly
```

---

## Core Workflow

Almost every operation follows this pattern:

```
1. Get broadcaster_id (once per session)
2. Run the relevant API command
3. Pipe to jq for readable output
```

```bash
# Set this at the start of any session
BROADCASTER_ID=$(twitch api get users | jq -r '.data[0].id')
USER_LOGIN=$(twitch api get users | jq -r '.data[0].login')
```

---

## Stream Management

See `references/stream-management.md` for full patterns.

### Update Title
```bash
twitch api patch channels \
  -q broadcaster_id=$BROADCASTER_ID \
  -b '{"title":"Your new stream title"}'
```

### Change Category
```bash
GAME_ID=$(twitch api get games -q name="Just Chatting" | jq -r '.data[0].id')
twitch api patch channels \
  -q broadcaster_id=$BROADCASTER_ID \
  -b "{\"game_id\":\"$GAME_ID\"}"
```

### Run an Ad (30/60/90/120/150/180 seconds)
```bash
twitch api post channels/commercial \
  -q broadcaster_id=$BROADCASTER_ID \
  -b '{"length":30}'
```

### Update Tags
```bash
twitch api patch channels \
  -q broadcaster_id=$BROADCASTER_ID \
  -b '{"tags":["coding","rust"]}'
```

---

## Data Queries

See `references/data-queries.md` for full patterns.

### Am I Live?
```bash
twitch api get streams -q user_login=$USER_LOGIN | jq '.data | length > 0'
```

### Current Viewer Count
```bash
twitch api get streams -q user_login=$USER_LOGIN | jq '.data[0].viewer_count'
```

### Follower Count
```bash
twitch api get channels/followers \
  -q broadcaster_id=$BROADCASTER_ID | jq '.total'
```

### Channel Info
```bash
twitch api get channels \
  -q broadcaster_id=$BROADCASTER_ID | jq '.data[0]'
```

### Recent Clips
```bash
twitch api get clips \
  -q broadcaster_id=$BROADCASTER_ID \
  -q first=10 | jq '.data[] | {title, view_count, url}'
```

---

## Error Handling

| Error | Meaning | Fix |
|-------|---------|-----|
| `401 Unauthorized` | Token expired or missing | `twitch token -u -s '<needed scopes>'` |
| `403 Forbidden` | Scope missing or wrong broadcaster_id | Add missing scope; verify BROADCASTER_ID is yours |
| `404 Not Found` | Wrong endpoint or ID | Check endpoint name; re-lookup game/user IDs |
| `400 Bad Request` | Malformed JSON in `-b` | Validate JSON syntax |
| Empty `data[]` | No results / offline | Check live status; verify IDs are correct |

---

## References

- `references/api_reference.md` — Full CLI command reference, flags, all endpoints, scopes
- `references/stream-management.md` — Patterns for updating title, category, tags, running ads
- `references/data-queries.md` — Patterns for viewer count, followers, clips, live status

---

## Verification Checklist

```bash
twitch version                                              # CLI installed
twitch api get users                                        # Auth works
twitch api get channels -q broadcaster_id=$BROADCASTER_ID  # Channel queries work
twitch api get streams -q user_login=$USER_LOGIN            # Stream queries work
```
