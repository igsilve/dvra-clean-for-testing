---
name: zp-code-scan-verification-validation
description: Verifies that security countermeasures are actually mitigated in code and records Verification Notes to SD Elements, with a selectable scan engine — AI Only (the original AI verdict engine), ZeroPath Only (triggers a ZeroPath scan whose backend writes verification results to SDE; skill posts no notes), and Hybrid (runs both the AI per-CM analysis and a ZeroPath scan, then posts one combined note per CM with status from a user-chosen authoritative source). Supports handoff mode (reads .sde-apply-handoff.json from apply-security-fixes) and standalone mode (fetches countermeasures from SDE via MCP with AI-driven file discovery), orthogonal to the scan engine. Wires the securitycompass-mcp + zeropath MCP servers in for the ZeroPath/Hybrid engines. Before posting each verification note, fetches existing verification notes (via `verification op=list`) to preserve prior verification details (read-then-append pattern, behaviour=combine). Forced-fail CMs receive posted notes for SDE visibility. Use when verifying security fixes, scanning code for countermeasure compliance, or validating mitigation after apply-fixes or manual remediation.
---

> **SUBAGENT / DELEGATION POLICY -- READ THIS FIRST**
>
> 1. **Same model as the parent, ALWAYS.** Any spawned subagent MUST run on the SAME model as the parent agent -- set the `model` parameter explicitly to the parent's model. If you cannot set the subagent's model, do NOT spawn -- run inline.
> 2. **NEVER Composer 2.** `composer-2.5-fast` (Composer 2) is FORBIDDEN as a subagent model in ANY environment -- it silently abandons CM verification loops, skips CMs, uses wrong endpoints for note POSTs, loses context, and produces unreliable verdicts. In Cursor the DEFAULT subagent is Composer 2, so you MUST override `model` to the parent's model explicitly; if you cannot override it, run inline.
> 3. **Parent owns completeness.** Delegation NEVER transfers responsibility for completeness. The parent re-derives every CM from SDE + disk (tri-source invariant) regardless of who did the work. Every subagent MUST emit `[VERIFY]`/`[PROGRESS]` lines and return a verifiable JSON result; the parent verifies every item.
>
> Subagent batching (Step A6 / Phase B) is permitted in ANY environment (including Cursor) under this policy; inline execution is the fallback only when the subagent `model` cannot be set to the parent's model. (Applies to the AI loop in `ai`/`hybrid`; `zeropath` has no AI loop.)
>
> Output at skill start: `[CHECKPOINT] Subagent policy: same-model-as-parent | Composer 2 FORBIDDEN | parent owns completeness (tri-source)`

# ZP Code Scan Verification Validation

> **STOP -- PHASE A RUNS IN PLAN MODE. DO NOT SWITCH TO AGENT MODE UNTIL PHASE B.**
>
> This skill has a sequence of mandatory interactive Phase A steps that MUST be completed in order in **plan mode** using `ask_question` calls: A0 (MCP check), **A0.0 (scan engine select)**, **A0-ZP (multi-MCP preflight — zeropath/hybrid only)**, A0.5 (mode+repo), A1/A1-S (CM source), A1.6 (risk policy check+confirm), A1.5+A3 (resume+scope), A2 (git), A4 (fail-rollback), A5 (batch — **skipped for `zeropath`**, no AI loop), A6 (subagent probe), **A-ZP1 (ZeroPath setup) + A-ZP2 (authoritative source — hybrid only; the scan-timeout question is removed for both engines, replaced by a 30-min default cap + 1-min polling)**, A7 (execution-plan gate). For `scan_engine == "ai"` the ZeroPath steps (A0-ZP/A-ZP1/A-ZP2) are skipped and the flow is identical to the original skill. All Phase A steps are read-only (MCP reads, file reads, user questions). You MUST NOT:
> - Switch to agent mode before Phase A is complete
> - Create a plan (via `CreatePlan`) before completing Phase A
> - Infer or assume any Phase A input (mode, scope, batch size, fail-rollback) from context
> - Default to `all` scope without asking the user via `ask_question` in Step A1.5+A3
> - Skip Step A1.5+A3 (resume + scope selection) for any reason
>
> **Step A1.5+A3 specifically:** Even if the user says "verify all CMs" or "run the skill", you MUST present the scope menu via `ask_question` and let the user explicitly select. When a prior run exists, the resume and scope questions are presented together in one `ask_question` call.
>
> **After Step A7 (user confirms the execution plan):** Switch to agent mode to begin Phase B.

This skill verifies that security countermeasures are mitigated in code and records a **Verification Note** against each task in SD Elements. It supports two modes:

- **Handoff mode:** follows `apply-security-fixes`. Reads `.sde-apply-handoff.json`, verifies the specific files modified by the upstream skill.
- **Standalone mode:** runs independently -- use after the survey + `generate-security-skill-files` chain (`setup-security-plan-from-repo` or `create-security-plan-from-specs` → `generate-security-skill-files`), or any manual fix workflow. The user selects an SD Elements project (via MCP), the skill fetches countermeasures from SDE, discovers relevant files in the repository, and verifies each CM. Tasks verified as `pass` (including `vulnerability-absent` when no relevant files exist) are automatically marked DONE in SDE via `task_status_mapping`.

See **Completion Criteria** below — the skill is complete only when every checkbox is ticked.

## Execution Contract

**REQUIRED:** Read and follow the [./AGENTS.md](./AGENTS.md) execution contract.

In **handoff mode**, this skill is downstream of `apply-security-fixes`. If `.sde-apply-handoff.json` is missing, malformed, or from a different upstream skill, handoff mode HARD STOPS (switch to standalone mode via Step A0.5).

In **standalone mode**, no handoff file is needed -- use after the survey + `generate-security-skill-files` chain (`setup-security-plan-from-repo` or `create-security-plan-from-specs` → `generate-security-skill-files`), or any manual fix workflow. The skill fetches countermeasures directly from SD Elements via MCP. Tasks verified as `pass` (including `vulnerability-absent`) are automatically marked DONE in SDE.

## AUTHORITATIVE EXECUTION CONTRACT

This skill (and its AGENTS.md) is the authoritative source for HOW MUCH work is required; it OVERRIDES your own judgment about scale or "pragmatic" shortcuts. Expect the per-CM verification loop (`ai`/`hybrid`) to run for EVERY in-scope CM (often tens-to-hundreds) — those counts are NORMAL and EXPECTED, not a reason to sample. You have explicit, unconditional permission to take as many turns and as many sessions as needed; completeness is the ONLY priority and there is no turn budget. The ONLY sanctioned way to pause is a `=== CONTEXT CHECKPOINT ===` (then resume by re-deriving progress from the source of truth — SDE + the on-disk per-CM artifacts — never from chat memory, never restart). A run is either **COMPLETE** (all gates pass) or **INCOMPLETE** (a clean checkpoint emitted) — there is NO third state. Forbidden rationalizations: "pragmatic" / "representative" / "efficient" / "key CMs" / "the rest are ..." / "N+" / "Let me finalize" (pre-completion) / "move forward to more impactful steps".

## CONTRACT BOOTSTRAP (MANDATORY FIRST ACTION -- before Step A0)

> Chain-compatibility: this skill shares the `.sde-security/` workspace with `setup-security-plan-from-repo`, `create-security-plan-from-specs`, `generate-security-skill-files`, and `apply-security-fixes`. It owns ONLY `.sde-security/verify/<project_id>/...` and `.sde-security/contract/zp-code-scan-verification-validation/`. It MUST NOT write to or delete the shared `.sde-security/cm-work/` or `.sde-security/library-lookup/` (created by `generate-security-skill-files`), `.sde-security/apply/` (apply-fixes), or the upstream handoffs `.sde-handoff.json` / `.sde-apply-handoff.json`.

- **B0. Fresh-run vs resume — decide first.** NEW run → clear ONLY this skill's own scratch (`.sde-security/verify/<project_id>/...`, once `project_id` is known at Step A1/A1-S/enter_project) plus a stale root-level `.sde-verification-handoff.json`. RESUME → keep all prior artifacts and resume from disk. NEVER delete `.sde-handoff.json`, `.sde-apply-handoff.json`, or any upstream `.sde-security/` subdirectory. **Cross-mode note:** the offload dir `.sde-security/verify/<project_id>/cm-work/` is keyed by `project_id` ONLY (not by `verification_mode`/`scan_engine`), so it can hold artifacts from a PRIOR run of a different mode/engine (e.g. an `ai` `one_by_one` run's per-CM artifacts vs a `zeropath` run's mirror artifacts). A fresh run clears it; independently, the Step D disk helpers (`assemble_handoff`/`verify_disk_vs_sde`) scope to THIS run's in-scope CM IDs, so stale cross-mode artifacts cannot corrupt Layer-2/assemble even if cleanup was skipped. Do NOT auto-resume against a prior `.sde-verification-handoff.json` whose `verification_mode`/`scan_engine` differs from the current run — treat it as fresh (or reconcile strictly by the current run's CM IDs).
- **B1. Fetch the EXACT served contract** for THIS skill (not memory): `prompts op=get prompt=zp-code-scan-verification-validation`.
- **B2. Pin it VERBATIM** to `.sde-security/contract/zp-code-scan-verification-validation/{SKILL,AGENTS}.md` (split on BEGIN/END markers if concatenated).
- **B3. Record a manifest** at `.sde-security/contract/zp-code-scan-verification-validation/manifest.json`: `{ skill, fetched_at, sha256_skill, sha256_agents, skill_chars, agents_chars }`.
- **B4. Staleness check (WARN, do NOT deadlock):** the contract you were GIVEN to execute is authoritative. If `prompts op=get` errors / is empty / lacks this skill, WARN "served prompt stale" and pin from the best available source (served-if-valid > on-disk source > given text). HARD STOP only if no source exists.
- **B5. Emit:** `[CONTRACT PINNED] skill=zp-code-scan-verification-validation | path=.sde-security/contract/zp-code-scan-verification-validation/ | SKILL chars={n} sha256={short} | AGENTS chars={n}`

### STEP PREFLIGHT CONVENTION (every step AND every batch)
- **Before each step:** reload that step's section from the pinned `.sde-security/contract/zp-code-scan-verification-validation/SKILL.md` (read ONLY that step's heading→next-heading range — context-light), THEN emit `[STEP] entering {step} | reloaded §{step} from disk? YES | sentinel: "{a verbatim line copied from that step's section on disk}"`. You cannot produce the correct sentinel without having re-read the section.
- **Heavy/looping steps (Phase B `ai`/`hybrid` AI loop):** ALSO reload at every batch boundary and include the sentinel in the `[RUNNING CHECK]`.
- A missing/incorrect sentinel = running from memory = **CONTRACT VIOLATION**. STOP and reload.

## SHELL TOOL USAGE POLICY (CANONICAL -- applies to this ENTIRE skill)

The AI owns ALL vulnerability analysis, verdicts, and note authoring (inline); scripts are allowed ONLY for mechanical/IO + SDE calls with completeness-verify + retry.

