# Generate Security Skill Files - Agent Execution Contract

> **SUBAGENT / DELEGATION POLICY -- READ THIS FIRST**
>
> Subagents (the Task tool / delegation) MAY be used to reduce the parent agent's context-window strain -- under STRICT rules. Delegation is NOT banned; using the wrong model is.
>
> 1. **Same model as the parent, ALWAYS.** Set the subagent `model` explicitly to the parent's model. If you cannot, run inline.
> 2. **NEVER Composer 2.** `composer-2.5-fast` is FORBIDDEN in ANY environment. In Cursor the DEFAULT subagent is Composer 2 -- override `model` or run inline.
> 3. **Parent owns completeness.** The parent re-derives every artifact from SDE + disk (tri-source) regardless of who did the work; every subagent emits `[PROGRESS]` and returns a verifiable result.
> 4. **Delegate only bounded, verifiable sub-tasks** (a CM-ID allow-list). NEVER let CMs be silently skipped.
> 5-9. Same-model is necessary but not sufficient; parent owns all ledger/status writes; snapshot-diff-rollback; allow-list only (no alternative/parallel files); never frame a worker as "batch N of M".
>
> **CURSOR IDE -- reasoning vs non-reasoning:** `.cursor/` present OR Cursor-only tools in the toolset -> `cursor_detected`. REASONING work (classification, library-match decisions, skill-file/content authoring) runs INLINE in the main agent. NON-REASONING actions (running the SDE Direct API Access batch script, mechanical IO/counting) MAY be delegated to a subagent even in Cursor (set `model` explicitly, NEVER `composer-2.5-fast`; the subagent returns only the compact summary and the parent re-derives coverage from disk).

This contract MUST be followed when executing `SKILL.md` in this directory.

## Skill Identity

**Name:** Generate Security Skill Files from SD Elements Countermeasures
**Purpose:** Countermeasure-loading + skill-file generation phase -- load CMs from a survey-complete handoff, let the user select a scope, classify, note PROCESS items, library-lookup, generate AGENTS.md + per-CM SKILL.md, write the apply-fixes handoff.
**Scope:** Handoff load, CM fetch, CM selection, classification, PROCESS notes, library lookup, domain grouping, AGENTS.md, per-CM skill files, verification, handoff. **Branches on `evidence_source` (codebase vs specs).**

**Consumes:** a `stage: survey-complete` handoff from `setup-security-plan-from-repo` (codebase) or `create-security-plan-from-specs` (specs).
**Produces:** a `stage: skill-files-generated` handoff for `@sde-skills/apply-security-fixes`.
**Does NOT include:** Configuring the survey (run a survey skill first) or applying fixes (use `@sde-skills/apply-security-fixes`).

---

## SELECTED SCOPE IS AUTHORITATIVE

The user-selected countermeasures (`.sde-security/selected-cms.json`) are the AUTHORITATIVE completeness scope. **TWO denominators** (Fix E — never the SDE project total, never "work so far"):
- `selected_file_tracked = |selected-cms.json ∩ non-PROCESS|` — per-CM coverage (classification, library lookup, `library-lookup/*.json` artifacts, CM-coverage check).
- `expected_skill_files = Σ per-CM max(matched_amendments, 1)` — total generated FILES and AGENTS.md ledger rows (a CM with N matched library technologies produces N files; a 0-match CM produces 1 template file).

---

## ⚠️ AI ANALYSIS REQUIRED -- NO SCRIPTED DECISIONS / NO GREP-TO-DECIDE

| Task | ❌ FORBIDDEN | ✅ REQUIRED |
|------|-------------|-------------|
| Classify a CM | keyword script DECIDES | AI confirms EVERY selected CM (a script may keyword-PROPOSE) |
| Find vulnerable code (codebase) | `grep "eval("` decides | READ file, UNDERSTAND context, document file:line |
| Connect CM to a feature (specs) | guess from titles | READ CM guidance + ANALYZE spec/placeholder context |
| Author SKILL.md content | a script authors | AI authors; `assemble_skill_files` copies library `amendment.text` byte-exact or assembles AI fields -- NEVER authors |

A CM with a matching library SKILL.md amendment MUST be file-tracked, never PROCESS.

---

## Completion Criteria

NOT complete until ALL are true:

- [ ] MCP connection verified
- [ ] `.sde-handoff.json` loaded + validated (stage in {survey-complete, skill-files-generated}; evidence_source/project_id/repository_path present); project_id re-validated via name-match
- [ ] All project countermeasures fetched (paginated)
- [ ] **Step 3.0 status pre-filter (task + verification) applied (defaults = no narrowing); CM selection made (all/specific/search) over the filtered pool and persisted to `.sde-security/selected-cms.json`; `=== CM SELECTION ===` emitted**
- [ ] Each SELECTED CM classified (CF/PR/IN; +ML_CODE/ML_DOC only when evidence_source==codebase); CLASSIFICATION = YES, anchored to selected_count
- [ ] Selected PROCESS CMs noted via addNote; PROCESS NOTES VERIFICATION = YES
- [ ] Library skill lookup run for EVERY selected file-tracked CM; LIBRARY SKILL LOOKUP VERIFICATION (API COVERAGE = YES); per-CM `.sde-security/library-lookup/{CM}.json` artifacts == selected_file_tracked
- [ ] Domains derived; (codebase) non-library CODE_FIX/ML_CODE mapped to file:line
- [ ] (codebase, Step 7.5, MCP-116) security branch created + pre-existing AI config archived; `git_enabled`/`security_branch`/`ai_backup_archive` originated for the handoff
- [ ] AGENTS.md created (specs) or merged with markers (codebase); LEDGER INIT + FORMAT CHECK = YES
- [ ] Skill files generated: **one per matched library technology** (`{CM_ID}-{tech-slug}`) plus one template file per 0-match CM (library byte-exact OR template; template format branches on evidence_source) -- excludes PROCESS; total == expected_skill_files
- [ ] CM-to-File CROSS-REFERENCE PASS; FILE GENERATION VERIFICATION = YES; LIBRARY CONTENT FIDELITY = YES
- [ ] `.sde-handoff.json` rewritten (stage=skill-files-generated) FIRST, then POST-EXECUTION AUDIT + verify-output.sh + FROM-SCRATCH FINAL VERIFICATION = ALL YES
- [ ] Tri-source invariant against SELECTED scope: expected_skill_files == skills/**/SKILL.md == AGENTS.md ledger rows; AND unique CM IDs on disk == selected_file_tracked (every selected file-tracked CM has >=1 file); AND library_lookup_audit length == selected_file_tracked
- [ ] Per-step PREFLIGHT emitted at each step boundary

---

## Mandatory Outputs

### Output Timing

| Step | What to Output |
|------|----------------|
| Step 0 | `[CHECKPOINT] MCP connection successful` |
| Step 1 | `[CONTRACT PINNED] ...` + `[CHECKPOINT] Handoff loaded: stage=..., evidence_source=..., project_id=...` |
| Step 2 | `[CHECKPOINT] Total project countermeasures: {N}` |
| Step 3.0 | `[CHECKPOINT] Status filter: task={..} verification={..} -> {P} of {N} CMs in pool` |
| Step 3 | `=== CM SELECTION ===` block + selected-cms.json written |
| Step 4 | `=== COUNTERMEASURE CLASSIFICATION ===` block |
| Step 5 | PROCESS NOTES BATCH PLAN + per-batch mini-gates + `=== PROCESS NOTES VERIFICATION ===` |
| Step 6 | `[CHECKPOINT] Pre-flight: I will query endpoint` + LIBRARY LOOKUP BATCH PLAN + mini-gates + `=== LIBRARY SKILL LOOKUP VERIFICATION ===` |
| Step 7.5 (codebase only) | `[CHECKPOINT] Git: ...` + `[CHECKPOINT] AI Config: ...` |
| Step 8 | `=== LEDGER INIT ===` + `=== AGENTS.md FORMAT CHECK ===` |
| Step 9 | `[CHECKPOINT] File generation method: content-offload + assemble_skill_files` + `[FIDELITY]` per library CM |
| Step 10 | `CROSS-REFERENCE PASS:` + `=== FILE GENERATION VERIFICATION ===` + `=== LIBRARY CONTENT FIDELITY ===` |
| Step 11 | `[CHECKPOINT] Handoff file written` + `=== POST-EXECUTION AUDIT ===` + `=== FROM-SCRATCH FINAL VERIFICATION ===` |

### Handoff Schema (Cross-Skill Contract)

**CONSUMED (input, `stage: survey-complete`):** required `project_id`, `evidence_source` (`codebase`|`specs`), `repository_path`; used `project_name`, `business_unit_id`, `application_id`, `risk_policy_id`, `sde_host`, `technology_pool`, and (specs only) `scaffold`/`spec_sources`/`initial_commit`. **The codebase git fields (`git_enabled`/`security_branch`/`ai_backup_archive`) are NOT consumed from the survey handoff — they are ORIGINATED by this skill's Step 7.5 repo-prep (MCP-116).** A `stage: skill-files-generated` handoff for the same project is accepted as a RESUME.

