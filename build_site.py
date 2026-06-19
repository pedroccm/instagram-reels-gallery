#!/usr/bin/env python3
"""Build a static gallery site from reels.json: downloads thumbnails locally and
writes site/index.html + site/data.js (self-contained, also opens via file://).

Usage:
    python build_site.py [reels.json] [site] [title] [emoji]
"""
import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SITE = "site"
THUMBS = os.path.join(SITE, "thumbs")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def download(reel):
    code, url = reel["code"], reel.get("thumb")
    if not url:
        return code, False
    path = os.path.join(THUMBS, code + ".jpg")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return code, True
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=25)
        if r.status_code == 200 and r.content:
            with open(path, "wb") as f:
                f.write(r.content)
            return code, True
    except Exception:
        pass
    return code, False


def main():
    global SITE, THUMBS
    src = sys.argv[1] if len(sys.argv) > 1 else "reels.json"
    SITE = sys.argv[2] if len(sys.argv) > 2 else "site"
    title = sys.argv[3] if len(sys.argv) > 3 else "Reels"
    emoji = sys.argv[4] if len(sys.argv) > 4 else "🎬"
    THUMBS = os.path.join(SITE, "thumbs")

    data = json.load(open(src, encoding="utf-8"))
    reels = data["reels"]
    os.makedirs(THUMBS, exist_ok=True)

    # download thumbnails in parallel
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for code, success in ex.map(download, reels):
            ok += 1 if success else 0
    print(f"thumbnails downloaded: {ok}/{len(reels)}")

    # build the site dataset (local thumb when it exists)
    items = []
    for r in reels:
        local = os.path.join("thumbs", r["code"] + ".jpg")
        has_local = os.path.exists(os.path.join(SITE, local))
        items.append({
            "code": r["code"],
            "url": r["url"],
            "by": r.get("shared_by") or "?",
            "ts": r.get("timestamp_ms") or 0,
            "caption": (r.get("caption") or "").strip(),
            "thumb": local.replace("\\", "/") if has_local else None,
            "type": "post" if r.get("item_type") == "xma_media_share" else "reel",
        })
    items.sort(key=lambda x: x["ts"], reverse=True)

    with open(os.path.join(SITE, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.TITLE = " + json.dumps(title, ensure_ascii=False) + ";\n")
        f.write("window.EMOJI = " + json.dumps(emoji, ensure_ascii=False) + ";\n")
        f.write("window.REELS = " + json.dumps(items, ensure_ascii=False) + ";\n")

    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(INDEX_HTML)

    print(f"OK -> {SITE}/index.html ({len(items)} reels, title {title!r})")


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title id="pgtitle">Reels</title>
<style>
  :root{
    --bg:#0a0a0f; --card:#15151f; --line:#23232f; --txt:#f4f4f7;
    --mut:#9a9ab0; --accent:#ff3d77; --accent2:#7b5cff;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
       font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
  header{position:sticky;top:0;z-index:10;backdrop-filter:blur(14px);
         background:rgba(10,10,15,.78);border-bottom:1px solid var(--line);
         padding:18px 20px 14px}
  .title{display:flex;align-items:center;gap:12px}
  .title h1{margin:0;font-size:22px;letter-spacing:.4px}
  .logo{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;
        background:linear-gradient(135deg,var(--accent),var(--accent2));font-size:18px}
  .sub{color:var(--mut);font-size:13px;margin:2px 0 0 46px}
  .bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:14px}
  .chip{border:1px solid var(--line);background:var(--card);color:var(--txt);
        padding:6px 12px;border-radius:999px;font-size:13px;cursor:pointer;
        transition:.15s;display:flex;gap:6px;align-items:center}
  .chip b{color:var(--mut);font-weight:600}
  .chip:hover{border-color:#3a3a4a}
  .chip.on{background:linear-gradient(135deg,var(--accent),var(--accent2));
           border-color:transparent}
  .chip.on b{color:rgba(255,255,255,.85)}
  .spacer{flex:1}
  .grid{display:grid;gap:14px;padding:18px 20px 60px;
        grid-template-columns:repeat(auto-fill,minmax(190px,1fr))}
  .card{position:relative;aspect-ratio:9/16;border-radius:16px;overflow:hidden;
        background:#1b1b27;border:1px solid var(--line);cursor:pointer;
        text-decoration:none;color:inherit;transition:.18s}
  .card:hover{transform:translateY(-3px);border-color:#3a3a4a;
              box-shadow:0 12px 30px rgba(0,0,0,.45)}
  .card img{width:100%;height:100%;object-fit:cover;display:block}
  .ph{width:100%;height:100%;display:grid;place-items:center;
      background:linear-gradient(135deg,#272735,#1a1a25);color:var(--mut);
      font-size:12px;padding:10px;text-align:center;word-break:break-all}
  .grad{position:absolute;inset:0;background:linear-gradient(to top,
        rgba(0,0,0,.85) 0%,rgba(0,0,0,.1) 42%,transparent 70%)}
  .play{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
        width:52px;height:52px;border-radius:50%;background:rgba(0,0,0,.45);
        backdrop-filter:blur(2px);display:grid;place-items:center;opacity:0;
        transition:.18s;border:1px solid rgba(255,255,255,.25)}
  .card:hover .play{opacity:1}
  .play svg{margin-left:3px}
  .badge{position:absolute;top:8px;right:8px;font-size:10px;letter-spacing:.5px;
         text-transform:uppercase;background:rgba(0,0,0,.55);padding:3px 7px;
         border-radius:6px;color:#fff;border:1px solid rgba(255,255,255,.18)}
  .meta{position:absolute;left:10px;right:10px;bottom:9px}
  .who{display:flex;align-items:center;gap:7px}
  .ava{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;
       font-size:11px;font-weight:700;color:#fff;flex:0 0 auto}
  .who span{font-size:12.5px;font-weight:600}
  .date{font-size:11px;color:#cfcfe0;margin-top:3px;opacity:.85}
  .cap{font-size:11px;color:#d8d8e6;margin-top:4px;display:-webkit-box;
       -webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;opacity:.9}
  .empty{color:var(--mut);text-align:center;padding:60px}
  footer{color:var(--mut);font-size:12px;text-align:center;padding:0 20px 40px}
</style>
</head>
<body>
<header>
  <div class="title">
    <div class="logo" id="logo">🎬</div>
    <h1 id="h1">Reels</h1>
  </div>
  <div class="sub" id="sub"></div>
  <div class="bar" id="filters"></div>
</header>
<div class="grid" id="grid"></div>
<footer id="foot"></footer>

<script src="data.js"></script>
<script>
const REELS = window.REELS || [];
const TITLE = window.TITLE || "Reels";
const EMOJI = window.EMOJI || "🎬";
document.getElementById("pgtitle").textContent = TITLE;
document.getElementById("h1").textContent = TITLE;
document.getElementById("logo").textContent = EMOJI;
const COLORS = ["#ff3d77","#7b5cff","#2dd4bf","#f59e0b","#38bdf8","#fb7185","#a3e635","#c084fc"];
const colorFor = (n) => { let h=0; for(const c of n) h=(h*31+c.charCodeAt(0))>>>0; return COLORS[h%COLORS.length]; };
const fmtDate = (ms) => ms ? new Date(ms).toLocaleString("en-US",{day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"}) : "";

let active = "all";
let order = "new";

const people = {};
REELS.forEach(r => people[r.by] = (people[r.by]||0)+1);
const sortedPeople = Object.entries(people).sort((a,b)=>b[1]-a[1]);

function renderFilters(){
  const el = document.getElementById("filters");
  const chips = [["all", REELS.length, "All"]]
    .concat(sortedPeople.map(([n,c]) => [n,c,n]));
  el.innerHTML = chips.map(([key,count,label]) =>
    `<button class="chip ${active===key?'on':''}" data-k="${key}">${label} <b>${count}</b></button>`
  ).join("") +
  `<div class="spacer"></div>
   <button class="chip" id="sortbtn">${order==='new'?'↓ Newest':'↑ Oldest'}</button>`;
  el.querySelectorAll(".chip[data-k]").forEach(b =>
    b.onclick = () => { active = b.dataset.k; render(); });
  document.getElementById("sortbtn").onclick = () => {
    order = order==='new'?'old':'new'; render();
  };
}

function render(){
  renderFilters();
  let list = REELS.filter(r => active==="all" || r.by===active);
  list = list.slice().sort((a,b)=> order==='new' ? b.ts-a.ts : a.ts-b.ts);

  document.getElementById("sub").textContent =
    `${REELS.length} reels · from ${sortedPeople.length} ${sortedPeople.length===1?'person':'people'}`;
  document.getElementById("foot").textContent =
    `${list.length} reels in this view · click to open on Instagram`;

  const grid = document.getElementById("grid");
  if(!list.length){ grid.innerHTML = `<div class="empty">Nothing here.</div>`; return; }
  grid.innerHTML = list.map(r => {
    const ini = (r.by||"?").slice(0,2).toUpperCase();
    const col = colorFor(r.by||"?");
    const media = r.thumb
      ? `<img loading="lazy" src="${r.thumb}" alt="">`
      : `<div class="ph">${r.code}</div>`;
    const cap = r.caption ? `<div class="cap">${r.caption.replace(/</g,"&lt;")}</div>` : "";
    return `<a class="card" href="${r.url}" target="_blank" rel="noopener">
      ${media}
      <div class="grad"></div>
      <div class="badge">${r.type}</div>
      <div class="play"><svg width="18" height="18" viewBox="0 0 24 24" fill="#fff"><path d="M8 5v14l11-7z"/></svg></div>
      <div class="meta">
        <div class="who"><span class="ava" style="background:${col}">${ini}</span><span>${r.by}</span></div>
        <div class="date">${fmtDate(r.ts)}</div>
        ${cap}
      </div>
    </a>`;
  }).join("");
}

render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
