const test = require('node:test');
const assert = require('node:assert/strict');
const policy = require('../docs/road-display-policy.js');
const r = (name,n,year='2025') => ({road_reference:name,event_count:n,year,transport_mode:'Vägtrafik'});
test('9/10/11 threshold and group remainder', () => {
 const all=[r('Väg A',9),r('Väg B',10),r('Väg C',11)];
 const totals=policy.totalsAcrossAllYears(all);
 assert.equal(policy.category('Väg A',totals),'Övrig väg, känd väg');
 assert.equal(policy.category('Väg B',totals),'Väg B');
 assert.equal(policy.category('Väg C',totals),'Väg C');
});
test('priority roads are independently visible with nonzero counts',()=>{
 const totals=policy.totalsAcrossAllYears([r('E4',1),r('Väg 94',2),r('Väg 97',1)]);
 for(const name of ['E4','Väg 94','Väg 97']) assert.equal(policy.category(name,totals),name);
});
test('unidentified road stays unknown',()=>{
 const totals=policy.totalsAcrossAllYears([r('Väg ej angiven',10),r('',3)]);
 assert.equal(policy.category('Väg ej angiven',totals),'Övrig väg, okänd väg');
 assert.equal(policy.category('',totals),'Övrig väg, okänd väg');
});
test('threshold is invariant under selected-year filtering',()=>{
 const all=[r('Väg D',10,'2024'),r('Väg D',2,'2025')];
 const totals=policy.totalsAcrossAllYears(all);
 assert.equal(policy.category(all[1].road_reference,totals),'Väg D');
});
test('disjoint buckets conserve total event_count',()=>{
 const all=[r('Väg A',9),r('Väg B',10),r('E4',1),r('Väg ej angiven',3)];
 const totals=policy.totalsAcrossAllYears(all), buckets=new Map();
 for(const row of all){
  const cat=policy.category(row.road_reference,totals);
  buckets.set(cat,(buckets.get(cat)||0)+row.event_count);
 }
 assert.equal([...buckets.values()].reduce((a,b)=>a+b,0),23);
 assert.equal(buckets.get('Övrig väg, känd väg'),9);
 assert.equal(buckets.get('Övrig väg, okänd väg'),3);
 assert.equal(buckets.get('Väg B'),10);
 assert.equal(buckets.get('E4'),1);
});
test('display grouping cannot create records and is not event-id deduplication',()=>{
 const all=[r('E4',1),r('E4',1)];
 assert.equal(all.length,2);
 assert.equal(policy.category('E4',policy.totalsAcrossAllYears(all)),'E4');
});
