#!/usr/bin/env python3
"""Caire company research and scoring pipeline.

CLI:
    GEMINI_API_KEY=... python backend/company_pipeline.py "WIKA Alexander Wiegand"

HTTP:
    GEMINI_API_KEY=... python backend/company_pipeline.py --serve --port 8000
    curl -X POST http://localhost:8000/research \
      -H 'Content-Type: application/json' \
      -d '{"company_name":"WIKA Alexander Wiegand"}'

The browser should call the HTTP endpoint, never Gemini directly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web-demo"
RESULTS_DIR = ROOT / "company_research" / "results"


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Read KEY=value lines from the git-ignored .env file without overriding the real environment."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and key and not key.startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


load_dotenv()


def api_key() -> str:
    """GEMINI_API_KEY, or AI_API_KEY (the name the .env uses with Google's OpenAI-compatible base URL)."""
    return os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY") or ""


MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_EVIDENCE = 25

WEIGHTS = {
    "society_care_fit": 0.10,
    "individual_care_fit": 0.10,
    "network_care_fit": 0.10,
    "gospel_care_fit": 0.05,
    "church_care_fit": 0.05,
    "regional_fit": 0.15,
    "caritas_activity_fit": 0.15,
    "csr_depth_fit": 0.10,
    "previous_engagement_fit": 0.10,
    "professional_responsibility_fit": 0.05,
    "reachability_fit": 0.05,
}

ROLE_PROMPTS = {
    "society_care_fit": """Evaluate Society care / Gesellschaftssorge. Look for concrete evidence of social cohesion, peace, local community investment, advocacy for disadvantaged people, civil-society participation, and responsible use of resources. Do not count ordinary commercial activity as social commitment.""",
    "individual_care_fit": """Evaluate Care for individuals / Personensorge. Look for human dignity, inclusion, accessibility, anti-discrimination, support for children, families, elderly people, people with disabilities, migrants, refugees, people in poverty, or people in crisis, plus empowerment and participation. Do not treat a diversity slogan alone as evidence.""",
    "network_care_fit": """Evaluate Network care / Netzwerksorge. Look for reliable partnerships with NGOs, welfare organizations, municipalities, churches, schools, and community groups; multi-year cooperation; employee or skills-based volunteering; in-kind support; knowledge-sharing; and responsible employment practices.""",
    "gospel_care_fit": """Evaluate compatibility with Gospel care / Evangeliumssorge. This is not a test of whether the company is Christian. Look for practical compassion, human dignity, solidarity, ethical responsibility, long-term social commitment, and conduct compatible with Caritas' Christian social ethics.""",
    "church_care_fit": """Evaluate Church and community compatibility / Kirchensorge. Look for respectful cooperation with faith-based or community organizations, support for accessible local services, belonging, care, participation, and willingness to work across organizational boundaries. Do not require church affiliation.""",
    "regional_fit": """Evaluate verified Mainfranken eligibility using only company-site evidence and the supplied region configuration. Mainfranken includes Würzburg and Schweinfurt plus Bad Kissingen, Haßberge, Kitzingen, Main-Spessart, Rhön-Grabfeld, Schweinfurt, and Würzburg. Score 100 for a verified site in scope, 80 for a substantial verified local site with headquarters elsewhere, 50 for an ambiguous connection, and 0 for no verified site in scope. Flag ambiguity.""",
    "caritas_activity_fit": """Evaluate alignment with Caritas activity areas: childcare, children and youth, education, elderly care, disability support, migration and integration, poverty support, social counselling, health, crisis or hospice support, volunteering, and community participation. Require evidence of actual commitment, not only a generic theme.""",
    "csr_depth_fit": """Evaluate CSR/philanthropy depth. Look for concrete dated projects, named recipients, outcomes, repeated activity, foundations, budgets, responsible teams, official CSR/ESG reporting, and transparent governance. Company size or revenue alone is not CSR depth.""",
    "previous_engagement_fit": """Evaluate documented previous donations, sponsorships, partnerships, volunteering, and other social engagement. Give more weight to dated local and regional support for welfare, disability, children, elderly people, poverty, migration, hospice, Caritas, Diakonie, Lebenshilfe, Tafel, or similar causes. Separate ordinary commercial sponsorship from social engagement.""",
    "professional_responsibility_fit": """Evaluate professional responsibility, transparency, governance, compliance, quality, safeguarding, human rights, and responsible stewardship. Also flag credible evidence of discrimination, exploitation, unsafe treatment, serious unresolved compliance failures, or a material gap between CSR claims and conduct. Unverified allegations require review, not automatic disqualification.""",
    "reachability_fit": """Evaluate practical reachability: a generic CSR, foundation, sponsorship, community, press, or contact route; an application process; local decision-making presence; or evidence that the company accepts nonprofit requests. Never use private personal contact information.""",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_context() -> tuple[str, dict[str, Any]]:
    values = (ROOT / "config" / "values.md").read_text(encoding="utf-8")
    scope = load_json(ROOT / "config" / "mainfranken_scope.json")
    return values, scope


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_json_text(text: str) -> Any:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def schema_for_research() -> dict[str, Any]:
    evidence = {
        "type": "object",
        "properties": {
            "evidence_id": {"type": "string"},
            "claim": {"type": "string"},
            "excerpt": {"type": "string"},
            "url": {"type": "string"},
            "source_title": {"type": "string"},
            "source_date": {"type": "string"},
            "source_type": {"type": "string"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low", "unknown"]},
        },
        "required": ["evidence_id", "claim", "excerpt", "url", "source_title", "source_date", "source_type", "confidence"],
    }
    return {
        "type": "object",
        "properties": {
            "company_name": {"type": "string"},
            "sector": {"type": "string"},
            "hq_city": {"type": "string"},
            "lower_franconia_sites": {"type": "array", "items": {"type": "string"}},
            "landkreis": {"type": "string"},
            "website": {"type": "string"},
            "employees_estimate": {"type": "string"},
            "revenue_estimate": {"type": "string"},
            "ownership": {"type": "string"},
            "csr_themes": {"type": "array", "items": {"type": "string"}},
            "csr_summary": {"type": "string"},
            "foundation": {"type": "string"},
            "previous_engagement": {"type": "array", "items": {"type": "string"}},
            "caritas_or_church_link": {"type": "string"},
            "contact": {"type": "string"},
            "evidence": {"type": "array", "items": evidence},
            "notes": {"type": "string"},
        },
        "required": ["company_name", "sector", "hq_city", "lower_franconia_sites", "landkreis", "website", "csr_themes", "csr_summary", "previous_engagement", "evidence", "notes"],
    }


def schema_for_score() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "criterion_id": {"type": "string"},
            "score": {"type": "integer"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low", "unknown"]},
            "status": {"type": "string", "enum": ["supported", "partially_supported", "insufficient_evidence", "contradicted"]},
            "reason": {"type": "string"},
            "supporting_evidence_ids": {"type": "array", "items": {"type": "string"}},
            "contradicting_evidence_ids": {"type": "array", "items": {"type": "string"}},
            "missing_information": {"type": "array", "items": {"type": "string"}},
            "risk_flags": {"type": "array", "items": {"type": "string"}},
            "review_required": {"type": "boolean"},
        },
        "required": ["criterion_id", "score", "confidence", "status", "reason", "supporting_evidence_ids", "contradicting_evidence_ids", "missing_information", "risk_flags", "review_required"],
    }


def schema_for_summary() -> dict[str, Any]:
    item = {"type": "object", "properties": {"text": {"type": "string"}, "evidence_ids": {"type": "array", "items": {"type": "string"}}}, "required": ["text", "evidence_ids"]}
    return {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["strong_candidate", "promising_candidate", "exploratory_candidate", "do_not_prioritize", "ineligible"]},
            "headline": {"type": "string"},
            "recommendation": {"type": "string"},
            "strongest_reasons": {"type": "array", "items": item},
            "caritas_matches": {"type": "array", "items": item},
            "risks_and_unknowns": {"type": "array", "items": {"type": "string"}},
            "outreach_angle": {"type": "string"},
            "suggested_contact_route": {"type": "string"},
            "source_ids": {"type": "array", "items": {"type": "string"}},
            "human_review_required": {"type": "boolean"},
        },
        "required": ["decision", "headline", "recommendation", "strongest_reasons", "caritas_matches", "risks_and_unknowns", "outreach_angle", "suggested_contact_route", "source_ids", "human_review_required"],
    }


