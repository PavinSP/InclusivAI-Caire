"""Turn company_research/companies.json into data.js for the Caire map demo.

    python3 prepare_data.py            # run from web-demo/, repo root is the parent folder

Steps per company:
  1. pick one site (first site that we can place on the map, else HQ city)
  2. place it at the town centre (hand-made lookup table; no geocoding service
     is available offline) and find which district polygon contains it
  3. tag scope = "mainfranken" (default map) or "extended" (Aschaffenburg and
     Miltenberg, shown only in the whole-diocese view) - see
     config/mainfranken_scope.json
  4. fan companies that share a town out in a small spiral so they can be
     told apart when zooming; positions are APPROXIMATE (town level only)
  5. compute a placeholder demo score (NOT the real scorer-agent pipeline)

Companies with no placeable site are listed at the end instead of being
guessed. Requires: shapely. Needs build_boundaries.py to have been run.
"""
import collections, json, math, os, re
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.ops import nearest_points

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("CAIRE_REPO", HERE.parent))
RAW = REPO / "company_research" / "companies.json"
DISTRICTS = HERE / "unterfranken-districts.geo.json"
OUT = HERE / "data.js"


def norm(s):
    s = (s or "").lower().strip()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return s


# Town centres + official district per town name; built by build_town_table.py
# (GeoNames, CC BY 4.0, plus a few manual entries flagged source="manual").
TOWNS = json.load(open(HERE / "town_coordinates.json", encoding="utf-8"))


CARITAS_THEMES = {
    "children & youth": "Kinder & Familie", "elderly care": "Senioren & Pflege",
    "disability inclusion": "Menschen mit Behinderung", "poverty": "Armut & Krisen",
    "migration/integration": "Migration & Integration", "education": "Jugend & Bildung",
    "health": "Senioren & Pflege", "volunteering": "Ehrenamt & Gemeinwesen",
    "regional development": "Ehrenamt & Gemeinwesen",
}

# text variants of the district field -> canonical label (used only to report
# disagreements with the map position)
TEXT_CANON = [
    ("würzburg (stadt)", "Würzburg (Stadt)"), ("würzburg (kreisfreie stadt)", "Würzburg (Stadt)"),
    ("stadt würzburg", "Würzburg (Stadt)"), ("landkreis würzburg", "Landkreis Würzburg"),
    ("würzburg (landkreis)", "Landkreis Würzburg"), ("schweinfurt (stadt)", "Schweinfurt (Stadt)"),
    ("stadt schweinfurt", "Schweinfurt (Stadt)"), ("landkreis schweinfurt", "Landkreis Schweinfurt"),
    ("schweinfurt (landkreis)", "Landkreis Schweinfurt"), ("aschaffenburg (stadt)", "Aschaffenburg (Stadt)"),
    ("stadt aschaffenburg", "Aschaffenburg (Stadt)"), ("landkreis aschaffenburg", "Landkreis Aschaffenburg"),
    ("aschaffenburg (landkreis)", "Landkreis Aschaffenburg"), ("miltenberg", "Landkreis Miltenberg"),
    ("kitzingen", "Landkreis Kitzingen"), ("main-spessart", "Landkreis Main-Spessart"),
    ("rhön-grabfeld", "Landkreis Rhön-Grabfeld"), ("bad kissingen", "Landkreis Bad Kissingen"),
    ("haßberge", "Landkreis Haßberge"),
]


def text_district(raw):
    k = (raw or "").lower()
    for needle, canon in TEXT_CANON:
        if needle in k:
            return canon
    return None


def load_districts():
    """label -> (polygon, scope)"""
    feats = json.load(open(DISTRICTS, encoding="utf-8"))["features"]
    return {f["properties"]["name"]: (shape(f["geometry"]), f["properties"]["scope"]) for f in feats}


def pick_site(record):
    """First site of the company that we can place on the map, else its HQ city."""
    cands = list(record.get("lower_franconia_sites") or [])
    if record.get("hq_city"):
        cands.append(record["hq_city"])
    for c in cands:
        entry = TOWNS.get(clean_town(c))
        if entry:
            return clean_town(c), entry
    return (clean_town(cands[0]) if cands else None), None


def clean_town(name):
    return re.sub(r"[\(;/,].*$", "", name or "").strip()


