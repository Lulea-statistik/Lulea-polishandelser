/* Calendar-month comparison for the existing Lulea statistics series. */
(function(root){
 function compare(rows,limit=6){
  const years=[...new Set(rows.map(r=>String(r.year)).filter(y=>/^\d{4}$/.test(y)))].sort((a,b)=>b.localeCompare(a)).slice(0,limit).sort();
  const buckets=new Map(years.map(y=>[y,Array(12).fill(0)]));
  for(const r of rows){
   const year=String(r.year),month=Number(r.month),n=Number(r.event_count);
   if(buckets.has(year)&&Number.isInteger(month)&&month>=1&&month<=12&&Number.isFinite(n)){
    buckets.get(year)[month-1]+=n;
   }
  }
  return years.map(year=>({year,counts:buckets.get(year)}));
 }
 const api={compare};
 if(typeof module!=="undefined"&&module.exports)module.exports=api;
 root.LuleaMonthCompare=api;
})(typeof globalThis!=="undefined"?globalThis:this);
