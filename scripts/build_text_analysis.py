"""Aggregate exploratory text analytics, only publish fixed labels and counts."""
import csv,json,re,itertools,math
from collections import Counter,defaultdict
from datetime import date
from build_wordcloud import ROOT,VOCAB,words

GROUPS={
 "Fordon":{"Personbil":"bil bilar personbil personbilar","Lastbil":"lastbil lastbilar","Cykel":"cykel cyklar elcykel","Buss":"buss bussar","MC/moped":"motorcykel moped","Snöskoter":"snöskoter skoter","Fyrhjuling":"fyrhjuling"},
 "Olyckstyp":{"Vilt":"viltolycka viltolyckor vilt","Singel":"singelolycka","Kollision":"kollision kolliderat krock krockat"},
 "Konsekvens":{"Personskada":"personskada skadad skadade","Ambulans/sjukhus":"ambulans sjukhus","Oskadd":"oskadd","Trafikstopp":"trafikstopp"},
 "Djur":{"Älg":"älg älgar","Ren":"ren renar","Rådjur":"rådjur"},
 "Väder":{"Halka":"halka halt","Snö":"snö snöfall","Regn":"regn","Dimma":"dimma"},
 "Plats":{"Butik":"butik butiker köpcentrum","Bostad":"bostad bostäder lägenhet villa","Skola":"skola skolor","Restaurang":"restaurang krog","Parkering":"parkering parkeringsplats"},
 "Åtgärd":{"Gripande":"gripen gripna gripande","Beslag":"beslag","Böter":"böter ordningsbot","Omhändertagande":"omhändertagande"},
 "Stöldobjekt":{"Cykel":"cykel cyklar elcykel","Fyrhjuling":"fyrhjuling","Snöskoter":"snöskoter skoter","Verktyg":"verktyg","Båt":"båt båtmotor"}
}
def main():
 totals=Counter();terms=Counter();pairs=Counter();features=Counter();flows=Counter();documents=[];seen=set()
 with (ROOT/'data/events.csv').open(encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   eid=r.get('event_id',''); geo=r.get('geography_group','');y=r.get('year','');typ=r.get('type_original','')
   if not eid or eid in seen or not geo.endswith(' kommun') or not y.isdigit() or not typ or r.get('is_summary','').lower() in ('true','1'):continue
   seen.add(eid)
   text=max((r.get(k,'') or '' for k in ('content','description','headline')),key=len)
   tokens=words(text)
   if not tokens:continue
   key=(geo,int(y),typ); totals[key]+=1
   ts=set(tokens)&VOCAB
   terms.update((*key,t) for t in ts)
   pairs.update((*key,a,b) for a,b in itertools.combinations(sorted(ts),2))
   hits={}
   for group,labels in GROUPS.items():
    if group=='Stöldobjekt' and not any(x in typ.casefold() for x in ('stöld','inbrott','tillgrepp')):continue
    hits[group]=[label for label,variants in labels.items() if ts.intersection(variants.split())]
    features.update((*key,group,label) for label in hits[group])
   if 'trafikolycka' in typ.casefold():
    path=[]
    for group in ('Fordon','Olyckstyp','Konsekvens'):
     h=hits.get(group,[])
     path.append(h[0] if len(h)==1 else ('Flera omnämnanden' if h else 'Okänd/ej nämnd'))
    flows[(*key,*path)]+=1
   if ts:documents.append((key,sorted(ts)))
 # Actual unsupervised clustering on curated words. Fixed seed, aggregate output only.
 clusters=[];cluster_totals=Counter();cluster_terms=defaultdict(Counter)
 if len(documents)>=20:
  from sklearn.feature_extraction.text import TfidfVectorizer
  from sklearn.cluster import MiniBatchKMeans
  from sklearn.decomposition import TruncatedSVD
  import numpy as np
  x=TfidfVectorizer(tokenizer=str.split,token_pattern=None,lowercase=False).fit_transform(' '.join(ts) for _,ts in documents)
  k=min(8,x.shape[0],x.shape[1])
  if k>=2:
   model=MiniBatchKMeans(n_clusters=k,random_state=42,n_init=3,batch_size=1024)
   ids=model.fit_predict(x)
   coords=TruncatedSVD(n_components=2,random_state=42).fit_transform(x) if x.shape[1]>=2 else np.zeros((x.shape[0],2))
   for (key,ts),cid in zip(documents,ids):
    cluster_totals[(*key,int(cid))]+=1;cluster_terms[int(cid)].update(ts)
   for cid in sorted(set(int(i) for i in ids)):
    mask=ids==cid
    clusters.append({'id':cid,'label':' / '.join(t for t,n in cluster_terms[cid].most_common(4) if n>=5),'x':float(coords[mask,0].mean()),'y':float(coords[mask,1].mean()),'n':int(mask.sum())})
 def safe(c):return [[*key,n] for key,n in sorted(c.items()) if n>=5]
 # For comparisons aggregate directly at municipality/year and reference level,
 # avoiding unequal suppression by type. Publish only paired cells with >=5.
 gt=Counter();gd=Counter()
 for (g,y,t),n in totals.items():gd[g,y]+=n
 for (g,y,t,w),n in terms.items():gt[g,y,w]+=n
 contrasts=[]
 for g,y in sorted(gd):
  ref=sum(n for (gg,yy),n in gd.items() if yy==y and gg!=g)
  for w in sorted(VOCAB):
   a=gt[g,y,w];b=sum(gt[gg,y,w] for gg,yy in gd if yy==y and gg!=g)
   if a>=5 and b>=5 and ref:contrasts.append([g,y,w,a,gd[g,y],b,ref])
 out={'totals':[[*k,n] for k,n in sorted(totals.items())],'terms':safe(terms),'pairs':safe(pairs),'features':safe(features),'flows':safe(flows),'clusters':clusters,'cluster_counts':safe(cluster_totals),'contrasts':contrasts,'generated':date.today().isoformat()}
 path=ROOT/'docs/data/text_analysis.json';path.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 print('text analysis:',sum(totals.values()),'documents;',len(out['pairs']),'pair cells;',len(clusters),'clusters')
if __name__=='__main__':main()
