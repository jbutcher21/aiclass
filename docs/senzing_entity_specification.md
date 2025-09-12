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

| Feature | Description | Importance | Guidance (Usage Types) |
| --- | --- | --- | --- |
| RECORD_TYPE | (e.g., PERSON, ORGANIZATION) | High | Include when known to prevent cross‑type resolution; omit if unknown. Use standardized kinds (PERSON, ORGANIZATION). Often used to determine icon/shape in graphs. |
| NAME (person) | Personal names | High | Usage: NAME_TYPE PRIMARY, AKA. Prefer parsed person names when available. |
| NAME (organization) | Organization legal or trade name | High | Usage: NAME_TYPE PRIMARY, DBA. |
| DATE_OF_BIRTH | Person date of birth | High | Full date preferred, but partial date accepted. |
| DATE_OF_DEATH | Person date of death | Medium | When applicable. |
| GENDER | Person gender | Medium | — |
| NATIONALITY | Person nationality | Low–Medium | — |
| CITIZENSHIP | Person citizenship | Low–Medium | — |
| PLACE_OF_BIRTH | Person place of birth | Low–Medium | — |
| REGISTRATION_DATE | Organization registration/incorporation date | Medium | Full date preferred, but partial date accepted.|
| REGISTRATION_COUNTRY | Organization registration country | Medium | — |
| ADDRESS | Postal/physical address | High | Usage: ADDR_TYPE HOME, MAILING, BUSINESS. Prefer parsed; assign BUSINESS to at least one org address when known. |
| PHONE | Telephone number | Medium | Usage: PHONE_TYPE MOBILE, HOME, WORK. MOBILE has special weight. |
| EMAIL | Email address | Medium | — |
| WEBSITE (org) | Organization website/domain | Low | Typically organizations; omit for people unless clearly a personal domain. |
| Social handles | Social/media handles | Medium | Features include: LINKEDIN, FACEBOOK, TWITTER, SKYPE, ZOOMROOM, INSTAGRAM, WHATSAPP, SIGNAL, TELEGRAM, TANGO, VIBER, WECHAT. |
| PASSPORT | Passport identifier | High | Include issuing country. |
| DRLIC | Driver’s license | High | Include issuing state/province/country. |
| SSN | US Social Security Number | High | Partial accepted. |
| TAX_ID | Tax identifier | High (org) / Medium (person) | Usage: TAX_ID_TYPE (e.g., EIN, VAT). Include issuing country. |
| NATIONAL_ID | National identifier | Medium | Usage: NATIONAL_ID_TYPE. Include issuing country. |
| OTHER_ID | Other/uncategorized identifier (catch‑all) | Low | Usage: OTHER_ID_TYPE. Use sparingly; prefer specific features to avoid cross‑type false positives. |
| DUNS_NUMBER | Company identifier | High | — |
| LEI_NUMBER | Legal Entity Identifier | High (financial) | — |
| NPI_NUMBER | US healthcare provider ID | Medium–High (healthcare) | — |
| ACCOUNT | Account or card number | Low | Usage: ACCOUNT_DOMAIN (e.g., VISA). |
| EMPLOYER | Person’s employer organization name | Low–Medium | Group association; helps resolve, not a relationship by itself. |
| GROUP_ASSOCIATION | Membership/affiliation | Low–Medium | Usage: GROUP_ASSOCIATION_TYPE; include org name. |
| GROUP_ASSN_ID | Group identifier | Low–Medium | Usage: GROUP_ASSN_ID_TYPE/NUMBER. |
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
- If you do decide to include them, keep them minimal and only include what helps a human understand matches.
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
  - RECORD_ID: strongly desired (string), unique within DATA_SOURCE.
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
- Keys: Find a unique key for each core entity (per DATA_SOURCE). If none exists, derive a deterministic RECORD_ID from identifying attributes.
- Children: Identify child lists/tables for names, addresses, phones, identifiers, emails, websites, social handles; join/aggregate them as separate FEATURES.
- Relationships: Locate link/join tables or explicit edge lists with roles/verbs; produce REL_POINTER(s) from the source entity to the target’s REL_ANCHOR with a clear REL_POINTER_ROLE.
- Arrays/sub‑documents: In JSON/XML, locate nested arrays (names, addresses, phones, identifiers) and flatten into FEATURES.
- Code lookups: Resolve type and country codes via code tables (e.g., address types, identifier issuing countries).
- Join strategy: Emit one JSON record per entity, containing all FEATURES and REL_* features, per the Recommended JSON Structure.

