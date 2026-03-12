# Data Queries — Twitch CLI Patterns

Get your broadcaster ID once:
```bash
BROADCASTER_ID=$(twitch api get users | jq -r '.data[0].id')
USER_LOGIN=$(twitch api get users | jq -r '.data[0].login')
```

---

## Check Live Status

```bash
twitch api get streams -q user_login=$USER_LOGIN
# Returns empty data[] if offline, stream object if live
```

Check if live (returns true/false):
```bash
twitch api get streams -q user_login=$USER_LOGIN | jq '.data | length > 0'
```

## Get Current Viewer Count

```bash
twitch api get streams -q user_login=$USER_LOGIN | jq '.data[0].viewer_count'
# Returns null if offline
```

Full stream info while live:
```bash
twitch api get streams -q user_login=$USER_LOGIN | jq '.data[0]'
# Fields: id, user_login, game_name, title, viewer_count, started_at, language, tags
```

## Get Channel Info (Always Available)

```bash
twitch api get channels -q broadcaster_id=$BROADCASTER_ID | jq '.data[0]'
# Fields: broadcaster_id, broadcaster_name, game_name, game_id, title, delay,
#         tags, content_classification_labels, is_branded_content
```

## Get Follower Count

```bash
twitch api get channels/followers \
  -q broadcaster_id=$BROADCASTER_ID | jq '.total'
```

Get recent followers (paginated, up to 20 per page):
```bash
twitch api get channels/followers \
  -q broadcaster_id=$BROADCASTER_ID \
  -q first=20 | jq '.data[].user_name'
```

Requires scope: `moderator:read:followers`

## Get Clips

Most recent clips:
```bash
twitch api get clips -q broadcaster_id=$BROADCASTER_ID -q first=10 | jq '.data[]'
# Fields: id, url, title, view_count, created_at, duration, creator_name
```

Clips by view count (sort isn't natively supported — pipe to jq):
```bash
twitch api get clips -q broadcaster_id=$BROADCASTER_ID -q first=100 \
  | jq '.data | sort_by(-.view_count) | .[0:10]'
```

Clips from last 7 days:
```bash
WEEK_AGO=$(date -u -v-7d +"%Y-%m-%dT%H:%M:%SZ")  # macOS
twitch api get clips \
  -q broadcaster_id=$BROADCASTER_ID \
  -q started_at=$WEEK_AGO \
  -q first=20 | jq '.data[]'
```

## Get Subscriber Count

```bash
twitch api get subscriptions \
  -q broadcaster_id=$BROADCASTER_ID | jq '.total'
```

Requires scope: `channel:read:subscriptions`

## Get Recent Stream Schedule

```bash
twitch api get schedule -q broadcaster_id=$BROADCASTER_ID | jq '.data.segments[]'
```

## Get Chat Settings

```bash
twitch api get chat/settings \
  -q broadcaster_id=$BROADCASTER_ID \
  -q moderator_id=$BROADCASTER_ID | jq '.data[0]'
# Shows: emote_mode, follower_mode, slow_mode, subscriber_mode, etc.
```

---

## Pagination

Twitch responses include a `pagination.cursor` for multi-page results:
```bash
# Get next page using cursor
CURSOR=$(twitch api get clips -q broadcaster_id=$BROADCASTER_ID -q first=20 | jq -r '.pagination.cursor')
twitch api get clips \
  -q broadcaster_id=$BROADCASTER_ID \
  -q first=20 \
  -q after=$CURSOR | jq '.data[]'
```

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Token expired | Re-run `twitch token -u -s 'moderator:read:followers'` |
| 403 Forbidden | Missing scope | Add required scope to token command |
| Empty `data[]` | Channel offline / no results | Check live status first |
