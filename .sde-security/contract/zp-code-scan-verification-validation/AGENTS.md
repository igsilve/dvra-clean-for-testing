# ZP Code Scan Verification Validation Skill - Agent Execution Contract

> **SUBAGENT / DELEGATION POLICY -- READ THIS FIRST**
>
> 1. **Same model as the parent, ALWAYS.** Any spawned subagent MUST run on the SAME model as the parent agent -- set the `model` parameter explicitly to the parent's model. If you cannot set the subagent's model, do NOT spawn -- run inline.
> 2. **NEVER Composer 2.** `composer-2.5-fast` (Composer 2) is FORBIDDEN as a subagent model in ANY environment -- it silently abandons CM verification loops, skips CMs, uses wrong endpoints for note POSTs, loses context, and produces unreliable verdicts. In Cursor the DEFAULT subagent is Composer 2, so you MUST override `model` to the parent's model explicitly; if you cannot override it, run inline.
> 3. **Parent owns completeness.** Delegation NEVER transfers responsibility for completeness. The parent re-derives every CM from SDE + disk (tri-source invariant) regardless of who did the work. Every subagent MUST emit `[VERIFY]`/`[PROGRESS]` lines and return a verifiable JSON result; the parent verifies every item.
>
> Subagent batching (Step A6 / Phase B) is permitted in ANY environment (including Cursor) under this policy; inline execution is the fallback ONLY when the subagent `model` cannot be set to the parent's model. (Governs the AI loop in `ai`/`hybrid`; `zeropath` has no AI loop.)
>
> Output at skill start: `[CHECKPOINT] Subagent policy: same-model-as-parent | Composer 2 FORBIDDEN | parent owns completeness (tri-source)`

This contract MUST be followed when executing `SKILL.md` in this directory.