Transaction‑like inputs
- For records that embed loosely controlled external parties (e.g., wires with free‑form sender/receiver), extract party identifiers and features, deduplicate, and create deterministic RECORD_IDs. Stamp the derived IDs on the transaction rows so downstream analysis can join back to resolved entities.

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
| RECORD_ID | Strongly Desired | 1001 | Must be unique within DATA_SOURCE; used to add/replace records. If the source lacks a primary key, construct a deterministic ID (e.g., hash of normalized identifying attributes). If omitted, Senzing generates a hash of features, making updates impractical. Do not duplicate RECORD_ID as a feature — retrieval uses DATA_SOURCE + RECORD_ID. |

Example
```json
{
  "DATA_SOURCE": "CUSTOMERS",
  "RECORD_ID": "1001",
}
```

### FEATURE: RECORD_TYPE
Importance: High (see What Features to Map)

| Attribute | Required | Example | Guidance |
| --- | --- |  --- | --- |
| RECORD_TYPE | Strongly Desired | PERSON | Prevents records of different types from resolving. Include when known to prevent cross‑type resolution; leave blank if unknown. Use standardized kinds (PERSON, ORGANIZATION). Often used to pick the icon/shape in graphs. |

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
Importance: High (see What Features to Map)

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
Importance: High (see What Features to Map)

| Attribute       | Example                                   | Guidance |
| ---             | ---                                       | --- |
| ADDR_TYPE       | HOME                                       | Optional; include when provided by the source. Common values: HOME, MAILING (persons); BUSINESS (organizations). |
| ADDR_LINE1      | 111 First St                               | First address line (street, number). |
| ADDR_LINE2      | Suite 101                                  | Second address line (apt/suite). |
| ADDR_LINE3      |                                            | Third address line (optional). |
| ADDR_LINE4      |                                            | Fourth address line (optional). |
| ADDR_LINE5      |                                            | Fifth address line (optional). |
| ADDR_LINE6      |                                            | Sixth address line (optional). |
| ADDR_CITY       | Las Vegas                                  | City/locality. |
| ADDR_STATE      | NV                                         | State/province/region code. |
| ADDR_POSTAL_CODE| 89111                                      | Postal/ZIP code. |
| ADDR_COUNTRY    | US                                         | Country code. |
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
Importance: Medium (see What Features to Map)

| Attribute    | Example       | Guidance |
| ---          | ---           | --- |
| PHONE_TYPE   | MOBILE        | Optional; include when provided by the source. Common values: MOBILE, HOME, WORK, FAX. MOBILE carries extra weight. |
| PHONE_NUMBER | 702-555-1212  | Telephone number. |

Rules
- One PHONE object per instance; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).
- Include PHONE_TYPE only when the source provides it (MOBILE carries extra weight).
- One PHONE object per number; represent multiple numbers as multiple PHONE objects.
- Do not put a list of numbers inside a single PHONE object.
- When a source uses clear prefixes (e.g., HOME_PHONE), you may derive PHONE_TYPE from the prefix.

Examples
- ✅ Phone without type
```json
{
  "FEATURES": [
    { "PHONE_NUMBER": "702-555-3434" }
  ]
}
```
- ✅ Phone with type
```json
{
  "FEATURES": [
    { "PHONE_TYPE": "MOBILE", "PHONE_NUMBER": "702-555-1212" }
  ]
}
```
- ❌ Incorrect (multiple instances cannot be in list)
```json
{
  "FEATURES": [
    { "PHONE_NUMBER": ["702-555-3434" , "702-555-1212"] }
  ]
}
```
- ✅ Multiple instances are objects in the FEATURES list
```json
{
  "FEATURES": [
    { "PHONE_NUMBER": "702-555-3434" },
    { "PHONE_NUMBER": "702-555-1212" }
  ]
}
```

## Physical and other attributes

### Feature: GENDER
Importance: Medium (see What Features to Map)

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
Importance: High (see What Features to Map)

| Attribute       | Example     | Guidance |
| ---             | ---         | --- |
| DATE_OF_BIRTH   | 1980-05-14  | Complete dates preferred; partial dates accepted when only partial is available (e.g., YYYY‑MM or MM‑DD). |

Rule
- One DATE_OF_BIRTH object per instance; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).

