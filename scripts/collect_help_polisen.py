"""Archive publication metadata from Polisen's 'Hjälp polisen' RSS.

This is a separate publication series, NOT an incident series.
No article body, photos, or personal-identifying details are scraped.
"""
from __future__ import annotations
import csv
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "help_polisen.csv"
FEED = "https://polisen.se/aktuellt/rss/hela-landet/hjalp-polisen-rss/"
FIELDS = ["source_url", "published_at", "title", "description", "first_seen_at", "last_seen_at"]

def tag_text(parent, key):
    element = parent.find(key)
    return (element.text or "").strip() if element is not None else ""

def main():
    now = datetime.now(timezone.utc).isoformat()
    req = urllib.request.Request(FEED, headers={"User-Agent": "Lulea-statistik research dashboard contact via GitHub"})
    with urllib.request.urlopen(req, timeout=35) as response:
        payload = response.read(3_000_000)
    root = ET.fromstring(payload)
    items = root.findall(".//item")
    if not items:
        raise RuntimeError("RSS feed contained no items; retaining existing history")
    existing = {}
    if OUTPUT.exists():
        with OUTPUT.open(encoding="utf-8", newline="") as f:
            existing = {r["source_url"]: r for r in csv.DictReader(f) if r.get("source_url")}
    added = 0
    for item in items:
        url = tag_text(item, "link") or tag_text(item, "guid")
        if not url.startswith("https://polisen.se/aktuellt/hjalp-polisen/"):
            continue
        title = tag_text(item, "title")
        description = tag_text(item, "description")
        pub = tag_text(item, "pubDate")
        try:
            published = parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat() if pub else ""
        except (ValueError, TypeError, IndexError):
            published = ""
        previous = existing.get(url, {})
        if not previous:
            added += 1
        existing[url] = dict(source_url=url, published_at=published or previous.get("published_at", ""),
                             title=title or previous.get("title", ""),
                             description=description or previous.get("description", ""),
                             first_seen_at=previous.get("first_seen_at", now),
                             last_seen_at=now)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(existing.values(), key=lambda r: (r["published_at"], r["source_url"])))
    print(f"feed_items={len(items)} new_publications={added} archived_total={len(existing)}")

if __name__ == "__main__":
    main()
