This document defines the Senzing Entity Specification — a detailed guide for mapping source data into Senzing’s entity resolution engine.

The process of mapping is taking a source field name, like CustomerName, and transforming it into a target field name, by applying specific rules, such as renaming, reformatting, or combining fields based on predefined logic or conditions. It’s like creating a bridge where data from one system is reshaped to fit the structure of another system, guided by those rules.

# Key Terms

![Diagram: Entity → Features → Attributes](images/ges-image1-key_terms.jpg "An Entity has Features; Features have Attributes")

## Entities, Features and Attributes:
- **Entity** — A real-world subject, primarily a PERSON or an ORGANIZATION, described by one record.
- **Feature** — A set of related attributes about the entity (e.g., NAME, ADDRESS, PHONE).
- **Attribute** — A single field within a feature (e.g., NAME_FIRST and NAME_LAST in NAME; ADDR_LINE1 in ADDRESS).

## Usage types and payload (optional attributes)
- **Usage Type** — A short label that distinguishes multiple instances of the same feature on one entity (e.g., HOME vs MAILING address, MOBILE vs HOME phone, PRIMARY vs ALIAS name). It helps explain “which one it is” when there are several. 
- **Payload Attributes** — These are attributes that are not used for matching, but can be helpful in understanding matches or making quick decisions. (e.g., STATUS: Active|Inactive, RISK_CATEGORY, INDUSTRY_CODE)

# What Features to Map

Entity resolution works best when you have a name and as many other features as you can find. The more features on each record, the better the entity resolution! Below are feature lists to look for in your sources. Rank indicates typical importance to entity resolution. 

| Feature | Description | Importance | Guidance |
| --- | --- | --- | --- |
| RECORD_TYPE | (e.g., PERSON, ORGANIZATION) | High | Include when known to prevent cross‑type resolution; omit if unknown. Use standardized kinds (PERSON, ORGANIZATION). Often used to determine icon/shape in graphs. |
| NAME (person) | Personal names | High | Look for: legal name, aliases/AKAs, maiden/former names, nickname/preferred name, transliterations/alternate scripts. Prefer parsed components when available (FIRST, MIDDLE, LAST, SUFFIX). |
| NAME (organization) | Organization legal or trade name | High | Look for: legal/registered name, trade/DBA, former names, short/brand names, transliterations/alternate scripts. |
| DATE_OF_BIRTH | Person date of birth | High | Full date preferred; partial values accepted. |
| ADDRESS (person) | Postal/physical address | High | Look for: residential/home, mailing/remittance, previous/old; prefer parsed components when available (LINE1/2, CITY, STATE/PROVINCE, POSTAL_CODE, COUNTRY). |
| ADDRESS (organization) | Organization location address | High | Look for: physical/business/registered office, mailing/remittance; prefer parsed components when available (LINE1/2, CITY, STATE/PROVINCE, POSTAL_CODE, COUNTRY). |
| PASSPORT | Passport identifier | High | Include issuing country. |
| DRLIC | Driver’s license | High | Include issuing state/province/country. |
| SSN | US Social Security Number | High | Partial values accepted. |
| TAX_ID | Tax identifier | High | Look for: EIN, VAT, TIN/ITIN; include issuing country. |
| NATIONAL_ID (person) | National/person identifier | High | Look for country‑specific IDs; include issuing country. Common examples: SIN (CA), CURP (MX), NINO (UK), NIR/INSEE (FR). |
| NATIONAL_ID (organization) | National/company registration identifier | High | Look for company registry numbers (not tax/VAT); include issuing country. Common examples: Company Number/CRN (UK), SIREN/SIRET (FR), Corporation Number (CA), Folio Mercantil (MX). |
| PHONE | Telephone number | Medium | Look for all phone numbers; distinguish mobile if possible; personal mobile numbers carry additional weight. |
| EMAIL | Email address | Medium | — |
| Social handles | Social/media handles | Medium | Features include: LINKEDIN, FACEBOOK, TWITTER, SKYPE, ZOOMROOM, INSTAGRAM, WHATSAPP, SIGNAL, TELEGRAM, TANGO, VIBER, WECHAT. |
| DUNS_NUMBER | Company identifier | Medium | — |
| LEI_NUMBER | Legal Entity Identifier | Medium | — |
| NPI_NUMBER | US healthcare provider ID | Medium | — |
| ACCOUNT | Account or card number | Medium | Look for bank or other account numbers that can aid resolution, especially across data sources. |
| OTHER_ID | Other/uncategorized identifier | Medium | For identifier types that can’t be mapped to one of Senzing’s specific identifier features. Use sparingly; if an identifier is used frequently, create a dedicated feature for it. |
| GENDER | Person gender | Low-Medium | — |
| EMPLOYER | Name of a person's employer | Medium-Low | Can aid resolution on smaller companies; subject to generic thresholds; form of group association. |
| GROUP_ASSOCIATION | Other organization names an entity is associated with | Medium-Low | Can aid resolution on smaller domains, subject to generic thresholds. |
| GROUP_ASSN_ID | Group identifier | Medium-Low | Can aid resolution on smaller domains, subject to generic thresholds. |
| DATE_OF_DEATH | Person date of death | Medium-Low | When applicable. |
| REGISTRATION_DATE | Organization registration/incorporation date | Medium-Low | Full date preferred; partial values accepted. |
| REGISTRATION_COUNTRY | Organization registration country | Low | — |
| NATIONALITY | Person nationality | Low | — |
| CITIZENSHIP | Person citizenship | Low | — |
| PLACE_OF_BIRTH | Person place of birth | Low | Typically not well controlled. |
| WEBSITE | Organization website/domain | Low | Typically shared across the organization’s hierarchy. |
| REL_ANCHOR | Relationship anchor for an entity | Relationship | Required if the entity can be related to; one per record. |
| REL_POINTER | Pointer to a related entity’s anchor | Relationship | Place on source entity; include REL_POINTER_ROLE (e.g., EMPLOYED_BY, SUBSIDIARY_OF, SPOUSE_OF). |
| TRUSTED_ID | Curated control identifier | Control | Forces records together or apart; like a curated ID layered over source IDs. Use cautiously per guidance. |

## Payload Attributes (Optional)

