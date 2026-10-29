"""Merge agent outputs in raw/*.json into companies.json, companies.csv and companies.xlsx."""
import csv, json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
records, seen = [], {}

def key(name):
    n = name.lower()
    n = re.sub(r"\b(gmbh|ag|se|kg|co|e\.?\s?g|eg|& co|mbh|holding|group|gruppe)\b", "", n)
    return re.sub(r"[^a-z0-9äöüß]", "", n)

for f in sorted((HERE / "raw").glob("*.json")):
    try:
        data = json.loads(f.read_text())
    except json.JSONDecodeError as e:
        print(f"!! {f.name}: invalid JSON ({e})", file=sys.stderr)
        continue
    for r in data:
        r["research_slice"] = f.stem
        k = key(r.get("company_name", ""))
        if k in seen:
            print(f"duplicate: {r['company_name']} ({f.stem}) ~ {seen[k]['company_name']} ({seen[k]['research_slice']})")
            continue
        seen[k] = r
        records.append(r)

(HERE / "companies.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))

cols = ["company_name", "sector", "hq_city", "landkreis", "lower_franconia_sites", "employees_estimate",
        "revenue_estimate", "ownership", "website", "csr_themes", "csr_summary", "foundation",
        "previous_engagement", "caritas_or_church_link", "csr_report_url", "contact", "evidence",
        "source_urls", "confidence", "notes", "research_slice"]

def flat(v):
    if isinstance(v, list):
        return " | ".join(f"{x.get('claim')}: {x.get('excerpt')} ({x.get('url')})" if isinstance(x, dict) else str(x) for x in v)
    return "" if v is None else str(v)

rows = [[flat(r.get(c)) for c in cols] for r in records]
with open(HERE / "companies.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh); w.writerow(cols); w.writerows(rows)

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook(); ws = wb.active; ws.title = "Companies"
    ws.append(cols); [setattr(c, "font", Font(bold=True)) for c in ws[1]]
    for row in rows: ws.append(row)
    ws.freeze_panes = "B2"; ws.auto_filter.ref = ws.dimensions
    wb.save(HERE / "companies.xlsx")
except ImportError:
    print("openpyxl missing; skipped xlsx", file=sys.stderr)

print(f"{len(records)} unique companies written")