Examples
```json
{
  "FEATURES": [
    { "DATE_OF_BIRTH": "1980-05-14" }
  ]
}
```

### Feature: DOD (Date of Death)
Importance: Medium (see What Features to Map)

| Attribute       | Example     | Guidance |
| ---             | ---         | --- |
| DATE_OF_DEATH   | 2010-05-14  | Complete dates preferred; partial dates accepted when only partial is available (e.g., YYYY‑MM or MM‑DD). |

Rule
- One DATE_OF_DEATH object per instance; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).
Example
```json
{
  "FEATURES": [
    { "DATE_OF_DEATH": "2010-05-14" }
  ]
}
```

### Feature: NATIONALITY
Importance: Low–Medium (see What Features to Map)

| Attribute   | Example | Guidance |
| ---         | ---     | --- |
| NATIONALITY | US      | Country of nationality (code or label) as provided by the source. |

Rule
- One NATIONALITY object per instance; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).
Example
```json
{
  "FEATURES": [
    { "NATIONALITY": "US" }
  ]
}
```

### Feature: CITIZENSHIP
Importance: Low–Medium (see What Features to Map)

| Attribute   | Example | Guidance |
| ---         | ---     | --- |
| CITIZENSHIP | US      | Country of citizenship (code or label) as provided by the source. |

Rule
- One CITIZENSHIP object per instance; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).
Example
```json
{
  "FEATURES": [
    { "CITIZENSHIP": "US" }
  ]
}
```

### Feature: POB (Place of Birth)
Importance: Low–Medium (see What Features to Map)

| Attribute        | Example   | Guidance |
| ---              | ---       | --- |
| PLACE_OF_BIRTH   | Chicago   | Place of birth; may be a city/region or a country code/label as provided by the source. |

Rule
- One PLACE_OF_BIRTH object per instance; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).
Example
```json
{
  "FEATURES": [
    { "PLACE_OF_BIRTH": "Chicago, IL" }
  ]
}
```

### Feature: REGISTRATION_DATE (Organizations)
Importance: Medium (see What Features to Map)

| Attribute          | Example     | Guidance |
| ---                | ---         | --- |
| REGISTRATION_DATE  | 2010-05-14  | Organization registration/incorporation date. Complete dates preferred; partial dates accepted when only partial is available (e.g., YYYY‑MM or MM‑DD). |

Rule
- One REGISTRATION_DATE object per instance; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).
Example
```json
{
  "FEATURES": [
    { "REGISTRATION_DATE": "2010-05-14" }
  ]
}
```

### Feature: REGISTRATION_COUNTRY (Organizations)
Importance: Medium (see What Features to Map)

| Attribute             | Example | Guidance |
| ---                   | ---     | --- |
| REGISTRATION_COUNTRY  | US      | Country of registration (code or label) as provided by the source. |

Rule
- One REGISTRATION_COUNTRY object per instance; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).
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
Importance: High (see What Features to Map)

| Attribute          | Example     | Guidance |
| ---                | ---         | --- |
| PASSPORT_NUMBER    | 123456789   | Passport number. |
| PASSPORT_COUNTRY   | US          | Issuing country. Include when available. |

Rules
- One PASSPORT object per instance; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).

Example
```json
{
  "FEATURES": [
    { "PASSPORT_NUMBER": "123456789", "PASSPORT_COUNTRY": "US" }
  ]
}
```

### Feature: DRLIC (Driver’s License)
Importance: High (see What Features to Map)

| Attribute               | Example | Guidance |
| ---                     | ---     | --- |
| DRIVERS_LICENSE_NUMBER  | 112233  | Driver’s license number. |
| DRIVERS_LICENSE_STATE   | NV      | Issuing state/province/country. Include when available. |

Rules
- One DRLIC object per instance; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).

Example
```json
{
  "FEATURES": [
    { "DRIVERS_LICENSE_NUMBER": "112233", "DRIVERS_LICENSE_STATE": "NV" }
  ]
}
```

### Feature: SSN (US Social Security Number)
Importance: High (see What Features to Map)

| Attribute   | Example      | Guidance |
| ---         | ---          | --- |
| SSN_NUMBER  | 123-12-1234  | US Social Security Number; partial accepted. |

Rules
- One SSN object per instance; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).

Example
```json
{
  "FEATURES": [
    { "SSN_NUMBER": "123-12-1234" }
  ]
}
```

### Feature: NATIONAL_ID
Importance: Medium (see What Features to Map)