The full details about a record should exist in your source systems. Senzing holds the features needed for entity resolution and acts as a pointer system to where the full details of their record can be found.

Payload attributes are optional because they are not used in matching. However, they can help a human reviewer quickly triage a match and decide whether looking up the full record is warranted.

Here are some examples of useful payload attributes:

- STATUS: Active/Inactive helps triage quickly (e.g., ignore inactive duplicates; focus on active customers).
- CREATE_DATE (or FIRST_SEEN): Helps sort duplicates and spot fraud risk (e.g., a new record with conflicting identifiers vs. an older established one).
- INDUSTRY_CODE/INDUSTRY: Codes and labels from data providers that describe the business (e.g., NAICS/SIC).
- JOB_TITLE: Role/title from HR or data providers; can inform risk, especially when matched to a watchlist entry.
- RISK_CATEGORY/RISK_SCORE: Watchlist-derived codes/scores that explain the type and severity of risk.

Performance note:
- Payload increases storage and I/O. Include only when it materially improves downstream understanding. On very large systems, evaluate impact before enabling broadly.
- If you do decide to include them, keep them minimal and only include what helps a human understand matches or an algorithm to triage them.
- You may decide to map a few during a proof of concept while you are analyzing matches and then remove them when you go to production.

# Examples of Senzing JSON

In prior versions we recommended a flat JSON structure with a separate sub-list for each feature that had multiple values. While we still support that, we now recommend the following JSON structure that has just one list for all features. It is much cleaner, and if you standardize on it, you can write a single parser to extract values for downstream processes if needed.

## Recommended JSON Structure

One Record Per Entity (Joining)
- Emit one JSON record per entity containing all FEATURES and disclosed relationships.
- Join/aggregate child tables/arrays into the master before output.
- Add REL_ANCHOR to any entity that can be related to; place REL_POINTER on the source of the relationship pointing to the target’s anchor.

Example (person)
```json
{
  "DATA_SOURCE": "CUSTOMERS",
  "RECORD_ID": "1001",
  "FEATURES": [
    { "RECORD_TYPE": "PERSON" },
    { "NAME_FIRST": "Robert", "NAME_LAST": "Smith" },
    { "DATE_OF_BIRTH": "1978-12-11" },
    { "ADDR_TYPE": "HOME", "ADDR_LINE1": "123 Main Street", "ADDR_CITY": "Las Vegas", "ADDR_STATE": "NV", "ADDR_POSTAL_CODE": "89132" },
    { "ADDR_TYPE": "MAILING", "ADDR_LINE1": "1515 Adela Lane", "ADDR_CITY": "Las Vegas", "ADDR_STATE": "NV", "ADDR_POSTAL_CODE": "89111" },
    { "PHONE_TYPE": "MOBILE", "PHONE_NUMBER": "702-919-1300" },
    { "DRIVERS_LICENSE_NUMBER": "112233", "DRIVERS_LICENSE_STATE": "NV" },
    { "EMAIL_ADDRESS": "bsmith@work.com" },
    { "REL_ANCHOR_DOMAIN": "CUSTOMERS", "REL_ANCHOR_KEY": "1001" },
    { "REL_POINTER_DOMAIN": "CUSTOMERS", "REL_POINTER_KEY": "1005", "REL_POINTER_ROLE": "SON_OF" }
  ],
  "CREATE_DATE": "2020-06-15",
  "STATUS": "Active"
}
```

Structure & Rules
- Root keys:
  - DATA_SOURCE: required (string).
  - RECORD_ID: strongly recommended (string), unique within DATA_SOURCE.
  - FEATURES: required (array of flat objects).
- FEATURES content:
  - One feature family per object (e.g., a NAME object, an ADDRESS object). Do not mix families in the same object.
  - RECORD_TYPE: optional but recommended; include as its own object when known (e.g., `{ "RECORD_TYPE": "PERSON" }`).
  - Usage types: include only when the source indicates them (e.g., NAME_TYPE PRIMARY/AKA, ADDR_TYPE HOME/MAILING/BUSINESS, PHONE_TYPE MOBILE).
- Mixing rules:
  - Do not mix NAME_FULL with parsed name fields in the same object.
  - Do not mix ADDR_FULL with parsed address fields in the same object.
- Relationship rules:
  - REL_ANCHOR: place one per record when the entity can be related to (REL_ANCHOR_DOMAIN, REL_ANCHOR_KEY).
  - REL_POINTER: place on the source entity for each disclosed relationship (REL_POINTER_DOMAIN, REL_POINTER_KEY, REL_POINTER_ROLE).
  - Do not mix REL_ANCHOR and REL_POINTER attributes in the same object (separate objects are fine in the same FEATURES array).
- Payload:
  - Optional, top-level scalars only (no lists/objects at root).
  - Use sparingly to aid human triage (e.g., STATUS, CREATE_DATE/FIRST_SEEN, ORG_STATUS, INDUSTRY).
  - The full record details should remain in your source systems; Senzing acts as a pointer system.

### Scalar vs Non-scalar (Good vs Bad)

Use one FEATURE object per attribute (a single string). Do not supply lists or nested objects inside a single feature object when there are multiple.

- ✅ Good (scalar)
```json
{
  "FEATURES": [
    { "EMAIL_ADDRESS": "alex@example.com" },
    { "EMAIL_ADDRESS": "a.taylor@example.com" }
  ]
}
```

- ❌ Bad (non-scalar list)
```json
{
  "FEATURES": [
    { "EMAIL_ADDRESS": ["alex@example.com", "a.taylor@example.com"] }
  ]
}
```

## Flat JSON Structure (Supported, not preferred)

The FEATURES‑list structure above is preferred. Flat JSON is supported for sources that cannot produce a FEATURES array. When using flat JSON, the rules under “Structure & Rules” still apply conceptually; where they reference FEATURES, interpret as root‑level attributes with unique prefixes.

