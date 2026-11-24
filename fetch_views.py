"""Fill in per-episode YouTube view counts (UNTESTED - written without network access).

Why this exists: per-episode views were not obtainable when the dataset was built, so the
"what drives views" model (views_model.py) is waiting on data/views_full.csv.

Usage (needs a YouTube Data API v3 key and the Hot Ones playlist id, both yours to supply):
    export YT_API_KEY=...
    python3 scripts/fetch_views.py --playlist-id PLxxxxxxxx
Output: data/views_full.csv with columns episode, views, as_of_date, video_id, video_title
Matching is by guest name appearing in the video title; unmatched episodes are listed so you can fix them by hand.
"""
import argparse
import csv
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
API = "https://www.googleapis.com/youtube/v3"


def get(path, **params):
    params["key"] = os.environ["YT_API_KEY"]
    with urllib.request.urlopen(f"{API}/{path}?{urllib.parse.urlencode(params)}") as r:
        return json.load(r)


def playlist_videos(pid):
    token, out = None, []
    while True:
        p = {"part": "snippet", "playlistId": pid, "maxResults": 50}
        if token:
            p["pageToken"] = token
        j = get("playlistItems", **p)
        out += [(i["snippet"]["resourceId"]["videoId"], i["snippet"]["title"]) for i in j["items"]]
        token = j.get("nextPageToken")
        if not token:
            return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--playlist-id", required=True)
    a = ap.parse_args()
    vids = playlist_videos(a.playlist_id)
    stats = {}
    for i in range(0, len(vids), 50):
        ids = ",".join(v for v, _ in vids[i:i + 50])
        for it in get("videos", part="statistics", id=ids)["items"]:
            stats[it["id"]] = int(it["statistics"].get("viewCount", 0))
    eps = pd.read_csv(DATA / "episodes.csv")
    today = dt.date.today().isoformat()
    rows, missing = [], []
    for _, e in eps.iterrows():
        first = e.guests.split(";")[0].lower()
        cand = [(v, t) for v, t in vids if first in t.lower()]
        if len(cand) == 1 or (cand and e.guests.count(";") == 0 and len(cand) > 0):
            v, t = cand[0]
            rows.append({"episode": e.episode, "views": stats.get(v), "as_of_date": today, "video_id": v, "video_title": t})
        else:
            missing.append((e.episode, e.guests, len(cand)))
    pd.DataFrame(rows).to_csv(DATA / "views_full.csv", index=False)
    print(f"matched {len(rows)} / {len(eps)}; unmatched or ambiguous:")
    for m in missing:
        print("  ", m)


if __name__ == "__main__":
    main()
