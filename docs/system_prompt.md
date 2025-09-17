# Bootstrap Instructions for Mapping Sessions (v2.23)

Use my system prompt and the Senzing spec from these URLs:

- **System Prompt (rules/workflow):**  
  https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/mapping_instructions.md  

- **Senzing Entity Specification (single source of truth):**  
  https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/senzing_entity_specification.md  

---

## How to Use

1. **Load the system prompt** and treat it as the governing rules.  
   - Must always follow the prompt + spec.  
   - No alternate docs are allowed.

2. **Step 0 → Provide schema or records.**  
   - Upload schema (JSON/YAML/CSV) or sample records (or both).  

3. **Step 1 → Source Summary (spec’s *Source Schema Types*).**  
   - Assistant applies the spec’s checklist: flat / multi-table / nested / arrays / mixed types / relationships / embedded entities.  
   - Lists all entities + relationships found with keys, join paths, cardinalities, evidence.  
   - Ends with a hard stop: “Ready to begin mapping?”  

4. **Step 2 → Interactive Draft Mapping (entity by entity).**  
   - Confirm `DATA_SOURCE` + `RECORD_ID` first (JSON skeleton).  
   - Then feature-by-feature with **mini mapping tables + JSON snippets**.  
   - **Per-feature hard stops** (`approve` / `adjust:`).  
   - Each snippet must:  
     1) include a **Spec Anchor** line citing the spec example it followed,  
     2) pass the **Spec Vocabulary Whitelist** (only allowed keys), and  
     3) satisfy the **Feature Homogeneity Rule** (one family per object).  
   - **Coverage Ledger** tracks every source field. Coverage Meter shown at each step.  
   - **Zero-Omission Gate**: cannot proceed until all fields are dispositioned.

5. **Step 3 → Finalized Mapping + Sample JSONs.**  
   - Full mapping table for all entities.  
   - Pretty-printed JSON examples (all spec-true).  
   - **Zero-Omission Gate**: must cover 100% of fields before proceeding.  
   - Snippets validated against the spec’s **Recommended JSON Structure** (payload at root, FEATURES array, RECORD_TYPE inside features).  
   - Enforces whitelist + homogeneity.  
   - Hard stop until approved.

6. **Step 4 → Python Mapping Script.**  
   - Assistant generates Python code implementing the mapping.  
   - You test on actual data, assistant iterates changes until approved.  
   - Hard stop until approved.

7. **Step 5 → Wrap-Up.**  
   - Assistant confirms completion, offers to start next source.

---

## Key Enforcement
- **Source Field Inventory**: assistant must echo the exact source field list; no fabricated fields.  
- **Coverage Ledger + Zero-Omission Gates**: every field dispositioned exactly once; cannot skip.  
- **Identifier Compliance**: only spec-listed identifiers (`SSN_NUMBER`, `PASSPORT_NUMBER`, etc.); no generic IDENTIFIER.  
- **Spec Vocabulary Whitelist**: only attribute keys literally present in spec examples.  
- **Spec Anchors**: each snippet cites the example it followed.  
- **Feature Homogeneity Rule**: one family per FEATURES object (`RECORD_TYPE` separate).  
- **Recommended JSON Structure**: enforced at every snippet/sample (payload at root, FEATURES array, RECORD_TYPE inside).  
- **No TRUSTED_ID** unless you explicitly ask.  
- **Per-feature approval gates** at every step.
