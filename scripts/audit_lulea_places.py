#!/usr/bin/env python3
"""Reproducerbar deskriptiv platsordsanalys för Luleåkommunens polishändelser."""
import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/events.csv"
DETAIL = ROOT / "data/audit_lulea_place_mentions.csv"
SUMMARY = ROOT / "data/audit_lulea_place_summary.csv"
FIELDS = ("title_location", "location_string", "headline", "description", "content")
KNOWN = {
    "Centrum": ["centrum","innerstaden","stadsviken","charlottendal","norra hamn","norra hamnen",
                "sodra hamn","sodra hamnen","ostermalm","gultzauudden","vastra stranden",
                "oscarsvarv","storgatan","smedjegatan","radstugatan","radstugugatan",
                "jarnvagsstation","jarnvagsstationen","centralstation","kopmantorget"],
    "Bergnäset": ["bergnaset"], "Bergviken": ["bergviken"], "Björkskatan": ["bjorkskatan"],
    "Gammelstad": ["gammelstad"], "Hertsön": ["hertson"], "Hertsöheden": ["hertsoheden"],
    "Kallkällan": ["kallkallan"], "Karlsvik": ["karlsvik"], "Kronan": ["kronan"],
    "Lerbäcken": ["lerbacken"], "Mjölkudden": ["mjolkudden"], "Munksund": ["munksund"],
    "Notviken": ["notviken"], "Porsön": ["porson"], "Råneå": ["ranea"],
    "Skurholmen": ["skurholmen"], "Storheden": ["storheden"], "Sunderbyn": ["sunderbyn"],
    "Svartöstaden": ["svartostaden"], "Örnäset": ["ornaset"]
}
# Gatutyper och namnbärande platstyper; korta rena ortnamn fångas via KNOWN.
SUFFIX = r"(?:gatan|vagen|vag|grand|stigen|leden|torget|plan|kajen|hamnen|hamn|stationen|station|platsen|parken|bron|udden)"
CANDIDATE = re.compile(r"(?<![a-z])(?:[a-z]{3,22}[ -]){0,2}[a-z]{3,27}" + SUFFIX + r"(?![a-z])")
STOP = {"kommun","lulea kommun","norrbottens lan","norrbotten","okand plats","centrala lulea"}
def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "").casefold())
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c)))
PATTERNS = {name: re.compile(r"(?<![a-z])"+re.escape(name)+r"(?![a-z])") for name in sorted({n for a in KNOWN.values() for n in a},key=len,reverse=True)}
def mentions(text):
    s = norm(text)
    found = {k for k,p in PATTERNS.items() if p.search(s)}
    found |= {m.group().strip() for m in CANDIDATE.finditer(s)}
    return found - STOP
def main():
    results = defaultdict(lambda: [set(),set(),Counter(),Counter()])
    totals = Counter()
    seen = set()
    with SOURCE.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("geography_group") or "").strip() != "Luleå kommun":
                continue
            eid = (row.get("event_id") or "").strip()
            if eid and eid in seen: continue
            if eid: seen.add(eid)
            totals["events"] += 1
            place = mentions(" ".join(row.get(k,"") or "" for k in FIELDS[:2]))
            narrative = mentions(" ".join(row.get(k,"") or "" for k in FIELDS[2:]))
            if place: totals["events_with_place_match"] += 1
            if narrative: totals["events_with_narrative_match"] += 1
            for name in place | narrative:
                rec = results[name]
                if name in place: rec[0].add(eid or str(totals["events"]))
                if name in narrative: rec[1].add(eid or str(totals["events"]))
                if (row.get("year") or "").isdigit(): rec[2][row["year"]] += 1
                rec[3][(row.get("type_original") or "Okänd")] += 1
    DETAIL.parent.mkdir(parents=True,exist_ok=True)
    with DETAIL.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f)
        w.writerow(["platsord_normaliserat","unik_handelser_platsfalt","unik_handelser_loptext","unika_handelser_totalt_max_sum","indikativ_klass","vanligaste_handelsetyp","antal_av_den_typen"])
        for name,rec in sorted(results.items(),key=lambda item:(-len(item[1][0]|item[1][1]),item[0])):
            category=next((d for d,aliases in KNOWN.items() if name in aliases),"Ej klassificerad/kandidat")
            typ,n=rec[3].most_common(1)[0]
            w.writerow([name,len(rec[0]),len(rec[1]),len(rec[0]|rec[1]),category,typ,n])
    with SUMMARY.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["matt","antal"])
        for key in ["events","events_with_place_match","events_with_narrative_match"]:
            w.writerow([key,totals[key]])
        w.writerow(["unika_platsord",len(results)])
        w.writerow(["unika_platsord_med_traf_fran_platsfalt",sum(bool(v[0]) for v in results.values())])
    print("Lulea events:",totals["events"],"place candidates:",len(results))
if __name__=="__main__":main()
