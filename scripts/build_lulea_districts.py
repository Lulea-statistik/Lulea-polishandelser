#!/usr/bin/env python3
"""Försiktig delområdesklassning för enbart Luleå kommun.

Ingen geokodning eller implicit stadsdelsgissning: bara platsfälten används.
Osäkra / motstridiga platsuppgifter redovisas som Okänt delområde.
"""
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/events.csv"
OUT = ROOT / "docs/data/lulea_district_monthly.csv"

ALIASES = {
 "Bergnäset": ["bergnaset", "bergnäset", "lulea flygplats", "luleå flygplats", "kallax flygplats", "f21", "f 21", "flottilj f21", "flygplatsen"],
 "Sörbyarna": ["sorbyarna", "sörbyarna", "antnas", "antnäs", "alvik", "ale", "ersnas", "ersnäs", "mattsund", "måttsund", "matsund", "alhamn", "langnas", "långnäs", "kallax by", "kallaxby"],
 "Bergviken": ["bergviken", "midgardsvagen", "midgårdsvägen", "delfinvagen", "delfinvägen", "hummergatan"],
 "Björkskatan": ["bjorkskatan", "björkskatan", "vaderleden", "väderleden"],
 "Centrum": [
  "centrum", "lulea centrum", "luleå centrum", "innerstaden", "lulea innerstad", "luleå innerstad",
  "stadsviken", "charlottendal", "norra hamn", "norra hamnen", "sodra hamn", "södra hamn", "sodra hamnen", "södra hamnen", "ostermalm", "östermalm",
  "gultzauudden", "gültzauudden", "gultzaudden", "gültsauudden", "vastra stranden", "västra stranden", "oscarsvarv",
  "storgatan", "smedjegatan", "radstugatan", "rådstugatan", "radstugugatan", "rådstugugatan",
  "jarnvagsstation", "järnvägsstation", "jarnvagsstationen", "järnvägsstationen", "lulea centralstation", "luleå centralstation",
  "kopmantorget", "köpmantorget", "kungsgatan", "stationsgatan", "skeppsbrogatan", "sandviksgatan",
  "busstationen", "busstation", "lulea busstation", "luleå busstation", "sodra hamnleden", "södra hamnleden",
  "lulea c", "luleå c", "kulturens hus", "stadsparken", "gymnasiebyn", "gymnasieby",
  "lulea domkyrka", "luleå domkyrka", "domkyrkan", "lulea energi arena", "luleå energi arena", "pontushallen",
  "smedjan galleria", "smedjan", "strand galleria", "shopping galleria", "shoppinghuset",
  "lulea live", "luleå live", "splash lulea", "splash luleå", "under solen", "rix fm festival", "rix fm-festival", "rixfm festival", "lulea hamnfestival", "luleå hamnfestival", "hamnfestivalen", "luleakalaset", "luleåkalaset", "musikens makt", "musikfestivalen i lulea", "musikfestivalen i luleå",
  "hermelinsparken", "jarnvagsparken", "järnvägsparken", "residensparken",
  "pontusbadet", "halsans hus", "hälsans hus", "norrbottensteatern", "norrbottens museum",
  "skomakargatan", "bastugatan", "residensgatan", "norra hamnpromenaden",
  "sodra hamnplan", "södra hamnplan", "norra hamn", "norra hamnen",
  "hermelinsgatan", "sodra smedjegatan", "södra smedjegatan", "smabatsgatan", "småbåtsgatan",
  "prastgatan", "prästgatan", "tullgatan", "kopmangatan", "köpmangatan", "magasinsgatan",
  "norra strandgatan", "vastra varvsgatan", "västra varvsgatan", "centrumhallplatsen", "centrumhållplatsen",
  "sodra hamnkranen", "södra hamnkranen", "hamnkranen", "karpen parkeringshus", "parkeringshuset karpen",
  "sodra hamnterminalen", "södra hamnterminalen", "lulea stadshus", "luleå stadshus", "lulea stadsbibliotek", "luleå stadsbibliotek",
 ],
 "Gammelstad": ["gammelstad"],
 "Hertsön": ["hertson", "hertsön"],
 "Hertsöheden": ["hertsoheden", "hertsöheden"],
 "Kallkällan": ["kallkallan", "kallkällan"],
 "Karlsvik": ["karlsvik"],
 "Kronan": ["kronan"],
 "Lerbäcken": ["lerbacken", "lerbäcken"],
 "Malmudden": ["malmudden", "lulea malmudden", "luleå malmudden"],
 "Mjölkudden": ["mjolkudden", "mjölkudden", "lulea mjolkudden", "luleå mjölkudden"],
 "Munksund": ["munksund"],
 "Notviken": ["notviken"],
 "Porsön": ["porson", "porsön", "teknikens hus", "lulea tekniska universitet", "luleå tekniska universitet", "lulea science park", "luleå science park"],
 "Råneå": ["ranea", "råneå"],
 "Skurholmen": ["skurholmen"],
 "Storheden": ["storheden", "ica maxi", "ica maxi storheden", "coop forum storheden"],
 "Skutviken": ["skutviken", "coop arena", "coop norrbotten arena"],
 "Sunderbyn": ["sunderbyn", "sunderby sjukhus", "sunderbyns sjukhus"],
 "Svartöstaden": ["svartostaden", "svartöstaden"],
 "Örnäset": ["ornaset", "örnäset"],
}
UNKNOWN = "Okänt delområde"
MULTI = "Flera stadsdelar i Luleå"
MULTI_ROADS = ["willys", "svartovagen", "hertsovagen", "bergnasbron", "bergnäsbron"]
def normalize(s):
 s = unicodedata.normalize("NFKD",str(s or "").casefold())
 s = "".join(c for c in s if not unicodedata.combining(c))
 return re.sub(r"\s+"," ",s)
