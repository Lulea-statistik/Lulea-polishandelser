from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EVENTS = DATA / "events.csv"
OUT = DATA / "norrbotten_place_to_municipality.csv"

SCB_WFS = "https://geodata.scb.se/geoserver/stat/wfs"
LAYERS = {
    "scb_tatort_2023": "stat:Tatorter_2023",
    "scb_smaort_2023": "stat:Smaorter_2023",
}

MUNICIPALITIES = {
    "Arvidsjaur", "Arjeplog", "Boden", "Gällivare", "Haparanda", "Jokkmokk",
    "Kalix", "Kiruna", "Luleå", "Pajala", "Piteå", "Älvsbyn", "Överkalix", "Övertorneå",
}

MUNICIPALITY_ALIASES = {
    "arvidsjaurs kommun": "Arvidsjaur", "arvidsjaur": "Arvidsjaur",
    "arjeplogs kommun": "Arjeplog", "arjeplog": "Arjeplog",
    "bodens kommun": "Boden", "boden": "Boden",
    "gällivare kommun": "Gällivare", "gällivare": "Gällivare",
    "haparanda kommun": "Haparanda", "haparanda": "Haparanda",
    "jokkmokks kommun": "Jokkmokk", "jokkmokk": "Jokkmokk",
    "kalix kommun": "Kalix", "kalix": "Kalix",
    "kiruna kommun": "Kiruna", "kiruna": "Kiruna",
    "luleå kommun": "Luleå", "luleå": "Luleå",
    "pajala kommun": "Pajala", "pajala": "Pajala",
    "piteå kommun": "Piteå", "piteå": "Piteå",
    "älvsbyns kommun": "Älvsbyn", "älvsbyn": "Älvsbyn",
    "överkalix kommun": "Överkalix", "överkalix": "Överkalix",
    "övertorneå kommun": "Övertorneå", "övertorneå": "Övertorneå",
}


def norm(value: str) -> str:
    s = unicodedata.normalize("NFKD", str(value or "").casefold())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9 -]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" -")
    return s


def canonical_municipalities_from_props(props: dict) -> set[str]:
    hits = set()
    for value in props.values():
        if value is None:
            continue
        text = str(value).casefold()
        for alias, canonical in MUNICIPALITY_ALIASES.items():
            if re.search(r"(?<![a-zåäö])" + re.escape(alias) + r"(?![a-zåäö])", text):
                hits.add(canonical)
    return hits


def candidate_place_name(props: dict, layer: str) -> str:
    keys = list(props)
    wanted = ("tatort", "tätort") if "tatort" in layer else ("smaort", "småort")
    ranked = []
    for key in keys:
        nk = norm(key)
        value = props.get(key)
        if value is None or not isinstance(value, str):
            continue
        nv = value.strip()
        if not nv or len(nv) > 120:
            continue
        score = 0
        if any(w in nk for w in wanted):
            score += 5
        if any(x in nk for x in ("namn", "beteckning", "name")):
            score += 4
        if any(x in nk for x in ("kod", "code", "kommun", "lan", "län")):
            score -= 8
        if score > 0:
            ranked.append((score, nv))
    if ranked:
        ranked.sort(reverse=True)
        return ranked[0][1]

    # Conservative fallback: choose a short text value that is not a municipality.
    vals = []
    for key, value in props.items():
        if not isinstance(value, str):
            continue
        v = value.strip()
        if not v or len(v) > 80:
            continue
        if canonical_municipalities_from_props({key: value}):
            continue
        nk = norm(key)
        if any(x in nk for x in ("kod", "code", "lan", "län")):
            continue
        vals.append(v)
    return vals[0] if len(vals) == 1 else ""


def fetch_scb_layer(source: str, typename: str) -> list[dict]:
    params = {
        "service": "WFS",
        "version": "1.1.0",
        "request": "GetFeature",
        "typeName": typename,
        "outputFormat": "application/json",
    }
    r = requests.get(SCB_WFS, params=params, timeout=120, headers={"User-Agent": "lulea-statistik-polishandelser/1.0"})
    r.raise_for_status()
    js = r.json()
    out = []
    for feature in js.get("features", []):
        props = feature.get("properties") or {}
        municipalities = canonical_municipalities_from_props(props)
        if len(municipalities) != 1:
            continue
        municipality = next(iter(municipalities))
        place = candidate_place_name(props, source)
        if not place:
            continue
        out.append({
            "place_name": place,
            "normalized_name": norm(place),
            "municipality": municipality,
            "source": source,
            "confidence": "official",
            "evidence_count": 1,
        })
    return out


def empirical_places() -> list[dict]:
    if not EVENTS.exists():
        return []
    df = pd.read_csv(EVENTS, dtype={"event_id": "string"}, low_memory=False)
    df = df[df["municipality"].isin(MUNICIPALITIES)].copy()
    observations = defaultdict(Counter)

    for _, row in df.iterrows():
        municipality = str(row.get("municipality", "") or "").strip()
        for col in ("title_location",):
            place = str(row.get(col, "") or "").strip()
            if not place:
                continue
            pnorm = norm(place)
            if len(pnorm) < 3 or pnorm in {norm(x) for x in MUNICIPALITIES}:
                continue
            observations[(place, pnorm)][municipality] += 1

    out = []
    for (place, pnorm), counts in observations.items():
        total = sum(counts.values())
        municipality, best = counts.most_common(1)[0]
        share = best / total if total else 0
        if total >= 5 and share >= 0.95:
            out.append({
                "place_name": place,
                "normalized_name": pnorm,
                "municipality": municipality,
                "source": "police_history",
                "confidence": "empirical_high",
                "evidence_count": total,
            })
    return out


def resolve(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["place_name","normalized_name","municipality","source","confidence","evidence_count"])

    df = pd.DataFrame(rows)
    # Any normalized place mapping to multiple municipalities is excluded.
    municipality_counts = df.groupby("normalized_name")["municipality"].nunique()
    safe_names = set(municipality_counts[municipality_counts == 1].index)
    df = df[df["normalized_name"].isin(safe_names)].copy()

    priority = {"official": 0, "empirical_high": 1}
    df["_priority"] = df["confidence"].map(priority).fillna(9)
    df = df.sort_values(["normalized_name", "_priority", "evidence_count"], ascending=[True, True, False])
    df = df.drop_duplicates("normalized_name", keep="first").drop(columns="_priority")
    return df.sort_values(["municipality", "normalized_name"])


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    rows = []
    for source, typename in LAYERS.items():
        part = fetch_scb_layer(source, typename)
        print(f"{source}: {len(part)} safe Norrbotten places")
        rows.extend(part)

    empirical = empirical_places()
    print(f"police_history: {len(empirical)} high-confidence places")
    rows.extend(empirical)

    out = resolve(rows)
    out.to_csv(OUT, index=False, encoding="utf-8")
    print(f"saved {len(out)} unique safe place mappings to {OUT}")


if __name__ == "__main__":
    main()
