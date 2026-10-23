#!/usr/bin/env python3
"""Apply Hertsovagen source-place format audit to the other seven high-volume GIS roads."""
import csv,re,sys
from pathlib import Path
from collections import Counter,defaultdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_lulea_top_eight_road_context import out,TOP
ROADS=TOP-{"hertsövägen"}
EXPECTED={"älvbrovägen":35,"haparandavägen":31,"storhedsvägen":22,"mariebergsvägen":20,"mjölkuddsvägen":18,"storsandsvägen":15,"väderleden":13}
assert ROADS==set(EXPECTED)
def classify(raw,name):
 p=re.sub(r"\s+"," ",str(raw).casefold().strip().strip(" ,.;"))
 # "Luleå Vägnamn, Luleå, Norrbottens län" is the common police formatting.
 p=re.sub(r"^luleå\s+(?="+re.escape(name)+r"\b)","",p)
 n=re.escape(name)
 if re.fullmatch(n+r"\s*[,.;:]?",p):return "A – endast vägnamn"
 if re.fullmatch(n+r"\s*,\s*luleå\s*,\s*norrbottens län",p):return "B – väg + kommun + län"
 if re.fullmatch(n+r"\s*,\s*luleå",p):return "B – väg + kommun"
 if re.fullmatch(n+r"\s*,\s*[^,]+\s*,\s*luleå\s*,\s*norrbottens län",p):return "C – väg + plats/verksamhet + kommun + län"
 if re.search(r"\b(?:korsning|rondell|trafikplats|mot|från|till|mellan|via)\b",p):return "D – färdväg/korsning eller flertydigt"
 if re.search(r"\b(?:på|vid|längs|utmed)\s+"+n+r"\b",p):return "E – explicit platsrelation"
 return "F – annan platsform, granska"
selected=[x for x in out if x["road_candidate"] in ROADS]
assert len(selected)==154,len(selected)
assert len({x["event_id"] for x in selected})==154
counts=Counter();by_road=Counter();examples=defaultdict(list);results=[]
for x in selected:
 road=x["road_candidate"];kind=classify(x["own_place_text"],road)
 counts[kind]+=1;by_road[road]+=1
 if len(examples[(road,kind)])<2:examples[(road,kind)].append(x["own_place_text"])
 results.append({"event_id":x["event_id"],"road_candidate":road,"own_place_text":x["own_place_text"],"source_excerpt":x["text_excerpt"],"previous_flags":x["review_flags"],"format_class":kind,"human_decision":"Väntar på källgranskning","decision_reason":"","published":"nej"})
assert dict(by_road)==EXPECTED,(dict(by_road),EXPECTED)
path=ROOT/"data/audit_lulea_seven_road_location_formats.csv"
with path.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
print("SEVEN_ROADS_COUNTS",dict(sorted(by_road.items())))
print("SEVEN_ROADS_FORMS",dict(sorted(counts.items())))
for (road,kind),sample in sorted(examples.items()):print("ROAD_FORMAT_EXAMPLE",road,kind,repr(sample))
print("SEVEN_ROADS_QA",{"total":154,"pending":154,"approved":0,"published":0})
