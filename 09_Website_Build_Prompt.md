# Website Build Prompt — Caire / Caritas Corporate Partner Matchmaker

Build a polished, production-quality bilingual web application called **Caire**: an AI-powered corporate-partner discovery and matching tool for Caritas Würzburg.

The purpose is to help Caritas fundraising staff answer one question:

> Which companies in the Mainfranken region should Caritas approach, and why are they a good match?

Use the local project files as the source of truth:

- `values.md` — canonical compact values ground truth for scoring and UI copy.
- `04_Caritas_Values_Summary.md` — current detailed values ground truth derived from `Caritas_Werte.pdf`.
- `Caritas_Einrichtungen.xlsx` — Caritas facilities, locations, and activity areas.
- `company_research/companies.json` — researched company records.
- `company_research/SCHEMA.md` — company data structure and evidence rules.
- `06_Architecture_and_Ideas.md` — proposed scorer-agent, aggregation, and evidence architecture.
- `config/mainfranken_scope.json` — canonical Mainfranken geographic scope and filtering rule.
- `08_Prospects_Ranked_By_Data.xlsx` and `07_Prospects_Not_Yet_Caritas_Partners.csv` — current ranked and prospect data.

Do not invent company facts, CSR activity, scores, contact details, citations, or values. Unknown information must appear as “Unknown” / “Nicht bekannt”, not as a guessed positive.

## Product and brand direction

Create a distinctive, trustworthy identity for **Caire**. Caire should feel like a calm intelligence layer for social impact: human, precise, transparent, regional, and professionally credible.

Use the supplied Caire/Caritas logo asset if available. Do not redraw or distort the logo. If no final logo asset exists, create a temporary wordmark treatment clearly marked as replaceable.