**PRODUCED (output, `stage: skill-files-generated`):**

| Field | Type | Notes |
|-------|------|-------|
| `source_skill` | string | `"generate-security-skill-files"` |
| `stage` | string | `"skill-files-generated"` |
| `evidence_source` | string | carried forward (`codebase`|`specs`) -- apply-security-fixes uses this for greenfield mode |
| `assessment_mode`, `version_label` | -- | carried forward from the survey handoff (MCP-118) |
| `repository_path` | string | |
| `project_id` | integer | validated |
| `project_name`, `business_unit_id`, `application_id`, `risk_policy_id`, `sde_host` | -- | carried forward |
| `technology_pool` | array | carried forward (helps apply-security-fixes pick file extensions) |
| `agents_md` | string | path to generated AGENTS.md |
| `skill_files` | array | generated per-CM SKILL.md paths |
| `selection_mode` | string | `all`/`specific`/`search` |
| `task_status_filter` | string | Step 3.0 SDE task-status filter: `all_statuses`/`todo_only`/`done_only` |
| `verification_status_filter` | string | Step 3.0 verification-status filter: `no_filter`/`unverified`/`unverified_and_fail` |
| `status_filtered_count` | integer | CMs remaining after the Step 3.0 status filter (pool the selection ran over) |
| `selected_cm_ids` | array | the authoritative selected scope |
| `total_countermeasures` | integer | = selected_count (apply-fixes operates on skill_files) |
| `project_total_countermeasures` | integer | full project size (reference) |
| `code_fix_count`, `documentation_count`, `process_count` | integer | selected-scope counts |
| `git_enabled`, `security_branch`, `ai_backup_archive` | -- | codebase: ORIGINATED in Step 7.5 (MCP-116); null for specs |
| `scaffold`, `initial_commit`, `spec_sources` | -- | specs (carried; null/empty for codebase) |
| `expected_skill_files` | integer | total generated files = Σ per-CM max(matched_amendments,1) (Fix E) |
| `library_sourced_cms` | array | ONE entry `{cm_id, amendment_id, matched_technology}` per library FILE (CM × matched tech) |
| `library_lookup_audit` | array | one per selected file-tracked CM: `{cm_id, endpoint, http_status, result, retry_count, queried_at, matched_amendments[]}` (each `matched_amendments` element `{amendment_id, technology}`) |
| `created_at` | string | ISO8601 |

**Post-write:** re-read; confirm valid JSON, `stage == "skill-files-generated"`, `library_lookup_audit` length == selected_file_tracked (per CM), `len(skill_files)` == expected_skill_files, `library_sourced_cms` length == library_file_count (one per CM×tech), every `skill_files` path exists.

---

## API Retry / Back-off Policy

| HTTP / error | Action |
|---|---|
| 429 | Wait 2s, retry once; on 2nd failure log FAILED, continue |
| 5xx / timeout / non-JSON | Wait 2s, retry once; on 2nd failure log FAILED, continue |
| 400 (validation/deps) | Inspect body; fix; retry once |
| 404 | amendments: no library counterpart → TEMPLATE_404; else fix id + retry once |
| 401 / 403 | NO retry; HARD STOP |

**Amendments fetch:** a TRANSIENT error MUST trigger ONE retry BEFORE falling back to template (`TEMPLATE_API_ERROR`). **PROCESS notes:** track `notes_failed[]`, retry the failed set once.

---

## Mandatory Gate Registry

| ID | Step | Pattern that MUST appear |
|----|------|--------------------------|
| G0-pre | 3.0 | `[CHECKPOINT] Status filter:` (always emitted; defaults = no narrowing) |
| G0 | 3 | `=== CM SELECTION ===` |
| G1 | 4 | `=== COUNTERMEASURE CLASSIFICATION ===` |
| G2 | 5 | `=== PROCESS NOTES VERIFICATION ===` |
| G3 | 6.1.1 | `[CHECKPOINT] Pre-flight: I will query endpoint` |
| G4 | 6.4 | `=== LIBRARY SKILL LOOKUP VERIFICATION ===` |
| G4.5 | 7.5 | `[CHECKPOINT] Git:` + `[CHECKPOINT] AI Config:` (codebase only) |
| G5 | 8.1 | `=== LEDGER INIT ===` + `=== AGENTS.md FORMAT CHECK ===` |
| G6 | 9.0 | `[CHECKPOINT] File generation method: content-offload + assemble_skill_files` |
| G7 | 10.0 | `CROSS-REFERENCE PASS:` |
| G8 | 10.1 | `=== FILE GENERATION VERIFICATION ===` |
| G9 | 10.2 | `=== LIBRARY CONTENT FIDELITY ===` |
| G10 | 11.1 | `=== POST-EXECUTION AUDIT ===` |
| G11 | 11.3 | `=== FROM-SCRATCH FINAL VERIFICATION ===` |

