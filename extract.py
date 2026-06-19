#!/usr/bin/env python3
"""
Extrai os Reels compartilhados num grupo de DM do Instagram usando o cookie
de sessao (sessionid). NAO usa usuario/senha.

Uso:
  1) coloque o sessionid num arquivo .sessionid (ou na env IG_SESSIONID)
  2) python extract.py list                      -> lista seus grupos/threads de DM
  3) python extract.py pull <thread_id> [--limit N]  -> puxa os reels -> reels.json
"""
import os
import re
import sys
import json
import time
import argparse

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from instagrapi import Client
except ImportError:
    sys.exit("instagrapi nao instalado. Rode:  pip install instagrapi")

# captura codes de reels/posts em qualquer URL do item (xma / link shares)
CODE_RE = re.compile(r"instagram\.com/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)")
# blocos XMA = formato atual de reel/post compartilhado na DM (story_share fica de fora: efemero)
XMA_KEYS = ("xma_clip", "xma_media_share")


def get_sessionid():
    sid = os.environ.get("IG_SESSIONID")
    if sid:
        return sid.strip()
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (".sessionid", os.path.join(here, ".sessionid")):
        if os.path.exists(p):
            return open(p, encoding="utf-8").read().strip()
    sys.exit("Faltou o sessionid. Crie um arquivo .sessionid ou defina IG_SESSIONID.")


def client():
    cl = Client()
    cl.delay_range = [1, 3]  # pausa entre requests pra nao parecer bot
    cl.login_by_sessionid(get_sessionid())
    return cl


def cmd_list(cl):
    threads = cl.direct_threads(amount=100)
    rows = []
    for t in threads:
        names = ", ".join(u.username for u in t.users)
        title = t.thread_title or names
        rows.append((bool(t.is_group), t.id, title, len(t.users), names))
    rows.sort(key=lambda r: not r[0])  # grupos primeiro
    print(f"\n{'TIPO':6} {'THREAD_ID':24} {'PART':>4}  TITULO")
    print("-" * 84)
    for is_group, tid, title, n, _names in rows:
        tipo = "GRUPO" if is_group else "1:1"
        print(f"{tipo:6} {str(tid):24} {n:>4}  {title}")
    print()


def _thumb_of(m):
    try:
        return m["image_versions2"]["candidates"][0]["url"]
    except Exception:
        return None


def media_from_item(item):
    """Devolve lista de dicts {code, url, owner, caption, thumb} pros reels do item."""
    out = {}

    def add(code, **kw):
        if not code:
            return
        d = out.setdefault(code, {"code": code})
        for k, v in kw.items():
            if v and not d.get(k):
                d[k] = v

    # 1) blocos XMA (formato atual: xma_clip = reel, xma_media_share = post)
    for key in XMA_KEYS:
        blk = item.get(key)
        if not isinstance(blk, list):
            continue
        for e in blk:
            if not isinstance(e, dict):
                continue
            m = CODE_RE.search(json.dumps(e, ensure_ascii=False))
            code = m.group(1) if m else None
            title = e.get("title_text")
            owner = title.split()[0] if isinstance(title, str) and title.strip() else None
            add(code, owner=owner, caption=title, thumb=e.get("preview_url"))

    # 2) shares antigos com dict de midia estruturado (media_share / clip)
    def walk(o):
        if isinstance(o, dict):
            code = o.get("code")
            if isinstance(code, str) and ("image_versions2" in o or "video_versions" in o or o.get("media_type")):
                owner = (o.get("user") or {}).get("username")
                cap = o.get("caption")
                cap = cap.get("text") if isinstance(cap, dict) else None
                add(code, owner=owner, caption=cap, thumb=_thumb_of(o))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(item)

    # 3) catch-all: qualquer link de reel/post solto no item cru
    for code in CODE_RE.findall(json.dumps(item, ensure_ascii=False)):
        add(code)

    return list(out.values())


def cmd_pull(cl, thread_id, limit, out="reels.json"):
    # mapa user_id -> username (participantes + viewer)
    users = {}
    try:
        info = cl.private_request(f"direct_v2/threads/{thread_id}/", params={"limit": 1})
        for u in info["thread"].get("users", []):
            users[str(u["pk"])] = u.get("username")
        users[str(cl.user_id)] = cl.account_info().username
    except Exception as e:
        print("aviso: nao consegui mapear todos os usuarios:", e)

    reels = []
    seen = set()
    cursor = None
    page = 0
    scanned = 0
    while True:
        params = {"visual_message_return_type": "unseen", "limit": "50"}
        if cursor:
            params["cursor"] = cursor
            params["direction"] = "older"
        res = cl.private_request(f"direct_v2/threads/{thread_id}/", params=params)
        thread = res["thread"]
        items = thread.get("items", [])
        scanned += len(items)
        for it in items:
            uid = str(it.get("user_id"))
            ts = int(it.get("timestamp", 0))  # microsegundos
            for m in media_from_item(it):
                if m["code"] in seen:
                    continue
                seen.add(m["code"])
                reels.append({
                    "code": m["code"],
                    "url": f"https://www.instagram.com/reel/{m['code']}/",
                    "owner": m.get("owner"),
                    "caption": m.get("caption"),
                    "thumb": m.get("thumb"),
                    "shared_by": users.get(uid, uid),
                    "shared_by_id": uid,
                    "timestamp_ms": ts // 1000 if ts else 0,
                    "item_type": it.get("item_type"),
                })
        page += 1
        print(f"  pagina {page}: {len(items)} msgs, {len(reels)} reels acumulados")
        cursor = thread.get("oldest_cursor")
        if not thread.get("has_older") or not cursor:
            break
        if limit and len(reels) >= limit:
            break
        time.sleep(1.5)

    reels.sort(key=lambda r: r["timestamp_ms"])
    payload = {
        "thread_id": thread_id,
        "count": len(reels),
        "scanned_messages": scanned,
        "reels": reels,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\nOK: {len(reels)} reels de {scanned} mensagens -> {out}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("pull")
    p.add_argument("thread_id")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--out", default="reels.json")
    args = ap.parse_args()

    cl = client()
    if args.cmd == "list":
        cmd_list(cl)
    elif args.cmd == "pull":
        cmd_pull(cl, args.thread_id, args.limit, args.out)


if __name__ == "__main__":
    main()