ROAD_PATTERNS = [re.compile(r"(?<![a-z])"+re.escape(normalize(road))+r"(?![a-z])") for road in MULTI_ROADS]
PATTERNS = {name:[re.compile(r"(?<![a-z])"+re.escape(normalize(alias))+r"(?![a-z])") for alias in al] for name,al in ALIASES.items()}
# Den snäva listan är uttryckligen godkänd för Centrum; ett naket omnämnande
# i löptexten räcker inte. "till/från busstationen" ska inte räknas.
NARRATIVE_CENTRUM = re.compile(
 r"(?<![a-z])(?:i|pa|vid|intill|utanfor|inne i|omkring|kring)\s+"
 r"(?:lulea\s+)?(?:innerstaden|centrum|busstationen|busstation)(?![a-z])"
)
# Snäva områdesnamn med tydlig platsinledning. Gatunamn från aliases
# läggs inte automatiskt till här: de kräver särskild adressgranskning.
NARRATIVE_DISTRICT_NAMES={
 "Bergnäset":["bergnaset","flygplatsen","lulea flygplats","f21","f 21"],"Sörbyarna":["sorbyarna","antnas","alvik","ale","ersnas","mattsund","matsund","alhamn","langnas","kallax by"],"Skutviken":["skutviken","coop arena"],"Bergviken":["bergviken"],
 "Björkskatan":["bjorkskatan"],"Gammelstad":["gammelstad"],
 "Hertsön":["hertson"],"Hertsöheden":["hertsoheden"],
 "Kallkällan":["kallkallan"],"Karlsvik":["karlsvik"],
 "Kronan":["kronan"],"Lerbäcken":["lerbacken"],
 "Malmudden":["malmudden"],"Mjölkudden":["mjolkudden"],
 "Munksund":["munksund"],"Notviken":["notviken"],
 "Porsön":["porson"],"Råneå":["ranea"],
 "Skurholmen":["skurholmen"],"Storheden":["storheden"],
 "Sunderbyn":["sunderbyn"],"Svartöstaden":["svartostaden"],
 "Örnäset":["ornaset"]}