def generate_json(client: genai.Client, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.1,
        ),
    )
    data = parse_json_text(response.text or "")
    if not isinstance(data, dict):
        raise ValueError("Gemini returned JSON that was not an object")
    return data


def research_company(client: genai.Client, company_name: str, values: str, scope: dict[str, Any]) -> dict[str, Any]:
    search_prompt = f"""
You are the public-source research agent for Caire, a Caritas Würzburg partner-matching tool.

Research the company named: {company_name}

Use Google Search grounding to find current, public, verifiable information. Prefer official company pages, annual/CSR/ESG reports, foundations, municipal pages, nonprofit pages, and reputable regional news. Search in German and English where useful.

Focus on:
- verified company sites and locations in Mainfranken
- company sector, ownership, and public scale indicators
- concrete CSR, philanthropy, volunteering, and foundation activity
- dated previous donations or partnerships
- links to children, elderly care, disability, migration, poverty, education, health, or community work
- generic public contact routes for CSR, sponsorship, foundation, press, or community relations

Do not infer facts. If a fact cannot be verified, say Unknown. Do not include private people's contact information. Include direct URLs in the research notes. Do not write a recommendation or score yet.

Mainfranken scope configuration:
{json.dumps(scope, ensure_ascii=False, indent=2)}

Caritas values context:
{values[:12000]}
"""
    grounded = client.models.generate_content(
        model=MODEL,
        contents=search_prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.1,
        ),
    )
    research_text = grounded.text or ""
    extract_prompt = f"""
Convert the research notes below into the supplied company-record schema.

Rules:
- Use only facts explicitly present in the research notes.
- Preserve uncertainty as Unknown or null-like text.
- Create one evidence object for every important claim.
- Use only URLs present in the research notes.
- Evidence excerpts must be short and faithful; do not invent quotations.
- If a source date is not present, use Unknown.
- Do not score the company.

Research notes:
{research_text[:30000]}

Candidate company name: {company_name}
"""
    record = generate_json(client, extract_prompt, schema_for_research())
    record["company_name"] = record.get("company_name") or company_name
    record["evidence"] = record.get("evidence", [])[:MAX_EVIDENCE]
    return record