The visual language should be inspired by the interaction model of Hackathon Hub: searchable discovery, strong filter controls, map/list browsing, compact information cards, and clear detail pages. Do not copy its logo, exact visual identity, text, or layout. Hackathon Hub demonstrates the value of combining search, filters, and map/list discovery in one flow. [Hackathon Hub reference](https://hackathonhub.eu/events)

## Page 1 — Animated Caire landing page

Create a memorable but restrained animated start screen.

### Animation sequence

1. Begin with a quiet background and a subtle regional/network motif: fine lines, points, or a simplified map-like pattern.
2. Animate the Caire logo into view using a smooth, short reveal. Keep the animation elegant and accessible; avoid loud particle effects or excessive parallax.
3. Reveal a short statement such as:

   **Find the right partners for the work that matters.**

   German version:

   **Die richtigen Partner für die Arbeit finden, die zählt.**

4. Show a clear “Enter Caire” / “Caire öffnen” action.
5. Include a skip-animation option and respect `prefers-reduced-motion`.
6. Keep the full intro under approximately 3 seconds and make it usable on mobile.

### Landing-page content

- Caire logo
- “Powered by Caritas Würzburg” or equivalent attribution, only if approved
- One-sentence explanation of the product
- Enter button
- Language control or language selection entry point
- Small privacy/data-provenance note

## Page 2 — Language selection

After entering, show a simple, premium language-selection page with two large choices:

- **Deutsch**
- **English**

Store the selection for the current session and allow switching later from the application header. The interface language changes, but company names, official organization names, URLs, and source quotes should remain faithful to their original form.

Do not translate uncertain company facts automatically without showing that the summary is translated. Preserve original source excerpts alongside translated explanations when useful.

## Page 3 — Mainfranken company map and discovery dashboard

After language selection, open the main application.

### Header

- Caire logo in the top-left.
- Product name and short context: “Caritas Würzburg partner intelligence”.
- Language switcher: Deutsch / English.
- Link to methodology / “How scoring works”.
- Optional settings or data-refresh indicator.

### Main layout

Use a responsive two-panel discovery layout:

- Large interactive map in the center or left.
- Search, filters, and result list in a clearly organized panel.
- On mobile, switch to map/list tabs or a bottom-sheet result panel.

The map should show **only companies in the explicitly configured Mainfranken region**. Do not silently show every company in Lower Franconia.

Use `config/mainfranken_scope.json` as the single region configuration. The default Mainfranken scope is:

- Cities: Würzburg and Schweinfurt.
- Districts: Bad Kissingen, Haßberge, Kitzingen, Main-Spessart, Rhön-Grabfeld, Schweinfurt, and Würzburg.
- Excluded from the default scope: Aschaffenburg and Miltenberg.

Display the active scope visibly in the UI, for example: “Showing companies in Mainfranken · 9 administrative areas”. Normalize variants such as “Würzburg (Stadt)” and “Landkreis Würzburg” before filtering, but preserve the original source values. Ambiguous multi-region records must be flagged for review rather than silently included. Add a future scope switch for “Mainfranken” versus “All Lower Franconia” only if the product owner approves it.

### Map behavior

- Use a reliable map library such as Leaflet + OpenStreetMap or MapLibre.
- Show company locations as clustered markers at zoomed-out levels.
- Use marker color or size to communicate fit score only with an accessible legend.
- Do not use color alone: include score labels or icons.
- Clicking or tapping a marker opens a compact preview card with:
  - Company name
  - Town / district
  - Sector
  - Fit score
  - Confidence
  - One-line reason for the match
  - “View details” / “Details ansehen” button
- Map markers must be based on verified coordinates or clearly labeled approximate locations. Never expose private personal addresses.
- Include an attribution for map data.

### Search bar

Place the main search bar above the map/list area. It should support:

- Company name
- Town or district
- Sector
- CSR topic, such as children, elderly care, disability, migration, education, health, or volunteering
- Natural-language queries, for example:
  - “Companies in Würzburg supporting children and education”
  - “Unternehmen im Raum Aschaffenburg mit Inklusionsprojekten”

Show suggested searches and a clear empty state. Debounce input and do not trigger expensive research for every keystroke.

### Filters

Include filters for:

- Town / district
- Sector
- CSR themes
- Caritas activity match
- Minimum fit score
- Confidence level
- Existing evidence / missing evidence
- Previous social engagement
- Company size or capacity, when available

Make active filters visible as removable chips and provide “Clear all”.

### Result cards

Each result card should show:

- Company name and sector
- Local site and district
- Fit score out of 100
- Confidence badge: High / Medium / Low
- Top two matching Caritas areas
- One-sentence recommendation
- Evidence count and latest evidence date
- “View details” action

Avoid ranking companies by company size or donation capacity alone.

## Page 4 — Company detail page

When a user clicks “View details” from a map marker or result card, navigate to a dedicated detail page or a full-screen detail route. Do not make the detail view a cramped tooltip.

### Detail-page structure

#### Company header

- Company name
- Sector
- Headquarters and Mainfranken site(s)
- Website link
- Ownership type, if verified
- Fit score and confidence
- “Last researched” date
- Research status and source count

#### Recommendation summary

Write a concise answer to:

> Why should Caritas approach this company?

Include a suggested outreach angle, for example a local Caritas facility, activity area, volunteer opportunity, or partnership format. Clearly label generated recommendations.

#### Score breakdown

Show the criteria separately, not only one opaque total. Every company must have two prominent but separate top-level indicators:

- **Fit score:** how well the company appears to match Caritas.
- **Evidence confidence:** how well-supported the assessment is by verified, dated sources.

Never merge these into a single trust score. A high fit score with low confidence must be visibly labeled as uncertain.

Show these criteria separately:

- Society care / `Gesellschaftssorge`
- Care for individuals / `Personensorge`
- Network care / `Netzwerksorge`
- Gospel care / `Evangeliumssorge`
- Church care / `Kirchensorge`
- Regional fit
- Caritas activity match
- CSR depth
- Previous engagement
- Reachability
- Reputation / risk

For each criterion show:

- Score
- Weight, if used
- Short reason
- Confidence
- Evidence links

Store the scoring result in this shape:

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

Use an expandable “How was this calculated?” panel with the scoring rubric and gates. Fit score and evidence confidence must be separate values.

#### Evidence and sources

Show a transparent evidence timeline or source list:

- Claim
- Short excerpt or paraphrase
- Source title / organization
- URL
- Publication or access date
- Evidence confidence

Do not display unsupported claims as facts. Mark stale, conflicting, or uncertain information clearly.

#### Caritas alignment

Show which Caritas services and facilities are relevant. Examples include:

- Childcare and education
- Elderly care and outpatient care
- Disability support
- Migration and integration
- Poverty and social counselling
- Health and crisis support
- Volunteering and community participation

Where possible, show a local explanation such as: “This company has a site near 12 Caritas facilities with relevant activity areas.” Do not claim proximity unless it is calculated from verified facility and company coordinates.

#### Outreach preparation

Include:

- Suggested first contact route
- Suggested partnership format
- Suggested donation or support topic, if evidence supports it
- Optional German outreach email draft
- Optional English translation

The draft must be editable, clearly labeled as AI-generated, and grounded in the company’s cited evidence. Never send it automatically.

## New-company research flow

If a searched company is not already in the local dataset:

1. Show “Company not yet researched” / “Unternehmen noch nicht recherchiert”.
2. Offer a deliberate action: “Research company” / “Unternehmen recherchieren”.
3. Send the request to a backend research queue, never scrape directly from the browser. Typing, autocomplete, or pressing Enter on an ordinary search must not start scraping automatically.
4. Show progress states: queued, collecting sources, validating facts, scoring, ready for review, failed.
5. Return a structured evidence record matching `company_research/SCHEMA.md`.
6. Run scoring only after evidence collection.
7. Show source links, confidence, timestamps, and unresolved fields.
8. Allow a human to approve or reject the new record before it appears in the ranked map.
9. Show whether the company is inside the configured Mainfranken scope before scoring it.

Respect robots.txt, website terms, rate limits, source licensing, and privacy rules. Prefer official company reports and credible regional sources. Do not scrape personal contact information. Use generic public contact channels only.

Provide a useful demo fallback: if live research is unavailable, use the existing local JSON records and clearly label the result as “Demo data” or “Local dataset”.

## Scoring and evidence rules

Implement the scoring architecture described in `06_Architecture_and_Ideas.md`, but keep the weights configurable.

Important rules:

- Mainfranken presence is a geographic eligibility gate, not merely a bonus. Use `config/mainfranken_scope.json`.
- No evidence means low confidence, not a guessed score.
- A thin record must not outrank a well-documented record solely because of an optimistic estimate.
- Keep fit and confidence separate.
- Preserve evidence at every scoring step.
- Store `overall_fit_score` and `evidence_confidence` separately in the API and UI.
- The synthesizer should write the final “why approach” explanation instead of concatenating scorer outputs.
- Avoid double-counting the same source across multiple criteria.
- Flag conflicting sources for human review.
- Never use religion, nationality, or company size as a proxy for value alignment.

## UX and visual quality

- Calm, modern, editorial, and data-rich without feeling like an enterprise spreadsheet.
- Strong typographic hierarchy and generous spacing.
- Rounded cards, restrained borders, subtle shadows, and clear states.
- Use animation to guide attention, not decorate every interaction.
- Responsive from mobile to large desktop.
- Keyboard navigable and screen-reader friendly.
- Meet WCAG-minded contrast and focus-state requirements.
- Include loading, empty, error, stale-data, low-confidence, and no-results states.
- Preserve the map/list context when returning from a company detail page.
- Keep the primary action obvious: discover a company, understand its fit, prepare outreach.

## Suggested navigation

- `/` — animated Caire intro
- `/language` — Deutsch / English choice
- `/discover` — Mainfranken map, search, filters, and result list
- `/company/:id` — company detail and evidence
- `/methodology` — scoring, sources, limitations, and values
- `/research/:jobId` — optional research-progress page

## What to remove or avoid

- Do not put all 257 researched companies on the map if they fall outside Mainfranken.
- Do not expose raw JSON, internal agent names, or implementation jargon to normal users.
- Do not show a single score without the breakdown and evidence.
- Do not scrape a company automatically just because a user typed a partial name.
- Do not present unverified Wikipedia-only facts as high-confidence evidence.
- Do not include private contact information.
- Do not create a giant dashboard before the core map, search, detail, and evidence flow works.
- Do not add a public “leaderboard” or gamification layer; this is a sensitive fundraising workflow.
- Do not include a donation or outreach submission action until human approval and permissions are designed.
- Do not hard-code the values in UI components; load the approved values from `values.md` / a configurable content layer so future revisions do not require a frontend rewrite.

## Definition of done

The prototype is successful when a user can:

1. Enter through the animated Caire intro.
2. Choose German or English.
3. See only the configured Mainfranken companies on the map.
4. Search or filter companies.
5. Tap a map marker and open a preview.
6. Navigate to a full company detail page.
7. Understand the score, confidence, Caritas alignment, sources, and risks.
8. Search for a company not yet researched and start a transparent research job.
9. Return to the map without losing the search context.
10. Prepare, but not automatically send, an evidence-based outreach draft.
