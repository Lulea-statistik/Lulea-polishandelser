from __future__ import annotations

import html
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "events.csv"
OUT = ROOT / "data" / "summary_details.csv"
OUT_MONTHLY = ROOT / "data" / "summary_details_monthly.csv"

MUNICIPALITIES = {
    "arvidsjaur": "Arvidsjaur",
    "arjeplog": "Arjeplog",
    "boden": "Boden",
    "gällivare": "Gällivare",
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

# Högprecisionsklassning av de typer som återkommer i Polisens länssammanfattningar.
# Ordningen är viktig: mer specifika mönster ligger före bredare.
TYPE_PATTERNS = [
    (r"\b(viltolycka|renolycka|rådjursolycka|älgolycka|trafikolycka[^\n,.]{0,30}\bvilt|kollider\w* med (älg|ren|rådjur|hjort)|påkö\w* (älg|ren|rådjur|hjort))\b", "Trafikolycka,  vilt"),
    (r"\bsingelolycka\b", "Trafikolycka"),
    (r"\b(drograttfylleri|rattfylleri)\b", "Rattfylleri"),
    (r"\b(grov olovlig körning|olovlig körning)\b", "Olovlig körning"),
    (r"\btrafikkontroll\b|\bhastighetskontroll\b|\bnykterhetskontroll\b", "Trafikkontroll"),
    (r"\btrafikbrott\b|\bvårdslöshet i trafik\b", "Trafikbrott"),
    (r"\btrafikhinder\b", "Trafikhinder"),
    (r"\btrafik\w*olycka\b|\bkollision\b|\bkrock\w*\b", "Trafikolycka"),
    (r"\barbetsplatsolycka\b|\bfallolycka\b", "Arbetsplatsolycka"),
    (r"\bmisshand\w*\b", "Misshandel"),
    (r"\bnarkotik\w*\b", "Narkotikabrott"),
    (r"\bstöld/inbrott\b|\bstöld genom inbrott\b", "Inbrott"),
    (r"\binbrott\w*\b", "Inbrott"),
    (r"\bringa stöld\b|\bsnatt\w*\b", "Stöld,  ringa"),
    (r"\bstöld\b|\bstul\w*\b|\btillgrip\w*\b", "Stöld"),
    (r"\bskadegör\w*\b", "Skadegörelse"),
    (r"\b(fylleri|lob|tillnyktring)\b", "Fylleri/LOB"),
    (r"\bolaga hot\b", "Olaga hot"),
    (r"\bofred\w*\b|\bförargelseväckande\b", "Ofredande/förargelse"),
    (r"\bknivlagen\b|\bbrott mot knivlagen\b", "Knivlagen"),
    (r"\bvapenlagen\b|\bbrott mot vapenlagen\b|\bvapenbrott\b", "Vapenlagen"),
    (r"\bbrand\w*\b", "Brand"),
    (r"\brån\w*\b", "Rån"),
    (r"\bfjällräddning\b", "Fjällräddning"),
    (r"\bförsvunn\w*\b", "Försvunnen person"),
    (r"\b(våld|hot) mot tjänsteman\b|\bvåld/hot mot tjänsteman\b|\bvåldsamt motstånd\b", "Våld/hot mot tjänsteman"),
    (r"\bvåldtäkt\w*\b|\bsexualbrott\b|\bsexuellt ofred\w*\b", "Sexualbrott"),
    (r"\b(försök till mord|mord|dråp)\b", "Mord/dråp"),
    (r"\b(olaga intrång|hemfridsbrott)\b", "Olaga intrång/hemfridsbrott"),
    (r"\b(bombhot|farligt föremål)\b", "Farligt föremål,  misstänkt"),
    (r"\b(skottlossning|detonation|explosion)\b", "Skottlossning/explosion"),
    (r"\bbedrägeri\b", "Bedrägeri"),
    (r"\bhäleri\b", "Häleri"),
    (r"\banträffat gods\b|\bupphittat föremål\b", "Anträffat gods"),
    (r"\bkontroll (?:av )?(?:person|fordon|person/fordon)\b", "Kontroll person/fordon"),
    (r"\bräddningsinsats\b", "Räddningsinsats"),
    (r"\bsjukdom/olycksfall\b", "Sjukdom/olycksfall"),
    (r"\bdjur\b", "Djur"),
]

TIME_LINE_RE = re.compile(
    r"(?im)(?:^|\n)\s*"
    r"(?:(?P<prefix>[^\n,]{2,90})\s*,\s*)?"
    r"(?:kl\.?\s*)?(?P<time>[0-2]?\d[:.]\d{2})"
    r"\s*[,;:-]?\s*(?P<rest>[^\n]{0,240})"
)

# Specialformat där både typ och plats står före klockslaget:
# "Ringa stöld (snatteri), Gällivare, Kl 15:15"
PRE_TIME_HEADER_RE = re.compile(
    r"(?im)^\s*(?P<label>[^\n]{2,100}?),\s*"
    r"(?P<place>[^\n,]{2,60}?),\s*(?:kl\.?\s*)"
    r"(?P<time>[0-2]?\d[:.]\d{2})\b"
)

NON_EVENT_RE = re.compile(
    r"(?i)^(?:lugnt|inget att rapportera|inga händelser att rapportera|"
    r"uppdatering|norrbotten\s*$|kl\s*[0-2]?\d[:.]\d{2}\s*[-–]\s*[0-2]?\d[:.]\d{2})"
)
TAG_BREAK_RE = re.compile(r"(?i)<\s*(?:br\s*/?|/?p|/?div|/?li|/?h\d)\s*>")
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"[ \t\xa0]+")
BLANK_RE = re.compile(r"\n{3,}")


