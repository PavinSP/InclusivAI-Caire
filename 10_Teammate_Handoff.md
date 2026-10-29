# Caire — Teammate Handoff

## What we are building

Build **Caire**, a bilingual German/English AI-powered partner-discovery tool for Caritas Würzburg.

The product should answer:

> Which companies in the Mainfranken region should Caritas approach, and why are they a good match?

The core experience is:

1. Animated Caire intro page.
2. German / English language selection.
3. Mainfranken company map with search and filters.
4. Company marker preview.
5. Full company-detail page with score, confidence, evidence, risks, Caritas activity matches, and outreach preparation.
6. Deliberate research flow for companies not yet in the dataset.

## Files to read first

Read these in this order:

1. `09_Website_Build_Prompt.md` — complete product and UI specification.
2. `values.md` — canonical values ground truth for scoring.
3. `config/mainfranken_scope.json` — geographic inclusion rules.
4. `06_Architecture_and_Ideas.md` — research, scoring, aggregation, and evidence architecture.
5. `company_research/SCHEMA.md` — company record format.
6. `company_research/companies.json` — current company research data.
7. `04_Caritas_Values_Summary.md` — detailed explanation of the Caritas values source.

## Current project data

- 257 researched company records are available in `company_research/companies.json`.
- The Excel and CSV exports are derived datasets; use JSON as the main development input.
- Caritas facilities and locations are in `Caritas_Einrichtungen.xlsx`.
- Company records include source URLs, evidence, CSR themes, regional locations, and confidence levels, but some records are incomplete or uncertain.
- Do not invent missing company facts.

## Geographic rule

The default map scope is **Mainfranken**:

- Cities: Würzburg and Schweinfurt
- Districts: Bad Kissingen, Haßberge, Kitzingen, Main-Spessart, Rhön-Grabfeld, Schweinfurt, and Würzburg

Aschaffenburg and Miltenberg are excluded from the default map. Use `config/mainfranken_scope.json` rather than hard-coding the region in multiple components.

Normalize variants such as `Würzburg (Stadt)`, `Stadt Würzburg`, and `Landkreis Würzburg`, but preserve the original source value. Ambiguous multi-region records should be flagged for review.

## Scoring rules

Never display only one unexplained score. Show:

- `overall_fit_score`: how well the company appears to match Caritas.
- `evidence_confidence`: how well-supported the assessment is by credible, dated sources.

Keep these separate. A high fit score with low evidence confidence must be visibly marked as uncertain.

Use the Caritas criteria:

- Society care
- Care for individuals
- Network care
- Gospel care
- Church care
- Regional fit
- Caritas activity match
- CSR depth
- Previous engagement
- Professional responsibility
- Reputation and risk

Every criterion needs a score, reason, confidence, and cited evidence.

## Research flow

If a user searches for a company that is not already in the dataset:

1. Show that the company has not yet been researched.
2. Require an explicit “Research company” action.
3. Create a backend research job; never scrape directly in the browser.
4. Show progress: queued → collecting sources → validating → scoring → ready for review → failed.
5. Store the result using `company_research/SCHEMA.md`.
6. Show sources, dates, confidence, and unresolved fields.
7. Require human approval before adding the company to the ranked map.

Respect robots.txt, website terms, rate limits, privacy rules, and source licensing. Use generic public contact channels only.

## Recommended implementation order

### Phase 1 — Data and configuration

- Load `companies.json`.
- Load `values.md`.
- Load `config/mainfranken_scope.json`.
- Normalize locations and filter to Mainfranken.
- Add stable company IDs.
- Validate missing fields and source URLs.

### Phase 2 — Core UI

- Build the animated landing page.
- Build language selection.
- Build the bilingual application shell.
- Build map/list discovery with search and filters.
- Add marker clustering and marker preview cards.

### Phase 3 — Detail experience

- Build the full company-detail route.
- Add score and confidence display.
- Add criterion-by-criterion breakdown.
- Add evidence and source timeline.
- Add Caritas facility/activity matching.
- Add editable, clearly labeled AI outreach draft.

### Phase 4 — Research workflow

- Add backend research-job endpoint.
- Add job-status UI.
- Add structured evidence validation.
- Add human approval/rejection.
- Add approved records to the map without losing existing search state.

### Phase 5 — Quality and demo polish

- Test German and English flows.
- Test mobile and desktop layouts.
- Test keyboard navigation and reduced motion.
- Test empty, loading, failed, stale, low-confidence, and no-results states.
- Verify every visible fact has a source or is clearly marked unknown.
- Verify that only Mainfranken companies appear in the default view.

## Do not build yet

- Do not automatically email companies.
- Do not add private contact data.
- Do not add a public leaderboard or gamification.
- Do not rank companies by size or donation capacity alone.
- Do not hide the scoring methodology.
- Do not show unsupported AI-generated facts as verified facts.
- Do not display all Lower Franconia companies when the scope is Mainfranken.

## Definition of done

The first usable prototype is complete when a user can:

- Enter through the Caire animation.
- Select German or English.
- See only eligible Mainfranken companies.
- Search and filter the map/list.
- Click a company marker and open its preview.
- Open a full detail page.
- Understand fit score, confidence, evidence, source dates, and risks.
- See which Caritas services are relevant.
- Start a research job for an unknown company.
- See the research status and approve the result before publication.
- Prepare but not automatically send an evidence-based outreach draft.
