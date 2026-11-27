"""Aggregate vocabulary from original notices, never publish raw text."""
import csv, re, html, json
from collections import Counter, defaultdict
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
STOP=set("""och att det som en ett i på av till för med den de dem har hade är var om från vid sig sin sitt sina under över efter före eller inte också då där när hur vad vem vilka vilken vilket ska skulle kan kunde får fick blev blir vara varit man hon han dom deras dess mot ut in upp ner fram genom sedan samt mellan denna detta dessa någon något några mycket mer mest än så nu även enligt kring två tre fyra fem polis polisen polisens patrull patrullen patruller uppgifter uppgift uppges uppger meddelar rapporterar händelse händelsen anmälan anmäld anmäls upprättas upprättat upprättades samband person personen personer plats platsen platsen kontakt larm larmas larmades gällande aktuell aktuella rubricering ärendet ärende inträffat aktuell cirka klockan kl län kommun norrbotten luleå html nbsp http https www""".split())
# Curated vocabulary limits accidental exposure of personal names or addresses.
VOCAB=set("""trafikolycka trafikolyckor olycka olyckor viltolycka viltolyckor bil bilar personbil personbilar lastbil lastbilar buss bussar cykel cyklar elcykel moped motorcykel snöskoter skoter fyrhjuling ren renar älg älgar rådjur hund hundar väg vägar vägbana dike diket halka halt snö snöfall is regn dimma mörker sikt hastighet trafik trafiken trafikstopp trafikhinder kollision kolliderat krock krockat singelolycka omkörning rattfylleri drograttfylleri nykterhet alkohol narkotika droger körkort böter ordningsbot kontroll kontroller kontrolleras flygplats järnväg tåg brand bränder rök röklukt eld eldsvåda räddningstjänst ambulans sjukhus vård skada skador skadad skadade personskada oskadd stöld stölder stulen stulet stulna inbrott inbrotten tillgrepp skadegörelse klotter bedrägeri bedrägerier misshandel hot olaga våld bråk ordningsstörning fylleri omhändertagande berusad berusade berusning butik butiker handel köpcentrum restaurang krog bostad bostäder lägenhet villa garage förråd källare skola skolor arbetsplats park parkering parkeringsplats centrum landsbygd bostadsområde offentlig återfunnen försvunnen eftersök fjällräddning räddningsinsats beslag gripen gripna gripande misstänkt misstänkta misstanke förhör utredning utreds avspärrning avspärrat vittne vittnen kamera övervakning verktyg maskin båt båtmotor dator mobiltelefon telefon plånbok pengar smycken drivmedel diesel bensin skjutvapen kniv hundpatrull ordningsvakt säkerhetsbälte vinterdäck sommardäck vatten översvämning storm vind träd nedfallna vilt djur djuren""".split())
class Plain(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts=[]
    def handle_data(self,data): self.parts.append(data)
def words(s):
    p=Plain();p.feed(html.unescape(s));return re.findall(r"[a-zåäöé]+", " ".join(p.parts).casefold())
def main():
    counts=defaultdict(Counter); docs=defaultdict(Counter); totals=Counter(); seen=set()
    with (ROOT/'data/events.csv').open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            eid=r.get('event_id','')
            if not eid or eid in seen:continue
            seen.add(eid)
            # Separate summaries, as their text can refer to multiple municipalities.
            geo=r.get('geography_group','')
            if r.get('is_summary','').lower() in ('true','1'):geo='Sammanfattningar (ej kommunfördelade)'
            y=r.get('year',''); typ=r.get('type_original','')
            if not y.isdigit() or not geo or not typ:continue
            text=max((r.get(k,'') or '' for k in ('content','description','headline')),key=len)
            tokens=words(text)
            if not tokens:continue
            key=(geo,int(y),typ);totals[key]+=1
            for n in (1,2,3):
                c=Counter(' '.join(p) for p in zip(*(tokens[i:] for i in range(n))) if all(w in VOCAB and w not in STOP for w in p))
                counts[key].update(c);docs[key].update(c.keys())
    out=[]
    for key,terms in sorted(counts.items()):
        for term,n in terms.items():
            d=docs[key][term]
            if d>=5:out.append([*key,term,n,d])
    data={'rows':out,'totals':[[*k,v] for k,v in sorted(totals.items())],'min_documents':5}
    path=ROOT/'docs/data/wordcloud.json';path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print('wordcloud rows',len(out),'documents',sum(totals.values()))
if __name__=='__main__':main()
