from __future__ import annotations

import json
import re
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
    "title_location", "location_string", "municipality", "municipality_source",
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


NORRBOTTEN_MUNICIPALITIES = {
    "arvidsjaur": "Arvidsjaur",
    "arjeplog": "Arjeplog",
    "boden": "Boden",
    "gällivare": "Gällivare",
    "haparan­da": "Haparanda",
    "haparanda": "Haparanda",
    "jokkmokk": "Jokkmokk",
    "kalix": "Kalix",
    "kiruna": "Kiruna",
    "luleå": "Luleå",
    "pajala": "Pajala",
    "piteå": "Piteå",
    "älvsbyn": "Älvsbyn",
    "överkalix": "Överkalix",
    "övertorneå": "Övertorneå",
}

# Officiella omrades-, by- och stadsdelsnamn publicerade av Lulea kommun.
# Anvands endast nar API:t saknar kommun. Generiska/otydliga namn ar medvetet
# exkluderade fran fri textsokning for att minimera felklassning.
LULEA_PLACE_NAMES = {
    "ale", "alvik", "antnas", "avan", "balinge", "ersnas", "falltrask",
    "kallax", "klovertrask", "mattsund", "moron", "vastmark",
    "bensbyn", "bjorsbyn", "brandon", "orarna", "borjelslandet", "person",
    "rutvik", "smedsbyn", "sunderbyn", "angesbyn",
    "hogson", "jamton", "mjofjarden", "niemisel", "orrbyn", "prastholm",
    "ranea", "vita", "berg-naset", "bergnaset", "bergviken", "bjorkskatan",
    "gammelstad", "hertson", "kronan", "lerbacken", "lulsundet",
    "lovskatan", "malmudden", "mjolkudden", "notviken", "porson",
    "skurholmen", "svartostaden", "ornaset"
}

LULEA_PLACE_CANONICAL = {
    "ale":"Ale","alvik":"Alvik","antnas":"Antnas","avan":"Avan","balinge":"Balinge",
    "ersnas":"Ersnas","falltrask":"Falltrask","kallax":"Kallax","klovertrask":"Klovertrask",
    "mattsund":"Mattsund","moron":"Moron","vastmark":"Vastmark","bensbyn":"Bensbyn",
    "bjorsbyn":"Bjorsbyn","brandon":"Brandon","orarna":"Orarna","borjelslandet":"Borjelslandet",
    "person":"Person","rutvik":"Rutvik","smedsbyn":"Smedsbyn","sunderbyn":"Sunderbyn",
    "angesbyn":"Angesbyn","hogson":"Hogson","jamton":"Jamton","mjofjarden":"Mjofjarden",
    "niemisel":"Niemisel","orrbyn":"Orrbyn","prastholm":"Prastholm","ranea":"Ranea",
    "vita":"Vita","bergnaset":"Bergnaset","berg-naset":"Bergnaset","bergviken":"Bergviken",
    "bjorkskatan":"Bjorkskatan","gammelstad":"Gammelstad","hertson":"Hertson","kronan":"Kronan",
    "lerbacken":"Lerbacken","lulsundet":"Lulsundet","lovskatan":"Lovskatan","malmudden":"Malmudden",
    "mjolkudden":"Mjolkudden","notviken":"Notviken","porson":"Porson","skurholmen":"Skurholmen",
    "svartostaden":"Svartostaden","ornaset":"Ornaset"
}

def _fold_place_text(value: str) -> str:
    return (value or "").casefold().translate(str.maketrans({
        "a":"a"
    }))

def _ascii_fold(value: str) -> str:
    return (value or "").casefold().translate(str.maketrans({
        "å":"a","ä":"a","ö":"o","é":"e"
    }))

def infer_lulea_place(title_location: str, location_string: str) -> str:
    """Return a high-confidence Lulea place name, otherwise empty string."""
    title = _ascii_fold((title_location or "").strip())
    loc = _ascii_fold(location_string or "")

    if title in LULEA_PLACE_NAMES:
        return LULEA_PLACE_CANONICAL.get(title, title_location.strip())

    hits = []
    for key in LULEA_PLACE_NAMES:
        if re.search(r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])", loc):
            hits.append(key)

    unique_hits = sorted(set(hits))
    if len(unique_hits) == 1:
        key = unique_hits[0]
        return LULEA_PLACE_CANONICAL.get(key, key)
    return ""

def infer_municipality_detail(municipality: str, title_location: str, location_string: str) -> tuple[str, str]:
    """Infer municipality and record why the assignment was made."""
    raw = (municipality or "").strip()
    if raw:
        return raw.replace(" kommun", "").replace(" Kommun", "").strip(), "api"

    title_cf = (title_location or "").strip().casefold()
    if title_cf in NORRBOTTEN_MUNICIPALITIES:
        return NORRBOTTEN_MUNICIPALITIES[title_cf], "municipality_name"

    loc_cf = (location_string or "").casefold()
    hits = []
    for key, canonical in NORRBOTTEN_MUNICIPALITIES.items():
        if key in loc_cf:
            hits.append(canonical)
    unique_hits = sorted(set(hits))
    if len(unique_hits) == 1:
        return unique_hits[0], "municipality_name"

    place = infer_lulea_place(title_location, location_string)
    if place:
        return "Luleå", "lulea_place_name"

    return "", "unknown"



def infer_municipality(municipality: str, title_location: str, location_string: str) -> str:
    return infer_municipality_detail(municipality, title_location, location_string)[0]


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
    municipality_api = (e.get("administrative_area_level_2") or "").strip()
    area = (e.get("administrative_area_level_1") or "").strip()
    title_location = (e.get("title_location") or "").strip()
    municipality, municipality_source = infer_municipality_detail(municipality_api, title_location, loc)
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
        "title_location": title_location,
        "location_string": loc,
        "municipality": municipality,
        "municipality_source": municipality_source,
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
