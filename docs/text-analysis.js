(async()=>{
const e=id=>document.getElementById(id),fmt=new Intl.NumberFormat('sv-SE',{maximumFractionDigits:1}), sum=a=>a.reduce((s,r)=>s+r.at(-1),0), colors=['#0b5cab','#b64135','#43876c','#8c68a6','#b78a36','#63788b'];
const svg=(tag,attrs={},label)=>{let n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(let [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(label!==undefined)n.textContent=label;return n};
function opts(id,values,def){e(id).replaceChildren(...values.map(v=>new Option(v,v,false,Array.isArray(def)?def.includes(v):v===def)))}
try{
let res=await fetch('data/text_analysis.json?v=20261127-fix1',{cache:'no-store'});if(!res.ok)throw Error('HTTP '+res.status);let d=await res.json();for(const k of ['totals','pairs','flows'])if(!Array.isArray(d[k]))throw Error('Datafält saknas: '+k);
let unique=(a,i)=>[...new Set(a.map(r=>String(r[i])))].sort((a,b)=>a.localeCompare(b,'sv'));
let years=unique(d.totals,1);opts('taGeo',unique(d.totals,0),'Luleå kommun');opts('taYear',['Alla',...years.slice().reverse()],'Alla');opts('taType',['Alla',...unique(d.totals,2)],'Alla');
let networkRoot=null;
function renderNetwork(match,selected){
 const picker=e('networkTerm'), net=e('taNetwork');
 const available=[...new Set(d.pairs.filter(r=>match(r)).flatMap(r=>[r[3],r[4]]))].sort((a,b)=>a.localeCompare(b,'sv'));
 if(!available.includes(networkRoot))networkRoot=selected.find(w=>available.includes(w))||available[0]||null;
 picker.replaceChildren(...available.map(w=>new Option(w,w,false,w===networkRoot)));
 picker.disabled=!available.length;
 const choose=w=>{networkRoot=w;renderNetwork(match,selected);};
 picker.onchange=()=>choose(picker.value);
 const root=networkRoot,links=new Map();
 for(const r of d.pairs){if(!match(r))continue;const other=r[3]===root?r[4]:r[4]===root?r[3]:null;if(other)links.set(other,(links.get(other)||0)+r[5]);}
 const top=[...links].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'sv')).slice(0,10);
 net.replaceChildren();
 e('networkCurrent').textContent=root?'Aktuellt begrepp: '+root:'Inga publicerbara begrepp i urvalet.';
 if(!top.length){net.append(svg('text',{x:400,y:210,'text-anchor':'middle',fill:'#66717d'},'Inga publicerbara samförekomster'));return;}
 const nodes=top.map(([w,n],i)=>({w,n,x:400+290*Math.cos(i*2*Math.PI/top.length),y:210+150*Math.sin(i*2*Math.PI/top.length)}));
 for(const p of nodes)net.append(svg('line',{x1:400,y1:210,x2:p.x,y2:p.y,stroke:'#94a3b8','stroke-width':1+7*p.n/top[0][1]}));
 net.append(svg('circle',{cx:400,cy:210,r:51,fill:'#0b5cab'}),svg('text',{x:400,y:214,'text-anchor':'middle',fill:'white','font-size':13},root));
 for(const p of nodes){
  const group=svg('g',{role:'button',tabindex:0,'aria-label':'Visa '+p.w+' som centralt begrepp, '+p.n+' notiser',class:'network-node'});
  group.append(svg('title',{},p.w+': minst '+p.n+' notiser. Klicka för att utforska begreppet.'),svg('circle',{cx:p.x,cy:p.y,r:17+19*Math.sqrt(p.n/top[0][1]),fill:'#a5c6e4'}),svg('text',{x:p.x,y:p.y+4,'text-anchor':'middle',fill:'#16202a','font-size':12},p.w),svg('text',{x:p.x,y:p.y+17,'text-anchor':'middle',fill:'#16202a','font-size':10},String(p.n)));
  group.addEventListener('click',()=>choose(p.w));
  group.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();choose(p.w);picker.focus({preventScroll:true});}});
  net.append(group);
 }
}

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
  for(const [w,el] of nodeEls)el.setAttribute('opacity',!focus||neighbors.has(w)?1:.16);
  for(const [l,el] of edgeEls)el.setAttribute('opacity',!focus ? .35 : (l.a.word===focus||l.b.word===focus ? .85 : .045));
  const selected=nodes.find(n=>n.word===focus);
  e('overviewDetail').textContent=selected?focus+' – '+selected.degree+' direkt sammankopplade begrepp. Klicka på ett annat begrepp eller välj Visa hela nätverket.':'Välj ett begrepp för att framhäva dess direkta samband.';
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
  for(const n of nodes){const el=svg('g',{class:'overview-node',role:'button',tabindex:0,'aria-label':n.word+', '+n.degree+' samband'});el.append(svg('title',{},n.word+' – '+n.degree+' samband'),svg('circle',{cx:n.x,cy:n.y,r:n.radius,fill:'#0b5cab',stroke:'white','stroke-width':1.5}),svg('text',{x:n.x,y:n.y+n.radius+12,'text-anchor':'middle','font-size':11,fill:'#16202a',stroke:'#f8fafc','stroke-width':2.5,'paint-order':'stroke'},n.word));el.onclick=()=>choose(n.word);el.onkeydown=ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();choose(n.word);}};graph.append(el);nodeEls.set(n.word,el);}
  if(!by.has(focus))focus='';
  picker.replaceChildren(new Option('Alla begrepp',''),...[...by.keys()].sort((a,b)=>a.localeCompare(b,'sv')).map(w=>new Option(w,w,false,w===focus)));picker.value=focus;picker.disabled=!nodes.length;
  e('overviewStatus').textContent=fmt.format(nodes.length)+' begrepp och '+fmt.format(edges.length)+' unika samband i urvalet'+(edges.length<all.length?' (av '+fmt.format(all.length)+' publicerbara samband)':'')+'.';
  if(!nodes.length)graph.append(svg('text',{x:500,y:325,'text-anchor':'middle',fill:'#66717d'},'Inga publicerbara samband för urvalet'));
  view={x:0,y:0,w:1000,h:650};updateView();highlight();
 }
 picker.onchange=()=>choose(picker.value);threshold.onchange=build;build();
}