| Attribute            | Example   | Guidance |
| ---                  | ---       | --- |
| NATIONAL_ID_TYPE     | CEDULA    | Type label from source (standardize when possible). If you mapped the issuing country and did not standardize the type, it’s okay to leave this blank. |
| NATIONAL_ID_NUMBER   | 123121234 | National identifier value. |
| NATIONAL_ID_COUNTRY  | FR        | Issuing country. |

Rules
- Use NATIONAL_ID for country‑issued identity numbers (often one per person/org). Do not map SSN, PASSPORT, or DRLIC here.

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
Importance: High (org) / Medium (person) (see What Features to Map)

| Attribute        | Example     | Guidance |
| ---              | ---         | --- |
| TAX_ID_TYPE      | EIN         | Type label from source (standardize when possible). If you mapped the issuing country and did not standardize the type, it’s okay to leave this blank. |
| TAX_ID_NUMBER    | 12-3456789  | Tax identifier value. |
| TAX_ID_COUNTRY   | US          | Issuing country. |

Rules
- Use TAX_ID for tax‑purpose identifiers (orgs or persons). Organizations may legitimately have multiple TAX_IDs.
- Prefer specific features (e.g., EIN via TAX_ID, INN, VAT) where identifiable.

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
Importance: Low (see What Features to Map)

| Attribute         | Example  | Guidance |
| ---               | ---      | --- |
| OTHER_ID_TYPE     | ISIN     | Required for classification; choose meaningful values. |
| OTHER_ID_NUMBER   | 123121234| Identifier value. |
| OTHER_ID_COUNTRY  | MX       | Issuer country when known (optional). |

Rules
- Use OTHER_ID sparingly as a catch‑all when you cannot confidently classify to a specific or generic feature.
- Prefer adding a specific feature for frequently used non‑country identifiers so matching behavior can be tuned.

Example
```json
{
  "FEATURES": [
    { "OTHER_ID_TYPE": "STUDENT_ID", "OTHER_ID_NUMBER": "S-998877" }
  ]
}
```

### Feature: ACCOUNT
Importance: Low (see What Features to Map)

| Attribute        | Example                | Guidance |
| ---              | ---                    | --- |
| ACCOUNT_NUMBER   | 1234-1234-1234-1234    | Account identifier (e.g., bank, card). |
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
Importance: High (see What Features to Map)

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
Importance: Medium–High (healthcare) (see What Features to Map)

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
Importance: High (financial) (see What Features to Map)

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
Importance: Medium (see What Features to Map)

| Attribute      | Example                | Guidance |
| ---            | ---                    | --- |
| EMAIL_ADDRESS  | someone@somewhere.com  | Email address. |

Rules
- One feature family per object: an EMAIL object should contain only EMAIL_* attributes.
- One EMAIL object per address; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).

Example
```json
{
  "FEATURES": [
    { "EMAIL_ADDRESS": "alex@example.com" }
  ]
}
```

## Feature: WEBSITE
Importance: Low (see What Features to Map)

| Attribute        | Example          | Guidance |
| ---              | ---              | --- |
| WEBSITE_ADDRESS  | somecompany.com  | Website or domain; typically for organizations. |

Rules
- Use primarily for organizations; include for a person only when clearly a personal domain.
- One WEBSITE object per domain; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).

Example
```json
{
  "FEATURES": [
    { "WEBSITE_ADDRESS": "acmetire.com" }
  ]
}
```

## Features for Social Media Handles
Importance: Medium (see What Features to Map)

Social handle features use the feature name as the attribute name.

| Feature/Attribute | Example           | Guidance |
| ---               | ---               | --- |
| LINKEDIN          | company-or-user   | Unique id/handle in the given domain. |
| FACEBOOK          | company-or-user   | Unique id/handle in the given domain. |
| TWITTER           | @handle           | Unique id/handle in the given domain. |
| SKYPE             | handle            | Unique id/handle in the given domain. |
| ZOOMROOM          | room-id           | Unique id/handle in the given domain. |
| INSTAGRAM         | @handle           | Unique id/handle in the given domain. |
| WHATSAPP          | phone-or-handle   | Unique id/handle in the given domain. |
| SIGNAL            | phone-or-handle   | Unique id/handle in the given domain. |
| TELEGRAM          | @handle           | Unique id/handle in the given domain. |
| TANGO             | handle            | Unique id/handle in the given domain. |
| VIBER             | phone-or-handle   | Unique id/handle in the given domain. |
| WECHAT            | handle            | Unique id/handle in the given domain. |

