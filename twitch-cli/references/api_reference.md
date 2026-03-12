# Twitch CLI — Command Reference

Official docs: https://dev.twitch.tv/docs/cli/

## Installation

```bash
# macOS via Homebrew
brew install twitchdev/twitch/twitch-cli

# Verify
twitch version
```

---

## Authentication

### Register an App (One-Time Setup)
1. Go to https://dev.twitch.tv/console
2. Click "Register Your Application"
3. Set OAuth Redirect URL to `http://localhost:3000`
4. Category: "Application Integration"
5. Copy your **Client ID** and generate a **Client Secret**

### Configure the CLI
```bash
twitch configure
# Prompts for Client ID and Client Secret
```

### Get a User Token (with scopes)
```bash
twitch token -u -s 'channel:manage:broadcast channel:edit:commercial moderator:read:followers user:read:email'
# Opens browser for OAuth flow, saves token locally
```

### Get an App Token (no user context)
```bash
twitch token
```

### Check Current Token
```bash
twitch token -s '' --print-token
```

---

## `twitch api` — Core Command

```
twitch api <METHOD> <ENDPOINT> [flags]
```

### Methods
| Flag | HTTP Method |
|------|-------------|
| `get` | GET |
| `post` | POST |
| `patch` | PATCH |
| `put` | PUT |
| `delete` | DELETE |

### Flags
| Flag | Description | Example |
|------|-------------|---------|
| `-q <key=value>` | Query parameter | `-q broadcaster_id=123` |
| `-b '<json>'` | Request body (JSON) | `-b '{"title":"test"}'` |
| `-H 'Key: Value'` | Custom header | `-H 'Content-Type: application/json'` |
| `--autopaginate` | Auto-fetch all pages | `twitch api get clips -q broadcaster_id=123 --autopaginate` |
| `--pretty` | Pretty-print JSON output | `twitch api get users --pretty` |
| `-n <count>` | Limit autopaginate pages | `-n 3` |

### Multiple Query Params
```bash
# Repeat -q for each param
twitch api get clips \
  -q broadcaster_id=123 \
  -q first=20 \
  -q started_at=2024-01-01T00:00:00Z
```

---

## Common Endpoints

### Users
```bash
twitch api get users                          # Current authenticated user
twitch api get users -q login=username        # By login name
twitch api get users -q id=123456             # By ID
```

### Channels
```bash
twitch api get channels -q broadcaster_id=ID
twitch api patch channels -q broadcaster_id=ID -b '{...}'
```

### Streams
```bash
twitch api get streams -q user_login=username
twitch api get streams -q user_id=ID
```

### Games / Categories
```bash
twitch api get games -q name="Game Name"
twitch api get games -q id=GAME_ID
twitch api get games/top -q first=10
```

### Clips
```bash
twitch api get clips -q broadcaster_id=ID
twitch api get clips -q id=CLIP_ID
twitch api post clips -q broadcaster_id=ID    # Create clip (requires channel:manage:broadcast)
```

### Chat
```bash
twitch api get chat/settings -q broadcaster_id=ID -q moderator_id=ID
twitch api patch chat/settings -q broadcaster_id=ID -q moderator_id=ID -b '{...}'
twitch api get chat/chatters -q broadcaster_id=ID -q moderator_id=ID
```

### Moderators
```bash
twitch api get moderation/moderators -q broadcaster_id=ID
twitch api get channels/followers -q broadcaster_id=ID
```

### Schedule
```bash
twitch api get schedule -q broadcaster_id=ID
twitch api post schedule/segment -q broadcaster_id=ID -b '{...}'
```

### Ads
```bash
twitch api post channels/commercial -q broadcaster_id=ID -b '{"length":30}'
twitch api get channels/ads -q broadcaster_id=ID
twitch api patch channels/ads/schedule/snooze -q broadcaster_id=ID
```

---

## Required Scopes by Operation

| Operation | Scope |
|-----------|-------|
| Update title/category/tags | `channel:manage:broadcast` |
| Run ads | `channel:edit:commercial` |
| Read follower count | `moderator:read:followers` |
| Read subscriptions | `channel:read:subscriptions` |
| Read email | `user:read:email` |
| Manage chat settings | `moderator:manage:chat_settings` |
| Create clips | `clips:edit` |
| Read hype train | `channel:read:hype_train` |

---

## Event Sub / Mock Events (Testing)

```bash
# List event types
twitch event list

# Trigger a mock follow event
twitch event trigger follow

# Trigger mock channel point redemption
twitch event trigger channel-points-custom-reward-redemption

# Forward events to local server
twitch event websocket start-server --port 8080
```

---

## Output & Filtering with jq

```bash
# Pretty print
twitch api get users | jq '.'

# Extract single field
twitch api get users | jq -r '.data[0].id'

# Extract multiple fields
twitch api get streams -q user_login=username | jq '.data[0] | {title, viewer_count, game_name}'

# Check if array is non-empty (live status)
twitch api get streams -q user_login=username | jq '.data | length > 0'
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `401 Unauthorized` | Token expired | `twitch token -u -s 'needed:scopes'` |
| `403 Forbidden` | Missing scope | Add scope to token command |
| `400 Bad Request` | Bad JSON body | Validate JSON in `-b` arg |
| `404 Not Found` | Wrong endpoint or ID | Check endpoint spelling and IDs |
| Empty response | Offline or no data | Check live status, verify IDs |
| `configure: command not found` | CLI not installed | `brew install twitchdev/twitch/twitch-cli` |
