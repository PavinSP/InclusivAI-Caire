/* Turn the scored prospect list (caritas_prospects_scored_Harsha.json) into
   data.js for the Caire map and company pages. This file is the source of
   truth for the demo; prepare_data.py (old companies.json heuristic) is kept
   only for reference.

       node prepare_scored_data.js [path/to/caritas_prospects_scored_Harsha.json]

   Per prospect:
     1. place it at the centre of `town_matched` (else HQ town) using
        town_coordinates.json; a few towns missing there are listed in EXTRA_TOWNS
     2. if only the district is known, place it at the district label point
        (flagged `position: "district"`)
     3. scope = "mainfranken" or "extended" from the district polygon properties
     4. fan companies sharing a town out in a small spiral, kept inside the
        district polygon (positions are APPROXIMATE, town level only)
   No town or district at all -> listed at the end, not guessed.
*/
const fs = require('fs');
const path = require('path');

const HERE = __dirname;
const SRC = process.argv[2] || path.join(HERE, '..', '..', 'caritas_prospects_scored_Harsha.json');
const OUT = path.join(HERE, 'data.js');

const TOWNS = JSON.parse(fs.readFileSync(path.join(HERE, 'town_coordinates.json'), 'utf8'));
const DISTRICTS = JSON.parse(fs.readFileSync(path.join(HERE, 'unterfranken-districts.geo.json'), 'utf8')).features;

// Towns in the scored list that town_coordinates.json does not have (approx., manual).
const EXTRA_TOWNS = {
  'Karlstein': { lat: 50.0436, lng: 9.0347, district: 'Landkreis Aschaffenburg', source: 'manual' },
};

// Free-text district field -> district polygon name (only used when no town is known).
const TEXT_CANON = [
  ['würzburg (stadt)', 'Würzburg (Stadt)'], ['würzburg (kreisfreie stadt)', 'Würzburg (Stadt)'],
  ['landkreis würzburg', 'Landkreis Würzburg'], ['würzburg (landkreis)', 'Landkreis Würzburg'],
  ['schweinfurt (stadt)', 'Schweinfurt (Stadt)'], ['stadt schweinfurt', 'Schweinfurt (Stadt)'],
  ['landkreis schweinfurt', 'Landkreis Schweinfurt'], ['schweinfurt (landkreis)', 'Landkreis Schweinfurt'],
  ['aschaffenburg (stadt)', 'Aschaffenburg (Stadt)'], ['stadt aschaffenburg', 'Aschaffenburg (Stadt)'],
  ['landkreis aschaffenburg', 'Landkreis Aschaffenburg'], ['aschaffenburg (landkreis)', 'Landkreis Aschaffenburg'],
  ['miltenberg', 'Landkreis Miltenberg'], ['kitzingen', 'Landkreis Kitzingen'],
  ['main-spessart', 'Landkreis Main-Spessart'], ['rhön-grabfeld', 'Landkreis Rhön-Grabfeld'],
  ['bad kissingen', 'Landkreis Bad Kissingen'], ['haßberge', 'Landkreis Haßberge'],
  ['würzburg', 'Würzburg (Stadt)'], ['aschaffenburg', 'Aschaffenburg (Stadt)'],
];
const textDistrict = raw => { const k = (raw || '').toLowerCase(); const hit = TEXT_CANON.find(([n]) => k.includes(n)); return hit ? hit[1] : null; };

// The scorer prefixes Caritas fields in English; map them to the map's activity areas.
const CARITAS_AREAS = {
  'children & youth': 'Kinder & Familie', 'elderly care': 'Senioren & Pflege',
  'disability inclusion': 'Menschen mit Behinderung', 'poverty': 'Armut & Krisen',
  'migration/integration': 'Migration & Integration', 'education': 'Jugend & Bildung',
  'health': 'Senioren & Pflege', 'volunteering': 'Ehrenamt & Gemeinwesen',
  'regional development': 'Ehrenamt & Gemeinwesen', 'addiction': 'Sucht & Beratung',
  'homelessness': 'Armut & Krisen',
};

const clean = s => String(s || '').replace(/[\(;\/,].*$/, '').trim();
const slug = s => s.toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '').replace(/ß/g, 'ss').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const district = name => DISTRICTS.find(f => f.properties.name === name);

