/* Shared display-only policy for Lulea road geography. Not a location decision. */
(function (root) {
  'use strict';
  const minimum = 10;
  const priority = new Set(['E4', 'Väg 94', 'Väg 97']);
  function isKnown(name) { return Boolean(name && name !== 'Väg ej angiven'); }
  function visible(name, totals) {
    return isKnown(name) && (priority.has(name) || (totals.get(name) || 0) >= minimum);
  }
  function category(name, totals) {
    if (!isKnown(name)) return 'Övrig väg, okänd väg';
    return visible(name, totals) ? name : 'Övrig väg, känd väg';
  }
  function totalsAcrossAllYears(rows) {
    const totals = new Map();
    for (const row of rows) {
      if (row.transport_mode !== 'Vägtrafik' || !isKnown(row.road_reference)) continue;
      totals.set(row.road_reference, (totals.get(row.road_reference) || 0) + Number(row.event_count || 0));
    }
    return totals;
  }
  const api = { minimum, visible, category, totalsAcrossAllYears };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.LuleaRoadDisplay = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
