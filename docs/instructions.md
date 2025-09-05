You are mapping a source system into the Senzing Entity Specification.

## What to analyze
- The source schema (and any sample rows if provided).

## What to produce (before code)
A) **Mapping Table** (with alternatives & rationale)  
B) **Proposed Relationships** (including any new entities created from inline PII)  
C) **Sample Senzing JSON** that follows the spec exactly

---

## Rules (follow the Senzing spec strictly)
1. Put **DATA_SOURCE** and **RECORD_ID** at the **root**; DATA_SOURCE is required.  
2. Use **one** sublist named **FEATURES** for all features.  
3. Put all **payload attributes at the root level** (do **not** create a `PAYLOAD` object).  
4. Do **not** emit arrays of feature values—if multiple values exist, create **multiple feature objects**.  
5. Use only defined feature/attribute names from the spec (e.g., `RECORD_TYPE`, `NAME_FIRST`, `NAME_LAST`, `NAME_FULL`, `DATE_OF_BIRTH`, `ADDR_*`, `PHONE_TYPE`, `PHONE_NUMBER`, `EMAIL_ADDRESS`, government IDs, etc.).  
6. Relationships use **REL_ANCHOR_DOMAIN** + **REL_ANCHOR_KEY** (current record) and **REL_POINTER_DOMAIN** + **REL_POINTER_KEY** + **REL_POINTER_ROLE** (related record).  
7. **Usage types** (e.g., `NAME_TYPE`, `ADDR_TYPE`, `PHONE_TYPE`) only when justified by the source.  
8. Prefer parsed names when available; else `NAME_FULL`.  
9. Do **not** invent attributes not in the spec.

---

## Decision heuristics (and alternatives to surface)
- If a field strengthens ER/linkage (names, `DATE_OF_BIRTH`, IDs, emails, phones, addresses, org names, registration numbers) → **FEATURE**.  
- If a field is a foreign key/reference to another real-world entity → **REL_* ** with a clear **REL_POINTER_ROLE**.  
- If a field is business metadata not used for ER (status codes, internal timestamps) → **payload (root attribute)**; also present **FEATURE vs payload** alternatives (with pros/cons) when borderline.  
- For **free text**, scan for inline PII (name/email/phone/ID/address). If present:
  - Propose **extraction** into a **new entity** (appropriate features),
  - And add a **relationship** from the main entity to that extracted entity (set `REL_POINTER_ROLE`).  

---

## Output format (mapping phase)

### A) Mapping Table
| Source Field | Primary Senzing Target | Alternatives (if any) | Transformations | Rationale | Confidence (0–1) |
|---|---|---|---|---|---|

- Alternatives must explicitly consider: **FEATURE vs payload**, **REL_* candidate**, and **inline-PII → new entity + relation** where relevant.
- Transformations: parsing/splitting, date normalization (`YYYY-MM-DD` for `DATE_OF_BIRTH`), address decomposition, E.164 phones, regex for inline-PII.

### B) Proposed Relationships
- **Main Entity → Related Entity**
  - `REL_ANCHOR_DOMAIN`: <this record’s domain (e.g., DATA_SOURCE)>
  - `REL_ANCHOR_KEY`: <this record’s RECORD_ID>
  - `REL_POINTER_DOMAIN`: <related record’s domain>
  - `REL_POINTER_KEY`: <related record’s key>
  - `REL_POINTER_ROLE`: <e.g., "SON_OF", "MANAGER", "OFFICER", "CONTACT">
  - **Linking fields**: <source fields establishing the link>
  - **Created from inline PII?** yes/no (if yes, specify extraction rule)

### C) Sample Senzing JSON (spec-compliant)
- Include `DATA_SOURCE`, `RECORD_ID`, one `FEATURES` array, and any root-level payload attributes.
- Show at least one relationship if applicable.

---

## ✅ After the user approves the mapping: Generate simple Python code

Produce a **single-file, dependency-light** Python script that:
- **Inputs**: CSV rows (or dicts) from the source.  
- **Outputs**: one **JSON object per row** that matches the approved mapping and the Senzing spec:
  - `DATA_SOURCE` (from config/constant), `RECORD_ID` (from mapped key), a single `FEATURES` list, root-level payload attributes.
  - Multiple values → multiple feature objects (no arrays).
  - Relationship objects using `REL_ANCHOR_DOMAIN/KEY` and `REL_POINTER_DOMAIN/KEY/ROLE`.
- **Implements transforms** agreed in the mapping:
  - Name parsing (if needed), date normalization to `YYYY-MM-DD`, phone normalization (basic digits-only + optional country code), address decomposition, trimming/lowercasing for emails, etc.
  - Optional **regex extraction** for inline PII (e.g., emails, phones) from free text, creating **new entities** and **relationship** records as specified.
- **Structure**:
  - `CONFIG`: constants (e.g., `DATA_SOURCE`, column names, simple regexes).
  - `map_record(row: dict) -> dict`: returns a spec-valid Senzing JSON object for the main entity.
  - `extract_inline_entities(row: dict) -> list[dict]`: returns additional Senzing JSON objects created from inline PII (if any).
  - `derive_relationships(main: dict, extracted: list[dict], row: dict) -> list[dict]`: creates relationship feature objects (with required `REL_*` fields).
  - `main()` that reads `input.csv` and writes `output.jsonl` (one JSON per line).
- **Safety & clarity**:
  - Use only Python stdlib (`csv`, `json`, `re`, `argparse`, `pathlib`, `typing`, `datetime`).
  - Type hints and docstrings.
  - No external services, no secrets.
  - Include 1–2 **doctest-style examples** (or a tiny `if __name__ == "__main__":` demo) to illustrate the transformation.

**Code Style Requirements**
- Prefer pure functions; avoid side effects except I/O in `main()`.
- Keep field names exactly as in the approved mapping and spec.
- Emit **only** spec-defined attributes in `FEATURES` and the required relationship fields.

---

## Inline-PII extraction guidance (for the code)
- Provide minimal, maintainable regex examples:
  - Email: `r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"`
  - Phone (US-leaning): `r"\b(?:\+1[-.\s]?)?$begin:math:text$?\\d{3}$end:math:text$?[-.\s]?\d{3}[-.\s]?\d{4}\b"`
- When extracting a person from free text:
  - Create a new entity with `RECORD_TYPE` (if applicable) and relevant features (`NAME_FULL` if only full name is available, `PHONE_NUMBER`, `EMAIL_ADDRESS`).
  - Create a relationship from the main entity to this new entity; set an appropriate `REL_POINTER_ROLE` (e.g., `"CONTACT"`).
- Document each regex and transformation in comments.

---

## Sanity checks (before finishing)
- Exactly one `FEATURES` list; **no** `PAYLOAD` wrapper.
- Multiple values → multiple feature objects, not arrays.
- Relationships include all required `REL_*` fields.
- Attribute names match the spec exactly.
- Python code mirrors the approved mapping, uses stdlib only, and writes valid JSONL.

---

## Deliverables Recap
1) Mapping Table (with alternatives & confidence)  
2) Proposed Relationships (incl. extracted entities)  
3) Sample Senzing JSON (spec-compliant)  
4) **After approval**: Simple Python script implementing the mapping + extraction + relationships, writing JSONL