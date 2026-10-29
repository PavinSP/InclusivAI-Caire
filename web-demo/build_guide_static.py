#!/usr/bin/env python3
"""Pre-generate the animated guide's summaries for the static GitHub Pages site.

    ../.venv/bin/python build_guide_static.py both A,vogel-communications-group-gmbh-co-kg en
    # args: mode (text|voice|both), tier letters and/or company ids, languages (en, de or en,de)
    ../.venv/bin/python build_guide_static.py text A,B        # Gemini text (cheap) for these tiers and/or company ids
    ../.venv/bin/python build_guide_static.py voice A,B       # ElevenLabs clips (costs credits) for the same selection

Writes guide_data.json ({id: {en, de, audio_en, audio_de}}) and guide_audio/*.mp3 next to the pages. guide.js reads
them when the site is not on localhost; companies without a clip are read by the browser's own voice.
"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "backend"))
import company_pipeline as cp  # noqa: E402

DATA, AUDIO = HERE / "guide_data.json", HERE / "guide_audio"


def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {}


def companies(sel: set) -> list:
    """Companies whose tier code or id is in sel."""
    cp.company_by_id("")
    return [c for c in cp._COMPANIES.values() if c.get("tier_code") in sel or c["id"] in sel]


def text_for(c, lang, retries=4):
    import time
    for i in range(retries):
        try:
            return cp.guide_text(c, lang)
        except Exception as exc:
            time.sleep(2 * (i + 1))
            err = exc
    print("failed", c["id"], lang, err, file=sys.stderr)
    return None


def build_text(sel: set, langs: tuple) -> None:
    out = load()
    jobs = [(c, l) for c in companies(sel) for l in langs if not out.get(c["id"], {}).get(l)]
    print(len(jobs), "summaries to write")
    with ThreadPoolExecutor(6) as pool:
        for (c, l), t in zip(jobs, pool.map(lambda j: text_for(*j), jobs)):
            if t:
                out.setdefault(c["id"], {})[l] = t
    DATA.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("have", sum(1 for v in out.values() if v.get("en") and v.get("de")), "companies with both languages")


def build_voice(sel: set, langs: tuple) -> None:
    out = load()
    AUDIO.mkdir(exist_ok=True)
    n = chars = 0
    for c in companies(sel):
        for l in langs:
            t = out.get(c["id"], {}).get(l)
            f = AUDIO / f"{c['id']}_{l}.mp3"
            if t and not f.exists() and cp.guide_audio(t, f):
                n += 1; chars += len(t)
            if f.exists():
                out[c["id"]]["audio_" + l] = f"guide_audio/{f.name}"
    DATA.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(n, "clips made,", chars, "characters")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    sel = set((sys.argv[2] if len(sys.argv) > 2 else "A").split(","))
    langs = tuple((sys.argv[3] if len(sys.argv) > 3 else "en").split(","))
    if mode in ("text", "both"):
        build_text(sel, langs)
    if mode in ("voice", "both"):
        build_voice(sel, langs)
