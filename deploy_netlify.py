#!/usr/bin/env python3
"""Deploy a static folder to Netlify via the REST API (zip upload).

Usage:
    NETLIFY_AUTH_TOKEN=... python deploy_netlify.py <folder> <site-name>

Token: https://app.netlify.com/user/applications#personal-access-tokens
Optionally set NETLIFY_ACCOUNT to a specific account slug; otherwise your
default account is used. This step is optional — `site/` is plain static files,
so you can also drag-drop it on Netlify, push to GitHub Pages, etc.
"""
import io
import os
import sys
import time
import zipfile

import requests

TOKEN = os.environ.get("NETLIFY_AUTH_TOKEN", "")
ACCOUNT = os.environ.get("NETLIFY_ACCOUNT", "")   # account slug (optional)
if not TOKEN:
    sys.exit("Set NETLIFY_AUTH_TOKEN "
             "(https://app.netlify.com/user/applications#personal-access-tokens).")

H = {"Authorization": f"Bearer {TOKEN}"}
API = "https://api.netlify.com/api/v1"

if len(sys.argv) < 3:
    sys.exit("usage: python deploy_netlify.py <folder> <site-name>")
SITE_DIR = sys.argv[1]
SITE_NAME = sys.argv[2].lower()


def find_or_create_site():
    endpoint = f"{API}/{ACCOUNT}/sites" if ACCOUNT else f"{API}/sites"
    r = requests.post(endpoint, headers=H, json={"name": SITE_NAME})
    if r.status_code in (200, 201):
        return r.json()
    if r.status_code == 422:  # name already taken on the account -> reuse it
        lst = requests.get(f"{API}/sites", headers=H,
                           params={"filter": "all", "per_page": 100}).json()
        for s in lst:
            if s.get("name") == SITE_NAME:
                print("site already exists, reusing")
                return s
    sys.exit(f"failed to create site ({r.status_code}): {r.text[:300]}")


def zip_dir(path):
    buf = io.BytesIO()
    n = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(path):
            for fn in files:
                full = os.path.join(root, fn)
                arc = os.path.relpath(full, path).replace("\\", "/")
                z.write(full, arc)
                n += 1
    return buf.getvalue(), n


def main():
    site = find_or_create_site()
    sid = site["id"]
    data, n = zip_dir(SITE_DIR)
    print(f"site_id={sid} | zip: {n} files, {len(data)/1e6:.1f} MB | uploading...")

    dh = dict(H)
    dh["Content-Type"] = "application/zip"
    dr = requests.post(f"{API}/sites/{sid}/deploys", headers=dh, data=data, timeout=300)
    if dr.status_code not in (200, 201):
        sys.exit(f"deploy failed ({dr.status_code}): {dr.text[:300]}")
    did = dr.json()["id"]

    for _ in range(80):
        d = requests.get(f"{API}/sites/{sid}/deploys/{did}", headers=H).json()
        state = d.get("state")
        print("  state:", state)
        if state == "ready":
            break
        if state == "error":
            sys.exit("deploy error: " + str(d.get("error_message")))
        time.sleep(3)

    print("\nDEPLOY OK")
    print("URL:", site.get("ssl_url") or site.get("url") or f"https://{SITE_NAME}.netlify.app")
    print("Admin:", site.get("admin_url"))


if __name__ == "__main__":
    main()
