---
name: instagram-reels-gallery
description: Extracts the Reels shared in an Instagram DM group (via your session cookie, no user/password) and builds a static gallery website out of them — grid of 9:16 cards, filter by who shared, sort by date, click to open on Instagram. Optionally deploys to Netlify. Use when the user wants to turn a group chat's shared Reels into a browsable site.
triggerPhrases:
  - "instagram-reels-gallery"
  - "build a site from the reels in this group"
  - "gallery of the reels shared in my dm group"
  - "monta um site com os reels do grupo"
  - "galeria dos reels do grupo"
---

# Instagram Reels Gallery

Pulls the Reels that people shared in an Instagram **DM group** and turns them into a
self-contained static gallery (filter by friend, sort by date, click to open).

## Pipeline

```bash
pip install instagrapi requests
# 1) put your sessionid in a .sessionid file (or IG_SESSIONID env)
python extract.py list                       # find your group's THREAD_ID
python extract.py pull <THREAD_ID>           # -> reels.json
python build_site.py                         # -> site/index.html
# optional:
NETLIFY_AUTH_TOKEN=... python deploy_netlify.py site my-reels-gallery
```

## Instructions for Claude

### Step 1 — Session
Needs a logged-in Instagram session. The user pastes their `sessionid` into a `.sessionid`
file in this folder, or sets `IG_SESSIONID`. It's git-ignored. Treat it like a password.

### Step 2 — Find the thread
`python extract.py list` lists DM threads with their `THREAD_ID` (groups first). Or
`python find_thread.py "part of the name"` to search by name/@username.
Note: the API `thread_id` is NOT the id in the web URL `/direct/t/<id>/`.

### Step 3 — Pull the reels
`python extract.py pull <THREAD_ID> [--limit N]` walks the conversation and writes
`reels.json` (code, url, owner, who shared it, date, thumbnail). Handles the current
`xma_clip`/`xma_media_share` share format and older structured shares.

### Step 4 — Build the site
`python build_site.py [reels.json] [site] [title] [emoji]` downloads thumbnails locally
(Instagram CDN URLs expire) and writes `site/index.html` + `site/data.js`. Opens via
`file://` or any static host.

### Step 5 — (Optional) Deploy
`deploy_netlify.py` zips and deploys `site/` via the Netlify REST API. Needs
`NETLIFY_AUTH_TOKEN`. Or just drag-drop `site/` on Netlify / push to GitHub Pages.

## Notes
- Uses Instagram's private API (against ToS). Block risk exists but is lower with a cookie
  than with user/password.
- `reels.json` and `site/` contain private group content — they're git-ignored.

## Dependencies
- `pip install instagrapi requests`
- A valid Instagram `sessionid`.
