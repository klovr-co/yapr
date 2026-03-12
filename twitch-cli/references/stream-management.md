# Stream Management — Twitch CLI Patterns

All write operations require a `broadcaster_id`. Get it once and reuse it:

```bash
twitch api get users | jq -r '.data[0].id'
# Save to a variable: BROADCASTER_ID=$(twitch api get users | jq -r '.data[0].id')
```

---

## Update Stream Title

```bash
twitch api patch channels \
  -q broadcaster_id=$BROADCASTER_ID \
  -b '{"title":"My new stream title"}'
```

## Update Stream Category (Game)

Step 1 — Look up the game ID by name:
```bash
twitch api get games -q name="Just Chatting"
# Returns: { "data": [{ "id": "509658", "name": "Just Chatting", ... }] }
GAME_ID=$(twitch api get games -q name="Just Chatting" | jq -r '.data[0].id')
```

Step 2 — Set the category:
```bash
twitch api patch channels \
  -q broadcaster_id=$BROADCASTER_ID \
  -b "{\"game_id\":\"$GAME_ID\"}"
```

## Update Title and Category Together

```bash
twitch api patch channels \
  -q broadcaster_id=$BROADCASTER_ID \
  -b "{\"title\":\"My stream title\",\"game_id\":\"$GAME_ID\"}"
```

## Update Stream Tags

Tags are set as an array of tag strings (Twitch handles them as freeform tags since the tag rework):
```bash
twitch api patch channels \
  -q broadcaster_id=$BROADCASTER_ID \
  -b '{"tags":["coding","rust","gamedev"]}'
```

To clear all tags:
```bash
twitch api patch channels \
  -q broadcaster_id=$BROADCASTER_ID \
  -b '{"tags":[]}'
```

## Run an Ad

Lengths: 30, 60, 90, 120, 150, 180 seconds.

```bash
twitch api post channels/commercial \
  -q broadcaster_id=$BROADCASTER_ID \
  -b '{"length":30}'
```

Requires scope: `channel:edit:commercial`

## Update Stream Language

```bash
twitch api patch channels \
  -q broadcaster_id=$BROADCASTER_ID \
  -b '{"broadcaster_language":"en"}'
```

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Token expired or missing scope | Re-run `twitch token -u -s 'channel:manage:broadcast'` |
| 403 Forbidden | Wrong broadcaster_id (not your channel) | Verify BROADCASTER_ID matches your account |
| 404 Not Found | Invalid game_id | Re-lookup the game name |
| 400 Bad Request | Malformed JSON body | Check `-b` JSON syntax |