def compute_score(r):
    """Placeholder demo heuristic - NOT the scorer-agent pipeline in 06_Architecture_and_Ideas.md."""
    conf = r.get("confidence", "low")
    ev_pts = min(len(r.get("evidence") or []), 5) / 5 * 100
    eng_pts = min(len(r.get("previous_engagement") or []), 4) / 4 * 100
    matched = [CARITAS_THEMES[t] for t in (r.get("csr_themes") or []) if t in CARITAS_THEMES]
    act_pts = min(len(set(matched)), 4) / 4 * 100
    depth_pts = (50 if r.get("csr_report_url") else 0) + (50 if r.get("foundation") else 0)
    church_pts = 100 if r.get("caritas_or_church_link") else 0
    overall = (ev_pts * .15 + eng_pts * .25 + act_pts * .25 + depth_pts * .20 + church_pts * .15)
    return round(overall), conf, sorted(set(matched))


GOLDEN_ANGLE = 2.399963229728653
SPREAD_UNIT_DEG = 0.0045  # ~500 m * sqrt(n)


def spread_stacked(items, districts):
    """Fan companies that share a town centre out in a spiral, kept inside the
    district polygon. Approximate by design (we only know the town)."""
    groups = collections.defaultdict(list)
    for c in items:
        c["town_lat"], c["town_lng"] = c["lat"], c["lng"]
        c["approx_location"] = True
        groups[(c["lat"], c["lng"])].append(c)
    for (lat, lng), members in groups.items():
        n = len(members)
        if n < 2:
            continue
        members.sort(key=lambda c: c["name"])
        host = districts[members[0]["landkreis"]][0]   # official district of the town
        inner = host.buffer(-0.002)
        inner = host if inner.is_empty else inner
        R = SPREAD_UNIT_DEG * math.sqrt(n)
        kx = 1 / math.cos(math.radians(lat))
        for i, c in enumerate(members):
            r, a = R * math.sqrt((i + .5) / n), i * GOLDEN_ANGLE
            pt = Point(lng + r * math.cos(a) * kx, lat + r * math.sin(a))
            if inner is not None and not inner.contains(pt):
                pt = nearest_points(inner, pt)[0]
            c["lat"], c["lng"] = round(pt.y, 6), round(pt.x, 6)
    return sum(1 for m in groups.values() if len(m) > 1)


def main():
    districts = load_districts()
    records = json.load(open(RAW, encoding="utf-8"))
    out, dropped, disagree = [], [], []
    for r in records:
        site, entry = pick_site(r)
        if not entry:
            dropped.append((r["company_name"], "no placeable site", site))
            continue
        label = entry["district"]
        if not label:
            dropped.append((r["company_name"], "first placeable site is outside the diocese", site))
            continue
        coords, scope = (entry["lat"], entry["lng"]), districts[label][1]
        txt = text_district(r.get("landkreis"))
        if txt and txt != label:
            disagree.append((r["company_name"], r.get("landkreis"), label, site))
        score, conf, matched = compute_score(r)
        out.append({
            "id": re.sub(r"[^a-z0-9]+", "-", r["company_name"].lower()).strip("-"),
            "name": r["company_name"], "sector": r["sector"],
            "town": clean_town(site), "landkreis": label, "scope": scope,
            "lat": coords[0], "lng": coords[1],
            "website": r.get("website"), "ownership": r.get("ownership"),
            "employees": r.get("employees_estimate"),
            "csr_themes": r.get("csr_themes") or [], "csr_summary": r.get("csr_summary"),
            "foundation": r.get("foundation"),
            "previous_engagement": r.get("previous_engagement") or [],
            "caritas_or_church_link": r.get("caritas_or_church_link"),
            "csr_report_url": r.get("csr_report_url"),
            "evidence": r.get("evidence") or [], "source_urls": r.get("source_urls") or [],
            "confidence": conf, "notes": r.get("notes"),
            "score": score, "matched_areas": matched,
        })
    towns = spread_stacked(out, districts)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("const CAIRE_COMPANIES = ")
        json.dump(out, f, ensure_ascii=False)
        f.write(";\n")

    by_scope = collections.Counter(c["scope"] for c in out)
    print(f"{len(records)} researched -> {len(out)} on the map "
          f"({by_scope['mainfranken']} Mainfranken + {by_scope['extended']} extended); spread {towns} stacked towns")
    print(f"dropped {len(dropped)} (not guessed):")
    for d in dropped:
        print("   ", *d, sep=" | ")
    print(f"district field in the research data disagrees with the map position for {len(disagree)} companies "
          f"(map position wins):")
    for d in disagree[:12]:
        print("   ", *d, sep=" | ")


if __name__ == "__main__":
    main()