Example (flat JSON)
```json
{
  "DATA_SOURCE": "CUSTOMERS",
  "RECORD_ID": "1001",
  "RECORD_TYPE": "PERSON",
  "NAME_LAST": "Fletcher",
  "NAME_FIRST": "Irwin",
  "NAME_MIDDLE": "Maurice",
  "DATE_OF_BIRTH": "1943-10-08",
  "HOME_ADDR_LINE1": "123 Main Street",
  "HOME_ADDR_CITY": "Las Vegas",
  "HOME_ADDR_STATE": "NV",
  "HOME_ADDR_POSTAL_CODE": "89132",
  "MAILING_ADDR_LINE1": "3 Underhill Way",
  "MAILING_ADDR_LINE2": "#7",
  "MAILING_ADDR_CITY": "Las Vegas",
  "MAILING_ADDR_STATE": "NV",
  "MAILING_ADDR_POSTAL_CODE": "89101",
  "MOBILE_PHONE_NUMBER": "702-919-1300",
  "EMAIL_ADDRESS": "babar@work.com",
  "STATUS": "Active",
  "CREATE_DATE": "2020-06-15"
}
```

How prefixes become usage types
- Root attribute names must be unique. When a source has multiple instances of the same feature, prefix each set with a single token (no punctuation). The prefix becomes the usage type.
  - Example: `HOME_ADDR_*` → `ADDR_TYPE=HOME`; `MAILING_ADDR_*` → `ADDR_TYPE=MAILING`.
  - Example: `MOBILE_PHONE_NUMBER` → `PHONE_TYPE=MOBILE`.

Flat JSON tips
- Prefer the recommended FEATURES‑list structure whenever possible for clarity and consistency.
- Use single‑token prefixes only (no punctuation) so the parser recognizes usage types.
- Relationship fields may appear at root as needed (e.g., `REL_ANCHOR_DOMAIN`, `REL_ANCHOR_KEY`, `REL_POINTER_DOMAIN`, `REL_POINTER_KEY`, `REL_POINTER_ROLE`). When relationships are present, the FEATURES‑list structure is clearer.
- Payload at root must be single values (scalars). Do not include lists or nested objects at root.

# Source Schema Types

Source inputs come in many forms: CSV/TSV files, JSON/JSONL, XML dumps, Parquet, and database queries/exports. Regardless of format, the mapping approach is the same: identify core entities (persons, organizations), find all feature data linked to them, and model disclosed relationships.

Common shapes
- Tabular/relational: master tables for core entities (persons, organizations) plus child tables for additional names, addresses, phones, identifiers, and relationship link tables. Use primary/foreign keys to join. Look up codes (e.g., ADDR_TYPE, country) via reference/code tables where needed. Map each fragment, then join/aggregate into one record per entity with all FEATURES and relationships.
- Graph‑like: node/edge exports. Nodes are entities (persons, organizations); edges are relationships. Features primarily come from node properties, but some sources model certain features (e.g., ADDRESS) as their own nodes. In that case, take the feature from the related node — there is no need to map it twice if it also appears as a property. Represent each disclosed relationship with a REL_POINTER from the source node to the target node’s REL_ANCHOR.

Relationships are directional
- The “from” (source) record gets the REL_POINTER; the “to” (target) record gets the REL_ANCHOR. Include one REL_ANCHOR per record when it can be related to; include as many REL_POINTERs as needed to represent its outgoing relationships.

Checklist
- Keys: Find the primary key for each core entity (per DATA_SOURCE). If none exists, construct a deterministic ID (e.g., hash of normalized identifying attributes) to use as RECORD_ID.
- Children: Identify child lists/tables for names, addresses, phones, identifiers, emails, websites, social handles; join/aggregate them as separate FEATURES.
- Relationships: Locate link/join tables or explicit edge lists with roles/verbs; produce REL_POINTER(s) from the source entity to the target’s REL_ANCHOR with a clear REL_POINTER_ROLE.
- Arrays/sub‑documents: In JSON/XML, locate nested arrays (names, addresses, phones, identifiers) and flatten into FEATURES.
- Code lookups: Resolve type and country codes via code tables (e.g., address types, identifier issuing countries).
- Join strategy: Emit one JSON record per entity, containing all FEATURES and REL_* features, per the Recommended JSON Structure.

Embedded (keyless) entities
- For records that reference entities without unique keys (e.g., sender and receiver on transactions), extract identifying attributes and compute a deterministic RECORD_ID as a hash of normalized values. Stamp this ID on the source record before mapping to Senzing, and track these IDs on the source side as well.
- For records that have features that clearly do not belong to the primary entity (e.g., employer name and address on a contact list, reference name and phone number on a job application), consider creating a second entity related to the primary entity.
- Use a stable normalization recipe (fixed fields and order; trim/collapse whitespace; case‑fold; normalize punctuation/diacritics) before hashing.

# General mapping guidance

The following sections cover how Senzing treats record updates versus replacements, usage types, and identifier mapping.

Important: Decisions in this section affect matching behavior and whether records break or reinforce matches. Coordinate changes carefully and validate with sample runs.
- Updating vs Replacing determines which features are present at match time (no hidden history in Senzing).
- Usage types with special meaning (PRIMARY/BUSINESS/MOBILE) influence display/weighting.
- Identifier choices (specific vs NATIONAL_ID/TAX_ID/OTHER_ID) control break/no‑break behavior.

## Updating vs Replacing Records

Senzing always replaces records. It keeps governance and interpretation clear, avoids storing stale or unknown history in Senzing, and respects data‑provider and watchlist contracts that often forbid retaining prior values. It is also impossible for Senzing alone to know whether a prior address was corrected vs. a move, or whether a missing phone was removed on purpose.

Guidance
- Present all features you wish to retain (including historical values) in a single JSON record at update time.
- If the source keeps feature history, map that history as additional FEATURES.
- If the source lacks history, you may maintain your own small history table (DATA_SOURCE, RECORD_ID, FEATURE type, feature JSON) and merge as needed when producing the new record.

## Mapping Usage Types

Senzing matches across usage types because they are not well standardized and are often mislabeled across systems. Therefore, map usage types primarily for reference. However, three usage types do have special meaning that influences display or weighting.

Guidance
- Only include usage types when the source clearly provides them.
- Special meanings that influence resolution/display:
  - NAME_TYPE PRIMARY: Used to choose the best display name when multiple names exist.
  - ADDR_TYPE BUSINESS (organizations): Adds weight to an organization’s physical location.
  - PHONE_TYPE MOBILE: Adds weight to personal mobile numbers.

## Mapping Identifiers

