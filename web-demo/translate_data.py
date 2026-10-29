#!/usr/bin/env python3
"""Build data_de.js: German versions of the English text in data.js, for the DE view of the map and company pages.

    ../.venv/bin/python translate_data.py

Uses Gemini (GEMINI_API_KEY from ../.env, like the backend). The pages look up each English string in
CAIRE_DE and fall back to English when a string is missing, so a partial run still works.
Translations are cached in translations_de.json, so re-running only translates new strings.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "backend"))
import company_pipeline as cp  # noqa: E402  (loads ../.env and the Gemini client settings)
from google import genai  # noqa: E402

CACHE = HERE / "translations_de.json"
OUT = HERE / "data_de.js"
BATCH = 60
# Identifiers, names, places and values the pages match on stay as they are.
SKIP_KEYS = {"id", "pid", "name", "website", "source_urls", "url", "town", "landkreis", "tier_code", "confidence",
             "scope", "position", "matched_areas", "csr_themes", "agent", "method", "lat", "lng"}


def load_data() -> list:
    src = (HERE / "data.js").read_text(encoding="utf-8")
    m = re.search(r"^const CAIRE_COMPANIES = (.*);\s*$", src, re.M)
    return json.loads(m.group(1))


def collect(node, key=None, out=None):
    out = set() if out is None else out
    if key in SKIP_KEYS:
        return out
    if isinstance(node, dict):
        for k, v in node.items():
            collect(v, k, out)
    elif isinstance(node, list):
        for v in node:
            collect(v, key, out)
    elif isinstance(node, str) and len(node) > 3 and re.search(r"[A-Za-z]{3}", node) and not re.match(r"https?://", node):
        out.add(node)
    return out


def translate(client, texts: list) -> list:
    prompt = (
        "Translate each English string in this JSON array into natural German for a Caritas fundraising team. "
        "Keep company names, place names, numbers, currencies, dates, URLs, tier letters (A/B/C/X) and German "
        "words that are already German unchanged. Return a JSON array of the same length and order.\n\n"
        + json.dumps(texts, ensure_ascii=False)
    )
    resp = client.models.generate_content(
        model=cp.MODEL, contents=prompt,
        config=genai.types.GenerateContentConfig(response_mime_type="application/json",
                                                 response_schema={"type": "array", "items": {"type": "string"}},
                                                 temperature=0.1))
    result = cp.parse_json_text(resp.text or "")
    if not isinstance(result, list) or len(result) != len(texts):
        raise ValueError("translation batch came back with the wrong length")
    return result


def main() -> None:
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    todo = sorted(collect(load_data()) - cache.keys())
    print(f"{len(cache)} cached, {len(todo)} to translate")
    if todo:
        client = genai.Client(api_key=cp.os.environ["GEMINI_API_KEY"])
        for i in range(0, len(todo), BATCH):
            chunk = todo[i:i + BATCH]
            try:
                cache.update(zip(chunk, translate(client, chunk)))
            except Exception as exc:  # keep going; the next run retries the failed batch
                print(f"batch {i // BATCH + 1} failed: {exc}", file=sys.stderr)
                continue
            CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {min(i + BATCH, len(todo))}/{len(todo)}")
    OUT.write_text(f"const CAIRE_DE = {json.dumps(cache, ensure_ascii=False)};\n", encoding="utf-8")
    print(f"wrote {OUT.name} with {len(cache)} strings")


if __name__ == "__main__":
    main()
