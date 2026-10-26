const test=require('node:test');const assert=require('node:assert/strict');const {compare}=require('../docs/lulea-month-compare.js');
test('sum rows per year and month',()=>{const a=compare([{year:'2026',month:'1',event_count:2},{year:'2026',month:'01',event_count:3},{year:'2025',month:'12',event_count:8}]);assert.equal(a[1].counts[0],5);assert.equal(a[0].counts[11],8)});
test('leave missing future months blank',()=>{const a=compare([{year:'2026',month:'10',event_count:7}]);assert.equal(a[0].counts[10],null)});
test('show at most last six years',()=>{const a=compare(Array.from({length:9},(_,i)=>({year:String(2018+i),month:'1',event_count:1})));assert.equal(a.length,6);assert.equal(a[0].year,'2021');assert.equal(a[5].year,'2026')});
test('exclude invalid month',()=>{assert.deepEqual(compare([{year:'2026',month:'13',event_count:4}])[0].counts,Array(12).fill(null))});
