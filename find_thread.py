#!/usr/bin/env python3
"""Find a DM thread_id (group or 1:1) by name / @username.
Usage:  python find_thread.py "part of the name"   """
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from instagrapi import Client

QUERY = " ".join(sys.argv[1:]).strip().lower()
if not QUERY:
    sys.exit('usage: python find_thread.py "name or @username"')


def get_sessionid():
    sid = os.environ.get("IG_SESSIONID")
    if sid:
        return sid.strip()
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (".sessionid", os.path.join(here, ".sessionid")):
        if os.path.exists(p):
            return open(p, encoding="utf-8").read().strip()
    sys.exit("Missing sessionid. Create a .sessionid file or set IG_SESSIONID.")


def main():
    cl = Client()
    cl.delay_range = [1, 3]
    cl.login_by_sessionid(get_sessionid())

    matches = []
    for endpoint in ("direct_v2/inbox/", "direct_v2/pending_inbox/"):
        cursor = None
        pages = 0
        while True:
            params = {"visual_message_return_type": "unseen", "thread_message_limit": "1",
                      "persistentBadging": "true", "limit": "20"}
            if cursor:
                params["cursor"] = cursor
                params["direction"] = "older"
            try:
                res = cl.private_request(endpoint, params=params)
            except Exception:
                break
            box = res.get("inbox") or res.get("pending") or {}
            for t in box.get("threads", []):
                users = t.get("users", [])
                hay = " ".join([
                    t.get("thread_title") or "",
                    *[u.get("username", "") for u in users],
                    *[u.get("full_name", "") for u in users],
                ]).lower()
                if QUERY in hay:
                    names = ", ".join(f"{u.get('username')} ({u.get('full_name')})" for u in users)
                    matches.append((len(users), str(t.get("thread_id")), t.get("thread_title") or names, names))
            pages += 1
            cursor = box.get("oldest_cursor")
            if not box.get("has_older") or not cursor or pages > 60:
                break

    if not matches:
        print(f"nothing matched {QUERY!r}")
        return
    print(f"{'PART':>4}  {'THREAD_ID':24}  TITLE / PARTICIPANTS")
    print("-" * 90)
    for n, tid, title, names in matches:
        print(f"{n:>4}  {tid:24}  {title}")
        if title != names:
            print(f"        -> {names}")


if __name__ == "__main__":
    main()