function inRing(pt, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
const inPolygon = (pt, geom) => inRing(pt, geom.coordinates[0]) && !geom.coordinates.slice(1).some(h => inRing(pt, h));

function place(p) {
  for (const cand of [p.town_matched, p.hq]) {
    const name = clean(cand);
    const entry = TOWNS[name] || EXTRA_TOWNS[name];
    if (entry && entry.district) return { town: entry.as || name, lat: entry.lat, lng: entry.lng, landkreis: entry.district, position: 'town' };
  }
  const lk = textDistrict(p.landkreis);
  const f = lk && district(lk);
  if (f) return { town: null, lat: f.properties.labelLat, lng: f.properties.labelLng, landkreis: lk, position: 'district' };
  return null;
}

const GOLDEN_ANGLE = 2.399963229728653;
const SPREAD_UNIT_DEG = 0.0045; // ~500 m * sqrt(n)

function spreadStacked(items) {
  const groups = {};
  items.forEach(c => {
    c.town_lat = c.lat; c.town_lng = c.lng;
    (groups[`${c.lat},${c.lng}`] ||= []).push(c);
  });
  let stacked = 0;
  Object.values(groups).forEach(members => {
    const n = members.length;
    if (n < 2) return;
    stacked++;
    members.sort((a, b) => a.name.localeCompare(b.name));
    const { lat, lng } = members[0];
    const geom = district(members[0].landkreis).geometry;
    const R = SPREAD_UNIT_DEG * Math.sqrt(n), kx = 1 / Math.cos(lat * Math.PI / 180);
    members.forEach((c, i) => {
      let r = R * Math.sqrt((i + .5) / n);
      const a = i * GOLDEN_ANGLE;
      // Pull the point back towards the town centre until it is inside the district.
      for (let k = 0; k < 8; k++, r *= 0.6) {
        const pt = [lng + r * Math.cos(a) * kx, lat + r * Math.sin(a)];
        if (inPolygon(pt, geom) || k === 7) { c.lng = +pt[0].toFixed(6); c.lat = +pt[1].toFixed(6); break; }
      }
    });
  });
  return stacked;
}

function main() {
  const src = JSON.parse(fs.readFileSync(SRC, 'utf8'));
  const out = [], dropped = [];
  for (const p of src.prospects) {
    const pos = place(p);
    if (!pos) { dropped.push([p.id, p.company, p.hq, p.landkreis]); continue; }
    const f = district(pos.landkreis);
    const matched = [...new Set([...(p.caritas_fields_matched || []), ...(p.csr_themes || [])]
      .map(t => CARITAS_AREAS[t]).filter(Boolean))].sort();
    out.push({
      id: slug(p.company), pid: p.id, rank: p.rank,
      name: p.company, sector: p.sector,
      town: pos.town || pos.landkreis, landkreis: pos.landkreis, scope: f.properties.scope,
      lat: pos.lat, lng: pos.lng, position: pos.position, approx_location: true,
      hq: p.hq, presence: p.presence, caritas_facilities_in_town: p.caritas_facilities_in_town,
      employees: p.employees_raw, size_class: p.size_class, foundation: p.foundation,
      csr_themes: p.csr_themes || [], caritas_fields_matched: p.caritas_fields_matched || [],
      matched_areas: matched,
      csr_summary: p.csr_summary, previous_engagement: p.past_engagements || [],
      church_link: p.church_link, caritas_network_link: p.caritas_network_link,
      website: p.website, contact: p.contact, source_urls: p.sources || [], source_notes: p.source_notes,
      confidence: p.source_confidence || 'low',
      gate: p.gate, scores: p.scores, tier: p.tier, tier_code: (p.tier || 'C')[0],
      // Lead priority (0-10 scale) is the headline number shown on the map.
      score: Math.round((p.scores.lead_priority || 0) * 10) / 10,
      agents: p.agents, explanation: p.explanation,
    });
  }
  const stacked = spreadStacked(out);
  const meta = { generated: src.meta.generated, model: src.meta.model, calibration: src.meta.calibration, counts: src.meta.counts, excluded_upstream: src.meta.excluded_upstream };

  fs.writeFileSync(OUT, `const CAIRE_META = ${JSON.stringify(meta)};\nconst CAIRE_COMPANIES = ${JSON.stringify(out)};\n`, 'utf8');

  const byScope = out.reduce((a, c) => (a[c.scope] = (a[c.scope] || 0) + 1, a), {});
  const ids = new Set(out.map(c => c.id));
  console.log(`${src.prospects.length} scored -> ${out.length} on the map (${byScope.mainfranken || 0} Mainfranken + ${byScope.extended || 0} extended); spread ${stacked} stacked towns`);
  if (ids.size !== out.length) console.log('WARNING: duplicate ids');
  console.log(`district-level position only: ${out.filter(c => c.position === 'district').map(c => c.name).join(', ') || 'none'}`);
  console.log(`dropped ${dropped.length} (not guessed):`);
  dropped.forEach(d => console.log('   ', d.join(' | ')));
}

main();
