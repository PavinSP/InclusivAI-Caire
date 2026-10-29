"""Build the district boundary files used by the Caire map demo.

Source: https://github.com/isellsoap/deutschlandGeoJSON (public domain),
derived from GeoBasis-DE / BKG data. Clone it, then run:

    python3 build_boundaries.py /path/to/deutschlandGeoJSON

Outputs (next to this script):
    unterfranken-districts.geo.json   12 districts of the Diocese of Würzburg,
                                      each tagged scope = mainfranken | extended
    mainfranken-outline.geo.json      dissolved outer boundary of the 9 Mainfranken areas
    unterfranken-outline.geo.json     dissolved outer boundary of all 12 areas

Scope rule comes from config/mainfranken_scope.json (cities + districts);
Aschaffenburg and Miltenberg are "extended" (whole diocese view only).
Requires: shapely
"""
import json, os, sys
from pathlib import Path
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "deutschlandGeoJSON") / "4_kreise" / "2_hoch.geo.json"
SIMPLIFY = 0.0008  # degrees, ~80 m: keeps district borders crisp when zoomed in

# dataset NAME_3 -> label shown on the map
DISTRICTS = {
    "Würzburg Städte": "Würzburg (Stadt)", "Würzburg": "Landkreis Würzburg",
    "Schweinfurt Städte": "Schweinfurt (Stadt)", "Schweinfurt": "Landkreis Schweinfurt",
    "Bad Kissingen": "Landkreis Bad Kissingen", "Haßberge": "Landkreis Haßberge",
    "Kitzingen": "Landkreis Kitzingen", "Main-Spessart": "Landkreis Main-Spessart",
    "Rhön-Grabfeld": "Landkreis Rhön-Grabfeld",
    "Aschaffenburg Städte": "Aschaffenburg (Stadt)", "Aschaffenburg": "Landkreis Aschaffenburg",
    "Miltenberg": "Landkreis Miltenberg",
}
EXTENDED = {"Aschaffenburg Städte", "Aschaffenburg", "Miltenberg"}


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    feats = [f for f in data["features"]
             if f["properties"].get("NAME_1") == "Bayern"
             and f["properties"].get("NAME_2") == "Unterfranken"
             and f["properties"].get("NAME_3") in DISTRICTS]
    assert len(feats) == 12, f"expected 12 districts, found {len(feats)}"

    out, all_geoms, mf_geoms = [], [], []
    for f in feats:
        key = f["properties"]["NAME_3"]
        geom = shape(f["geometry"])
        scope = "extended" if key in EXTENDED else "mainfranken"
        all_geoms.append(geom)
        if scope == "mainfranken":
            mf_geoms.append(geom)
        p = geom.representative_point()
        out.append({"type": "Feature",
                    "properties": {"name": DISTRICTS[key], "key": key, "scope": scope,
                                   "labelLat": round(p.y, 5), "labelLng": round(p.x, 5)},
                    "geometry": mapping(geom.simplify(SIMPLIFY, preserve_topology=True))})
    out.sort(key=lambda f: (f["properties"]["scope"], f["properties"]["name"]))

    def dump(name, features):
        path = HERE / name
        json.dump({"type": "FeatureCollection", "features": features}, open(path, "w", encoding="utf-8"),
                  ensure_ascii=False)
        print(f"{name}: {os.path.getsize(path) / 1024:.0f} KB")

    dump("unterfranken-districts.geo.json", out)
    for name, geoms, label in (("mainfranken-outline.geo.json", mf_geoms, "Mainfranken"),
                               ("unterfranken-outline.geo.json", all_geoms, "Unterfranken")):
        u = unary_union(geoms).simplify(SIMPLIFY, preserve_topology=True)
        dump(name, [{"type": "Feature", "properties": {"name": label}, "geometry": mapping(u)}])


if __name__ == "__main__":
    main()