**AUTHORITATIVE EXECUTION CONTRACT:** This contract is the authoritative source for HOW MUCH work is required; it OVERRIDES your judgment about scale or "pragmatic" shortcuts. Expect the per-CM verification loop (`ai`/`hybrid`) to run for EVERY in-scope CM (tens-to-hundreds is NORMAL, not a reason to sample). You have explicit permission to take as many turns/sessions as needed — completeness is the only priority; the ONLY sanctioned pause is a `=== CONTEXT CHECKPOINT ===` (resume by re-deriving from SDE + the on-disk per-CM artifacts, never chat memory). A run is COMPLETE (all gates pass) or INCOMPLETE (clean checkpoint) — no third state. Forbidden rationalizations: "pragmatic" / "representative" / "efficient" / "key CMs" / "the rest are ..." / "Let me finalize" (pre-completion). See SKILL.md CONTRACT BOOTSTRAP + STEP PREFLIGHT (pin the served contract to `.sde-security/contract/zp-code-scan-verification-validation/`; reload each step's section + quote a sentinel).

> **CRITICAL: PHASE A RUNS IN PLAN MODE. DO NOT SWITCH TO AGENT MODE UNTIL PHASE B.**
>
> Complete ALL Phase A steps (A0-A7) in plan mode using `ask_question` for user inputs and read-only tools for context gathering. Phase A is entirely read-only. Step A1.5+A3 (resume + scope selection) MUST use `ask_question` -- never infer scope from the user's message or default to `all`. When a prior run exists, present both the resume choice and the scope choice in a single `ask_question` call. Only after the user confirms the execution plan in Step A7 should you switch to agent mode for Phase B.

## Skill Identity

**Name:** ZP Code Scan Verification Validation
**Purpose:** Verify that security countermeasures are actually mitigated in code, and record a Verification Note on each task in SD Elements. Adds a selectable **scan engine** — `ai` (the original AI verdict engine), `zeropath` (ZeroPath scan; its backend writes SDE verification results — skill posts no notes), and `hybrid` (AI per-CM analysis + a ZeroPath scan, merged into one combined note per CM with status from a user-chosen authoritative source). Supports two CM-source modes orthogonal to the engine: **handoff mode** (downstream of `apply-security-fixes`) and **standalone mode** (independent — user selects an SDE project via MCP, or enters a project id directly).
**Handoff identity (UNCHANGED for shared resume):** writes `.sde-verification-handoff.json` with `source_skill == "code-scan-verification-validation"` — the handoff filename and `source_skill` value are deliberately preserved so resume state is shared with the original skill. Only the skill NAME/title is `zp-code-scan-verification-validation`.
**Scope:** Read-only with respect to source files; write-only with respect to SDE `/analysis-notes/` and the local `.sde-verification-handoff.json`.

**SHELL TOOL USAGE POLICY (see SKILL.md for the canonical table):** the AI owns ALL vuln analysis (B2), verdicts (B3), and finding/note authoring — inline, NEVER a script and NEVER offloaded to disk in place of doing it (the disk-offload stores the OUTPUT of the AI's analysis, not a substitute for it). Applies to the `ai` engine and the `hybrid` AI loop; `zeropath` runs no AI analysis. Scripts are allowed ONLY for mechanical/IO (per-CM result offload, disk count, assemble-from-disk, the Layer-2 verify script). SDE notes are posted per-CM via `verification op=create` with verify+retry — **NO Composite API** (`hybrid` posts ONE combined note per CM; `zeropath` posts none).

---

## ⚠️ STEP 0: MODE SELECTION — HANDOFF OR STANDALONE

This skill supports two modes, selected by the user at Step A0.5:

- **Handoff mode:** requires `.sde-apply-handoff.json` at the selected repository root with `source_skill == "apply-security-fixes"`. If missing/malformed, HARD STOP (or switch to standalone mode).
- **Standalone mode:** no handoff file needed -- use after the survey + `generate-security-skill-files` chain (`setup-security-plan-from-repo` or `create-security-plan-from-specs` → `generate-security-skill-files`), or any manual fix workflow. The user selects an SD Elements project via MCP, and the skill fetches countermeasures directly from SDE. Tasks verified as `pass` (including `vulnerability-absent`) are marked DONE via `task_status_mapping`.

### Execution Order (MANDATORY)

```
1. Phase A:
   A0.   MCP connection check (sdelements)
   A0.0. Scan engine selection (ai | zeropath | hybrid) — FIRST interactive question; orthogonal to mode
   A0-ZP. [zeropath|hybrid ONLY] Multi-MCP preflight (sdelements + zeropath + securitycompass) + SDE tenant-match guard (HARD STOP on any failure)
   A0.5. Mode selection (handoff | standalone | enter project id directly) + repository path
   --- HANDOFF MODE ---
   A1.   Handoff detection + validation (HARD STOP if missing/wrong)
   --- STANDALONE MODE ---
   A1-S. SDE project selection + CM fetch + SDE status filters
   --- BOTH MODES ---
   A1.6. Risk policy check + confirm (display the project's current SDE risk policy; user confirms; read-only -- NO change)
   A1.5+A3. Resume from prior run (if applicable) + Scope selection (combined ask_question -- NEVER infer or default) -- AI ENGINE ONLY; for zeropath|hybrid this step is SKIPPED and scope is forced to "all" (R-ZP10)
   A2.   Git tree safety + branch checkout (HARD STOP if dirty)
   A4.   Fail-verdict rollback opt-in
   A5.   Batch size selection (default 10) -- ai/hybrid ONLY; SKIPPED for zeropath (no AI loop, batch_size = "n/a")
   A6.   Subagent capability probe (inline fallback if unavailable)
   A-ZP1. [zeropath|hybrid ONLY] ZeroPath setup: resolve repo (repositories_list/manual/addByUrl) -> reuse-or-addProjectMapping -> syncRules (409 retry) -> getMappingAudit -> A-ZP1.6 scan_branch select + verify committed+pushed to the ZeroPath remote (HARD STOP -> user pushes; R-ZP11)
   A-ZP2. [hybrid ONLY] Authoritative-source choice (ai|zeropath). Scan-timeout question REMOVED for both engines -- status polled every 1 min with a 30-min default cap (zeropath asks nothing in A-ZP2)
   A7.   Execution plan summary + user confirmation (Phase A verification gate; includes scan_engine, ZP setup summary, authoritative source, scan side-effect warning)
2. Phase B — ENGINE ROUTER (by scan_engine):
   - scan_engine == "ai": the original AI per-CM loop below runs verbatim.
   - scan_engine == "zeropath": run the ZeroPath-Only engine (scans_start -> poll scans_get to Finished every 1 min (30-min default cap), scans_cancel if the cap is hit -> confirm push via getSyncHistory -> report from getMappingAudit/getIntegration/issues_list; pass-by-absence WARN gate). Skill posts NO verification notes. The AI per-CM loop is SKIPPED.
   - scan_engine == "hybrid": kick off scans_start (non-blocking) -> run the AI per-CM loop below with B5 DEFERRED (return verdict, no POST) -> after push lands, read ZeroPath's SDE note per CM and post ONE combined note per in-scope CM (behaviour=combine), status from the authoritative source.
2a. AI per-CM loop (used by scan_engine ai, and by hybrid with B5 deferred) — parent loop = pure orchestrator; or inline if execution_mode == "inline":
   Phase 1 — Parent short-circuits (per-CM, before batching):
     [HANDOFF MODE ONLY]:
       B0a. Documented short-circuit (under selected_cms): record skipped_out_of_scope
       B0b. Upstream-Skipped short-circuit: forced fail/high + B4+B5 POST inline
       B0b2. Code-CM empty-files forced-fail (handoff v2 only): fail/high + B4+B5 POST inline
       B0b3. Non-code-CM empty-files OOS (handoff v2 only): skipped_out_of_scope
     [STANDALONE MODE]: no handoff-derived short-circuits; all CMs pass through
     [BOTH MODES]:
       B0c. one_by_one user prompt (yes/skip/stop)
   Phase 2 — Per-CM verification (subagent or inline):
     Surviving CMs grouped into batches of batch_size.
     When execution_mode == "subagent": up to 5 batches dispatched in parallel per round.
     When execution_mode == "inline": batch_size=1, no parallel (Step A6).
     Each batch -> per-CM verification sequentially:
       [HANDOFF MODE]:  B1 (fetch) + B1.5 (short-circuit) + B2 (analyse) + B4 (fetch existing notes) + B5 (POST)
       [STANDALONE MODE]: B1 (fetch) + B1.7 (file discovery) + B2 (analyse) + B4 (fetch existing notes) + B5 (POST)
              -> B1.5 inside subagent (handoff mode only, after category fetched from SDE):
                   L-FF2-sub: code CM with empty files_modified[] -> forced fail/high
                   L-OOS-sub: non-code CM with empty files_modified[] -> out_of_scope
              -> B1.7 inside subagent (standalone mode only):
                   discover relevant files via grep/glob + AI ranking
                   no files found -> pass/high (vulnerability-absent)
              -> returns JSON ARRAY of {result_kind, verdict?, note_post_status, auth_failure, reason}
              -> on result_kind=out_of_scope, parent records skipped_out_of_scope (no POST)
              -> on auth_failure=true, parent stops dispatching further ROUNDS and records unreached (rest of this batch + subsequent rounds; same-round siblings keep real verdicts; deduped)
              -> on malformed return, parent records partial/low/analysis-uncertain for batch
              -> on timeout (all retries), parent records partial/low/subagent-timeout for batch
3. Step D: Write .sde-verification-handoff.json
4. Completion verification block
```

### Why AI Analysis, NOT Just Status Inheritance

| ❌ Assume pass because apply-fixes said "Applied" or SDE says "DONE" | ✅ `read_file` the relevant files and verify the fix is present |
|---|---|
| Grep for a fix pattern | Read the file, reason about it in context of CM's `text` and `problem` |
| Trust `files_modified[]` alone (handoff) or skip analysis (standalone) | Confirm every relevant file actually mitigates the vulnerability |

---

## ⚠️ MANDATORY USER INPUTS - NEVER SKIP

Regardless of mode:

0. **MUST ask the user** for the scan engine (`ai` / `zeropath` / `hybrid`) at Step A0.0 — the FIRST interactive question. Never infer it. For `zeropath`/`hybrid`, the A0-ZP preflight, A-ZP1 ZeroPath setup, and (hybrid) A-ZP2 authoritative-source inputs are ALSO mandatory.
1. **MUST ask the user** for mode (handoff / standalone / enter-project-id) and repository path (Step A0.5)
2. **MUST ask the user** to confirm the input (handoff values or SDE project + filters) before entering Phase B
3. **(ai engine ONLY) MUST ask the user** for verification scope **via `ask_question`** (Step A1.5+A3) -- even if the user's message implies a scope. When a prior run exists, the scope question is presented alongside the resume choice in a single `ask_question` call (two questions, one batch). When no prior run exists, only the scope question is presented. The scope question MUST be a structured `ask_question` call, not inferred from conversation context. If the user says "verify all", you still present the menu. If `one_cm` or `multi_cm` selected, **MUST immediately prompt for CM ID(s)** in the same step before proceeding to A4. **For `zeropath`/`hybrid` this step is SKIPPED entirely (R-ZP10): scope is force-set to `all`, resume is not offered, and NO scope/resume question is asked.**
4. **MUST ask the user** for the fail-rollback opt-in (Step A4)
5. **Batch size (Step A5):** **SKIPPED for `zeropath`** (no AI loop — set `batch_size = "n/a"`, do not ask). For `ai`/`hybrid`: auto-set to 1 when exactly one CM is selected (skip the question); otherwise **MUST ask the user**
6. **MUST display + confirm** the project's current risk policy (Step A1.6) — read-only; HARD STOP on cancel; the skill never changes the policy (all engines, all modes)

**Standalone mode additional:**
7. **MUST ask the user** to select an SDE project (Step A1-S.1)
8. **MUST ask the user** for task status filter and verification status filter (Step A1-S.3)

**NEVER:**
- Auto-proceed just because the handoff file validates or CMs were fetched
- Assume `all` scope **when `scan_engine == "ai"`** (for `zeropath`/`hybrid`, scope is force-set to `all` by R-ZP10 — that is required, not an assumption)
- Send `task_status_mapping: {"fail": "TODO"}` without A4 opt-in
- Auto-select an SDE project in standalone mode

---

## CRITICAL ENFORCEMENT RULES

### Rule 1: Progress Output is MANDATORY

Every per-CM transition emits exactly one of the canonical checkpoint formats listed under "Mandatory Outputs > Progress Checkpoints" below. The default for a normally-verified CM is:

```
[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict={pass|partial|fail} | confidence={high|low} | note={POSTED|FAILED:{reason}}
```

Other documented variants (each with its own row in the Mandatory Outputs table) are required for their respective paths and are NOT substitutes for the `[VERIFY]` line above when a CM is verified normally:

- `[VERIFY-DISPATCH]` immediately before each batch subagent launch (includes batch number and CM IDs)
- `[VERIFY]` with `note={POSTED|FAILED:{reason}}` for the parent forced-fail short-circuits (B0b upstream-Skipped; B0b2 code CM with empty `files_modified[]` when `handoff_version == "2"`) which run B4+B5 POST inline, and for the subagent's L-FF2-sub lane (code CM with empty `files_modified[]` when v1) which runs B4+B5 inside the subagent
- `[VERIFY]` with `note=FAILED:subagent-malformed` (verdict=partial, confidence=low) for malformed subagent returns (emitted per CM in the batch)
- `[VERIFY]` with `note=FAILED:subagent-timeout` (verdict=partial, confidence=low) for subagent timeout after all retries (emitted per CM in the batch)
- `[VERIFY]` with `note=NOT_SENT_AUTH_FAILURE` for the current CM in an auth-failure abort
- `[SKIP-OOS]` for Documented CMs under `selected_cms` (parent B0a), parent B0b3 (non-code CM with empty `files_modified[]` when `handoff_version == "2"`), AND subagent L-OOS-sub returns when `parsed.result_kind == "out_of_scope"` (non-code CM with empty `files_modified[]` when v1)
- `[SKIP-USER]` for `one_by_one` per-CM `skip`
- `[STOP]` for `one_by_one` `stop` and for auth-failure abort (single line bulk-summarising unreached CMs; the unreached CMs are still recorded individually in `verification_results[]` to preserve the Sum-check identity)
- `[INFO]` for the empty-in-scope short-circuit (`in_scope_total == 0`)

Skipping any of the above when its trigger fires is a contract violation.

### Rule 2: Loop Until Scoped Remaining = 0 (Parent = Pure Orchestrator / Inline Executor)

The parent loop is a **pure orchestrator**: it does scope filtering, up to four forced short-circuit lanes (B0a Documented OOS, B0b upstream-Skipped forced-fail, B0b2 code-CM empty-files forced-fail, B0b3 non-code-CM empty-files OOS), the `one_by_one` user prompt, and result-recording. **When `execution_mode == "subagent"`, it does NOT run B1 fetch, B2 analysis, B3 verdict, B4 note-fetch, or B5 POST inline for any in-scope CM that survives the parent short-circuits** — those run inside `generalPurpose` subagents dispatched in batches. (When `execution_mode == "inline"` — Step A6 fallback — B1/B2/B3/B4/B5 run inline with batch_size=1; see Rule 9.) B0b2 and B0b3 fire **only when `handoff_version == "2"`** (which includes `cm.category`); when `handoff_version == "1"`, the empty-`files_modified[]` discriminator is enforced **inside the per-CM verification context** (subagent or inline) via L-FF2-sub/L-OOS-sub (after `cm.category` is fetched live in B1).

The loop has two phases: Phase 1 runs parent short-circuits per-CM and collects surviving CMs into the eligible set. Phase 2 groups them into batches and dispatches them for verification — via subagents when `execution_mode == "subagent"`, or processed inline when `execution_mode == "inline"` (see Rule 9) — with retry/timeout handling and result processing.

```python
if in_scope_total == 0:
    print("[INFO] No in-scope CMs after filtering. Nothing to verify; writing empty handoff.")

# ── Phase 1: Parent short-circuits (B0a/B0b/B0b2/B0b3/B0c) ──
subagent_eligible = []
for cm in in_scope:
    done += 1
    # ── Handoff-mode-only short-circuits ──
    if verification_mode == "handoff":
        if cm.status == "Documented":
            results.append(record_out_of_scope(cm, ...))
            continue
        if cm.status == "Skipped":
            verdict = forced_fail(cm, ...)
            existing_notes = fetch_existing_notes(project_id, cm.full_id)  # B4 inline
            post_status = post_verification_note(project_id, cm, verdict, existing_notes)  # B5 inline
            results.append(record_verified(cm, verdict, post_status))
            continue
        # B0b2/B0b3: parent-side empty-files short-circuits (handoff v2 only)
        if handoff_has_category and cm.category in ("CODE_FIX", "ML_CODE") and len(cm.files_modified) == 0:
            verdict = forced_fail(cm, ...)
            existing_notes = fetch_existing_notes(project_id, cm.full_id)  # B4 inline
            post_status = post_verification_note(project_id, cm, verdict, existing_notes)  # B5 inline
            results.append(record_verified(cm, verdict, post_status))
            continue
        if handoff_has_category and cm.category in ("INFRA", "ML_DOC") and len(cm.files_modified) == 0:
            results.append(record_out_of_scope(cm, ...))
            continue
    # (standalone mode: no handoff-derived short-circuits — all CMs proceed to batching)
    if scope == "one_by_one":
        r = ask("yes/skip/stop")
        # skip -> record_skipped(cm, "user skipped") + continue.
        # stop -> record the stop CM + every unreached CM (in_scope[done:]) via
        #         record_skipped, then `break` out of Phase-1 collection. Do NOT
        #         set `aborted`: the pre-stop "yes" CMs already in
        #         subagent_eligible MUST still be verified in Phase 2. (`aborted`
        #         is reserved for the involuntary auth-failure abort below.)
    subagent_eligible.append(cm)

# ── Phase 2: Batched verification (runs whenever eligible CMs were collected;
#    a user `stop` does NOT skip it — only an auth-failure sets `aborted`) ──
if not aborted and len(subagent_eligible) > 0:
    SUBAGENT_TIMEOUT_MS = 300_000   # 5 minutes
    MAX_RETRIES         = 2         # 2 retries = 3 total attempts
    parallel_subagents  = 5 if execution_mode == "subagent" else 1   # batches dispatched concurrently per round (A7; matches SKILL.md)
    batch_num           = 0         # 1-based dispatch counter, incremented per batch below

    batches = [subagent_eligible[i:i+batch_size] for i in range(0, len(subagent_eligible), batch_size)]

    if execution_mode == "subagent":
        for round_start in range(0, len(batches), parallel_subagents):
            round_batches = batches[round_start : round_start + parallel_subagents]

            for batch in round_batches:
                batch_num += 1
                print(f"[VERIFY-DISPATCH] batch {batch_num}/{len(batches)} | {len(batch)} CMs: {[cm.full_id for cm in batch]} | subagent launched")

            parallel_results = launch_subagents_parallel(
                [render_batch_subagent_prompt(batch, ...) for batch in round_batches],
                timeout_ms=SUBAGENT_TIMEOUT_MS, max_retries=MAX_RETRIES)

            for batch, sub_raw in zip(round_batches, parallel_results):
                if sub_raw is TIMEOUT:
                    for cm in batch: ...      # partial/low/subagent-timeout
                    continue
                parsed_array = parse_and_validate_batch_output(sub_raw, ...)
                if parsed_array.is_error:
                    for cm in batch: ...      # partial/low/analysis-uncertain
                    continue
                for cm, parsed in zip(batch, parsed_array.results):
                    if parsed.is_error: ...   # partial/low for this CM only
                    elif parsed.result_kind == "out_of_scope": ...  # record_out_of_scope
                    elif parsed.auth_failure: ...  # stop future rounds; record unreached (rest of batch + subsequent rounds), dedupe; same-round siblings keep verdicts
                    else: ...                 # normal path

    else:  # execution_mode == "inline"
        for batch in batches:  # batch_size=1, sequential
            batch_num += 1
            print(f"[VERIFY-DISPATCH] batch {batch_num}/{len(batches)} | {len(batch)} CMs: {[cm.full_id for cm in batch]} | inline")
            for cm in batch:
                run_inline_verification(cm, ...)  # B1 + B1.5/B1.7 + B2 + B3 + B4 + B5 in parent context
            if done % 5 == 0:
                print("=== CONTEXT CHECKPOINT ===")
```

Agent-initiated early exit is forbidden. User-initiated paths in `one_by_one` (`skip` per-CM and `stop` loop-terminating) MUST record entries via `record_skipped(cm, reason)` to preserve the Sum-check identity. The auth-failure path is involuntary but is also covered: the current CM is recorded with `NOT_SENT_AUTH_FAILURE` and every unreached CM is recorded via `record_skipped` — see SKILL.md Rule 10. **In `one_by_one` (ai engine) each per-CM `ask_question` ends the turn; on the user's reply you MUST continue the loop to the NEXT in-scope CM (re-derive the done-set from `cm-work/*.json` on resume). Do NOT emit a completion block or any "complete"/"SKILL COMPLETE"/"done" declaration until `running_total (P+PT+F+S+S_oos) == in_scope_total` — declaring complete after the FIRST CM is the most common violation and is forbidden.**

### Rule 3: Verification Before Completion

Before using "complete", "finished", "done", "summary":
1. Output the completion verification block
2. Confirm `Sum check = YES`
3. Only then use completion words

### Rule 4: Upstream Handoff is Read-Only

- ✅ Read `.sde-apply-handoff.json`
- ❌ NEVER modify or delete `.sde-apply-handoff.json`
- ✅ Write `.sde-verification-handoff.json` (separate file)

### Rule 5: No False Positives — Negative Signal is Canonical

> **No false positives. Negative signal is canonical; positive signal is corroborative. Recognition is corroborative; absence-of-vulnerability is canonical.**
>
> A `fail` verdict requires **CITED, CONCRETE EVIDENCE** of a vulnerability — exactly four sources are allowed:
> 1. a residual vulnerable pattern matching `ctx.problem`, cited at a specific file:line, OR
> 2. a residual marker comment (`vuln-code-snippet`, `VULNERABLE`, `TODO: fix`, etc.), cited at a specific file:line, OR
> 3. an upstream forced-fail signal: `cm.status == "Skipped"` (parent short-circuit B0b) **(handoff mode only)**, OR
> 4. empty `files_modified[]` for a CODE_FIX/ML_CODE CM (parent B0b2 when `handoff_version == "2"`, subagent L-FF2-sub when v1) **(handoff mode only)**.
>
> **Standalone mode uses only sources (1) and (2).** Sources (3) and (4) are inapplicable because standalone mode has no upstream `Skipped` status or apply-fixes `files_modified[]`.
>
> **Absence of the canonical mitigation pattern is NEVER a `fail` criterion.**
> **Failure to recognise the developer's mitigation style is NEVER a `fail` criterion.**
> **If Q1 is `absent_high_confidence` and the marker scan is clean, the verdict is `pass` — regardless of Q2 (canonical mitigation match) and Q3 (alternative mitigation recognition).**
> **An empty or partially populated `ctx.how_tos[]` is NOT a degraded path. Q2 is OPTIONAL — it runs only when `ctx.how_tos[]` is non-empty AND has at least one language-applicable entry. Otherwise Q2 is skipped entirely and the matrix collapses to Q1 + Q3 + marker scan; `Q1 = absent_high_confidence` + clean markers yields `pass`/`high` regardless of whether Q2 ran.**
>
> `partial` is reserved for **genuine analysis ambiguity** (Q1 = `ambiguous`: AI cannot determine whether the vulnerability is present — obfuscated code, indirect data flow, partial coverage) and for context-fetch failures (404/5xx/timeout/network). It is **NOT** a substitute for `pass` when the AI is confident no vulnerability exists. `partial` is also the verdict for malformed subagent returns (a parse error is not vulnerability evidence; recording it as `fail` would itself be a false positive).
>
> Q2 (canonical mitigation pattern from `ctx.how_tos`, optional — see above) and Q3 (semantic-equivalence alternative mitigation) are corroborative — they enrich findings and rationale. They do **NOT** gate the verdict.

This callout MUST appear in five places total: three byte-identical full callouts (SKILL.md "No-False-Positives Invariant" section, SKILL.md Step B3 verdict-matrix preamble, this AGENTS.md Rule 5) plus two content-equivalent adaptations (SKILL.md Numbered Enforcement Rules — Rule 5 abbreviated reference; Subagent Prompt Template appendix — plain-text rendering inside a code fence cannot use Markdown blockquote syntax). All five mentions are content-equivalent.

### Rule 6: Residual Markers are a Fail Criterion

If any `files_modified[]` file contains `vuln-code-snippet`, `VULNERABLE`, `INSECURE`, `TODO: fix`, `FIXME: security`, `<!-- VULNERABLE -->`, `# SECURITY ISSUE`, `// TODO: fix`, or similar intentional-vulnerability markers → verdict is `fail` with `high` confidence, regardless of logic. (This is the canonical hardcoded marker list — must match SKILL.md Step B-Subagent input list byte-for-byte.)

### Rule 7: Repository Intent is Irrelevant

As with the upstream skill, "training repo", "intentionally vulnerable", "low priority", "demo", "CTF" are FORBIDDEN rationalizations. Verdicts are a function of code evidence only.

### Rule 8: Fail-Rollback Requires Opt-In

`task_status_mapping: {"fail": "TODO"}` is included in the POST payload ONLY when the user selected `yes_rollback` at Step A4. Default (`no_verification_only`) omits that mapping entirely.

**Hybrid caveat (DONE-on-fail):** in `hybrid`, ZeroPath's scan push has ALREADY auto-marked every mapped CM `DONE` before the skill posts its combined note. With `no_verification_only`, a `fail` verdict therefore records `verification_status=fail` while the task stays `DONE` (a misleading "Done + Failed" state). The A4 prompt MUST surface this for hybrid and prefer `yes_rollback`. (Not applicable to `ai` — never pre-marks DONE — or `zeropath` — posts no skill note.)

`task_status_mapping: {"pass": "DONE"}` is ALWAYS included.

### Rule 9: Per-CM Verification Runs in Batched `generalPurpose` Subagents (or Inline Fallback)

When `execution_mode == "subagent"`, the parent loop is a pure orchestrator (it dispatches work but does not run B1/B2/B3/B4/B5 itself); when `execution_mode == "inline"`, the parent loop both orchestrates short-circuits and executes B1/B2/B3/B4/B5 in-context (see inline fallback below). **Handoff mode:** CMs that survive the parent forced short-circuits (B0a Documented OOS, B0b upstream-Skipped forced-fail, and — when `handoff_version == "2"` — B0b2 code-CM empty-files forced-fail, B0b3 non-code-CM empty-files OOS) and are not skipped via `one_by_one`'s `skip`/`stop` are grouped into batches. **Standalone mode:** all post-filter CMs pass through (no handoff-derived short-circuits apply). In both modes, batches of `batch_size` CMs (default 10, configurable in Step A5) are formed. When `execution_mode == "subagent"`, each batch is dispatched to **one `generalPurpose` subagent**, which processes its CMs sequentially — performing B1 (fetch), then B1.5 (handoff mode short-circuits) or B1.7 (standalone mode file discovery), then B2 (AI analysis via `read_file`), B4 (fetch existing notes for read-then-append preservation), and B5 (POST via `verification op=create`) for each CM — and returns a **JSON array** of per-CM results. Up to 5 batches may be dispatched in parallel per round. When `execution_mode == "inline"`, batches are `batch_size=1` and processed sequentially in-context (see inline fallback below).

**Inline fallback (Step A6):** When the MCP client does not support subagent generation (`execution_mode == "inline"`), B1/B2/B3/B4/B5 run inline in the parent context with `batch_size=1`, no parallel dispatch, and a mandatory `=== CONTEXT CHECKPOINT ===` every 5 CMs. The agent warns the user about context-window limits: `[WARN]` if `in_scope_total > 20` (context exhaustion likely — consider reducing scope), and a `[HARD RECOMMEND]` if `in_scope_total > 50` (strongly recommend `selected_cms` with max ~20 CMs, or `one_by_one` mode). **The "reduce scope" remediation is `scan_engine == "ai"` ONLY; for `hybrid`, scope is fixed to `all` (R-ZP10) and CANNOT be reduced — the run checkpoints every 5 CMs and resumes across turns instead (or runs in a non-Cursor client for parallel subagents).** This is one of two valid exceptions to the subagent-only rule; the other is the forced-fail POST exception below. Inline fallback activates ONLY when the subagent `model` cannot be set to the parent's model (SUBAGENT/DELEGATION POLICY) — it is not forced by environment. All inline fallback infrastructure (batch_size=1, context checkpoints, Rule 9 relaxation) applies identically.

**Forced-fail POST exception:** Parent B0b (upstream-Skipped) and B0b2 (code CM with empty `files_modified[]`, handoff v2) run B4 (fetch existing notes) + B5 (POST verification note) inline in the parent after recording the forced-fail verdict. These CMs never enter the subagent pipeline (they are consumed by parent short-circuits before batching), so this is a scoped exception to the pure-orchestrator rule. The POST ensures forced-fail rework candidates have visible notes in the SDE UI with upstream context preserved. Subagent L-FF2-sub (handoff v1) performs the same B4+B5 POST inside the subagent. **In `hybrid` mode these forced-fail lanes DEFER the POST (`note_post_status="DEFERRED_HYBRID"`) and contribute their `ai_status="fail"` to the single combined note posted in Phase B-HYB (R-ZP3), rather than posting inline.**

**Retry/timeout:** If a subagent does not return within `subagent_timeout_ms` (default 300000 = 5 minutes), the parent kills it and re-launches the same batch (up to `max_retries=2` retries, 3 total attempts). After exhaustion, every CM in the batch is recorded as `partial`/low with `subagent-timeout` finding. A timeout is not vulnerability evidence.

**Subagent contract (non-negotiable):**

- Type MUST be `generalPurpose` (NOT `explore` — `explore` is readonly and cannot call MCP).
- Prompt MUST be rendered from the canonical Subagent Prompt Template appendix in `SKILL.md` with placeholders substituted (`batch[]` array of CM descriptors, `verification_mode`, `repository_path`, `project_id`, `security_branch`, `task_status_mapping_opt_in`). **Handoff mode:** when `handoff_version == "1"`, `cm.category` is not available — the subagent fetches it live from SDE in B1 and uses it in B1.5 to dispatch L-FF2-sub or L-OOS-sub. When `handoff_version == "2"`, `cm.category` is in the handoff and the parent uses it for B0b2/B0b3 parent-side short-circuits before batching; CMs that still reach a subagent have already survived those checks, and the subagent's B1.5 acts as a redundant guard. **Standalone mode:** B1.5 is skipped; the subagent runs B1.7 (file discovery) instead.
- Prompt MUST include the batch iteration procedure, the verbatim No-False-Positives Invariant, B-Sub procedure, B3 verdict matrix, hardcoded marker list, and strict JSON array return schema. Drift from the verbatim template is a contract violation.
- Subagent return MUST be a strict JSON **array** with exactly `len(batch)` elements. Parent MUST validate (array length, per-element `full_id` match, schema conformance).
- Malformed return (entire batch) -> parent records every CM in batch as `partial`/`low`/`analysis-uncertain` with `note_post_status="FAILED:subagent-malformed"`. Never `fail`.
- Malformed individual element -> parent records that CM as `partial`/`low`/`analysis-uncertain`; other CMs in the batch use their own parsed results.
- Timeout (all retries exhausted) -> parent records every CM in batch as `partial`/`low`/`subagent-timeout` with `note_post_status="FAILED:subagent-timeout"`. Never `fail`.
- `auth_failure: true` (any element) -> parent stops dispatching further ROUNDS (records the auth-failure CM with `NOT_SENT_AUTH_FAILURE`, records every unreached CM — the rest of this batch + all batches in subsequent rounds — via `record_skipped` (deduped by `full_id`); sibling batches already returned in the SAME round keep their real verdicts; surfaces "Refresh credentials and re-run"). The subagent's strict-JSON return schema requires `verdict` to be present even when `auth_failure: true`: for B1 401/403 the subagent MUST set verdict `partial`/`low` with one `context-fetch-failed` finding; for B5 401/403 the subagent MUST emit the verdict already determined in B3.

**Forbidden (when `execution_mode == "subagent"`):** running B1 fetch, B2 analysis, B3 verdict, B4 note-fetch, or B5 POST inline in the parent context for any in-scope CM. The parent's own context budget is preserved by delegation to batched subagents. (When `execution_mode == "inline"` — Step A6 fallback — B1/B2/B3/B4/B5 run inline with batch_size=1 and context checkpoints; see Rule 9 "Inline fallback" paragraph above.) Additional exception: parent B0b/B0b2 forced-fail short-circuits run B4+B5 inline; see the "Forced-fail POST exception" paragraph.

### Rule 10: API Payload + Concept Model Conform to SDE Spec

The Verification Note payload and the surrounding concept model MUST match the official SDE documentation. Specifically:

- **`behaviour`** MUST be one of `combine` / `replace-scanner` / `replace`. `append` is NOT a valid value (was never documented at any release). This skill uses `combine`.
- **`findings[]`** elements MUST include both `desc` and `count` keys (per the [API spec](https://docs.sdelements.com/master/api/docs/analysis-notes/)). Every `desc` value MUST begin with `[AI-SAST via Code Scan Verification Validation | {model}]` and end with `| verdict={verdict} confidence={confidence}` (see SKILL.md Step B3 aggregation table for templates). Findings are aggregated by category for the SDE payload; per-location detail goes in the local handoff.
- **`fail` verdicts MUST emit at least one finding** (spec-required for automatic verification; this skill extends to manual verification too).
- **`finding_ref`** MUST use the `Agent: code-scan-verification-validation | Model: {model} | Repo: {repo_name} | CM: {full_cm_id} | Run: {iso8601_utc} | Handoff: .sde-verification-handoff.json` format. `{repo_name}` is the basename of `repository_path`, captured in Phase A and forwarded to subagents.
- **Verification status** (`pass` / `partial` / `fail` / `none`) and **countermeasure (task) status** (`TODO` / `DONE` / `NA`) are **separate** SDE resources. Never use one term to refer to the other.
- **Notes without `analysis_session` are Manual Verification by design.** Do NOT mint a synthetic `analysis_session` ID — without a registered SDE Verification Connection plugin, SDE will reject the request.
References: [SD Elements Verification Notes API](https://docs.sdelements.com/master/api/docs/analysis-notes/), [Verification status (User Guide)](https://docs.sdelements.com/master/guide/docs/integrations/security_tools/overview/verification_status.html), [Verification Statuses API](https://docs.sdelements.com/master/api/docs/verification-statuses/), [Task Statuses API](https://docs.sdelements.com/release/2023.2/api/docs/task-statuses/).

---

## ZeroPath / Hybrid Engine Rules (R-ZP1 – R-ZP11)

These rules apply ONLY when `scan_engine in {"zeropath","hybrid"}` and are **strictly additive** — they NEVER weaken any rule above. The AI verdict engine and Rules 1-16 / all Forbidden Behaviors apply unchanged to `scan_engine == "ai"` and to the AI half of `hybrid` (the only delta in hybrid is R-ZP3's deferred B5). Engine scope is noted per rule.

- **R-ZP1 — Preflight + tenant-match (both):** Before A0.5, run Step A0-ZP. HARD STOP if sdelements/zeropath/securitycompass is unreachable or unauthenticated, if no `enabled` integration exists, or if `host(getIntegration.sdeBaseUrl) != host(SDE_HOST)`. No scan may run until preflight passes.
- **R-ZP2 — ZeroPath-Only posts no notes (zeropath):** The skill MUST NOT call `verification op=create`. ZeroPath's native push owns SDE verification/task status; the skill only triggers, waits, and reports.
- **R-ZP3 — Hybrid deferred POST → one combined note (hybrid):** The AI per-CM loop MUST defer B5 (return the verdict, set `note_post_status="DEFERRED_HYBRID"`, do NOT POST) — this INCLUDES the parent forced-fail lanes (B0b upstream-Skipped, B0b2 empty-files code CM), which in hybrid record `DEFERRED_HYBRID` + `ai_status="fail"` instead of posting inline. (NOTE: under `zeropath`/`hybrid`, R-ZP10 forces `scope="all"`, and the `all` filter EXCLUDES `Skipped` CMs — so **B0b (upstream-Skipped) is unreachable for these engines; only B0b2 (Applied code CM with empty `files_modified[]`, which passes the `all` filter) actually fires**. The B0b lane is retained only for `selected_cms` parity with the AI engine, which R-ZP10 makes AI-only.) After the push lands, the PARENT posts exactly ONE combined `verification op=create` note per in-scope CM that holds a `DEFERRED_HYBRID` disposition, finalizing each entry's status to the merged verdict (no entry may retain `DEFERRED_HYBRID` in the written handoff). CMs the AI loop recorded as skipped / skipped_out_of_scope keep their disposition (no combined note). The AI loop never double-posts.
- **R-ZP4 — Append, never overwrite (hybrid):** The combined note MUST use `behaviour="combine"` (the SDE append-equivalent). `replace` / `replace-scanner` are FORBIDDEN (they clobber ZeroPath's note); literal `append` is not a valid SDE value. Run B4 `verification op=list` first to preserve prior notes.
- **R-ZP5 — Async-push gate (both):** Before reading ZeroPath's per-CM SDE note (hybrid) or reporting push stats (zeropath), WAIT for `getSyncHistory` to show `security_compass.push status=success` scoped to THIS run — match on `scanId` AND `sdeProjectId` AND `mappingId`, NOT `scanId` alone. One `scanId` fans out to EVERY SDE project mapped to the repo, so a SIBLING project's push success would satisfy a scanId-only predicate and cause reading stale/empty ZP notes for the WRONG project (observed live: a sibling project's push reached success ~9 min before this project's push even started). PAGINATE `getSyncHistory` (do NOT cap at `limit=10`) — with N mapped projects each emitting started+success (+rule_sync) events, this project's success row can be past the first page. The push is asynchronous and lags scan-Finished.
- **R-ZP6 — Scan side-effect warning (both):** Before `scans_start`, emit `[WARN] A ZeroPath scan will auto-update mapped CM statuses in SDE project {sdeProjectId}.` and include it in the A7 execution plan. A scan mutates SDE.
- **R-ZP7 — Scanned-commit correctness is governed by R-ZP11 (both):** branch/commit correctness is asserted at A-ZP1.6 and post-scan via `scanTargetBranchCommitSha == scan_branch_remote_sha` (the verified-pushed tip). Do NOT compare `scan.commitSha` against local `git rev-parse HEAD` — `scan_branch` may legitimately differ from the checked-out branch in ZeroPath-Only, so a local-HEAD compare would false-WARN. Optionally read the scanned snapshot via zeropath `code_read`/`code_search`.
- **R-ZP8 — Dedicated tools + direct-API for reference endpoints (both):** use the dedicated tools (`project`, `project_countermeasures`, `verification`, `library_search`). For a reference endpoint with no dedicated tool, use a direct-API call with `Authorization: Token` (a script when there's anything to reconcile, else a one-line curl) against the absolute `https://$SDE_HOST/api/v2/...` URL. (Historical note: earlier client builds double-prefixed a full path passed to `api_request` and returned SPA HTML; the current tool instead REQUIRES a server-relative `/api/<segment>/` path and rejects relative paths/query strings — see CHANGELOG "Harden the generic `api_request` tool". Either way, prefer dedicated tools + direct-API here rather than `api_request`.)
- **R-ZP9 — Weak-pass (pass-by-absence) WARN gate (zeropath; also hybrid when a ZeroPath pass-by-absence sets `final`):** After the push, for every CM where ZeroPath marked DONE with 0 issues mapped to it, emit the plain-English `[WARN] Weak pass — {full_cm_id} "{title}": ZeroPath scanned and found no violation, but "no violation found" is NOT proof the control is in place. ZeroPath auto-marked this Done. Treat as unverified until AI/human confirms the control exists.` line and surface the count in the completion block. In hybrid this fires only when `authoritative_source == "zeropath"` (the weak ZeroPath pass actually sets the verdict; when AI is authoritative the AI verdict governs). The run still COMPLETES (ZeroPath-Only is the trust-ZeroPath engine) — a loud label, not a block.
- **R-ZP10 — Force all CMs (zeropath|hybrid):** these engines ALWAYS verify all mapped/Applicable CMs. Step A1.5+A3 (resume + scope) is **SKIPPED**; `scope` is force-set to `"all"`, `scope_args = {}`, `has_prior_run = false` (no resume). Narrow scopes (`one_cm` / `selected_cms` / `one_by_one`) and the B0c `one_by_one` prompt are UNAVAILABLE for these engines — they are AI-engine-only. `in_scope_total` for zeropath/hybrid is the full mapped/Applicable CM set. To verify a curated subset, the user must choose `scan_engine == "ai"`.
- **R-ZP11 — Scan branch must be committed + pushed to the ZeroPath remote (zeropath|hybrid):** ZeroPath scans a branch on the remote it clones (`repositories_list.vcs.url`), defaulting to the repo default branch (usually `main`) — NOT the local working branch. At Step A-ZP1.6 the skill MUST (a) ask the user which `scan_branch` to scan, and (b) verify it is committed (`git status --porcelain` empty of SOURCE changes — scoped to exclude the skill's own `.sde-security/` scratch and `.sde-verification-handoff.json`) and pushed (`git ls-remote --heads {vcs.url} {scan_branch}` present AND remote tip == local HEAD). If the branch is missing on the remote, or has uncommitted/unpushed commits → **HARD STOP** instructing the user to `git push -u origin {scan_branch}` (NO PR required). The skill MUST NOT push on the user's behalf. `scans_start` MUST pass `branch=scan_branch`, and after the scan the skill MUST assert `scanTargetBranch == scan_branch` and `scanTargetBranchCommitSha == scan_branch_remote_sha` (else WARN: branch not pushed / push lagged). This prevents ZeroPath silently verifying stale `main`. **Hybrid coherence:** for `hybrid`, `scan_branch` defaults to and MUST equal A2's checked-out `branch_name` (the AI loop reads local files on that branch); HARD STOP on mismatch so the AI loop and ZeroPath verify the SAME code (ZeroPath-Only has no AI loop, so any branch is allowed).

**Signal-source rule (hybrid):** the per-CM ZeroPath verdict MUST be read from ZeroPath's OWN SDE verification note (`verification op=list`, keyed by `task_id`) — NOT from securitycompass aggregate counts (which expose only totals). **ZeroPath-native notes have an EMPTY `finding_ref`; the skill's own notes start with `Agent: ...`. The ZP signal is the latest note with `finding_ref == ""` — a bare `.latest()` is FORBIDDEN because on a re-run the skill's own combined note is newest and would be misread as ZeroPath's signal.** `count:0` = pass-by-absence. The ZeroPath issue link (for `fail` notes) is correlated via `vulnerabilities_search`/`endpoints_search` → `issues_get.url` and is LINK-ONLY (never sets the verdict).

---

## Completion Criteria

This skill is NOT complete until ALL of the following are true:

- [ ] Scan engine selected (Step A0.0): `ai` | `zeropath` | `hybrid`
- [ ] **zeropath|hybrid:** Step A0-ZP preflight passed (sdelements+zeropath+securitycompass reachable; integration enabled; tenant match) and Step A-ZP1 setup done (repo resolved, mapping reused/added, syncRules ok, getMappingAudit read, **scan_branch chosen + verified committed+pushed to the ZeroPath remote — R-ZP11**); **hybrid:** A-ZP2 authoritative source chosen
- [ ] **zeropath|hybrid:** the scan ran on `scan_branch` (`scanTargetBranch == scan_branch` and `scanTargetBranchCommitSha == scan_branch_remote_sha`) — NOT a stale default branch
- [ ] **zeropath engine:** scan Finished + `security_compass.push status=success` confirmed; skill posted ZERO `verification op=create` notes; pass-by-absence WARN gate run; ZeroPath-Only completion block emitted with Gate=YES
- [ ] **hybrid engine:** scan reconciled + push confirmed; AI loop ran with B5 deferred; exactly ONE combined note per in-scope CM (`behaviour=combine`); Sum-check + combined-note posted-coverage (re-derived from SDE) + APPEND check all YES
- [ ] MCP connection verified
- [ ] Mode selected (Step A0.5): `handoff` or `standalone` (or `enter_project`); repository path confirmed
- [ ] **Handoff mode:** `.sde-apply-handoff.json` loaded, validated, and user-confirmed
- [ ] **Standalone mode:** SDE project selected; CMs fetched; status filters applied; user confirmed
- [ ] `git status --porcelain` returned empty BEFORE any checkout
- [ ] Branch checked out (handoff: `security_branch` if present; standalone: user-selected or current)
- [ ] Risk policy displayed and confirmed by the user (Step A1.6)
- [ ] **(ai engine)** User answered Step A1.5+A3 (resume + scope; for `one_cm`/`multi_cm`, CM IDs collected immediately); **(zeropath|hybrid)** A1.5+A3 skipped, `scope == "all"` (forced, R-ZP10). Plus Step A4 (fail-rollback) for all engines, and Step A5 (batch size — auto-set to 1 for single-CM scope, otherwise user-selected or default 10) for `ai`/`hybrid` only (**SKIPPED for `zeropath`** — no AI loop, `batch_size = "n/a"`)
- [ ] Subagent capability probed (Step A6); `execution_mode` set to `subagent` or `inline`
- [ ] Phase A verification block output with `MATCH = YES`; user confirmed execution plan (Step A7)
- [ ] Every in-scope CM has: SDE context fetched, relevant files read, verdict derived, existing notes fetched via B4 (POST-eligible CMs only — user-skipped and Documented-under-`selected_cms` CMs are recorded without fetch/read)
- [ ] Every in-scope CM has a recorded result entry: a Verification Note POST attempt (POSTED or FAILED with recorded cause) for POST-eligible CMs; a `record_skipped` / `record_out_of_scope` entry for the no-POST classes — no CM is silently dropped
- [ ] `.sde-verification-handoff.json` written to repository root
- [ ] Completion verification block output with `Sum check = YES`
- [ ] **Posted-note coverage re-derived from SDE** (`verification op=list` per POST-eligible CM, matched on `finding_ref`) == NP — NOT trusted from the in-memory results array; no sampling (`ai`/`hybrid`)
- [ ] **Terminal verification (T9): all 3 layers YES** — Layer 1 (inline re-derive from `.sde-security/verify/<project_id>/cm-work/*.json` + run-marker + surviving-output), Layer 2 (`verify_disk_vs_sde(in_scope_total, in_scope_ids)` exits 0), Layer 3 (tri-source: SDE == disk artifacts == handoff rows == in_scope_total)
- [ ] **Handoff mode:** `.sde-apply-handoff.json` was NOT modified or deleted

---

## MANDATORY GATE REGISTRY

Every gate below MUST appear during a run (engine-gated as noted); the final audit cross-checks each as FOUND/MISSING.

| Gate | Where | Pass condition |
|------|-------|----------------|
| G1 — Phase A MATCH | Step A7 | `inputs gathered == expected` (dynamic per engine×mode); user confirmed the plan |
| G2 — Per-batch mini-gate (`ai`/`hybrid`) | Phase B AI loop, each batch | `[VERIFY] count == disk artifacts == expected(batch)` before advancing (T5) |
| G3 — Gate-the-gate (`ai`/`hybrid`) | Phase B completion | BATCH PLAN emitted AND a mini-gate per batch (count == total batches) |
| G4 — Sum-check | Completion block | `P + PT + F + S + S_oos == canonical_total` (Anchoring Rule; canonical_total = in_scope_total fresh / already_done + in_scope_total on resume) |
| G5 — Posted-note coverage (`ai`/`hybrid`) | Completion block | re-derived from SDE (`verification op=list`, match `finding_ref`) == NP |
| G6 — Layer-2 verify script | Terminal verification | `verify_disk_vs_sde(in_scope_total, in_scope_ids)` exits 0 |
| G7 — Layer-3 tri-source | Terminal verification | SDE in-scope set == disk artifacts == handoff rows == in_scope_total |
| G8 — R-ZP11 branch verify (`zeropath`/`hybrid`) | A-ZP1.6 + post-scan | `scan_branch` committed+pushed; `scanTargetBranchCommitSha == scan_branch_remote_sha` |
| G9 — Scan Finished + push success (`zeropath`/`hybrid`) | Phase B-ZP/B-HYB | `scans_get status=Finished` AND `getSyncHistory security_compass.push status=success` |
| G10 — APPEND check (`hybrid`) | Phase B-HYB completion | `verification op=list` shows ≥2 notes per in-scope mapped CM (ZeroPath's + combined) |
| G11 — Pass-by-absence WARN (`zeropath`; `hybrid` when ZP-authoritative) | Phase B-ZP / merge | weak-pass WARN emitted + counted for each CM marked DONE with 0 issues mapped (R-ZP9) |

---

## Mandatory Outputs

### Progress Checkpoints

| After | Required Output |
|-------|-----------------|
| MCP verified | `[CHECKPOINT] MCP connection successful` |
| Scan engine selected (A0.0) | `[CHECKPOINT] Scan engine: {scan_engine}` |
| Preflight OK (A0-ZP; zeropath\|hybrid) | `[CHECKPOINT] Preflight OK: sdelements + zeropath + securitycompass reachable; tenant match {host}` |
| ZeroPath setup (A-ZP1; zeropath\|hybrid) | `[CHECKPOINT] ZeroPath setup: project {sdeProjectId} <-> repo {repo_name} ({repositoryId}); mapping {mappingId}; sync {sastDetectable} sast / {rulesCreated} rules; supported {supportedCount}/{totalCount}; scan_branch={scan_branch} @ {scan_branch_remote_sha} (pushed)` |
| Branch not pushed (A-ZP1.6; zeropath\|hybrid) | HARD STOP: `Branch {scan_branch} is not on the ZeroPath remote {vcs.url}. Push it: git push -u origin {scan_branch} (no PR). ZeroPath cannot scan an unpushed branch.` |
| Hybrid inputs (A-ZP2; hybrid) | `[CHECKPOINT] Authoritative source: {authoritative_source}; scan polling: every 1 min (30-min default cap)` |
| Scan started (zeropath\|hybrid) | `[CHECKPOINT] ZeroPath scan started: {scanId} (branch {scanTargetBranch} @ {commitSha})` + `[WARN]` if `scanTargetBranch/commit != scan_branch @ scan_branch_remote_sha` (R-ZP11) |
| Scan finished (zeropath\|hybrid) | `[CHECKPOINT] ZeroPath scan {scanId} status=Finished` (poll every 1 min; 30-min default cap -> `scans_cancel` + HARD STOP) |
| Push landed (zeropath\|hybrid) | `[CHECKPOINT] ZeroPath push success for scan {scanId} (markedDone {D}, issuesMapped {M}, unmapped {U})` |
| Weak pass / pass-by-absence (zeropath; hybrid when ZP-authoritative) | `[WARN] Weak pass — {full_cm_id} "{title}": ZeroPath scanned and found no violation, but "no violation found" is NOT proof the control is in place. ZeroPath auto-marked this Done. Treat as unverified until AI/human confirms the control exists.` |
| Hybrid combined note (hybrid) | `[VERIFY] {done}/{total} \| {full_cm_id} \| ai={ai_status} zp={zp_status} -> {final} \| note={POSTED\|FAILED:{reason}}` |
| Mode + repo selected (A0.5) | `[CHECKPOINT] Mode: {verification_mode}; repository: {repository_path}` |
| Handoff loaded (handoff mode) | `[CHECKPOINT] Handoff loaded: {N} CMs ({A}/{D}/{S}) from apply-security-fixes` |
| Standalone CMs fetched (standalone mode) | `[CHECKPOINT] Standalone mode: {N} countermeasures fetched from project {project_name} (ID: {project_id}) \| task_status_filter: {filter} \| verification_filter: {filter}` |
| Risk policy confirmed (A1.6) | `[CHECKPOINT] Risk policy: {policy_name} (ID: {policy_id}) — confirmed` (or `Risk policy: (none set) — confirmed`) |
| Resume + scope status (A1.5+A3; ai engine) | `[CHECKPOINT] Resume: {already_done} CMs from prior run; {still_todo} remaining` OR `Resume: starting fresh` followed by `[CHECKPOINT] Scope: {scope}` |
| Scope forced (A1.5+A3 skipped; zeropath\|hybrid) | `[CHECKPOINT] Scope forced to all (scan_engine={scan_engine} verifies all mapped/Applicable CMs); A1.5+A3 resume/scope questions skipped.` |
| Git + branch | `[CHECKPOINT] Git tree clean; checked out {branch_name}` |
| Scope + rollback | `[CHECKPOINT] Scope: {scope}; fail-rollback: {yes_rollback \| no_verification_only}` |
| Batch size (A5; ai/hybrid) | `[CHECKPOINT] Batch size: {batch_size}; parallel subagents: 5` — zeropath: `[CHECKPOINT] Batch size: n/a (ZeroPath-Only has no AI loop)` |
| Subagent probe (A6) | `[CHECKPOINT] Execution mode: {subagent \| inline}` |
| Phase A verified + user confirmed plan (A7) | `[CHECKPOINT] Phase A complete: {count}/{expected} inputs gathered; user confirmed execution plan` |
| Empty in-scope set (after `filter_by_scope`) | `[INFO] No in-scope CMs after filtering. Nothing to verify; writing empty handoff.` |
| Batch subagent dispatched | `[VERIFY-DISPATCH] batch {batch_num}/{total_batches} | {N} CMs: [{cm_ids}] | subagent launched` |
| Each CM (normal subagent return) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict={...} | confidence={...} | note={POSTED\|FAILED:{reason}}` |
| Forced fail — B0b (upstream Skipped) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict=fail | confidence=high | note={POSTED\|FAILED:{reason}}` |
| Forced fail — B0b2 (code CM, empty `files_modified`, v2) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict=fail | confidence=high | note={POSTED\|FAILED:{reason}} (parent B0b2)` |
| Malformed subagent return (batch) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict=partial | confidence=low | note=FAILED:subagent-malformed` (per CM) |
| Subagent timeout (all retries exhausted) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict=partial | confidence=low | note=FAILED:subagent-timeout` (per CM) |
| Auth failure (any subagent's 401/403) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict={...} | confidence={...} | note=NOT_SENT_AUTH_FAILURE` followed by `[STOP] Auth failure at {full_cm_id}; aborted run; recorded {N} unreached CMs to preserve Sum-check identity. Refresh credentials and re-run.` |
| Documented CM under `selected_cms` (parent B0a) | `[SKIP-OOS] {done}/{in_scope_total} | {full_cm_id} | out-of-scope (Documented)` |
| Parent B0b3 (non-code CM, empty `files_modified`, v2) | `[SKIP-OOS] {done}/{in_scope_total} | {full_cm_id} | out-of-scope (parent B0b3: {category}, empty files_modified)` |
| Subagent L-OOS-sub (non-code CM with empty `files_modified[]`, v1) | `[SKIP-OOS] {done}/{in_scope_total} | {full_cm_id} | out-of-scope (subagent L-OOS-sub: {reason})` |
| User skip in `one_by_one` | `[SKIP-USER] {done}/{in_scope_total} | {full_cm_id} | user skipped` |
| User stop in `one_by_one` | `[STOP] User stopped at {done}/{in_scope_total}; recorded {N} CMs as user-stopped to preserve Sum-check identity` |
| Own handoff | `[CHECKPOINT] Verification handoff written: .sde-verification-handoff.json ({N} records)` |
| Completion | Verification block (see below) + `✅ COMPLETION GATE PASSED` |

### Completion Verification Block (REQUIRED)

```
=== COMPLETION VERIFICATION ===
Skill: code-scan-verification-validation
MCP connection: ✓
Mode: {verification_mode}
CM source:
  (handoff)    Handoff loaded: ✓ ({N} CMs)
  (standalone) SDE project: ✓ ({project_name}, {N} CMs)
Git tree safety: ✓
Scope: {scope}
Fail-rollback opt-in: {yes_rollback | no_verification_only}

Per-CM verdicts (SDE UI labels):
- Pass:                  {P}
- Partial Pass:          {PT}
- Fail:                  {F}
- Skipped (user):        {S}
- Skipped (out of scope): {S_oos}

Verification Notes:
- POSTED: {NP}
- FAILED: {NF}  (IDs: {list or "none"})

Own handoff written: ✓ (.sde-verification-handoff.json)
Upstream handoff:
  (handoff)    preserved: ✓ (.sde-apply-handoff.json untouched)
  (standalone) N/A

Sum check: {P + PT + F + S + S_oos} == {canonical_total}? {YES/NO}   (canonical_total = in_scope_total fresh; = already_done + in_scope_total on resume)
Posted-note coverage (re-derived from SDE via verification op=list, matched on finding_ref) == NP? {YES/NO}
===============================
```

Print the line matching the current `verification_mode`; omit the other.

### Gate Logic

**If `Sum check = NO` OR posted-note coverage `= NO` OR `NF > 0` with no recorded cause:**
```
INCOMPLETE: retry failed notes / reconcile from SDE, or explain NF cause before declaring complete.
```

**If `Sum check = YES`:**
```
✅ COMPLETION GATE PASSED
Verified {P} Pass / {PT} Partial Pass / {F} Fail / {S} Skipped (user) / {S_oos} Skipped (out of scope)
Rework candidates: {F} (see .sde-verification-handoff.json → failed_cms_for_rework)
```

### Engine-specific completion gates (the block above is the `ai` engine)

The completion block + gate above apply to `scan_engine == "ai"` and to the AI-verdict portion of `hybrid`. The two ZeroPath engines use the engine-specific blocks defined in SKILL.md (`Phase B-ZP` / `Phase B-HYB`), mirrored here:

- **`zeropath` gate:** scan `status=Finished` AND `security_compass.push status=success` (re-derived from `getSyncHistory`). Report `countermeasuresMarkedDone / issuesMapped / unmapped`, coverage, and the **pass-by-absence count** (R-ZP9). The skill posts NO notes, so there is NO per-note coverage line. Gate = (Finished AND push success). On YES → `✅ COMPLETION GATE PASSED (ZeroPath-Only)` + recommend Hybrid for pass-by-absence CMs.
- **`hybrid` gate:** Sum-check `P+PT+F+S+S_oos == in_scope_total` (over in-scope CMs) AND combined-note posted-coverage re-derived from SDE (matched on the `Engine: hybrid` `finding_ref`) == NP AND **APPEND check** (`verification op=list` shows ≥2 notes per in-scope mapped CM: ZeroPath's + the combined). On all YES → `✅ COMPLETION GATE PASSED (Hybrid)`.

---

## SDE API Contract

### Verification Note Endpoint

```
verification op=create project_id={project_id} task_id={full_cm_id} behaviour=combine confidence={...} status={...} findings=[...] finding_ref={...} task_status_mapping={...}
```

Invoked via the `verification` MCP tool (`op=create`). The specialised `project_countermeasures` tool (including `op=update`) does NOT expose `verification_status` for writes; that field is derived from analysis notes.

**`full_cm_id` format:** The `verification` tool auto-normalizes `task_id` via `normalizeProjectTaskId()` — it accepts `"T123"`, `"123-T123"`, `42`, etc. The handoff stores the full form (`full_id`, e.g. `"31768-T123"`); using it verbatim is recommended for clarity but no longer causes a 404 if a bare slug is passed.

**SDE Verification Type (CRITICAL):** Notes from this skill are posted **without** an `analysis_session` field, so SDE classifies them as **Manual Verification** (`automatic: false` on the resulting note). This is by design — the AI agent is not a registered SDE Verification Connection plugin. Reference: [Verification status (User Guide)](https://docs.sdelements.com/master/guide/docs/integrations/security_tools/overview/verification_status.html). Do NOT add a fake `analysis_session` ID to fake automatic mode; without a registered plugin, SDE will reject the request.

**Out-of-scope CMs — Handoff Mode (CRITICAL):** No POST is sent for any CM whose `cm.status == "Documented"` in `.sde-apply-handoff.json`. These are filtered out of `all` / `one_by_one` scopes before the loop and only enter via explicit user inclusion in `selected_cms`, where Step B0a (in the parent loop) short-circuits them as `skipped_out_of_scope` before any subagent dispatch. SAST scanners follow the same convention: they don't acknowledge what they cannot scan.

### Payload Template

```json
{
  "behaviour": "combine",
  "confidence": "high | low",
  "status": "pass | partial | fail",
  "findings": [
    { "desc": "[AI-SAST via Code Scan Verification Validation | {model}] {category-specific detail} | verdict={verdict} confidence={confidence}", "count": "1" }
  ],
  "finding_ref": "Agent: code-scan-verification-validation | Model: {model} | Repo: {repo_name} | CM: {full_cm_id} | Run: {iso8601_utc} | Handoff: .sde-verification-handoff.json",
  "pinned": false,
  "task_status_mapping": {
    "pass": "DONE"
    // "fail": "TODO"  ← only if user opted in at Step A4 AND current verdict is fail
  }
}
```

- `behaviour: "combine"` — the SDE spec's "combine with all previous results" mode. Preserves prior verification notes (the audit trail) while adding the new one. NOTE: with `combine`, SDE's derived `verification_status` is computed across the COMBINED set and is **fail-dominant** — a prior `fail` is NOT cleared by a newer `combine` `pass` note; it is NOT simply "the most-recent note wins" (a `behaviour=replace` note, e.g. ZeroPath's per-scan push, is what resets the baseline so the latest scan wins). Reason about re-run/resume status accordingly. (`append` is NOT a valid SDE behaviour value; the only allowed values are `combine` / `replace-scanner` / `replace`.)
- `findings` are **aggregated by category** for the SDE payload; each element MUST include `desc` and `count` per the SDE spec. Per-location detail is preserved in `.sde-verification-handoff.json` (see `verification_results[].findings[]`).
- A `fail` verdict MUST emit at least one finding (spec-required for automatic verification; we extend to manual too).
- `finding_ref` is the SDE UI's "Report Reference" field. Use the form `Agent: code-scan-verification-validation | Model: {model} | Repo: {repo_name} | CM: {full_cm_id} | Run: {iso8601_utc} | Handoff: .sde-verification-handoff.json` — the primary fields (Agent, Model, Repo) are immediately visible in the SDE UI. The CM and Run fields let a viewer locate the full reasoning in the local handoff file.
- `pinned: false` avoids auto-pinning accumulated notes in the SDE UI. Users may manually pin the latest one if desired.

### Retry / Back-off

| HTTP | Action |
|------|--------|
| 429 | sleep 1s, retry once. On second 429 → `FAILED: rate-limited`, continue loop. |
| 5xx | retry once after 1s, then `FAILED`, continue. |
| 4xx (other) | no retry; `FAILED` with server body; continue. |
| 401 / 403 | no retry; subagent returns `auth_failure: true` with a verdict still populated (B1 401/403 → `partial`/`low` + `context-fetch-failed`; B5 401/403 → the B3-computed verdict); parent HARD STOPs the run, records current CM as `NOT_SENT_AUTH_FAILURE`, records every unreached CM via `record_skipped(c, reason="run aborted: auth failure at ...; not reached")`, surfaces "Refresh credentials and re-run". (Token lacks read or analysis-note write scope; an authenticated continue would silently fail every remaining CM and corrupt totals.) |
| network error | retry once after 1s, then `FAILED`, continue. |

---

## Forbidden Behaviors

| Action | Why Forbidden | Consequence |
|--------|---------------|-------------|
| **Running any external script (Python, shell, JS) to do skill work** | Every step is inline AI work or delegated to a `generalPurpose` subagent | Delete the script; dispatch a subagent or redo inline |
| **Running handoff mode without `.sde-apply-handoff.json`** | No source for `files_modified` in handoff mode | HARD STOP (switch to standalone via A0.5) |
| **Accepting handoff with wrong `source_skill`** | Contract violation | HARD STOP |
| **Auto-proceeding after handoff load or SDE fetch** | User must confirm | Ask before Phase B |
| **Running standalone mode without user selecting SDE project** | No source for countermeasures | HARD STOP |
| **`git checkout` on dirty tree** | Destroys local work | HARD STOP |
| **Overwriting `.sde-apply-handoff.json`** | Upstream audit integrity | Write `.sde-verification-handoff.json` instead |
| **Defaulting to `pass`** | Uncertainty is `partial` | Subagent re-reads files or records `partial` |
| **Defaulting to `fail`** | `fail` needs cited residual evidence (one of four sources — see Rule 5) | Use `partial` with `low` confidence |
| **Marking `fail` because the canonical mitigation pattern was not found** | False-positive vector — Q2 (canonical mitigation match) is corroborative, not gating | Apply the No-False-Positives Invariant; if Q1 is `absent_high_confidence`, verdict is `pass` |
| **Marking `partial` because the developer used a different mitigation style** | Same false-positive vector | If Q1 is `absent_high_confidence` and marker scan is clean, verdict is `pass` regardless of Q2/Q3 |
| **Marking malformed-subagent-output as `fail`** | A parse error is not vulnerability evidence | Record `partial`/`low`/`analysis-uncertain` |
| **Using `project_countermeasures op=update` to set verification status** | Field is read-only there | Subagent uses `verification op=create` |
| **(zeropath\|hybrid) Using the `api_request` tool** | Prefer dedicated tools; `api_request` requires a server-relative `/api/<segment>/` path (historically double-prefixed → SPA HTML) | Dedicated tools; direct-API (curl/script + `Authorization: Token`) shell fallback for reference endpoints (R-ZP8) |
| **(zeropath) Posting any `verification op=create` note** | ZeroPath's native push owns SDE status in ZeroPath-Only | Trigger/wait/report only; post nothing (R-ZP2) |
| **(hybrid) AI loop posting B5 in-loop** | Must produce ONE combined note, not an AI note + a ZeroPath note race | Defer B5 (`DEFERRED_HYBRID`); parent posts the combined note after push (R-ZP3) |
| **(hybrid) Combined note with `replace`/`replace-scanner`** | Would clobber ZeroPath's note | Use `behaviour=combine` + B4 fetch-existing (R-ZP4) |
| **(hybrid) Reading the per-CM ZP verdict from securitycompass aggregate counts** | `getSyncHistory`/`getIntegration` expose only totals, not per-CM | Read ZeroPath's SDE note via `verification op=list` keyed by `task_id` |
| **(zeropath\|hybrid) Calling `scans_start` without the side-effect warning or before preflight passes** | A scan mutates SDE; preflight prevents wrong-tenant push | Emit R-ZP6 warning; run A0-ZP first (R-ZP1) |
| **(zeropath\|hybrid) Scanning without verifying `scan_branch` is committed + pushed to the ZeroPath remote** | ZeroPath silently scans stale `main` / unpushed code, so verdicts reflect the wrong code | A-ZP1.6: ask branch + `git status`/`git ls-remote` verify; HARD STOP instructing `git push -u origin {scan_branch}` (R-ZP11) |
| **(zeropath\|hybrid) The skill auto-pushing or committing the branch on the user's behalf** | The user owns git history + remote credentials | Verify and INSTRUCT only; the user performs the push (R-ZP11) |
| **(zeropath\|hybrid) Reading push results before `security_compass.push status=success`** | Push is async; reads race the push | Wait via `getSyncHistory` (R-ZP5) |
| **Sending `task_status_mapping.fail: TODO` without A4 opt-in** | User did not consent | Omit the fail mapping (subagent uses `task_status_mapping_opt_in` placeholder) |
| **Skipping progress output** | Contract violation | Output `[VERIFY-DISPATCH]` and `[VERIFY]` for every CM |
| **Summary before gate** | Premature completion | Gate must pass first |
| **Declaring completion from the in-memory results array without re-deriving posted-note coverage from SDE** | The loop's own POSTED/FAILED flags are not source-of-truth; a lazy/aborted loop can report counts that don't match SDE | Re-derive posted-note coverage via `verification op=list` (match `finding_ref`) for every POST-eligible CM; no sampling |
| **Agent-initiated early exit** | Only user-initiated paths in `one_by_one` (`skip` per-CM, `stop` loop-terminating) are valid; the involuntary auth-failure abort path is also documented and preserves the Sum-check identity | Continue loop |
| **Declaring complete / emitting "SKILL COMPLETE" after fewer than `in_scope_total` CMs (esp. after the FIRST CM in `one_by_one`)** | The agent hallucinates completion at a per-CM turn boundary; there is no per-CM / single-CM completion state | Continue to the next in-scope CM (or emit a CONTEXT CHECKPOINT); completion is valid ONLY when `running_total == in_scope_total` |
| **Sampling / stopping early via a summary judgment** (any ban-phrase: "key CMs", "representative", "pragmatic", "the rest are", "only N", "N+", "Let me finalize" pre-completion) | The per-CM `[VERIFY]` + per-CM disk artifact count is the ONLY basis for the gate; in-memory tallies and summary judgments are forbidden (T8 anti-sampling; `ai`/`hybrid` AI loop) | STOP, discard the conclusion, return to the BATCH PLAN, process every remaining in-scope CM |
| **Running B1 fetch / B2 analysis / B3 verdict / B4 note-fetch / B5 POST inline in the parent (when `execution_mode == "subagent"`)** | Context-budget contract — parent is a pure orchestrator | Dispatch batched `generalPurpose` subagents. Exception: `execution_mode == "inline"` (Step A6 fallback) runs B1/B2/B3/B4/B5 inline with batch_size=1 and context checkpoints. Additional exception: parent B0b/B0b2 forced-fail short-circuits run B4+B5 inline |
| **Marking subagent-timeout as `fail`** | Timeout is not vulnerability evidence | Record `partial`/low with `subagent-timeout` finding |
| **Skipping the parent forced-fail short-circuit (B0b) before subagent dispatch** | Wasteful and risks subagent re-deriving wrong verdict | Run B0a/B0b BEFORE any subagent launch |
| **Accepting subagent output without JSON-schema validation** | Malformed verdicts corrupt totals | Validate; on parse error record `partial`/`low`/`analysis-uncertain` |
| **Dispatching FURTHER ROUNDS (new subagent launches) after a subagent reports `auth_failure: true`** | Every subsequent subagent will fail identically and corrupt totals | Stop dispatching further rounds; still record same-round sibling batches already returned with their real verdicts; record unreached CMs (rest of this batch + subsequent rounds) as `record_skipped` (deduped by `full_id`), surface remediation |
| **Subagent type other than `generalPurpose`** | `explore` is readonly and cannot call MCP for B1/B5 | Use `generalPurpose` |
| **Subagent prompt that paraphrases or omits the verbatim template** | Drift from the canonical contract is a false-positive vector | Render the Subagent Prompt Template byte-identically |
| **Skipping the residual-marker scan** | Markers are a fail criterion | Always include the marker list verbatim in the subagent prompt |
| **Grep-only verdict** | Grep misses semantics | Subagent must `read_file` + perform AI analysis (Q1/Q2/Q3) |
| **Posting any verdict to a `Documented`-only CM** | SAST convention — nothing on disk to scan after `apply-fixes` deletes `skills/`; UI must show "No Verification Status" honestly | Filter excludes Documented from `all` / `one_by_one` before the loop; under `selected_cms`, Step B0a records `skipped_out_of_scope` for any explicitly-listed Documented IDs; no API call in either case |
| **Requesting elevated shell permissions for local file ops** | Triggers approval prompts that can abort commands | Use default sandbox |
| **Skipping Step A1.5+A3 scope selection or defaulting to `all` without `ask_question`** | User must explicitly choose scope; `all` on a 400+ CM project is expensive and may not be intended | Return to Step A1.5+A3 and present the `ask_question` menu |
| **Inferring scope from the user's chat message instead of using `ask_question`** | Chat-message inference bypasses the structured input contract; the user may have been describing context, not selecting a scope | Present the `ask_question` menu regardless of what the user said |
| **Skipping B4 (fetch existing notes) to save time** | Rich upstream note details will be lost; verification notes will overwrite rather than preserve prior context | Always fetch existing notes before POST; B4 failure is non-fatal but the attempt is mandatory |
| **Spawning a subagent on Composer 2 (`composer-2.5-fast`) or any model other than the parent's** | Composer 2 / weaker models silently abandon CM verification loops, skip CMs, use wrong API endpoints for note POSTs, lose context, and produce unreliable verdicts | Set the subagent `model` explicitly to the parent's model (SUBAGENT/DELEGATION POLICY); in Cursor override the Composer-2 default; if you cannot set the model, run inline |
| **Delegating in a way that lets CMs be silently skipped, or treating delegation as transferring completeness** | The parent ALWAYS re-derives coverage for every in-scope CM from SDE + disk (tri-source) | Delegate only bounded, verifiable batches; every subagent emits `[VERIFY]`/`[PROGRESS]`; the parent verifies every CM against the Sum-check |

---

### Subagent / Delegation Policy -- Detailed Rationale

The same-model / NEVER-Composer-2 policy is enforced because the following failure modes have been **observed in production runs** with Composer 2 / wrong-model subagents:

| Failure Mode | Impact |
|---|---|
| Subagent silently abandoned CM verification loop after ~15 CMs | Remaining CMs left unverified; agent falsely reported completion |
| Subagent skipped CMs and falsely claimed "all verified" | No verification for skipped CMs; silent data loss in handoff |
| Subagent lost context mid-loop | Repeated identical verification; missed CMs entirely |
| Subagent used wrong SDE API endpoint for verification notes | Notes posted to wrong field or silently dropped |
| Composer delegated verification dispatch | Produced unreliable verdicts; missed B4 note preservation |

**Enforcement summary:**
- Subagents MAY be used to reduce context strain in ANY environment (including Cursor), but the subagent `model` MUST be set explicitly to the parent's model — NEVER `composer-2.5-fast` (Composer 2). In Cursor the default subagent is Composer 2, so you MUST override the model.
- If the subagent `model` cannot be set to the parent's model, run inline (`execution_mode = "inline"`, Step A6 fallback).
- The parent ALWAYS owns completeness: re-derive every CM from SDE + disk (tri-source) regardless of who did the work; every subagent emits `[VERIFY]`/`[PROGRESS]` and the parent verifies every item.
- If context limits are hit, checkpoint and resume in a new turn; subagent batching (same-model) or the inline fallback both preserve completeness across turns.
- Composer 2 is FORBIDDEN as a subagent model with **NO exceptions** (override the Cursor default or run inline).
- Inline fallback leverages the existing infrastructure (batch_size=1, context checkpoints, Rule 9 relaxation) when same-model delegation is unavailable.

---

## Input Sources

### Handoff Mode — `.sde-apply-handoff.json`

**Input file:** `.sde-apply-handoff.json` at the user-selected repository root (written by `apply-security-fixes` Step 6.5).

**Out of scope:** `.sde-handoff.json` (written by `generate-security-skill-files`). This skill MUST NOT read, write, rename, or delete that file. It is owned by the upstream skill-generation skill and may be needed again for subsequent `apply-fixes` runs.

**Required keys:**
- `source_skill == "apply-security-fixes"`
- `handoff_version == "1"` or `"2"` (both accepted; `"2"` includes per-CM `category`)
- `repository_path`
- `project_id`
- `countermeasures[]` with per-CM entries

**Required per-CM fields (minimal schema):**
- `id`, `full_id`, `status`, `files_modified[]`
- `sde_note_result` (audit-only — records whether the upstream skill's SDE note was `ADDED`/`FAILED`/`NOT_SENT`; not used for verification logic or short-circuit decisions, but preserved in the handoff for downstream traceability)
- `category` (present when `handoff_version == "2"`; one of `CODE_FIX | ML_CODE | INFRA | ML_DOC`)

**Fields NOT in the handoff (fetched live from SDE):**
- `title`, `domain`, fix text, problem description, how-tos -- all pulled in Step B1 via `project_countermeasures op=get expand=text,problem,tags,how_tos,phase,name`
- `category` is fetched live when `handoff_version == "1"` (field absent); when `"2"`, the parent uses the handoff value for B0b2/B0b3 short-circuits, saving a subagent launch

**Optional fields (used when present):**
- `upstream_handoff`, `security_branch`, `scope`, `totals`

**Checkpoint Output:**

```
[CHECKPOINT] Handoff loaded: {N} CMs ({A} Applied / {D} Documented / {S} Skipped) from apply-security-fixes
```

**User Confirmation (MANDATORY):**

> "Found handoff from apply-security-fixes. Use these values? [Use handoff / Cancel]"

Cancel → skill aborts (or user can re-run and choose standalone mode at A0.5).

### Standalone Mode — SDE MCP

**Input source:** SD Elements project selected by the user via MCP at Step A1-S.

No handoff file is consumed. All countermeasure data comes from the SDE API:

- **Project selection:** user picks from `project op=list page_size=100`; validate project access with `project_countermeasures op=list page_size=1` before full fetch — on 403/404, HARD STOP with remediation
- **CM list:** `project_countermeasures op=list expand=text,status,problem,tags,how_tos,phase page_size=250`; paginate if the project has >250 CMs (follow `next` links or increment `page` until exhausted)
- **Status filters:** user selects task status filter (`DONE` only / `TODO` only / all) and verification status filter (`none` only / `none` + `fail` / all)
- **Per-CM fields available:** `id`, `full_id`, `sde_task_status`; `category` is DERIVED from `phase`+title/text (SDE has NO native `category` field)
- **`files_modified[]`:** always `[]` — file discovery happens in subagent B1.7

**Checkpoint Output:**

```
[CHECKPOINT] Standalone mode: {N} countermeasures fetched from project {project_name} (ID: {project_id}) | task_status_filter: {filter} | verification_filter: {filter}
```

**User Confirmation (MANDATORY):**

> "Found {N} countermeasures in project {project_name} matching your filters. Proceed with verification? [Proceed / Cancel]"

Cancel → skill aborts.

---

## Handoff Emission

**Output file:** `.sde-verification-handoff.json` at the repository root (SEPARATE from `.sde-apply-handoff.json`). **Filename and `source_skill` are REUSED from the original skill (shared resume).** Engine fields below are ADDITIVE (absent/null for `ai`; populated for `zeropath`/`hybrid`). See SKILL.md Step D for the full schema. New per-result keys: `ai_status`, `zp_status`, `zp_issue_url`. New `note_post_status` sentinels: `DEFERRED_HYBRID` (transient — must be resolved to the combined-note result before the handoff is written) and `NOT_SENT_ZP_NATIVE` (zeropath; ZeroPath's push owns the note). The new top-level `zeropath` block records `{ repositoryId, mappingId, scan_branch, scan_branch_remote_sha, scanId, commitSha, sync_stats, push_stats, coverage[], pass_by_absence_count }` (`scan_branch`/`scan_branch_remote_sha` capture the R-ZP11 verified-pushed branch; on success `commitSha == scan_branch_remote_sha`).

**Assembled from disk (T6):** `verification_results[]` MUST be built by `assemble_handoff(in_scope_ids)` reading the per-CM offload files `.sde-security/verify/{project_id}/cm-work/{full_cm_id}.json` for THIS run's in-scope CM IDs ONLY (never a whole-dir glob — the dir is keyed by project_id and may hold a prior different-mode run's artifacts) (written during Phase B / B-HYB as each result is finalized; hybrid offloads a DEFERRED artifact per-CM during the AI loop — so per-batch mini-gates pass — then OVERWRITES it with the final combined record after the merge; zeropath offloads the ZP-native mirror) — NEVER from in-context memory. The offload stores the OUTPUT of the AI's analysis only; the analysis itself is never offloaded (SHELL TOOL USAGE POLICY). See SKILL.md Step D for the helper pseudocode.

### Schema

```json
{
  "source_skill": "code-scan-verification-validation",
  "handoff_version": "1",
  "scan_engine": "ai | zeropath | hybrid",
  "authoritative_source": "ai | zeropath | null",
  "verification_mode": "handoff | standalone | enter_project",
  "execution_mode": "subagent | inline",
  "resumed_from": "{prior_generated_at or null}",
  "generated_at": "{iso8601_utc}",
  "upstream_handoff": ".sde-apply-handoff.json | null",
  "project_id": "{project_id}",
  "risk_policy_id": "{risk_policy_id or null}",
  "repository_path": "{path}",
  "scope": "all | selected_cms | one_by_one",
  "scope_args": { "cm_ids": ["..."] },
  "fail_rollback_opt_in": "yes_rollback | no_verification_only",
  "totals": { "verified_pass": P, "verified_partial": PT, "verified_fail": F, "skipped": S, "skipped_out_of_scope": S_oos, "note_failed": NF },
  "verification_results": [ { "full_cm_id": "...", "status": "pass | partial | fail | skipped | skipped_out_of_scope", "confidence": "high | low | n/a", "findings": [{"file": "...", "line": 0, "description": "...", "category": "residual-marker | residual-vulnerable-pattern | mitigation-confirmed | alternative-mitigation-accepted | vulnerability-absent-mitigation-unrecognized | vulnerability-absent | not-applicable-how-to-skipped | analysis-uncertain | context-fetch-failed | scope-mismatch | subagent-timeout | upstream-note-preserved | upstream-note-fetch-failed"}], "finding_ref": "...", "note_post_status": "POSTED | FAILED:{reason} | NOT_SENT | NOT_SENT_OUT_OF_SCOPE | NOT_SENT_FORCED_FAIL | NOT_SENT_AUTH_FAILURE | NOT_SENT_ZP_NATIVE | DEFERRED_HYBRID (transient — MUST NOT survive into the written handoff; see SKILL Step D)", "reason": "free-text; populated for skipped / skipped_out_of_scope / auth-aborted entries; empty string for pass/partial/fail" } ],
  "failed_cms_for_rework": [ { "full_cm_id": "...", "reason": "..." } ]
}
```

### Constraints

- `source_skill` MUST be `"code-scan-verification-validation"` (not `"apply-security-fixes"`)
- `upstream_handoff` MUST be `".sde-apply-handoff.json"` in handoff mode (so a future skill can walk the chain) or `null` in standalone mode
- `failed_cms_for_rework[]` is populated from entries where `status == "fail"`
- `scope` MUST be one of the three canonical values (`all` / `selected_cms` / `one_by_one`); the menu shortcuts `one_cm` and `multi_cm` both serialize as `selected_cms`. Legacy values `single_cm` and `domain` are accepted on read and aliased (`single_cm` -> `selected_cms`; `domain` is rejected with a remediation message because the handoff lacks CM domain data) — never written. The `domain` scope was removed in beta-3.2.0.
- Per-finding `category` MUST be one of: `residual-marker`, `residual-vulnerable-pattern`, `mitigation-confirmed`, `alternative-mitigation-accepted`, `vulnerability-absent-mitigation-unrecognized`, `vulnerability-absent`, `not-applicable-how-to-skipped`, `analysis-uncertain`, `context-fetch-failed`, `scope-mismatch`, `subagent-timeout`, `upstream-note-preserved`, `upstream-note-fetch-failed`. The `vulnerability-absent` category is used in standalone mode when B1.7 finds no relevant files in the repository. The `upstream-note-preserved` and `upstream-note-fetch-failed` categories are audit-only (no verdict impact) — they record whether B4's note-fetch preserved upstream details or failed. The deprecated category `missing-fix` (pre-3.2.0) MUST NOT appear in any new handoff.
- `scope_args.cm_ids[]` MUST be present (length >= 1) iff `scope == "selected_cms"`; absent for the other two scopes (`all`, `one_by_one`).

---

## Context Limit Handling

If approaching context limits mid-loop:

```
=== CONTEXT CHECKPOINT ===
Skill: code-scan-verification-validation
Progress: {done}/{in_scope_total}
Verified so far: {P} pass, {PT} partial, {F} fail, {S} skipped (user), {S_oos} skipped (out of scope)
Last completed: {full_cm_id}
Remaining: [{id1}, {id2}, ...]
Status: INCOMPLETE - requires continuation
==========================

To resume: Say "continue"
```

On resume: continue from exact position; re-read the canonical CM source (handoff mode: `.sde-apply-handoff.json`; standalone mode: re-fetch from SDE); skip already-verified CMs via Step A1.5+A3's set-subtraction reconciliation against the canonical source. Spurious entries in prior verification results are flagged and excluded from the gap calculation.

---

## Contract Acceptance

By reading this file, you agree to:

0. Ask the user for the scan engine (`ai` / `zeropath` / `hybrid`) at Step A0.0 (FIRST question). For `zeropath`/`hybrid`: run the A0-ZP preflight (HARD STOP on failure or tenant mismatch), the A-ZP1 ZeroPath setup, and (hybrid) the A-ZP2 authoritative-source choice; obey R-ZP1–R-ZP11; prefer dedicated tools + direct-API (Token) for reference endpoints (R-ZP8), not `api_request`. The `ai` engine and the AI half of `hybrid` follow ALL rules below unchanged.
1. Verify MCP connection before Phase A
2. Ask the user for mode (handoff / standalone / enter_project) and repository path at Step A0.5
3. **Handoff mode:** treat `.sde-apply-handoff.json` as a HARD REQUIREMENT (HARD STOP if missing/wrong source). **Standalone mode:** require SDE project selection via MCP at Step A1-S
4. Always ask the user to confirm the handoff values (handoff mode) or SDE project + CM filters (standalone mode) before Phase B
5. Run `git status --porcelain` (scoped to SOURCE changes — exclude the skill's own `.sde-security/` scratch and `.sde-verification-handoff.json`) BEFORE any `git checkout` and HARD STOP if non-empty
6. Ask the user for resume + scope (Step A1.5+A3, **ai engine ONLY** — for `zeropath`/`hybrid` this step is skipped and scope is forced to `all` per R-ZP10), fail-rollback opt-in (Step A4), and batch size (Step A5 — **ai/hybrid only; SKIPPED for `zeropath`**, no AI loop) - never assume (for ai)
7. Probe for subagent support (Step A6). If unavailable, activate inline fallback mode (`execution_mode == "inline"`: batch_size=1, no parallel, context checkpoints every 5 CMs, warn user about context limits)
8. Output the Phase A verification block (Step A7) summarizing all collected inputs (including `execution_mode` from A6); wait for user confirmation before starting Phase B. If MATCH = NO, loop back to the first missing input. If the user cancels, abort.
9. Dispatch batched `generalPurpose` subagents (batch_size CMs per subagent, up to 5 in parallel; or run inline if `execution_mode == "inline"`) to fetch full CM context from SDE, perform AI analysis (with file discovery in standalone mode via B1.7), and POST the verification note for each CM in the batch. **"In-scope" has one canonical meaning: whatever `filter_by_scope` returned.** **Handoff mode:** under `all` / `one_by_one` the filter excludes Documented and Skipped CMs; under `selected_cms` the filter includes whatever IDs the user explicitly listed. Documented CMs are short-circuited at parent B0a; upstream-Skipped at parent B0b; empty-files code CMs at parent B0b2 (v2) or subagent L-FF2-sub (v1); empty-files non-code CMs at parent B0b3 (v2) or subagent L-OOS-sub (v1). **Standalone mode:** all CMs that pass the SDE status filters are in scope; no handoff-derived short-circuits (B0a/B0b/B0b2/B0b3) apply; B1.7 file discovery runs instead of B1.5 (inside the subagent when `execution_mode == "subagent"`, or inline in the parent when `execution_mode == "inline"`). User-skipped CMs (`one_by_one` mode) are no-fetch/no-read/no-POST, recorded via `record_skipped`. Timed-out batches are recorded as `partial`/low/`subagent-timeout` — never `fail`.
10. The subagent (or, in handoff mode, the parent for B0b2/B0b3 short-circuits) determines the disposition of each CM. For CMs that reach per-CM verification (subagent or inline), only the verification context calls `read_file` on the relevant files (handoff: `files_modified[]`; standalone: `discovered_files[]` from B1.7) and performs Q1/Q2/Q3 AI analysis. When `execution_mode == "subagent"`, the parent's context budget is preserved by delegation to batched subagents. (In inline mode, context accumulates in the parent — see Step A6 context checkpoints.)
11. Include the residual-marker scan (verbatim hardcoded list) in the verification context (subagent prompt or inline analysis) as a fail criterion
12. Record a result entry for every in-scope CM. POST-eligible CMs receive a Verification Note via `verification op=create` (with documented retry/back-off) — in subagent mode this runs inside the subagent, in inline mode it runs in the parent context. Forced-fail CMs (handoff mode parent B0b/B0b2, subagent L-FF2-sub) also receive a B4+B5 POST (inline for parent, inside subagent for L-FF2-sub) to ensure rework candidates have visible notes in SDE. User-skipped CMs, Documented CMs (handoff mode under `selected_cms` parent B0a), OOS CMs (handoff mode parent B0b3, subagent L-OOS-sub), timed-out batches, and run-aborted CMs are recorded with the appropriate `note_post_status` — no API call, but the audit-trail entry is mandatory
13. Include `task_status_mapping.fail: TODO` ONLY when the user opted in at A4 AND the current verdict is `fail` (forwarded to subagents via `task_status_mapping_opt_in`)
14. Never default to `pass` or `fail` under uncertainty — map to `partial` with `low` confidence (Rule 5: No-False-Positives Invariant)
15. When `execution_mode == "subagent"`: validate every subagent's JSON array output against the strict return schema (array length == batch size, per-element `full_id` match); on parse error record `partial`/`low`/`analysis-uncertain` for every CM in the batch (NEVER `fail`). When `execution_mode == "inline"`: validate the inline verification result for each CM against the same per-element schema
16. On any subagent's `auth_failure: true`, stop dispatching further ROUNDS and record every unreached CM (the rest of this batch + all batches in subsequent rounds) via `record_skipped` (deduped by `full_id`; sibling batches already returned in the same round keep their real verdicts) to preserve the Sum-check identity
17. On subagent timeout (all retries exhausted), record every CM in the batch as `partial`/`low`/`subagent-timeout` (NEVER `fail`)
18. Write `.sde-verification-handoff.json` at the repository root; in handoff mode, NEVER modify or delete `.sde-apply-handoff.json`
19. Output the completion verification block before declaring success
20. Apply all rules regardless of repository intent (training/CTF/demo are irrelevant)
21. Never run external scripts to perform skill steps
22. **Any spawned subagent MUST use the parent agent's model (set `model` explicitly) — NEVER `composer-2.5-fast` (Composer 2).** In Cursor the default subagent is Composer 2, so you MUST override it; if you cannot set the model, run inline (`execution_mode = "inline"`, Step A6 fallback). Subagent batching is permitted in ANY environment under the SUBAGENT/DELEGATION POLICY; the parent always re-derives completeness from SDE + disk (tri-source)

**There are NO exceptions to these rules except two documented subagent-dispatch relaxations — the inline fallback mode (Step A6 / Rule 9) and the parent forced-fail short-circuit POST (B0b/B0b2 run B4+B5 inline — Rule 9) — which relax only the subagent-dispatch requirement while preserving all verdict, evidence, and API rules. Inline fallback applies only when the subagent model cannot be set to the parent's model. This skill is REPOSITORY-AGNOSTIC and VERDICT-AGNOSTIC.**

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│ ZP CODE SCAN VERIFICATION VALIDATION - EXECUTION RULES       │
├─────────────────────────────────────────────────────────────┤
│ ⚠️ Step A0.0: User picks SCAN ENGINE (ai|zeropath|hybrid)   │
│ ⚠️ zeropath|hybrid: A0-ZP preflight + tenant-match (HARD)   │
│ ⚠️ zeropath|hybrid: A-ZP1 map+syncRules+audit; scan mutates │
│    SDE (side-effect warning before scans_start)             │
│ ⚠️ zeropath|hybrid: scan_branch MUST be committed+pushed to │
│    the ZeroPath remote (R-ZP11); else HARD STOP (user pushes│
│    ); hybrid: scan_branch == checked-out branch             │
│ ⚠️ zeropath: posts NO notes (ZeroPath push owns status);   │
│    pass-by-absence WARN gate                                 │
│ ⚠️ hybrid: defer AI B5; ONE combined note (behaviour=combine│
│    ); status = authoritative source (A-ZP2)                 │
│ ⚠️ Prefer dedicated tools; direct-API (Token) for ref eps  │
│ ⚠️ Step A0.5: User picks MODE (handoff|standalone|project) │
│ ⚠️ Handoff mode: .sde-apply-handoff.json REQUIRED at repo   │
│ ⚠️ Standalone mode: SDE project selection via MCP            │
│ ⚠️ Git tree MUST be clean before checkout                    │
│ ⚠️ Handoff mode: upstream handoff is READ-ONLY               │
├─────────────────────────────────────────────────────────────┤
│ ✓ Verify MCP, select mode+repo, load input, confirm w/user │
│ ✓ git status --porcelain empty → checkout branch            │
│ ✓ Ask resume+scope (A1.5+A3), fail-rollback (A4), batch (A5)│
│   (zeropath: A1.5+A3, A5 batch & A-ZP2 timeout SKIPPED)     │
│ ✓ Subagent probe (A6); inline fallback if unavailable       │
│ ✓ Phase A summary + user confirmation (A7) before Phase B   │
│ ✓ Handoff: B0a/B0b/B0b2/B0b3 short-circuits, then batch    │
│ ✓ Standalone: all CMs → batch (no handoff short-circuits)   │
│ ✓ Handoff subagent: B1+B1.5+B2+B3+B4+B5 per CM             │
│ ✓ Standalone subagent: B1+B1.7(discover)+B2+B3+B4+B5 per CM │
│ ✓ Return JSON array of results                              │
│ ✓ Retry/timeout: kill+relaunch after 5min, max 2 retries    │
│ ✓ task_status_mapping: pass→DONE always; fail→TODO only opt │
│ ✓ partial/low on uncertainty; fail = cited sources only      │
│   (residual-pattern, residual-marker; +Skipped/empty-files  │
│    in handoff mode)                                          │
│ ✓ NO false positives — Q1=absent_high_confidence + clean    │
│   markers → pass regardless of Q2/Q3                        │
│ ✓ Residual markers = fail                                   │
│ ✓ Retry 429/5xx once with 1s back-off, then FAILED          │
│ ✓ 401/403 → auth_failure, parent HARD STOPs, record all     │
│   unreached as record_skipped                               │
│ ✓ Malformed subagent return → partial/low/analysis-uncert.  │
│ ✓ Write .sde-verification-handoff.json at the end           │
│ ✓ Output [VERIFY-DISPATCH], [VERIFY] per CM; completion blk │
├─────────────────────────────────────────────────────────────┤
│ ✗ Handoff mode: Do NOT run without the handoff file         │
│ ✗ Standalone: Do NOT run without SDE project selection      │
│ ✗ Do NOT checkout on a dirty tree                           │
│ ✗ Handoff mode: Do NOT overwrite .sde-apply-handoff.json    │
│ ✗ Do NOT auto-proceed after input confirmation              │
│ ✗ Do NOT default pass or fail on uncertainty                │
│ ✗ Do NOT mark fail because canonical pattern not recognised │
│ ✗ Do NOT mark malformed-subagent-output as fail             │
│ ✗ Do NOT mark subagent-timeout as fail                      │
│ ✗ Do NOT run B1/B2/B3/B4/B5 inline (unless inline mode)     │
│ ✗ Do NOT use subagent type other than generalPurpose        │
│ ✗ Do NOT continue loop after auth_failure: true             │
│ ✗ Do NOT send fail→TODO mapping without user opt-in         │
│ ✗ Do NOT skip the residual-marker scan                      │
│ ✗ Do NOT rely on grep alone for verdicts                    │
│ ✗ Do NOT exit the loop agent-initiated                      │
│ ✗ Do NOT request elevated shell permissions for local files │
└─────────────────────────────────────────────────────────────┘
```