def score_one(client: genai.Client, criterion_id: str, company: dict[str, Any], values: str, scope: dict[str, Any]) -> dict[str, Any]:
    evidence = company.get("evidence", [])
    prompt = f"""
You are one specialist evaluator in the Caire system.

Criterion ID: {criterion_id}
Criterion instructions:
{ROLE_PROMPTS[criterion_id]}

Evaluate only this criterion. Use only the company record and evidence below. Every positive or negative claim must cite evidence IDs. Missing evidence means low confidence or unknown; never guess.

Caritas values ground truth:
{values[:12000]}

Region configuration:
{json.dumps(scope, ensure_ascii=False, indent=2)}

Company record:
{json.dumps(company, ensure_ascii=False, indent=2)}

Return the required score JSON. The criterion_id must be exactly: {criterion_id}
"""
    result = generate_json(client, prompt, schema_for_score())
    result["criterion_id"] = criterion_id
    result["score"] = max(0, min(100, int(result.get("score", 0))))
    return result


def confidence_number(label: str) -> float:
    return {"high": 1.0, "medium": 0.67, "low": 0.33, "unknown": 0.0}.get(label, 0.0)


def aggregate(company: dict[str, Any], scores: list[dict[str, Any]], scope: dict[str, Any]) -> dict[str, Any]:
    by_id = {item["criterion_id"]: item for item in scores}
    overall = sum(by_id[k]["score"] * weight for k, weight in WEIGHTS.items() if k in by_id)
    confidence_score = sum(confidence_number(by_id[k].get("confidence", "unknown")) * weight for k, weight in WEIGHTS.items() if k in by_id)
    confidence = "high" if confidence_score >= 0.80 else "medium" if confidence_score >= 0.55 else "low" if confidence_score >= 0.25 else "unknown"
    regional = by_id.get("regional_fit", {})
    eligible = regional.get("score", 0) > 0 and regional.get("status") != "contradicted"
    risks = sorted({flag for item in scores for flag in item.get("risk_flags", [])})
    review = any(item.get("review_required") for item in scores) or confidence in {"low", "unknown"} or not eligible
    return {
        "overall_fit_score": round(overall),
        "evidence_confidence": confidence,
        "confidence_score": round(confidence_score, 3),
        "eligibility": {"scope": scope["scope_id"], "eligible": eligible, "reason": regional.get("reason", "")},
        "criterion_scores": scores,
        "risk_flags": risks,
        "human_review_required": review,
    }