Some source systems have many codes for identifiers, and mapping them to Senzing attributes is not always obvious. The spec provides specific features for common identifiers (e.g., SSN, PASSPORT, DRLIC, DUNS_NUMBER, LEI_NUMBER, NPI_NUMBER) and three generic features (NATIONAL_ID, TAX_ID, OTHER_ID) for identifiers that are not one of the specifics.

Guidance
- Prefer specific features (SSN, PASSPORT, DRLIC, DUNS_NUMBER, LEI_NUMBER, NPI_NUMBER) before generic NATIONAL_ID/TAX_ID/OTHER_ID.
- Always include issuer details when applicable (e.g., country for PASSPORT/NATIONAL_ID/TAX_ID; state/country for DRLIC).
- Use OTHER_ID sparingly rather than as a catch‑all; prefer adding specific features to avoid cross‑type false positives.
- When unknown, consult and maintain a mapping table (a “crosswalk”) and perform curated lookups (no PII) against authoritative sources; add findings to your crosswalk when confirmed.

### Choosing NATIONAL_ID vs TAX_ID vs OTHER_ID (when unknown)

Some sources provide a list of identifiers with fields like `id_type`, `id_number`, and `id_country`. Others embed the country in the type (e.g., `RU-INN`). Use the steps below to choose the right Senzing feature and to standardize types.

Guidance
- Normalize the type token (uppercase, trim punctuation). Split any country prefix (e.g., `RU-INN` → country `RU`, type `INN`).
- If the type clearly maps to a specific feature, use it (e.g., SSN → SSN; PASSPORT → PASSPORT; DRIVERS_LICENSE → DRLIC; LEI → LEI_NUMBER; DUNS → DUNS_NUMBER; NPI → NPI_NUMBER).
- Otherwise decide among generics using issuer/purpose:
  - NATIONAL_ID: issued by a country as a national identifier (often one per person/org). Examples: `CEDULA` (various LATAM countries), `SIREN` (FR org id).
  - TAX_ID: issued by a country (or state) specifically for taxation (orgs or persons). Examples: `EIN/FEIN` (US), `INN` (RU), `VAT` (many countries).
  - OTHER_ID: use as a last resort when you cannot confidently classify; include a meaningful `OTHER_ID_TYPE`.
- Always include the issuer where applicable (country/state). If not provided, infer from the type token only when reliable.
- Maintain a local crosswalk of tokens → canonical types and target features. Add aliases (e.g., `FEIN` → `EIN`) and record conclusions from curated lookups so decisions are consistent.

Examples
- `INN` or `RU-INN` (Russia tax id) → TAX_ID with `TAX_ID_TYPE=INN`, `TAX_ID_COUNTRY=RU`.
- `EIN`/`FEIN` (US) → TAX_ID with `TAX_ID_TYPE=EIN`, `TAX_ID_COUNTRY=US`.
- `CEDULA` (various countries) → NATIONAL_ID with `NATIONAL_ID_TYPE=CEDULA` and the appropriate `NATIONAL_ID_COUNTRY`.
- `SIREN` (FR company id) → NATIONAL_ID with `NATIONAL_ID_TYPE=SIREN`, `NATIONAL_ID_COUNTRY=FR`.

# Registered Feature Attributes

## Attributes for the Record Key

These attributes tie records in Senzing back to your source system. Place them at the root of each JSON record.

| Attribute | Required | Example | Guidance |
| --- | --- | --- | --- |
| DATA_SOURCE | Required | CUSTOMERS | Short, stable code naming the source (e.g., CUSTOMERS). If you have multiple similar sources, use distinct codes (e.g., BANKING_CUSTOMERS, MORTGAGE_CUSTOMERS). Prefer uppercase, no spaces. Used for retrieval and reporting — keep it consistent. |
| RECORD_ID | Strongly Recommended | 1001 | Must be unique within DATA_SOURCE; used to add/replace records. If the source lacks a primary key, construct a deterministic ID (e.g., hash of normalized identifying attributes). If omitted, Senzing generates a hash of features, making updates impractical. Do not duplicate RECORD_ID as a feature — retrieval uses DATA_SOURCE + RECORD_ID. |

Example
```json
{
  "DATA_SOURCE": "CUSTOMERS",
  "RECORD_ID": "1001",
}
```

### FEATURE: RECORD_TYPE
Importance: High

| Attribute | Required | Example | Guidance |
| --- | --- |  --- | --- |
| RECORD_TYPE | Recommended | PERSON | Prevents records of different types from resolving. Include when known to prevent cross‑type resolution; leave blank if unknown. Use standardized kinds (PERSON, ORGANIZATION). Often used to pick the icon/shape in graphs. |

Example
```json
{
  "FEATURES": [
    { "RECORD_TYPE": "PERSON" }
  ]
}
```

Tips for adding RECORD_TYPEs
- If you choose to add RECORD_TYPE, pick values that make sense for visualization too (e.g., a value that can map to a graph icon/shape).
- Many watchlists have standardized on values such as VESSEL and AIRCRAFT. You do not need to register these in Senzing to use them as RECORD_TYPE.
- If you add such types, also include their appropriate identifiers as FEATURES so matching remains effective (e.g., `IMO_NUMBER`, `CALL_SIGN` for vessels; `AIRCRAFT_TAIL_NUMBER` for aircraft).


## Feature: NAME
Importance: High

| Attribute    | Example                 | Guidance |
| ---          | ---                     | --- |
| NAME_TYPE    | PRIMARY                 | Optional; include when the source provides it. Common values: PRIMARY, AKA (persons), DBA (organizations). |
| NAME_FIRST   | Robert                  | Person given name. |
| NAME_LAST    | Smith                   | Person surname. |
| NAME_MIDDLE  | A                       | Person middle name/initial (optional). |
| NAME_PREFIX  | Dr                      | Person title/prefix (optional). |
| NAME_SUFFIX  | Jr                      | Person suffix (optional). |
| NAME_ORG     | Acme Tire Inc.          | Organization name. |
| NAME_FULL    | Robert J Smith, Trust   | Single-field name when type (person vs org) is unknown or only a full name is provided. |

