# Configure SD Elements Survey from Codebase - Agent Execution Contract

> **SUBAGENT / DELEGATION POLICY -- READ THIS FIRST**
>
> Subagents (the Task tool / delegation) MAY be used to reduce the parent agent's context-window strain -- under STRICT rules. Delegation is NOT banned; using the wrong model is.
>
> 1. **Same model as the parent, ALWAYS.** Set the subagent `model` explicitly to the parent's model. If you cannot, run inline.
> 2. **NEVER Composer 2.** `composer-2.5-fast` is FORBIDDEN as a subagent model in ANY environment. In Cursor the DEFAULT subagent is Composer 2, so you MUST override `model` or run inline.
> 3. **Parent owns completeness.** The parent re-derives every artifact from SDE + disk regardless of who did the work; every subagent emits `[PROGRESS]` and returns a verifiable result.
> 4. **Delegate only bounded, verifiable sub-tasks** (e.g. a batch of survey-question analysis). NEVER delegate in a way that lets questions be silently skipped.

This contract MUST be followed when executing `SKILL.md` in this directory.

## Skill Identity

**Name:** Configure SD Elements Survey from Codebase
**Purpose:** Survey-configuration phase only - MCP connection, user inputs, project create/load, survey retrieval + fill + commit from codebase analysis, and write a handoff file.
**Scope:** MCP connection, user inputs, project setup, survey configuration, survey commit, post-commit risk-policy assignment, handoff. (Security branch + AI-config archive moved to `generate-security-skill-files` per MCP-116.)

**Does NOT include:** Countermeasure retrieval/classification, library lookup, AGENTS.md/skill-file generation (use `@sde-skills/generate-security-skill-files`), or applying fixes (use `@sde-skills/apply-security-fixes`).

---

## ⚠️⚠️⚠️ AI CODE ANALYSIS REQUIRED - NO GREP/PATTERN MATCHING ⚠️⚠️⚠️

**This skill MUST use AI code analysis to DECIDE survey answers. Do NOT rely on grep or pattern matching to decide.**

| Task | ❌ FORBIDDEN (grep decides) | ✅ REQUIRED (AI Analysis) |
|------|---------------------------|---------------------------|
| Decide a survey answer | `grep "import"` → select | READ file, UNDERSTAND context |
| Identify technologies | pattern match file names | ANALYZE codebase structure |

Grep/shell may PRE-FILTER candidate files and COUNT; the survey-answer DECISION is AI-only.

---

## ⚠️ MANDATORY USER INPUTS - NEVER SKIP

**CRITICAL: You MUST ALWAYS prompt the user for ALL inputs. NEVER assume or skip.**

1. **MUST ask the user** which repository to harden - even if there's only one visible. **First confirm whether the current workspace IS the target repo** (check the workspace root for repo markers: `.git/`, `package.json`, `pom.xml`, `go.mod`, `Cargo.toml`, `requirements.txt`); if so, offer "This repository (current workspace)" as the first option with a "Browse subdirectories..." fallback (only `list_dir` the parent if the user chooses to browse). Do NOT immediately ask permission to explore the parent folder when the agent is already inside the target repo.
2. **MUST ask the user** whether this is an **initial assessment or an update** (MCP-118): initial → create a new project; update → reuse an existing project and offer a version suffix on the project name. Store `assessment_mode` + `version_label`.
3. **MUST ask the user** to select a business unit (if creating new)
4. **MUST ask the user** to select or create an application (if creating new)
5. **MUST ask the user** to confirm/enter the project name
6. **Risk policy: DEFERRED to after commit (Step 2.5, MCP-116).** Do NOT ask for or assign a risk policy during Step 1, and do NOT pass `risk_policy` when creating the project. (If the business unit has a `default_risk_policy`, SDE auto-applies it on create anyway — the create response will show a non-null `risk_policy`; the display-and-keep branch below handles that.) After the survey is committed (Step 2.5): if a policy is already set, display and keep it (`[CHECKPOINT] Risk policy: already set -> {name} (ID: {id}) (kept)`); if none is set, prompt for one and `project op=update`, then re-fetch countermeasures.

**EXCEPTION — PRE-SUPPLIED / NON-INTERACTIVE INPUTS:** If inputs are PRE-SUPPLIED (caller/parent agent, a `.sde-handoff.json`, or the environment) OR no interactive `ask_question` tool / human is available, USE those inputs and SKIP the interactive prompt, recording `[INPUT] source={caller|handoff|env}: ...`. Never silently invent inputs — if neither pre-supplied nor interactive is possible, STOP and ask the caller.