NARRATIVE_DISTRICT_PATTERNS={
 district:re.compile(r"(?<![a-z])(?:i|pa|vid|intill|utanfor|kring)\s+(?:lulea\s+)?(?:"+"|".join(names)+r")(?![a-z])")
 for district,names in NARRATIVE_DISTRICT_NAMES.items()
}
# SCB tätorter 2023, verified in data/norrbotten_place_to_municipality.csv.
# Separate locality labels; no inference of administrative district boundaries.
EXACT_LOCALITIES = ("Kallax", "Rutvik", "Bensbyn", "Bälinge", "Klöverträsk", "Brändön", "Avan", "Sundom", "Persön")
def exact_locality(row):
 if str(row.get("is_summary") or "").strip().casefold() in ("true","1"):return UNKNOWN
 fields=[unicodedata.normalize("NFC",str(row.get(k) or "")).strip().casefold() for k in ("title_location","location_string")]
 candidates=set()
 for field in fields:
  if field in ("","luleå","luleå kommun","norrbotten","norrbottens län"):continue
  matches={name for name in EXACT_LOCALITIES if re.fullmatch(re.escape(name.casefold())+r"(?:,\s*luleå(?:,\s*norrbottens län)?)?",field)}
  if not matches:return UNKNOWN
  candidates.update(matches)
 if len(candidates)!=1:return UNKNOWN
 target=next(iter(candidates))
 narrative=" ".join(str(row.get(k) or "") for k in ("headline","description","content"))
 n=normalize(narrative)
 if any(p.search(n) for pats in PATTERNS.values() for p in pats):return UNKNOWN
 if any(p.search(n) for p in ROAD_PATTERNS):return UNKNOWN
 if re.search(r"(?<![a-z0-9])(?:e\s*\d{1,3}|(?:riksvag|lansvag|vag(?:en)?|rv|lv)\s*(?:nr\.?\s*)?\d{1,4}|[a-z]{3,}(?:vagen|leden|gatan|bron|banken))(?![a-z0-9])",n):return UNKNOWN
 raw=unicodedata.normalize("NFC",narrative).casefold()
 if any(name!=target and re.search(r"(?<!\w)"+re.escape(name.casefold())+r"(?!\w)",raw) for name in EXACT_LOCALITIES):return UNKNOWN
 return target

# Group 3, revision #6: explicit heading/lead location, not incidental mentions.
CENTRUM_LABEL = r"(?:lulea\s+centrum|lulea\s+innerstad(?:en)?|innerstaden|centrala\s+lulea|centrum)"
CENTRUM_PREFIX = re.compile(r"^\s*"+CENTRUM_LABEL+r"\s*[,;:–-]\s*(?:misstankt|man|kvinna|person|stold|brand|misshandel|rattfylleri|trafikolycka|kontroll|brott|skadegorelse|brak|inbrott|fylleri|olovlig|ran|polis)\b")
CENTRUM_SUFFIX = re.compile(r"^\s*(?:misstankt\s+)?(?:ringa\s+)?(?:stold|snatteri|brand|misshandel|skadegorelse|inbrott|ran|brak|kontroll|rattfylleri|olovlig korning)\b[^.!?<>]{0,120},\s*"+CENTRUM_LABEL+r"\s*[.!]?\s*$")
CENTRUM_EXPLICIT = re.compile(r"^\s*(?:misstankt\s+)?(?:stold|snatteri|brand|misshandel|skadegorelse|inbrott|ran|brak|kontroll|rattfylleri|olovlig korning)\b[^.!?<>]{0,100}\s+i\s+(?:centrala lulea|lulea innerstad(?:en)?|lulea centrum)\s*[.!]?\s*$")
CENTRUM_OTHER = re.compile(r"(?<![a-z])(?:boden(?:s)?|pitea(?:s)?|kalix|alvsbyn|haparanda|kiruna|gallivare|arvidsjaur|arjeplog|jokkmokk|overkalix|overtornea|pajala|hertso(?:ns|s)?|hersto|orn(?:n)?aset(?:s)?|bjorkskatan(?:s)?|kyrkbyn|gammelstaden|nationella forensiska)(?![a-z])")
CENTRUM_ROAD = re.compile(r"(?<![a-z0-9])(?:e\s*\d{1,3}|(?:riksvag|lansvag|vag(?:en)?|rv|lv)\s*(?:nr\.?\s*)?\d{1,4}|[a-z]{3,}(?:vagen|leden|gatan|bron|banken))(?![a-z0-9])")
def centrum_rescue(row):
 if str(row.get("is_summary") or "").strip().casefold() in ("true","1"):return UNKNOWN
 # Only generic or empty own place fields; no override of explicit unknown place.
 generic={"","lulea","lulea kommun","norrbotten","norrbottens lan","lulea, norrbottens lan","lulea, lulea, norrbottens lan"}
 if any(normalize(row.get(k)).strip() not in generic for k in ("title_location","location_string")):return UNKNOWN
 fields=[normalize(row.get(k)).strip() for k in ("headline","description","content")]
 all_text=" ".join(fields)
 if CENTRUM_OTHER.search(all_text):return UNKNOWN
 if any(p.search(all_text) for name,pats in PATTERNS.items() if name!="Centrum" for p in pats):return UNKNOWN
 if any(p.search(all_text) for p in ROAD_PATTERNS) or CENTRUM_ROAD.search(all_text):return UNKNOWN
 raw=unicodedata.normalize("NFC"," ".join(str(row.get(k) or "") for k in ("headline","description","content"))).casefold()
 if any(re.search(r"(?<!\w)"+re.escape(name.casefold())+r"(?!\w)",raw) for name in EXACT_LOCALITIES):return UNKNOWN
 # Only headline or first sentence of description; not arbitrary later sentences.
 for value in fields[:2]:
  lead=re.split(r"(?<=[.!?])\s+|<",value,maxsplit=1)[0].strip()
  if re.search(r"\b(?:till|fran|mot|via|mellan|fardades|korde)\b",lead):continue
  if CENTRUM_PREFIX.search(lead) or CENTRUM_SUFFIX.fullmatch(lead) or CENTRUM_EXPLICIT.fullmatch(lead):return "Centrum"
 return UNKNOWN