Rules
- Prefer parsed person names (NAME_FIRST/NAME_LAST/...) when available; use NAME_ORG for organizations; use NAME_FULL only when the type is unknown or only a single field exists.
- One feature family per object: do not mix NAME_FULL with parsed name fields in the same object; do not mix NAME_ORG with parsed person fields in the same object.
- Use NAME_TYPE only when provided by the source (e.g., PRIMARY, AKA, DBA).
- When multiple names exist, NAME_TYPE=PRIMARY is special: it determines the best display name for the resolved entity (prefer PRIMARY over AKA).

Examples
- ✅ Person (parsed)
```json
{
  "FEATURES": [
    { "NAME_FIRST": "Robert", "NAME_LAST": "Smith", "NAME_MIDDLE": "A" }
  ]
}
```
- ✅ Organization
```json
{
  "FEATURES": [
    { "NAME_ORG": "Acme Tire Inc.", "NAME_TYPE": "PRIMARY" }
  ]
}
```
- ✅ Unknown type
```json
{
  "FEATURES": [
    { "NAME_FULL": "Robert J Smith, Trust" }
  ]
}
```
- ❌ Incorrect (split across multiple NAME objects)
```json
{
  "FEATURES": [
    { "NAME_LAST": "Smith" },
    { "NAME_FIRST": "Robert" }
  ]
}
```
- ❌ Incorrect (mixing NAME_ORG with parsed person fields)
```json
{
  "FEATURES": [
    { "NAME_ORG": "Acme Tire Inc.", "NAME_FIRST": "Robert" }
  ]
}
```

## Feature: ADDRESS
Importance: High

| Attribute       | Example                                   | Guidance |
| ---             | ---                                       | --- |
| ADDR_TYPE       | HOME                                      | Optional; include when provided by the source. Common values: HOME, MAILING (persons); BUSINESS (organizations). |
| ADDR_LINE1      | 111 First St                              | First address line (street, number). |
| ADDR_LINE2      | Suite 101                                 | Second address line (apt/suite). |
| ADDR_LINE3      |                                           | Third address line (optional). |
| ADDR_LINE4      |                                           | Fourth address line (optional). |
| ADDR_LINE5      |                                           | Fifth address line (optional). |
| ADDR_LINE6      |                                           | Sixth address line (optional). |
| ADDR_CITY       | Las Vegas                                 | City/locality. |
| ADDR_STATE      | NV                                        | State/province/region code. |
| ADDR_POSTAL_CODE| 89111                                     | Postal/ZIP code. |
| ADDR_COUNTRY    | US                                        | Country code. |
| ADDR_FULL       | 3 Underhill Way, Las Vegas, NV 89101, US  | Single-field address when parsed components are unavailable. |

Rules
- Prefer parsed address fields when available (ADDR_LINE1..ADDR_LINE6, ADDR_CITY, ADDR_STATE, ADDR_POSTAL_CODE, ADDR_COUNTRY).
- Use ADDR_FULL only when parsed components are unavailable.
- Do not mix ADDR_FULL with parsed address fields in the same object.
- For organizations, assign ADDR_TYPE=BUSINESS to at least one address when known (adds weight to the physical location).

Examples
- ✅ Parsed address
```json
{
  "FEATURES": [
    { "ADDR_TYPE": "HOME", "ADDR_LINE1": "111 First St", "ADDR_CITY": "Las Vegas", "ADDR_STATE": "NV", "ADDR_POSTAL_CODE": "89111" }
  ]
}
```
- ✅ Single-field address
```json
{
  "FEATURES": [
    { "ADDR_TYPE": "MAILING", "ADDR_FULL": "3 Underhill Way, Las Vegas, NV 89101, US" }
  ]
}
```
- ❌ Incorrect (mixing ADDR_FULL with parsed fields)
```json
{
  "FEATURES": [
    { "ADDR_FULL": "123 Main St, Las Vegas, NV 89132", "ADDR_CITY": "Las Vegas" }
  ]
}
```

## Feature: PHONE
Importance: Medium

| Attribute    | Example       | Guidance |
| ---          | ---           | --- |
| PHONE_TYPE   | MOBILE        | Optional; include when provided by the source. Common values: MOBILE, HOME, WORK, FAX. MOBILE carries extra weight. |
| PHONE_NUMBER | 702-555-1212  | Telephone number. |

Rules
- Include PHONE_TYPE only when the source provides it (MOBILE carries extra weight).
- One PHONE object per number; represent multiple numbers as multiple PHONE objects.
- Do not put a list of numbers inside a single PHONE object.
- When a source uses clear prefixes (e.g., HOME_PHONE), you may derive PHONE_TYPE from the prefix.

Examples
```
{
  "FEATURES": [
    { "PHONE_TYPE": "MOBILE", "PHONE_NUMBER": "702-555-1212" },
    { "PHONE_NUMBER": "702-555-3434" }
  ]
}
```

## Physical and other attributes

### Feature: GENDER
Importance: Low-Medium

| Attribute | Example | Guidance |
| ---       | ---     | --- |
| GENDER    | M       | Gender code or label from the source. For matching, only M, F, Male, and Female are considered; other values are ignored to avoid denials (e.g., M vs UNK). |

Example
```json
{
  "FEATURES": [
    { "GENDER": "F" }
  ]
}
```

### Feature: DOB (Date of Birth)
Importance: High

| Attribute       | Example     | Guidance |
| ---             | ---         | --- |
| DATE_OF_BIRTH   | 1980-05-14  | Complete dates preferred; partial dates accepted when only partial is available (e.g., YYYY‑MM or MM‑DD). |

Examples
```json
{
  "FEATURES": [
    { "DATE_OF_BIRTH": "1980-05-14" }
  ]
}
```

### Feature: DOD (Date of Death)
Importance: Low-Medium

| Attribute       | Example     | Guidance |
| ---             | ---         | --- |
| DATE_OF_DEATH   | 2010-05-14  | Complete dates preferred; partial dates accepted when only partial is available (e.g., YYYY‑MM or MM‑DD). |

Example
```json
{
  "FEATURES": [
    { "DATE_OF_DEATH": "2010-05-14" }
  ]
}
```

### Feature: NATIONALITY
Importance: Low

| Attribute   | Example | Guidance |
| ---         | ---     | --- |
| NATIONALITY | US      | Country of nationality (code or label) as provided by the source. |

