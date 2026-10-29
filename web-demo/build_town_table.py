"""Build town_coordinates.json: one verified-source coordinate + district per town
name that appears in company_research/companies.json.

Why: the research data only has town names. Coordinates come from GeoNames
(CC BY 4.0, https://www.geonames.org/) through the npm package `all-the-cities`;
a handful of small places missing from that gazetteer are entered by hand
(MANUAL below, accuracy about +-2 km, flagged source="manual").
The district comes from the municipality's official key (AGS prefix 096xx).

Export the gazetteer once (needs `npm i all-the-cities`):

    node -e "const c=require('all-the-cities');require('fs').writeFileSync('gazetteer.json',
      JSON.stringify(c.filter(x=>x.country==='DE'&&x.loc.coordinates[0]>8.9&&x.loc.coordinates[0]<11&&
      x.loc.coordinates[1]>49.4&&x.loc.coordinates[1]<50.65).map(x=>({id:x.cityId,name:x.name,
      alt:x.altName,lat:x.loc.coordinates[1],lng:x.loc.coordinates[0],muni:x.muni||'',pop:x.population}))))"

Then:  python3 build_town_table.py gazetteer.json
Requires: shapely (only for the self-check against build_boundaries.py output)
"""
import collections, json, os, re, sys
from pathlib import Path
from shapely.geometry import Point, shape

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("CAIRE_REPO", HERE.parent))
GAZ = Path(sys.argv[1] if len(sys.argv) > 1 else "gazetteer.json")

AGS_DISTRICT = {
    "09661": "Aschaffenburg (Stadt)", "09662": "Schweinfurt (Stadt)", "09663": "Würzburg (Stadt)",
    "09671": "Landkreis Aschaffenburg", "09672": "Landkreis Bad Kissingen", "09673": "Landkreis Rhön-Grabfeld",
    "09674": "Landkreis Haßberge", "09675": "Landkreis Kitzingen", "09676": "Landkreis Miltenberg",
    "09677": "Landkreis Main-Spessart", "09678": "Landkreis Schweinfurt", "09679": "Landkreis Würzburg",
}

# Places missing from the gazetteer: (lat, lng, expected district). Approximate.
MANUAL = {
    "Ebern": (50.0997, 10.7958, "Landkreis Haßberge"),
    "Königsberg i. Bay.": (50.0797, 10.5761, "Landkreis Haßberge"),
    "Karlstein am Main": (50.0522, 9.0678, "Landkreis Aschaffenburg"),
    "Bessenbach": (49.9833, 9.2667, "Landkreis Aschaffenburg"),
    "Amorbach": (49.6419, 9.2183, "Landkreis Miltenberg"),
    "Lülsfeld": (49.9100, 10.2700, "Landkreis Schweinfurt"),
    "Abtswind": (49.7700, 10.3800, "Landkreis Kitzingen"),
    "Castell": (49.7200, 10.3300, "Landkreis Kitzingen"),
}
# Alternative spellings / sub-places -> the town we place them at.
ALIASES = {
    "Würzburg area": "Würzburg", "Würzburg-Heidingsfeld": "Würzburg", "Schweinfurt area": "Schweinfurt",
    "Kitzingen area": "Kitzingen", "Grettstadt site": "Grettstadt", "Ochsenfurt-Hohestadt": "Ochsenfurt",
    "Bad Kissingen-Albertshausen": "Bad Kissingen", "Albertshausen": "Bad Kissingen",
    "Eltmann-Eschenbach": "Eltmann", "Eschenbach": "Eltmann", "Königsberg": "Königsberg i. Bay.",
    "Nordheim am Main": "Nordheim", "Zeil am Main": "Zeil",
}


def norm(s):
    s = (s or "").lower().strip()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return s


def clean_town(name):
    return re.sub(r"[\(;/,].*$", "", name or "").strip()


def variants(n):
    cur = n
    for pat, sub in ((r"\ba\.\s?d\.", "an der"), (r"\bi\.\s?UFr\.?", "in Unterfranken"),
                     (r"\bv\.\s?d\.", "vor der")):
        cur = re.sub(pat, sub, cur)
    out = [n, cur]
    for suffix in (" am Main", " in Unterfranken", " im Grabfeld", " an der Saale"):
        out.append(cur + suffix)
    return [norm(v) for v in dict.fromkeys(out)]


def main():
    gaz = json.load(open(GAZ, encoding="utf-8"))
    idx = collections.defaultdict(list)
    for p in gaz:
        for n in {p["name"], *(a for a in (p["alt"] or "").split(",") if a)}:
            idx[norm(n)].append(p)

    recs = json.load(open(REPO / "company_research" / "companies.json", encoding="utf-8"))
    names = collections.Counter()
    for r in recs:
        for c in (r.get("lower_franconia_sites") or []) + ([r["hq_city"]] if r.get("hq_city") else []):
            if clean_town(c):
                names[clean_town(c)] += 1

    table, unresolved = {}, []
    for name in names:
        target = ALIASES.get(name, name)
        if target in MANUAL:
            lat, lng, dist = MANUAL[target]
            table[name] = {"lat": lat, "lng": lng, "district": dist, "source": "manual", "as": target}
            continue
        hit = None
        for v in variants(target):
            if v in idx:
                hit = sorted(idx[v], key=lambda p: (not p["muni"].startswith("096"), -p["pop"]))[0]
                break
        if not hit:
            unresolved.append(name)
            continue
        table[name] = {"lat": round(hit["lat"], 5), "lng": round(hit["lng"], 5),
                       "district": AGS_DISTRICT.get(hit["muni"][:5]),  # None => outside the diocese
                       "source": f"geonames:{hit['id']}", "as": hit["name"]}

    # self-check: does each coordinate fall in (or very near) the district its key says?
    polys = {f["properties"]["name"]: shape(f["geometry"]) for f in
             json.load(open(HERE / "unterfranken-districts.geo.json", encoding="utf-8"))["features"]}
    off = []
    for name, t in table.items():
        poly = polys.get(t["district"])
        if poly is not None and poly.distance(Point(t["lng"], t["lat"])) > 0.003:  # ~300 m
            off.append((name, t["district"], round(poly.distance(Point(t["lng"], t["lat"])) * 111, 1)))

    json.dump(dict(sorted(table.items())), open(HERE / "town_coordinates.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    inside = sum(1 for t in table.values() if t["district"])
    print(f"{len(table)} towns resolved ({inside} inside the diocese, "
          f"{sum(1 for t in table.values() if t['source']=='manual')} manual); {len(unresolved)} names not placeable")
    print("not placeable (non-places, other regions or whole-district phrases):", sorted(unresolved))
    print("coordinate more than 300 m outside the district its key says (km):", off)


if __name__ == "__main__":
    main()