# Restrict the new narrative rule to explicit police deployment or incident
# location; a person's destination, transport or mere mention is not enough.
CENTRUM_OBJECTS = (
 "lulea centrum","centrala lulea","lulea innerstad","innerstaden","centrum",
 "ostermalm","norra hamnen","norra hamn","sodra hamnen","sodra hamn",
 "gultzauudden","vastra stranden","oscarsvarv","stadsviken","charlottendal",
 "lulea busstation","busstationen","busstation","lulea centralstation",
 "jarnvagsstationen","jarnvagsstation","gymnasiebyn","stadsparken",
 "hermelinsparken","jarnvagsparken","residensparken","kulturens hus",
 "lulea stadshus","lulea stadsbibliotek","pontusbadet","lulea domkyrka"
)
_COBJ = r"(?:"+ "|".join(re.escape(x) for x in sorted(CENTRUM_OBJECTS,key=len,reverse=True))+r")(?![a-z])"
_CDEPLOY = re.compile(r"\b(?:polis(?:en|patrull(?:en|er|erna)?)?|(?:en )?patrull(?:en|er|erna)?)\s+(?:har\s+)?(?:beordras|beordrades|beordrats|larmas|larmades|larmats|kallas|kallades|kallats|skickas|skickades|skickats|aker|akte|ak[t] )\s*(?:ut\s+)?till\s+(?:(?:en|ett)\s+(?:butik|adress|plats|bostad|restaurang)\s+(?:i|pa|vid)\s+)?"+_COBJ+r"(?=\s*(?:[,.:;!?]|$)|\s+(?:i lulea\b|med anledning av\b|efter\b|dar\b|pa grund av\b|for att\b))")
_CINCIDENT = re.compile(r"\b(?:larm om (?:brand|brak|inbrott)|(?:en )?(?:brand|stold|inbrott|misshandel|brak|skadegorelse|ran))\s+(?:i|pa|vid|intill|utanfor)\s+"+_COBJ+r"(?=\s*(?:[,.:;!?]|$)|\s+(?:i lulea\b|dar\b))")
_COTHER_PLACES = ("jamton","stromsund","borjelslandet","niemisel","smedsbyn","sinksundet","kallviken","orrbyn","hogsta","orar na","orarna")
def centrum_dispatch_rescue(row):
 if str(row.get("is_summary") or "").strip().casefold() in ("true","1"):return UNKNOWN
 generic={"","lulea","lulea kommun","norrbotten","norrbottens lan","lulea, norrbottens lan","lulea, lulea, norrbottens lan"}
 if any(normalize(row.get(k)).strip() not in generic for k in ("title_location","location_string")):return UNKNOWN
 from html import unescape
 raw_fields=[unescape(re.sub(r"<[^>]*>"," ",str(row.get(k) or ""))) for k in ("headline","description","content")]
 raw=" ".join(raw_fields)
 n=normalize(raw)
 if CENTRUM_OTHER.search(n) or CENTRUM_ROAD.search(n) or any(p.search(n) for p in ROAD_PATTERNS):return UNKNOWN
 if any(p.search(n) for name,pats in PATTERNS.items() if name!="Centrum" for p in pats):return UNKNOWN
 if any(re.search(r"(?<![a-z])"+re.escape(x)+r"(?![a-z])",n) for x in _COTHER_PLACES):return UNKNOWN
 if any(re.search(r"(?<!\w)"+re.escape(name.casefold())+r"(?!\w)",unicodedata.normalize("NFC",raw).casefold()) for name in EXACT_LOCALITIES):return UNKNOWN
 for field in raw_fields:
  # Limit the rule to the first two sentences per source field.
  for sentence in re.split(r"(?<=[.!?])\s+|\n+",field)[:2]:
   sentence=normalize(sentence).strip()
   if re.search(r"\b(?:inte|aldrig|tidigare|felaktigt|i stallet|ovning|transport|fordes|skjutsades)\b",sentence):continue
   if _CDEPLOY.search(sentence) or _CINCIDENT.search(sentence):return "Centrum"
 return UNKNOWN