Example
```json
{
  "FEATURES": [
    { "NATIONALITY": "US" }
  ]
}
```

### Feature: CITIZENSHIP
Importance: Low

| Attribute   | Example | Guidance |
| ---         | ---     | --- |
| CITIZENSHIP | US      | Country of citizenship (code or label) as provided by the source. |

Example
```json
{
  "FEATURES": [
    { "CITIZENSHIP": "US" }
  ]
}
```

### Feature: POB (Place of Birth)
Importance: Low

| Attribute        | Example   | Guidance |
| ---              | ---       | --- |
| PLACE_OF_BIRTH   | Chicago   | Place of birth; may be a city/region or a country code/label as provided by the source. |

Example
```json
{
  "FEATURES": [
    { "PLACE_OF_BIRTH": "Chicago, IL" }
  ]
}
```

### Feature: REGISTRATION_DATE (Organizations)
Importance: Low-Medium

| Attribute          | Example     | Guidance |
| ---                | ---         | --- |
| REGISTRATION_DATE  | 2010-05-14  | Organization registration/incorporation date. Complete dates preferred; partial dates accepted when only partial is available (e.g., YYYY‑MM or MM‑DD). |

Example
```json
{
  "FEATURES": [
    { "REGISTRATION_DATE": "2010-05-14" }
  ]
}
```

### Feature: REGISTRATION_COUNTRY (Organizations)
Importance: Low

| Attribute             | Example | Guidance |
| ---                   | ---     | --- |
| REGISTRATION_COUNTRY  | US      | Country of registration (code or label) as provided by the source. |

Example
```json
{
  "FEATURES": [
    { "REGISTRATION_COUNTRY": "US" }
  ]
}
```

## Identifiers

### Feature: PASSPORT
Importance: High

| Attribute          | Example     | Guidance |
| ---                | ---         | --- |
| PASSPORT_NUMBER    | 123456789   | Passport number. |
| PASSPORT_COUNTRY   | US          | Issuing country. Strongly recommended. |

Example
```json
{
  "FEATURES": [
    { "PASSPORT_NUMBER": "123456789", "PASSPORT_COUNTRY": "US" }
  ]
}
```

### Feature: DRLIC (Driver’s License)
Importance: High

| Attribute               | Example | Guidance |
| ---                     | ---     | --- |
| DRIVERS_LICENSE_NUMBER  | 112233  | Driver’s license number. |
| DRIVERS_LICENSE_STATE   | NV      | Issuing state/province/country. Strongly recommended. |

Example
```json
{
  "FEATURES": [
    { "DRIVERS_LICENSE_NUMBER": "112233", "DRIVERS_LICENSE_STATE": "NV" }
  ]
}
```

### Feature: SSN (US Social Security Number)
Importance: High

| Attribute   | Example      | Guidance |
| ---         | ---          | --- |
| SSN_NUMBER  | 123-12-1234  | US Social Security Number; partial accepted. |

Example
```json
{
  "FEATURES": [
    { "SSN_NUMBER": "123-12-1234" }
  ]
}
```

### Feature: NATIONAL_ID
Importance: High

| Attribute            | Example   | Guidance |
| ---                  | ---       | --- |
| NATIONAL_ID_TYPE     | CEDULA    | Use the type label from the source; standardize across sources. |
| NATIONAL_ID_NUMBER   | 123121234 | National identifier value. |
| NATIONAL_ID_COUNTRY  | FR        | Issuing country. Strongly recommended. |

Rules
- If the source type cannot be standardized and NATIONAL_ID_COUNTRY is present, leave NATIONAL_ID_TYPE blank.

Good/Bad
- ✅ Good
```json
{
  "FEATURES": [
    { "NATIONAL_ID_TYPE": "SIREN", "NATIONAL_ID_NUMBER": "552081317", "NATIONAL_ID_COUNTRY": "FR" }
  ]
}
```
- ❌ Bad (SSN mapped as NATIONAL_ID)
```json
{
  "FEATURES": [
    { "NATIONAL_ID_TYPE": "SSN", "NATIONAL_ID_NUMBER": "123-12-1234" }
  ]
}
```

### Feature: TAX_ID
Importance: High

| Attribute        | Example     | Guidance |
| ---              | ---         | --- |
| TAX_ID_TYPE      | EIN         | Use the type label from the source; standardize across sources. |
| TAX_ID_NUMBER    | 12-3456789  | Tax identification number. |
| TAX_ID_COUNTRY   | US          | Issuing country. Strongly recommended. |

Rules
- If the source type cannot be standardized and TAX_ID_COUNTRY is present, leave TAX_ID_TYPE blank.

Good/Bad
- ✅ Good
```json
{
  "FEATURES": [
    { "TAX_ID_TYPE": "EIN", "TAX_ID_NUMBER": "12-3456789", "TAX_ID_COUNTRY": "US" }
  ]
}
```
- ❌ Bad (EIN as NATIONAL_ID)
```json
{
  "FEATURES": [
    { "NATIONAL_ID_TYPE": "EIN", "NATIONAL_ID_NUMBER": "12-3456789", "NATIONAL_ID_COUNTRY": "US" }
  ]
}
```

### Feature: OTHER_ID
Importance: Medium

| Attribute         | Example  | Guidance |
| ---               | ---      | --- |
| OTHER_ID_TYPE     | ISIN     | Standardized source type strongly recommended as not always issued by a country |
| OTHER_ID_NUMBER   | 123121234| Identification number. |
| OTHER_ID_COUNTRY  | MX       | Optional as country often not known or issued by an organization |

Rules
- Use OTHER_ID sparingly, not as a catch‑all when you cannot confidently classify to a specific or generic feature.
- Prefer adding a specific feature for frequently used non‑country identifiers so matching behavior can be adjusted.

Example
```json
{
  "FEATURES": [
    { "OTHER_ID_TYPE": "ISIN", "OTHER_ID_NUMBER": "123121234" }
  ]
}
```

### Feature: ACCOUNT
Importance: Medium

| Attribute        | Example                | Guidance |
| ---              | ---                    | --- |
| ACCOUNT_NUMBER   | 1234-1234-1234-1234    | Account number (e.g., bank, card). |
| ACCOUNT_DOMAIN   | VISA                   | Domain/system for the account number. |