function render(){
let g=e('taGeo').value,y=e('taYear').value,t=e('taType').value,selected=['trafikolycka'];
let match=(r,ignoreYear=false)=>r[0]===g&&(ignoreYear||y==='Alla'||String(r[1])===y)&&(t==='Alla'||r[2]===t);
let denom=sum(d.totals.filter(r=>match(r)));e('taStatus').textContent='Urval: '+fmt.format(denom)+' originalnotiser med text. Data genererad '+d.generated+'. '+fmt.format(d.pairs.length)+' samförekomstrader i källdata.';
renderNetwork(match,selected);
try{renderOverview(match);}catch(err){e('overviewStatus').textContent='Nätverksöversikten kunde inte ritas: '+err.message;console.error(err);}
let paths=new Map();for(let r of d.flows){if(match(r)){let k=JSON.stringify(r.slice(3,6));paths.set(k,(paths.get(k)||0)+r[6])}}let flow=e('taFlow');flow.replaceChildren();if(!paths.size){flow.textContent='Inga publicerbara trafikflöden i urvalet.';return}let list=[...paths].map(([k,n])=>({p:JSON.parse(k),n})),total=list.reduce((a,r)=>a+r.n,0),groups=[0,1,2].map(i=>{let m=new Map();for(let r of list)m.set(r.p[i],(m.get(r.p[i])||0)+r.n);return [...m].sort((a,b)=>b[1]-a[1])}),height=Math.max(420,Math.max(...groups.map(a=>a.length))*45+80),scale=(height-65-12*Math.max(...groups.map(a=>a.length)))/total,xs=[165,440,715],pos=groups.map((a,i)=>{let yy=38,m=new Map();for(let [name,n] of a){m.set(name,{y:yy,h:n*scale,used:0,n});yy+=n*scale+12}return m}),s=svg('svg',{viewBox:'0 0 900 '+height,style:'width:100%;min-width:720px'});
for(let r of list){let a=pos[0].get(r.p[0]),b=pos[1].get(r.p[1]),c=pos[2].get(r.p[2]),w=r.n*scale,yy=[a,b,c].map(n=>n.y+n.used+w/2);for(let j=0;j<2;j++){let x=xs[j]+12,X=xs[j+1],mid=(x+X)/2;let p=svg('path',{d:'M'+x+' '+yy[j]+' C'+mid+' '+yy[j]+' '+mid+' '+yy[j+1]+' '+X+' '+yy[j+1],stroke:colors[groups[0].findIndex(z=>z[0]===r.p[0])%colors.length],'stroke-opacity':.28,'stroke-width':w,fill:'none'});p.append(svg('title',{},r.p.join(' → ')+': '+r.n));s.append(p)}for(let n of [a,b,c])n.used+=w}
for(let i=0;i<3;i++){s.append(svg('text',{x:xs[i],y:20,'font-weight':600,'font-size':14,fill:'#16202a'},['Fordon','Olyckstyp','Konsekvens'][i]));for(let [name,n] of pos[i]){s.append(svg('rect',{x:xs[i],y:n.y,width:12,height:n.h,fill:'#0b5cab'}),svg('text',{x:xs[i]-5,y:n.y+Math.max(10,n.h/2),'text-anchor':'end','font-size':11,fill:'#16202a'},name+' ('+n.n+')'))}}flow.append(s);let p=document.createElement('p');p.className='note';p.textContent='Publicerade flöden: minst '+fmt.format(total)+' notiser. Varje notis bidrar till en väg.';flow.append(p);
}
for(let id of ['taGeo','taYear','taType'])e(id).addEventListener('change',render);render();
}catch(err){e('taStatus').textContent='Textanalysen kunde inte läsas: '+err.message+'. Kör Update polishandelser efter merge.'}
})();
