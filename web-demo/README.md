# Caire map demo (web-demo)

Static site (also served by the backend, see the top-level README). Open `index.html` through any static server (e.g. `python3 -m http.server` in this folder).
Pages: `index.html` (logo splash) -> `home.html` (landing) -> `map.html` (Leaflet map) -> `company.html?id=<slug>` (one page per company).
Data source of truth: `caritas_prospects_scored_Harsha.json` (scored prospects, 10-agent model), turned into `data.js` by
`node prepare_scored_data.js [path to json]`. The generated `data.js` is committed, so the site runs without that input file.
Opens on **Lower Franconia** (whole diocese, incl. Aschaffenburg and Miltenberg); switch to **Mainfranken** (9 areas) with the toggle.
Per `config/mainfranken_scope.json` Mainfranken excludes those two; confirm with Caritas which view is the right default.

## Rebuild the data
1. `python3 build_boundaries.py <path to isellsoap/deutschlandGeoJSON clone>` -> district + outline GeoJSON
2. `python3 build_town_table.py gazetteer.json` -> `town_coordinates.json` (export command is in the script header)
3. `node prepare_scored_data.js <scored json>` -> `data.js`
4. `python3 translate_data.py` -> `data_de.js` (German text; needs a Gemini key in `../.env`)

## Caveats
- Positions are **approximate**: research data has town names only. Companies in the same town are fanned out in a small spiral.
- 9 small towns are hand-entered (`source: "manual"`, about +-2 km).
- Versicherungskammer Bayern (HQ Munich, no Lower Franconia town) is not on the map. Photovoltaik Zentrum Bayern and Madinger are pinned at their district centre.
- The number shown is the scorer's **lead priority** (0-10); tiers A ≥ 5.0, B ≥ 3.5, C below, X = reputation gate failed.

## Attribution
Boundaries: GeoBasis-DE / BKG via isellsoap/deutschlandGeoJSON (public domain). Town coordinates: GeoNames, CC BY 4.0.
Map libraries: Leaflet 1.9.4, leaflet.markercluster 1.5.3 (loaded from cdnjs).
