from __future__ import annotations

import argparse
import time
from common import api_get, parse_event, save_events


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--area", default="Norrbottens län")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--max-pages", type=int, default=10000)
    p.add_argument("--sleep", type=float, default=0.35)
    args = p.parse_args()

    page = 1
    rows = []
    seen = set()
    last_page = None

    while page <= args.max_pages:
        payload = api_get("events", {
            "area": args.area,
            "limit": args.limit,
            "page": page,
        })
        data = payload.get("data") or []
        links = payload.get("links") or {}
        last_page = links.get("last_page") or last_page
        print(f"page={page} rows={len(data)} last_page={last_page}")
        if not data:
            break

        for e in data:
            event_id = str(e.get("id"))
            if event_id in seen:
                continue
            seen.add(event_id)
            rows.append(parse_event(e))

        if last_page and page >= int(last_page):
            break
        page += 1
        time.sleep(args.sleep)

    df = save_events(rows)
    print(f"saved_total={len(df)} fetched_unique={len(rows)}")


if __name__ == "__main__":
    main()
