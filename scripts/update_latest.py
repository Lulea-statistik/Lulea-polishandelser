from __future__ import annotations

import time
from common import api_get, parse_event, save_events


def main() -> None:
    rows = []
    for page in range(1, 6):
        payload = api_get("events", {"area": "Norrbottens län", "limit": 100, "page": page})
        data = payload.get("data") or []
        if not data:
            break
        rows.extend(parse_event(e) for e in data)
        time.sleep(0.25)
    df = save_events(rows)
    print(f"saved_total={len(df)} refreshed={len(rows)}")


if __name__ == "__main__":
    main()
