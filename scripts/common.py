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
PLACE_DICTIONARY = DATA_DIR / "norrbotten_place_to_municipality.csv"

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



MUNICIPALITY_GROUP_LABELS = {
    "Arvidsjaur": "Arvidsjaurs kommun",
    "Arjeplog": "Arjeplogs kommun",
    "Boden": "Bodens kommun",
    "Gällivare": "Gällivare kommun",
    "Haparanda": "Haparanda kommun",
    "Jokkmokk": "Jokkmokks kommun",
    "Kalix": "Kalix kommun",
    "Kiruna": "Kiruna kommun",
    "Luleå": "Luleå kommun",
    "Pajala": "Pajala kommun",
    "Piteå": "Piteå kommun",
    "Älvsbyn": "Älvsbyns kommun",
    "Överkalix": "Överkalix kommun",
    "Övertorneå": "Övertorneå kommun",
}

OTHER_COUNTY_TITLE_ALIASES = {
    "stockholms län": "Stockholms län",
    "uppsala län": "Uppsala län",
    "södermanlands län": "Södermanlands län",
    "östergötlands län": "Östergötlands län",
    "jönköpings län": "Jönköpings län",
    "kronobergs län": "Kronobergs län",
    "kalmar län": "Kalmar län",
    "gotlands län": "Gotlands län",
    "blekinge län": "Blekinge län",
    "skåne län": "Skåne län",
    "hallands län": "Hallands län",
    "västra götalands län": "Västra Götalands län",
    "värmlands län": "Värmlands län",
    "örebro län": "Örebro län",
    "västmanlands län": "Västmanlands län",
    "dalarnas län": "Dalarnas län",
    "gävleborgs län": "Gävleborgs län",
    "västernorrlands län": "Västernorrlands län",
    "västernorrland län": "Västernorrlands län",
    "jämtlands län": "Jämtlands län",
    "västerbottens län": "Västerbottens län",
    "västerbotten": "Västerbottens län",
}

SWEDISH_COUNTIES = {
    "stockholms län", "uppsala län", "södermanlands län", "östergötlands län",
    "jönköpings län", "kronobergs län", "kalmar län", "gotlands län",
    "blekinge län", "skåne län", "hallands län", "västra götalands län",
    "värmlands län", "örebro län", "västmanlands län", "dalarnas län",
    "gävleborgs län", "västernorrlands län", "jämtlands län",
    "västerbottens län", "norrbottens län",
}

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

EMPIRICAL_SAFE_PLACES = {
    "storheden": "Luleå",
    "bergnaset": "Luleå",
    "gammelstad": "Luleå",
    "rutvik": "Luleå",
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

    # Exact place in the dedicated title-location field is strong evidence.
    if title in LULEA_PLACE_NAMES:
        return LULEA_PLACE_CANONICAL.get(title, title_location.strip())

    parts = [p.strip() for p in loc.split(",") if p.strip()]
    leading_text = ", ".join(parts[:2])

    place_hits = []
    for key in LULEA_PLACE_NAMES:
        if re.search(r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])", leading_text):
            place_hits.append(key)

    unique_places = sorted(set(place_hits))
    if len(unique_places) != 1:
        return ""

    # Do not use county-summary strings that start with Norrbotten as evidence,
    # even when a Lulea place happens to be the second item.
    if parts and parts[0] in {"norrbotten", "norrbottens lan"}:
        return ""

    # Free-text/list matching is only accepted when the same location string
    # does not also name another Norrbotten municipality.
    municipality_hits = set()
    loc_cf = (location_string or "").casefold()
    for key, canonical in NORRBOTTEN_MUNICIPALITIES.items():
        if key in loc_cf:
            municipality_hits.add(canonical)

    other_municipalities = municipality_hits - {"Luleå"}
    if other_municipalities:
        return ""

    key = unique_places[0]
    return LULEA_PLACE_CANONICAL.get(key, key)


_PLACE_LOOKUP: list[tuple[str, str, str]] | None = None


def load_norrbotten_place_dictionary() -> list[tuple[str, str, str]]:
    global _PLACE_LOOKUP
    if _PLACE_LOOKUP is not None:
        return _PLACE_LOOKUP
    rows = []
    if PLACE_DICTIONARY.exists():
        df = pd.read_csv(PLACE_DICTIONARY, dtype=str).fillna("")
        for _, r in df.iterrows():
            normalized = _ascii_fold(str(r.get("normalized_name") or r.get("place_name") or "")).strip()
            normalized = re.sub(r"[^a-z0-9 -]+", " ", normalized)
            normalized = re.sub(r"\s+", " ", normalized).strip(" -")
            municipality = str(r.get("municipality", "") or "").strip()
            place_name = str(r.get("place_name", "") or "").strip()
            if normalized and municipality in MUNICIPALITY_GROUP_LABELS:
                rows.append((normalized, municipality, place_name))
    _PLACE_LOOKUP = sorted(rows, key=lambda x: len(x[0]), reverse=True)
    return _PLACE_LOOKUP