Rule
- One handle per object; do not supply lists or nested objects (see [Scalar vs Non-scalar](#scalar-vs-non-scalar-good-vs-bad)).

Example
```json
{
  "FEATURES": [
    { "LINKEDIN": "acme-tire-inc" }
  ]
}
```


## Group Associations

Group associations capture memberships or affiliations (e.g., employer, club) that can improve entity resolution across sources.  They are not the same as disclosed relationships. Group associations help resolve entities; disclosed relationships relate entities.

Warning: Group associations are subject to generic thresholds to reduce false positives and maintain performance. They will not resolve all employees of a large organization across sources; they are most effective with smaller cohorts (e.g., executives, owners, specific teams).

### Feature: EMPLOYER
Importance: Low–Medium (see What Features to Map)

| Attribute | Example | Notes |
| --- | --- | --- | 
| EMPLOYER | ABC Company | This is the name of the organization the person is employed by. |

Rules
- Use EMPLOYER to help resolve people who share an employer across sources; it does not create a disclosed relationship by itself.
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
Importance: Low–Medium (see What Features to Map)

| Attribute | Example | Notes |
| --- | --- | --- | 
| GROUP_ASSOCIATION_TYPE | MEMBER | This is the type of group an entity belongs to. |
| GROUP_ASSOCIATION_ORG_NAME | Group name | This is the name of the organization an entity belongs to. |

Rules
- Use GROUP_ASSOCIATION to capture memberships/affiliations that aid resolution; it does not create a disclosed relationship by itself.
- Include GROUP_ASSOCIATION_TYPE only when the source clearly indicates it (e.g., MEMBER, OFFICER, OWNER).

Example
```json
{
  "FEATURES": [
    { "GROUP_ASSOCIATION_TYPE": "MEMBER", "GROUP_ASSOCIATION_ORG_NAME": "Local Trade Group" }
  ]
}
```

### Feature: GROUP_ASSN_ID
Importance: Low–Medium (see What Features to Map)

| Attribute | Example | Notes |
| --- | --- | --- | 
| GROUP_ASSN_ID_TYPE | DUNS | When the group a person is associated with has a registered identifier, place the type of identifier here. |
| GROUP_ASSN_ID_NUMBER | 12345 | When the group a person is associated with has a registered identifier, place the identifier here. |

Rules
- Use when the group/organization has a registered identifier (e.g., DUNS). Include both type and number when available.

Example
```json
{
  "FEATURES": [
    { "GROUP_ASSN_ID_TYPE": "DUNS", "GROUP_ASSN_ID_NUMBER": "12345" }
  ]
}
```

## Disclosed relationships

Some data sources keep track of known relationships between entities. Look for a table within the source system that defines such relationships and include them here.

A relationship can either be unidirectional, where one record points to the other, or bidirectional, where they each point to the other.

![Screenshot](images/ges-image3-relationship.png)

This is accomplished by giving a REL_ANCHOR feature to any record that can be related to and a REL_POINTER feature to each record that relates to it.   A record should only ever have one REL_ANCHOR feature, but may have zero or more REL_POINTER features.  For instance, several people may be related to a company so the company only needs one REL_ANCHOR feature they all point to.  But a single person may be related to more than one company so that person can have several REL_POINTER features. 

### Feature: REL_ANCHOR
Category: Relationship (see What Features to Map)

| Attribute | Example | Notes |
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
Category: Relationship (see What Features to Map)

| Attribute | Example | Notes |
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
Category: Control (see What Features to Map)

A Trusted ID will absolutely force records together when they have the same key in the same domain even if all their other features are different.  Conversely, two records with a different key in the same domain will be forced apart even if all their other features are the same.

This feature can be used by data stewards to manually force records together or apart.  It can also be used for an source system identifier that is so trusted you want it to never be overruled by Senzing.  

| Attribute | Example | Notes |
| --- | --- | --- |
| TRUSTED_ID_DOMAIN | STEWARD | Short code for the identifier domain/system (e.g., STEWARD, MASTER_ID). |
| TRUSTED_ID_KEY | 1234-12345 | The identifier value shared by records that must resolve together. |

Rules
- One TRUSTED_ID object per curated identifier. If a record legitimately has multiple curated IDs, add multiple TRUSTED_ID objects (one per ID).

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