---

## Forbidden Behaviors

| Action | Why Forbidden |
|--------|---------------|
| **Executing any step/batch from memory without reloading its section from the pinned `.sde-security/contract/generate-security-skill-files/SKILL.md`** | Contract pinned at CONTRACT BOOTSTRAP; every preflight reloads the section and quotes a verbatim sentinel |
| **Using the SDE project total (or "work so far") as a verification denominator** | Use `selected_file_tracked` (per-CM) and `expected_skill_files` (files/ledger); the project total is a superset |
| **Using only the FIRST matched library amendment per CM / collapsing multiple matched technologies into one file** | Fix E: keep ALL matched techs — one `{CM_ID}-{tech-slug}` file per matched amendment; file/ledger denominator is `expected_skill_files` |
| **Running this skill without a valid survey-complete handoff** | HARD STOP; run a survey skill first |
| **Re-prompting for CM selection on resume instead of re-reading selected-cms.json** | selected-cms.json is the durable denominator |
| **Classifying without AI confirmation / classifying via a script** | Classification is AI-confirmed for every selected CM |
| **Emitting ML_CODE/ML_DOC when evidence_source == specs** | Greenfield uses CF/PR/IN only; ML folds into CODE_FIX or INFRA/PROCESS |
| **Skipping the library skill lookup or querying a "representative sample"** | EVERY selected file-tracked CM MUST be queried; per-CM `[PROGRESS]` + disk artifact required |
| **Using any endpoint other than `/api/v2/library/tasks/{CM_ID}/amendments/`** | Only `amendments` returns SKILL.md files |
| **Using the `api_request` MCP tool for batch/composite work** | Batch/composite goes through the SDE Direct API Access script (direct `POST /api/v2/composite/`) |
| **Summarizing / paraphrasing / truncating a library-sourced amendment** | Must be byte-for-byte; LIBRARY CONTENT FIDELITY verifies `written_len >= source_amendment_char_count` |
| **Generating SKILL.md for PROCESS CMs** | PROCESS are note-only in SDE |
| **Writing a script that AUTHORS SKILL.md content** | RC-4 failure; `assemble_skill_files` copies-verbatim / assembles AI fields only |
| **A verification block whose denominator is "files generated so far"** | Anchoring Rule violation |
| **Printing SKILL COMPLETE while any audit line is NO or missing** | Audit re-derives from SDE + disk; ALL must be YES |
| **Spot-checking/sampling the final audit instead of re-deriving every artifact class** | Enumerate every class with a re-derived count |
| **Marking a loop-heavy step (4,5,6,9) completed in TodoWrite before its gate passes** | Loop steps stay in_progress until ALL = YES |
| **Restarting from scratch (or dropping the remainder) after a context-limit interruption** | Emit CONTEXT CHECKPOINT, resume by re-deriving from SDE + disk |
| **Sampling tells in reasoning** ("key CMs"/"the rest"/"representative"/"only N"/"N+"/"Let me finalize"/"move forward to more impactful steps") | STOP, return to the BATCH PLAN, process every remaining CM |
| **Making per-CM sequential SDE calls instead of the Composite API for 2+ CMs** | PROCESS notes 50/call, amendments 25/call via composite |
| **Configuring/committing the survey here** | OUT OF SCOPE -- a survey skill does that |

---

## Classification Rules

Before marking a SELECTED CM non-CODE_FIX:

| If claiming... | You MUST have... |
|----------------|------------------|
| ML_DOC (codebase only) | searched `ai/`, `ml/`, model files, tf/pytorch imports |
| INFRA (container) | read Dockerfile/compose (codebase) or deployment spec sections (specs) and concluded infra-only |
| INFRA (database/network) | read DB/network code (codebase) or spec sections (specs) and concluded infra-only |
| PROCESS | confirmed it is organizational with no code/feature to implement |

**Default to CODE_FIX.** A matching library amendment ⇒ file-tracked, never PROCESS. Repository intent is IRRELEVANT (no "intentionally vulnerable" exceptions).