def synthesize(client: genai.Client, company: dict[str, Any], aggregate_result: dict[str, Any], values: str) -> dict[str, Any]:
    prompt = f"""
You are the recommendation writer for Caire, an evidence-based partner-matching tool for Caritas Würzburg.

Use only the company record, evaluator outputs, aggregate result, and Caritas values below. Do not invent facts or URLs. Every important claim must reference supplied evidence IDs. If evidence is weak or missing, say so.

Company:
{json.dumps(company, ensure_ascii=False, indent=2)}

Aggregate:
{json.dumps(aggregate_result, ensure_ascii=False, indent=2)}

Caritas values:
{values[:12000]}

Write a concise, honest recommendation. Include a decision, headline, recommendation, strongest reasons, relevant Caritas matches, risks/unknowns, outreach angle, contact route, source IDs, and human-review status. Return only the required JSON.
"""
    result = generate_json(client, prompt, schema_for_summary())
    result["overall_fit_score"] = aggregate_result["overall_fit_score"]
    result["evidence_confidence"] = aggregate_result["evidence_confidence"]
    return result


def run_pipeline(company_name: str, workers: int = 3) -> dict[str, Any]:
    if not api_key():
        raise RuntimeError("GEMINI_API_KEY is not set. Put it in the backend environment, never in frontend code.")
    values, scope = load_context()
    client = genai.Client(api_key=api_key())
    company = research_company(client, company_name, values, scope)
    criteria = list(ROLE_PROMPTS)
    scores: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 4))) as pool:
        futures = {pool.submit(score_one, client, key, company, values, scope): key for key in criteria}
        for future in as_completed(futures):
            scores.append(future.result())
    scores.sort(key=lambda item: criteria.index(item["criterion_id"]))
    aggregate_result = aggregate(company, scores, scope)
    summary = synthesize(client, company, aggregate_result, values)
    company_id = "company_" + hashlib.sha1(company["company_name"].lower().encode("utf-8")).hexdigest()[:12]
    return {
        "company_id": company_id,
        "company": company,
        "aggregate": aggregate_result,
        "summary": summary,
        "generated_at": utc_now(),
        "model": MODEL,
        "pipeline_version": "v1",
    }


def cache_path(company_name: str) -> Path:
    slug = re.sub(r"[^a-z0-9äöüß]+", "-", company_name.lower()).strip("-")[:60] or "company"
    return RESULTS_DIR / f"{slug}.json"


def research_cached(company_name: str) -> dict[str, Any]:
    """Re-searching the same name returns the saved result instead of paying for a new Gemini run."""
    path = cache_path(company_name)
    if path.exists():
        return load_json(path)
    result = run_pipeline(company_name)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


GUIDE_DIR = ROOT / "company_research" / "guide"
GUIDE_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # Sarah, same voice as the intro
_COMPANIES: dict[str, Any] = {}


def company_by_id(company_id: str) -> dict[str, Any] | None:
    """The scored prospects the map shows, read from web-demo/data.js."""
    if not _COMPANIES:
        text = (WEB_ROOT / "data.js").read_text(encoding="utf-8")
        m = re.search(r"^const CAIRE_COMPANIES = (.*);\s*$", text, re.M)
        _COMPANIES.update({c["id"]: c for c in json.loads(m.group(1))} if m else {})
    return _COMPANIES.get(company_id)


VERDICTS = {
    "A": "a strong fit: Caritas should approach this company now",
    "B": "a promising fit: worth nurturing, not yet a priority",
    "C": "a weak fit for now: low priority",
    "X": "not recommended: it failed the reputation check, so Caritas should not approach it",
}


