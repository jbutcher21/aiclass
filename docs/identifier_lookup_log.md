# Identifier Lookup Log

Purpose: Record curated web lookups used to disambiguate identifier types or standards. Do not include PII. Link only to authoritative/neutral sources. Mirror key conclusions back into `identifier_crosswalk.json` when approved.

## Logging Guidelines
- No PII: redact values, use placeholders (e.g., `<VALUE>`)
- Authoritative sources: standards bodies, official registries, primary docs
- Minimalism: capture just enough to audit the decision
- Crosswalk sync: propose alias/canonical additions after confirmation

## Entry Template

---
Date: YYYY-MM-DD

Query: What does token "<TOKEN>" represent? Country/context: <CC|ORG|Unknown>

Candidate Meanings:
- Meaning A — Source: <URL>
- Meaning B — Source: <URL>

Evaluation:
- Notes: <brief rationale>

Conclusion:
- Canonical: <CANONICAL_KEY e.g., INN>
- Senzing Feature: <FEATURE e.g., TAX_ID>
- Attributes: <attribute keys that must be populated, e.g., TAX_ID_TYPE, TAX_ID_COUNTRY>

Actions:
- Crosswalk update proposed: <Yes|No>
- Aliases to add: ["<ALIAS1>", "<ALIAS2>"]
- Country/Issuer rule: <e.g., TAX_ID_COUNTRY="RU">

Reviewer Approval: <name/initials or link to approval>

---

## Example Entry

---
Date: 2025-09-10

Query: What is token "INN"? Country/context: RU

Candidate Meanings:
- RU Taxpayer Identification Number — Source: https://en.wikipedia.org/wiki/Tax_identification_number#Russia
- RU Federal Tax Service — Source: https://www.nalog.gov.ru/ (landing)

Evaluation:
- Commonly used abbreviation (ИНН) for Russia taxpayer ID; maps to tax identifier; requires country RU

Conclusion:
- Canonical: INN
- Senzing Feature: TAX_ID
- Attributes: TAX_ID_TYPE, TAX_ID_NUMBER, TAX_ID_COUNTRY

Actions:
- Crosswalk update proposed: Yes
- Aliases to add: ["ИНН"]
- Country/Issuer rule: TAX_ID_COUNTRY="RU"

Reviewer Approval: <JB>

---