def district(row):
 text=normalize(" ".join((row.get("title_location") or "",row.get("location_string") or "")))
 matches={name for name,pats in PATTERNS.items() if any(p.search(text) for p in pats)}
 if len(matches)>1: return MULTI
 if len(matches)==1: return next(iter(matches))
 if any(p.search(text) for p in ROAD_PATTERNS): return MULTI
 # Använd löptext bara om platsfält inte redan ger säker stadsdel.
 narrative=normalize(" ".join((row.get(k) or "") for k in ("headline","description","content")))
 candidates={name for name,pattern in NARRATIVE_DISTRICT_PATTERNS.items() if pattern.search(narrative)}
 if NARRATIVE_CENTRUM.search(narrative):candidates.add("Centrum")
 # En explicit geografisk rubrikinledning (t.ex. "Innerstaden, ...")
 # kan ange händelseplats utan preposition. Gäller inte sammanfattningar
 # eller platser som bara förekommer längre in i löptexten.
 headline=normalize(row.get("headline") or "")
 description=normalize(row.get("description") or "")
 is_summary=str(row.get("is_summary") or "").strip().casefold() in ("true","1")
 innerstad_prefix=re.compile(r"^[ ]*(?:lulea[ ]*[,–-][ ]*)?innerstaden[ ]*[,.:;–-][ ]+")
 if not is_summary and (innerstad_prefix.search(headline) or innerstad_prefix.search(description)):
  candidates.add("Centrum")
 if len(candidates)==1:
  selected=next(iter(candidates))
  # Blockera när en annan stadsdel, bro eller lång väg också omnämns.
  others={name for name,pats in PATTERNS.items() if name!=selected and any(p.search(narrative) for p in pats)}
  if not others and not any(p.search(narrative) for p in ROAD_PATTERNS):
   return selected
 locality=exact_locality(row)
 if locality!=UNKNOWN:return locality
 rescued=centrum_rescue(row)
 if rescued!=UNKNOWN:return rescued
 return centrum_dispatch_rescue(row)
def main():
 if not SOURCE.exists(): raise SystemExit("Missing events.csv")
 counts=defaultdict(int)
 ids=set()
 with SOURCE.open(encoding="utf-8-sig",newline="") as stream:
  reader=csv.DictReader(stream)
  required={"geography_group","title_location","location_string","type_original"}
  if not required.issubset(reader.fieldnames or []):raise SystemExit("Unexpected events.csv columns")
  for row in reader:
   if (row.get("geography_group") or "").strip()!="Luleå kommun":continue
   eid=(row.get("event_id") or "").strip()
   if eid:
    if eid in ids:continue
    ids.add(eid)
   year=(row.get("year") or "").strip()
   month=(row.get("month") or "").strip()
   if not year.isdigit() or not month.isdigit() or not (1<=int(month)<=12):continue
   month=f"{int(month):02d}"
   typ=(row.get("type_original") or "Okänd händelsetyp").strip()
   counts[(year,month,district(row),typ)]+=1
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open("w",encoding="utf-8",newline="") as stream:
  writer=csv.writer(stream);writer.writerow(["year","month","geography_group","type_original","event_count"])
  for key,n in sorted(counts.items()):writer.writerow([*key,n])
 print("Luleå-delområden:",sum(counts.values()),"unika händelser","kategorier:",len(counts))
if __name__=="__main__":main()
