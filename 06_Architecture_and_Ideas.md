# Architecture & Ideas: Caritas AI Matchmaker

Written for: the hackathon team (Pavin and teammates).

## 1. Core idea

One scraper agent builds an evidence record per company. That record is sent to about 10 scorer agents, and each one scores a single criterion using its own rules. A synthesizer agent then combines the scores into one overall score and writes the reasons for approaching the company.

```
Company list ──► Research job ──► Scraper agent ──► Evidence record (company_research/raw/*.json)
                                        │
        ┌──────────┬──────────┬─────────┼──────────┬──────────┐
     Scorer 1   Scorer 2   Scorer 3   ...      Scorer 10
   (score + reason + cited evidence + confidence each)
        └──────────┴──────────┴─────────┼──────────┴──────────┘
                                        ▼
                      Aggregator (weights + gates)
                                        ▼
                  Synthesizer (why approach, outreach angle,
                  matching Caritas services, German email draft)
                                        ▼
                  Ranked list UI (+ Mainfranken map view)
```

## 2. Assessment of the idea

It fits the brief, which asks "which companies, and why" with rationale and evidence, not just a number. Parallel specialist scorers keep each criterion explainable.

### Risks and fixes
1. **No scoring from memory.** Scorers may only use the scraped evidence and must cite it. No evidence means low confidence, not a guessed score.
2. **Scrape once, fan out.** All scorers read the same record, so they don't disagree on facts.
3. **Confidence next to fit.** A thin record must not outrank a well-documented one (the schema already has `confidence`).
4. **Weights and gates, not a plain average.** For example, no Lower Franconia presence means excluded.
5. **Synthesizer agent.** It writes the final "why", not a concatenation of ten reasons.
6. **Transparent rubric in the UI.** Show criteria, weights and evidence quotes.
7. **Separate fit from confidence.** `overall_fit_score` answers how well the company appears to match; `evidence_confidence` answers how well-supported that assessment is.
8. **Research deliberately.** Typing in the search box must not start scraping. A user explicitly starts a research job, which runs in the backend and enters human review before publication.

## 3. Scorer agents (draft, 8 to 10)

| # | Agent | Question it answers | Main inputs |
|---|---|---|---|
| 1 | Society fit (Gesellschaftssorge) | Sustained local investment, social cohesion, cooperation with civil society? | csr_summary, previous_engagement |
| 2 | Individuals fit (Personensorge) | Inclusion, accessibility, support for vulnerable people? | csr_summary, evidence |
| 3 | Network fit (Netzwerksorge) | Reliable partnerships with NGOs, church, public bodies? | previous_engagement, caritas_or_church_link |
| 4 | Regional fit | Sites in Caritas towns / Landkreise (checked against the facilities Excel) | lower_franconia_sites, landkreis |
| 5 | CSR depth | Real foundation or budget versus marketing language | foundation, csr_report_url |
| 6 | Past engagement | Concrete, dated donations to social/church causes | previous_engagement |
| 7 | Activity match | CSR themes versus Caritas fields (children, elderly care, migration, disability, counselling) | csr_themes |
| 8 | Financial capacity | Size and revenue versus plausible gift size | employees_estimate, revenue_estimate |
| 9 | Reputation / risk | Controversies, exclusion topics (arms, gambling) | evidence, news |
| 10 | Reachability | Contact path or open application form | contact, website |

Output of every scorer: `{score 0-100, reason, evidence[{claim, excerpt, url}], confidence}`.

## 4. Aggregation (draft)

- **Gates (fail means excluded):** verified Mainfranken presence according to `config/mainfranken_scope.json`; no unresolved reputation or exclusion red flag.
- **Weighted sum** of the remaining scorers. Starting weights: values (1-3 combined) 25%, regional 15%, activity match 15%, past engagement 15%, CSR depth 10%, capacity 10%, reachability 5%, reputation 5%.
- **Confidence** is the average of the scorer confidences. The UI shows fit and confidence separately.
- Weights are a starting point and should be tuned on known good partners such as Sparkasse Mainfranken.

The scoring record should include:

```json
{
  "overall_fit_score": 0,
  "evidence_confidence": "low",
  "confidence_reasons": [],
  "eligibility": {
    "scope": "mainfranken",
    "eligible": false,
    "reason": ""
  },
  "criteria": [],
  "human_review_required": true
}
```

## 5. Extra ideas for the demo

- **Map/list discovery:** Use a Hackathon Hub-inspired discovery pattern: search and filters above a map/list view, clustered markers, compact previews, and dedicated detail pages. The product must have its own Caire visual identity.
- **Map view:** Caritas facilities plotted against company sites, with matched pairs linked. Strongest demo visual.
- **Facility-level matching:** "Company X sits near 12 Caritas kitas in Aschaffenburg" rather than matching to Caritas as a whole.
- **German outreach email draft** per company, referencing its own past giving.
- **Ask-size estimate:** realistic donation range from past gifts and company size.
- **Timing signals:** anniversaries, new sites, foundation grant cycles.
- **Ethical-exclusion filter** based on the values document.
- **Gap analysis:** Caritas fields with no matched sponsors yet.

## 6. Priorities

1. Clean pipeline from scraper to scorers to synthesizer, with evidence kept at every step.
2. Ranked list with expandable reasons, evidence and sources.
3. Map view and German outreach draft as the two demo-visible extras.

## 7. Current state (2026-10-29)

- `company_research/raw/` has two slices: `banks_utilities_retail` (5 companies) and `aschaffenburg_miltenberg` (11).
- `merge.py` dedupes the slices into `companies.json`, `.csv` and `.xlsx`.
- `config/mainfranken_scope.json` defines the default map/filter scope: Würzburg and Schweinfurt plus the seven Mainfranken districts.
- `values.md` is the compact ground-truth file used by the website and scoring layer; the expanded interpretation remains in `04_Caritas_Values_Summary.md`.
- Not yet built: scorer agents, aggregator, synthesizer, UI.