Example
```json
{
  "FEATURES": [
    { "ACCOUNT_NUMBER": "1234-1234-1234-1234", "ACCOUNT_DOMAIN": "VISA" }
  ]
}
```

### Feature: DUNS_NUMBER
Importance: Medium

| Attribute    | Example | Guidance |
| ---          | ---     | --- |
| DUNS_NUMBER  | 123123  | Dun & Bradstreet company identifier. |

Example
```json
{
  "FEATURES": [
    { "DUNS_NUMBER": "123123" }
  ]
}
```

### Feature: NPI_NUMBER
Importance: Medium

| Attribute    | Example | Guidance |
| ---          | ---     | --- |
| NPI_NUMBER   | 123123  | US healthcare provider identifier. |

Example
```json
{
  "FEATURES": [
    { "NPI_NUMBER": "123123" }
  ]
}
```

### Feature: LEI_NUMBER
Importance: Medium

| Attribute    | Example | Guidance |
| ---          | ---     | --- |
| LEI_NUMBER   | 123123  | Legal Entity Identifier. |

Example
```json
{
  "FEATURES": [
    { "LEI_NUMBER": "123123" }
  ]
}
```

## Feature: EMAIL
Importance: Medium

| Attribute      | Example                | Guidance |
| ---            | ---                    | --- |
| EMAIL_ADDRESS  | someone@somewhere.com  | Email address. |


Example
```json
{
  "FEATURES": [
    { "EMAIL_ADDRESS": "alex@example.com" }
  ]
}
```

## Feature: WEBSITE
Importance: Low

| Attribute        | Example          | Guidance |
| ---              | ---              | --- |
| WEBSITE_ADDRESS  | somecompany.com  | Website or domain; typically for organizations. |

Example
```json
{
  "FEATURES": [
    { "WEBSITE_ADDRESS": "acmetire.com" }
  ]
}
```

## Features for Social Media Handles
Importance: Medium

Social handle features use the feature name as the attribute name.

| Feature/Attribute | Example           | Guidance |
| ---               | ---               | --- |
| LINKEDIN          | in/jane-doe       | Canonical handle/ID; no URL; no leading @. |
| FACEBOOK          | brand.page        | Canonical handle/ID; no URL; no leading @. |
| TWITTER           | john_doe          | Canonical handle/ID; no URL; no leading @. |
| SKYPE             | handle            | Canonical handle/ID; no URL. |
| ZOOMROOM          | room-id           | Canonical handle/ID; no URL. |
| INSTAGRAM         | jane.doe          | Canonical handle/ID; no URL; no leading @. |
| WHATSAPP          | +14155551234      | Canonical handle/ID; also map to PHONE. |
| SIGNAL            | +14155551234      | Canonical handle/ID; also map to PHONE. |
| TELEGRAM          | acme_support      | Canonical handle/ID; strip t.me/. |
| TANGO             | handle            | Canonical handle/ID; no URL. |
| VIBER             | +14155551234      | Canonical handle/ID; also map to PHONE. |
| WECHAT            | handle            | Canonical handle/ID; no URL. |

Rules
- Normalize values: store the canonical handle/ID, not a full URL. Strip `http(s)://`, `www.`, trailing slashes, query params, and a leading `@`.
- One handle per object: add one FEATURES object per platform handle; do not concatenate multiple handles.
- Prefer handle/ID over URL: if only a profile URL is provided, extract the handle/ID.
- Don’t use content links: skip post/status URLs; only capture profile-level handles/IDs.
- Case handling: store handles lowercased for case‑insensitive platforms; preserve exact case if a platform is case‑sensitive.
- Phone‑based apps: when a handle is a phone number (e.g., WhatsApp, Signal, Viber), also map the number to PHONE in addition to the app‑specific feature.
- Persons vs organizations: map personal handles on person records and brand handles on organization records when known; avoid crossing them.
- Stability: handles can change; use alongside stronger identifiers (email, phone, gov IDs).

- Platform specifics
  - TWITTER (X): letters, numbers, underscores; length 1–15; case‑insensitive.
  - INSTAGRAM: letters, numbers, periods, underscores; length 1–30; case‑insensitive.
  - TELEGRAM: letters, numbers, underscores; 5–32; case‑insensitive; strip `t.me/`.
  - LINKEDIN: prefer the public slug (e.g., `in/jane-doe` or `company/acme`); if only a URL is provided, extract the slug.

Example
```json
{
  "FEATURES": [
    { "LINKEDIN": "in/john-smith" },
    { "TWITTER": "janedoe" }
  ]
}
```

## Group Associations

Group associations capture memberships or affiliations (e.g., employer, club) that aid entity resolution across sources. They do not create disclosed relationships. Group associations are subject to generic thresholds and are most effective for smaller, specific groups; they are less effective for very large, generic groups.

### Feature: EMPLOYER
Importance: Low-Medium

| Attribute | Example | Guidance |
| --- | --- | --- | 
| EMPLOYER | ABC Company | This is the name of the organization the person is employed by. |

Rules
- When the source provides explicit employment relationships between person and organization records, prefer REL_POINTER/REL_ANCHOR to model the relationship; EMPLOYER can still be included for resolution.

Example
```json
{
  "FEATURES": [
    { "EMPLOYER": "ABC Company" }
  ]
}
```

### Feature: GROUP_ASSOCIATION
Importance: Low-Medium

| Attribute | Example | Guidance |
| --- | --- | --- | 
| GROUP_ASSOCIATION_TYPE | OWNER_EXEC | Specific group/role within the organization; use precise categories (e.g., OWNER_EXEC, BOARD_MEMBER) to improve resolution. |
| GROUP_ASSOCIATION_ORG_NAME | Group name | Name of the associated organization; use the official or standardized name. |

Rules
- Provide GROUP_ASSOCIATION_TYPE to keep the group specific. Specific roles/groups (e.g., owners/executives of a company) are much smaller than the general population and therefore more discriminative.
- Example of discriminative power: the combination of a name with a small group (e.g., "George Washington" + "US President") is far rarer than the name alone.

Example
```json
{
  "FEATURES": [
    { "GROUP_ASSOCIATION_TYPE": "OWNER_EXEC", "GROUP_ASSOCIATION_ORG_NAME": "ABC Company" }
  ]
}
```