def clean_text(value: str) -> str:
    s = html.unescape(value or "")
    s = TAG_BREAK_RE.sub("\n", s)
    s = TAG_RE.sub(" ", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = SPACE_RE.sub(" ", s)
    s = "\n".join(line.strip() for line in s.split("\n"))
    s = BLANK_RE.sub("\n\n", s)
    return s.strip()


def municipality_from_text(value: str) -> str:
    p = (value or "").casefold()
    hits = []
    for key, canonical in MUNICIPALITIES.items():
        if re.search(r"(?<![a-zåäö])" + re.escape(key) + r"(?![a-zåäö])", p):
            hits.append(canonical)
    hits = sorted(set(hits))
    return hits[0] if len(hits) == 1 else ""


def geography(municipality: str) -> str:
    if municipality == "Luleå":
        return "Luleå kommun"
    if municipality:
        return "Övriga Norrbotten"
    return "Norrbotten, okänd kommun"


def classify_type(value: str) -> str:
    text = (value or "").casefold()
    for pattern, label in TYPE_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            return label
    return ""


def source_text(row: pd.Series) -> str:
    # content är den fullständiga sammanfattningstexten i normalfallet.
    # description/headline är ofta utdrag eller kopior av samma text. Att
    # konkatenera alla tre skapade därför dubbla tidsstämplar och falska
    # underhändelser. Använd i stället första tillgängliga fullvärdiga källa.
    for col in ("content", "description", "headline"):
        v = row.get(col, "")
        if pd.notna(v) and str(v).strip():
            return clean_text(str(v))
    return ""


def first_meaningful_line(body: str) -> str:
    for line in (body or "").split("\n"):
        line = line.strip(" -–—.;:")
        if not line:
            continue
        if line.casefold().startswith(("polisen ", "uppdatering", "text av")):
            continue
        return line
    return ""


def extract_row(row: pd.Series) -> list[dict]:
    text = source_text(row)
    matches = list(TIME_LINE_RE.finditer(text))
    out = []

    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip(" \n-–—")
        prefix = SPACE_RE.sub(" ", match.group("prefix") or "").strip(" .;:-")
        rest = SPACE_RE.sub(" ", match.group("rest") or "").strip(" .;:-")
        first_line = first_meaningful_line(body)
        header = ", ".join(x for x in (prefix, rest) if x)

        # Tydliga status-/uppdateringsrader är inte egna händelser.
        if NON_EVENT_RE.search(header) and not classify_type(body[:250]):
            continue

        # Tidsintervall som beskriver rapportperioden, t.ex. "04:00 - 06:30
        # Inget att rapportera", är inte två underhändelser.
        before = text[max(0, match.start() - 8):match.start()]
        after = text[match.end():match.end() + 18]
        range_context = (before + match.group(0) + after).casefold()
        if re.search(r"\b[0-2]?\d[:.]\d{2}\s*[-–—]\s*[0-2]?\d[:.]\d{2}\b", range_context):
            if re.search(r"inget att rapportera|lugnt|inga händelser", header + " " + body[:180], re.I):
                continue

        # Klassificera först rubrikdelen, därefter första brödtextraden och
        # slutligen början av hela segmentet.
        event_type = classify_type(header)
        if not event_type:
            event_type = classify_type(first_line)
        if not event_type:
            event_type = classify_type(header + "\n" + body[:500])

        municipality = municipality_from_text(header)
        if not municipality:
            municipality = municipality_from_text(first_line)

        # Behåll även tidsatta händelser där brottstypen inte kan klassas.
        # De ska räknas i totalen men särredovisas som oklassificerade.
        if not event_type:
            substantive = (header + " " + first_line).strip()
            if len(substantive) < 5:
                continue
            event_type = "Övrigt/oklassificerad"

        parts = [p.strip() for p in re.split(r"\s*[,;/]\s*", header) if p.strip()]
        place_parts = []
        for part in parts:
            if municipality and part.casefold() == municipality.casefold():
                continue
            if classify_type(part):
                continue
            if re.fullmatch(r"(?:kl\.?\s*)?[0-2]?\d[:.]\d{2}", part, flags=re.I):
                continue
            place_parts.append(part)
        place = ", ".join(place_parts[:2]).strip()

        confidence = "high" if municipality and event_type != "Övrigt/oklassificerad" else "medium"
        out.append({
            "parent_event_id": row.get("event_id", ""),
            "date": row.get("date", ""),
            "year": row.get("year", ""),
            "month": row.get("month", ""),
            "summary_type": row.get("type_original", ""),
            "time": match.group("time").replace(".", ":"),
            "event_type_extracted": event_type,
            "place_text": place,
            "municipality": municipality,
            "geography_group": geography(municipality),
            "description": body,
            "source_link": row.get("external_source_link", "") or row.get("brottsplatskartan_url", ""),
            "confidence": confidence,
        })
    # Fånga specialformat med typ + plats före klockslag. Lägg bara till om
    # samma tid inte redan fångats av standardparsern.
    existing_times = {str(x.get("time", "")) for x in out}
    for match in PRE_TIME_HEADER_RE.finditer(text):
        t = match.group("time").replace(".", ":")
        if t in existing_times:
            continue
        label = match.group("label").strip(" .;:-")
        place_label = match.group("place").strip(" .;:-")
        event_type = classify_type(label)
        municipality = municipality_from_text(place_label)
        if not event_type:
            continue

        line_end = text.find("\n", match.end())
        if line_end < 0:
            line_end = len(text)
        body = text[match.end():line_end].strip(" .;:-")
        out.append({
            "parent_event_id": row.get("event_id", ""),
            "date": row.get("date", ""),
            "year": row.get("year", ""),
            "month": row.get("month", ""),
            "summary_type": row.get("type_original", ""),
            "time": t,
            "event_type_extracted": event_type,
            "place_text": place_label,
            "municipality": municipality,
            "geography_group": geography(municipality),
            "description": body,
            "source_link": row.get("external_source_link", "") or row.get("brottsplatskartan_url", ""),
            "confidence": "high" if municipality else "medium",
        })
        existing_times.add(t)

    # Fånga tydliga rubrikrader utan klockslag, t.ex. "Misshandel, Luleå".
    # Dessa förekommer framför allt i nyare sammanfattningar.
    lines = [ln.strip() for ln in text.split("\n")]
    timed_line_indexes = {
        i for i, ln in enumerate(lines)
        if re.search(r"(?i)(?:^|[\s,;/\-–—])(?:kl\.?\s*)?[0-2]?\d[:.]\d{2}(?:\s|[,;:/\-–—]|$)", ln)
    }
    existing_keys = {
        (str(x["event_type_extracted"]).casefold(), str(x["municipality"]).casefold(), str(x["description"])[:80].casefold())
        for x in out
    }

    for i, line in enumerate(lines):
        if not line or i in timed_line_indexes:
            continue
        if i > 0 and (i - 1) in timed_line_indexes:
            # Vanligt format där typ står på raden efter en tidsatt platsrad;
            # den är redan del av den tidsatta händelsen.
            continue

        event_type = classify_type(line)
        municipality = municipality_from_text(line)
        if not event_type or not municipality:
            continue
        if NON_EVENT_RE.search(line):
            continue

        body_lines = []
        for j in range(i + 1, min(len(lines), i + 8)):
            nxt = lines[j].strip()
            if not nxt:
                if body_lines:
                    break
                continue
            if j in timed_line_indexes:
                break
            # Ny tydlig typ+kommun-rubrik markerar nästa händelse.
            if classify_type(nxt) and municipality_from_text(nxt):
                break
            body_lines.append(nxt)
        body = " ".join(body_lines).strip()
        key = (event_type.casefold(), municipality.casefold(), body[:80].casefold())
        if key in existing_keys:
            continue
        existing_keys.add(key)

        out.append({
            "parent_event_id": row.get("event_id", ""),
            "date": row.get("date", ""),
            "year": row.get("year", ""),
            "month": row.get("month", ""),
            "summary_type": row.get("type_original", ""),
            "time": "",
            "event_type_extracted": event_type,
            "place_text": line,
            "municipality": municipality,
            "geography_group": geography(municipality),
            "description": body,
            "source_link": row.get("external_source_link", "") or row.get("brottsplatskartan_url", ""),
            "confidence": "medium",
        })

    # Sekundär rubrikextraktion kan ibland återfånga samma händelse utan
    # klockslag, t.ex. "Hastighetskontroll, Boden Kl. 17.30". Om en tidsatt
    # träff med samma typ och kommun redan finns behålls den tidsatta posten.
    timed_pairs = {
        (str(x.get("event_type_extracted","")).casefold(), str(x.get("municipality","")).casefold())
        for x in out if str(x.get("time","")).strip()
    }
    timed_types = {
        str(x.get("event_type_extracted","")).casefold()
        for x in out if str(x.get("time","")).strip()
    }
    if timed_pairs:
        cleaned = []
        for x in out:
            if str(x.get("time","")).strip():
                cleaned.append(x)
                continue
            pair = (
                str(x.get("event_type_extracted","")).casefold(),
                str(x.get("municipality","")).casefold(),
            )
            etype = pair[0]
            # Exakt typ+kommun-match: säkert dubblettfall.
            if pair in timed_pairs:
                continue
            # Om det bara finns en tidsatt händelse av denna typ i texten och
            # den saknar kommun, behandla en otidsatt rubrik av samma typ som
            # samma händelse. Detta fångar t.ex. "Hastighetskontroll, Boden
            # Kl. 17.30" utan att slå ihop flera separata tidsatta händelser.
            matching_timed = [
                y for y in out
                if str(y.get("time","")).strip()
                and str(y.get("event_type_extracted","")).casefold() == etype
            ]
            if (
                etype in timed_types
                and len(matching_timed) == 1
                and not str(matching_timed[0].get("municipality","")).strip()
            ):
                continue
            cleaned.append(x)
        out = cleaned

    return out

def main() -> None:
    if not EVENTS.exists() or EVENTS.stat().st_size == 0:
        raise SystemExit("data/events.csv saknas eller är tom")

    df = pd.read_csv(EVENTS, dtype={"event_id": "string"}, low_memory=False)
    is_summary = df.get("is_summary", pd.Series(False, index=df.index)).astype(str).str.casefold().isin(["true", "1"])
    type_summary = df.get("type_original", pd.Series("", index=df.index)).fillna("").str.casefold().str.startswith("sammanfattning")
    summaries = df[is_summary | type_summary].copy()

    records = []
    for _, row in summaries.iterrows():
        records.extend(extract_row(row))

    cols = [
        "parent_event_id", "date", "year", "month", "summary_type", "time",
        "event_type_extracted", "place_text", "municipality", "geography_group",
        "description", "source_link", "confidence",
    ]
    out = pd.DataFrame(records, columns=cols)
    if not out.empty:
        out = out.drop_duplicates(
            subset=["parent_event_id", "time", "event_type_extracted", "place_text"],
            keep="first",
        ).sort_values(["date", "time", "parent_event_id"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False, encoding="utf-8")

    mcols = ["year", "month", "geography_group", "event_type_extracted", "event_count"]
    if out.empty:
        monthly = pd.DataFrame(columns=mcols)
    else:
        out["year"] = pd.to_numeric(out["year"], errors="coerce")
        out["month"] = pd.to_numeric(out["month"], errors="coerce")
        monthly = (
            out.dropna(subset=["year", "month"])
            .groupby(["year", "month", "geography_group", "event_type_extracted"], dropna=False)
            .size()
            .reset_index(name="event_count")
            .sort_values(
                ["year", "month", "geography_group", "event_count"],
                ascending=[True, True, True, False],
            )
        )
    monthly.to_csv(OUT_MONTHLY, index=False, encoding="utf-8")

    print(
        f"summaries={len(summaries)} extracted_subevents={len(out)} "
        f"lulea={int((out['municipality'] == 'Luleå').sum()) if not out.empty else 0}"
    )


if __name__ == "__main__":
    main()
