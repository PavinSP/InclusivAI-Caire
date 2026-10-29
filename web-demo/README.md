# Caire map demo (web-demo)

Static page: Leaflet map of companies researched in `company_research/companies.json`.
Open `index.html` through any static server (e.g. `python3 -m http.server` in this folder).
Switch between **Mainfranken** (default, 9 areas) and the **Lower Franconia** (whole diocese; adds Aschaffenburg and Miltenberg).
Per `config/mainfranken_scope.json` the default scope excludes those two; confirm with Caritas before showing the wider view.

## Rebuild the data
1. `python3 build_boundaries.py <path to isellsoap/deutschlandGeoJSON clone>` -> district + outline GeoJSON
2. `python3 build_town_table.py gazetteer.json` -> `town_coordinates.json` (export command is in the script header)
3. `python3 prepare_data.py` -> `data.js`

## Caveats
- Positions are **approximate**: research data has town names only. Companies in the same town are fanned out in a small spiral.
- 9 small towns are hand-entered (`source: "manual"`, about +-2 km).
- 3 companies are not on the map because no site could be placed (Versicherungskammer Bayern, Magnets4you, Madinger).
- The score shown is a **placeholder heuristic**, not the scorer-agent pipeline from `06_Architecture_and_Ideas.md`.

## Attribution
Boundaries: GeoBasis-DE / BKG via isellsoap/deutschlandGeoJSON (public domain). Town coordinates: GeoNames, CC BY 4.0.
Map libraries: Leaflet 1.9.4, leaflet.markercluster 1.5.3 (loaded from cdnjs).
