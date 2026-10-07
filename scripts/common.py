from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

API_BASE = "https://brottsplatskartan.se/api"
APP_ID = "lulea-statistik-polishandelser"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
EVENTS_CSV = DATA_DIR / "events.csv"
MONTHLY_CSV = DATA_DIR / "monthly_summary.csv"
RAW_JSONL = DATA_DIR / "events_raw.jsonl"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": f"{APP_ID}/1.0 (+GitHub Actions)"})

EVENT_COLUMNS = [
    "event_id", "published_datetime", "date", "year", "month",
    "type_original", "headline", "description", "content",
    "title_location", "location_string", "municipality",
    "administrative_area_level_1", "geography_group",
    "latitude", "longitude", "is_summary", "is_multi_location",
    "external_source_link", "brottsplatskartan_url", "retrieved_at"
]


def api_get(path: str, params: dict[str, Any] | None = None, retries: int = 4) -> dict[str, Any]:
    params = dict(params or {})
    params.setdefault("app", APP_ID)
    url = f"{API_BASE}/{path.lstrip('/')}"
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=45)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"API request failed: {url} params={params}") from last_error


def geography_group(municipality: str, area: str) -> str:
    municipality_cf = (municipality or "").strip().casefold()
    area_cf = (area or "").strip().casefold()
    if municipality_cf == "luleå":
        return "Luleå kommun"
    if area_cf == "norrbottens län":
        if municipality_cf:
            return "Övriga Norrbotten"
        return "Norrbotten, okänd kommun"
    return "Utanför Norrbotten"


def parse_event(e: dict[str, Any]) -> dict[str, Any]:
    published = e.get("pubdate_iso8601") or e.get("published_at") or e.get("date")
    dt = None
    if published:
        try:
            dt = pd.to_datetime(published, utc=True)
        except Exception:
            dt = None

    title_type = (e.get("title_type") or e.get("type") or "").strip()
    loc = (e.get("location_string") or e.get("locations") or "").strip()
    municipality = (e.get("administrative_area_level_2") or "").strip()
    area = (e.get("administrative_area_level_1") or "").strip()
    is_summary = title_type.casefold().startswith("sammanfattning")
    is_multi = bool(is_summary or loc.count(",") >= 4)

    return {
        "event_id": e.get("id"),
        "published_datetime": dt.isoformat() if dt is not None else published,
        "date": dt.date().isoformat() if dt is not None else "",
        "year": int(dt.year) if dt is not None else "",
        "month": int(dt.month) if dt is not None else "",
        "type_original": title_type,
        "headline": e.get("headline") or "",
        "description": e.get("description") or e.get("content_teaser") or "",
        "content": e.get("content") or "",
        "title_location": e.get("title_location") or "",
        "location_string": loc,
        "municipality": municipality,
        "administrative_area_level_1": area,
        "geography_group": geography_group(municipality, area),
        "latitude": e.get("lat"),
        "longitude": e.get("lng"),
        "is_summary": is_summary,
        "is_multi_location": is_multi,
        "external_source_link": e.get("external_source_link") or "",
        "brottsplatskartan_url": e.get("permalink") or "",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


def load_existing() -> pd.DataFrame:
    if EVENTS_CSV.exists() and EVENTS_CSV.stat().st_size > 0:
        return pd.read_csv(EVENTS_CSV, dtype={"event_id": "string"})
    return pd.DataFrame(columns=EVENT_COLUMNS)


def save_events(rows: list[dict[str, Any]], append_raw: bool = True) -> pd.DataFrame:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_existing()
    new = pd.DataFrame(rows, columns=EVENT_COLUMNS)
    if not new.empty:
        new["event_id"] = new["event_id"].astype("string")
    all_df = pd.concat([existing, new], ignore_index=True)
    if not all_df.empty:
        all_df = all_df.drop_duplicates(subset=["event_id"], keep="last")
        all_df = all_df.sort_values(["published_datetime", "event_id"], na_position="last")
    all_df.to_csv(EVENTS_CSV, index=False, encoding="utf-8")

    if append_raw and rows:
        with RAW_JSONL.open("a", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    write_monthly_summary(all_df)
    return all_df


def write_monthly_summary(df: pd.DataFrame) -> None:
    columns = ["year", "month", "geography_group", "type_original", "event_count"]
    if df.empty:
        pd.DataFrame(columns=columns).to_csv(MONTHLY_CSV, index=False)
        return
    x = df.copy()
    x["year"] = pd.to_numeric(x["year"], errors="coerce")
    x["month"] = pd.to_numeric(x["month"], errors="coerce")
    x = x.dropna(subset=["year", "month"])
    out = (x.groupby(["year", "month", "geography_group", "type_original"], dropna=False)
             .size().reset_index(name="event_count")
             .sort_values(["year", "month", "geography_group", "event_count"],
                          ascending=[True, True, True, False]))
    out.to_csv(MONTHLY_CSV, index=False, encoding="utf-8")