---

## Completion Criteria

This skill is NOT complete until ALL of the following are true:

- [ ] MCP connection verified successfully
- [ ] User inputs **INTERACTIVELY gathered** (repository, project mode, business unit, application, project name) - **NO ASSUMPTIONS** (except pre-supplied/non-interactive)
- [ ] SD Elements project created or loaded; `project_id` validated via `project op=get` name-match
- [ ] Risk policy assigned AFTER commit (Step 2.5, MCP-116): project created WITHOUT a policy; post-commit display-and-keep if set, select+`update` if none (or skipped if API unavailable); countermeasures re-fetched
- [ ] **Full survey structure retrieved via `project_survey` op `getDraft` (include=survey) BEFORE any codebase analysis**
- [ ] **Survey structure checkpoint output**
- [ ] Codebase analyzed using survey structure as the checklist (NOT a hardcoded list)
- [ ] **EVERY question in the survey structure systematically checked**
- [ ] **Dynamic survey coverage verification block output** (Questions skipped: 0)
- [ ] Survey questions answered with code evidence; every successfully-answered question has an accompanying comment
- [ ] Survey committed and countermeasures generated
- [ ] **`.sde-handoff.json` written** (`stage: survey-complete`, `evidence_source: codebase`) and re-read/validated
- [ ] SURVEY COMPLETION VERIFICATION block output
- [ ] Per-step PREFLIGHT emitted at each step boundary confirming the prior step's verification block was present

**You cannot claim completion until all boxes are checked and the handoff file exists.**

---

## Mandatory Outputs

### Output Timing Requirements

| Step | When to Output | What to Output |
|------|----------------|----------------|
| After Step 0 | After MCP test succeeds | `[CHECKPOINT] MCP connection successful` |
| After Step 1 | After all user inputs collected | `[CHECKPOINT] Inputs: repo=..., project=... (ID: ...), risk_policy=...` + `=== PROJECT ID VALIDATION ===` |
| After Step 2.0 | After survey structure retrieved | `[CHECKPOINT] Survey structure retrieved: {N} questions across {N} categories` |
| After Step 2.1 | After technology discovery | `[CHECKPOINT] Technologies: {list}` |
| After Step 2.3.1 | **OUTPUT** - Before survey commit | `=== SURVEY COVERAGE VERIFICATION (DYNAMIC) ===` block |
| After Step 2.4 | After survey commit | `[CHECKPOINT] Survey committed, generating countermeasures...` |
| After Step 2.5 | After risk policy assigned post-commit | `[CHECKPOINT] Risk policy assigned post-commit: {risk_policy_id or SKIPPED} | countermeasures now: {N}` |
| After Step 3 | After handoff written | `=== SURVEY COMPLETION VERIFICATION ===` + `[CHECKPOINT] Handoff file written: .sde-handoff.json (stage=survey-complete...)` |

### Survey Coverage Verification (REQUIRED -- DYNAMIC)

The categories MUST come from the actual survey structure retrieved via `getDraft include=survey`, NOT a hardcoded list. Use the exact `=== SURVEY COVERAGE VERIFICATION (DYNAMIC) ===` format in SKILL.md Step 2.3.1. Do not proceed to commit until OVERALL VERIFICATION = YES.

### Handoff Schema (Cross-Skill Contract)

This skill WRITES `.sde-handoff.json` with `stage: "survey-complete"`. The consumer is `@sde-skills/generate-security-skill-files`.

