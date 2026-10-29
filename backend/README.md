# Caire Gemini Company Pipeline

This backend accepts a company name, researches public information with Gemini Google Search grounding, extracts a structured evidence record, runs specialist evaluators, calculates the weighted score in Python, and generates a cited recommendation.

## Setup

Use a virtual environment and install the dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export GEMINI_API_KEY="your-key"
```

Never place the real key in frontend code, JSON files, Git, or browser requests.

## CLI

```bash
python backend/company_pipeline.py "WIKA Alexander Wiegand" --output company_research/results/wika.json
```

## HTTP server (website + endpoints)

Start the local backend:

```bash
python backend/company_pipeline.py --serve --port 8000
```

Call it from the server-side application or a local demo frontend:

```bash
curl -X POST http://127.0.0.1:8000/research \
  -H 'Content-Type: application/json' \
  -d '{"company_name":"WIKA Alexander Wiegand"}'
```

The response includes:

- Structured company record
- Evidence objects and URLs
- Specialist criterion scores
- Deterministic weighted aggregate
- Separate fit score and evidence confidence
- Risk flags and human-review status
- Final recommendation and outreach angle

## Important prototype limitations

- This is a synchronous demo endpoint. Production should use a job queue and return a `job_id` immediately.
- The Gemini Google Search result is used for public research; the model must not be treated as an infallible scraper.
- Add retries, request-rate limits, persistence, authentication, and structured logging before deployment.
- Validate all sources and manually review new companies before publishing them on the map.

## Endpoints and caches

- `GET /` serves `web-demo/`, so the site and the API share one origin.
- `POST /research` `{"company_name": "..."}` researches and scores a new company; results are cached in `company_research/results/`.
- `POST /guide` `{"id": "<company id>", "lang": "en|de"}` returns the animated guide's summary and a voice clip; cached in `company_research/guide/`.
- Both cache folders are git-ignored. The static site uses pre-generated summaries from `web-demo/build_guide_static.py` instead.
