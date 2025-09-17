# Bootstrap Instructions for Mapping Sessions (v2.14, no linter)

Use my **system prompt** from this URL:

- **System Prompt (rules/workflow):**  
  https://raw.githubusercontent.com/jbutcher21/aiclass/main/docs/systemprompt_v2_14.md

---

## Instructions

1. **Load the system prompt** and treat it as the governing rules for this session.  
   - Paste the contents of `systemprompt_v2_14.md` into a new ChatGPT conversation.  
   - This locks in the workflow and guardrails.

2. **Provide your source schema and/or sample records.**  
   - Either is acceptable.  
   - If both are available, provide both.

3. **Follow the workflow (hard stops at each stage):**

   - **Output 1: Source Summary**  
     - High-level summary only.  
     - No mapping yet.  
     - Ends by asking if you’re ready to begin mapping.  

   - **Output 2: Interactive Draft Mapping** (entity-by-entity, feature-by-feature)  
     - Confirm `DATA_SOURCE` + `RECORD_ID` with a tiny JSON snippet (empty `FEATURES`).  
     - For each feature family:  
       - Show a **mini mapping table**.  
       - Show a **JSON snippet** with just that feature.  
       - Confirm or adjust (hard stop).  
     - Propose **Payload attributes**, confirm.  
     - Show **Ignored/unmapped fields**, confirm.  
     - Every source field must be dispositioned.  

   - **Output 3: Finalized Mapping + Sample JSONs**  
     - Show the **full mapping table** (strict 4-column format).  
     - Show one **complete sample JSON** per entity.  
     - Confirm or adjust (hard stop).  

   - **Output 4: Python Mapping Script**  
     - Generate source-to-Senzing transformation code.  
     - You test it on actual data.  
     - Iterate until approved (hard stop).  

   - **Output 5: Wrap-Up**  
     - Congratulate you on completing the mapping.  
     - End with: *“I’m ready for the next source to map whenever you are!”*

---

## Standard Mapping Table Format

All mapping tables (mini and final) must use **exactly these columns**:

| Source field | Feature | Target Attribute | Transformations |
|--------------|---------|------------------|-----------------|

- **Feature column values:**  
  - `Required` → only for `DATA_SOURCE`, `RECORD_ID`  
  - `Payload` → valid root/payload attribute (per spec)  
  - `Ignored` → not mapped  
  - Or the actual **feature family name** (e.g., `NAME`, `ADDRESS`, `PHONE`, `PASSPORT_NUMBER`, `SSN_NUMBER`, etc.)

---

