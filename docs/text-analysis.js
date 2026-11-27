(async()=>{
const e=id=>document.getElementById(id),fmt=new Intl.NumberFormat('sv-SE',{maximumFractionDigits:1}), sum=a=>a.reduce((s,r)=>s+r.at(-1),0);
const svg=(tag,attrs={},label)=>{let n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(let [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(label!==undefined)n.textContent=label;return n};
function opts(id,values,def){e(id).replaceChildren(...values.map(v=>new Option(v,v,false,Array.isArray(def)?def.includes(v):v===def)))}
try{
let res=await fetch('data/text_analysis.json?v=20261127-fix1',{cache:'no-store'});if(!res.ok)throw Error('HTTP '+res.status);let d=await res.json();for(const k of ['totals','pairs'])if(!Array.isArray(d[k]))throw Error('Datafält saknas: '+k);
let unique=(a,i)=>[...new Set(a.map(r=>String(r[i])))].sort((a,b)=>a.localeCompare(b,'sv'));
let years=unique(d.totals,1);opts('taGeo',unique(d.totals,0),'Luleå kommun');opts('taYear',['Alla',...years.slice().reverse()],'Alla');opts('taType',['Alla',...unique(d.totals,2)],'Alla');
function renderOverview(match){
 const graph=e('overviewGraph'),picker=e('overviewTerm'),threshold=e('overviewMin');
 const pairs=new Map();
 for(const r of d.pairs){if(!match(r))continue;const key=JSON.stringify([r[3],r[4]].sort());pairs.set(key,(pairs.get(key)||0)+r[5]);}
 const all=[...pairs].map(([k,n])=>({words:JSON.parse(k),n})).sort((a,b)=>b.n-a.n);
 let focus=picker.value||'', view={x:0,y:0,w:1000,h:650},drag=null;
 const updateView=()=>graph.setAttribute('viewBox',[view.x,view.y,view.w,view.h].join(' '));
 const zoom=(factor,x=view.x+view.w/2,y=view.y+view.h/2)=>{const w=Math.max(90,Math.min(4000,view.w*factor)),ratio=w/view.w;view={x:x-(x-view.x)*ratio,y:y-(y-view.y)*ratio,w,h:view.h*ratio};updateView();};
 const coord=ev=>{const p=graph.createSVGPoint();p.x=ev.clientX;p.y=ev.clientY;return p.matrixTransform(graph.getScreenCTM().inverse());};
 e('overviewIn').onclick=()=>zoom(.75);e('overviewOut').onclick=()=>zoom(1/.75);
 e('overviewFit').onclick=()=>{focus='';picker.value='';view={x:0,y:0,w:1000,h:650};updateView();highlight();};
 graph.onwheel=ev=>{if(!ev.ctrlKey)return;ev.preventDefault();const p=coord(ev);zoom(ev.deltaY>0?1.15:1/1.15,p.x,p.y);};
 graph.onpointerdown=ev=>{if(ev.button!==0||ev.target.closest('.overview-node'))return;drag={id:ev.pointerId,x:ev.clientX,y:ev.clientY,vx:view.x,vy:view.y};graph.setPointerCapture(ev.pointerId);graph.style.cursor='grabbing';};
 graph.onpointermove=ev=>{if(!drag||drag.id!==ev.pointerId)return;const scale=graph.getScreenCTM().a;view.x=drag.vx-(ev.clientX-drag.x)/scale;view.y=drag.vy-(ev.clientY-drag.y)/scale;updateView();};
 graph.onpointerup=graph.onpointercancel=ev=>{if(drag&&drag.id===ev.pointerId){drag=null;graph.style.cursor='grab';if(graph.hasPointerCapture(ev.pointerId))graph.releasePointerCapture(ev.pointerId);}};
 let nodes=[],edges=[],nodeEls=new Map(),edgeEls=[];
 function highlight(){
  const neighbors=new Set([focus]);for(const l of edges)if(l.a.word===focus||l.b.word===focus){neighbors.add(l.a.word);neighbors.add(l.b.word);}
  for(const [w,el] of nodeEls){
   const active=!!focus&&w===focus;
   el.setAttribute('opacity',!focus||neighbors.has(w)?1:.16);
   el.classList.toggle('overview-selected',active);
   el.setAttribute('aria-pressed',String(active));
   const ring=el.querySelector('.overview-selection-ring');
   if(ring)ring.setAttribute('visibility',active?'visible':'hidden');
  }
  if(focus&&nodeEls.has(focus))graph.append(nodeEls.get(focus));
  for(const [l,el] of edgeEls)el.setAttribute('opacity',!focus ? .35 : (l.a.word===focus||l.b.word===focus ? .85 : .045));
  const selected=nodes.find(n=>n.word===focus);
  e('overviewDetail').textContent=selected?focus+' – '+selected.degree+' direkt sammankopplade begrepp. Klicka på samma nod igen för att avmarkera och visa hela nätverket.':'Välj ett begrepp för att framhäva dess direkta samband.';
 }
 function choose(w){focus=w;picker.value=w;highlight();}
 function build(){
  const min=+threshold.value, filtered=all.filter(l=>l.n>=min),degree=new Map();
  for(const l of filtered)for(const w of l.words)degree.set(w,(degree.get(w)||0)+1);
  nodes=[...degree].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'sv')).map(([word,degree],i)=>{const a=i*2.39996323,r=24*Math.sqrt(i);return {word,degree,x:500+r*Math.cos(a),y:325+r*Math.sin(a),radius:7+2.6*Math.sqrt(degree)};});
  const by=new Map(nodes.map(n=>[n.word,n]));edges=filtered.map(l=>({a:by.get(l.words[0]),b:by.get(l.words[1]),n:l.n}));
  // Deterministic force layout: repulsion, weighted attraction, centering.
  for(let iter=0;iter<260;iter++){
   const cool=1-iter/280;for(const n of nodes){n.dx=(500-n.x)*.012;n.dy=(325-n.y)*.012;}
   for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){const a=nodes[i],b=nodes[j],x=a.x-b.x,y=a.y-b.y,dist=Math.max(.1,Math.hypot(x,y)),f=1250/(dist*dist)+Math.max(0,a.radius+b.radius+18-dist)*.11;a.dx+=x/dist*f;a.dy+=y/dist*f;b.dx-=x/dist*f;b.dy-=y/dist*f;}
   for(const l of edges){const x=l.b.x-l.a.x,y=l.b.y-l.a.y,dist=Math.max(.1,Math.hypot(x,y)),f=(dist-100)*.012*Math.min(2,Math.log2(l.n+1)/3);l.a.dx+=x/dist*f;l.a.dy+=y/dist*f;l.b.dx-=x/dist*f;l.b.dy-=y/dist*f;}
   for(const n of nodes){n.x=Math.max(45,Math.min(955,n.x+Math.max(-12,Math.min(12,n.dx))*cool));n.y=Math.max(38,Math.min(612,n.y+Math.max(-12,Math.min(12,n.dy))*cool));}
  }
  // Fit the full layout into the available viewport.
  if(nodes.length>1){const xx=nodes.map(n=>n.x),yy=nodes.map(n=>n.y),xmin=Math.min(...xx),xmax=Math.max(...xx),ymin=Math.min(...yy),ymax=Math.max(...yy),k=Math.min(830/Math.max(1,xmax-xmin),510/Math.max(1,ymax-ymin));for(const n of nodes){n.x=500+(n.x-(xmin+xmax)/2)*k;n.y=325+(n.y-(ymin+ymax)/2)*k;}}
  graph.replaceChildren();nodeEls=new Map();edgeEls=[];
  const max=Math.max(1,...edges.map(l=>l.n));
  for(const l of edges){const el=svg('line',{x1:l.a.x,y1:l.a.y,x2:l.b.x,y2:l.b.y,stroke:'#647e99','stroke-width':.7+4*Math.sqrt(l.n/max)});el.append(svg('title',{},l.a.word+' / '+l.b.word+': minst '+fmt.format(l.n)+' notiser'));graph.append(el);edgeEls.push([l,el]);}
  for(const n of nodes){const el=svg('g',{class:'overview-node',role:'button',tabindex:0,'aria-label':n.word+', '+n.degree+' samband'});el.append(svg('title',{},n.word+' – '+n.degree+' samband'),svg('circle',{class:'overview-selection-ring',cx:n.x,cy:n.y,r:n.radius+5,fill:'none',stroke:'#b64135','stroke-width':3,visibility:'hidden','pointer-events':'none'}),svg('circle',{class:'overview-core',cx:n.x,cy:n.y,r:n.radius,fill:'#0b5cab',stroke:'white','stroke-width':1.5}),svg('text',{x:n.x,y:n.y+n.radius+12,'text-anchor':'middle','font-size':11,fill:'#16202a',stroke:'#f8fafc','stroke-width':2.5,'paint-order':'stroke'},n.word));el.onclick=()=>choose(focus===n.word?'':n.word);el.onkeydown=ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();choose(focus===n.word?'':n.word);}};graph.append(el);nodeEls.set(n.word,el);}
  if(!by.has(focus))focus='';
  picker.replaceChildren(new Option('Alla begrepp',''),...[...by.keys()].sort((a,b)=>a.localeCompare(b,'sv')).map(w=>new Option(w,w,false,w===focus)));picker.value=focus;picker.disabled=!nodes.length;
  e('overviewStatus').textContent=fmt.format(nodes.length)+' begrepp och '+fmt.format(edges.length)+' unika samband i urvalet'+(edges.length<all.length?' (av '+fmt.format(all.length)+' publicerbara samband)':'')+'.';
  if(!nodes.length)graph.append(svg('text',{x:500,y:325,'text-anchor':'middle',fill:'#66717d'},'Inga publicerbara samband för urvalet'));
  view={x:0,y:0,w:1000,h:650};updateView();highlight();
 }
 picker.onchange=()=>choose(picker.value);threshold.onchange=build;build();
}

function render(){
let g=e('taGeo').value,y=e('taYear').value,t=e('taType').value;
let match=(r,ignoreYear=false)=>r[0]===g&&(ignoreYear||y==='Alla'||String(r[1])===y)&&(t==='Alla'||r[2]===t);
let denom=sum(d.totals.filter(r=>match(r)));e('taStatus').textContent='Urval: '+fmt.format(denom)+' originalnotiser med text. Data genererad '+d.generated+'. '+fmt.format(d.pairs.length)+' samförekomstrader i källdata.';
try{renderOverview(match);}catch(err){e('overviewStatus').textContent='Nätverksöversikten kunde inte ritas: '+err.message;console.error(err);}

}
for(let id of ['taGeo','taYear','taType'])e(id).addEventListener('change',render);render();
}catch(err){e('taStatus').textContent='Textanalysen kunde inte läsas: '+err.message+'. Kör Update polishandelser efter merge.'}
})();