| Field | Type | Description |
|-------|------|-------------|
| `source_skill` | string | `"setup-security-plan-from-repo"` |
| `stage` | string | `"survey-complete"` |
| `evidence_source` | string | `"codebase"` |
| `assessment_mode` | string | `"initial"` or `"update"` (MCP-118) |
| `version_label` | string | version suffix applied on update (null otherwise) |
| `repository_path` | string | Path to the analyzed repo |
| `project_id` | integer | SD Elements project ID (validated via name-match) |
| `project_name` | string | SD Elements project name |
| `business_unit_id` | string/int | SD Elements BU ID |
| `application_id` | string/int | SD Elements application ID |
| `risk_policy_id` | string | Risk policy ID (null if unset/skipped) |
| `sde_host` | string | SD Elements base URL (if available) |
| `survey_committed` | boolean | Always true at handoff |
| `technology_pool` | array | Selected survey answer texts (for the next skill's library lookup) |
| `created_at` | string | ISO8601 timestamp |

The full JSON example is in SKILL.md Step 3.2. After writing, RE-READ and validate (valid JSON, `stage == "survey-complete"`, project_id matches).

---

## Survey Iteration Contract (MANDATORY)

**The survey structure from SD Elements determines what to search for - NOT a hardcoded checklist.**

### The Agent MUST:
1. **Call `project_survey` op `getDraft` (include=survey) FIRST** - Before any codebase analysis (NOT `getProjectSurvey`, which returns only selected answer IDs)
2. **Parse ALL questions** from the survey structure
3. **For EACH question:** identify the category, use the category-to-search-pattern mapping, search the codebase, select with evidence or mark checked-not-applicable
4. **Track and report on ALL questions** - Dynamic verification

### The Agent MUST NOT:

| Forbidden Action | Why Forbidden |
|------------------|---------------|
| Using a hardcoded list of features to check | Survey structure IS your checklist |
| Skipping questions that "seem irrelevant" | Survey questions define security relevance |
| Stopping after finding "enough" technologies | Every question must be checked |
| Starting codebase analysis before retrieving the survey structure | Survey determines what to search for |
| Using a static verification checklist | Verification must be dynamic from survey |

---

## API Retry / Back-off Policy

| HTTP / error | Action |
|---|---|
| 429 (rate limit) | Wait 2s, retry once; on 2nd failure: log FAILED, continue |
| 5xx / timeout / non-JSON | Wait 2s, retry once; on 2nd failure: log FAILED, continue |
| 400 (validation/deps) | Inspect body; fix (e.g. select parent answer first); retry once |
| 404 | Fix the ID and retry once; else skip with warning |
| 401 / 403 | No retry; HARD STOP (credentials/permissions) |

**Survey answer select (`mutateByText`/`updateByIds`):** On `failed_answers` due to dependencies, select the parent answer then retry the child once. An answer may appear in BOTH the added/selected AND failed lists of the same response (dependency not yet resolved) -- it was NOT actually applied; the ONLY source of truth is `getDraft`.

**Survey comment and `commitDraft`:** Retry once on transient error; 401/403 hard-stop.

---

## Mandatory Gate Registry

These gates MUST be emitted during execution:

| ID | Step | Pattern that MUST appear in output |
|----|------|------------------------------------|
| G1 | 2.0 | `[CHECKPOINT] Survey structure retrieved:` |
| G2 | 2.3.1 | `=== SURVEY COVERAGE VERIFICATION (DYNAMIC) ===` (Questions skipped: 0) |
| G3 | 2.4 | `[CHECKPOINT] Survey committed, generating countermeasures...` |
| G3.5 | 2.5 | `[CHECKPOINT] Risk policy assigned post-commit:` |
| G4 | 3 | `=== SURVEY COMPLETION VERIFICATION ===` |
| G5 | 3 | `[CHECKPOINT] Handoff file written: .sde-handoff.json (stage=survey-complete` |

**Skip-to-handoff carve-out (update mode, Q3b step 6):** when the run reuses an ALREADY-COMPLETE, committed existing survey, the Step 2 FILL is bypassed, so G1/G2/G3 are satisfied by the reused committed survey (the SURVEY COMPLETION VERIFICATION records the reused-existing-survey path) rather than by fresh Step 2 emissions — G3.5 (risk policy, Step 2.5), G4, and G5 still fire normally. This is the ONLY exemption from emitting G1/G2/G3 fresh.

---

## Forbidden Behaviors

| Action | Why Forbidden |
|--------|---------------|
| **Executing any step from memory without reloading its section from the pinned `.sde-security/contract/setup-security-plan-from-repo/SKILL.md`** | The contract is pinned at CONTRACT BOOTSTRAP; every preflight must reload the section and quote a verbatim sentinel |
| **Using ONLY grep to DECIDE survey answers** | AI analysis required to understand code context (grep may pre-filter only) |
| Skipping MCP verification | Connection must be confirmed |
| **Assuming repository/project without asking user** | User MUST explicitly select (except pre-supplied/non-interactive) |
| **Asking for a risk policy when one is already set** | If a policy is set, display it and keep it; only prompt when none is set |
| **Using a hardcoded feature checklist** | Survey structure from `getDraft include=survey` IS your checklist |
| **Starting codebase analysis before retrieving the survey structure** | Survey structure determines what to search for |
| **Skipping survey questions** | Every question in the survey must be evaluated |
| **Selecting a survey answer without an accompanying comment on the same question** | Every successfully selected answer MUST be an atomic pair (gate: comments per question >= questions with >=1 selected answer; gated/invalid answers recorded as `skipped-gated`) |
| **Writing a project_id not confirmed via `project op=get` name-match** | Only the validated project_id may be used downstream and in the handoff |
| **Proceeding to commit without the dynamic coverage verification** | Must output the verification block from the actual survey |
| **Loading countermeasures, classifying, doing library lookup, or generating AGENTS.md / skill files** | OUT OF SCOPE -- that is `@sde-skills/generate-security-skill-files` |
| **Ending the run before `.sde-handoff.json` is written and the SURVEY COMPLETION VERIFICATION block is output** | Every run MUST produce the handoff and the completion block |
| **Restarting from scratch (or silently dropping the remainder) after a context-limit interruption** | Emit the CONTEXT CHECKPOINT, then on resume RE-DERIVE progress from SDE + disk and continue only the incomplete portion |
| **Marking the survey-fill step as "completed" in TodoWrite before its coverage gate passes** | Loop steps stay "in_progress" until the verification gate shows ALL = YES |

---

## Failure Recovery

### If MCP Connection Fails
1. Check if SD Elements MCP server is configured
2. Verify credentials in environment variables
3. Provide installation guide if server not found
4. **Do not proceed** until connection succeeds

### If Survey Commit Fails
1. Check for validation errors in survey answers
2. Verify all required questions are answered
3. Try committing again after fixing issues
4. **Output:** `[ERROR] Survey commit failed: {reason}. Retrying...`

### If Zero Countermeasures Generated
1. Survey answers may not match codebase (e.g., selected "Java" but codebase is Python)
2. Review and correct survey answers, recommit
3. (The next skill surfaces the count; if 0, return here.)

### If Project Creation Fails
1. Check for duplicate project name; suggest alternative with timestamp suffix
2. Verify business unit and application IDs are valid

---

## Contract Acceptance

By reading this file, you agree to:

1. Verify MCP connection before proceeding
2. **⚠️ MANDATORY STEP EXECUTION ORDER -- ALL sub-steps must execute in this exact sequence:**
   `0 → 0.1 → 0.2 → 0.3 → 1 → 2 → 2.0 → 2.1 → 2.1.1 → 2.2 → 2.3 → 2.3.1 → 2.4 → 2.5 (assign risk policy after commit) → 3 (write .sde-handoff.json + completion block)` (security branch + AI-config archive moved to generate-security-skill-files per MCP-116)
   NO step or sub-step may be skipped or reordered.
3. **ALWAYS prompt the user for ALL inputs** - repository, project mode, business unit, application, project name - **NEVER assume or skip** (except pre-supplied/non-interactive)
4. **Risk policy is assigned AFTER commit (Step 2.5, MCP-116)** — never at project creation; display-and-keep if set, select+`update` if none, then re-fetch countermeasures
5. **⚠️ Call `project_survey` op `getDraft` (include=survey) FIRST** - before any codebase analysis - the survey structure IS your checklist
6. **⚠️ Iterate through EVERY question in the survey structure** - NOT a hardcoded list
7. Fill survey with code evidence only; every successfully-selected answer gets a comment
8. **⚠️ Output DYNAMIC coverage verification block** - categories from actual survey - STOP if NO
9. Commit the survey
10. **Write `.sde-handoff.json` (`stage: survey-complete`, `evidence_source: codebase`) and re-read/validate it**
11. Output the SURVEY COMPLETION VERIFICATION block as the final output
12. Not claim completion until ALL criteria met and the handoff file exists
13. Use EXACT output formats specified (no variations)
14. **Subagents MAY be used to reduce context strain, but ONLY with `model` set explicitly to the parent's model -- NEVER Composer 2; if you cannot set the model, run inline**
15. Do NOT load countermeasures or generate skill files -- that is `@sde-skills/generate-security-skill-files`

**There are NO exceptions to these rules.**
