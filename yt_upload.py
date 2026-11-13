#!/usr/bin/env python3
"""Yatay videoyu YouTube'a normal video olarak yukler (Buffer yalnizca Short gonderdigi icin).

Kimlik bilgileri ortam degiskenlerinden okunur, depoya YAZILMAZ:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

Kullanim:
  python3 yt_upload.py VIDEO.mp4 --title "Baslik" --desc "Aciklama" \
      [--tags a,b,c] [--privacy public|unlisted|private] \
      [--publish-at 2026-11-14T19:00:00+03:00] [--thumb kapak.png] [--category 27]

--publish-at verilirse video once gizli yuklenir, o saatte YouTube kendisi yayina alir.
Cikti: tek satir JSON {"id", "url", "privacy", "publishAt", "thumb"}.
Ag: oauth2.googleapis.com ve www.googleapis.com izinli olmali.
"""
import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
THUMB_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set?uploadType=media&videoId="
CHUNK = 8 * 1024 * 1024  # 256 KB'nin kati


def die(msg):
    print("HATA: " + msg, file=sys.stderr)
    sys.exit(1)


def access_token():
    need = ["YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"]
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        die("eksik ortam degiskeni: " + ", ".join(missing))
    data = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data), timeout=60) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        die("token alinamadi (%s): %s" % (e.code, e.read().decode()[:300]))


def start_session(token, meta, size, ctype):
    body = json.dumps(meta).encode()
    req = urllib.request.Request(UPLOAD_URL, data=body, method="POST", headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": ctype,
        "X-Upload-Content-Length": str(size),
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.headers["Location"]
    except urllib.error.HTTPError as e:
        die("yukleme baslatilamadi (%s): %s" % (e.code, e.read().decode()[:500]))


def send_file(session, path, size, ctype):
    sent = 0
    with open(path, "rb") as f:
        while sent < size:
            f.seek(sent)
            chunk = f.read(CHUNK)
            end = sent + len(chunk) - 1
            req = urllib.request.Request(session, data=chunk, method="PUT", headers={
                "Content-Type": ctype,
                "Content-Length": str(len(chunk)),
                "Content-Range": "bytes %d-%d/%d" % (sent, end, size),
            })
            for attempt in range(6):
                try:
                    with urllib.request.urlopen(req, timeout=600) as r:
                        return json.load(r)  # 200/201: bitti
                except urllib.error.HTTPError as e:
                    if e.code == 308:  # parca alindi, devam
                        rng = e.headers.get("Range")
                        sent = int(rng.split("-")[1]) + 1 if rng else end + 1
                        break
                    if e.code in (500, 502, 503, 504) and attempt < 5:
                        time.sleep(2 ** attempt)
                        continue
                    die("yukleme hatasi (%s): %s" % (e.code, e.read().decode()[:500]))
                except (urllib.error.URLError, TimeoutError) as e:
                    if attempt < 5:
                        time.sleep(2 ** attempt)
                        continue
                    die("ag hatasi: %s" % e)
    die("yukleme tamamlanmadi")


def set_thumb(token, video_id, path):
    ctype = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        data = f.read()
    req = urllib.request.Request(THUMB_URL + video_id, data=data, method="POST", headers={
        "Authorization": "Bearer " + token,
        "Content-Type": ctype,
        "Content-Length": str(len(data)),
    })
    try:
        with urllib.request.urlopen(req, timeout=120):
            return "ok"
    except urllib.error.HTTPError as e:
        return "hata %s: %s" % (e.code, e.read().decode()[:200])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--title", required=True)
    ap.add_argument("--desc", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    ap.add_argument("--publish-at", default="")
    ap.add_argument("--thumb", default="")
    ap.add_argument("--category", default="27")  # 27 = Education
    ap.add_argument("--lang", default="tr")
    a = ap.parse_args()

    if not os.path.isfile(a.video):
        die("dosya yok: " + a.video)
    if len(a.title) > 100:
        die("baslik 100 karakteri geciyor")

    status = {"privacyStatus": a.privacy, "selfDeclaredMadeForKids": False}
    if a.publish_at:
        status["privacyStatus"] = "private"
        status["publishAt"] = a.publish_at
    meta = {
        "snippet": {
            "title": a.title,
            "description": a.desc,
            "tags": [t.strip() for t in a.tags.split(",") if t.strip()],
            "categoryId": a.category,
            "defaultLanguage": a.lang,
            "defaultAudioLanguage": a.lang,
        },
        "status": status,
    }
    size = os.path.getsize(a.video)
    ctype = mimetypes.guess_type(a.video)[0] or "video/mp4"
    token = access_token()
    session = start_session(token, meta, size, ctype)
    res = send_file(session, a.video, size, ctype)
    out = {
        "id": res["id"],
        "url": "https://www.youtube.com/watch?v=" + res["id"],
        "privacy": res.get("status", {}).get("privacyStatus"),
        "publishAt": res.get("status", {}).get("publishAt"),
        "uploadStatus": res.get("status", {}).get("uploadStatus"),
    }
    if a.thumb:
        out["thumb"] = set_thumb(token, res["id"], a.thumb) if os.path.isfile(a.thumb) else "dosya yok"
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
