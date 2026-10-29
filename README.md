# Caire: AI partner matching for Caritas Würzburg

Caire helps the fundraising team of the **Caritasverband für die Diözese Würzburg e. V.** answer one question:

> Which companies in Lower Franconia should we approach, and why are they a good match?

It was built for the Caritas "AI Matchmaker" hackathon challenge (see [docs/challenge/](docs/challenge/)). It researches regional companies from public sources, scores each one against the Caritas values with a set of specialist scoring agents, and shows the result on an interactive map with the reasons and sources for every score.

**Live demo:** https://pavinsp.github.io/InclusivAI-Caire/

## What you can do with it

- **Map of 224 scored prospects** in Lower Franconia (switchable to the nine Mainfranken areas), with search and filters for district, evidence confidence, minimum score and Caritas field of work.
- **Colour-coded tiers:** green = approach now (A), yellow = worth nurturing (B), red = low priority (C), black = do not approach, failed the reputation check (X).
- **A page per company** with the score breakdown by agent, strengths, gaps, risks to verify, approach angle, CSR evidence and source links.
- **German and English** throughout, **light and dark mode**.
- **Voice guide:** an animated character says in two sentences whether a company is a good fit and points to the page for details. A short spoken intro is on the landing page.
- **Research on demand (local only):** type a company that is not in the list and the backend researches and scores it with Gemini.

## How it works

```
Public sources ──► research agents ──► company_research/raw/*.json ──► merge.py ──► companies.json (257 records)
                                                                                         │
                       scoring agents A1–A10 (prompts in docs/scoring_prompts.md) ◄──────┘
                                         │
                      weighted score + reputation gate + capacity multiplier
                                         ▼
                      web-demo/data.js (scored prospects) ──► map and company pages
```

- **Scoring model:** ten agents (ethical conduct, volunteering, mission and CSR match, field-of-work synergy, regional rootedness, philanthropy track record, financial capacity, timing, a pass/fail reputation gate, and a reviewer). Final score = gate × Σ(weight × score × confidence); lead priority adds a capacity multiplier and a volunteering bonus. Missing evidence gives a neutral score with low confidence, not a low score. The formulas and tier thresholds are shown on every company page.
- **Values ground truth:** [config/values.md](config/values.md), derived from the Caritas values document. Geographic rules are in [config/mainfranken_scope.json](config/mainfranken_scope.json).
- **Evidence rule:** scorers may only use evidence in the company record and must cite it. Nothing is invented; unknown stays unknown.
- Design notes and the reasoning behind the architecture: [docs/architecture.md](docs/architecture.md).

## Repository layout

| Path | What is in it |
|---|---|
| `web-demo/` | The website: landing page, Leaflet map, company pages, translations, voice guide. Static, no build step. |
| `backend/` | Python server: serves the site, researches and scores new companies with Gemini, writes the guide summaries. |
| `company_research/` | Research records per region and sector (`raw/`), their schema, and `merge.py` that builds `companies.json/.csv/.xlsx`. |
| `config/` | Caritas values and the Mainfranken scope rules used by the scoring. |
| `data/prospects/` | Prospect list without existing Caritas partners, and a ranking by how much data we hold per company. |
| `docs/` | Architecture, scoring prompts, and the challenge material (brief, transcript, values, facilities). |
| `.github/workflows/` | Publishes `web-demo/` to GitHub Pages. |

## Run it locally

**Just the website** (no keys needed):

```bash
cd web-demo
python3 -m http.server 8000      # open http://localhost:8000
```

**With the backend** (research on demand, animated guide with Gemini and ElevenLabs voice):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example .env     # then add your keys; .env is git-ignored
python backend/company_pipeline.py --serve --port 8000
```

Keys go in `.env` only, never in the web pages: `GEMINI_API_KEY` (or `AI_API_KEY`) for Gemini and `ELEVENLABS_API_KEY` for the voice. Details in [backend/README.md](backend/README.md).

**Rebuild the data:** `python company_research/merge.py` merges the research slices; the steps for the website data are in [web-demo/README.md](web-demo/README.md).

## Limitations

- **Evidence is thin for many companies.** 171 of the 224 scored prospects rest on one or two sources, and 140 are rated low confidence. Confidence is shown next to every score, and nothing has been verified by a person yet. Check the sources before contacting a company.
- **"Not yet a partner" means no Caritas link was found in public sources**, not that none exists. Compare with Caritas donor records first.
- **Map positions are approximate** (town level), not exact addresses.
- **German text is machine-translated** from the English evidence and has not been proofread.
- **Voice:** only five companies have a pre-recorded ElevenLabs voice (English). All others are read by the browser's own voice.
- **Research on demand needs the local backend** and a Gemini key; the free Gemini tier is limited to a few requests per day per model.
- Only public information is used; no private persons' contact details are stored.

## Credits

Region boundaries: GeoBasis-DE / BKG via [isellsoap/deutschlandGeoJSON](https://github.com/isellsoap/deutschlandGeoJSON). Town coordinates: GeoNames (CC BY 4.0). Map: Leaflet and leaflet.markercluster. Voice: ElevenLabs. AI assistance: Google Gemini and Anthropic Claude. Caritas facility data, values document and map are provided by Caritas Würzburg for the challenge.