---

## Failure Recovery

- **Handoff missing/non-conformant:** HARD STOP -- run a survey skill first. On resume, a `stage=skill-files-generated` handoff for THIS project is valid.
- **Zero countermeasures:** survey not committed / generated none → return to the survey skill.
- **Library API HTML / wrong endpoint:** use the absolute path `/api/v2/library/tasks/{CM_ID}/amendments/` in the composite sub-request; verify `test_connection`.
- **Count mismatch:** re-derive expected from `selected-cms.json` ∩ non-PROCESS; add the missing files.

---

## Contract Acceptance

By reading this file, you agree to:

1. Verify MCP connection before proceeding.
2. **⚠️ MANDATORY STEP EXECUTION ORDER:**
   `0 → 1 (load+validate handoff) → 2 (fetch CMs incl. status expand) → 3 (3.0 optional status pre-filter [task + verification] → 3.1 select all/specific/search over the filtered pool -> selected-cms.json) → 4 (classify selected) → 5 (PROCESS notes) → 6 (library lookup: 6.0 → 6.0.5 → 6.1 → 6.1.1 → 6.1.2 → 6.2 → 6.3 → 6.4) → 7 (domains + code map) → 7.5 (codebase repo-prep: security branch + AI-config archive, MCP-116) → 8 (AGENTS.md: merge codebase / create specs; 8.1 ledger+format) → 9 (per-CM files: 9.0 → 9.0.1 → 9.1 → 9.2) → 10 (10.0 cross-ref → 10.1 file-gen → 10.2 fidelity → 10.3 intent) → 11 (11.0 write handoff FIRST → 11.1 audit → 11.2 verify-output.sh → 11.3 from-scratch)`
   NO step may be skipped or reordered. Step 6 is the most commonly skipped -- API COVERAGE = YES before Step 7.
3. **The selected set (`selected-cms.json`) is the authoritative scope** -- per-CM denominator = `selected_file_tracked`; file/ledger denominator = `expected_skill_files` (Σ per-CM max(matched_amendments,1), Fix E); never the SDE project total or work-so-far. A CM with multiple matched library technologies yields one `{CM_ID}-{tech-slug}` file per tech.
4. **Branch on `evidence_source`:** codebase → 5 categories incl. ML_CODE/ML_DOC, "Code to Fix" template, AGENTS.md MERGE, map vulnerable code, AND run the Step 7.5 repo-prep (security branch + AI-config archive, MCP-116); specs → CF/PR/IN only, "Spec Context" template, AGENTS.md CREATE, skip Step 7.5.
5. Classify EVERY selected CM with AI confirmation; output the CLASSIFICATION block -- STOP if NO.
6. Note every selected PROCESS CM via addNote; output PROCESS NOTES VERIFICATION.
7. **For EACH selected file-tracked CM, query the library amendments API** (`/api/v2/library/tasks/{CM_ID}/amendments/`) via the SDE Direct API Access script (composite GET), NOT the `api_request` MCP tool; output a `[PROGRESS]` line and a per-CM disk artifact per CM; API COVERAGE = YES before proceeding.
8. Write library-sourced SKILL.md content byte-exact; fall back to template when content lacks YAML front matter.
9. Generate AGENTS.md + per-CM files; output LEDGER INIT, FORMAT CHECK, CROSS-REFERENCE, FILE GENERATION, LIBRARY CONTENT FIDELITY.
10. Write `.sde-handoff.json` (`stage: skill-files-generated`, carrying survey fields forward) FIRST, then run the POST-EXECUTION AUDIT + verify-output.sh + FROM-SCRATCH FINAL VERIFICATION; do NOT print SKILL COMPLETE until ALL = YES.
11. **Subagents: reasoning stays inline, non-reasoning may be delegated.** REASONING (classification, library-match decisions, skill-file/content authoring) runs in the main agent OR a same-model subagent -- NEVER Composer 2; in Cursor, reasoning delegation is inline. NON-REASONING (running the SDE Direct API Access batch script, mechanical IO/counting) MAY be delegated to a subagent even in Cursor (set `model` explicitly, never `composer-2.5-fast`; subagent returns only the summary, parent re-derives coverage from disk).
12. **Batch/composite SDE calls go through the SDE Direct API Access script** (direct `POST /api/v2/composite/`, `Authorization: Token`), NEVER the `api_request` MCP tool.
13. Do NOT configure/commit the survey or apply fixes -- those are other skills.

**There are NO exceptions to these rules.**