| Work | Owner | Rule |
|------|-------|------|
| Reading code; vuln ANALYSIS (B2); VERDICT (B3); finding/note authoring | AI only | inline (subagent or parent); NO script may read code, decide a verdict, or author findings. Applies to the `ai` engine and the `hybrid` AI loop; `zeropath` runs no AI analysis |
| Per-CM result OFFLOAD (write the AI's already-produced verdict/findings JSON), disk count, assemble-from-disk, Layer-2 verify script | script OK | mechanical only; implement the helper routines yourself from the pseudocode in this contract |
| SDE note POST | per-CM `verification op=create` WITH verify + retry | **NO Composite API** — notes are posted ONE CM at a time (the dedicated tool): `ai` posts per-CM; `hybrid` posts ONE combined note per CM; `zeropath` posts none (ZeroPath's push owns status). Never batch note POSTs into a composite call |
| git / file reads / `/tmp` scratch | OK | |

**AI ANALYSIS IS NEVER OFFLOADED.** The disk-offload (Phase B per-CM loop; helpers in Step D / T6) stores the OUTPUT of the AI's analysis (the verdict + findings the AI already produced). It is NEVER a substitute for doing the analysis: for the `ai` engine and the `hybrid` AI loop, B2 (read + analyze the code) and B3 (derive `pass`/`partial`/`fail` via the No-False-Positives Invariant) MUST run as AI reasoning inline, never by a script and never "deferred to disk in place of doing it." (`zeropath` runs no AI analysis.)

---

## ⚠️ AI CODE ANALYSIS REQUIRED - NO GREP-ONLY VERDICTS ⚠️

Verification verdicts MUST come from **reading the relevant files with `read_file`** (modified files in handoff mode; discovered files in standalone mode) and reasoning about whether the code actually mitigates the vulnerability described in `ctx.problem` (the vulnerability) and the recommended fix described in `ctx.text` (the canonical fix narrative). `ctx.how_tos[]` is **optional, corroborative input** — many SDE CMs have empty or partially populated `how_tos[]`, and the verdict logic must work correctly in that case (see Step B3 verdict matrix; Q2 is skipped when `ctx.how_tos[]` is empty or has no language-applicable entries). Grep is acceptable only as a pre-filter to locate residual markers; it is never sufficient by itself to declare `pass`.

| ❌ FORBIDDEN | ✅ REQUIRED |
|-------------|-------------|
| `pass` because `files_modified` is non-empty | `read_file` each modified file, confirm fix is present and correct |
| `fail` based on a hunch | `fail` requires a cited residual pattern or marker |
| Skipping CMs whose files no longer exist | HARD STOP, report the inconsistency |
| Posting any verdict (pass/partial/fail) to a Documented-only CM | Filter excludes from `all` / `one_by_one`; under `selected_cms`, Step B0a records `skipped_out_of_scope`; no API call in either case (SAST convention; nothing on disk to scan) |
| Marking `fail` because the canonical mitigation pattern was not found | The vulnerability described in `ctx.problem` being absent is canonical; recognition of the mitigation is corroborative. Use the no-false-positives invariant in Step B3 — `fail` requires CITED evidence (residual pattern, residual marker, or — handoff mode only — upstream `Skipped` or empty `files_modified[]` for code CMs) |
| Marking `fail` or `partial` because `ctx.how_tos[]` is empty or has no applicable entries | Q2 is OPTIONAL. The matrix collapses to Q1 + Q3 + marker scan; `Q1=absent_high_confidence` + clean markers always yields `pass`/`high` — `how_tos` is corroborative-only |
| Marking `partial` because the developer used a different mitigation style than the how-to | If Q1 is `absent_high_confidence`, the verdict is `pass` regardless of Q2/Q3. `partial` is reserved for genuine analysis ambiguity (Q1 = `ambiguous`) or context-fetch failures |

---

## Status concepts: verification status vs. countermeasure status

SD Elements has **two separate, independent status concepts** ([User Guide reference](https://docs.sdelements.com/master/guide/docs/integrations/security_tools/overview/verification_status.html)):

| Concept | Values | API resource | What it means |
|---------|--------|--------------|---------------|
| **Countermeasure (task) status** — workflow state | `TODO` (Incomplete) / `DONE` (Complete) / `NA` (Not Applicable) | `/api/v2/task-statuses/` | The work-item state. Customizable via custom statuses with one of the three "meanings". |
| **Verification status** — verification outcome | `pass` / `partial` / `fail` / `none` | `/api/v2/verification-statuses/` | Whether the countermeasure has actually been verified as completed. Independent of countermeasure status. |

This skill writes **verification status** by creating a Verification Note via `verification op=create`. It can also atomically update **countermeasure (task) status** via the optional `task_status_mapping` field on the same payload (see Step B3). The two are distinct fields in the SDE data model and in the SDE UI; this skill never conflates them.

Throughout this skill, "verdict" = verification status. "Workflow status" / "task status" = countermeasure status. Never use one to refer to the other.

---

## Scope of static verification

SD Elements treats this skill the same way it treats any SAST scanner posted via Manual Verification: it only emits Verification Notes for countermeasures whose mitigation is **in code or config files**. This matches the convention used by Veracode, Checkmarx, Snyk Code, Fortify, Semgrep, etc. when they report into SDE.

**Handoff mode:** Documentation-only countermeasures (`ML_DOC`, and `INFRA` CMs that `apply-fixes` recorded as `Documented`) are **out of scope for static analysis**. The skill skips them without a verification note POST — the SDE UI honestly shows "No Verification Status" until a human or a different verifier weighs in. Beyond the SAST convention, there is a hard operational reason: `apply-fixes` Step 7 deletes the `skills/` directory before this skill runs. Documented CMs have empty `files_modified[]` and **no surviving local artifact to read**. The skill defers to SDE's existing surfaces — the `[AI-Documented] ...` comment that `apply-fixes` posted via `project_countermeasures op=addNote`, plus the CM's `how_tos` and `text` fields.

> **Reviewer note — verdict scope vs SDE `verification_status`:** in the `ai`/`hybrid` handoff path the per-contract verdict is scoped to the CM's `files_modified[]` (what `apply-fixes` changed), NOT the whole repo. So a CM whose applied files are clean is verified `pass` even though a whole-repo scanner (e.g. ZeroPath, incl. this skill's own zeropath engine) mapped a finding to the same CM. Because combined notes use `behaviour=combine` (fail-dominant across the note set), the CM's SDE `verification_status` can REMAIN `fail` from a prior whole-repo note while the ai/hybrid run logs `pass` for its scoped fix. Expected, not a conflict: the two answer different questions (this apply's scoped change vs the CM's combined history). Only a `replace`/`replace-scanner` note (e.g. ZeroPath's per-scan push) resets the baseline. Reviewers seeing "pass in log / fail in UI" should reconcile via the note history.

**Standalone mode:** There is no upstream `Documented`/`Skipped`/`Applied` status. All CMs that pass the SDE status filters (Step A1-S.3) are in scope. The file discovery step (B1.7) determines whether relevant code exists; if no relevant files are found, the verdict is `pass` with `vulnerability-absent` (the vulnerability does not appear in the codebase).

### Handoff-mode discriminator

The skill reads `status` from `.sde-apply-handoff.json` for each entry. Filtering happens at `filter_by_scope` (before the loop), so the loop only sees in-scope CMs:

| `cm.status` | Lane | Filter (`all` / `one_by_one`) | Filter (`selected_cms`) | Loop action |
|-----------------------|------|-------------------------------|-------------------------|-------------|
| `Applied` | In scope | included | included if listed | Per-CM verification (via batched subagent or inline — see Step A6): B1 (fetch CM context via MCP) + B2 (AI analysis on modified files) + B3 (verdict) + B4 (fetch existing notes) + B5 (POST Verification Note via MCP) per CM in batch |
| `Documented` | **Out of scope** | **excluded by filter** | included if listed (after warning) | Step B0a defensive guard (parent loop): record `skipped_out_of_scope`, emit `[SKIP-OOS]`; no subagent dispatch, no SDE fetch, no API call |
| `Skipped` | In scope (forced fail) | **excluded by filter** | included if listed | Step B0b forced-fail lane (parent loop): record `verdict=fail / confidence=high` with finding "CM was skipped by apply-fixes; no mitigation present"; no subagent dispatch; parent runs B4+B5 inline to POST the forced-fail note to SDE |

Net effect: Documented and upstream-Skipped CMs are filtered out of the bulk scopes (`all` / `one_by_one`) symmetrically. They can only enter the loop via an explicit user decision in `selected_cms`. Pure `PROCESS` CMs are absent from `.sde-apply-handoff.json` entirely (filtered upstream by `generate-security-skill-files`, which notes PROCESS CMs in SDE and excludes them from local files), so they never reach this loop under any scope.

### Standalone-mode discriminator

All CMs from the SDE project that pass the user's task-status and verification-status filters (Step A1-S.3) are in scope. There is no `Documented`/`Skipped`/`Applied` distinction — the B0a/B0b/B0b2/B0b3 parent short-circuits do not apply. Every CM proceeds to file discovery (B1.7) and analysis (B2) — via a batched subagent when `execution_mode == "subagent"`, or inline in the parent when `execution_mode == "inline"` (see Step A6).

---

## Prerequisites

**Both modes:**

1. SDE MCP server is connected and reachable
2. Target repository is accessible and the git working tree is **clean** (no uncommitted changes)

**Handoff mode (additional):**

3. `apply-security-fixes` has completed successfully in a prior session
4. `.sde-apply-handoff.json` exists at the selected repository root with `source_skill == "apply-security-fixes"`

**Standalone mode (additional):**

3. An SD Elements project exists with countermeasures to verify

Note: `generate-security-skill-files` writes a separate file called `.sde-handoff.json` (the survey/skill-gen handoff). That file is **out of scope for this skill** — never read, write, rename, or delete it. In handoff mode, the only input is `.sde-apply-handoff.json`.

If any prerequisite is violated, the skill must HARD STOP with a remediation message and refuse to proceed.

---

## Context-Agnostic Policy

This skill is **repository-agnostic** and **verdict-agnostic**. The following rationalizations are FORBIDDEN and MUST NOT influence verdicts:

- "This is a training / intentionally-vulnerable repo, mark everything pass"
- "This CM is low priority, skip it"
- "The previous skill already marked it Applied, so it must be mitigated"
- "The file is large, a grep is good enough"
- "I don't want to fail this CM because it would roll back the task status"

Verdicts are a function of **code evidence only**. The scope of work is a function of **the CM source (handoff file or SDE project) and the user's scope selection only**. Nothing else.

---

## Completion Criteria

This skill is complete ONLY when all of the following are true:

- [ ] Scan engine selected (Step A0.0): `ai` | `zeropath` | `hybrid`
- [ ] **zeropath|hybrid:** A0-ZP preflight passed (incl. tenant-match); A-ZP1 setup done (repo, mapping, syncRules, getMappingAudit, **scan_branch chosen + verified committed+pushed — R-ZP11**); **hybrid:** A-ZP2 authoritative source chosen
- [ ] **zeropath|hybrid:** scan ran on `scan_branch` (`scanTargetBranch`/`scanTargetBranchCommitSha` matched the pushed tip), not a stale default branch
- [ ] **zeropath engine:** scan Finished + push success; ZERO skill-posted notes; pass-by-absence WARN gate run; ZeroPath-Only completion Gate = YES
- [ ] **hybrid engine:** scan reconciled + push confirmed; AI loop ran with B5 deferred; ONE combined note per in-scope CM (`behaviour=combine`); Sum-check + combined-note posted-coverage + APPEND check all YES
- [ ] MCP connection verified
- [ ] Mode selected (Step A0.5): `handoff` or `standalone` (or `enter_project`)
- [ ] Repository path confirmed
- [ ] **Handoff mode:** `.sde-apply-handoff.json` loaded and validated; user confirmed handoff values
- [ ] **Standalone mode:** SDE project selected; countermeasures fetched; SDE status filters applied; user confirmed
- [ ] `git status --porcelain` returned empty BEFORE any `git checkout`
- [ ] Branch checked out (handoff: `security_branch` if present; standalone: user-selected or current)
- [ ] Risk policy displayed and confirmed by the user (Step A1.6)
- [ ] **(ai engine)** User selected a verification scope (`all` / `selected_cms` / `one_by_one`); for `one_cm`/`multi_cm`, CM IDs were collected immediately in Step A1.5+A3. **(zeropath|hybrid)** A1.5+A3 skipped; `scope == "all"` forced (R-ZP10)
- [ ] User answered the fail-rollback opt-in question (Step A4)
- [ ] Batch size resolved (Step A5): auto-set to 1 for single-CM scope, or user-selected / default (10) for multi-CM scopes
- [ ] Subagent capability probed (Step A6); `execution_mode` set to `subagent` or `inline`
- [ ] Phase A verification block output with `MATCH = YES`; user confirmed execution plan (Step A7)
- [ ] Every in-scope CM has: full SDE context fetched, relevant files read (modified files in handoff mode; discovered files in standalone mode), verdict derived, existing notes fetched via B4 (POST-eligible CMs only — user-skipped and Documented-under-`selected_cms` CMs are recorded without fetch/read)
- [ ] Every in-scope CM has a recorded result entry: a Verification Note created via `verification op=create` (or a logged failure with cause) for POST-eligible CMs; a `record_skipped` / `record_out_of_scope` entry for the no-POST classes — no CM is silently dropped
- [ ] `.sde-verification-handoff.json` written to repository root
- [ ] Completion verification block output with `Sum check = YES`
- [ ] **Posted-note coverage re-derived from SDE** (`verification op=list` per POST-eligible CM, matched on `finding_ref`) == NP — NOT trusted from the in-memory results array
- [ ] **Handoff mode:** Upstream `.sde-apply-handoff.json` was NOT modified or deleted by this skill

---

## Mandatory Checkpoints

Output these at the indicated points:

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
| Handoff loaded (handoff mode) | `[CHECKPOINT] Handoff loaded: {N} CMs ({A} Applied / {D} Documented / {S} Skipped) from {source_skill}` |
| Standalone CMs fetched (standalone mode) | `[CHECKPOINT] Standalone mode: {N} countermeasures fetched from project {project_name} (ID: {project_id}) \| task_status_filter: {filter} \| verification_filter: {filter}` |
| Risk policy confirmed (A1.6) | `[CHECKPOINT] Risk policy: {policy_name} (ID: {policy_id}) — confirmed` (or `Risk policy: (none set) — confirmed`) |
| Resume + scope status (A1.5+A3; ai engine) | `[CHECKPOINT] Resume: {already_done} CMs from prior run; {still_todo} remaining` OR `Resume: starting fresh` followed by `[CHECKPOINT] Scope: {scope}` |
| Scope forced (A1.5+A3 skipped; zeropath\|hybrid) | `[CHECKPOINT] Scope forced to all (scan_engine={scan_engine} verifies all mapped/Applicable CMs); A1.5+A3 resume/scope questions skipped.` |
| Git clean check | `[CHECKPOINT] Git tree clean; checked out {branch_name}` |
| Scope + rollback selected | `[CHECKPOINT] Scope: {scope}; fail-rollback: {yes_rollback \| no_verification_only}` |
| Batch size (A5) | `[CHECKPOINT] Batch size: {batch_size}; parallel subagents: 5` |
| Subagent probe (A6) | `[CHECKPOINT] Execution mode: {subagent \| inline}` |
| Phase A verified + user confirmed plan (A7) | `[CHECKPOINT] Phase A complete: {count}/{expected} inputs gathered; user confirmed execution plan` |
| Empty in-scope set (after `filter_by_scope`) | `[INFO] No in-scope CMs after filtering. Nothing to verify; writing empty handoff.` |
| Batch dispatched | `[VERIFY-DISPATCH] batch {batch_num}/{total_batches} | {N} CMs: [{cm_ids}] | {subagent launched \| inline}` |
| Each CM (normal verification return) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict={pass\|partial\|fail} | confidence={high\|low} | note={POSTED\|FAILED:{reason}}` |
| Forced fail — B0b (upstream Skipped) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict=fail | confidence=high | note={POSTED\|FAILED:{reason}}` |
| Forced fail — B0b2 (code CM, empty `files_modified`, v2) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict=fail | confidence=high | note={POSTED\|FAILED:{reason}} (parent B0b2)` |
| Malformed subagent return (batch) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict=partial | confidence=low | note=FAILED:subagent-malformed` (emitted per CM in batch) |
| Subagent timeout (all retries exhausted) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict=partial | confidence=low | note=FAILED:subagent-timeout` (emitted per CM in batch) |
| Auth failure (any subagent's 401/403) | `[VERIFY] {done}/{in_scope_total} | {full_cm_id} | verdict={status} | confidence={conf} | note=NOT_SENT_AUTH_FAILURE` followed by `[STOP] Auth failure at {full_cm_id}; aborted run; recorded {N} unreached CMs to preserve Sum-check identity. Refresh credentials and re-run.` |
| Documented CM under `selected_cms` (parent B0a) | `[SKIP-OOS] {done}/{in_scope_total} | {full_cm_id} | out-of-scope (Documented)` |
| Parent B0b3 (non-code CM with empty `files_modified[]`, v2 only) | `[SKIP-OOS] {done}/{in_scope_total} | {full_cm_id} | out-of-scope (parent B0b3: {category}, empty files_modified)` |
| Subagent L-OOS-sub (non-code CM with empty `files_modified[]`, v1) | `[SKIP-OOS] {done}/{in_scope_total} | {full_cm_id} | out-of-scope (subagent L-OOS-sub: {reason})` |
| User skip in `one_by_one` | `[SKIP-USER] {done}/{in_scope_total} | {full_cm_id} | user skipped` |
| User stop in `one_by_one` | `[STOP] User stopped at {done}/{in_scope_total}; recorded {N} CMs as user-stopped to preserve Sum-check identity` |
| Own handoff | `[CHECKPOINT] Verification handoff written: .sde-verification-handoff.json ({N} records)` |
| Completion | Verification block (see below) + `✅ COMPLETION GATE PASSED` |

---

## Phase A: Interactive Setup

All interactive user input happens in Phase A. Phase B runs to completion without further prompts (except explicit per-CM approval in `one_by_one` scope). **The agent MUST complete ALL Phase A steps before starting ANY Phase B step.**

### Step A0. Verify MCP Connection

Call a trivial SDE MCP tool (e.g., list projects with a tiny page size) to confirm the server is reachable. If it fails, abort with a clear remediation.

**[CHECKPOINT]** `MCP connection successful`

### Step A0.0. Scan Engine Selection (FIRST interactive question)

> This is the FIRST `ask_question` of Phase A. It selects which engine drives verification. It is orthogonal to `verification_mode` (handoff|standalone), which is still chosen at A0.5.

Ask via `ask_question`:
- **Prompt:** "Which scan engine should drive verification?"
- **Options:**
  - `{"id": "ai", "label": "AI Only — read code and verify each CM with the AI verdict engine (original behavior)"}`
  - `{"id": "zeropath", "label": "ZeroPath Only — trigger a ZeroPath scan; ZeroPath's backend writes verification results to SDE (skill posts no notes)"}`
  - `{"id": "hybrid", "label": "Hybrid — run both AI per-CM analysis and a ZeroPath scan, then post one combined note per CM"}`

Store `scan_engine = "ai" | "zeropath" | "hybrid"`.

**[CHECKPOINT]** `Scan engine: {scan_engine}`

**Routing:**
- If `scan_engine == "ai"`: the rest of Phase A and Phase B run EXACTLY as the original skill (no ZeroPath steps). Proceed to Step A0.5.
- If `scan_engine in {"zeropath", "hybrid"}`: proceed to **Step A0-ZP** (Multi-MCP Preflight) BEFORE A0.5. The ZeroPath setup (A-ZP1) and Hybrid inputs (A-ZP2) run later in Phase A as noted below, and Phase B routes to the ZeroPath-Only or Hybrid engine.

### Step A0-ZP. Multi-MCP Preflight + Tenant-Match Guard (zeropath | hybrid ONLY)

> Runs only when `scan_engine in {"zeropath","hybrid"}`. Every failure below is a **HARD STOP** with a descriptive, actionable remediation — these are blockers, not warnings. Skip this entire step when `scan_engine == "ai"`.

Run the four checks in order:

1. **sdelements reachable:** call `test_connection`. Expect `connection_successful == true`. On failure → HARD STOP: "SD Elements MCP unreachable ({error}). Fix SDE_HOST/SDE_API_KEY in mcp.json and retry."
2. **zeropath reachable + authenticated:** call `repositories_list {limit: 1}`. Any 401/403/connection error → HARD STOP: "ZeroPath MCP auth/connectivity failed ({error}). Check ZEROPATH_TOKEN_ID / ZEROPATH_TOKEN_SECRET / ZEROPATH_BASE_URL in mcp.json."
3. **securitycompass integration present + enabled:** call `securityCompass.getIntegration`.
   - If it returns null / no integration → HARD STOP: "No SD Elements↔ZeroPath integration configured for this ZeroPath org. Run securityCompass.upsertIntegration (sdeBaseUrl + sdeApiToken) first." (offer to run it).
   - If `enabled == false` → HARD STOP: "Integration is disabled. Re-enable via securityCompass.upsertIntegration {enabled: true}."
   - Then call `securityCompass.getSyncHistory {limit: 1}` to confirm the caller token is authorized (an auth error here is also a HARD STOP).
4. **Tenant-match guard (CRITICAL):** compare `host(getIntegration.sdeBaseUrl)` with `host(SDE_HOST)` (the SDE MCP's configured host). If they differ → **HARD STOP**: "Tenant mismatch — ZeroPath integration targets {sdeBaseUrl} but the SDE MCP targets {SDE_HOST}. A ZeroPath scan would push results to a DIFFERENT tenant than the one this skill reads/writes. Reconcile via securityCompass.upsertIntegration {sdeBaseUrl: <SDE_HOST>} before proceeding." (This guard exists because the mismatch silently routes ZeroPath's push to the wrong SDE tenant.)

**[CHECKPOINT]** `Preflight OK: sdelements + zeropath + securitycompass reachable; tenant match {host}`

Proceed to **Step A0.5**.

### Step A0.5. Mode + Repository Selection

Two questions determine how the skill discovers countermeasures and where it scans.

**Q1 — Repository path:**

Ask via `ask_question`:
- **Prompt:** "Which repository should I verify?"
- **Options:**
  - `{"id": "current", "label": "Current repository ({cwd})"}`
  - `{"id": "browse", "label": "Enter a different repository path"}`

If `browse`: follow-up text prompt for the absolute path. Validate that the path exists and contains a `.git/` directory (i.e., is a git repo). If validation fails, HARD STOP with remediation.

Store `repository_path`. Derive `repo_name = basename(repository_path)` (e.g., `my-app` from `/home/user/my-app`).

**Q2 — Verification mode:**

Ask via `ask_question`:
- **Prompt:** "How should I discover countermeasures?"
- **Options:**
  - `{"id": "handoff", "label": "From handoff file (.sde-apply-handoff.json in the repo) — use after apply-security-fixes"}`
  - `{"id": "standalone", "label": "From SD Elements project (no handoff needed — use after generate-security-skill-files, or manual fixes)"}`
  - `{"id": "enter_project", "label": "Enter an SD Elements project ID directly (fast path for any engine when you already know the project id)"}`

Store `verification_mode = "handoff" | "standalone" | "enter_project"`.

> **`enter_project` (direct-id fast path — first-class under ALL engines):** Present this option for every `scan_engine` (`ai` / `zeropath` / `hybrid`). It is identical to `standalone` EXCEPT the project is entered by **numeric id directly** instead of being picked from the `project op=list` menu — do NOT silently rewrite it to `standalone`; it is a first-class `verification_mode` everywhere. Follow-up text prompt for the numeric SDE project id; validate via `project_countermeasures op=list project_id={id} page_size=1` (on 403/404 → HARD STOP). Store `project_id`, `project_name` (from `project op=get`). Then: for `ai`/`hybrid`, fetch the CM list and apply the SDE status filters exactly as Step A1-S.2/A1-S.3 (so `enter_project` gathers the SAME inputs as `standalone`, just with a typed id). For `zeropath` (ZeroPath-Only) the CM list only scopes the report, so the 2 status filters are NOT gathered.

**[CHECKPOINT]** `Mode: {verification_mode}; repository: {repository_path}`

If `verification_mode == "handoff"` → proceed to **Step A1** (handoff validation).
If `verification_mode == "standalone"` → proceed to **Step A1-S** (SDE project selection).
If `verification_mode == "enter_project"` → resolve `project_id` as above, then (ai/hybrid) run the A1-S.2/A1-S.3 CM fetch+filters, and proceed to **Step A1.6** (Risk Policy Check + Confirm), then **Step A1.5+A3**.

### Step A1. Detect and Validate Handoff (handoff mode only)

```python
handoff_path = f"{repository_path}/.sde-apply-handoff.json"
if not exists(handoff_path):
    HARD_STOP(f"""
    This skill requires .sde-apply-handoff.json produced by apply-security-fixes.
    It is not present at {handoff_path}. Run apply-security-fixes first,
    or switch to standalone mode (re-run and choose "From SD Elements project").
    """)

handoff = json.load(open(handoff_path))

if handoff.get("source_skill") != "apply-security-fixes":
    HARD_STOP(f"""
    .sde-apply-handoff.json has source_skill={handoff.get('source_skill')!r}.
    This skill only accepts handoffs from apply-security-fixes.
    """)

if handoff.get("handoff_version") not in ("1", "2"):
    WARN("Unknown handoff_version; proceed at your own risk.")

handoff_has_category = (handoff.get("handoff_version") == "2")

required_keys = ["repository_path", "project_id", "countermeasures"]
missing = [k for k in required_keys if k not in handoff]
if missing:
    HARD_STOP(f"Handoff is malformed: missing {missing}")
```

Show the user a summary of `repository_path`, `project_name`, `project_id`, scope, totals, and ask:

> "Use this handoff? [Use handoff / Cancel]"

If the user declines, the skill aborts. In handoff mode there is no manual fallback because `files_modified[]` cannot be reconstructed without the handoff. (To verify without a handoff, re-run and select standalone mode at Step A0.5.)

**[CHECKPOINT]** `Handoff loaded: {N} CMs ({A} Applied / {D} Documented / {S} Skipped) from apply-security-fixes`

After the checkpoint, proceed to **Step A1.6** (Risk Policy Check + Confirm) and then **Step A1.5+A3** (resume + scope selection).

### Step A1-S. SDE Project Selection (standalone mode only)

This step replaces Step A1 when `verification_mode == "standalone"`. The skill fetches countermeasures directly from SD Elements via MCP — no handoff file needed.

#### A1-S.1: Project Selection

List available projects and let the user pick one:

1. Call `project` with `op: "list"` and `page_size: 100` to retrieve the project list.
2. Ask via `ask_question`:
   - **Prompt:** "Select the SD Elements project to verify against:"
   - **Options:** Each project as `{"id": "{project_id}", "label": "{project_name} (ID: {project_id})"}`
3. **Wait for user response** — do not auto-select.
4. Validate with `project_countermeasures op=list project_id={selected_id} page_size=1` to confirm access.
5. Store `project_id`, `project_name`.

#### A1-S.2: Fetch Countermeasures from SDE

SDE tracks per-CM **task status** (`DONE` / `TODO` / `NA`) and **verification status** (`pass` / `partial` / `fail` / `none`). The MCP tool exposes both:

```python
cms_raw = project_countermeasures(op="list", project_id=project_id,
                                  page_size=250,
                                  expand="text,status,problem,tags,how_tos,phase")
```

Paginate if the project has more than 250 CMs (follow `next` links or increment `page` until exhausted).

#### A1-S.3: Scope Filter by SDE Status

After fetching, ask the user which CMs to include based on SDE's own status data.

**Q-S3 — Task status filter:**

Ask via `ask_question`:
- **Prompt:** "Which countermeasures should be in scope based on their SDE task status?"
- **Options:**
  - `{"id": "done_only", "label": "Only DONE (Complete) — verify that completed CMs are actually mitigated (recommended)"}`
  - `{"id": "todo_only", "label": "Only TODO (Incomplete) — scan for unmitigated vulnerabilities"}`
  - `{"id": "all_statuses", "label": "All statuses (DONE + TODO) — full scan"}`

Store `task_status_filter`.

**Q-S4 — Verification status filter:**

Ask via `ask_question`:
- **Prompt:** "Filter by existing verification status?"
- **Options:**
  - `{"id": "unverified", "label": "Only unverified (none) — skip CMs that already have a pass/partial/fail verdict"}`
  - `{"id": "unverified_and_fail", "label": "Unverified + previously failed — re-check failures"}`
  - `{"id": "no_filter", "label": "No filter — verify all regardless of prior verification status"}`

Store `verification_status_filter`.

Apply both filters to build the in-memory CM list. Each entry gets:
- `id`, `full_id` (from SDE response)
- `sde_task_status` — the actual SDE task status (`DONE` / `TODO` / `NA`), preserved for audit
- `files_modified = []` (empty — standalone mode has no apply-fixes record; file discovery happens in subagent B1.7)
- `category` — DERIVED from the CM's `phase` (in the `expand` response) + title/text; SDE exposes NO native per-CM `category` field (same classification apply-security-fixes / generate-security-skill-files use)

CMs with task status `NA` are always excluded (not applicable = nothing to verify).

**[CHECKPOINT]** `Standalone mode: {N} countermeasures fetched from project {project_name} (ID: {project_id}) | task_status_filter: {task_status_filter} | verification_filter: {verification_status_filter}`

User confirmation:
> "Found {N} countermeasures in project {project_name} matching your filters (task_status={task_status_filter}, verification={verification_status_filter}). Proceed to scope selection? [Proceed / Cancel]"

If the user declines, the skill aborts.

After the checkpoint, proceed to **Step A1.6** (Risk Policy Check + Confirm) and then **Step A1.5+A3** (resume + scope selection). **DO NOT start Phase B or launch subagents yet -- the user MUST select a scope via `ask_question` first.**

### Step A1.6. Risk Policy Check + Confirm

> Runs in ALL modes once `project_id` is known (handoff: from the handoff file; standalone: Step A1-S; enter_project: the entered id). Read-only: the skill DISPLAYS the project's current SDE risk policy and asks the user to confirm. It does NOT change the policy.

1. Call `project` with `op: "get"` and `project_id` (reuse a prior `project op=get` response if one was already fetched) and read the current `risk_policy`.
2. Display:
   - If set: `Current risk policy for this project: {policy_name} (ID: {policy_id})`
   - If unset: `Current risk policy for this project: (none set)`
3. Ask via `ask_question`:
   - **Prompt:** "This project's risk policy (shown above) determines which countermeasures are in scope. Proceed with verification using this risk policy?"
   - **Options:**
     - `{"id": "proceed", "label": "Proceed — verify against this risk policy"}`
     - `{"id": "cancel", "label": "Cancel — I'll change the risk policy in SD Elements first, then re-run"}`
4. On `cancel` → **HARD STOP**: "Aborted at user request. Change the project's risk policy in SD Elements, then re-run this skill." The skill NEVER modifies the risk policy.
5. Store `risk_policy_id` and `risk_policy_name` (for the Step A7 plan summary and the handoff record).

**[CHECKPOINT]** `Risk policy: {policy_name} (ID: {policy_id}) — confirmed` (or `Risk policy: (none set) — confirmed`)

### Step A1.5+A3. Resume from Prior Verification Run + Scope Selection

> **ENGINE GATE (R-ZP10) — checked FIRST.** This entire step (resume detection + scope selection) is **AI-ENGINE-ONLY**. If `scan_engine in {"zeropath","hybrid"}`:
> - Do NOT present the resume or scope `ask_question`. Narrow scopes (`one_cm` / `selected_cms` / `one_by_one`) are unavailable for these engines — ZeroPath always scans the whole repo and its push updates ALL mapped CMs, and the Hybrid AI loop covers all of them too.
> - Force `scope = "all"`, `scope_args = {}`, `has_prior_run = false` (fresh; resume is not offered).
> - Emit `[CHECKPOINT] Scope forced to all (scan_engine={scan_engine} verifies all mapped/Applicable CMs); A1.5+A3 resume/scope questions skipped.`
> - Then proceed directly to **Step A2**. Skip the rest of this step.
>
> The remainder of this step applies ONLY when `scan_engine == "ai"`.

> **When a prior run exists, this step presents BOTH the resume choice and the scope choice in a single `ask_question` call (two questions, one batch).** This eliminates unnecessary back-and-forth. When no prior run exists, only the scope question is presented.
>
> **HARD GATE (scope, ai engine): The scope MUST be selected by the user via `ask_question`. You MUST NOT infer, assume, or default to any scope. If the user's initial message implies a scope (e.g., "verify all CMs"), you still MUST present the `ask_question` menu and let the user explicitly confirm. If scope is not collected here (when `scan_engine == "ai"`), Step A7's MATCH check will fail and Phase B cannot start.** (For `zeropath`/`hybrid`, scope is force-set to `all` by the engine gate above and is NOT a gathered input.)

**Phase 1 — Detect and reconcile prior run:**

Check whether a `.sde-verification-handoff.json` already exists at `{repository_path}/.sde-verification-handoff.json`. If it does:

1. **Load and validate** it (must have `source_skill == "code-scan-verification-validation"` and a valid `verification_results[]`).
2. **Extract the set of already-verified CM IDs** — all entries in `verification_results[]` that have `status` in `{pass, partial, fail}` (i.e., CMs where a verdict was derived, regardless of whether the POST succeeded).
3. **Reconcile against the canonical CM source** using set subtraction. The canonical source depends on the mode AND the selected scope:
   - **Handoff mode:** `handoff["countermeasures"]` where `cm["status"] == "Applied"`
   - **Standalone mode:** the filtered CM list from Step A1-S.3
   - **When `scope == "selected_cms"`:** the canonical set is exactly the user-SELECTED `cm_ids` (NOT the full filtered list). Otherwise a CM the prior run verified that is outside the current selection would be mis-counted (carried forward or flagged spurious) and corrupt a narrower-scope handoff.
   ```python
   # Handoff mode:
   canonical_cm_ids = {cm["full_id"] for cm in handoff["countermeasures"] if cm["status"] == "Applied"}
   # Standalone mode:
   canonical_cm_ids = {cm["full_id"] for cm in standalone_cm_list}
   # selected_cms (either mode): narrow the canonical set to exactly the selected IDs
   if scope == "selected_cms":
       canonical_cm_ids = set(scope_args["cm_ids"])

   prior_verified_ids = {r["full_cm_id"] for r in prior["verification_results"] if r["status"] in ("pass", "partial", "fail")}
   already_done = canonical_cm_ids & prior_verified_ids
   still_todo = canonical_cm_ids - prior_verified_ids
   spurious = prior_verified_ids - canonical_cm_ids
   ```
   **Resume with a narrower/different scope than the prior run:** `already_done` / `still_todo`, the per-CM disk artifacts, and the Layer-2 / tri-source checks are ALL scoped to THIS run's `canonical_cm_ids` (the current scope), never the prior run's. CMs the prior run verified that fall outside the current scope are `spurious` (warned + ignored), and the disk-count check counts only the current run's in-scope CMs — so resuming with a smaller or different CM set does NOT break the disk-vs-expected tri-source identity.
4. **Warn about spurious entries** (CMs in the prior verification results that are NOT in the canonical set):
   ```
   [WARN] Prior verification contains {len(spurious)} entries not in canonical CM set: {list(spurious)[:10]}
   These will be ignored during reconciliation.
   ```
5. Set `has_prior_run = true`.

If no `.sde-verification-handoff.json` exists, set `has_prior_run = false`.

**Phase 2 — Combined ask_question:**

**When `has_prior_run == true`:** present TWO questions in a single `ask_question` call:

- **Q1 — Resume:** "Found prior verification run ({len(already_done)} CMs already verified, {len(still_todo)} remaining). Resume or start fresh?"
  - `{"id": "resume", "label": "Resume — skip the {len(already_done)} already-verified CM(s), verify the remaining {len(still_todo)}"}`
  - `{"id": "fresh", "label": "Start fresh — ignore prior run, re-verify from scratch"}`

- **Q2 — Scope:** "Which countermeasures should I verify?"
  - `{"id": "one_cm", "label": "Verify a single CM by ID"}`
  - `{"id": "multi_cm", "label": "Verify multiple specific CMs by ID"}`
  - `{"id": "all", "label": "Verify all in-scope CMs (handoff: Applied only — Skipped and Documented excluded; standalone: all filtered CMs from SDE)"}`
  - `{"id": "one_by_one", "label": "One-by-one mode: walk through each in-scope CM with individual yes/skip/stop confirmation"}`

Both Q1 and Q2 MUST be in the same `ask_question` call so the user answers them together.

- If Q1 = `resume`: filter `in_scope` to `still_todo` only; carry forward `already_done` results into the final handoff.
- If Q1 = `fresh`: ignore the prior file; proceed as if no prior run exists.

**When `has_prior_run == false`:** present only the scope question (Q2 above) in a single `ask_question` call. Emit `[CHECKPOINT] Resume: starting fresh (no prior run)`.

**In BOTH branches (ai engine), immediately after Q2 (scope) is answered via `ask_question`, set `scope_was_user_selected = true`** — the flag the Step A7 scope gate checks (for `zeropath`/`hybrid`, scope is force-set to `all` by R-ZP10 and the gate is skipped, per the A7 scope-gate note).

**Phase 3 — CM ID follow-up (if needed):**

**Immediately after the user selects `one_cm` or `multi_cm` in Q2, prompt for the CM ID(s) BEFORE proceeding to Step A4.** This ensures the execution plan (Step A7) already contains the resolved CM list.

- **`one_cm` shortcut:** `"Enter the CM ID to verify (e.g., T123):"` -> validates exactly 1 ID.
- **`multi_cm` shortcut:** `"Enter one or more CM IDs separated by commas (e.g., T123,T145,T200):"` -> validates 1+ IDs.

The `one_cm` and `multi_cm` menu shortcuts both resolve to the canonical internal scope `selected_cms` (the only difference is the follow-up prompt copy and how many IDs are accepted). This skill's **verification** handoff (`.sde-verification-handoff.json`) stores the three canonical values: `all` / `selected_cms` / `one_by_one`. Note: the **upstream** apply-fixes handoff (`.sde-apply-handoff.json`) may contain legacy scope values (`domain=...`, `single_cm=...`, `one_by_one`) from apply-fixes' own scope selection — this field is read-only audit metadata and is NOT used to drive `filter_by_scope`. Verification always uses the user's own scope selection from this step. (The pre-3.2.0 `domain` scope was removed in beta-3.2.0 — `.sde-apply-handoff.json` does not carry CM domain data, so domain-scoped filtering was never realisable at the filter stage. Use `selected_cms` to verify a curated subset.)

`scope_args` for `selected_cms` is `{"cm_ids": [str, ...]}` (length >= 1, all IDs must exist in the canonical CM source — handoff mode: `handoff["countermeasures"]`; standalone mode: Step A1-S.3 filtered CM list — or HARD STOP).

**`Skipped` and `Documented` CMs are excluded by default** from `all` and `one_by_one` — there is nothing to statically verify (see "Scope of static verification" section). They reach the loop only via `selected_cms` when the user explicitly lists their IDs.

**`selected_cms` warning hooks (after ID collection, before loop):**

1. If any selected ID has `cm.status == "Documented"`, prompt once:
   > "You selected {N_doc} documentation-only CM(s): {ids}. Static verification will silently skip these (out of scope; see 'Scope of static verification'). Continue?"
   - `{"id": "yes_skip_docs", "label": "Yes — skip those silently, verify the rest"}` (proceeds with the full list; B0 short-circuits the doc-only ones inside the loop)
   - `{"id": "drop_docs", "label": "Drop the doc-only IDs and continue with the rest"}` (filters them out before the loop)
   - `{"id": "cancel", "label": "Cancel and re-pick"}`

2. If any selected ID has `cm.status == "Skipped"`, surface an info-only line (no prompt — the forced-`fail` lane is well-defined):
   > "Note: {N_skipped} CM(s) you selected were marked Skipped by apply-fixes ({ids}); they will receive a forced fail / high verdict."

If `one_by_one` is selected and the in-scope count is **> 20**, warn:

> "You selected one_by_one for {N} CMs. This will require {N} confirmations. Proceed? [Yes / Switch to all]"

**Legacy compatibility:** older handoffs and scripts may pass `scope: "single_cm"` (the pre-3.1.3 name). The skill aliases `single_cm` -> `selected_cms` on load and emits a one-time deprecation warning.

**[CHECKPOINT]** `Resume: {len(already_done)} CMs from prior run; {len(still_todo)} remaining` OR `Resume: starting fresh (no prior run or user declined)`

**[CHECKPOINT]** `Scope: {scope}` (emitted immediately after both resume and scope are resolved)

### Step A2. Git Tree Safety + Branch Checkout

Before ANY `git checkout`:

```bash
cd {repository_path}
# Scope the cleanliness check to TRACKED SOURCE changes only. The skill's OWN
# artifacts are expected to differ and MUST NOT trip this gate: `.sde-security/`
# scratch (regenerable) and `.sde-verification-handoff.json` (a tracked file that
# B0 deletes on a fresh run). Excluding them prevents a false HARD STOP.
git status --porcelain -- . ':(exclude).sde-security/' ':(exclude).sde-verification-handoff.json' ':(exclude).sde-apply-handoff.json' ':(exclude).sde-handoff.json'
```

- If output is **non-empty** (real source/tracked changes outside the skill's own paths) → **HARD STOP** with:
  > "Working tree is dirty (uncommitted source changes). Stash or commit your changes before running code-scan-verification-validation."
- If output is **empty** → proceed. (Differences confined to `.sde-security/` scratch or `.sde-verification-handoff.json` are the skill's own artifacts and are intentionally ignored — a genuine source change still HARD STOPs.)

**Branch checkout (mode-dependent):**

- **Handoff mode:** if `handoff.security_branch` is set, run `git checkout {handoff.security_branch}`. If the branch does not exist locally, report it and ask the user whether to proceed on the current branch (degraded mode — verdicts may be misleading).
- **Standalone mode:** no `security_branch` is available from a handoff. Ask via `ask_question`:
  - **Prompt:** "Which branch should I verify? (current: `{current_branch}`)"
  - **Options:**
    - `{"id": "current", "label": "Stay on current branch ({current_branch})"}`
    - `{"id": "other", "label": "Switch to a different branch"}`
  - If `other`: follow-up text prompt for branch name; run `git checkout {branch}`. If the branch does not exist, HARD STOP.

**[CHECKPOINT]** `Git tree clean; checked out {branch_name}`

### Step A3. (Merged into Step A1.5+A3)

Scope selection has been merged into Step A1.5+A3 above. If you reach this step, scope and resume have already been collected. Proceed to Step A4.

### Step A4. Fail-Verdict Status-Rollback Opt-In

Creating a Verification Note via `verification op=create` updates the task's derived **verification status** (`pass` / `partial` / `fail` / `none`). It can also atomically set the task's **countermeasure (task) status** (`TODO` / `DONE` / `NA`) via the optional `task_status_mapping` field. These are two separate concepts (see "Status concepts" section above). A `pass` verdict should always bump the task to `DONE`. A `fail` verdict, however, could undo the `DONE` that `apply-fixes` set, which is destructive if the user is mid-review.

Ask the user:

- **Prompt:** "If a CM verifies as FAIL, should I also roll its SDE task status back to TODO?"
- **Options:**
  - `{"id": "no_verification_only", "label": "No — only update verification_status, leave workflow status alone (recommended)"}`
  - `{"id": "yes_rollback", "label": "Yes — also set task status to TODO on fail"}`

Regardless of the answer, `pass → DONE` is **always** sent. Partial verdicts never touch workflow status.

> **Note (hybrid):** ZeroPath's scan push has ALREADY auto-marked every mapped CM `DONE` before this skill posts its combined note. So if you choose "No rollback", a later `fail` verdict records `verification_status=fail` but the task **stays DONE** — a misleading "Done + Failed" state. For `scan_engine == "hybrid"`, prefer **`yes_rollback`** if you want failures to actually show as not-done. (In `ai`/`zeropath` engines this caveat does not apply: `ai` never pre-marks DONE, and `zeropath` posts no skill note.)

**[CHECKPOINT]** `Scope: {scope}; fail-rollback: {yes_rollback | no_verification_only}`

### Step A5. Batch Size Selection

**Engine-skip guard (zeropath):** If `scan_engine == "zeropath"`, do NOT ask this question — ZeroPath-Only runs no AI per-CM loop, so batch size is meaningless. Set `batch_size = "n/a"` and skip this step entirely. Output:
```
[CHECKPOINT] Batch size: n/a (ZeroPath-Only has no AI loop)
```

**Auto-skip guard:** If `scope == "selected_cms"` and the resolved CM list contains exactly 1 CM, set `batch_size = 1` and skip this step entirely (there is nothing to batch). Output:
```
[CHECKPOINT] Batch size: 1 (auto — single CM selected); parallel subagents: 1
```

Otherwise (engine `ai` or `hybrid`), ask the user via `ask_question`:

- **Prompt:** "How many CMs should each verification batch contain? (Each batch processes N CMs sequentially. Higher = fewer launches but more per-batch context usage. If inline fallback activates in Step A6, batch size is forced to 1.)"
- **Options:**
  - `{"id": "1", "label": "1 — one CM per subagent (original behavior, slowest but most isolated)"}`
  - `{"id": "5", "label": "5 — small batches"}`
  - `{"id": "10", "label": "10 — recommended for 100+ CMs (default)"}`
  - `{"id": "20", "label": "20 — aggressive batching (for very large projects)"}`

Store `batch_size` as an integer. Default is 10 if the user does not override.

**[CHECKPOINT]** `Batch size: {batch_size}; parallel subagents: 5`

### Step A6. Subagent Capability Probe

Per the SUBAGENT / DELEGATION POLICY (top of this file), subagent batching is permitted in ANY environment (including Cursor) provided the subagent `model` is set explicitly to the parent's model and is NEVER `composer-2.5-fast`. (This governs the AI loop in `ai`/`hybrid`; `zeropath` has no AI loop.) Run the probe:

1. Determine the parent agent's model. Attempt to launch a trivial `generalPurpose` subagent with `model` set explicitly to the parent's model (e.g., a prompt that returns a known string). If it succeeds, set `execution_mode = "subagent"` and proceed to the next Phase A step (**A-ZP1 if `scan_engine in {"zeropath","hybrid"}`, else A7**).
2. If you CANNOT set the subagent's `model` to the parent's model (or the launch fails / `generalPurpose` is unavailable), activate **inline fallback mode**: set `execution_mode = "inline"`. Inline is the fallback ONLY when same-model delegation is unavailable — it is NOT forced by environment.

After the probe (and the inline-fallback handling below), proceed to **Step A-ZP1** when `scan_engine in {"zeropath","hybrid"}`, otherwise to **Step A7**.

**Inline fallback mode activation:**

```
[WARN] This MCP client does not support subagent generation.
Verification will run INLINE in the parent context.
Large CM sets may exhaust the context window.
Batch size forced to 1; parallel dispatch disabled.
```

- `batch_size` is forced to `1` (process CMs one at a time inline). The user's Step A5 selection is overridden.
- Parallel dispatch is disabled (only one CM processed at a time).
- **Context-window warnings** (the "reduce scope" remediation applies to `scan_engine == "ai"` ONLY — for `hybrid` the AI loop MUST cover all CMs (R-ZP10), so scope CANNOT be reduced):
  - If `in_scope_total > 20`: `"[WARN] {in_scope_total} CMs will run inline. Context exhaustion is likely."` — **(ai)** add `" Consider reducing scope to selected_cms with a smaller set."`; **(hybrid)** add `" Scope is fixed to all (R-ZP10); checkpoint-and-resume across turns will be used, or run in a non-Cursor client to enable parallel subagents."`
  - If `in_scope_total > 50`: `"[HARD RECOMMEND] {in_scope_total} CMs inline will almost certainly exhaust the context window."` — **(ai)** `" Strongly recommend reducing scope to selected_cms (max ~20 CMs) or one_by_one mode. Proceed anyway? [Proceed / Reduce scope]"` (on `Reduce scope`, return to Step A1.5+A3); **(hybrid)** `" Scope cannot be reduced (R-ZP10); the run will checkpoint every 5 CMs and resume across turns. Proceed? [Proceed / Cancel]"` (no scope-reduction option).
- **Context checkpointing:** After every 5 CMs processed inline, the agent outputs a `=== CONTEXT CHECKPOINT ===` block (see Context Limit Handling below) so the user can resume if the window runs out.
- **Rule 12 relaxation (AGENTS.md Rule 9):** In inline fallback mode, B1 fetch, B2 analysis, B3 verdict, B4 note-fetch, and B5 POST run in the parent context instead of a subagent. This is the inline-fallback exception to Rule 12's "subagents only" constraint; the other scoped exception is the parent forced-fail short-circuit POST (B0b/B0b2 run B4+B5 inline — see the forced-fail POST exception in Rule 9).

**[CHECKPOINT]** `Execution mode: {subagent | inline}` (if inline, also `batch_size forced to 1; context-window warning issued`)

### Step A-ZP1. ZeroPath Setup — Repo, Mapping, Sync, Coverage (zeropath | hybrid ONLY)

> Runs after A6 and before A7, only when `scan_engine in {"zeropath","hybrid"}`. By now `sdeProjectId` is known (handoff `project_id` / standalone selection / `enter_project`). All HARD STOPs below are descriptive blockers.

1. **Resolve `sdeProjectId`:** handoff → `handoff["project_id"]`; standalone/enter_project → the selected/entered id. (`project op=get` gives `project_name` for the plan/report.)
2. **Resolve the ZeroPath repository:**
   - Call `repositories_list {search: repo_name}`. Present matches via `ask_question` (`{"id":"{repositoryId}","label":"{name} ({vcs.url or vcsType})"}`), plus:
     - `{"id":"manual","label":"Enter a ZeroPath repository id or git URL directly"}`
   - If `manual` and a repo id is given → use it. If a git URL is given and no repo exists for it → call `repositories_addByUrl {url}` to add it, then use the new `repositoryId`.
   - If no match and no manual entry → HARD STOP: "Repository {repo_name} is not in ZeroPath. Add it (repositories_addByUrl) or pick an existing repo."
   - Validate the chosen repo has a scannable `vcs.vcsType` (`genericGit` or `uploaded`). Store `repositoryId`.
3. **Mapping (idempotent):** call `securityCompass.getIntegration`. If a `projectMappings[]` entry exists for (`sdeProjectId`, `repositoryId`), reuse its `id` as `mappingId`. Otherwise call `securityCompass.addProjectMapping {sdeProjectId, repositoryId}` → store the returned `id` as `mappingId`. (Never create a duplicate mapping for the same triple.)
4. **Sync rules:** call `securityCompass.syncRules {mappingId}`. On HTTP 409 ("sync already running") → wait ~5s and retry, up to 2 retries. Capture `countermeasuresFetched / sastDetectable / rulesCreated / skipped`.
5. **Coverage:** call `securityCompass.getMappingAudit {mappingId}` → per-CM `coverage` (`sast | nl_rule | unsupported`), `supportedCount / totalCount`. Store for the report and (hybrid) merge.
6. **Scan branch selection + commit/push verification (CRITICAL — R-ZP11):** ZeroPath scans a **branch on the remote it clones** (`repositories_list` → `vcs.url`), defaulting to the repo's default branch (usually `main`). Your hardening work is almost always on a different branch, so you MUST tell ZeroPath which branch to scan AND that branch MUST be committed + pushed to that remote first — otherwise ZeroPath scans stale code (or fails).
   - **6a. Ask the branch** via `ask_question`. **Default `scan_branch` to the branch A2 checked out (`branch_name`)** so the scan matches the working branch.
     - **Prompt:** "Which branch should ZeroPath scan? (ZeroPath scans the remote `{vcs.url}`. Default = the checked-out branch `{branch_name}`.)"
     - **Options:** `{"id":"checked_out","label":"The checked-out branch ({branch_name}) — recommended"}`, `{"id":"default","label":"Repository default branch ({repo.defaultScanTargetBranch or 'main'})"}`, `{"id":"other","label":"Enter a different branch name"}`. Store `scan_branch`.
   - **6a-HYBRID coherence gate (R-ZP11) — `hybrid` only:** the Hybrid AI loop reads the LOCAL files on A2's checked-out branch (`branch_name`), while ZeroPath scans `scan_branch` on the remote. These MUST be the same branch or the merge compares mismatched code. If `scan_engine == "hybrid"` AND `scan_branch != branch_name` → **HARD STOP**: "Hybrid requires the ZeroPath scan branch and the locally-verified (AI-loop) branch to match. You picked `{scan_branch}` but the checked-out branch is `{branch_name}`. Either choose the checked-out branch, or re-run A2 to check out `{scan_branch}` first." (ZeroPath-Only has no AI loop, so any `scan_branch` is allowed there.)
   - **6b. Verify committed:** if a local clone exists at `repository_path`, run `git -C {repository_path} status --porcelain -- . ':(exclude).sde-security/' ':(exclude).sde-verification-handoff.json' ':(exclude).sde-apply-handoff.json' ':(exclude).sde-handoff.json'` (the skill's OWN scratch/handoff are expected to differ and MUST NOT trip this gate; scope the check to tracked SOURCE changes). If non-empty (uncommitted SOURCE changes on `scan_branch`) → **HARD STOP**: "Uncommitted source changes on `{scan_branch}`. Commit them, then push the branch — ZeroPath can only scan committed+pushed code. (No PR needed.)"
   - **6c. Verify pushed to the ZeroPath remote:** capture `local_sha = git -C {repository_path} rev-parse {scan_branch}` and `remote_sha = git ls-remote --heads {vcs.url} {scan_branch}` (first column).
     - If `scan_branch` is **absent on the remote** → **HARD STOP**: "Branch `{scan_branch}` is not on the ZeroPath remote `{vcs.url}` (it only has the branches ZeroPath can see). You MUST push it first: `git push -u origin {scan_branch}`. ZeroPath cannot scan an unpushed branch. (No PR required — just push the branch.)"
     - If present but `remote_sha != local_sha` (unpushed local commits) → **HARD STOP**: "`{scan_branch}` on the remote is at `{remote_sha}` but your local HEAD is `{local_sha}` — you have unpushed commits. Run `git push origin {scan_branch}` so ZeroPath scans your latest work."
     - Else (present and `remote_sha == local_sha`) → store `scan_branch_remote_sha = remote_sha`; proceed.
   - **6d. No local clone?** If `repository_path` has no git checkout of `scan_branch`, still run `git ls-remote --heads {vcs.url} {scan_branch}`; if absent → HARD STOP (same push instruction). The skill NEVER pushes on the user's behalf — it only verifies and instructs.

**[CHECKPOINT]** `ZeroPath setup: project {sdeProjectId} <-> repo {repo_name} ({repositoryId}); mapping {mappingId}; sync {sastDetectable} sast / {rulesCreated} rules; supported {supportedCount}/{totalCount}; scan_branch={scan_branch} @ {scan_branch_remote_sha} (pushed)`

> **Scope is forced to `all` for `zeropath`/`hybrid`** (Step A1.5+A3 is skipped by the engine gate — R-ZP10). ZeroPath always scans the whole repo and its push updates all `{totalCount}` mapped CMs in project `{sdeProjectId}`; the Hybrid AI loop covers all of them too. There are no narrow-scope options for these engines. To verify a curated subset without scanning/mutating the rest, use `scan_engine == "ai"`.

### Step A-ZP2. Authoritative Source (hybrid only)

**Q1 — Authoritative source (HYBRID ONLY):** one choice for the entire run.
- **Prompt:** "When AI and ZeroPath disagree on a CM, which result sets the SDE verification status?"
- **Options:**
  - `{"id":"ai","label":"AI (recommended — ZeroPath 'pass' is pass-by-absence, not proof the control exists)"}`
  - `{"id":"zeropath","label":"ZeroPath"}`

Store `authoritative_source = "ai" | "zeropath"` (hybrid only; unused for zeropath).

**Scan timeout (NOT asked):** the skill does NOT ask the user for a scan timeout. Set an internal default `scan_timeout_ms = 1800000` (30 minutes) used only as a safety cap; the scan status is polled every 1 minute (see Phase B-ZP / B-HYB). This applies to both `zeropath` and `hybrid`. **For `zeropath`, A-ZP2 asks NOTHING** (no authoritative-source question, no timeout question) — it falls through to A7.

**[CHECKPOINT]** (hybrid only) `Authoritative source: {authoritative_source}; scan polling: every 1 min (30-min default cap)`

### Step A7. Execution Plan Summary + Confirmation

After the subagent probe (and, for zeropath/hybrid, A-ZP1/A-ZP2), the agent MUST output the Phase A verification block summarizing every collected input (including `execution_mode` from A6) and wait for user confirmation. This serves as both the Phase A verification gate and the execution plan the user reviews before authorizing the run.

```
=== PHASE A VERIFICATION — EXECUTION PLAN ===
Scan engine: {scan_engine}
ZeroPath setup (zeropath|hybrid only):
  Repo: {repo_name} ({repositoryId}) | Mapping: {mappingId}
  Scan branch: {scan_branch} @ {scan_branch_remote_sha} (committed + pushed; hybrid: == checked-out {branch_name})
  Sync: {sastDetectable} sast / {nl_rule_count} nl_rule / {unsupported_count} unsupported (supported {supportedCount}/{totalCount})
  Authoritative source (hybrid): {authoritative_source} | Scan polling: every 1 min (30-min default cap)
  ⚠️ SIDE EFFECT: starting a ZeroPath scan will AUTO-UPDATE mapped CM statuses in SDE project {sdeProjectId}.
Mode: {verification_mode}
Repository: {repository_path}
Branch: {branch_name}
CM source:
  (handoff)    Handoff file: {N} CMs ({A} Applied / {D} Documented / {S} Skipped)
  (standalone) SDE project: {project_name} (ID: {project_id}), {N} CMs
               task_status_filter: {task_status_filter}
               verification_filter: {verification_status_filter}
Risk policy: {risk_policy_name} (ID: {risk_policy_id}) [confirmed] | (none set) [confirmed]
Resume: {resuming from prior ({already_done} done, {still_todo} remaining) | fresh start}
Scope: {scope} {scope_args if selected_cms} ({ai: user-selected in A1.5+A3: YES | zeropath|hybrid: all (forced — engine verifies all mapped CMs; A1.5+A3 skipped)})
Fail-rollback: {yes_rollback | no_verification_only}
Execution mode: {ai|hybrid: subagent | inline ; zeropath: n/a (no AI loop)}
Batch size: {ai|hybrid: {batch_size} | parallel: {5 if subagent, 1 if inline} ; zeropath: n/a (no AI loop)}
Estimated launches: {ai|hybrid: ceil(in_scope_total / batch_size) {subagent batches | inline iterations} ; zeropath: n/a}

Inputs gathered: {count}/{expected}
MATCH: {count} == {expected}? {YES/NO}
==============================================
```

Print the line matching the current `verification_mode`; omit the other.

**Scope gate (before counting):**
```python
# scope is user-selected via A1.5+A3 for the `ai` engine ONLY. For zeropath/hybrid, A1.5+A3 is
# skipped and scope is force-set to "all" (R-ZP10) -- so the user-selection assertion applies to
# `ai` only; asserting it for zeropath/hybrid would wrongly HARD STOP a valid run.
if scan_engine == "ai":
    assert scope_was_user_selected, \
        "HARD STOP: scope was not collected via ask_question in Step A1.5+A3. Return to A1.5+A3."
```
For `scan_engine == "ai"`, if `scope` is not set or was not gathered via an explicit `ask_question` call in Step A1.5+A3, the MATCH check below MUST fail — do NOT infer a default scope to make it pass. For `zeropath`/`hybrid`, `scope` is force-set to `all` by R-ZP10 (not a gathered input) and this assertion is skipped.

**Expected input count (computed dynamically per `scan_engine` × `verification_mode`):**
- Base AI inputs: handoff = 10 (MCP, mode+repo, handoff confirm, risk-policy confirm, resume, git, scope, fail-rollback, batch size, subagent probe); standalone = 12 (adds project selection + the 2 SDE status filters); `enter_project` = **12 for `ai`/`hybrid`**. **`resume` is CONDITIONAL — gathered ONLY when a prior run exists; on a FRESH run subtract 1 from the base (fresh handoff = 9, fresh standalone = 11). `expected = base - (0 if has_prior_run else 1)`; never loop back to collect `resume` on a fresh run.** (For zeropath/hybrid, resume is already dropped via R-ZP10, so this conditional applies to the `ai` engine paths.) (identical inputs to `standalone` — a typed project-id entry replaces the project-list pick, and the 2 SDE status filters ARE gathered per A0.5) and **= 10 for `zeropath`** (ZeroPath-Only gathers no status filters; the typed id just replaces the project pick). The Step A1.6 risk-policy confirm is gathered in ALL modes/engines (included in base).
- `scan_engine == "ai"`: base + 1 (A0.0 engine selection — the scan-engine question is asked for EVERY engine, see Step A0.0, so `ai` counts it too; zeropath/hybrid add the same +1 below). resume + scope ARE gathered in A1.5+A3.
- For `zeropath`/`hybrid`, **A1.5+A3 is skipped (R-ZP10)** so its inputs are NOT gathered: subtract `resume` and `scope` from the base. The A-ZP2 scan-timeout question is removed for BOTH engines (replaced by a fixed 30-min default cap + 1-min polling), so it is NOT a gathered input. The A5 batch question is additionally skipped for `zeropath` (no AI loop). Then add the engine inputs:
  - `scan_engine == "zeropath"`: (base - 3) [drop resume, scope, batch] + 1 (A0.0 engine) + 1 (A0-ZP preflight) + 1 (A-ZP1 setup).
  - `scan_engine == "hybrid"`: (base - 2) [drop resume, scope] + 1 (A0.0) + 1 (A0-ZP) + 1 (A-ZP1) + 1 (A-ZP2 authoritative source).
Compute `expected` from this formula for the active engine×mode; MATCH compares the dynamically computed `expected`. `scope` is force-set to `all` for zeropath/hybrid and is NOT counted as a gathered input. (A2 git, A4 fail-rollback, A6 probe are still gathered for ALL engines; **A5 batch is SKIPPED and not counted for `zeropath`** (no AI loop) but gathered for `ai`/`hybrid`; the **A-ZP2 scan-timeout question is removed for both engines** and not counted.) The formula is a guide: MATCH ultimately compares the count of inputs ACTUALLY gathered this run; if a difference is solely due to how `enter_project`'s CM-fetch + status-filter inputs are bundled vs counted separately, treat the gathered count as authoritative and do NOT fail MATCH on that ambiguity.

**If MATCH = NO:** return to the first missing Phase A step and re-collect. Do NOT proceed until YES.

**If MATCH = YES:** ask via `ask_question`:
- **Prompt:** "Proceed with this execution plan?"
- **Options:**
  - `{"id": "proceed", "label": "Proceed — start Phase B verification"}`
  - `{"id": "cancel", "label": "Cancel — abort the skill"}`

If `cancel`, the skill aborts. Only on `proceed` does Phase B begin.

**[CHECKPOINT]** `Phase A complete: {count}/{expected} inputs gathered; user confirmed execution plan`

---

## Phase B: Engine Router

Phase B routes by `scan_engine`:

- **`scan_engine == "ai"`** → run the **AI Per-CM Verification Loop** below VERBATIM (the original engine). No ZeroPath calls.
- **`scan_engine == "zeropath"`** → run **Phase B-ZP (ZeroPath-Only Engine)** instead of the AI loop. The skill triggers a ZeroPath scan, waits, confirms the push, and reports. It posts NO verification notes (R-ZP2). Then write the handoff (Step D, `scan_engine="zeropath"`) and the ZeroPath-Only completion block.
- **`scan_engine == "hybrid"`** → run **Phase B-HYB (Hybrid Engine)**: kick off the scan non-blocking, run the AI Per-CM Loop below with **B5 deferred** (R-ZP3), then merge and post one combined note per in-scope CM. Then write the handoff (`scan_engine="hybrid"`) and the Hybrid completion block.

The AI Per-CM Verification Loop (immediately below) is the shared engine used by `ai` (posts notes in-loop) and by `hybrid` (returns verdicts, defers the POST). Phase B-ZP and Phase B-HYB are defined after Step B3.

## Phase B: Per-CM Verification Loop (AI engine — used by `ai`, and by `hybrid` with B5 deferred)

> **Scope note for `hybrid`:** when this loop is invoked by the Hybrid engine, `scope` is always `"all"` (forced by R-ZP10 — A1.5+A3 is skipped), so `in_scope` is the full mapped/Applicable CM set and the user-scope paths below — B0a-under-`selected_cms`, the B0c `one_by_one` prompt, and `selected_cms` ID handling — are **inert** (never triggered). They apply only to `scan_engine == "ai"`. ZeroPath-Only does not run this loop at all.

Phase B is a **parent-orchestrator + batched-verification** architecture. The parent loop does scope filtering, short-circuit lanes (mode-dependent — see below), the `one_by_one` user prompt, progress output, and result-recording — nothing else. For each batch of in-scope CMs that survive the parent short-circuits: when `execution_mode == "subagent"`, the parent dispatches **one `generalPurpose` subagent per batch** which performs the full B1 + [B1.5 or B1.7] + B2 + B3 + B4 + B5 cycle for each CM in its batch, sequentially, within its own isolated context (fetch ctx via MCP -> AI analysis on files -> fetch existing notes -> POST verification note via MCP), and returns a **JSON array** of small structured results; when `execution_mode == "inline"` (Step A6 fallback), the parent itself executes the same B1+B2+B3+B4+B5 cycle in-context with `batch_size=1`. When `execution_mode == "subagent"`, no `ctx`, no file contents, no payload ever lives in the parent's conversation history. When `execution_mode == "inline"`, context does accumulate in the parent — see Step A6 context checkpoints.

**Mode-dependent parent short-circuits:**

- **Handoff mode:** two to four lanes — B0a (Documented out-of-scope), B0b (upstream-Skipped forced-fail), and when `handoff_version == "2"` provides `cm.category`: B0b2 (code-CM empty-files forced-fail), B0b3 (non-code-CM empty-files out-of-scope). When `handoff_version == "1"` (no `cm.category`), the empty-`files_modified[]` discriminator is enforced inside the subagent (L-FF2-sub / L-OOS-sub in B1.5).
- **Standalone mode:** no handoff-derived short-circuits (B0a/B0b/B0b2/B0b3 are all inapplicable because there is no upstream `status` or `files_modified[]` from apply-fixes). All CMs pass through to per-CM verification (via subagent or inline — see Step A6). The verification context performs **file discovery** (B1.7) before analysis (B2). The only parent-level gate is B0c (`one_by_one` user prompt).

The architecture exists to bound parent context across large projects: a 431-CM project with inline execution would accumulate ~431 ctx blobs (incl. fat `how_tos[]`) + ~1000+ file contents + 431 prompts + 431 payloads in the parent, blowing out the context window. With batched-subagent dispatch (default `batch_size=10`), the parent retains only ~431 small verdict-summary records across ~44 subagent launches (instead of 431). Each subagent's context holds ~10 MCP responses + ~10-30 file reads, well within subagent context limits.

### Batching and Retry/Timeout

**Batch size** is configurable via Step A5 (default 10). CMs that survive the parent short-circuits (handoff mode: B0a/B0b/B0b2/B0b3/B0c — where B0b2/B0b3 fire only when `handoff_version == "2"`; standalone mode: B0c only) are collected into batches of `batch_size` CMs. When `execution_mode == "subagent"`, each batch is dispatched to one `generalPurpose` subagent and up to 5 subagents may be dispatched in parallel per round (so each round processes up to `5 × batch_size` CMs). When `execution_mode == "inline"`, batches are processed sequentially in-context with `batch_size=1` (see Step A6 inline fallback).

### Batch plan + per-batch mini-gate (T5 — anti-sampling)

> **Engine gating:** the BATCH PLAN + mini-gates apply to the AI per-CM loop — `scan_engine == "ai"` and the `hybrid` AI loop. **`zeropath` has NO AI loop (single repo-wide scan), so the batch plan is N/A there** (its completeness is the Sum-check over mapped CMs in Phase B-ZP).

**ANCHORING RULE:** the loop denominator `in_scope_total` MUST come from the source of truth (the scope-filtered CM set; for `zeropath`/`hybrid` `scope` is forced to `all` per R-ZP10, so `in_scope_total` = every mapped/Applicable CM), NEVER from "CMs processed so far." Emit the batch plan ONCE before the AI loop; it IS your execution contract:

```
=== PHASE B BATCH PLAN (ai / hybrid AI loop) ===
in_scope_total (from source of truth): {N}
Batch size: {B}   Total batches: {ceil(N/B)}
Batch 1/{t}: {cm_ids...}   ...   Batch {t}/{t}: {cm_ids...}
================================================
```

Per batch, after the subagent returns (or inline processing completes) AND each result is offloaded to disk (T6; hybrid offloads a DEFERRED artifact per-CM DURING the loop — overwritten with the combined record after the merge — so `d` is non-zero mid-loop and this mini-gate is satisfiable for hybrid):

```
--- BATCH {k}/{t} COMPLETE ---
Expected (this batch): {b_k}   [VERIFY] lines emitted: {c}   Disk artifacts written this batch: {d}   BATCH PASS: {c}=={b_k} AND {d}=={b_k}? {YES/NO}
[RUNNING CHECK] disk artifacts total {disk}/{N} | batches {k}/{t} | on track? {Y/N} | reloaded §Phase B from disk? YES | sentinel: "{verbatim line}"
---
```

If `BATCH PASS = NO`: reprocess the missing CMs in THIS batch and re-run the mini-gate; do NOT advance until YES. The count of individually processed CMs (per-CM `[VERIFY]` + per-CM disk artifact) is the ONLY basis for the completion gate.

**Gate-the-gate precondition (the `ai`/`hybrid` Phase B completion block is INVALID if unmet):** the `=== PHASE B BATCH PLAN ===` header was emitted, AND a `--- BATCH k/t COMPLETE ---` mini-gate appeared for EVERY batch (count of mini-gates == total batches). (`zeropath` is exempt — no AI loop.)

### Anti-sampling (T8 — 3 layers + ban-phrase HARD STOP)

Three independent layers prevent the AI loop (`ai`/`hybrid`) from stopping early or sampling:
1. **Durable per-CM disk proof** — one `.sde-security/verify/{project_id}/cm-work/{full_cm_id}.json` per in-scope CM (T6); `verify_disk_vs_sde` counts them.
2. **Gate-the-gate** — the completion block cannot be filled until the BATCH PLAN + a mini-gate for EVERY batch exist (above).
3. **Ban-language HARD STOP** — if ANY of these phrases appears in your reasoning about loop scope, STOP, discard the conclusion, return to the BATCH PLAN, and process every remaining in-scope CM: "key CMs" / "across all categories" / "the pattern is clear" / "the rest have/are" / "only N ..." / "N+" / "representative" / "pragmatic" / "efficient" / "Let me finalize" (pre-completion) / "move forward to more impactful steps".

The count of individually processed CMs (per-CM `[VERIFY]` + per-CM disk artifact) is the ONLY basis for the completion gate — never a summary judgment or in-memory tally. (`zeropath`'s completeness is the Phase B-ZP Sum-check over mapped CMs.)

**Retry/timeout** protects against subagent startup stalls:

- **Timeout:** If a subagent does not return within `subagent_timeout_ms` (default 300000 = 5 minutes), the parent kills it and re-launches with the same batch.
- **Max retries:** 2 retries per batch (3 total attempts). After exhaustion, every CM in the batch is recorded as `partial`/`low` with finding category `subagent-timeout` and `note_post_status="FAILED:subagent-timeout"`.
- Timeout/retry is transparent to the subagent — the subagent prompt and procedure are identical on each attempt.

### No-False-Positives Invariant (CANONICAL)

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

This invariant appears in five places: this section (full callout), Step B3 verdict matrix preamble (full callout, content-identical), the Numbered Enforcement Rules (Rule 5, abbreviated reference + 4-source list), AGENTS.md Rule 5 (full callout, content-identical with this section), and the Subagent Prompt Template appendix (the template is plain text inside a code fence so it cannot use Markdown blockquote syntax, and uses section headers to distinguish handoff/standalone fail sources instead of inline annotations). All five mentions are content-equivalent: they convey the same four fail sources, the same "(handoff mode only)" scope restriction on sources (3) and (4), and the same standalone-mode clarification.

### Parent loop pseudocode

```python
# CM source depends on mode
if verification_mode == "handoff":
    cm_source = handoff["countermeasures"]
else:  # standalone
    cm_source = standalone_cm_list  # built in Step A1-S.3

in_scope = filter_by_scope(cm_source, scope, scope_args)
in_scope_total = len(in_scope)
done = 0
results = []

if in_scope_total == 0:
    print("[INFO] No in-scope CMs after filtering. Nothing to verify; writing empty handoff.")
    # falls through to handoff emission with all-zero totals; Sum check 0 == 0 → YES

# ── Phase 1: Parent short-circuits ────────────────────────────────────
# These run per-CM BEFORE batching. CMs consumed here never enter a batch.
# In handoff mode: B0a/B0b always fire; B0b2/B0b3 fire only when handoff v2.
# In standalone mode: B0a/B0b/B0b2/B0b3 are all SKIPPED (no upstream status
#   or files_modified from apply-fixes). Only B0c (one_by_one prompt) applies.
subagent_eligible = []
aborted = False
for cm in in_scope:
    done += 1

    # ── Handoff-mode-only short-circuits ──
    if verification_mode == "handoff":

        # Step B0a. Documented under selected_cms — defensive guard.
        if cm.status == "Documented":
            results.append(record_out_of_scope(cm, reason="documentation-only CM; static verification not applicable"))
            print(f"[SKIP-OOS] {done}/{in_scope_total} | {cm.full_id} | out-of-scope (Documented)")
            continue

        # Step B0b. Upstream-Skipped — forced fail/high + B4+B5 POST.
        #   HYBRID: defer the POST — record the forced-fail verdict with
        #   note_post_status="DEFERRED_HYBRID"; the Phase B-HYB merge treats these
        #   deferred forced-fails as ai_status="fail" (record_verified does not persist
        #   ai_status, so the merge defaults it). Do NOT post inline in hybrid.
        #   NOTE: unreachable under zeropath/hybrid — R-ZP10 forces scope="all" and the
        #   `all` filter excludes Skipped CMs, so this branch only fires via selected_cms
        #   (AI-engine only). Only B0b2 (Applied code CM, empty files) fires for zp/hybrid.
        if cm.status == "Skipped":
            verdict = forced_fail(cm, reason="CM was skipped by apply-fixes; no mitigation present", category="residual-vulnerable-pattern")
            if scan_engine == "hybrid":
                results.append(record_verified(cm, verdict, note_post_status="DEFERRED_HYBRID"))
                print(f"[VERIFY] {done}/{in_scope_total} | {cm.full_id} | verdict=fail | confidence=high | note=DEFERRED_HYBRID")
                continue
            existing_notes = fetch_existing_notes(project_id, cm.full_id)  # B4 inline (ai engine)
            post_status = post_verification_note(project_id, cm, verdict, existing_notes)  # B5 inline (ai engine)
            results.append(record_verified(cm, verdict, note_post_status=post_status))
            print(f"[VERIFY] {done}/{in_scope_total} | {cm.full_id} | verdict=fail | confidence=high | note={post_status}")
            continue

        # Step B0b2. Parent code-CM forced-fail (handoff v2 only) + B4+B5 POST.
        #   HYBRID: same deferral as B0b.
        if handoff_has_category and cm.category in ("CODE_FIX", "ML_CODE") and len(cm.files_modified) == 0:
            verdict = forced_fail(cm, reason="code CM (CODE_FIX/ML_CODE) with no modified files", category="residual-vulnerable-pattern")
            if scan_engine == "hybrid":
                results.append(record_verified(cm, verdict, note_post_status="DEFERRED_HYBRID"))
                print(f"[VERIFY] {done}/{in_scope_total} | {cm.full_id} | verdict=fail | confidence=high | note=DEFERRED_HYBRID (parent B0b2)")
                continue
            existing_notes = fetch_existing_notes(project_id, cm.full_id)  # B4 inline (ai engine)
            post_status = post_verification_note(project_id, cm, verdict, existing_notes)  # B5 inline (ai engine)
            results.append(record_verified(cm, verdict, note_post_status=post_status))
            print(f"[VERIFY] {done}/{in_scope_total} | {cm.full_id} | verdict=fail | confidence=high | note={post_status} (parent B0b2)")
            continue

        # Step B0b3. Parent non-code-CM out-of-scope (handoff v2 only).
        if handoff_has_category and cm.category in ("INFRA", "ML_DOC") and len(cm.files_modified) == 0:
            results.append(record_out_of_scope(cm, reason="non-code CM with no modified files; static verification not applicable (parent B0b3)"))
            print(f"[SKIP-OOS] {done}/{in_scope_total} | {cm.full_id} | out-of-scope (parent B0b3: {cm.category}, empty files_modified)")
            continue

    # (standalone mode: no handoff-derived short-circuits — all CMs proceed to batching)

    # Step B0c. one_by_one user prompt (parent loop).
    if scope == "one_by_one":
        show_cm_summary(cm)
        resp = ask_question("Verify this CM?", ["yes", "skip", "stop"])
        if resp == "skip":
            results.append(record_skipped(cm, reason="user skipped"))
            print(f"[SKIP-USER] {done}/{in_scope_total} | {cm.full_id} | user skipped")
            continue
        if resp == "stop":
            # `stop` halts COLLECTION only. Any pre-stop "yes" CMs already in
            # subagent_eligible MUST still be verified in Phase 2 — do NOT set
            # `aborted` (that flag is reserved for the involuntary auth-failure
            # abort, which alone must skip Phase 2). Record the stop CM + every
            # unreached CM as user-stopped, then break out of Phase-1 collection.
            results.append(record_skipped(cm, reason="user stopped (loop terminated at this CM)"))
            for c in in_scope[done:]:
                results.append(record_skipped(c, reason="user stopped (loop terminated; not reached)"))
            remaining_recorded = 1 + (in_scope_total - done)
            print(f"[STOP] User stopped at {done}/{in_scope_total}; recorded {remaining_recorded} CMs as user-stopped (pre-stop 'yes' CMs still verified in Phase 2) to preserve Sum-check identity")
            break   # halt collection; Phase 2 still runs for the already-collected subagent_eligible
        # resp == "yes": accept this CM and CONTINUE the loop. This ask_question ENDED the
        # turn; when the user replies, resume the LOOP to the NEXT in-scope CM (on resume,
        # re-derive the done-set from cm-work/*.json — never restart, never finalize).
        # Accepting ONE CM is NOT completion: do NOT emit a completion block or any
        # "complete"/"SKILL COMPLETE" line here — {in_scope_total - done} CMs still remain.
        print(f"[ONE-BY-ONE] {done}/{in_scope_total} accepted; {in_scope_total - done} remaining — continue to the NEXT CM (do NOT stop or declare complete)")

    subagent_eligible.append(cm)

# ── Phase 2: Batched subagent dispatch ─────────────────────────────────
# CMs that survived B0a/B0b/B0b2/B0b3/B0c are split into batches of `batch_size`.
# Up to `parallel_subagents` (default 5) batches are dispatched concurrently.
# Each subagent processes its batch sequentially (B1+B2+B3+B4+B5 per CM) and
# returns a JSON array of per-CM results. Retry/timeout protects against stalls.

SUBAGENT_TIMEOUT_MS = 300_000   # 5 minutes
MAX_RETRIES         = 2         # 2 retries = 3 total attempts
parallel_subagents  = 5 if execution_mode == "subagent" else 1   # batches dispatched concurrently per round (A7: 5 if subagent, 1 if inline)

if not aborted:
    batches = [subagent_eligible[i:i+batch_size] for i in range(0, len(subagent_eligible), batch_size)]
    batch_done = 0

    for round_start in range(0, len(batches), parallel_subagents):
        round_batches = batches[round_start : round_start + parallel_subagents]

        if execution_mode == "subagent":
            for i, batch in enumerate(round_batches):   # global 1-based batch number = round_start + i + 1 (batch_done is a completion counter, not a dispatch counter)
                cm_ids = [cm.full_id for cm in batch]
                print(f"[VERIFY-DISPATCH] batch {round_start + i + 1}/{len(batches)} | {len(batch)} CMs: {cm_ids} | subagent launched")
            parallel_results = launch_subagents_parallel(
                [render_batch_subagent_prompt(batch, project_id, security_branch,
                                              task_status_mapping_opt_in,
                                              hybrid_defer=(scan_engine == "hybrid"), ...)
                 for batch in round_batches],
                timeout_ms=SUBAGENT_TIMEOUT_MS,
                max_retries=MAX_RETRIES,
            )
        else:  # execution_mode == "inline"
            # batch_size == 1, round_batches has exactly one single-CM batch
            cm_ids = [cm.full_id for cm in round_batches[0]]
            print(f"[VERIFY-DISPATCH] batch {round_start + 1}/{len(batches)} | {len(round_batches[0])} CMs: {cm_ids} | inline")   # inline: parallel_subagents=1 so round_start is the 0-based batch index
            parallel_results = [run_inline_verification(round_batches[0], ...)]

        for batch, sub_raw in zip(round_batches, parallel_results):
            batch_done += 1

            # Timeout exhaustion: subagent never returned after all retries
            if sub_raw is TIMEOUT:
                for cm in batch:
                    v = make_verdict("partial", "low",
                        findings_for_sde=[{"desc": f"[AI-SAST via Code Scan Verification Validation | {model}] Subagent timed out after retries | verdict=partial confidence=low", "count": "1"}],
                        findings_for_handoff=[{"file": "(n/a)", "line": 0,
                            "description": "subagent did not return within timeout after max retries",
                            "category": "subagent-timeout"}])
                    results.append(record_verified(cm, v, note_post_status="FAILED:subagent-timeout"))
                    done_offset = in_scope.index(cm) + 1
                    print(f"[VERIFY] {done_offset}/{in_scope_total} | {cm.full_id} | verdict=partial | confidence=low | note=FAILED:subagent-timeout")
                continue

            # Parse the JSON array returned by the subagent
            parsed_array = parse_and_validate_batch_output(sub_raw, expected_ids=[cm.full_id for cm in batch])

            if parsed_array.is_error:
                # Entire batch malformed — record all CMs as partial/low
                for cm in batch:
                    v = make_verdict("partial", "low",
                        findings_for_sde=[{"desc": f"[AI-SAST via Code Scan Verification Validation | {model}] Subagent analysis uncertain: malformed return | verdict=partial confidence=low", "count": "1"}],
                        findings_for_handoff=[{"file": "(n/a)", "line": 0,
                            "description": f"subagent returned malformed output: {parsed_array.error}",
                            "category": "analysis-uncertain"}])
                    results.append(record_verified(cm, v, note_post_status="FAILED:subagent-malformed"))
                    done_offset = in_scope.index(cm) + 1
                    print(f"[VERIFY] {done_offset}/{in_scope_total} | {cm.full_id} | verdict=partial | confidence=low | note=FAILED:subagent-malformed")
                continue

            # Process each per-CM result from the batch array
            for cm, parsed in zip(batch, parsed_array.results):
                done_offset = in_scope.index(cm) + 1

                if parsed.is_error:
                    v = make_verdict("partial", "low",
                        findings_for_sde=[{"desc": f"[AI-SAST via Code Scan Verification Validation | {model}] Subagent analysis uncertain: malformed return | verdict=partial confidence=low", "count": "1"}],
                        findings_for_handoff=[{"file": "(n/a)", "line": 0,
                            "description": f"subagent returned malformed output for this CM: {parsed.error}",
                            "category": "analysis-uncertain"}])
                    results.append(record_verified(cm, v, note_post_status="FAILED:subagent-malformed"))
                    print(f"[VERIFY] {done_offset}/{in_scope_total} | {cm.full_id} | verdict=partial | confidence=low | note=FAILED:subagent-malformed")
                    continue

                if parsed.result_kind == "out_of_scope":
                    results.append(record_out_of_scope(cm, reason=parsed.reason))
                    print(f"[SKIP-OOS] {done_offset}/{in_scope_total} | {cm.full_id} | out-of-scope (subagent L-OOS-sub: {parsed.reason})")
                    continue

                if parsed.auth_failure:
                    results.append(record_verified(cm, parsed.verdict, note_post_status="NOT_SENT_AUTH_FAILURE"))
                    aborted = True
                    # Auth is dead -> stop dispatching FUTURE ROUNDS. Sibling batches already
                    # dispatched in THIS round have returned (and may have already POSTed): let the
                    # enclosing loop record their REAL verdicts below -- do NOT mark them skipped.
                    # Mark as unreached only: the rest of THIS batch + every batch in subsequent
                    # rounds. Dedupe by full_id so a CM already recorded (this batch's auth CM, or a
                    # sibling batch that already POSTed) is never overwritten as skipped -- this
                    # preserves the Sum-check identity (no CM double-counted, none silently dropped).
                    recorded_ids = {r["full_cm_id"] for r in results}
                    unreached = list(batch[batch.index(cm)+1:])
                    for future_batch in batches[round_start + parallel_subagents:]:
                        unreached.extend(future_batch)
                    newly_skipped = 0
                    for c in unreached:
                        if c.full_id in recorded_ids:
                            continue
                        results.append(record_skipped(c, reason=f"run aborted: auth failure at {cm.full_id}; not reached"))
                        recorded_ids.add(c.full_id)
                        newly_skipped += 1
                    print(f"[VERIFY] {done_offset}/{in_scope_total} | {cm.full_id} | verdict={parsed.verdict.status} | confidence={parsed.verdict.confidence} | note=NOT_SENT_AUTH_FAILURE")
                    print(f"[STOP] Auth failure at {cm.full_id}; aborted run; recorded {newly_skipped} unreached CMs (rest of this batch + all subsequent rounds) as skipped to preserve the Sum-check identity. Sibling batches already returned in this round keep their real verdicts. Refresh credentials and re-run.")
                    break

                # Normal path
                results.append(record_verified(cm, parsed.verdict, parsed.note_post_status))
                print(f"[VERIFY] {done_offset}/{in_scope_total} | {cm.full_id} | verdict={parsed.verdict.status} | confidence={parsed.verdict.confidence} | note={parsed.note_post_status}")

            # NOTE: on `aborted`, do NOT break here -- the remaining sibling batches in THIS round
            # were already dispatched in parallel and have returned; process them normally so their
            # real verdicts are recorded. Only subsequent ROUNDS are stopped (round-level break below).
        if aborted:
            break
```

Sum-check identity `P + PT + F + S + S_oos == canonical_total` holds across all paths (canonical_total = in_scope_total on a fresh run; = already_done + in_scope_total on resume, since totals are recomputed from the merged verification_results[]):

- Parent B0a (Documented under `selected_cms`) contributes to **S_oos**.
- Parent B0b (upstream-`Skipped` forced-fail) contributes to **F**. B4+B5 POST runs inline; contributes to **NP** on success.
- Parent B0b2 (code CM with empty `files_modified[]`, `handoff_version == "2"` only) contributes to **F**. B4+B5 POST runs inline; contributes to **NP** on success.
- Parent B0b3 (non-code CM with empty `files_modified[]`, `handoff_version == "2"` only) contributes to **S_oos**.
- Parent B0c (`one_by_one` user `skip`/`stop`) contributes to **S** (the current CM and every unreached CM).
- Subagent L-FF2-sub (code CM with empty `files_modified[]`, `result_kind="verified"` + `fail`; `handoff_version == "1"` only) contributes to **F**.
- Subagent L-OOS-sub (non-code CM with empty `files_modified[]`, `result_kind="out_of_scope"`; `handoff_version == "1"` only) contributes to **S_oos** (parent dispatches `record_out_of_scope` from the `parsed.result_kind == "out_of_scope"` branch).
- Subagent auth-abort (B1 401/403 or B5 401/403, `auth_failure: true`, `result_kind="verified"`) contributes to **whichever of {P, PT, F} `parsed.verdict.status` maps to** (the current CM — `partial`/low for B1 auth-failure, the B3-computed verdict for B5 auth-failure) **+** S (every unreached CM = the rest of this batch + all batches in subsequent rounds, recorded by parent via `record_skipped`, deduped by `full_id`; sibling batches already returned in the SAME round keep their real verdicts and are NOT counted here).
- Subagent timeout (all retries exhausted) contributes to **PT** (`partial`/low/subagent-timeout) for every CM in the timed-out batch.
- Malformed subagent return contributes to **PT** (`partial`/low/analysis-uncertain) for every CM in the batch.
- Normal subagent return (`result_kind="verified"`, no auth failure) contributes to whichever of {P, PT, F} the verdict resolves to.

`record_out_of_scope(cm, reason)` returns a result entry with `status="skipped_out_of_scope"`, `note_post_status="NOT_SENT_OUT_OF_SCOPE"`, empty `findings_for_handoff`, and no `payload`. The `reason` argument is persisted on the entry's `reason` field (see Step D schema) so downstream tooling can distinguish out-of-scope sub-cases without consulting console logs. These entries are counted in the `Skipped (out of scope)` bucket of the completion block (distinct from user-initiated skips). Note: this `reason` field is per-entry on `verification_results[]`; it is distinct from the existing `failed_cms_for_rework[].reason` field (which only fires for `fail` entries).

`record_skipped(cm, reason)` returns a result entry with `status="skipped"`, `note_post_status="NOT_SENT"`, `confidence="n/a"`, empty `findings`/`findings_for_handoff`, and no `payload`. The `reason` argument is persisted on the entry's `reason` field (see Step D schema) and is free-text; it distinguishes the user-initiated and run-abort no-POST sub-cases: `"user skipped"` (per-CM `skip` in `one_by_one`), `"user stopped (loop terminated at this CM)"` (the `stop` CM the user landed on), `"user stopped (loop terminated; not reached)"` (CMs after the `stop` point), and `"run aborted: auth failure at {full_cm_id}; not reached"` (CMs after a subagent's 401/403). All four are counted in the `Skipped (user)` bucket of the completion block (distinct from `skipped_out_of_scope`). The result entry is **mandatory** for every user-skip / user-stop / run-aborted CM — agents MUST NOT omit it (this is what keeps the Sum-check identity `P + PT + F + S + S_oos == in_scope_total` valid for all paths). Note: this per-entry `reason` field is distinct from `failed_cms_for_rework[].reason` (which only fires for `fail` entries).

`record_verified(cm, verdict, note_post_status)` returns a result entry with `status` from `verdict.status`, `confidence` from `verdict.confidence`, the verdict's `findings_for_handoff` list, and the supplied `note_post_status` ("POSTED" / "FAILED:{reason}" / "NOT_SENT_FORCED_FAIL" / "NOT_SENT_AUTH_FAILURE" / "FAILED:subagent-malformed" / "FAILED:subagent-timeout" / "DEFERRED_HYBRID" (hybrid transient — rewritten to the combined-note result after Phase B-HYB)).

`forced_fail(cm, reason, category)` returns a verdict with `status="fail"`, `confidence="high"`, one `findings_for_sde` entry (`desc=f"[AI-SAST via Code Scan Verification Validation | {model}] {reason} | verdict=fail confidence=high"`, `count="1"`), and one `findings_for_handoff` entry (`file=cm.files_modified[0]` if any else `"(n/a)"`, `line=0`, `description=reason`, `category=category`). The parent runs B4 (fetch existing notes) + B5 (POST verification note) inline for forced-fail lanes — this is a scoped exception to the pure-orchestrator rule (these CMs never enter the subagent pipeline). Any preserved upstream notes from B4 are included as `upstream-note-preserved` findings. If the POST fails after retries, `note_post_status` is `FAILED:{reason}` (the forced-fail verdict is still recorded locally in the handoff).

### Step B-Subagent. Batched Verification (B1 + B2 + B3 + B4 + B5 × N CMs)

When `execution_mode == "subagent"`: each batch is dispatched to a `generalPurpose` task agent (chosen because it has MCP access — required for both `project_countermeasures op=get` in B1 and `verification op=create` in B5; the readonly `explore` type cannot call MCP). The parent renders the canonical Subagent Prompt Template (Appendix) with placeholders substituted and dispatches one subagent per **batch** of surviving in-scope CMs. When `execution_mode == "inline"`: the parent itself executes the same B1 + B2 + B3 + B4 + B5 sequence in-context for `batch_size=1` (see Step A6 inline fallback and Rule 12). In both modes, the verification iterates over its batch sequentially — in handoff mode performing B1 + B1.5 + B2 + B3 + B4 + B5 per CM; in standalone mode performing B1 + B1.7 + B2 + B3 + B4 + B5 per CM — and returns a **JSON array** of per-CM results.

**Subagent input (rendered into the prompt by the parent):**

- `batch[]` — array of CM descriptors, each containing:
  - `cm.full_id` (full SDE task id, e.g., `"31768-T123"`)
  - `cm.id` (numeric task id)
  - `cm.status` — in handoff mode will be `"Applied"` (the `Skipped` and `Documented` lanes are handled by parent short-circuits); in standalone mode this field carries the SDE task status (`DONE` / `TODO`)
  - `cm.files_modified[]` — absolute paths (handoff mode); empty `[]` (standalone mode — file discovery happens in B1.7)
- `verification_mode` — `"handoff"` or `"standalone"` (controls whether B1.5 short-circuits and B1.7 file discovery apply). **`enter_project` is rendered to the subagent as `"standalone"`** (the parent maps it when substituting this placeholder): for per-CM verification `enter_project` behaves identically to standalone — empty `files_modified[]` → B1.7 file discovery. This mapping is explicit, not implicit.
- `repository_path` — absolute path to the repo root (used by B1.7 in standalone mode for file discovery)
- `repo_name` — basename of `repository_path` (e.g., `my-app`); used in `finding_ref`
- `project_id`
- `security_branch`
- `task_status_mapping_opt_in` — boolean from Step A4 (whether parent allows `task_status_mapping.fail: TODO` in the payload)
- The verbatim **No-False-Positives Invariant** (see callout above)
- The verbatim **B-Sub procedure** (B1 fetch + B1.5 short-circuit + B1.7 file discovery [standalone only] + B2 analyse + B3 verdict + B4 fetch existing notes + B5 POST, including all retry rules and auth-failure handling — see Appendix)
- The verbatim **Step B3 verdict matrix** (handoff mode: 2 to 4 short-circuit lanes already consumed by parent (B0a, B0b; plus B0b2, B0b3 when `handoff_version == "2"`) + 5 subagent-side lanes + 6-row matrix + mixed-file aggregation rule; standalone mode: no parent short-circuits consumed, subagent B1.5 skipped, B1.7 file discovery added)
- The verbatim **hardcoded residual-marker list**: `vuln-code-snippet`, `VULNERABLE`, `INSECURE`, `TODO: fix`, `FIXME: security`, `<!-- VULNERABLE -->`, `# SECURITY ISSUE`, `// TODO: fix`
- The verbatim **strict JSON return schema** (below — now an array)

**Handoff-mode note:** When `handoff_version == "1"`, `cm.category` is **not** passed by the parent (the field is absent from the handoff). The subagent DERIVES `ctx.category` from the CM's `phase` + `title`/`text` in B1's `project_countermeasures op=get` response (SDE exposes NO native per-CM `category` field — use the same classification apply-security-fixes / generate-security-skill-files apply) and uses it in B1.5 to dispatch the subagent-side short-circuit lanes L-FF2-sub and L-OOS-sub. When `handoff_version == "2"`, the parent already has `cm.category` and uses it for B0b2/B0b3 parent-side short-circuits — CMs caught there never reach a subagent. CMs that survive B0b2/B0b3 still have `phase` fetched in B1 and B1.5 re-derives category as a redundant guard.

**Standalone-mode note:** B1.5 is skipped entirely (no upstream `files_modified[]` to gate on). After B1 fetch, the subagent runs **B1.7 File Discovery** to identify which files in the repository are relevant to this CM, then proceeds to B2 with the discovered files.

**Subagent procedure (verbatim in the prompt):**

1. **B1 (fetch):** call MCP `project_countermeasures op=get` with `expand=text,problem,tags,how_tos,phase,name` (`phase` is required so `ctx.category` is available in the response — see B1.5; the `op=list` CM fetch expands `phase` for the same reason). On HTTP 401/403 -> set `result_kind="verified"`, set verdict `partial`/`low` with one `context-fetch-failed` finding (description: `"[AI-SAST via Code Scan Verification Validation | {model}] Could not fetch CM context from SDE: HTTP {401|403} | verdict=partial confidence=low"`), set `note_post_status="NOT_SENT_AUTH_FAILURE"`, set `auth_failure: true`, and return immediately (no B1.5, no B2, no B5). The verdict is REQUIRED by the strict-JSON return schema even when `auth_failure: true`. On 404/5xx/timeout/network -> skip B1.5/B2, set `result_kind="verified"`, set verdict `partial`/`low` with one `context-fetch-failed` finding (description: `"[AI-SAST via Code Scan Verification Validation | {model}] Could not fetch CM context from SDE: HTTP {code} | verdict=partial confidence=low"`), skip B5, set `note_post_status="FAILED:fetch-{code}"`, return.
1.5. **B1.5 (subagent short-circuit — handoff mode only, runs only after B1 succeeds):** determine `ctx.category` (one of `CODE_FIX | ML_CODE | INFRA | ML_DOC`) — use the handoff `cm.category` when present (v2), else DERIVE it from the CM's `phase` + `title`/`text` in the B1 response (SDE exposes NO native per-CM `category` field; use the same classification apply-security-fixes / generate-security-skill-files apply). **Skip this step entirely in standalone mode** (proceed to B1.7).
   - **L-FF2-sub** — if `ctx.category in {CODE_FIX, ML_CODE}` AND `len(cm.files_modified) == 0`: a code CM with no modified files IS the cited evidence for `fail`. Set `result_kind="verified"`, verdict `fail`/`high` with one `residual-vulnerable-pattern` finding (`file="(n/a)"`, `line=0`, `description="[AI-SAST via Code Scan Verification Validation | {model}] code CM (CODE_FIX/ML_CODE) with no modified files | verdict=fail confidence=high"`), `reason="code CM with no modified files"`. Skip B2. **Proceed to B4 (fetch existing notes) + B5 (POST)** to ensure the forced-fail verdict is visible in SDE with any upstream note context preserved. Set `note_post_status` from B5 result (`POSTED` on success, `FAILED:{reason}` on failure). Return.
   - **L-OOS-sub** — if `ctx.category in {INFRA, ML_DOC}` AND `len(cm.files_modified) == 0`: a non-code CM with no modified files has nothing on disk to statically verify (apply-fixes Step 7 deletes `skills/`; the SDE UI already shows the relevant context via the `[AI-Documented]` note from upstream and the CM's own `text`/`how_tos`). Set `result_kind="out_of_scope"`, leave `verdict` absent, `reason="non-code CM with no modified files; static verification not applicable"`, `note_post_status="NOT_SENT_OUT_OF_SCOPE"`, skip B2, skip B5, return.
   - **Otherwise** (non-empty `files_modified[]`): proceed to B2.
1.7. **B1.7 (file discovery — standalone mode only, runs after B1 succeeds):** In standalone mode, `cm.files_modified` is always `[]` because there is no apply-fixes record. The subagent must discover which files in the repository are relevant to this CM.
   - **Step 1:** Extract search terms from `ctx.problem` + `ctx.text` + `ctx.how_tos[]` — vulnerability keywords, API/function names, framework patterns, file extensions/types.
   - **Step 2:** Use `grep`/`glob` (via shell tools) within `{repository_path}` to find candidate files matching the search terms. Exclude common non-source directories (`node_modules/`, `.git/`, `__pycache__/`, `dist/`, `build/`, `vendor/`). **Cap:** MAX 200 candidate matches per search term; MAX 500 total candidates before ranking. If limits are exceeded, narrow search terms with more specific patterns or use directory scoping.
   - **Step 3:** AI-rank the candidates by relevance to the CM's vulnerability description (`ctx.problem`). Prioritize files that contain code patterns related to the vulnerability surface (e.g., SQL queries for SQL injection CMs, authentication handlers for auth CMs).
   - **Step 4:** Select top N files (cap at 10 per CM to stay within context budget). Store as `discovered_files[]`.
   - **Step 5:** If no relevant files are found: set `result_kind="verified"`, verdict `pass`/`high` with one `vulnerability-absent` finding (`file="(repo-wide scan)"`, `line=0`, `description="[AI-SAST via Code Scan Verification Validation | {model}] No files relevant to this CM's vulnerability surface found in repository | verdict=pass confidence=high"`), `note_post_status` from B4+B5 (fetch existing notes, then POST), return after B5.
   - **Otherwise** (`discovered_files[]` is non-empty): proceed to B2 using `discovered_files[]` in place of `cm.files_modified[]`.
2. **B2 (analyse) — for each file in `cm.files_modified[]` (handoff mode) or `discovered_files[]` (standalone mode):** ground all reasoning in `ctx.problem` and `ctx.text` (the canonical statement of the vulnerability and the recommended fix). `ctx.how_tos[]` is **optional and corroborative**: many SDE CMs have empty or partially populated `how_tos[]`, and the verdict logic must work correctly in that case.
   - **Detect language/framework** (extension/shebang/manifest hints).
   - **Filter `ctx.how_tos[]` to applicable language(s)** if non-empty. Record skipped how-tos as `not-applicable-how-to-skipped` audit findings (no verdict impact). If `ctx.how_tos[]` is empty or no entries are language-applicable, Q2 is skipped entirely (see below) — this is a normal, not a degraded, path.
   - **Q1 (per file, negative-canonical) — Vulnerability presence.** Driven by `ctx.problem` and `ctx.text` (NOT by `ctx.how_tos[]`). Determine which of three explicit states applies:
     - `absent_high_confidence` — confident vulnerability described in `ctx.problem` is NOT present in this file (clean code path, sink not reachable, parameterised/validated input, etc.).
     - `present_cited` — found a residual vulnerable pattern matching `ctx.problem`; emit `residual-vulnerable-pattern` finding cited at file:line.
     - `ambiguous` — cannot determine (obfuscated code, indirect data flow, partial coverage). Any uncertainty defaults to `ambiguous`, NOT `absent_high_confidence`.
   - **Q2 (per applicable how-to, positive-corroborative) — Canonical mitigation match. OPTIONAL — runs ONLY when `ctx.how_tos` is non-empty AND has at least one language-applicable entry.** For each applicable how-to: is its canonical mitigation pattern present? If yes -> emit `mitigation-confirmed` finding citing the how-to id. Q2 is corroborative only — it never gates the verdict. When Q2 is skipped (empty/non-applicable how-tos), proceed straight to Q3.
   - **Q3 (per file, semantic-equivalence-corroborative) — Alternative mitigation.** ASKED when (a) `ctx.how_tos` is empty or has no applicable entries (Q2 skipped), OR (b) every applicable Q2 returned no. Is some other recognisable mitigation present that prevents `ctx.problem` by the same security property? If yes -> emit `alternative-mitigation-accepted` finding with rationale ("file uses SQLAlchemy ORM `session.query(...).filter_by(...)` which prevents string-concat SQL by the same property as parameter binding described in `ctx.text`"). Q3 is corroborative only.
   - **Marker scan (per file):** scan for the hardcoded marker list. A hit -> emit `residual-marker` finding cited at file:line.
3. **B3 (verdict):** apply the verdict matrix below. The No-False-Positives Invariant is canonical: Q1 is the gate; Q2 and Q3 are corroborative; an empty/inapplicable `ctx.how_tos[]` does NOT degrade confidence — `Q1=absent_high_confidence` + clean markers = `pass`/`high` even when Q2 was skipped.
3.5. **B4 (fetch existing notes — read-then-append):** before building the POST payload, fetch any existing **verification** notes on this CM to preserve prior verification detail. Call `verification` with `op: "list"`, `project_id: {project_id}`, `task_id: {cm.full_id}` to retrieve existing verification/analysis notes. (Note: this is the **verification-note** channel only; apply-fixes' `[AI-Applied]/[AI-Documented]` audit comments live in the separate **countermeasure-note** channel via `project_countermeasures op=addNote` and are intentionally NOT merged here — the three note channels are kept distinct.) If the CM has prior verification notes from earlier runs, extract their description text and store as `existing_notes[]`. On HTTP 404/5xx/timeout/network error: B4 is **non-fatal** — set `existing_notes = []`, emit one `upstream-note-fetch-failed` finding (`file="(n/a)"`, `line=0`, `description="Could not fetch existing notes: {error}"`, `category="upstream-note-fetch-failed"`), and proceed to B5. On HTTP 401/403: treat as auth failure (same as B1 auth path — set `auth_failure: true` and return). When `existing_notes[]` is non-empty, B5 includes an `upstream-note-preserved` finding in the payload (see B5).
4. **B5 (post):** build the payload (`behaviour=combine`, `confidence`, `status`, aggregated `findings`, `finding_ref`, `pinned=false`, `task_status_mapping`). If `existing_notes[]` from B4 is non-empty, append one `upstream-note-preserved` finding per preserved note (`desc="[AI-SAST via Code Scan Verification Validation | {model}] Prior note preserved: {upstream_note_summary, <=200ch} | (audit-only, no verdict impact)"`, `count="1"`). Call `verification` with `op: "create"`, `project_id`, `task_id: {full_id}`, and the payload fields (`behaviour`, `confidence`, `status`, `findings`, `finding_ref`, `pinned`, `task_status_mapping`). Retry/back-off: HTTP 429 sleep 1s + retry once; 5xx retry once after 1s; network retry once after 1s; 401/403 STOP and return `auth_failure: true`; 4xx (other) record `note_post_status="FAILED:{server body}"` and return verdict.

**Loop scopes (read carefully):** Q1 runs **once per file** (not per how-to); Q2 runs **once per (file × applicable how-to)**; Q3 runs **once per file** (only when all Q2 results were no); marker scan runs **once per file**.

**Subagent output (strict JSON array; parent parses and validates):**

The subagent returns a JSON **array** with one element per CM in the batch, in the same order as the input `batch[]` array. Each element has the same schema as the pre-batch single-CM result:

```json
[
  {
    "full_id": "{project_id}-T{n}",
    "result_kind": "verified | out_of_scope",
    "verdict": {
      "status": "pass | partial | fail",
      "confidence": "high | low",
      "findings_for_sde": [{"desc": "...", "count": "N"}],
      "findings_for_handoff": [
        {
          "file": "...",
          "line": 0,
          "description": "...",
          "category": "residual-marker | residual-vulnerable-pattern | mitigation-confirmed | alternative-mitigation-accepted | vulnerability-absent-mitigation-unrecognized | vulnerability-absent | not-applicable-how-to-skipped | analysis-uncertain | context-fetch-failed | scope-mismatch | upstream-note-preserved | upstream-note-fetch-failed"
        }
      ]
    },
    "note_post_status": "POSTED | FAILED:{reason} | NOT_SENT_FORCED_FAIL | NOT_SENT_OUT_OF_SCOPE | NOT_SENT_AUTH_FAILURE | DEFERRED_HYBRID",
    "auth_failure": false,
    "reason": "free-text; required when result_kind=='out_of_scope' or for L-FF2-sub forced-fail; empty string otherwise",
    "rationale_summary": "<=300 chars; what the subagent observed and why it picked this verdict (or, for result_kind=='out_of_scope', why the CM was OOS)"
  }
]
```

The array MUST contain exactly `len(batch)` elements. The `full_id` in each element MUST match the corresponding `batch[i].full_id`. If the subagent encounters an `auth_failure` mid-batch, it MUST still return results for all CMs processed so far (including the auth-failure CM) and fill the remaining slots with `result_kind="verified"`, `verdict={status:"partial", confidence:"low", ...}`, `auth_failure: true`, `note_post_status="NOT_SENT_AUTH_FAILURE"`.

**Per-element field semantics** (identical to the pre-batch schema):

- **`result_kind`** is a discriminator. `"verified"` means the subagent produced a verdict (B3 matrix, L-FF2-sub forced fail, or B1 fetch failure). `"out_of_scope"` means the L-OOS-sub lane fired and the parent must record `skipped_out_of_scope`.
- **`verdict`** is REQUIRED when `result_kind=="verified"` and MUST be omitted when `result_kind=="out_of_scope"`.
- **`note_post_status`** is REQUIRED in both branches. Valid values when `result_kind=="out_of_scope"` are `NOT_SENT_OUT_OF_SCOPE` only; when `result_kind=="verified"` any of the other values may apply.
- **`auth_failure`** is REQUIRED in both branches; only ever `true` for the B1/B5 401/403 paths (and those are always `result_kind=="verified"`).
- **`reason`** is free-text and is preserved on the `verification_results[]` entry's `reason` field. REQUIRED for `result_kind=="out_of_scope"` and for the L-FF2-sub forced-fail branch; may be empty string otherwise.

The category `missing-fix` is **NOT** in the enum (deprecated in beta-3.2.0 — was a false-positive vector under the old "no canonical pattern found = problem" rule).

**Subagent failure handling (parent-side):**

- **Timeout (all retries exhausted)** -> parent records every CM in the batch as `verdict=partial` / `confidence=low` / one finding with category `subagent-timeout` and description `"subagent did not return within timeout after max retries"`; `note_post_status="FAILED:subagent-timeout"`. Never `fail` — a timeout is not vulnerability evidence.
- **Malformed JSON / parse error / schema validation failure (entire batch)** -> parent records every CM in the batch as `verdict=partial` / `confidence=low` / one finding with category `analysis-uncertain` and description `"subagent returned malformed output: {error}"`; `note_post_status="FAILED:subagent-malformed"`. Never `fail`.
- **Malformed individual element** -> parent records that specific CM as `partial`/`low`/`analysis-uncertain`; other CMs in the batch use their own parsed results.
- **`auth_failure: true`** (any element in any subagent's batch) -> parent stops dispatching further ROUNDS, records the auth-failure CM with `note_post_status="NOT_SENT_AUTH_FAILURE"`, records every unreached CM (the rest of this batch + all batches in subsequent rounds) via `record_skipped(c, reason="run aborted: auth failure at ...; not reached")` (deduped by `full_id`; sibling batches already returned in the SAME round keep their real verdicts), surfaces the remediation message (`Refresh credentials and re-run`), and exits. This preserves Sum-check identity.

### Step B3. Verdict Matrix (CANONICAL)

The verdict matrix is governed by the No-False-Positives Invariant (full callout, byte-identical with the Phase B preamble and AGENTS.md Rule 5):

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

Two to four short-circuit lanes run in the **parent loop** before per-CM verification begins (handoff mode only). The first two (B0a L-OOS, B0b L-FF1) always fire in handoff mode. The next two (B0b2 L-FF2-parent, B0b3 L-OOS-parent) fire **only when `handoff_version == "2"`** (which includes `cm.category`); when `handoff_version == "1"`, these conditions are instead caught inside the per-CM verification context (subagent or inline) via L-FF2-sub/L-OOS-sub. Five more lanes run inside the per-CM verification context (B1.5 + B1 fetch failures): two B1.5 lanes that branch on `ctx.category` for empty `files_modified[]` (redundant with B0b2/B0b3 when handoff v2 but still enforced for v1), and three B1-fetch lanes (one for non-auth fetch errors, two for the auth-failure split B1 vs B5). The 6-row matrix is the AI's analysis-driven verdict for surviving cases (non-empty `files_modified[]`).

**Parent short-circuit lanes (no per-CM verification dispatched):**

| Lane | Trigger | Result | Confidence | Finding | `note_post_status` |
|------|---------|--------|------------|---------|--------------------|
| L-OOS (B0a) | `cm.status == "Documented"` AND `scope == selected_cms` | `skipped_out_of_scope` | n/a | n/a (recorded with `reason`) | `NOT_SENT_OUT_OF_SCOPE` |
| L-FF1 (B0b) | `cm.status == "Skipped"` | `fail` | high | `residual-vulnerable-pattern` ("CM was skipped by apply-fixes; no mitigation present") | `POSTED` (B4+B5 inline; `FAILED:{reason}` if POST fails) |
| L-FF2-parent (B0b2) | `handoff_has_category` AND `cm.category in {CODE_FIX, ML_CODE}` AND `len(cm.files_modified) == 0` | `fail` | high | `residual-vulnerable-pattern` ("code CM with no modified files") | `POSTED` (B4+B5 inline; `FAILED:{reason}` if POST fails) |
| L-OOS-parent (B0b3) | `handoff_has_category` AND `cm.category in {INFRA, ML_DOC}` AND `len(cm.files_modified) == 0` | `skipped_out_of_scope` | n/a | n/a (recorded with `reason`) | `NOT_SENT_OUT_OF_SCOPE` |

**Per-CM verification lanes (run inside the subagent or inline context in B1.5 + B1 fetch error handling, before the matrix):**

| Lane | Trigger | `result_kind` | Verdict | Confidence | Finding | `note_post_status` |
|------|---------|---------------|---------|------------|---------|--------------------|
| L-FF2-sub | B1.5: `ctx.category in {CODE_FIX, ML_CODE}` AND `len(cm.files_modified) == 0` | `verified` | `fail` | high | `residual-vulnerable-pattern` ("code CM (CODE_FIX/ML_CODE) with no modified files") | `POSTED` (B4+B5 runs; `FAILED:{reason}` if POST fails) |
| L-OOS-sub | B1.5: `ctx.category in {INFRA, ML_DOC}` AND `len(cm.files_modified) == 0` | `out_of_scope` | (omitted) | n/a | n/a (recorded with `reason="non-code CM with no modified files; static verification not applicable"`) | `NOT_SENT_OUT_OF_SCOPE` (no B2, no POST) |
| L-FETCH | B1 fetch returns 404 / 5xx / timeout / network error | `verified` | `partial` | low | `context-fetch-failed` | `FAILED:fetch-{code}` (no POST attempted) |
| L-AUTH-B1 | B1 fetch returns 401 / 403 | `verified` | `partial` | low | `context-fetch-failed` ("Could not fetch CM context from SDE: 401/403") | `NOT_SENT_AUTH_FAILURE`; subagent ALSO sets `auth_failure: true`; parent HARD STOPs |
| L-AUTH-B5 | B5 POST returns 401 / 403 (verdict already determined in B3) | `verified` | `pass` / `partial` / `fail` (from B3) | high / low (from B3) | findings already aggregated in B3 | `NOT_SENT_AUTH_FAILURE`; subagent ALSO sets `auth_failure: true`; parent HARD STOPs |

**Main verdict matrix (per-file aggregated; each row is "all files in `cm.files_modified[]` (handoff) or `discovered_files[]` (standalone) agree on this row"):**

| Q1 (per file) | Q2 (per applicable how-to; *skipped when ctx.how_tos empty or no applicable entries*) | Q3 (per file; runs when Q2 was skipped or all Q2=no) | Marker scan (per file) | Verdict | Confidence | Primary finding |
|---|---|---|---|---|---|---|
| `absent_high_confidence` | any Yes (Q2 ran) | -- | clean | `pass` | high | `mitigation-confirmed` (cites how-to id) |
| `absent_high_confidence` | all No (Q2 ran) OR Q2 skipped | Yes (AI rationale) | clean | `pass` | high | `alternative-mitigation-accepted` (cites observed code + security property; cites how-to id only if a how-to existed) |
| `absent_high_confidence` | all No (Q2 ran) OR Q2 skipped | No | clean | `pass` | high | `vulnerability-absent-mitigation-unrecognized` (AI confirms vuln from `ctx.problem` is absent even though it cannot identify the specific mitigation strategy; this is the canonical "negative-signal-canonical" outcome and applies whether or not how-tos existed) |
| `ambiguous` | -- | -- | clean | `partial` | low | `analysis-uncertain` (cites the ambiguity reason) |
| `present_cited` | -- | -- | -- | `fail` | high | `residual-vulnerable-pattern` (cites file:line) |
| -- | -- | -- | hit | `fail` | high | `residual-marker` (cites file:line) |

**Note on empty `ctx.how_tos[]`:** when `ctx.how_tos[]` is empty or has no language-applicable entries, Q2 is skipped entirely. The matrix collapses to Q1 + Q3 + marker scan, which is fully sufficient: `Q1=absent_high_confidence` + clean markers always yields `pass`/`high` regardless of whether Q2 ran. This is by design — the No-False-Positives Invariant treats Q2 as corroborative-only.

**Mixed-file aggregation rule.** If files in the analysis set (`cm.files_modified[]` in handoff mode, `discovered_files[]` in standalone mode) produce different rows, the verdict for the CM is the worst row hit, in this order:
1. any `present_cited` OR any marker hit -> `fail`/high (cite all hits)
2. any `ambiguous` -> `partial`/low
3. all `absent_high_confidence` -> `pass`/high

Findings from ALL files are concatenated (no de-duplication of file-level evidence).

**Hard rules (from the No-False-Positives Invariant):**

- Every `fail` MUST emit at least one finding CITED with `file` + `line` (or, for parent forced-fail lanes L-FF1 / B0b2 and the subagent forced-fail lane L-FF2-sub, with a structured upstream reason and `line=0`).
- **Handoff mode:** the four — and ONLY four — sources of `fail` evidence are: (1) cited `residual-vulnerable-pattern`, (2) cited `residual-marker`, (3) upstream `Skipped` audit status (parent L-FF1), (4) empty `files_modified[]` for CODE_FIX/ML_CODE (parent B0b2 when v2, subagent L-FF2-sub when v1). **Standalone mode:** only sources (1) and (2) apply (there is no upstream `Skipped` status and `files_modified` is always empty by design).
- "Failure to recognise a mitigation" is NEVER a `fail` source.
- "Failure to recognise a mitigation" is NEVER a `partial` source either — `partial` is reserved for AI-side ambiguity (Q1=`ambiguous`), context-fetch failures (L-FETCH), and malformed-subagent-output handling.

#### Aggregating findings for the SDE payload

The subagent collects per-location observations as it analyses each modified file. Before POSTing, observations are **grouped by category** and **one `{desc, count}` entry per non-empty category** is emitted to the SDE payload:

| Category | `desc` template (MANDATORY `[AI-SAST ...]` prefix + detail) | Verdict impact |
|----------|--------------------------|----------------|
| `residual-marker` | `[AI-SAST via Code Scan Verification Validation \| {model}] Residual vulnerability marker(s) in {file_basenames} \| verdict={verdict} confidence={confidence}` | `fail` (canonical) |
| `residual-vulnerable-pattern` | `[AI-SAST via Code Scan Verification Validation \| {model}] Residual vulnerable pattern in {file_basenames}: {ctx.problem summary, ≤120ch} \| verdict={verdict} confidence={confidence}` | `fail` (canonical) |
| `mitigation-confirmed` | `[AI-SAST via Code Scan Verification Validation \| {model}] Mitigation confirmed in {file_basenames}: how-to {how_to_id} pattern present \| verdict={verdict} confidence={confidence}` | corroborative (informs `pass` rationale) |
| `alternative-mitigation-accepted` | `[AI-SAST via Code Scan Verification Validation \| {model}] Alternative mitigation in {file_basenames}: {AI rationale, ≤200ch} \| verdict={verdict} confidence={confidence}` | corroborative (informs `pass` rationale) |
| `vulnerability-absent-mitigation-unrecognized` | `[AI-SAST via Code Scan Verification Validation \| {model}] Vulnerability absent in {file_basenames}: pattern from ctx.problem confidently absent; accepted under no-false-positives invariant \| verdict={verdict} confidence={confidence}` | corroborative (informs `pass` rationale) |
| `not-applicable-how-to-skipped` | `[AI-SAST via Code Scan Verification Validation \| {model}] How-to {how_to_id} ({lang}) skipped: not applicable to {detected_lang} in {file_basenames}` | none (audit) |
| `analysis-uncertain` | `[AI-SAST via Code Scan Verification Validation \| {model}] Analysis uncertain in {file_basenames}: {ambiguity reason} \| verdict={verdict} confidence={confidence}` | `partial` |
| `context-fetch-failed` | `[AI-SAST via Code Scan Verification Validation \| {model}] Context fetch failed: could not retrieve CM data from SDE \| verdict={verdict} confidence={confidence}` | `partial` |
| `scope-mismatch` | `[AI-SAST via Code Scan Verification Validation \| {model}] Scope mismatch in {file_basenames}: CM scope extends beyond repository files \| verdict={verdict} confidence={confidence}` | `partial` |
| `subagent-timeout` | `[AI-SAST via Code Scan Verification Validation \| {model}] Subagent timed out after max retries \| verdict={verdict} confidence={confidence}` | `partial` |
| `upstream-note-preserved` | `[AI-SAST via Code Scan Verification Validation \| {model}] Prior note preserved: {upstream_note_summary, ≤200ch} \| (audit-only, no verdict impact)` | none (audit) |
| `upstream-note-fetch-failed` | `[AI-SAST via Code Scan Verification Validation \| {model}] Could not fetch existing notes: {error} \| (audit-only, no verdict impact)` | none (audit) |

**Template placeholders:** `{model}` = LLM model identifier at runtime (e.g., `claude-4-sonnet`, `gpt-4o`). `{file_basenames}` = comma-separated basenames from the analysis file set (`cm.files_modified[]` in handoff mode, `discovered_files[]` in standalone mode). The `[AI-SAST via Code Scan Verification Validation | {model}]` prefix is **MANDATORY** on every `findings[].desc` value in the SDE payload — it identifies the tool and model to reviewers in the SDE UI.

`count` is the number of per-location observations in that bucket, **stringified** (e.g., `"3"`) to match the SDE spec's example.

Per-location detail (`{file, line, description, category}`) goes into `.sde-verification-handoff.json` `verification_results[].findings[]` unchanged — that file is the source-of-truth artefact pointed at by `finding_ref` (see below).

The deprecated category `missing-fix` (pre-3.2.0) MUST NOT appear in any new payload or handoff.

#### Verification Note Payload

Build the payload (subagent does this in B5; parent only sees the post status afterwards):

```json
{
  "behaviour": "combine",
  "confidence": "high",
  "status": "pass",
  "findings": [
    { "desc": "[AI-SAST via Code Scan Verification Validation | {model}] Mitigation confirmed in {file_basenames}: how-to ht-12 pattern present | verdict=pass confidence=high", "count": "1" }
  ],
  "finding_ref": "Agent: code-scan-verification-validation | Model: {model} | Repo: {repo_name} | CM: {full_cm_id} | Run: 2026-04-21T14:03:11Z | Handoff: .sde-verification-handoff.json",
  "pinned": false,
  "task_status_mapping": {
    "pass": "DONE"
  }
}
```

For a `fail` verdict, the same payload but with aggregated negative findings:

```json
{
  "behaviour": "combine",
  "confidence": "high",
  "status": "fail",
  "findings": [
    { "desc": "[AI-SAST via Code Scan Verification Validation | {model}] Residual vulnerability marker(s) in {file_basenames} | verdict=fail confidence=high", "count": "3" },
    { "desc": "[AI-SAST via Code Scan Verification Validation | {model}] Residual vulnerable pattern in {file_basenames}: {ctx.problem summary} | verdict=fail confidence=high", "count": "1" }
  ],
  "finding_ref": "Agent: code-scan-verification-validation | Model: {model} | Repo: {repo_name} | CM: {full_cm_id} | Run: 2026-04-21T14:03:11Z | Handoff: .sde-verification-handoff.json",
  "pinned": false,
  "task_status_mapping": {
    "pass": "DONE",
    "fail": "TODO"
  }
}
```

`task_status_mapping` rules (subagent enforces; passed via `task_status_mapping_opt_in` in the prompt):

- `"pass": "DONE"` is **always** included.
- `"fail": "TODO"` is included **only if** the user chose `yes_rollback` in Step A4 AND the current verdict is `fail`.
- `partial` never maps to a workflow status.

`behaviour: "combine"` is the SDE spec's "combine with all previous results" mode. It preserves prior verification notes (the audit trail) while adding the new one. NOTE: with `combine`, SDE's derived `verification_status` is computed across the COMBINED set of notes and is **fail-dominant** — a single prior `fail` keeps the derived status `fail` even after a newer `combine` note says `pass` (a later pass does NOT clear an earlier fail). It is therefore NOT simply "the most-recent note wins"; a `behaviour=replace` note (e.g. ZeroPath's per-scan push) is what resets the baseline so the latest scan wins. Re-runs preserve history; reason about re-run/resume status with this in mind.

`finding_ref` is the SDE UI's "Report Reference" field — it's expected to point at a retrievable artefact where a viewer can find more detail. The subagent writes the `finding_ref` using the format `Agent: code-scan-verification-validation | Model: {model} | Repo: {repo_name} | CM: {full_cm_id} | Run: {iso8601_utc} | Handoff: .sde-verification-handoff.json` — the primary fields (Agent, Model, Repo) are immediately visible in the SDE UI's Report Reference column. The CM and Run fields let a human locate the full reasoning in `.sde-verification-handoff.json` and distinguish per-CM, per-run notes. `{repo_name}` is the basename of `repository_path` (e.g., `my-app` from `/home/user/my-app`), captured in Phase A and forwarded to subagents.

#### Verification mode: manual (by design)

Notes from this skill are posted **without** an `analysis_session` ID, so SDE classifies them as **Manual Verification** (`automatic: false` on the resulting note resource). This is intentional — the AI agent is not a registered SDE Verification Connection plugin, and the SD Elements User Guide's [Manual verification](https://docs.sdelements.com/master/guide/docs/integrations/security_tools/overview/verification_status.html) path applies. Implications:

- The SDE UI groups these notes under "Manual Verification" rather than under a scanner name (Veracode, Fortify, etc.).
- Per the API spec, a `fail` note in **automatic** mode requires at least one finding; in **manual** mode it does not. This skill always emits at least one finding for `fail` regardless, so the SDE UI consistently shows the cited evidence.
- DO NOT mint a synthetic `analysis_session` ID to "promote" notes to automatic mode — without a registered Verification Connection plugin on the SDE side, the server will reject the payload and the audit trail will be lost.

If/when the AI agent is registered as a real SDE Verification Connection (out of scope for this skill), this section becomes obsolete and the payload will need an `analysis_session` field; the rest of the schema stays the same.

#### Verification tool call (subagent's B5)

```json
{
  "tool": "verification",
  "op": "create",
  "project_id": "{project_id}",
  "task_id": "{cm.full_id}",
  "behaviour": "combine",
  "confidence": "{confidence}",
  "status": "{verdict}",
  "findings": [/* aggregated findings */],
  "finding_ref": "{finding_ref}",
  "task_status_mapping": {/* see Step B3 */}
}
```

**Note on `{cm.full_id}`:** The `verification` tool auto-normalizes `task_id` via `normalizeProjectTaskId()` — it accepts `"T123"`, `"123-T123"`, `42`, etc. The handoff stores the full form (`full_id`, e.g. `"31768-T123"`); using it verbatim is recommended for clarity but no longer causes a 404 if a bare slug is passed.

**Hybrid B5 deferral (R-ZP3):** when `scan_engine == "hybrid"`, the AI loop above runs B1–B4 and B3 (verdict) but DOES NOT execute B5. Each per-CM result is returned/recorded with `note_post_status = "DEFERRED_HYBRID"` and the AI verdict (`ai_status`, `ai_confidence`, `findings`). The single combined POST happens in Phase B-HYB after the ZeroPath push lands. (Forced-fail parent lanes B0b/B0b2 also defer their POST in hybrid — they contribute an `ai_status="fail"` to the merge instead of posting inline.)

---

## Phase B-ZP. ZeroPath-Only Engine (runs when `scan_engine == "zeropath"`)

> Replaces the AI Per-CM Loop. The skill triggers a ZeroPath scan; ZeroPath's backend writes the verification results to SDE. **The skill posts NO `verification op=create` notes (R-ZP2).** `scope` (A1.5+A3) is used only to scope the report; ZeroPath always scans the whole repo.

```python
# Setup: variables used below.
# NOTE (R-ZP11 supersedes R-ZP7): branch correctness is now verified at A-ZP1.6
#   (scan_branch committed+pushed; scan_branch_remote_sha captured) and asserted
#   after the scan via scanTargetBranchCommitSha == scan_branch_remote_sha. No
#   separate local_head/commitSha drift check is needed — scan_branch_remote_sha
#   is the single source of truth.
# mapped_in_scope_cms = the CMs in this mapping (getMappingAudit/supportedTaskIds)
#   intersected with the user's A1.5+A3 scope (all -> every mapped CM; selected_cms
#   -> only listed IDs that are mapped). ZeroPath always scans the whole repo;
#   this set only bounds what the skill REPORTS / mirrors into the handoff.
mapped_in_scope_cms = [cm for cm in a_zp1_audit.tasks if in_scope_filter(cm.full_id, scope, scope_args)]  # a_zp1_audit = getMappingAudit from Step A-ZP1

# R-ZP6: side-effect warning BEFORE any scan
print(f"[WARN] A ZeroPath scan will auto-update mapped CM statuses in SDE project {sdeProjectId}.")

# 1. Start the scan on the VERIFIED, PUSHED branch from A-ZP1 step 6 (R-ZP11)
scan = scans_start(repositories=[{"id": repositoryId, "branch": scan_branch}])   # scan_branch is committed+pushed (A-ZP1.6)
scanId = scan.scans[0].scanId
meta = scans_get(scanId)
commitSha = meta.scanTargetBranchCommitSha
print(f"[CHECKPOINT] ZeroPath scan started: {scanId} | branch {meta.scanTargetBranch} | commit {commitSha}")
# R-ZP11 assertion: ZeroPath must have scanned the branch tip we verified as pushed.
if meta.scanTargetBranch != scan_branch or commitSha != scan_branch_remote_sha:
    print(f"[WARN] ZeroPath scanned branch={meta.scanTargetBranch} @ {commitSha}, expected {scan_branch} @ {scan_branch_remote_sha}. "
          f"Likely the branch was not pushed (or push lagged) — re-push {scan_branch} and re-run.")

# 2. Wait until Finished — poll the scan status every 1 minute (NOT user-configurable).
#    scan_timeout_ms is the internal 30-min default safety cap (A-ZP2; no longer asked).
deadline = now() + scan_timeout_ms
while scans_get(scanId).status not in ("Finished", "Errored"):
    if now() > deadline:
        scans_cancel(scanId)
        HARD_STOP(f"ZeroPath scan {scanId} exceeded the 30-min default cap; cancelled.")
    sleep(60_000)   # poll every 1 minute
if scans_get(scanId).status == "Errored":
    HARD_STOP(f"ZeroPath scan {scanId} Errored.")
print(f"[CHECKPOINT] ZeroPath scan {scanId} status=Finished")

# 3. R-ZP5: wait for the async push to land. CRITICAL — scope the match to THIS SDE project
#    (+ mapping), NOT just scanId. One scanId fans out to EVERY SDE project mapped to the repo,
#    so a SIBLING project's push reaching "success" satisfies a scanId-only predicate and makes
#    us read stale/empty ZP notes for the WRONG project. Also PAGINATE getSyncHistory (do NOT cap
#    at limit=10): with N mapped projects each emitting started+success (+rule_sync) events, this
#    project's success row can be far past the first page.
def push_success_event():
    for ev in iterate_sync_history(page_size=50):   # newest-first, paginate until found or history exhausted
        if (ev.apiEndpointName == "security_compass.push" and ev.status == "success"
                and ev.scanId == scanId and ev.sdeProjectId == sdeProjectId and ev.mappingId == mappingId):
            return ev
    return None
while not push_success_event():
    if now() > deadline:
        print("[WARN] push-success event not seen before timeout; reporting last-known stats.")
        break
    sleep(5_000)
push = push_success_event()   # scoped to THIS project+mapping (issuesMapped, unmapped, countermeasuresMarkedDone)
print(f"[CHECKPOINT] ZeroPath push success for scan {scanId} (markedDone {push.countermeasuresMarkedDone}, issuesMapped {push.issuesMapped}, unmapped {push.unmapped})")

# 4. Report (no POST). Read per-CM outcome from SDE for the handoff mirror.
audit  = getMappingAudit(mappingId)                 # per-CM coverage
issues = issues_list(repositoryId=repositoryId)     # repo-wide; scope by repositoryId (NOT scanId)
stats  = stats_summary(repositoryId=repositoryId)
# optional artifact: write issues_export(scanId=scanId) to {repository_path}/.sde-zp-findings.json

# 5. R-ZP9: pass-by-absence WARN gate (read each mapped CM's SDE note)
pass_by_absence = 0
verification_results = []
for cm in mapped_in_scope_cms:                      # CMs in the mapping/audit (scope-filtered for the report)
    # Read ZeroPath's OWN note only: ZeroPath-native notes have an EMPTY finding_ref;
    # the skill's notes start with "Agent: ...". Never read the skill's own note as the ZP signal.
    notes = verification(op="list", project_id=sdeProjectId, task_id=cm.full_id).results
    zp_note = next((n for n in notes if n.finding_ref == ""), None)   # latest ZeroPath-native note
    zp_status = zp_note.status if zp_note else "none"
    mapped_issue_count = int(zp_note.findings[0].count) if (zp_note and zp_note.findings) else 0
    if zp_status == "pass" and mapped_issue_count == 0:
        pass_by_absence += 1
        print(f'[WARN] Weak pass — {cm.full_id} "{cm.title}": ZeroPath scanned and found no violation, '
              f'but "no violation found" is NOT proof the control is in place. ZeroPath auto-marked this Done. '
              f'Treat as unverified until AI/human confirms the control exists.')
    # A mapped CM with NO ZeroPath-native note (unsupported/unmapped coverage) has zp_status "none",
    # which is NOT in VALID_STATUS -> assemble_handoff would assert-fail once this rec is offloaded.
    # Map it to a valid handoff status (skipped_out_of_scope: ZeroPath produced no signal) while
    # keeping zp_status verbatim for the ZeroPath-Only display block.
    handoff_status = zp_status if zp_status in ("pass", "partial", "fail") else "skipped_out_of_scope"
    rec = {
        "full_cm_id": cm.full_id, "status": handoff_status, "confidence": "n/a",
        "findings": [],   # always-present shape (REQUIRED_KEYS subset); ZeroPath issues live in ZeroPath, the SDE ZP-native note holds the count
        "zp_status": zp_status, "note_post_status": "NOT_SENT_ZP_NATIVE",
        "reason": ("ZeroPath native push wrote this verification; skill posted nothing"
                   if zp_status in ("pass", "partial", "fail")
                   else "mapped CM but no ZeroPath-native note (unsupported/unmapped); no ZP signal"),
    }
    verification_results.append(rec)
    offload_cm_result(cm.full_id, rec)   # MANDATORY: write the per-CM ZP-native mirror artifact to cm-work/ so the T9 Layer-1/2/3 disk audit (below) has artifacts to count; without this, zeropath's disk-based terminal gate is structurally unpassable
# Step D writes the handoff with scan_engine="zeropath", the zeropath{} block, and verification_results assembled from the cm-work/ artifacts (same assemble_handoff path as ai/hybrid).
```

**[CHECKPOINT]** `Verification handoff written: .sde-verification-handoff.json ({N} records)` (same as AI path; `scan_engine="zeropath"`).

### Phase B-ZP Completion Verification Block (REQUIRED for `zeropath`)

```
=== COMPLETION VERIFICATION (ZeroPath-Only) ===
Skill: code-scan-verification-validation
Scan engine: zeropath
MCP connections: ✓ (sdelements + zeropath + securitycompass; tenant match)
ZeroPath scan: {scanId} status=Finished
ZeroPath push: security_compass.push status=success
Countermeasures: fetched {countermeasuresFetched} | sast {X} | nl_rule {Y} | unsupported {Z}
Pushed: countermeasuresMarkedDone {D} | issuesMapped {M} | unmapped {U}
Weak passes (ZeroPath found nothing, so the pass is unproven): {pass_by_absence} of {totalCount}
  -> marked Done but NOT positively verified: {weak_pass_cm_id_list}
  -> To positively verify these, re-run with the AI or Hybrid engine.
Skill-posted verification notes: 0 (ZeroPath native push owns SDE status)
Own handoff written: ✓ (.sde-verification-handoff.json, scan_engine=zeropath)
Gate: scan Finished AND push success? {YES/NO}
================================================
```

**Also apply the T9 terminal verification (engine-adjusted):** Layer 1 (re-derive the mapped-CM coverage from the per-CM ZP-native mirror artifacts in `.sde-security/verify/{project_id}/cm-work/`), Layer 2 (`verify_disk_vs_sde(in_scope_total, mapped_in_scope_ids)` where `in_scope_total` = mapped CM count and `mapped_in_scope_ids` = the mapped/in-scope CM full_ids — counts ONLY those, never a whole-dir glob, exits 0), Layer 3 (tri-source: getMappingAudit mapped set == disk artifacts == handoff rows == in_scope_total; ZeroPath push `countermeasuresMarkedDone` reconciles). All YES required.

**If Gate = NO** (scan not Finished, push not confirmed, or any T9 layer fails)**:** output `INCOMPLETE`; do not declare complete. **If Gate = YES:** `✅ COMPLETION GATE PASSED (ZeroPath-Only)` + recommend Hybrid for any pass-by-absence CMs.

---

## Phase B-HYB. Hybrid Engine (runs when `scan_engine == "hybrid"`)

> Runs ONE repo-wide ZeroPath scan (non-blocking) AND the full AI Per-CM Loop (B5 deferred), then posts ONE combined note per in-scope CM. `status` comes from the user-chosen `authoritative_source`; the other source is used when one has no signal. The AI loop uses subagent batching (same-model) or inline per the SUBAGENT/DELEGATION POLICY.

```python
# 1. R-ZP6 warning + start scan NON-BLOCKING on the VERIFIED, PUSHED branch (R-ZP11)
print(f"[WARN] A ZeroPath scan will auto-update mapped CM statuses in SDE project {sdeProjectId}.")
scan = scans_start(repositories=[{"id": repositoryId, "branch": scan_branch}])    # scan_branch verified pushed in A-ZP1.6
scanId = scan.scans[0].scanId
meta = scans_get(scanId)
commitSha = meta.scanTargetBranchCommitSha
print(f"[CHECKPOINT] ZeroPath scan started: {scanId} | branch {meta.scanTargetBranch} | commit {commitSha}")
if meta.scanTargetBranch != scan_branch or commitSha != scan_branch_remote_sha:
    print(f"[WARN] ZeroPath scanned branch={meta.scanTargetBranch} @ {commitSha}, expected {scan_branch} @ {scan_branch_remote_sha}. Re-push {scan_branch} and re-run.")

# 2. Run the AI Per-CM Loop (above) with B5 DEFERRED (R-ZP3).
#    Each in-scope CM -> ai_status/ai_confidence/findings, note_post_status="DEFERRED_HYBRID" (no POST).
ai_results = run_ai_per_cm_loop(deferred_post=True)   # dict keyed by full_cm_id

# 3. Reconcile the scan + push (R-ZP5) — poll status every 1 minute.
#    scan_timeout_ms is the internal 30-min default safety cap (A-ZP2; no longer asked).
deadline = now() + scan_timeout_ms
while scans_get(scanId).status not in ("Finished", "Errored"):
    if now() > deadline:
        scans_cancel(scanId); print("[WARN] scan hit the 30-min default cap; ZP signal will be unavailable for merge."); break
    sleep(60_000)   # poll every 1 minute
push_ok = False
if scans_get(scanId).status == "Finished":
    # scope to THIS project+mapping (NOT scanId-only) and PAGINATE — a sibling SDE project mapped to
    # the same repo can reach push "success" for the same scanId first (see R-ZP5 / Phase B-ZP note).
    def hyb_push_success():
        for ev in iterate_sync_history(page_size=50):
            if (ev.apiEndpointName == "security_compass.push" and ev.status == "success"
                    and ev.scanId == scanId and ev.sdeProjectId == sdeProjectId and ev.mappingId == mappingId):
                return ev
        return None
    while not hyb_push_success():
        if now() > deadline: break
        sleep(5_000)
    push_ok = hyb_push_success() is not None
audit = getMappingAudit(mappingId)

# 4. Merge per in-scope CM and post ONE combined note
#    ONLY finalize CMs whose AI-loop disposition is a deferred verdict
#    (note_post_status=="DEFERRED_HYBRID"). CMs the AI loop recorded as
#    skipped (user skip/stop) or skipped_out_of_scope (B0a/B0b3, handoff mode)
#    keep their disposition — NO combined note, NO ZP read. This preserves the
#    Sum-check identity (their S / S_oos entries are untouched).
NP = 0; NF = 0; pass_by_absence = 0; weak_pass_cms = []
for cm in in_scope:                              # AI scope only
    r = result_for(cm.full_id)                   # the entry recorded by the AI loop
    if r.note_post_status != "DEFERRED_HYBRID":
        continue                                 # skipped / OOS — leave as-is
    ai = ai_results.get(cm.full_id)              # subagent/inline AI verdict (object with .status/.confidence); may be partial on timeout/malformed
    if ai is None:                               # parent forced-fail lanes (B0b/B0b2) record DEFERRED_HYBRID without a subagent verdict and record_verified does NOT persist ai_status -> default to "fail" (the forced-fail verdict), avoiding KeyError/undefined
        ai = ai_verdict(status=getattr(r, "ai_status", "fail"), confidence=getattr(r, "ai_confidence", "high"))
    # --- ZP signal: read ZeroPath's OWN SDE note, keyed by task_id (NOT securitycompass aggregates) ---
    # ZeroPath-native notes have an EMPTY finding_ref; the skill's own combined note starts with
    # "Agent: ...". On a re-run the skill's note is newest, so a bare .latest() would read OUR verdict
    # as ZeroPath's. Always pick the latest note whose finding_ref == "".
    zp_note = (next((n for n in verification(op="list", project_id=sdeProjectId, task_id=cm.full_id).results
                     if n.finding_ref == ""), None)
               if push_ok else None)
    if zp_note and audit.coverage_of(cm.full_id) in ("sast", "nl_rule"):
        zp_status = zp_note.status                       # pass (count0=pass-by-absence) | fail
    else:
        zp_status = None                                 # unsupported/unmapped or push missing -> no ZP signal
    # --- ZP issue link for fails (LINK-ONLY; never sets verdict) ---
    zp_issue_url = None
    if (zp_status == "fail") or (ai.status == "fail"):
        hit = vulnerabilities_search(query=f"{cm.title} {cm.problem}").top_match(repositoryId)  # or endpoints_search
        zp_issue_url = issues_get(hit.id).url if hit else None
    # --- pick final status: authoritative source; fall back to the other when one has no signal ---
    if zp_status is None:        final = ai.status
    elif authoritative_source == "ai":   final = ai.status
    else:                         final = zp_status
    final_conf = ai.confidence if (authoritative_source == "ai" or zp_status is None) else "high"
    # --- R-ZP9 weak-pass (pass-by-absence) WARN: only when a ZeroPath count:0 pass SET the final verdict ---
    # NOTE ON SEMANTICS: `pass_by_absence` (and the handoff `pass_by_absence_count`) counts VERDICT-SETTING
    # weak passes ONLY (authoritative_source=="zeropath"). With authoritative_source=="ai" it is 0 even if
    # ZeroPath returned count:0 passes for several CMs — because the AI verdict, not the ZP pass, governs.
    # It is NOT a raw tally of every ZeroPath count:0 pass; do not read it as "how many CMs ZeroPath passed-by-absence".
    zp_issue_count = int(zp_note.findings[0].count) if (zp_note and zp_note.findings) else 0
    if final == "pass" and zp_status == "pass" and zp_issue_count == 0 and authoritative_source == "zeropath":
        pass_by_absence += 1; weak_pass_cms.append(cm.full_id)
        print(f'[WARN] Weak pass — {cm.full_id} "{cm.title}": ZeroPath scanned and found no violation, '
              f'but "no violation found" is NOT proof the control is in place. ZeroPath auto-marked this Done. '
              f'Treat as unverified until AI/human confirms the control exists.')
    # --- B4 preserve, then ONE combined note (R-ZP4 behaviour=combine) ---
    existing = verification(op="list", project_id=sdeProjectId, task_id=cm.full_id)
    findings = build_combined_findings(ai, zp_note, zp_issue_url, existing)   # AI desc + ZeroPath desc (+url) + preserved
    tsm = resolve_task_status_mapping(statusChoices, fail_rollback_opt_in, final)  # pass->DONE always; fail->TODO only if opt-in
    finding_ref = (f"Agent: zp-code-scan-verification-validation | Model: {model} | Repo: {repo_name} "
                   f"| CM: {cm.full_id} | Run: {iso8601_utc} | Engine: hybrid | Handoff: .sde-verification-handoff.json")
    post = verification(op="create", project_id=sdeProjectId, task_id=cm.full_id,
                        behaviour="combine", status=final, confidence=final_conf,
                        findings=findings, finding_ref=finding_ref, pinned=False, task_status_mapping=tsm)
    # retry/back-off + auth-failure HARD STOP exactly as the AI B5 contract
    # --- FINALIZE the result entry: replace DEFERRED_HYBRID; this status feeds the Sum-check ---
    r.status            = final                  # P/PT/F bucket is now the combined verdict
    r.confidence        = final_conf
    r.ai_status         = ai.status
    r.zp_status         = zp_status if zp_status is not None else "none"
    r.zp_issue_url      = zp_issue_url
    r.note_post_status  = post                   # "POSTED" or "FAILED:{reason}" — never leaves as DEFERRED_HYBRID
    NP += (post == POSTED); NF += (post != POSTED)
    print(f"[VERIFY] {done}/{in_scope_total} | {cm.full_id} | ai={ai.status} zp={zp_status} -> {final} | note={post}")
# INVARIANT: after this loop, NO result entry may retain note_post_status=="DEFERRED_HYBRID".
# Totals (P/PT/F/S/S_oos) are recomputed from the finalized results; Sum-check uses them.
# Step D writes the handoff with scan_engine="hybrid", zeropath{} block, and per-result ai_status/zp_status/zp_issue_url.
```

**Notes:**
- **Out-of-AI-scope CMs:** ZeroPath's push may have written notes on mapped CMs that are NOT in the AI scope; those ZeroPath notes stand as-is (the skill posts combined notes ONLY for in-scope CMs). Coverage math below is scoped to in-scope CMs.
- **Authoritative AI `fail` overriding ZeroPath pass-by-absence DONE:** if `authoritative_source == "ai"` and `final == "fail"`, the combined note carries `status=fail`; with `fail_rollback_opt_in == "yes_rollback"` the `task_status_mapping.fail` rolls the CM back from the DONE ZeroPath's push set. Without opt-in, only `verification_status` flips to fail (task stays DONE). This is the core value of Hybrid.
- **Degraded AI verdict:** AI timeout/malformed → `ai.status="partial"` (per the AI loop contract); the merge still posts a combined note. AI/SDE 401/403 during the loop still HARD STOPs the whole run (records unreached via `record_skipped`) before any merge POST.

### Phase B-HYB Completion Verification Block (REQUIRED for `hybrid`)

```
=== COMPLETION VERIFICATION (Hybrid) ===
Skill: code-scan-verification-validation
Scan engine: hybrid | Authoritative source: {authoritative_source}
MCP connections: ✓ (sdelements + zeropath + securitycompass; tenant match)
ZeroPath scan: {scanId} status={Finished|timed-out} | push success: {YES/NO}
Per-CM verdicts (SDE UI labels; from combined notes):
- Pass: {P} | Partial Pass: {PT} | Fail: {F} | Skipped (user): {S} | Skipped (OOS): {S_oos}
Weak passes (ZeroPath found nothing, so the pass is unproven): {pass_by_absence} of {in_scope_total}
  -> marked Done but NOT positively verified: {weak_pass_cms or none} (only when authoritative source = ZeroPath)
Combined Verification Notes: POSTED {NP} | FAILED {NF} (IDs: {list or none})
Sum check: {P + PT + F + S + S_oos} == {canonical_total}? {YES/NO}   (canonical_total = in_scope_total on a FRESH run; = already_done + in_scope_total on RESUME — totals recomputed from the MERGED verification_results[]; matches Layer-3)
Posted-note coverage (re-derived from SDE via verification op=list, matched on the combined finding_ref) == NP? {YES/NO}
APPEND check (verification op=list shows >= 2 notes per in-scope mapped CM: ZeroPath's + combined) == YES? {YES/NO}
================================================
```

**Also apply the T9 terminal verification + the T5 gate-the-gate precondition** (the BATCH PLAN + a mini-gate per batch for the hybrid AI loop): Layer 1 (re-derive from the per-CM disk artifacts in `.sde-security/verify/{project_id}/cm-work/`, written AFTER the merge replaced `DEFERRED_HYBRID`), Layer 2 (`verify_disk_vs_sde(in_scope_total, in_scope_ids)` where `in_scope_ids = [cm.full_id for cm in in_scope]` — counts ONLY this run's in-scope artifacts, exits 0), Layer 3 (tri-source: SDE in-scope set == disk artifacts == handoff rows == in_scope_total). All YES required.

**If Sum check = NO, posted-note coverage = NO, APPEND check = NO, any T9 layer fails, or NF > 0 without cause:** output `INCOMPLETE` and retry/reconcile before declaring complete. **If all YES:** `✅ COMPLETION GATE PASSED (Hybrid)`.

---

## Step D. Write Own Handoff File

After the loop completes (or exits via user `stop`), write `.sde-verification-handoff.json` to `{repository_path}`. In handoff mode, **do not overwrite `.sde-apply-handoff.json`** — the upstream file must remain intact so the user can re-run `apply-fixes` or `code-scan-verification-validation` without losing audit data.

### Per-CM disk-offload + assemble-from-disk (T6 — context-window survival)

> The per-CM result RECORD is offloaded to disk AS IT IS PRODUCED so the parent context stays small (200K-survivable, multi-session normal). **This stores the OUTPUT of the AI's analysis — it NEVER replaces B2/B3 (the AI vuln analysis + verdict stay AI-only inline; SHELL TOOL USAGE POLICY).** The handoff `verification_results[]` is ASSEMBLED FROM DISK, never from in-context memory. Namespaced dir (chain-compat): `.sde-security/verify/{project_id}/cm-work/{full_cm_id}.json` (NEVER the shared `.sde-security/cm-work/`).
>
> **Engine gating:** `ai` offloads each CM's verdict/findings as produced. `hybrid` offloads TWICE: (1) a DEFERRED artifact per-CM DURING the AI loop (`note_post_status=DEFERRED_HYBRID`) so the per-batch T5 mini-gate's disk-count passes while the loop runs; (2) the Phase B-HYB merge OVERWRITES each with the FINAL combined record (`POSTED`/`FAILED`). A per-CM artifact therefore exists throughout — deferred during the loop, final after merge. `zeropath` has no AI loop — it offloads the per-CM coverage / pass-by-absence mirror record (`note_post_status = "NOT_SENT_ZP_NATIVE"`) so the handoff + Layer-2 verify still re-derive from disk.

These helper routines are MECHANICAL (IO only) — implement them yourself from this pseudocode (PoC-proven before shipping). The per-CM record IS the full `verification_results[]` entry (see the Step D schema below): `full_cm_id, status, confidence, findings, note_post_status, reason` are ALWAYS present; `title`, `findings_aggregated_for_sde`, `finding_ref` (and, for hybrid, `ai_status`/`ai_confidence`) are present for verified/posted entries and ABSENT for `skipped`/`skipped_out_of_scope`. `REQUIRED_KEYS` is the always-present subset the assemble step validates (optional fields allowed).

```python
CM_WORK = f".sde-security/verify/{project_id}/cm-work"   # namespaced; NOT the shared cm-work/
REQUIRED_KEYS = {"full_cm_id", "status", "confidence", "findings", "note_post_status", "reason"}  # always-present subset; verified/posted entries ALSO carry title, findings_aggregated_for_sde, finding_ref (+ ai_status/ai_confidence for hybrid)
VALID_STATUS  = {"pass", "partial", "fail", "skipped", "skipped_out_of_scope"}

def offload_cm_result(full_cm_id, result):
    # write the ALREADY-PRODUCED result (ai/hybrid: AI verdict; zeropath: ZP-native mirror).
    # Mechanical; performs NO analysis.
    os.makedirs(CM_WORK, exist_ok=True)
    write_json(f"{CM_WORK}/{full_cm_id}.json", result)   # one file per CM
    print(f"[FIDELITY] {full_cm_id}: status={result['status']} findings={len(result.get('findings',[]))} offloaded=YES")

def assemble_handoff(in_scope_ids):
    # Step D: build verification_results[] by READING DISK for THIS RUN's in-scope CMs ONLY.
    # NEVER os.listdir the whole dir: the namespaced dir is keyed by project_id (NOT by
    # verification_mode/scan_engine), so it can hold artifacts from a PRIOR run of a DIFFERENT
    # mode/engine (e.g. a zeropath enter_project run left per-CM mirror artifacts). Those are not
    # this run's and MUST NOT be ingested. Carried-forward already_done entries merge SEPARATELY
    # from the prior handoff JSON (resume-merge below), not from a disk glob.
    # (in_scope_ids: ai/hybrid = [cm.full_id for cm in in_scope]; zeropath = mapped_in_scope_cms full_ids.)
    results = []
    for full_cm_id in in_scope_ids:
        path = f"{CM_WORK}/{full_cm_id}.json"
        assert os.path.exists(path), f"{full_cm_id}: missing offload artifact (a Phase B lane skipped offload_cm_result)"
        rec = read_json(path)
        assert REQUIRED_KEYS <= set(rec), f"{full_cm_id}: missing required keys"   # subset: optional title/findings_aggregated_for_sde/finding_ref (+ai_status/ai_confidence hybrid) allowed
        assert rec["status"] in VALID_STATUS and rec["full_cm_id"] == full_cm_id
        results.append(rec)
    return results            # THIS run's entries; merged with carried-forward already_done on resume

def verify_disk_vs_sde(expected_count, in_scope_ids):
    # Layer-2 (terminal verification): count THIS RUN's in-scope artifacts ONLY (existence check
    # per in-scope full_cm_id) — never a whole-dir glob, so foreign/stale artifacts from a prior
    # different-mode run cannot over-count. Non-zero exit on shortfall.
    n = sum(1 for full_cm_id in in_scope_ids if os.path.exists(f"{CM_WORK}/{full_cm_id}.json"))
    return 0 if n == expected_count else 1   # context-light: existence checks only, never reads bodies
```

In Phase B / B-HYB, immediately after a CM's result entry is finalized on EVERY disposition lane (parent short-circuits B0a/B0b/B0b2/B0b3, `one_by_one` B0c skip/stop, subagent verdict/malformed/OOS/auth, inline path; for `hybrid` the AI loop offloads a DEFERRED artifact per-CM during the loop — so per-batch mini-gates pass — and the merge then OVERWRITES it with the final combined record), call `offload_cm_result(full_cm_id, entry)` — every `results.append(record_*(...))` is immediately followed by `offload_cm_result(cm.full_id, results[-1])`; a lane that appends without offloading causes a Layer-2 disk-count shortfall. In Step D, build `verification_results[]` via `assemble_handoff(in_scope_ids)` where `in_scope_ids` is THIS run's scope-filtered set (ai/hybrid = `[cm.full_id for cm in in_scope]`, on resume `still_todo`; zeropath = the mapped/in-scope CM full_ids) — then apply resume-merge below. Both disk helpers take the in-scope ID list so they read/count ONLY this run's artifacts, never a whole-dir glob. The expected denominator for `verify_disk_vs_sde(in_scope_total, in_scope_ids)` is `in_scope_total` (the Anchoring Rule) — never "work so far." (For `zeropath`, `in_scope_total` = the mapped/in-scope CM count mirrored from `getMappingAudit`.)

**Resume merge logic:** If Step A1.5+A3 loaded a prior verification run and the user chose to resume, the handoff MUST merge prior results with new results. `verification_results[]` is the concatenation of carried-forward prior entries (`already_done`) and newly-derived entries from this session. Totals are recomputed from the merged set. The `resumed_from` field records the prior handoff's `generated_at` timestamp for audit traceability.

> **Engine fields are ADDITIVE.** `source_skill` stays `"code-scan-verification-validation"` and the filename stays `.sde-verification-handoff.json` (shared resume with the original skill — resume reconciliation matches entries with `status in {pass,partial,fail}` regardless of which `scan_engine` produced them). The new `scan_engine`, `authoritative_source`, and `zeropath` keys, and the per-result `ai_status`/`zp_status`/`zp_issue_url` keys, are absent in `ai`-engine handoffs (or null) and present for `zeropath`/`hybrid`.

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
  "repository_path": "{repository_path}",
  "scope": "all | selected_cms | one_by_one",
  "scope_args": { "cm_ids": ["..."] },
  "fail_rollback_opt_in": "yes_rollback | no_verification_only",
  "zeropath": {
    "repositoryId": "{uuid or null}",
    "mappingId": "{uuid or null}",
    "scanId": "{uuid or null}",
    "scan_branch": "{branch ZeroPath scanned, or null}",
    "scan_branch_remote_sha": "{verified pushed tip of scan_branch, or null}",
    "commitSha": "{sha ZeroPath actually scanned (== scan_branch_remote_sha on success), or null}",
    "sync_stats": { "countermeasuresFetched": 0, "sastDetectable": 0, "rulesCreated": 0, "skipped": 0 },
    "push_stats": { "issuesMapped": 0, "countermeasuresMarkedDone": 0, "unmapped": 0, "status": "success | failed | none" },
    "coverage": [ { "taskId": "{project_id}-T123", "coverage": "sast | nl_rule | unsupported" } ],
    "pass_by_absence_count": 0
  },
  "totals": {
    "verified_pass": P,
    "verified_partial": PT,
    "verified_fail": F,
    "skipped": S,
    "skipped_out_of_scope": S_oos,
    "note_failed": NF
  },
  "verification_results": [
    {
      "full_cm_id": "{project_id}-T123",
      "title": "...",
      "status": "pass | partial | fail | skipped | skipped_out_of_scope",
      "confidence": "high | low | n/a",
      "ai_status": "pass | partial | fail | null",
      "zp_status": "pass | fail | none | null",
      "zp_issue_url": "{https://...zeropath.com/app/issues/... or null}",
      "findings": [
        { "file": "src/auth.ts", "line": 42, "description": "Parameterised query; matches ctx.text guidance.", "category": "mitigation-confirmed" }
      ],
      "findings_aggregated_for_sde": [
        { "desc": "[AI-SAST via Code Scan Verification Validation | {model}] Mitigation confirmed in {file_basenames}: how-to {how_to_id} pattern present | verdict=pass confidence=high", "count": "1" }
      ],
      "finding_ref": "Agent: code-scan-verification-validation | Model: {model} | Repo: {repo_name} | CM: {project_id}-T123 | Run: {iso8601_utc} | Handoff: .sde-verification-handoff.json",
      "note_post_status": "POSTED | FAILED:{reason} | NOT_SENT | NOT_SENT_OUT_OF_SCOPE | NOT_SENT_FORCED_FAIL | NOT_SENT_AUTH_FAILURE | DEFERRED_HYBRID | NOT_SENT_ZP_NATIVE",
      "reason": ""
    }
  ],
  "failed_cms_for_rework": [
    { "full_cm_id": "{project_id}-T145", "reason": "residual marker vuln-code-snippet at src/x.ts:88" }
  ]
}
```

`failed_cms_for_rework[]` is a convenience list populated from entries where `status == "fail"`. It lets a future rework skill (or a second pass of `apply-fixes`) target exactly the broken mitigations.

**Engine-specific `note_post_status` sentinels:**
- `DEFERRED_HYBRID` — (hybrid only, transient) the AI loop produced a verdict but deferred the POST; the FINAL handoff entry is rewritten to the combined-note result (`POSTED` / `FAILED:{reason}`) after Phase B-HYB posts. A `DEFERRED_HYBRID` value MUST NOT survive into the written handoff.
- `NOT_SENT_ZP_NATIVE` — (zeropath only) the skill posted nothing; ZeroPath's native push wrote this CM's verification note. `status`/`zp_status` mirror ZeroPath's SDE note; `confidence` is `n/a`.

**Hybrid combined-note `finding_ref`:** the Phase B-HYB combined note uses `Agent: zp-code-scan-verification-validation | Model: {model} | Repo: {repo_name} | CM: {full_cm_id} | Run: {iso8601_utc} | Engine: hybrid | Handoff: .sde-verification-handoff.json` (distinct from ZeroPath's own note, which has an empty `finding_ref`). The Hybrid completion gate re-derives posted-note coverage by matching THIS `finding_ref`. (The `ai`-engine `finding_ref` is unchanged — `Agent: code-scan-verification-validation | ...` — so AI-engine runs stay byte-faithful.)

`skipped_out_of_scope` entries **(handoff mode only)** record CMs that were skipped without a verification note POST because `cm.status == "Documented"` (parent B0a), because the parent's B0b3 lane fired (non-code CM with empty `files_modified[]`, `handoff_version == "2"`), or because the subagent's L-OOS-sub lane fired (non-code CM with empty `files_modified[]`, `handoff_version == "1"`). In standalone mode, B1.5 is skipped entirely (no L-OOS-sub); the B1.7 file discovery step handles the "no relevant files" case with a `pass`/`high`/`vulnerability-absent` verdict instead — standalone mode does not produce `skipped_out_of_scope` entries. These handoff-mode sub-cases behave differently under scope filtering: **Documented CMs** are excluded by `filter_by_scope` under `all` / `one_by_one` and only enter the loop via `selected_cms` (where B0a fires); **Applied non-code CMs with empty `files_modified[]`** pass the scope filter under all scopes (they are Applied, not Documented) and produce `skipped_out_of_scope` entries via B0b3 (v2) or L-OOS-sub (v1) inside the loop. For all `skipped_out_of_scope` entries, `findings` is `[]`, `findings_aggregated_for_sde` is `[]`, `confidence` is `"n/a"`, `note_post_status` is `"NOT_SENT_OUT_OF_SCOPE"`, and no payload was constructed or sent — but the entry is still recorded so audit/totals reconciliation works downstream. `skipped` (user) entries follow the same shape as `skipped_out_of_scope` entries — `findings`/`findings_aggregated_for_sde` are `[]`, `confidence` is `"n/a"`, no payload was constructed — except `note_post_status` is `"NOT_SENT"` (no out-of-scope qualifier). They are produced by `record_skipped(cm, reason)` in two paths: the `one_by_one` per-CM `skip` path (one entry per skipped CM) and the `one_by_one` `stop` path (one entry for the `stop` CM plus one entry for every remaining in-scope CM). All such entries are mandatory and preserve the Sum-check identity. All `record_skipped` / `record_out_of_scope` entries persist the `reason` string on the entry's `reason` field (Step D schema, alongside `note_post_status`) — this is how downstream tooling distinguishes the three user-initiated no-POST sub-cases (and the Documented out-of-scope case) without consulting console logs.

**[CHECKPOINT]** `Verification handoff written: .sde-verification-handoff.json ({N} records)`

---

## Completion Verification Block (REQUIRED before "complete")

> **PRECONDITION — do NOT emit this block, and do NOT say "complete" / "SKILL COMPLETE" / "done", until `running_total = P + PT + F + S + S_oos == in_scope_total`.** Emitting a completion after fewer CMs is a contract violation. In `one_by_one` scope (ai engine) each per-CM `ask_question` ENDS the turn; when the user replies, CONTINUE the loop to the NEXT in-scope CM (on resume, re-derive the done-set from `cm-work/*.json` — never restart, never finalize). Processing ONE CM is NEVER completion. If `running_total < in_scope_total`, the only valid outputs are: continue the loop, or emit a `=== CONTEXT CHECKPOINT ===` — never a completion line.

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

Sum check: {P + PT + F + S + S_oos} == {canonical_total}? {YES/NO}   (canonical_total = in_scope_total on a FRESH run; = already_done + in_scope_total on RESUME — totals recomputed from the MERGED verification_results[]; matches Layer-3)
Posted-note coverage (re-derived from SDE, NOT the in-memory results array):
  for each POST-eligible in-scope CM, verification op=list -> a note for THIS run
  exists (match on finding_ref)? {YES/NO}  (re-derived count == NP?)
===============================
```

Print the line matching the current `verification_mode`; omit the other.

### Terminal verification (T9 — 3 layers, AI-performed; gate-the-gate precondition)

**Gate-the-gate precondition (this block is INVALID if unmet, `ai`/`hybrid`):** the `=== PHASE B BATCH PLAN ===` was emitted AND a `--- BATCH k/t COMPLETE ---` mini-gate exists for EVERY batch (T5). (`zeropath` is exempt — its gate is the Phase B-ZP block.) If not, return to Phase B.

The completion gate is the conjunction of three independent layers. The AI performs Layers 1 and 3 itself; Layer 2 is the one mechanical (scripted) layer.

- **Layer 1 — inline re-derivation from disk (AI):** re-derive every count from the per-CM disk artifacts `.sde-security/verify/{project_id}/cm-work/*.json` (NOT an in-memory tally), plus a **run-marker proof** (each artifact belongs to THIS run) and a **surviving-output check** (the per-CM artifact exists on disk). The `Sum check` + `Posted-note coverage` lines are Layer 1. (For `zeropath` the artifacts are the ZP-native mirror records.)
- **Layer 2 — verify script (mechanical):** run `verify_disk_vs_sde(in_scope_total, in_scope_ids)` (Step D helper) — disk-only, context-light, counts ONLY this run's in-scope artifacts (never a whole-dir glob, so a prior different-mode run's stale artifacts cannot over-count) and exits non-zero on any shortfall. Paste its result.
- **Layer 3 — from-scratch clean-room tri-source (AI):** trusting NOTHING from the run, assert: **SDE source-of-truth (in-scope CM set) == disk artifacts (`cm-work/*.json` count) == handoff rows (`verification_results[]`) == `in_scope_total`**. Posted-note coverage re-derived from SDE (`verification op=list`, match on `finding_ref`) == `NP` (`ai`/`hybrid`; `zeropath` posts no skill notes — its coverage is the ZeroPath push `countermeasuresMarkedDone`).

ALL THREE layers must be YES before the run is **COMPLETE**.

**If Sum check = NO**, **posted-note coverage = NO**, **Layer 2 exits non-zero**, **the tri-source invariant fails**, or **`NF > 0` without documented cause** → output `INCOMPLETE` and loop back to retry failed notes (or re-fetch / re-offload to reconcile) before declaring completion. Do NOT trust the in-memory POSTED/FAILED flags alone — the coverage line MUST be re-derived from SDE via `verification op=list`.

**If Sum check = YES and NF cause is recorded:**

```
✅ COMPLETION GATE PASSED
Verified {P} Pass / {PT} Partial Pass / {F} Fail / {S} Skipped (user) / {S_oos} Skipped (out of scope)
Rework candidates: {F} (see .sde-verification-handoff.json → failed_cms_for_rework)
```

---

## Numbered Enforcement Rules

1. **Handoff is a hard requirement in handoff mode.** Missing, wrong `source_skill`, or declined by user → HARD STOP. No manual fallback. In standalone mode, SDE project selection (Step A1-S) replaces the handoff requirement. Missing SDE project selection in standalone mode → HARD STOP.
2. **Git tree must be clean of SOURCE changes BEFORE any checkout.** `git status --porcelain` — scoped to exclude the skill's OWN `.sde-security/` scratch and `.sde-verification-handoff.json` (e.g. `git status --porcelain -- . ':(exclude).sde-security/' ':(exclude).sde-verification-handoff.json' ':(exclude).sde-apply-handoff.json' ':(exclude).sde-handoff.json'`) — must be empty, or HARD STOP. A genuine uncommitted source change still HARD STOPs; the skill's own regenerable artifacts never trip this gate.
3. **Upstream `.sde-apply-handoff.json` MUST NOT be modified or deleted by this skill.** Write only to `.sde-verification-handoff.json`.
4. **"In-scope" has one canonical meaning: whatever `filter_by_scope` returned.** Filter behaviour: under `all` / `one_by_one` the filter excludes Documented and Skipped CMs (nothing on disk to scan or no mitigation to verify); under `selected_cms` the filter includes whatever IDs the user explicitly listed (subject to the Step A1.5+A3 warning prompts for Documented and Skipped). `in_scope_total = len(in_scope)` is computed after the filter and used everywhere (loop bound, Sum check, completion block). Every in-scope CM has a recorded result entry: CMs that pass through per-CM verification (B-Subagent or inline) receive a POST attempt and any failure is logged (not silently dropped); user-skipped CMs (`one_by_one`), Documented CMs (under `selected_cms`), non-code CMs with empty `files_modified[]` (parent B0b3 for v2, subagent L-OOS-sub for v1, recorded as `skipped_out_of_scope`), and run-aborted CMs after a subagent auth failure are recorded without an API call (`note_post_status` set to `NOT_SENT` / `NOT_SENT_OUT_OF_SCOPE` / `NOT_SENT_AUTH_FAILURE` respectively) — no POST, but the audit-trail entry is still written. Forced-fail CMs — upstream-Skipped (parent B0b), empty-files-modified code CMs (parent B0b2 for v2, subagent L-FF2-sub for v1) — now receive a B4+B5 POST (inline for parent, inside subagent for L-FF2-sub) with `note_post_status` set to `POSTED` on success or `FAILED:{reason}` on failure. (User-`skip` and user-`stop` in `one_by_one` mode are explicit user choices, not agent-initiated early exits — see Rule 10 for the loop-termination contract.) CMs with `cm.status == "Documented"` are filtered out under `all` / `one_by_one`; they can only enter the loop via `selected_cms` after an explicit user decision, in which case Step B0a short-circuits them as `skipped_out_of_scope` — no subagent dispatch, no SDE fetch, no file reads, no API call, no `task_status_mapping` touch. Pure `PROCESS` CMs never reach this skill (filtered upstream).
5. **No false positives. Negative signal is canonical; positive signal is corroborative.** *(See the verbatim "No-False-Positives Invariant" callout in Phase B.)* If Q1 is `absent_high_confidence` and the marker scan is clean, the verdict is `pass` — regardless of Q2 and Q3. **Q2 is OPTIONAL** — it runs only when `ctx.how_tos[]` is non-empty AND has at least one language-applicable entry; an empty/inapplicable `how_tos[]` is a normal path, not a degraded one. **Never default to `pass` or `fail` on uncertainty.** Uncertainty maps to `partial` with `low` confidence. `fail` is allowed from exactly four cited evidence sources: (1) cited `residual-vulnerable-pattern`, (2) cited `residual-marker`, (3) upstream `Skipped` audit status (parent B0b) **(handoff mode only)**, (4) empty `files_modified[]` for CODE_FIX/ML_CODE (parent B0b2 when `handoff_version == "2"`, subagent L-FF2-sub when v1) **(handoff mode only)**. Standalone mode uses only sources (1) and (2). Failure to recognise the developer's mitigation style is NEVER a `fail` or `partial` source.
6. **Progress output is mandatory.** Every per-CM transition emits exactly one of the canonical checkpoint formats listed in the Mandatory Checkpoints table (`[VERIFY]` for normal subagent return / forced-fail / malformed-subagent / auth-failure-current-CM; `[VERIFY-DISPATCH]` immediately before each batch dispatch (subagent launch or inline execution start); `[SKIP-OOS]` for Documented under `selected_cms` (parent B0a), parent B0b3 (non-code CM with empty files, v2), AND subagent L-OOS-sub returns (`parsed.result_kind == "out_of_scope"`, v1); `[SKIP-USER]` for `one_by_one` per-CM `skip`; `[STOP]` for `one_by_one` `stop` AND for the auth-failure aborted run, in both cases bulk-summarising the unreached CMs; `[INFO]` for the empty-in-scope short-circuit). The unreached CMs after `stop` or auth-failure are recorded individually in `verification_results[]` (preserving Sum-check) but share a single `[STOP]` line — that is the contract.
7. **`task_status_mapping.fail: TODO` is ONLY sent if the user opted in at Step A4.** Default behaviour leaves workflow status untouched on fail. The opt-in flag is forwarded to each subagent via the `task_status_mapping_opt_in` placeholder in the prompt template.
8. **Residual vulnerability markers are a fail criterion**, even if the logic appears fixed. The hardcoded marker list MUST appear verbatim in the subagent prompt template.
9. **Completion verification block is required** before any use of the words "complete", "finished", "done", "summary".
10. **No agent-initiated early exit.** Two user-initiated early-exit paths are allowed in `one_by_one` scope, and BOTH preserve the Sum-check identity `P + PT + F + S + S_oos == in_scope_total`:
    - **per-CM `skip`** — records `record_skipped(cm, reason="user skipped")` and continues to the next CM.
    - **`stop`** — records `record_skipped(cm, reason="user stopped (loop terminated at this CM)")` for the current CM AND `record_skipped(c, reason="user stopped (loop terminated; not reached)")` for every remaining in-scope CM (`in_scope[done:]`), then terminates the loop.

    A third *involuntary* run-terminating path exists: subagent `auth_failure: true` (401/403). Parent records the current CM with `NOT_SENT_AUTH_FAILURE` and every unreached CM via `record_skipped(c, reason="run aborted: auth failure at ...; not reached")`. This preserves the Sum-check identity even though the run did not complete successfully.

    No other path may bypass the per-CM verification cycle (B1 + B2 + B3 + B4 + B5) for an in-scope CM — whether that cycle runs inside a subagent (`execution_mode == "subagent"`) or inline in the parent (`execution_mode == "inline"`, Step A6 fallback). No agent-initiated condition (context limits, "critical ones done", repository intent) is a valid early exit. **In `one_by_one` scope specifically (ai engine): after each per-CM decision (a turn boundary), you MUST continue to the next in-scope CM until `running_total == in_scope_total`. Declaring the run complete — or emitting "SKILL COMPLETE"/a completion block — after a single CM is the most common violation and is FORBIDDEN; there is no per-CM or single-CM completion state, only the whole-scope Sum-check.**
11. **API payload + concept model MUST conform to the SDE spec.**
    - `behaviour` MUST be one of `combine` / `replace-scanner` / `replace`. `append` is invalid.
    - Each `findings[]` element MUST include `desc` and `count` (aggregated; per-location detail goes in the local handoff).
    - Every `fail` verdict MUST emit at least one finding.
    - Verification status (`pass`/`partial`/`fail`/`none`) and countermeasure status (`TODO`/`DONE`/`NA`) are separate concepts; never conflate them.
    - Notes without `analysis_session` register as Manual Verification by design; do NOT fake an `analysis_session`.
    - `finding_ref` MUST use the `Agent: code-scan-verification-validation | Model: {model} | Repo: {repo_name} | CM: {full_cm_id} | Run: {iso8601_utc} | Handoff: .sde-verification-handoff.json` form.
    - References: [Verification Notes API](https://docs.sdelements.com/master/api/docs/analysis-notes/), [Verification status (User Guide)](https://docs.sdelements.com/master/guide/docs/integrations/security_tools/overview/verification_status.html).
12. **Per-CM verification MUST be performed by a `generalPurpose` subagent (batched)** — unless `execution_mode == "inline"` (Step A6 fallback; see also AGENTS.md Rule 9). When `execution_mode == "subagent"`, the parent loop is a pure orchestrator — no inline B1 fetch, no inline B2 analysis, no inline B4 note-fetch, no inline B5 POST for any in-scope CM that survives the parent short-circuit lanes. CMs are grouped into batches of `batch_size` (default 10, configurable in Step A5). Each batch is dispatched to one `generalPurpose` subagent which processes its CMs sequentially and returns a JSON array. Up to 5 batches may run in parallel per round. **Exception:** When the MCP client does not support subagent generation (`execution_mode == "inline"` from Step A6), B1/B2/B3/B4/B5 run inline in the parent context with `batch_size=1`, no parallel dispatch, and mandatory context checkpoints every 5 CMs. This is the inline-fallback exception to the subagent-only rule; separately, the parent forced-fail short-circuits (B0b/B0b2) run B4+B5 inline (a scoped exception — see Rule 9), because those CMs never enter the subagent pipeline.
13. **Subagent contract is non-negotiable.** Subagent type MUST be `generalPurpose`. Input MUST include the batch array, the verbatim No-False-Positives Invariant, B-Sub procedure, B3 verdict matrix, hardcoded marker list, batch iteration procedure, and strict JSON array return schema (rendered from the Subagent Prompt Template appendix). The subagent MUST return a strict JSON array with no extra prose; the parent MUST validate against the schema (array length == batch size, each element's `full_id` matches).
14. **Malformed subagent output is `partial`/low/`analysis-uncertain`, NEVER `fail`.** A parse error is not vulnerability evidence; recording it as `fail` would itself be a false positive. If the entire batch output is malformed, every CM in the batch is recorded as `partial`/low. If an individual element within a valid array is malformed, only that CM is recorded as `partial`/low; other CMs use their own parsed results.
15. **Subagent `auth_failure: true` stops dispatching further ROUNDS.** Continuing would silently fail every remaining CM and corrupt totals. Record the auth-failure CM (`NOT_SENT_AUTH_FAILURE`) and every unreached CM (the rest of this batch + all batches in subsequent rounds) via `record_skipped` (deduped by `full_id`; sibling batches already returned in the same round keep their real verdicts), and surface a remediation message.
16. **Subagent timeout triggers retry, then graceful degradation.** If a subagent does not return within `subagent_timeout_ms` (default 300000 = 5 minutes), the parent kills it and re-launches the same batch (up to `max_retries=2` retries, 3 total attempts). After exhaustion, every CM in the batch is recorded as `partial`/low with finding category `subagent-timeout` and `note_post_status="FAILED:subagent-timeout"`. A timeout is not vulnerability evidence; recording it as `fail` would be a false positive.

### ZeroPath / Hybrid Engine Rules (R-ZP1 – R-ZP11)

These apply ONLY when `scan_engine in {"zeropath","hybrid"}` and are **strictly additive** — they never weaken Rules 1-16. The AI verdict engine and Rules 1-16 apply unchanged to `scan_engine == "ai"` and to the AI half of `hybrid` (only delta in hybrid: R-ZP3 defers B5). (Full enforcement detail mirrored in AGENTS.md "ZeroPath / Hybrid Engine Rules".)

- **R-ZP1 — Preflight + tenant-match (both):** run Step A0-ZP before A0.5; HARD STOP on any MCP unreachable/unauthenticated, no enabled integration, or `host(getIntegration.sdeBaseUrl) != host(SDE_HOST)`. No scan until preflight passes.
- **R-ZP2 — ZeroPath-Only posts no notes (zeropath):** MUST NOT call `verification op=create`; ZeroPath's push owns SDE status; skill only triggers/waits/reports.
- **R-ZP3 — Hybrid deferred POST → one combined note (hybrid):** AI loop defers B5 (`note_post_status="DEFERRED_HYBRID"`, no POST); after push lands the parent posts exactly ONE combined note per in-scope CM.
- **R-ZP4 — Append, never overwrite (hybrid):** combined note uses `behaviour="combine"`; `replace`/`replace-scanner` FORBIDDEN; `append` invalid; B4 fetch-existing first.
- **R-ZP5 — Async-push gate (both):** before reading ZeroPath's per-CM note (hybrid) or reporting push stats (zeropath), wait for `getSyncHistory` `security_compass.push status=success` scoped to THIS run — match `scanId` AND `sdeProjectId` AND `mappingId` (NOT scanId alone: one scanId fans out to every SDE project mapped to the repo, so a sibling project's success would falsely satisfy a scanId-only gate) — and PAGINATE (do not cap at `limit=10`).
- **R-ZP6 — Scan side-effect warning (both):** before `scans_start`, emit the `[WARN] A ZeroPath scan will auto-update mapped CM statuses in SDE project {sdeProjectId}.` line (also in the A7 plan).
- **R-ZP7 — Scanned-commit correctness is governed by R-ZP11 (both):** branch/commit correctness is asserted at A-ZP1.6 + post-scan via `scanTargetBranchCommitSha == scan_branch_remote_sha` (the verified-pushed tip). Do NOT compare `scan.commitSha` against local `git rev-parse HEAD` — `scan_branch` may legitimately differ from the checked-out branch in ZeroPath-Only, so a local-HEAD compare would false-WARN. Optionally read the scanned snapshot via `code_read`/`code_search`.
- **R-ZP8 — Dedicated tools + direct-API for reference endpoints (both):** use dedicated tools; for a reference endpoint with no dedicated tool, use a direct-API call (curl/script + `Authorization: Token`) against the absolute `/api/v2/...` URL -- not `api_request`. (Historical: earlier builds double-prefixed a full path via `api_request` → SPA HTML; the current tool requires a server-relative `/api/<segment>/` path -- CHANGELOG "Harden the generic `api_request` tool".)
- **R-ZP9 — Weak-pass (pass-by-absence) WARN gate (zeropath; also hybrid when a ZeroPath pass-by-absence sets `final`):** for every CM where ZeroPath marked DONE with 0 issues mapped, emit the plain-English `[WARN] Weak pass — {full_cm_id} "{title}": ZeroPath scanned and found no violation, but "no violation found" is NOT proof the control is in place ...` line and surface the count in the completion block. In hybrid this fires only when `authoritative_source == "zeropath"` (i.e. the weak ZeroPath pass actually sets the verdict; when AI is authoritative the AI verdict governs). Run still completes (loud label, not a block).
- **R-ZP10 — Force all CMs (zeropath|hybrid):** these engines ALWAYS verify all mapped/Applicable CMs. Step A1.5+A3 (resume + scope) is SKIPPED; `scope` is forced to `"all"`, `scope_args={}`, `has_prior_run=false`. Narrow scopes (`one_cm`/`selected_cms`/`one_by_one`) and the B0c `one_by_one` prompt are AI-engine-only and never reached under zeropath/hybrid. To scope a subset, use `scan_engine=ai`.
- **R-ZP11 — Scan branch committed + pushed to the ZeroPath remote (zeropath|hybrid):** ZeroPath scans a branch on the remote it clones (`vcs.url`), defaulting to `main` — not the local working branch. A-ZP1.6 MUST ask `scan_branch` and verify it is committed (`git status` clean of SOURCE changes — the skill's own `.sde-security/` scratch + `.sde-verification-handoff.json` are excluded) AND pushed (`git ls-remote --heads {vcs.url} {scan_branch}` present, remote tip == local HEAD). If missing/unpushed → HARD STOP telling the user to `git push -u origin {scan_branch}` (no PR). The skill never pushes for the user. `scans_start` passes `branch=scan_branch`; after the scan assert `scanTargetBranch==scan_branch` and `scanTargetBranchCommitSha==scan_branch_remote_sha`. **Hybrid coherence:** for `hybrid`, `scan_branch` MUST equal A2's checked-out `branch_name` (the AI loop reads local files on that branch) — HARD STOP on mismatch so AI and ZeroPath verify the same code.

**Signal-source rule (hybrid):** read the per-CM ZeroPath verdict from ZeroPath's OWN SDE verification note (`verification op=list`, keyed by `task_id`), NOT from securitycompass aggregates; `count:0` = pass-by-absence. **The ZeroPath signal is the latest note whose `finding_ref == ""` (ZeroPath-native) — NEVER the skill's own `Agent: ...` note.** Using a bare `.latest()` is forbidden: on a re-run the skill's combined note is newest and would be misread as ZeroPath's signal. ZP issue link via `vulnerabilities_search`/`endpoints_search` → `issues_get.url` is LINK-ONLY.

---

## Forbidden Actions

| Action | Why Forbidden | Consequence |
|--------|---------------|-------------|
| (Handoff mode) Running without `.sde-apply-handoff.json` | File is the only source of `files_modified` in handoff mode | HARD STOP |
| (Standalone mode) Running without SDE project selection | No source for countermeasures in standalone mode | HARD STOP |
| Auto-proceeding after handoff load or SDE CM fetch without user confirm | Violates user-confirmation rule | Ask before Phase B |
| `git checkout` on dirty tree | Destroys local work | HARD STOP at Step A2 |
| Overwriting `.sde-apply-handoff.json` | Upstream audit trail is sacred | Write to `.sde-verification-handoff.json` instead |
| Marking `pass` because apply-fixes marked Applied | Status is not evidence | Per-CM verification re-reads files and verifies code |
| Marking `fail` without a cited residual pattern or marker | Defaults on uncertainty are forbidden | Use `partial` + `low` confidence |
| Marking `fail` because the canonical mitigation pattern was not found | False-positive vector — Q2 (canonical mitigation match) is corroborative, not gating | Apply the No-False-Positives Invariant; if Q1 is `absent_high_confidence`, verdict is `pass` |
| Marking `partial` because the developer used a different mitigation style than the how-to | Same false-positive vector | If Q1 is `absent_high_confidence` and marker scan is clean, verdict is `pass` regardless of Q2/Q3 |
| Marking malformed-subagent-output as `fail` | Parse error is not vulnerability evidence | Record `partial`/low with `analysis-uncertain` finding |
| Running B1, B2, B3, B4, or B5 inline in the parent context (when `execution_mode == "subagent"`) | Context-budget contract — parent is a pure orchestrator | Dispatch batched `generalPurpose` subagents (batch_size CMs per subagent). Exception: `execution_mode == "inline"` (Step A6 fallback) runs B1/B2/B3/B4/B5 inline with batch_size=1 and context checkpoints. Additional exception: parent B0b/B0b2 forced-fail short-circuits run B4+B5 inline (see Rule 9 forced-fail POST exception) |
| Marking subagent-timeout as `fail` | Timeout is not vulnerability evidence | Record `partial`/low with `subagent-timeout` finding |
| Skipping the parent forced-fail short-circuits (B0b, B0b2/B0b3 for v2) before per-CM verification | Forced-fail evidence is the upstream `Skipped` audit signal (B0b) or empty `files_modified[]` with known category (B0b2/B0b3); proceeding to verification is wasteful and risks re-deriving the wrong verdict | Always run B0a/B0b/B0b2/B0b3 BEFORE dispatching a subagent or starting inline verification |
| Accepting subagent output without JSON-schema validation | Malformed verdicts corrupt totals | Validate; on parse error record `partial`/low/`analysis-uncertain` |
| Dispatching FURTHER ROUNDS (new subagent launches) after a subagent reports `auth_failure: true` | Every subsequent subagent will fail identically; partial run corrupts totals | Stop dispatching further rounds; still record the same-round sibling batches already returned with their real verdicts; record unreached CMs (rest of this batch + subsequent rounds) as `record_skipped` (deduped by `full_id`); surface remediation |
| Using `project_countermeasures op=update` to set verification | That field is read-only there | Subagent uses `verification op=create` |
| (zeropath\|hybrid) Using the `api_request` tool | Prefer dedicated tools; `api_request` requires a server-relative `/api/<segment>/` path (historically double-prefixed → SPA HTML) | Dedicated tools; direct-API (curl/script + `Authorization: Token`) shell fallback (R-ZP8) |
| (zeropath) Posting any `verification op=create` note | ZeroPath's push owns SDE status | Trigger/wait/report only (R-ZP2) |
| (hybrid) AI loop posting B5 in-loop | Must be ONE combined note | Defer B5 (`DEFERRED_HYBRID`); parent posts combined note (R-ZP3) |
| (hybrid) Combined note with `replace`/`replace-scanner` | Clobbers ZeroPath's note | `behaviour=combine` + B4 fetch-existing (R-ZP4) |
| (hybrid) Reading per-CM ZP verdict from securitycompass aggregates | Aggregates have no per-CM detail | Read ZeroPath's SDE note via `verification op=list` keyed by `task_id` |
| (zeropath\|hybrid) `scans_start` without side-effect warning or before preflight | Scan mutates SDE; wrong-tenant risk | R-ZP6 warning; run A0-ZP first (R-ZP1) |
| (zeropath\|hybrid) Scanning without verifying `scan_branch` is committed + pushed | ZeroPath silently scans stale `main` / unpushed code | A-ZP1.6 gate: ask branch + verify pushed; HARD STOP telling user to `git push -u origin {scan_branch}` (R-ZP11) |
| (zeropath\|hybrid) The skill pushing/committing the branch itself | The user owns their git history/remote creds; auto-push is unsafe | Verify + instruct only; user runs the push (R-ZP11) |
| (zeropath\|hybrid) Reading push results before push success | Push is async | Wait for `security_compass.push status=success` (R-ZP5) |
| Sending `task_status_mapping.fail: TODO` without A4 opt-in | User did not consent to workflow rollback | Omit the fail mapping (controlled via `task_status_mapping_opt_in` placeholder) |
| Skipping the residual-marker check | Markers indicate incomplete cleanup | Include the marker list verbatim in the subagent prompt template |
| Grep-only verdict | Grep can't read semantics | Subagent must `read_file` + perform AI analysis (Q1/Q2/Q3) |
| Agent-initiated early exit before all `in_scope_total` CMs are processed (Sum check ≠ YES) | Contract violation | Continue the loop |
| Declaring the run complete / emitting "SKILL COMPLETE" (or the completion block) after processing fewer than `in_scope_total` CMs — especially after the FIRST CM in `one_by_one` | The agent hallucinates completion at a per-CM turn boundary; there is no per-CM or single-CM completion state | Continue to the next in-scope CM (or emit a `=== CONTEXT CHECKPOINT ===`); the completion block is valid ONLY when `running_total == in_scope_total` |
| Requesting elevated shell permissions for local file ops | Unnecessary and triggers approval prompts | Use default sandbox |
| Skipping B4 (fetch existing notes) to save time | Rich upstream note details will be lost; verification notes will overwrite rather than preserve prior context | Always fetch existing notes before POST; B4 failure is non-fatal but the attempt is mandatory |
| **Spawning a subagent on Composer 2 (`composer-2.5-fast`) or any model other than the parent's** | Composer 2 / weaker models silently abandon CM verification loops, skip CMs, use wrong API endpoints for note POSTs, lose context, and produce unreliable verdicts | Set the subagent `model` explicitly to the parent's model (SUBAGENT/DELEGATION POLICY); in Cursor override the Composer-2 default; if you cannot set the model, run inline (`execution_mode = "inline"`) |
| **Delegating in a way that lets CMs be silently skipped, or treating delegation as transferring completeness** | The parent ALWAYS re-derives coverage for every in-scope CM from SDE + disk (tri-source) | Delegate only bounded, verifiable batches; every subagent emits `[VERIFY]`/`[PROGRESS]`; the parent verifies every CM against the Sum-check |

---

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| `.sde-apply-handoff.json` not found | apply-fixes not run, or ran in a different repository | Re-run apply-fixes in this repository first, or switch to standalone mode |
| `source_skill` is not `apply-security-fixes` | Wrong upstream skill, stale file | HARD STOP; ask user to clean up |
| `git status --porcelain` non-empty | Local uncommitted changes | HARD STOP; user stashes or commits |
| `security_branch` not present locally | Handoff refers to a remote-only branch | Fetch, or ask user to proceed on current branch (degraded mode) |
| `files_modified[]` empty for a CODE_FIX CM | apply-fixes bug or skipped CM | Verdict `fail`, finding: "code CM with no modified files" |
| SDE `project_countermeasures op=get` returns 404 | CM re-indexed, project wiped | `partial` + `low` confidence; log the error |
| `verification op=create` returns 429 | SDE rate limit | Sleep 1s, retry once, then record FAILED |
| `verification op=create` or `project_countermeasures op=get` returns 401 / 403 | Project token lacks read or analysis-note write scope | Subagent returns `auth_failure: true`; parent stops dispatching further rounds and records unreached CMs (rest of this batch + subsequent rounds; same-round siblings keep their real verdicts) as `record_skipped` (deduped) to preserve Sum-check; ask user to refresh credentials |
| Subagent returns malformed JSON | Subagent strayed from the strict-JSON instruction or returned partial output | Parent records `partial`/low/`analysis-uncertain` for every CM in the batch (NEVER `fail`); continue to next batch |
| Subagent stalls at "Starting up" for minutes | Platform-level subagent startup issue | Retry/timeout handles this automatically: parent kills after `subagent_timeout_ms` (default 5 min), retries up to `max_retries` (default 2), then records `partial`/low/`subagent-timeout` for the batch. Increase `batch_size` to reduce total launches. |
| Residual `vuln-code-snippet` marker found | apply-fixes cleanup was incomplete | Verdict `fail`; include marker location in findings |
| User selected `one_by_one` for 50 CMs by mistake | Misclick | Offer the "Switch to all" option at the warning prompt |
| SDE task shows many verification notes over time | Intended audit trail (we use `behaviour: "combine"`) | Each run adds a note distinguished by its `finding_ref` timestamp; SDE UI can filter to the latest. Not a bug. |
| B4 note-fetch returns 404/5xx for a CM | CM has no prior notes in SDE, or SDE connectivity issue | Non-fatal; proceed to B5 POST without upstream context; record `upstream-note-fetch-failed` finding (audit-only, no verdict impact) |
| Forced-fail POST returns 4xx/5xx after retries | SDE API issue for the forced-fail CM | Record `FAILED:{reason}` as `note_post_status`; the forced-fail verdict is still recorded locally in the handoff. The CM appears in `failed_cms_for_rework` regardless of POST success. |
| Rework candidate CM has no visible note in SDE | Prior behavior (pre B4+B5 forced-fail POST) — forced-fail CMs used `NOT_SENT_FORCED_FAIL` | Re-run verification for those CMs via `selected_cms` scope to POST notes retroactively |

---

## Handoff to Next Skill

After the completion verification block shows `Sum check = YES`:

```
✅ SKILL COMPLETE: Code scan verification validation finished

=== FINAL COUNTS (SDE UI labels) ===
Pass:                    {P}
Partial Pass:            {PT}
Fail:                    {F}
Skipped (user):          {S}
Skipped (out of scope):  {S_oos}
Verification Notes POSTED: {NP} / {NP + NF}
(POST attempts = P + PT + F = in_scope_total - S - S_oos. User-skipped and out-of-scope CMs receive no API call.)
====================================

Stored values for downstream use (.sde-verification-handoff.json):
- verification_mode: {handoff | standalone}
- upstream_handoff: {.sde-apply-handoff.json | null}
- project_id: {id}
- repository_path: {path}
- scope: {scope}
- fail_rollback_opt_in: {yes_rollback | no_verification_only}
- failed_cms_for_rework: {F} entries

Next skill: (optional) @sde-skills/apply-security-fixes (re-run, scoped to failed_cms_for_rework) OR human review in SD Elements UI.
```

### Downstream Skill Expectations

The downstream skill MUST:
1. Read `.sde-verification-handoff.json` if present.
2. ALWAYS ask the user to confirm loaded values (NEVER auto-proceed).
3. Fall back to full question flow if the user declines.

---

## Appendix: Subagent Prompt Template (CANONICAL — render verbatim)

The parent's `render_batch_subagent_prompt(...)` function MUST emit exactly this template with placeholders substituted. This is the single source of truth for what a verification subagent does. Drift from this template — even paraphrasing — is a contract violation.

```
You are a batched code-scan-verification-validation subagent. You operate in your own
isolated context — there is no shared state with the parent. You will process
a BATCH of countermeasures sequentially. For EACH CM in the batch, you will
perform B1 (fetch CM context from SDE), then mode-dependent steps:
  - Handoff mode: B1.5 (short-circuit) + B2 (AI code analysis on modified files)
  - Standalone mode: B1.7 (file discovery) + B2 (AI code analysis on discovered files)
then B3 (verdict), B4 (fetch existing notes for read-then-append preservation),
and B5 (POST verification note to SDE), and collect the per-CM result.
After processing all CMs, return a strict-JSON ARRAY of results (one
element per CM, in the same order as the input batch). You MUST NOT exceed
this scope: do not modify source files, do not run git, do not write any
local files, do not call other MCP tools beyond `project_countermeasures
op=get`, `verification op=list` (for B4 note fetch), and `verification op=create`
(and in standalone mode, grep/glob/read_file for file discovery in B1.7).

============================================================================
INPUTS (substituted by parent)
============================================================================
BATCH (array of CM descriptors — process each sequentially):
{batch_json}

verification_mode             = {verification_mode}  ("handoff" or "standalone"; parent maps enter_project -> standalone, i.e. B1.7 file discovery)
repository_path               = {repository_path}
repo_name                     = {repo_name}  (basename of repository_path; used in finding_ref)
project_id                    = {project_id}
security_branch               = {security_branch}
task_status_mapping_opt_in    = {task_status_mapping_opt_in}  (true|false; from Step A4)
hybrid_defer                  = {hybrid_defer}  (true|false; true ONLY when scan_engine="hybrid" — defer B5, see B5 step)

Each CM in the batch has: full_id, id, status, files_modified[].
  - Handoff mode: status will be "Applied"; files_modified[] has absolute paths.
  - Standalone mode: status is the SDE task status (DONE/TODO); files_modified[]
    is empty (file discovery happens in B1.7 below).

NOTE (handoff mode only): cm.category may or may not be passed by the parent
(it is present in handoff_version "2" but absent in "1"). Regardless, you MUST
derive ctx.category (CODE_FIX | ML_CODE | INFRA | ML_DOC) from the CM's `phase`
+ `title`/`text` in the B1 fetch response (SDE exposes NO native per-CM
`category` field — use the same classification apply-security-fixes /
generate-security-skill-files apply) and use it in B1.5 (subagent short-circuit
lanes L-FF2-sub and L-OOS-sub). When handoff v2, the parent's B0b2/B0b3 may have
already caught empty-files CMs; surviving CMs still run B1.5 as a redundant
guard. In standalone mode, B1.5 is SKIPPED entirely — proceed to B1.7.

============================================================================
BATCH ITERATION PROCEDURE
============================================================================
Initialize an empty results array. For each CM in the batch (in order):
  1. Run the B-Sub PROCEDURE below for this CM.
  2. Collect the per-CM result object.
  3. Append it to the results array.
  4. If the CM triggered auth_failure (401/403 from B1, B4, or B5):
     - For every REMAINING CM in the batch (not yet processed), append a
       result with result_kind="verified", verdict={status:"partial",
       confidence:"low", findings_for_sde:[{desc:"[AI-SAST via Code Scan
       Verification Validation | {model}] Auth failure on prior CM; batch aborted |
       verdict=partial confidence=low", count:"1"}],
       findings_for_handoff:[{file:"(n/a)", line:0,
       description:"Auth failure on prior CM; not processed",
       category:"context-fetch-failed"}]}, auth_failure:true,
       note_post_status:"NOT_SENT_AUTH_FAILURE", reason:"", rationale_summary:
       "batch aborted due to auth failure on earlier CM".
     - STOP processing further CMs. Return the results array immediately.
After all CMs are processed (or batch is aborted), return the results array.

============================================================================
NO-FALSE-POSITIVES INVARIANT (CANONICAL — verbatim)
============================================================================
No false positives. Negative signal is canonical; positive signal is
corroborative. Recognition is corroborative; absence-of-vulnerability is
canonical.

A `fail` verdict requires CITED, CONCRETE EVIDENCE of a vulnerability.

Handoff mode — four sources are allowed:
  1. a residual vulnerable pattern matching ctx.problem, cited at file:line, OR
  2. a residual marker comment (vuln-code-snippet, VULNERABLE, TODO: fix, etc.),
     cited at file:line, OR
  3. an upstream forced-fail signal: cm.status == "Skipped" (parent
     short-circuit B0b — already handled before subagent dispatch), OR
  4. empty files_modified[] for a CODE_FIX/ML_CODE CM (parent B0b2 when
     handoff_version == "2" — already handled before subagent dispatch;
     subagent L-FF2-sub when v1, fired by YOU in B1.5 after ctx.category
     is read from the B1 fetch response).

Standalone mode — only sources (1) and (2) apply (there is no upstream
Skipped status and files_modified is always empty by design; B1.5 is
skipped entirely).

Absence of the canonical mitigation pattern is NEVER a `fail` criterion.
Failure to recognise the developer's mitigation style is NEVER a `fail`
criterion. If Q1 is `absent_high_confidence` and the marker scan is clean,
the verdict is `pass` — regardless of Q2 and Q3.

An empty or partially populated ctx.how_tos[] is NOT a degraded path. Q2 is
OPTIONAL — it runs only when ctx.how_tos[] is non-empty AND has at least one
language-applicable entry. Otherwise Q2 is skipped entirely and the matrix
collapses to Q1 + Q3 + marker scan; Q1=absent_high_confidence + clean
markers yields pass/high regardless of whether Q2 ran.

`partial` is reserved for genuine analysis ambiguity (Q1=`ambiguous`) and
context-fetch failures (404/5xx/timeout/network). It is NOT a substitute for
`pass` when you are confident no vulnerability exists.

Q2 (canonical mitigation pattern from ctx.how_tos, optional — see above) and
Q3 (semantic-equivalence alternative mitigation) are corroborative — they
enrich findings and rationale. They do NOT gate the verdict.

============================================================================
B-Sub PROCEDURE
============================================================================
1. B1 (fetch). Call MCP `project_countermeasures` with:
       op       = "get"
       project_id = {project_id}
       countermeasure_id = {cm.full_id}   # op=get identity param is countermeasure_id (NOT task_id; task_id is only for op=create/add-library-CM)
       expand     = "text,problem,tags,how_tos,phase,name"   # comma-separated STRING (the live project_countermeasures `expand` param is type=string; a JSON array risks a 400 / silently-ignored expand -> missing phase/name -> degraded category derivation)
   The response includes the CM's `phase` (+ title/text) but NO native
   `category` field. DERIVE ctx.category (one of CODE_FIX | ML_CODE | INFRA |
   ML_DOC) from `phase` + title/text (the same classification apply-security-fixes /
   generate-security-skill-files apply). When `handoff_version == "1"`, cm.category
   is NOT passed by the parent — you derive it here and use it in B1.5 below. When
   `handoff_version == "2"`, the parent already has cm.category and uses
   it for B0b2/B0b3 parent-side short-circuits; CMs that reach this
   subagent have already survived those checks, and B1.5 re-derives category
   from phase+title/text as a redundant guard.
   - HTTP 401/403 -> set result_kind = "verified"; set verdict `partial` /
     `low`; emit one finding with category `context-fetch-failed` and
     description "[AI-SAST via Code Scan Verification Validation | {model}] Could
     not fetch CM context from SDE: HTTP {401|403} | verdict=partial
     confidence=low"; set note_post_status = "NOT_SENT_AUTH_FAILURE"; set
     auth_failure: true; return immediately. Do NOT attempt B1.5, B2, or
     B5. The verdict is REQUIRED by the strict-JSON return schema even
     when auth_failure: true (parent calls record_verified(cm,
     parsed.verdict, ...) and parsed.verdict.status determines which
     Sum-check bucket the current CM contributes to).
   - HTTP 404 / 5xx / timeout / network error -> skip B1.5/B2; set
     result_kind = "verified"; set verdict `partial` / `low`; emit one
     finding with category `context-fetch-failed` and description
     "[AI-SAST via Code Scan Verification Validation | {model}] Could not fetch CM
     context from SDE: {error} | verdict=partial confidence=low"; skip B5
     (do not POST); set note_post_status = "FAILED:fetch-{code}"; return.

1.5. B1.5 (subagent short-circuit — HANDOFF MODE ONLY; runs only after
   B1 succeeds). SKIP THIS STEP ENTIRELY in standalone mode (proceed to
   B1.7). Determine ctx.category (one of CODE_FIX | ML_CODE | INFRA | ML_DOC) —
   use the handoff cm.category when present, else DERIVE it from the CM's
   `phase` + title/text in the B1 response (SDE has no native category field).

   - L-FF2-sub: if ctx.category in {CODE_FIX, ML_CODE} AND
     len(cm.files_modified) == 0:
       set result_kind        = "verified"
       set verdict.status     = "fail"
       set verdict.confidence = "high"
       emit one findings_for_handoff entry:
         { file: "(n/a)", line: 0,
           description: "[AI-SAST via Code Scan Verification Validation | {model}] code CM (CODE_FIX/ML_CODE) with no modified files | verdict=fail confidence=high",
           category: "residual-vulnerable-pattern" }
       emit one findings_for_sde entry:
         { desc: "[AI-SAST via Code Scan Verification Validation | {model}] code CM with no modified files (no mitigation present) | verdict=fail confidence=high",
           count: "1" }
       set reason            = "code CM with no modified files"
       set auth_failure      = false
       Skip B2. Proceed to B4 (fetch existing notes) + B5 (POST) to
       ensure the forced-fail verdict is visible in SDE with any upstream
       note context preserved. Set note_post_status from B5 result
       (POSTED on 2xx, FAILED:{reason} on failure). Return.

   - L-OOS-sub: if ctx.category in {INFRA, ML_DOC} AND
     len(cm.files_modified) == 0:
       set result_kind        = "out_of_scope"
       OMIT the `verdict` key entirely (out-of-scope entries do not
         carry a verdict; parent records skipped_out_of_scope).
       set reason            = "non-code CM with no modified files; static verification not applicable"
       set note_post_status  = "NOT_SENT_OUT_OF_SCOPE"
       set auth_failure      = false
       skip B2 and B5. Return.

   - Otherwise (non-empty cm.files_modified[]): proceed to B2 with
     result_kind = "verified" (set this once now; B3 will populate
     verdict).

1.7. B1.7 (file discovery — STANDALONE MODE ONLY; runs only after B1
   succeeds). SKIP THIS STEP ENTIRELY in handoff mode (proceed to B2 with
   cm.files_modified[]). In standalone mode, cm.files_modified is always []
   because there is no apply-fixes record. Discover relevant files:

   a. Extract search terms from ctx.problem + ctx.text + ctx.how_tos[]:
      vulnerability keywords, API/function names, framework patterns,
      file extensions/types relevant to the vulnerability surface.
   b. Use grep/glob (via shell tools) within {repository_path} to find
      candidate files. Exclude non-source directories: node_modules/,
      .git/, __pycache__/, dist/, build/, vendor/, .venv/.
   c. AI-rank the candidates by relevance to ctx.problem. Prioritize files
      that contain code patterns related to the vulnerability surface
      (e.g., SQL queries for SQL injection CMs, auth handlers for auth CMs).
   d. Select top N files (cap at 10 to stay within context budget).
      Store as discovered_files[].
   e. If NO relevant files found:
        set result_kind        = "verified"
        set verdict.status     = "pass"
        set verdict.confidence = "high"
        emit one findings_for_handoff entry:
          { file: "(repo-wide scan)", line: 0,
            description: "[AI-SAST via Code Scan Verification Validation | {model}] No files relevant to this CM's vulnerability surface found in repository | verdict=pass confidence=high",
            category: "vulnerability-absent" }
        emit one findings_for_sde entry:
          { desc: "[AI-SAST via Code Scan Verification Validation | {model}] No files relevant to this CM's vulnerability surface found in repository | verdict=pass confidence=high",
            count: "1" }
        set reason            = ""
        set auth_failure      = false
        Proceed to B4 (fetch existing notes) + B5 (POST the pass verdict). Skip B2/B3.
   f. Otherwise (discovered_files[] is non-empty): set result_kind =
      "verified"; proceed to B2 using discovered_files[] in place of
      cm.files_modified[].

2. B2 (analyse).
   Files to analyse:
     - Handoff mode: cm.files_modified[] (absolute paths from the handoff)
     - Standalone mode: discovered_files[] (from B1.7)
   Let analysis_files = cm.files_modified[] (handoff) or discovered_files[]
   (standalone).

   PRE-FILTER — scope-mismatch check (runs once per CM, before per-file
   analysis). Read ctx.problem and ctx.text. Determine whether the CM's
   full mitigation scope relates to analysis_files or extends to resources
   outside this repository (infrastructure, runtime config, process controls,
   third-party services, organisational policy). If the scope is external:
     - Emit one `scope-mismatch` finding:
         { file: analysis_files[0] or "(n/a)", line: 0,
           description: "[AI-SAST via Code Scan Verification Validation | {model}] CM scope ({ctx.problem summary, ≤100ch}) extends beyond repository files; partial verdict due to scope mismatch | verdict=partial confidence=low",
           category: "scope-mismatch" }
     - Set verdict = partial / low.
     - Proceed to B4 (fetch existing notes) + B5 (POST the partial verdict). Skip the per-file Q1/Q2/Q3
       analysis below.
   If the scope relates to analysis_files, proceed with the full per-file
   analysis below.

   Ground all reasoning in ctx.problem (the vulnerability)
   and ctx.text (the recommended fix). ctx.how_tos[] is OPTIONAL and
   CORROBORATIVE — many CMs have empty/partial how_tos[], and the verdict
   logic must work correctly in that case. For each file in analysis_files:
   a. read the full current contents.
   b. Detect language/framework from extension/shebang/manifest hints
      (*.py->Python; package.json->Node; pom.xml/*.java->Java; *.go->Go;
      *.cs/*.csproj->.NET; etc.).
   c. If ctx.how_tos[] is non-empty: filter to language-applicable entries.
      For each how-to filtered out, emit one `not-applicable-how-to-skipped`
      finding (audit only — no verdict impact). If ctx.how_tos[] is empty
      OR no entries are language-applicable: Q2 will be SKIPPED entirely
      (this is a normal path, not a degraded one).
   d. Q1 (PER FILE — negative-canonical, vulnerability presence). Driven by
      ctx.problem and ctx.text — NOT by ctx.how_tos[]. Determine one of
      three explicit states:
        absent_high_confidence — confident the vulnerability pattern from
          ctx.problem is NOT present (clean code path; sink not reachable;
          input parameterised/validated/escaped/typed).
        present_cited         — found a residual vulnerable pattern matching
          ctx.problem; emit `residual-vulnerable-pattern` finding cited at
          file:line.
        ambiguous             — cannot determine (obfuscated code; indirect
          data flow; partial coverage; missing dependency code). Default to
          `ambiguous` whenever in doubt — NEVER pick `absent_high_confidence`
          unless you are confident.
   e. Q2 (PER APPLICABLE HOW-TO — positive-corroborative, canonical match).
      OPTIONAL: runs ONLY when ctx.how_tos[] is non-empty AND has at least
      one language-applicable entry from step c. For each applicable how-to:
      is its canonical mitigation pattern present in this file? If yes ->
      emit `mitigation-confirmed` finding citing the how-to id. Q2 is
      corroborative only — it NEVER gates the verdict. When Q2 is skipped
      (empty or no applicable how-tos), proceed directly to Q3.
   f. Q3 (PER FILE — semantic-equivalence-corroborative). Asked when
      (a) ctx.how_tos[] is empty OR has no language-applicable entries
      (Q2 was skipped), OR (b) every applicable Q2 in this file returned
      no. Question: is some other recognisable mitigation present that
      prevents the vulnerability described in ctx.problem by the same
      security property described in ctx.text? If yes -> emit
      `alternative-mitigation-accepted` finding with a specific rationale
      (cite the observed code construct + the security property it shares
      with ctx.text's recommended fix). Q3 is corroborative only.
   g. Marker scan (PER FILE). Scan for the hardcoded marker list:
        vuln-code-snippet, VULNERABLE, INSECURE, TODO: fix,
        FIXME: security, <!-- VULNERABLE -->, # SECURITY ISSUE, // TODO: fix
      Any hit -> emit `residual-marker` finding cited at file:line.

3. B3 (verdict). Apply the verdict matrix.

   Note: Q2 is OPTIONAL — when ctx.how_tos[] is empty or has no
   language-applicable entries, Q2 is skipped and the matrix collapses to
   Q1 + Q3 + marker scan. Q1=absent_high_confidence + clean markers always
   yields pass/high regardless of whether Q2 ran (per the No-False-Positives
   Invariant; Q2 is corroborative-only).

   Per-file rows (each file produces one row):
     Q1=absent_high_confidence + Q2 any-Yes (Q2 ran) + clean markers
                                                              -> pass/high  + mitigation-confirmed
     Q1=absent_high_confidence + (Q2 all-No OR Q2 skipped) + Q3=Yes + clean
                                                              -> pass/high  + alternative-mitigation-accepted
     Q1=absent_high_confidence + (Q2 all-No OR Q2 skipped) + Q3=No  + clean
                                                              -> pass/high  + vulnerability-absent-mitigation-unrecognized
     Q1=ambiguous              + clean markers                -> partial/low + analysis-uncertain
     Q1=present_cited                                          -> fail/high  + residual-vulnerable-pattern
     marker hit (any Q1)                                       -> fail/high  + residual-marker

   Mixed-file aggregation: if files produce different rows, the verdict for
   the CM is the worst row hit, in this order:
     (1) any present_cited OR any marker hit -> fail/high (concatenate all hits)
     (2) any ambiguous -> partial/low
     (3) all absent_high_confidence -> pass/high
   Findings from ALL files are concatenated (no de-duplication).

3.5. B4 (fetch existing notes — read-then-append). Before building the
   POST payload, fetch existing **verification** notes on this CM to preserve
   prior verification detail (verification-note channel only — apply-fixes'
   addNote audit comments are a separate channel and are NOT merged here).
   Call verification with op="list",
   project_id={project_id}, task_id={cm.full_id}.
   If notes exist, extract description text and store as existing_notes[].
   On 404/5xx/timeout/network: non-fatal — set existing_notes=[], emit one
   upstream-note-fetch-failed finding (file="(n/a)", line=0,
   description="Could not fetch existing notes: {error}",
   category="upstream-note-fetch-failed"), proceed to B5.
   On 401/403: treat as auth failure (same as B1 auth path — set
   auth_failure: true and return immediately).

4. B5 (post).
   HYBRID DEFERRAL (when hybrid_defer == true — set by the parent for scan_engine="hybrid"):
     DO NOT POST. Skip the verification op=create call entirely. Set
     note_post_status = "DEFERRED_HYBRID" and return the verdict (status,
     confidence, findings_for_sde, findings_for_handoff). The PARENT posts the
     single combined note in Phase B-HYB after the ZeroPath push lands. Then
     skip the rest of this step.
   Otherwise (hybrid_defer == false — scan_engine="ai"), build payload and POST:
     behaviour       = "combine"
     confidence      = verdict.confidence
     status          = verdict.status
     findings        = aggregated by category (one {desc, count} per category;
                       count stringified; each desc MUST begin with
                       "[AI-SAST via Code Scan Verification Validation | {model}] ")
                       PLUS if existing_notes[] is non-empty from B4: append one
                       upstream-note-preserved finding per preserved note
                       (desc="[AI-SAST via Code Scan Verification Validation |
                       {model}] Prior note preserved: {upstream_note_summary,
                       <=200ch} | (audit-only, no verdict impact)", count="1")
     finding_ref     = "Agent: code-scan-verification-validation | Model: {model} | Repo: {repo_name} | CM: {cm.full_id} | Run: {iso8601_utc} | Handoff: .sde-verification-handoff.json"
     pinned          = false
     task_status_mapping = {"pass": "DONE"}
                       PLUS {"fail": "TODO"} ONLY if (task_status_mapping_opt_in
                       AND verdict.status == "fail")
   Call: verification op=create project_id={project_id} task_id={cm.full_id}
   Retry/back-off:
     HTTP 429        -> sleep 1s, retry once. Second 429 -> note_post_status
                        = "FAILED:rate-limited"; return verdict.
     HTTP 5xx        -> retry once after 1s; on second failure
                        note_post_status = "FAILED:5xx-{code}"; return verdict.
     network error   -> retry once after 1s; on second failure
                        note_post_status = "FAILED:network-{error}"; return verdict.
     HTTP 401 / 403  -> return immediately with auth_failure: true and
                        note_post_status = "NOT_SENT_AUTH_FAILURE". Parent will
                        HARD STOP the run.
     HTTP 4xx other  -> note_post_status = "FAILED:{code}-{server-body, ≤200ch}";
                        return verdict.
     2xx             -> note_post_status = "POSTED"; return verdict.

============================================================================
RETURN SCHEMA (STRICT JSON ARRAY — no extra prose, no markdown, no code fences)
============================================================================
Return a JSON ARRAY with exactly one element per CM in the input batch,
in the same order. Each element has this schema:

[
  {
    "full_id": "{cm.full_id}",
    "result_kind": "verified | out_of_scope",
    "verdict": {
      "status": "pass | partial | fail",
      "confidence": "high | low",
      "findings_for_sde": [{"desc": "...", "count": "N"}],
      "findings_for_handoff": [
        {
          "file": "...",
          "line": 0,
          "description": "...",
          "category": "residual-marker | residual-vulnerable-pattern | mitigation-confirmed | alternative-mitigation-accepted | vulnerability-absent-mitigation-unrecognized | vulnerability-absent | not-applicable-how-to-skipped | analysis-uncertain | context-fetch-failed | scope-mismatch | upstream-note-preserved | upstream-note-fetch-failed"
        }
      ]
    },
    "note_post_status": "POSTED | FAILED:{reason} | NOT_SENT_FORCED_FAIL | NOT_SENT_OUT_OF_SCOPE | NOT_SENT_AUTH_FAILURE | DEFERRED_HYBRID",
    "auth_failure": false,
    "reason": "free-text; required for result_kind=out_of_scope and for L-FF2-sub forced-fail; empty string otherwise",
    "rationale_summary": "≤300 chars; what you observed and why this verdict (or, for result_kind=out_of_scope, why the CM was OOS)"
  }
]

Field rules (STRICT):
  - The array MUST have exactly len(batch) elements. Each element's full_id
    MUST match the corresponding batch[i].full_id.
  - result_kind is a discriminator. "verified" means a verdict is present.
    "out_of_scope" means the L-OOS-sub lane fired (B1.5 with non-code CM
    AND empty cm.files_modified[]); the parent will record
    skipped_out_of_scope and not POST.
  - verdict is REQUIRED when result_kind="verified"; it MUST be omitted
    entirely when result_kind="out_of_scope".
  - note_post_status is REQUIRED in both branches. For
    result_kind="out_of_scope" the only valid value is
    NOT_SENT_OUT_OF_SCOPE. For result_kind="verified" pick one of the
    others depending on the path you took (POSTED on a 2xx — including
    L-FF2-sub which now runs B4+B5 POST,
    FAILED:{...} on a 4xx-non-auth/5xx/network,
    NOT_SENT_AUTH_FAILURE for 401/403,
    DEFERRED_HYBRID when scan_engine="hybrid" and B5 is deferred to the
    combined post in Phase B-HYB (R-ZP3)).
  - auth_failure is REQUIRED in both branches.
  - reason is REQUIRED (and non-empty) when result_kind="out_of_scope"
    or when L-FF2-sub fires. Otherwise it MAY be the empty string.
  - If auth_failure fires mid-batch, fill remaining slots with
    auth_failure:true stubs (see BATCH ITERATION PROCEDURE above).

The category `missing-fix` is NOT permitted (deprecated in beta-3.2.0).

Return STRICT JSON ARRAY only. No prose, no markdown, no code fences. The
parent will fail your output if it cannot json.loads() the entire response.
```