#!/usr/bin/env python3
"""
fetch_videos.py
Fetches all videos and showcases from the Melton Vimeo account
and writes the result to data.json for use by the site builder.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

VIMEO_TOKEN = os.environ.get("VIMEO_TOKEN")
if not VIMEO_TOKEN:
    print("ERROR: VIMEO_TOKEN environment variable not set.", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://api.vimeo.com"
HEADERS = {
    "Authorization": f"Bearer {VIMEO_TOKEN}",
    "Accept": "application/vnd.vimeo.*+json;version=3.4",
    "Content-Type": "application/json",
}


def vimeo_get(path, params=None):
    """Make a paginated GET request to the Vimeo API, returning all items."""
    url = f"{BASE_URL}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    all_data = []
    while url:
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            print(f"HTTP error {e.code} fetching {url}: {e.reason}", file=sys.stderr)
            sys.exit(1)

        all_data.extend(body.get("data", []))

        paging = body.get("paging", {})
        next_page = paging.get("next")
        url = f"{BASE_URL}{next_page}" if next_page else None

    return all_data


def format_date(iso_str):
    """Convert ISO 8601 date string to a human-readable format."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%B %-d, %Y")
    except ValueError:
        return iso_str[:10]


def extract_video(v):
    """Extract the fields we care about from a Vimeo video object."""
    return {
        "title": v.get("name", "Untitled"),
        "url": v.get("link", ""),
        "date": format_date(v.get("created_time", "")),
        "date_raw": v.get("created_time", ""),
        "description": (v.get("description") or "").strip(),
    }


def main():
    print("Fetching all videos...")
    raw_videos = vimeo_get("/me/videos", {"per_page": 100, "fields": "name,link,created_time,description"})
    print(f"  Found {len(raw_videos)} video(s).")

    all_videos = sorted(
        [extract_video(v) for v in raw_videos],
        key=lambda x: x["date_raw"],
        reverse=True,
    )

    print("Fetching showcases...")
    raw_showcases = vimeo_get("/me/albums", {"per_page": 100, "fields": "name,link,uri"})
    print(f"  Found {len(raw_showcases)} showcase(s).")

    showcases = []
    for s in raw_showcases:
        showcase_uri = s.get("uri", "")
        showcase_id = showcase_uri.split("/")[-1] if showcase_uri else None
        if not showcase_id:
            continue

        print(f"  Fetching videos for showcase: {s.get('name')}...")
        raw_sv = vimeo_get(
            f"/me/albums/{showcase_id}/videos",
            {"per_page": 100, "fields": "name,link,created_time,description"},
        )
        showcase_videos = sorted(
            [extract_video(v) for v in raw_sv],
            key=lambda x: x["date_raw"],
            reverse=True,
        )

        showcases.append({
            "title": s.get("name", "Untitled Showcase"),
            "url": s.get("link", ""),
            "videos": showcase_videos,
        })

    showcases.sort(key=lambda x: x["title"].lower())

    output = {
        "generated": datetime.now(timezone.utc).strftime("%B %-d, %Y at %-I:%M %p UTC"),
        "videos": all_videos,
        "showcases": showcases,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\ndata.json written: {len(all_videos)} videos, {len(showcases)} showcases.")


if __name__ == "__main__":
    main()
