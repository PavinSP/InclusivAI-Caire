# Caire Values Ground Truth

This file is the compact, machine-readable interpretation of `docs/challenge/Caritas_Werte.pdf` for the Caire corporate-partner matcher. The detailed source interpretation is in `docs/challenge/values_summary.md`.

## Organization

Caritasverband für die Diözese Würzburg e. V. is a Christian, professional welfare and civil-society organization serving people in the Diocese of Würzburg and Lower Franconia. It is rooted in the Gospel but provides practical help to all people, regardless of whether they are Christian. It works with professional staff, volunteers, churches, public authorities, welfare organizations, and civil-society partners.

## Five equally important areas of responsibility

These areas are complementary and must not be treated as a ranking.

### 1. Society care — `Gesellschaftssorge`

Caritas wants to contribute to peace, social cohesion, a good society, and the common good. It participates in public life, contributes professional expertise, advocates for disadvantaged people whose voices are not sufficiently heard, strengthens local solidarity, and handles entrusted funds economically and responsibly.

### 2. Care for individuals — `Personensorge`

Caritas serves people because every person has dignity and value, not because they belong to a particular religion. It supports wellbeing, self-help, independence, self-determination, participation, and the development of each person's abilities. It respects personal, cultural, religious, and spiritual diversity.

### 3. Network care — `Netzwerksorge`

Caritas develops a reliable network of help. It cooperates with church organizations, public welfare bodies, other welfare providers, local institutions, and civil-society actors. It values quality, sustainable financing, qualified staff, appropriate working conditions, local resources, shared expertise, and long-term cooperation.

### 4. Gospel care — `Evangeliumssorge`

Caritas derives its mission from the Gospel and makes faith credible through practical compassion, solidarity, hope, love, and service to people in need. It continuously reviews and improves its services against people's needs and Christian social ethics. A partner does not need to be Christian, but its conduct must be compatible with human dignity, compassion, solidarity, and responsible service.

### 5. Church care — `Kirchensorge`

Caritas is an active social and pastoral part of the Church. It helps the Church remain credible, relevant, and present in people's everyday lives and life crises, including beyond traditional church structures. It values cooperation, learning, practical compassion, and accessible local support.

## Foundational principles

- **Human dignity and personality (`Personalität`):** people have rights, agency, abilities, and a right to participate in decisions affecting their lives.
- **Solidarity (`Solidarität`):** people and institutions have responsibilities toward one another, especially toward people experiencing poverty, exclusion, crisis, or disadvantage.
- **Subsidiarity (`Subsidiarität`):** decisions and support should be as close to people and local communities as possible, with higher-level support where needed.
- **Common good (`Gemeinwohl`):** activities should create broad social value rather than benefit only a narrow group.
- **Peace and social cohesion:** partners should support constructive coexistence and avoid discrimination, division, violence, and exploitation.
- **Responsible stewardship:** financial and other entrusted resources should be used transparently, lawfully, economically, and responsibly.

## Partner-alignment criteria

A strong potential partner demonstrates evidence of:

1. Human dignity, empowerment, accessibility, and non-discrimination.
2. Solidarity with people experiencing disadvantage or vulnerability.
3. Broad social or community benefit.
4. A real connection to Mainfranken or another relevant local Caritas area.
5. Alignment with Caritas activities such as childcare, education, elderly care, disability support, migration/integration, poverty support, counselling, health, and crisis support.
6. Respectful, reliable, and preferably long-term cooperation.
7. Transparent and responsible governance, funding, and reporting.
8. Support for employees, volunteers, local institutions, or community-led solutions.
9. Willingness to cooperate with a Christian organization without requiring beneficiaries or employees to be Christian.
10. Evidence of learning, innovation, service improvement, or knowledge-sharing where relevant.

## Positive evidence

Give additional weight to dated and verifiable evidence such as:

- Multi-year social investment or partnerships.
- Local grants, donations, or volunteering in Mainfranken.
- Support for children, families, elderly people, people with disabilities, refugees, migrants, people in poverty, or people in crisis.
- Employee volunteering or skills-based support.
- Partnerships with NGOs, welfare organizations, municipalities, or community groups.
- Transparent reporting of beneficiaries, outcomes, funding, and limitations.
- Fair treatment of employees and affected communities.

## Caution evidence

Reduce confidence and trigger human review for credible evidence of:

- Discrimination, exclusion, exploitation, unsafe treatment, or serious social harm.
- A material gap between CSR claims and business conduct.
- Unclear donation use or opaque governance.
- A purely publicity-driven contribution without meaningful social benefit.
- Conduct that undermines peace, human dignity, solidarity, or the common good.
- Pressure that would compromise Caritas' independence or service to beneficiaries.
- Serious unresolved controversies or compliance failures.

Unverified allegations must not automatically disqualify a company. Store the source, date, confidence, and resolution status.

## Scoring rules

- Keep **fit** and **evidence confidence** as separate fields.
- No evidence means `unknown` or low confidence; it does not mean positive alignment.
- Score each criterion separately before aggregation.
- Preserve the evidence claim, excerpt/paraphrase, URL, source date, and confidence.
- Do not rank by donation capacity, company size, religion, nationality, or industry alone.
- Do not require a company to be Christian or church-affiliated.
- Do not treat CSR slogans as evidence without concrete activity or outcomes.
- Flag conflicting sources for human review.
- Keep the five areas of responsibility equally important unless an explicitly approved weighting says otherwise.

## Canonical assessment fields

```text
society_care_fit
individual_care_fit
network_care_fit
gospel_care_fit
church_care_fit
regional_fit
caritas_activity_fit
csr_depth_fit
previous_engagement_fit
professional_responsibility_fit
reputation_risk
overall_fit_score
evidence_confidence
positive_evidence[]
caution_evidence[]
source_urls[]
human_review_required
```

Each criterion should contain a score, reason, confidence, and cited evidence. An overall recommendation must explain **why** the company is relevant to Caritas and which Caritas activity or local facility could be the basis for outreach.

## Ground-truth definition

> A good Caritas partner is a transparent, responsible, locally relevant organization whose demonstrated actions support human dignity, solidarity, inclusion, the common good, and reliable cooperation with Caritas' professional services and networks.