### Feature: GROUP_ASSN_ID
Importance: Low-Medium

| Attribute | Example | Guidance |
| --- | --- | --- | 
| GROUP_ASSN_ID_TYPE | COMPANY_ID | The type of group identifier an entity is associated with. |
| GROUP_ASSN_ID_NUMBER | 12345 | The identifier the entity is associated with. If the group has a registered identifier, place it here. |

Rules
- Use when the group/organization has a registered identifier (e.g., DUNS). Include both type and number when available.

Example
```json
{
  "FEATURES": [
    { "GROUP_ASSN_ID_TYPE": "COMPANY_ID", "GROUP_ASSN_ID_NUMBER": "12345" }
  ]
}
```

## Disclosed relationships

Some data sources keep track of known relationships between entities. Look for a table within the source system that defines such relationships and include them here.

A relationship can either be unidirectional, where one record points to the other, or bidirectional, where they each point to the other.

![Screenshot](images/ges-image3-relationship.png)

This is accomplished by giving a REL_ANCHOR feature to any record that can be related to and a REL_POINTER feature to each record that relates to it.   A record should only ever have one REL_ANCHOR feature, but may have zero or more REL_POINTER features.  For instance, several people may be related to a company so the company only needs one REL_ANCHOR feature they all point to.  But a single person may be related to more than one company so that person can have several REL_POINTER features. 

### Feature: REL_ANCHOR
Category: Relationship

| Attribute | Example | Guidance |
| --- | --- | --- | 
| REL_ANCHOR_DOMAIN | CUSTOMERS | This code helps keep the REL_ANCHOR_KEY unique.  This is a code (without dashes) for the data source or source field that is contributing the relationship.  
| REL_ANCHOR_KEY | 1001 | This key should be a unique value for the record within the REL_ANCHOR_DOMAIN.  You can just use the current record's RECORD_ID here.|

Rules
- Include at most one REL_ANCHOR per record, only when the entity can be related to by others.
- REL_ANCHOR identifies the target entity for relationships using `REL_ANCHOR_DOMAIN` and `REL_ANCHOR_KEY`.
- Do not mix REL_ANCHOR and REL_POINTER attributes in the same feature object (separate objects in FEATURES are fine).
- Use a domain code without dashes to avoid confusion in downstream match key parsing.

Examples
```json
{
  "FEATURES": [
    { "REL_ANCHOR_DOMAIN": "CUSTOMERS", "REL_ANCHOR_KEY": "ACME-1001" }
  ]
}
```

- ❌ Incorrect (multiple REL_ANCHOR objects — only one allowed per record)
```json
{
  "FEATURES": [
    { "REL_ANCHOR_DOMAIN": "CUSTOMERS", "REL_ANCHOR_KEY": "ACME-1001" },
    { "REL_ANCHOR_DOMAIN": "CUSTOMERS", "REL_ANCHOR_KEY": "ACME-2002" }
  ]
}
```

### Feature: REL_POINTER
Category: Relationship

| Attribute | Example | Guidance |
| --- | --- | --- | 
| REL_POINTER_DOMAIN | CUSTOMERS | See REL_ANCHOR_DOMAIN above. |
| REL_POINTER_KEY | 1001 | See REL_ANCHOR_KEY above.
| REL_POINTER_ROLE | SPOUSE | This is the role the pointer record has to the anchor record.  Such as OFFICER_OF, SON_OF, SUBSIDIARY_OF, etc.  It is best to standardize these role codes for display and filtering. |

Rules
- Place REL_POINTER on the source entity for each disclosed relationship to a target entity.
- Provide `REL_POINTER_DOMAIN` and `REL_POINTER_KEY` to point to the target’s REL_ANCHOR; include a clear `REL_POINTER_ROLE`.
- Represent multiple relationships by adding multiple REL_POINTER objects in FEATURES (one per relationship).
- Do not mix REL_POINTER and REL_ANCHOR attributes in the same feature object.

Examples
```json
{
  "FEATURES": [
    { "REL_POINTER_DOMAIN": "CUSTOMERS", "REL_POINTER_KEY": "ACME-1001", "REL_POINTER_ROLE": "EMPLOYED_BY" }
  ]
}
```

- ❌ Incorrect (mixing REL_ANCHOR and REL_POINTER attributes in the same object)
```json
{
  "FEATURES": [
    { "REL_POINTER_DOMAIN": "CUSTOMERS", "REL_POINTER_KEY": "ACME-1001", "REL_POINTER_ROLE": "EMPLOYED_BY", "REL_ANCHOR_DOMAIN": "CUSTOMERS", "REL_ANCHOR_KEY": "ACME-1001" }
  ]
}
```

### Feature: TRUSTED_ID
Category: Control

A Trusted ID will absolutely force records together when they have the same key in the same domain even if all their other features are different.  Conversely, two records with a different key in the same domain will be forced apart even if all their other features are the same.

This feature can be used by data stewards to manually force records together or apart.  It can also be used for an source system identifier that is so trusted you want it to never be overruled by Senzing.  

| Attribute | Example | Guidance |
| --- | --- | --- |
| TRUSTED_ID_DOMAIN | STEWARD | Short code for the identifier domain/system (e.g., STEWARD, MASTER_ID). |
| TRUSTED_ID_KEY | 1234-12345 | The identifier value shared by records that must resolve together. |

Example
```json
{
  "FEATURES": [
    { "TRUSTED_ID_DOMAIN": "STEWARD", "TRUSTED_ID_KEY": "1234-12345" }
  ]
}
```

# Additional configuration

Senzing comes pre-configured with all the features, attributes, and settings you will likely need to begin resolving persons and organizations immediately. The only configuration that really needs to be added is what you named your data sources.

Email support@senzing.com for assistance with custom features.

## How to add a data source

In your Senzing project's bin directory is an application called sz_configtool. Adding a new data source is as simple as registering the code you want to use for it. 

```console
sz_configtool.py  

Welcome to the Senzing configuration tool! Type help or ? to list commands

(szcfg) addDataSource CUSTOMERS

Data source successfully added!

(szcfg) save

Are you certain you wish to proceed and save changes? (y/n) y

Configuration changes saved!
```
