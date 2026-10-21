#!/usr/bin/env python3
"""Frekvensgranskning av byggnader, butiker och arenor bland okända Luleåposter."""
import csv,re,sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_lulea_districts import district,UNKNOWN,normalize
ROOT=Path(__file__).resolve().parents[1]
TERMS={
"Coop Norrbotten Arena / Coop Arena":[r"coop(?: norrbotten)? arena",r"coop arena",r"delfinen(?: arena)?"],
"Luleå Energi Arena / Pontushallen":[r"lulea energi arena",r"pontushallen",r"pontus hallen"],
"Smedjan galleria":[r"smedjan(?: galleria)?"],
"Shopping galleria":[r"shopping(?:huset| galleria)?"],
"Strand galleria":[r"strand galleria",r"strand shopping"],
"Kulturens hus":[r"kulturens hus"],
"Stadsparken":[r"stadsparken"],
"Stadshuset":[r"stadshuset",r"lulea stadshus"],
"ICA Maxi":[r"ica maxi"],
"Willys":[r"willys"],
"Systembolaget":[r"systembolaget",r"systembolag"],
"Musikfestivalen i Luleå":[r"musikfestivalen i lulea"],
"Coop Forum":[r"coop forum"],
"Coop butik (ospecificerad)":[r"coop (?:butik|affar|stormarknad)"],
"Luleå Hockey":[r"lulea hockey"],
"Luleå Basket / BC Luleå":[r"lulea basket",r"bc lulea"],
"Arcushallen / Arcus":[r"arcushallen",r"arcus hall"],
"Skutviken":[r"skutviken"],
"Storheden handelsområde":[r"storheden"],
"Gymnasiebyn":[r"gymnasiebyn"],
"Busstationen":[r"busstationen"],
"Järnvägsstationen":[r"jarnvagsstationen",r"centralstationen"],
"Luleå Live":[r"lulea live",r"lulea-live"],
"Splash Luleå":[r"splash lulea",r"splashfestivalen"],
"Under Solen":[r"under solen",r"under-solen"],
"RIX FM Festival":[r"rix fm festival",r"rixfm festival",r"rix fm-festival"],
"Luleå Hamnfestival":[r"lulea hamnfestival",r"hamnfestivalen"],
"Luleåkalaset":[r"luleakalaset",r"lulea kalaset"],
"Musikens makt":[r"musikens makt"],
"Coop Norrbotten Arena":[r"coop norrbotten arena"],
"Shopping":[r"shoppinghuset",r"shopping galleria"],
"Pontushallen":[r"pontushallen"],
"Norrbottensteatern":[r"norrbottensteatern"],
"Norrbottens museum":[r"norrbottens museum"],
"Stadsbiblioteket":[r"stadsbiblioteket"],
"Södra Hamnplan":[r"sodra hamnplan"],
"Norra hamn":[r"norra hamn"],
"Luleå Science Park":[r"lulea science park"],
"Teknikens hus":[r"teknikens hus"],
"Universitetet / LTU":[r"lulea tekniska universitet",r"ltu"],
"Arcusområdet":[r"arcusomradet",r"arcusvagen"],
"SSAB Luleå":[r"ssab"],
"Luleå sjukhus / Sunderby sjukhus":[r"sunderby sjukhus",r"sunderbyns sjukhus"],
"Storhedens handelsplats":[r"storhedens handelsplats"]
}
PAT={label:[re.compile(r"(?<![a-z])"+p+r"(?![a-z])") for p in terms] for label,terms in TERMS.items()}
FIELDS=("title_location","location_string")
BODY=("headline","description","content")
allstats=defaultdict(lambda:[set(),set(),set()])
examples=[]
seen=set()
with (ROOT/"data/events.csv").open(encoding="utf-8-sig",newline="") as f:
 for row in csv.DictReader(f):
  if row.get("geography_group")!="Luleå kommun" or district(row)!=UNKNOWN:continue
  eid=row.get("event_id","")
  if eid and eid in seen:continue
  if eid:seen.add(eid)
  ident=eid or str(len(seen)+1000000)
  place=" ".join(row.get(k,"") or "" for k in FIELDS)
  body=" ".join(row.get(k,"") or "" for k in BODY)
  for label,patterns in PAT.items():
   p=any(x.search(normalize(place)) for x in patterns)
   b=any(x.search(normalize(body)) for x in patterns)
   if not (p or b):continue
   if p:allstats[label][0].add(ident)
   if b:allstats[label][1].add(ident)
   allstats[label][2].add(ident)
   if len(examples)<1500:examples.append((ident,label,int(p),int(b),place[:200],row.get("year","")))
out=ROOT/"data/audit_lulea_unknown_landmarks.csv"
with out.open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f);w.writerow(["plats_eller_verksamhet","unika_okanda_platsfalt","unika_okanda_loptext","unika_okanda_totalt","tolkning"])
 for name,(place,body,allids) in sorted(allstats.items(),key=lambda kv:-len(kv[1][2])):
  w.writerow([name,len(place),len(body),len(allids),"Granska om namn avser händelseplats; verksamhetsnamn är inte automatiskt adress"])
with (ROOT/"data/audit_lulea_unknown_landmark_examples.csv").open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f);w.writerow(["event_id","platsnamn","platsfalt","loptext","ursprungligt_platsfalt","ar"]);w.writerows(examples)
print("Landmarks:",[(k,len(v[2])) for k,v in sorted(allstats.items(),key=lambda kv:-len(kv[1][2]))])
