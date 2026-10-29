# Company research schema (one JSON array per agent)

Each element:
{
  "company_name": "official name",
  "sector": "e.g. Automotive supplier, Banking, Retail",
  "hq_city": "city of headquarters",
  "lower_franconia_sites": ["Würzburg", "Schweinfurt", ...],
  "landkreis": "primary Landkreis / kreisfreie Stadt in Unterfranken",
  "employees_estimate": "number or range, with year if known (region or total, say which)",
  "revenue_estimate": "with year, or null",
  "ownership": "family-owned / listed / cooperative / public / foreign subsidiary ...",
  "website": "https://...",
  "csr_themes": ["children & youth", "elderly care", "disability inclusion", "poverty", "migration/integration", "education", "health", "environment", "culture", "sport", "regional development", "volunteering"],
  "csr_summary": "2-4 sentences on concrete CSR / philanthropy activity",
  "foundation": "name of corporate/family foundation, if any, else null",
  "previous_engagement": ["concrete donations, sponsorships, partnerships with dates, esp. social/church/Caritas/Diakonie/Lebenshilfe/Tafel"],
  "caritas_or_church_link": "any known link to Caritas, Diözese Würzburg, Catholic/Christian institutions, else null",
  "csr_report_url": "URL to sustainability/CSR/ESG report or page, or null",
  "contact": "public contact for CSR/sponsoring/press (generic email/page only, no private persons' personal data)",
  "evidence": [{"claim": "...", "excerpt": "short quote/paraphrase", "url": "..."}],
  "source_urls": ["..."],
  "confidence": "high | medium | low (how well-evidenced the record is)",
  "notes": "anything relevant, e.g. size uncertain, possible fit angles"
}

Rules: only real, verified info; null where unknown; never invent donations or URLs.