def infer_norrbotten_place(value: str) -> tuple[str, str]:
    text = _ascii_fold(value or "")
    text = re.sub(r"[^a-z0-9 -]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    hits = []
    for normalized, municipality, place_name in load_norrbotten_place_dictionary():
        if len(normalized) < 3:
            continue
        if re.search(r"(?<![a-z0-9])" + re.escape(normalized) + r"(?![a-z0-9])", text):
            hits.append((municipality, place_name))
    municipalities = sorted(set(m for m, _ in hits))
    if len(municipalities) != 1:
        return "", ""
    municipality = municipalities[0]
    place_names = sorted(set(p for m, p in hits if m == municipality), key=len, reverse=True)
    return municipality, (place_names[0] if place_names else "")


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
    if len(unique_hits) > 1:
        return "", "ambiguous_municipality_names"

    place = infer_lulea_place(title_location, location_string)
    if place:
        return "Luleå", "lulea_place_name"

    # Empiriskt validerade ortnamn från säkert kommunbestämda historiska
    # icke-sammanfattningar. Dessa används endast när ingen explicit
    # Norrbottenskommun ovan har identifierats och alla träffar pekar på
    # samma kommun.
    empirical_text = _ascii_fold(" ".join([title_location or "", location_string or ""]))
    empirical_parts = [p.strip() for p in (location_string or "").split(",") if p.strip()]
    empirical_hits = set()
    for place_key, canonical in EMPIRICAL_SAFE_PLACES.items():
        if re.search(r"(?<![a-z0-9])" + re.escape(place_key) + r"(?![a-z0-9])", empirical_text):
            empirical_hits.add(canonical)
    if len(empirical_hits) == 1 and len(empirical_parts) <= 4:
        # Om källans länsfält uttryckligen pekar på annat län ska ingen
        # Norrbottenklassning göras här.
        if "västerbottens län" not in loc_cf and not re.search(r"(?<![a-zåäö])västerbotten(?![a-zåäö])", loc_cf):
            return next(iter(empirical_hits)), "empirical_place"

    # Ortreferensen är en konservativ fallback. Den används inte när
    # title_location pekar ut en annan, icke-generisk plats som inte själv
    # kan kopplas till samma Norrbottenskommun.
    generic_titles = {"", "norrbotten", "norrbottens län", "norrbottens lan"}
    title_norm = _ascii_fold(title_location or "").strip()
    title_inferred = ""
    if title_norm not in generic_titles:
        title_inferred, _ = infer_norrbotten_place(title_location)
        if not title_inferred:
            return "", "title_location_conflict"

    # Långa platslistor är ofta länssammanställningar/kontroller som berör
    # flera orter. Hellre okänd kommun än falsk precision.
    parts = [p.strip() for p in (location_string or "").split(",") if p.strip()]
    if len(parts) > 5:
        return "", "multi_location_ambiguous"

    loc_cf = (location_string or "").casefold()
    if "västerbottens län" in loc_cf or re.search(r"(?<![a-zåäö])västerbotten(?![a-zåäö])", loc_cf):
        return "", "cross_county_ambiguous"

    inferred, inferred_place = infer_norrbotten_place(" ".join([title_location or "", location_string or ""]))
    if inferred and (not title_inferred or title_inferred == inferred):
        return inferred, "place_dictionary"

    return "", "unknown"



def infer_municipality(municipality: str, title_location: str, location_string: str) -> str:
    return infer_municipality_detail(municipality, title_location, location_string)[0]


def geography_group(
    municipality: str,
    area: str,
    municipality_source: str = "",
    title_location: str = "",
) -> str:
    municipality_clean = (municipality or "").strip()
    area_cf = (area or "").strip().casefold()
    title_cf = (title_location or "").strip().casefold()
    source = (municipality_source or "").strip()
    if municipality_clean in MUNICIPALITY_GROUP_LABELS:
        return MUNICIPALITY_GROUP_LABELS[municipality_clean]
    if title_cf in OTHER_COUNTY_TITLE_ALIASES:
        return "Övriga Sverige"
    if area_cf == "norrbottens län" and source == "ambiguous_municipality_names":
        return "Flera kommuner i Norrbotten"
    if area_cf == "norrbottens län":
        return "Norrbotten, okänd kommun"
    if area_cf in SWEDISH_COUNTIES:
        return "Övriga Sverige"
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
    if is_summary and municipality_source == "place_dictionary":
        municipality = ""
        municipality_source = "summary_container"
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
        "geography_group": geography_group(municipality, area, municipality_source, title_location),
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

        # En länssammanfattning kan innehålla flera kommuner och får därför
        # aldrig flyttas som hel behållare med ortreferensen. Kommunfördelning
        # sker i stället på de extraherade underhändelserna.
        is_summary_mask = all_df["is_summary"].astype(str).str.casefold().isin(["true", "1"])

        # Rensa tidigare ortbaserade tilldelningar på sammanfattningsbehållare.
        prior_summary_place = (
            is_summary_mask
            & all_df["municipality_source"].fillna("").astype(str).eq("place_dictionary")
        )
        all_df.loc[prior_summary_place, "municipality"] = ""
        all_df.loc[prior_summary_place, "municipality_source"] = "summary_container"

        # Kör om kommuninferensen endast för historiska icke-sammanfattningar
        # som fortfarande saknar kommun.
        missing_mask = (
            all_df["municipality"].fillna("").astype(str).str.strip().eq("")
            & ~is_summary_mask
        )
        for idx in all_df.index[missing_mask]:
            municipality, source = infer_municipality_detail(
                "",
                str(all_df.at[idx, "title_location"] or ""),
                str(all_df.at[idx, "location_string"] or ""),
            )
            if municipality:
                all_df.at[idx, "municipality"] = municipality
                all_df.at[idx, "municipality_source"] = source

        # Räkna därefter om geografisk grupp för hela historiken.
        all_df["geography_group"] = all_df.apply(
            lambda r: geography_group(
                str(r.get("municipality", "") or ""),
                str(r.get("administrative_area_level_1", "") or ""),
                str(r.get("municipality_source", "") or ""),
                str(r.get("title_location", "") or ""),
            ),
            axis=1,
        )
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