def guide_text(company: dict[str, Any], lang: str) -> str:
    """Two short spoken sentences: is it a good fit, and where to read more. Verdict comes from the stored tier."""
    tier = company.get("tier_code", "C")
    expl = company.get("explanation") or {}
    facts = {
        "name": company.get("name"), "town": company.get("town"), "sector": company.get("sector"),
        "tier_verdict": VERDICTS.get(tier, VERDICTS["C"]),
        "headline": expl.get("headline"),
        "top_reasons": [d.get("why") for d in (expl.get("top_drivers") or [])[:2]],
    }
    language = "German (formal, 'Sie')" if lang == "de" else "English"
    prompt = f"""You are Caire, a friendly voice guide in a tool that helps Caritas Würzburg find corporate partners.
Write what you say out loud about this company, in {language}: at most 2 short sentences, about 35 words.
Say whether it is a good fit for Caritas, matching tier_verdict exactly (do not upgrade or downgrade it), with at most one concrete reason from the facts. Then tell the listener to see the page for more details.
Use only the facts below, no numbers or scores, no markdown, no emojis. Return only the spoken text.

Facts:
{json.dumps(facts, ensure_ascii=False)}"""
    client = genai.Client(api_key=api_key())
    response = client.models.generate_content(model=MODEL, contents=prompt, config=types.GenerateContentConfig(temperature=0.4))
    return (response.text or "").strip().strip('"')


def guide_audio(text: str, path: Path) -> bool:
    """ElevenLabs voice for the guide; False (and the browser's own voice takes over) if there is no key or quota."""
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        return False
    import urllib.request
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{GUIDE_VOICE_ID}?output_format=mp3_44100_128",
        data=json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                         "voice_settings": {"stability": 0.7, "similarity_boost": 0.75, "style": 0.2, "speed": 0.9}}).encode("utf-8"),
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            path.write_bytes(resp.read())
        return True
    except Exception as exc:  # voice is optional; the text still shows
        print(f"guide voice failed: {exc}", file=sys.stderr)
        return False


def guide(company_id: str, lang: str) -> dict[str, Any]:
    """Cached per company and language, so each summary costs one Gemini call and one voice clip, once."""
    lang = "de" if lang == "de" else "en"
    company = company_by_id(company_id)
    if not company:
        raise ValueError("unknown company")
    GUIDE_DIR.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^a-z0-9-]", "", company_id.lower()) + "_" + lang
    meta, audio = GUIDE_DIR / f"{stem}.json", GUIDE_DIR / f"{stem}.mp3"
    if meta.exists():
        text = load_json(meta)["text"]
    else:
        text = guide_text(company, lang)
        meta.write_text(json.dumps({"text": text}, ensure_ascii=False), encoding="utf-8")
    if not audio.exists():
        guide_audio(text, audio)
    return {"text": text, "audio": f"/guide-audio/{stem}.mp3" if audio.exists() else None}


CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
                 ".json": "application/json; charset=utf-8", ".png": "image/png", ".mp3": "audio/mpeg", ".jpeg": "image/jpeg", ".jpg": "image/jpeg"}


class ResearchHandler(BaseHTTPRequestHandler):
    def send_json(self, status: int, data: Any) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        # Serve the web demo from the same origin so the browser never needs the API key or CORS.
        rel = self.path.split("?", 1)[0].lstrip("/") or "index.html"
        if rel.startswith("guide-audio/"):
            base, rel = GUIDE_DIR, rel[len("guide-audio/"):]
        else:
            base = WEB_ROOT
        target = (base / rel).resolve()
        if base.resolve() not in target.parents or not target.is_file():
            self.send_error(404)
            return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES.get(target.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in ("/research", "/guide"):
            self.send_error(404, "Use POST /research or /guide")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            if self.path == "/guide":
                self.send_json(200, guide(str(body.get("id", "")), str(body.get("lang", "en"))))
                return
            company_name = str(body.get("company_name", "")).strip()
            if not company_name or len(company_name) > 200:
                raise ValueError("company_name is required and must be at most 200 characters")
            self.send_json(200, research_cached(company_name))
        except Exception as exc:  # keep the demo API simple; production should log safely
            self.send_json(500, {"error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        print(fmt % args, file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Research and score a new Caire company")
    parser.add_argument("company_name", nargs="?", help="Company to research")
    parser.add_argument("--output", type=Path, help="Write the JSON result to this file")
    parser.add_argument("--workers", type=int, default=3, help="Concurrent scoring agents, default 3")
    parser.add_argument("--serve", action="store_true", help="Start POST /research HTTP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.serve:
        server = ThreadingHTTPServer((args.host, args.port), ResearchHandler)
        print(f"Caire pipeline listening on http://{args.host}:{args.port}")
        server.serve_forever()
    if not args.company_name:
        parser.error("provide a company name or use --serve")
    result = run_pipeline(args.company_name, workers=args.workers)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
