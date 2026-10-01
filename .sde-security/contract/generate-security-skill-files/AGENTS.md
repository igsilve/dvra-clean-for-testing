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
> **CURSOR IDE -- reasoning vs non-reasoning:** `.cursor/` present OR Cursor-only tools in the toolset -> `cursor_detected`. REASONING work (classification, library-match decisions, skill-file/content authoring) runs INLINE in the main agent. `composite` WRITE batches (Step 5 PROCESS-note posting) and mechanical IO/counting MAY be delegated to a subagent even in Cursor (set `model` explicitly, NEVER `composer-2.5-fast`; the subagent returns the tool's `{ posted, failed, failed_ids }` plus the `http_status_code` of every `failed_ids` entry, and the parent re-derives coverage from those results and the Step 5.2 SDE re-query). `composite` GET lookups (Steps 6.0.5 / 6.2 and any resume re-fetch) are NEVER delegated -- they run in the main agent.

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
| Author SKILL.md content | a script authors | AI authors; `assemble_skill_files` copies library `amendment.text` byte-exact (then the CM's project Additional Requirements, also copied verbatim) or assembles AI fields -- NEVER authors |

A CM with a matching library SKILL.md amendment MUST be file-tracked, never PROCESS.

---

## Completion Criteria

NOT complete until ALL are true:

- [ ] MCP connection verified (incl. one `composite op=schema` probe before Step 5; tool-not-found → STOP, server must be updated/reloaded)
- [ ] `.sde-handoff.json` loaded + validated (stage in {survey-complete, skill-files-generated}; evidence_source/project_id/repository_path present); project_id re-validated via name-match
- [ ] All project countermeasures fetched (one call, `page_size >= count`, `expand=text`; short return → `[WARN] tool limitation`); `.sde-security/project-requirements/{CM_ID}.json` written for EVERY CM
- [ ] **Step 3.0 status pre-filter (task + verification) applied (defaults = no narrowing); CM selection made (all/specific/search) over the filtered pool and persisted to `.sde-security/selected-cms.json`; `=== CM SELECTION ===` emitted**
- [ ] Each SELECTED CM classified (CF/PR/IN; +ML_CODE/ML_DOC only when evidence_source==codebase); CLASSIFICATION = YES, anchored to selected_count; persisted to `.sde-security/classification.json` (`{CM_ID: {category, domain}}`, domain filled in Step 7)
- [ ] Selected PROCESS CMs noted via addNote; PROCESS NOTES VERIFICATION = YES
- [ ] Library skill lookup run for EVERY selected file-tracked CM; LIBRARY SKILL LOOKUP VERIFICATION (API COVERAGE = YES); per-CM `.sde-security/library-lookup/{CM}.json` artifacts == selected_file_tracked
- [ ] Domains derived; (codebase) non-library CODE_FIX/ML_CODE mapped to file:line
- [ ] (codebase, Step 7.5, MCP-116) security branch created + pre-existing AI config archived; `git_enabled`/`security_branch`/`ai_backup_archive` originated for the handoff
- [ ] AGENTS.md created (specs) or merged with markers (codebase); LEDGER INIT + FORMAT CHECK = YES
- [ ] Skill files generated: **one per matched library technology** (`{CM_ID}-{tech-slug}`) plus one template file per 0-match CM (library byte-exact + the CM's project Additional Requirements appended, OR template; template format branches on evidence_source) -- excludes PROCESS; total == expected_skill_files
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
| Step 2 | `[CHECKPOINT] Total project countermeasures: {N} \| project-requirements/*.json written: {N} ({K} with >=1 Additional Requirement)` (both `{N}` equal) |
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

**CONSUMED (input, `stage: survey-complete`):** required `project_id`, `evidence_source` (`codebase`|`specs`), `repository_path`; used `project_name`, `business_unit_id`, `application_id`, `risk_policy_id`, `sde_host`, `technology_pool`, and (specs only) `scaffold`/`spec_sources`/`initial_commit`. **The codebase git fields (`git_enabled`/`security_branch`/`ai_backup_archive`) are NOT consumed from the survey handoff — they are ORIGINATED by this skill's Step 7.5 repo-prep (MCP-116).** A `stage: skill-files-generated` handoff for the same project is accepted as a RESUME; so is `stage: survey-complete` when B0 finds this skill's own prior artifacts (an interrupted run never reaches Step 11) -- valid only if `selected-cms.json.project_id` matches, `verify-output.sh` is absent, and `selected-cms.json.created_at` is later than the handoff's `created_at`; otherwise NEW run.

**PRODUCED (output, `stage: skill-files-generated`):**

| Field | Type | Notes |
|-------|------|-------|
| `source_skill` | string | `"generate-security-skill-files"` |
| `stage` | string | `"skill-files-generated"` |
| `evidence_source` | string | carried forward (`codebase`|`specs`) -- apply-security-fixes uses this for greenfield mode |
| `assessment_mode`, `version_label` | -- | carried forward from the survey handoff (MCP-118) |
| `repository_path` | string | |
| `project_id` | integer | validated |
| `business_unit_id`, `application_id` | integer | carried forward; a quoted upstream ID (create-security-plan-from-specs writes "{id}") is written as its integer value |
| `project_name`, `risk_policy_id`, `sde_host` | -- | carried forward |
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
| `library_sourced_cms` | array | ONE entry `{cm_id, amendment_id, matched_technology, additional_requirements_count}` per library FILE (CM × matched tech) |
| `library_lookup_audit` | array | one per selected file-tracked CM: `{cm_id, endpoint, http_status, result, retry_count, queried_at, matched_amendments[], additional_requirements_count}` (each `matched_amendments` element `{amendment_id, technology}`; `additional_requirements_count` = the CM's `count` from `.sde-security/project-requirements/{CM_ID}.json`; appended ONLY to its library files (`result == LIBRARY_SOURCED`) -- template CMs record the count but their file never gets the section; `result` `PENDING_MATCH` is transient (Step 6.2→6.3) and never appears in `.sde-handoff.json`) |
| `created_at` | string | ISO8601 |

**Post-write:** re-read; confirm valid JSON, `stage == "skill-files-generated"`, `library_lookup_audit` length == selected_file_tracked (per CM), `len(skill_files)` == expected_skill_files, `library_sourced_cms` length == library_file_count (one per CM×tech), every `additional_requirements_count` matches its CM's `project-requirements/{CM_ID}.json` count, every `skill_files` path exists.

---

## API Retry / Back-off Policy

| HTTP / error | Action |
|---|---|
| 429 | Wait 2s, retry once; on 2nd failure log FAILED, continue |
| 5xx / timeout / non-JSON | Wait 2s, retry once; on 2nd failure log FAILED, continue |
| 400 (validation/deps) | Inspect body; fix; retry once |
| 404 | amendments: no library counterpart → TEMPLATE_404; else fix id + retry once |
| 401 / 403 | NO retry; HARD STOP |

This table governs single/interactive MCP-tool calls. Batch sub-requests sent through `composite` are retried by the tool itself (once) -- act only on the returned `failed_ids`, as described below.

**Amendments fetch (Step 6.2, single pass, ≤5 CMs/call -- drop to 2 for the remaining CMs once a response exceeds ~100k chars, 1 for a CM with many amendments; size scales with amendments per CM; response always carries full text, Step 6.3 matches from it with no second fetch; a re-fetch overwrites the CM's artifact):** the `composite` tool retries the failed subset once automatically; for a CM still in `failed_ids` after that, classify by its `http_status_code` -- 404 → `TEMPLATE_404`, 401/403 → HARD STOP, any other non-2xx, or a 2xx whose `body` is not JSON or lacks `results` → template (`TEMPLATE_API_ERROR`). **PROCESS notes:** 401/403 on any sub-request → HARD STOP; otherwise track `notes_failed[]` from `failed_ids` in the tool result (the tool has already retried them once) and re-post only those still missing after the Step 5.2 SDE re-query.

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
| **Re-prompting for CM selection, re-classifying, or re-running the 6.0.5 probe on resume instead of re-reading selected-cms.json / classification.json / library-probe.json** | these files are the durable denominator, classification, and probe record |
| **Classifying without AI confirmation / classifying via a script** | Classification is AI-confirmed for every selected CM |
| **Emitting ML_CODE/ML_DOC when evidence_source == specs** | Greenfield uses CF/PR/IN only; ML folds into CODE_FIX or INFRA/PROCESS |
| **Skipping the library skill lookup or querying a "representative sample"** | EVERY selected file-tracked CM MUST be queried; per-CM `[PROGRESS]` + disk artifact required |
| **Using any endpoint other than `/api/v2/library/tasks/{CM_ID}/amendments/`** | Only `amendments` returns SKILL.md files |
| **Using the `api_request` MCP tool for batch/composite work** | Batch/composite goes through the `composite` MCP tool (`op=execute`); credentials stay server-side |
| **Summarizing / paraphrasing / truncating a library-sourced amendment** | The amendment text must be byte-for-byte; LIBRARY CONTENT FIDELITY verifies the file's first `source_amendment_char_count` chars equal it exactly. Appending the CM's project Additional Requirements after it (SKILL.md Step 9.1) is REQUIRED, not a violation |
| **Generating SKILL.md for PROCESS CMs** | PROCESS are note-only in SDE |
| **Writing a script that AUTHORS SKILL.md content** | RC-4 failure; `assemble_skill_files` copies-verbatim (library text + project Additional Requirements) / assembles AI fields only |
| **A verification block whose denominator is "files generated so far"** | Anchoring Rule violation |
| **Printing SKILL COMPLETE while any audit line is NO or missing** | Audit re-derives from SDE + disk; ALL must be YES |
| **Spot-checking/sampling the final audit instead of re-deriving every artifact class** | Enumerate every class with a re-derived count |
| **Marking a loop-heavy step (4,5,6,9) completed in TodoWrite before its gate passes** | Loop steps stay in_progress until ALL = YES |
| **Restarting from scratch (or dropping the remainder) after a context-limit interruption** | Emit CONTEXT CHECKPOINT, resume by re-deriving from SDE + disk |
| **Sampling tells in reasoning** ("key CMs"/"the rest"/"representative"/"only N"/"N+"/"Let me finalize"/"move forward to more impactful steps") | STOP, return to the BATCH PLAN, process every remaining CM |
| **Making per-CM sequential SDE calls instead of the `composite` MCP tool for 2+ CMs** | PROCESS notes 50/call, amendments ≤5/call (2 or 1 once a response exceeds ~100k chars; full text always returned) via `composite op=execute` (tool cap 100/call) |
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

- **Handoff missing/non-conformant:** HARD STOP -- run a survey skill first. On resume, a `stage=skill-files-generated` handoff for THIS project is valid; so is `stage=survey-complete` with this skill's prior artifacts (B0 → resume, clear nothing).
- **Resume before Step 11:** no `verify-output.sh` and handoff still `survey-complete` → skip RESUME STEP 0 (nothing to verify yet) and re-derive the done-set; the Step 6 pre-flight/batch plan covers only CMs without a final `library-lookup/` artifact, and the mini-gate counts only final (non-`PENDING_MATCH`) artifacts.
- **Zero countermeasures:** survey not committed / generated none → return to the survey skill.
- **Library API HTML / wrong endpoint:** use the absolute path `/api/v2/library/tasks/{CM_ID}/amendments/` in the composite sub-request; verify `test_connection`.
- **Count mismatch:** re-derive expected from `selected-cms.json` ∩ non-PROCESS; add the missing files.

---

## Contract Acceptance

By reading this file, you agree to:

1. Verify MCP connection before proceeding, including one `composite op=schema` probe (tool-not-found → STOP before Step 5).
2. **⚠️ MANDATORY STEP EXECUTION ORDER:**
   `0 → 1 (load+validate handoff) → 2 (fetch CMs incl. status expand) → 3 (3.0 optional status pre-filter [task + verification] → 3.1 select all/specific/search over the filtered pool -> selected-cms.json) → 4 (classify selected) → 5 (PROCESS notes) → 6 (library lookup: 6.0 → 6.0.5 → 6.1 → 6.1.1 → 6.1.2 → 6.2 → 6.3 → 6.4) → 7 (domains + code map) → 7.5 (codebase repo-prep: security branch + AI-config archive, MCP-116) → 8 (AGENTS.md: merge codebase / create specs; 8.1 ledger+format) → 9 (per-CM files: 9.0 → 9.0.1 → 9.1 → 9.2) → 10 (10.0 cross-ref → 10.1 file-gen → 10.2 fidelity → 10.3 intent) → 11 (11.0 write handoff FIRST → 11.1 audit → 11.2 verify-output.sh → 11.3 from-scratch)`
   NO step may be skipped or reordered. Step 6 is the most commonly skipped -- API COVERAGE = YES before Step 7.
3. **The selected set (`selected-cms.json`) is the authoritative scope** -- per-CM denominator = `selected_file_tracked`; file/ledger denominator = `expected_skill_files` (Σ per-CM max(matched_amendments,1), Fix E); never the SDE project total or work-so-far. A CM with multiple matched library technologies yields one `{CM_ID}-{tech-slug}` file per tech.
4. **Branch on `evidence_source`:** codebase → 5 categories incl. ML_CODE/ML_DOC, "Code to Fix" template, AGENTS.md MERGE, map vulnerable code, AND run the Step 7.5 repo-prep (security branch + AI-config archive, MCP-116); specs → CF/PR/IN only, "Spec Context" template, AGENTS.md CREATE, skip Step 7.5.
5. Classify EVERY selected CM with AI confirmation; output the CLASSIFICATION block -- STOP if NO.
6. Note every selected PROCESS CM via addNote; output PROCESS NOTES VERIFICATION.
7. **For EACH selected file-tracked CM, query the library amendments API** (`/api/v2/library/tasks/{CM_ID}/amendments/`) via the `composite` MCP tool (`op=execute`, composite GET), NOT the `api_request` MCP tool; output a `[PROGRESS]` line and a per-CM disk artifact per CM; API COVERAGE = YES before proceeding.
8. Write library-sourced SKILL.md content byte-exact, then append the CM's project Additional Requirements -- read ONLY from `.sde-security/project-requirements/{CM_ID}.json` (Step 2's `text.amendments`, minus `{CM_ID} - SKILL.md - *` titles) -- verbatim at the bottom when its `count` > 0; fall back to template when content lacks YAML front matter (template files never get the Additional Requirements section).
9. Generate AGENTS.md + per-CM files; output LEDGER INIT, FORMAT CHECK, CROSS-REFERENCE, FILE GENERATION, LIBRARY CONTENT FIDELITY.
10. Write `.sde-handoff.json` (`stage: skill-files-generated`, carrying survey fields forward) FIRST, then run the POST-EXECUTION AUDIT + verify-output.sh + FROM-SCRATCH FINAL VERIFICATION; do NOT print SKILL COMPLETE until ALL = YES.
11. **Subagents: reasoning stays inline; composite writes may be delegated, composite GETs stay inline.** REASONING (classification, library-match decisions, skill-file/content authoring) runs in the main agent OR a same-model subagent -- NEVER Composer 2; in Cursor, reasoning delegation is inline. `composite` WRITE batches (Step 5 PROCESS-note posting) and mechanical IO/counting MAY be delegated to a subagent even in Cursor (set `model` explicitly, never `composer-2.5-fast`; subagent returns the tool's `{ posted, failed, failed_ids }` plus the `http_status_code` of every `failed_ids` entry, parent re-derives coverage from those results and the Step 5.2 SDE re-query). `composite` GET lookups (Steps 6.0.5 / 6.2 and any resume re-fetch) are NEVER delegated -- main agent only.
12. **Batch/composite SDE calls go through the `composite` MCP tool** (`op=execute`), NEVER the `api_request` MCP tool, an embedded script, or inline `curl` -- credentials stay server-side.
13. Do NOT configure/commit the survey or apply fixes -- those are other skills.

**There are NO exceptions to these rules.**
