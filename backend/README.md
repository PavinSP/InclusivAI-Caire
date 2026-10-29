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

## HTTP endpoint for the future search bar

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
