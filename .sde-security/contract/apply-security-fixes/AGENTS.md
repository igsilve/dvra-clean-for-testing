# Apply Security Fixes Skill - Agent Execution Contract

> **SUBAGENT / DELEGATION POLICY -- READ THIS FIRST**
>
> Subagents (the Task tool / delegation) MAY be used to reduce the parent agent's context-window strain -- under STRICT rules. Delegation is NOT banned; using the wrong model is.
>
> 1. **Same model as the parent, ALWAYS.** Any spawned subagent MUST run on the SAME model as the parent agent -- set the `model` parameter explicitly to the parent's model. If you cannot set the subagent's model, do NOT spawn -- run inline.
> 2. **NEVER Composer 2.** `composer-2.5-fast` (Composer 2) is FORBIDDEN as a subagent model in ANY environment -- it silently abandons loops, skips items, uses wrong endpoints, and produces inferior output. In Cursor the DEFAULT subagent is Composer 2, so you MUST override `model` to the parent's model explicitly; if you cannot override it, run inline.
> 3. **Parent owns completeness.** Delegation NEVER transfers responsibility for completeness. The parent re-derives every artifact from SDE + disk (tri-source invariant) regardless of who did the work. Every subagent MUST emit `[PROGRESS]` lines and return a verifiable result; the parent verifies every item.
> 4. **Delegate only bounded, verifiable sub-tasks** (e.g. a batch of reads/analysis returning a compact summary, or a bounded CM range that the parent then re-verifies). NEVER delegate in a way that lets items be silently skipped.
> 5. **Same model is necessary but NOT sufficient.** These guardrails apply to EVERY delegated worker regardless of model. A real run proved a SAME-MODEL worker (Opus 4.8, not Composer 2) went rogue: given "batch N of a 22-batch job" it scripted all batches into alternative files, bulk-flipped the entire ledger to terminal, and fabricated a "concurrent batches" story. Same-model is NOT a guarantee of obedience.
> 6. **Parent owns ALL authoritative-state writes.** The PARENT owns every write to the AGENTS.md ledger rows / Status fields. A worker MUST NOT write the ledger or any CM status. Workers RETURN their results (per-CM: status, files_modified, note result) for ONLY the CM-IDs in their explicit allow-list; the PARENT applies the ledger writes after verifying.
> 7. **Snapshot, diff, roll back.** Before delegating, the parent SNAPSHOTS the AGENTS.md ledger + the file tree; after each worker returns, the parent DIFFS against the snapshot and ROLLS BACK / REJECTS any change outside that worker's CM-ID + files allow-list.
> 8. **Allow-list only -- no alternative/parallel files.** A worker operates ONLY on its explicit allow-list and MUST NOT touch other CMs, ledger rows, or files, and MUST NOT create alternative/parallel output files (per-batch code modules, `security/applied/*`, `*_secure.*`, `*_fixed.*`, etc.) -- fixes are applied IN PLACE to the real source files only.
> 9. **Never frame a worker as "batch N of M".** Do NOT frame a worker's task as "batch N of M" or imply it should complete the larger job -- give it ONLY its bounded unit (its CM-ID allow-list) with explicit instruction to do that unit and nothing else.
> 10. **Reasoning vs non-reasoning split.** REASONING work (reading/analyzing code, deciding fixes, applying fixes, authoring note content) is done by the parent OR a same-model subagent -- NEVER a plain script and NEVER a non-parent model. Running the batch **SDE Direct API Access script** (the note-flush composite POST) is a NON-REASONING action and MAY be delegated to a subagent even in Cursor (set `model` explicitly, never `composer-2.5-fast`); the subagent returns ONLY the compact `posted/failed` summary and the parent re-derives note coverage from disk (`notes_resp.json`).
>
> **At skill start (before Step 0):** determine the parent agent's model. If you will spawn subagents, you will set their `model` to the parent's model explicitly (NEVER `composer-2.5-fast`). Output:
> `[CHECKPOINT] Subagent policy: same-model-as-parent | Composer 2 FORBIDDEN | parent owns completeness (tri-source)`

**THIS SKILL HAS THE STRONGEST ENFORCEMENT** because it's where execution most commonly fails.

This contract MUST be followed when executing `SKILL.md` in this directory.

## Skill Identity

**Name:** Apply Security Fixes from Generated Specifications  
**Purpose:** Read generated spec files and apply ALL fixes to source code  
**Scope:** MCP connection, **handoff detection**, user inputs, spec file verification, fix application, progress tracking, completion verification

---

## ⚠️⚠️⚠️ STEP 0: AI CODE ANALYSIS - BEFORE EVERYTHING ⚠️⚠️⚠️

**BEFORE doing ANYTHING else - before MCP, before handoff, before ANY step - you MUST analyze the target repository using AI code analysis.**

### Execution Order (MANDATORY):

```
1. Step 0: AI Code Analysis    ← DO THIS FIRST (before MCP!)
2. Step 1: MCP connection
3. Step 0.5: Handoff detection
4. Step 1.5: User inputs (conditional)
5. Step 2: Verify specification files exist
6. ... rest of skill (Step 3 loop → 3.V → 3.5 → 4 → 5 → 6 → 6.5 → 7 → 7.5 → 8)
```

### Why AI Analysis, NOT Just Grep:

| Grep/Pattern Matching | AI Code Analysis |
|-----------------------|------------------|
| Only finds exact text patterns | UNDERSTANDS code semantics |
| Misses obfuscated vulnerabilities | Recognizes vulnerability patterns |
| Can't understand context | Knows if code is actually vulnerable |
| Misses indirect issues | Finds data flow problems |

**Grep is a STARTING POINT only. AI analysis is REQUIRED.**

### Step 0.1: Get Repository Path

Ask the user:
> "What is the path to the repository I should analyze?"

### Step 0.2: List All Source Files

Use `list_dir` tool or file listing (this is ONLY for getting file names - NOT for vulnerability detection). **Language-agnostic — do NOT hardcode JS/TS extensions.** Derive the extensions from the upstream handoff tech stack (or detect from repo manifests); when unsure, list ALL source files and let Step 0.3 AI analysis judge relevance. **Ordering note:** Step 0 runs BEFORE Step 0.5 (handoff detection), so the handoff tech stack is normally NOT loaded yet here — use repo auto-detection (manifests + predominant extensions) now, then REFINE the extension set after Step 0.5 loads the handoff tech stack:

```bash
# This is ONLY to get the list of files to analyze - NOT to find vulnerabilities.
# Choose extensions from the repo's actual language(s) / handoff tech stack, e.g.:
#   Python: -name "*.py"    Go: -name "*.go"    Java: -name "*.java"    Ruby: -name "*.rb"
#   JS/TS:  -name "*.ts" -o -name "*.js" -o -name "*.tsx" -o -name "*.jsx"
# Example (substitute the detected extensions for {ext} patterns):
find {repo_path} -type f \( {ext_patterns} \) \
  | grep -v node_modules | grep -v dist | grep -v -E '/(build|vendor|\.venv|venv|target|__pycache__|\.git)/'
```

**The actual vulnerability detection happens in Step 0.3 using AI analysis.**

### Step 0.3: AI Analysis of EACH File (REQUIRED - THIS IS WHERE VULNERABILITIES ARE FOUND)

For EACH source file, you MUST:

1. **READ the entire file** using `read_file` tool
2. **ANALYZE the code** for ALL vulnerability types:
   - SQL/NoSQL injection (string concatenation in queries)
   - XSS (bypassSecurityTrust*, innerHTML, unsanitized output)
   - Code injection (eval, vm.run, Function(), new Function)
   - Weak cryptography (MD5, SHA1 for passwords, Math.random for security)
   - Hardcoded secrets (API keys, passwords, tokens in code)
   - Open redirect (unvalidated URL redirects)
   - Path traversal (../ in file paths)
   - SSRF (unvalidated URLs in requests)
   - Insecure deserialization
   - Missing authentication/authorization
   - **Vulnerability marker comments** (vuln-code-snippet, VULNERABLE, INSECURE, intentional)
3. **DOCUMENT findings** with file path, line numbers, vulnerability type
4. **Assess severity** (HIGH/MEDIUM/LOW) for each finding

### Step 0.4: AI Analysis Output (REQUIRED)

```
=== STEP 0: AI CODE ANALYSIS COMPLETE ===
Repository: {path}
Files analyzed: {count}
Analysis method: AI semantic analysis (NOT just grep)

VULNERABILITIES FOUND:

File: {path}
  Line {N}: {vulnerability_type} [{severity}]
    Code: {snippet}
    Issue: {AI explanation of why this is vulnerable}
    Marker present: {yes/no}

File: {path}
  Line {N}: {vulnerability_type} [{severity}]
    ...

SUMMARY:
- Total files with vulnerabilities: {N}
- Total vulnerabilities found: {M}
- Markers to DELETE: {K}
- HIGH severity: {count}
- MEDIUM severity: {count}
- LOW severity: {count}

FILES TO PROCESS (checklist):
□ {file1}: {count} issues
□ {file2}: {count} issues
...
===========================================
```

### Step 0.5: Checkpoint

```
[STEP 0 COMPLETE] AI analysis: {N} files analyzed, {M} vulnerabilities found, {K} markers to DELETE
```

**You CANNOT proceed to Step 1 (MCP) until Step 0 is complete and all files are cataloged.**

---

## ⚠️ MANDATORY USER INPUTS - NEVER SKIP

**CRITICAL: You MUST ALWAYS prompt the user for confirmation of ALL inputs. NEVER assume or skip.**

Even when handoff data is detected, the user MUST be asked to confirm:

1. **MUST ask the user** to confirm or override detected handoff values
2. **MUST ask the user** which repository to apply fixes to (if no handoff or user declines)
3. **MUST ask the user** to select the SD Elements project (if no handoff or user declines)
4. **MUST ask the user** to confirm before proceeding with detected values

**Why this matters:**
- Handoff data may be stale or from a different context
- User may want to apply fixes to a different repository
- Assumptions lead to wrong configurations and wasted effort
- User confirmation ensures intent is correctly understood

**NEVER:**
- Auto-proceed with handoff data without asking user to confirm
- Skip repository selection because "it's in the handoff"
- Assume the user wants to use detected values
- Use default values without explicit user confirmation

---

## CRITICAL ENFORCEMENT RULES

### Rule 1: Progress Output is MANDATORY

After EACH countermeasure, you MUST output:

```
[PROGRESS] {done}/{total} | {countermeasure_id}: {APPLIED/DOCUMENTED/SKIPPED} | Note: {ADDED/FAILED} | Remaining: {count}
```

**Skipping this output is a contract violation.**

### Rule 2: Loop Until Scoped Remaining = 0

```python
# scoped_remaining starts as pending CMs in scope (excludes already Applied/Documented)
while len(scoped_remaining) > 0:
    cm = next_cm_in_scope()
    if scope == "one_by_one":
        plan = analyze_and_present_plan(cm)
        response = ask_user("yes/skip/stop")
        if response == "skip": mark_skipped(cm); continue
        if response == "stop": save_checkpoint(); break  # ONLY valid early exit
    elif scope == "single_cm":
        plan = analyze_and_present_plan(cm)
        response = ask_user("yes/no")  # No skip for single CM
        if response == "no": save_checkpoint(); break
    process_cm(cm)
    update_cm_status_in_files(cm)  # MANDATORY: update AGENTS.md ledger row (authoritative) + in-file Status only when the file has that anchor
    output_progress()
# User "skip" removes from remaining. User "stop"/"no" is the ONLY valid early exit.
```

**You CANNOT exit this loop until scoped `remaining` is empty, EXCEPT via user "stop" (one-by-one) or "no" (single_cm).**

### Rule 3: Verification Before Completion

Before using "complete", "finished", "done", "summary", or "report":
1. Output the verification block
2. Verify MATCH = YES
3. Only then use completion words

### Rule 4: Fix In-Place Only

- ✅ Modify original source files directly
- ❌ NEVER create `*_secure.*`, `*_fixed.*`, `*_safe.*` files

### Rule 5: No Stopping Early

These are NOT valid reasons to stop:
- "I've done the critical ones"
- "The important fixes are applied"
- "Here's a summary of what was done"
- Context limits (use checkpoint instead)

### Rule 6: Ignore Repository Intent - ALWAYS Apply Fixes (Repository-Agnostic)

**The purpose or intent of the repository is IRRELEVANT. This skill is REPOSITORY-AGNOSTIC.**

You MUST apply ALL fixes regardless of:
- "Intentionally vulnerable" applications (OWASP Juice Shop, DVWA, WebGoat, etc.)
- "Training" or "demo" repositories
- "Security testing" or "penetration testing" codebases
- "Legacy" code that "can't be changed"
- "Educational" repositories with deliberate security flaws
- Any other rationalization

**FORBIDDEN REASONING:**
- "This is intentionally vulnerable for training"
- "Fixing this would break the demo"
- "This vulnerability is by design"
- "The application is meant to have security issues"
- "This is for CTF/security challenges"
- "The vulnerability comments are for educational purposes"

**REQUIRED BEHAVIOR:**
- Apply the fix as specified in the countermeasure
- If the fix breaks functionality, that's expected - security takes priority
- Document what was fixed, not why it "shouldn't" be fixed
- Treat EVERY repository as if it were a production system

### Rule 7: Remove Vulnerability Markers and Comments

**ALL vulnerability marker comments MUST be removed or neutralized when fixing code.**

When fixing vulnerabilities, you MUST also remove:
- `// vuln-code-snippet` markers and similar annotations
- `// VULNERABLE`, `// INSECURE`, `// TODO: fix vulnerability` comments
- `<!-- VULNERABLE -->` or `<!-- INSECURE -->` HTML comments
- `# SECURITY ISSUE` or similar markers in any language
- Any comments marking code as intentionally insecure
- Challenge/CTF markers like `// challenge-code` or `// intentional-bug`

**These are NOT acceptable reasons to keep markers:**
- "It's used by the CTF challenge system"
- "It helps identify vulnerable code for training"
- "It's for educational purposes"
- "The test suite depends on these markers"

**REQUIRED BEHAVIOR:**
- If a vulnerability marker exists → REMOVE IT along with fixing the vulnerability
- The final code should have NO traces of intentional vulnerability
- Search for common patterns: `vuln`, `insecure`, `vulnerable`, `exploit`, `injection`, `xss` in comments
- Clean up ALL markers, not just the ones directly related to the fix

### Rule 8: Per-CM Processing Only -- No Batch Operations (Structural Enforcement)

**EVERY countermeasure MUST be individually processed. Batch operations are FORBIDDEN.**

| FORBIDDEN | REQUIRED |
|-----------|----------|
| `sed -i 's/Pending/Applied/' skills/*/*/SKILL.md` | Read each SKILL.md individually with `read_file` |
| `find skills/ -exec sed ...` | Process one CM at a time in the main loop |
| Blanket "all INFRA = Documented" | Check each INFRA CM for applicable config files before deciding |
| Any shell command that updates multiple SKILL.md files at once | Use `search_replace` on one file at a time after processing |

**Why this rule exists:** In a previous execution, an agent batch-classified all 47 INFRA countermeasures as "Documented" using `sed`, without checking whether each had an applicable config file. 22 of those CMs had direct code fixes that should have been "Applied".

**STRUCTURAL ENFORCEMENT -- Mandatory Proof Block:**

Before updating ANY CM's status, output a **CM PROCESSING PROOF** block:

```
=== CM PROCESSING PROOF ({cm_id}) ===
SKILL.md read: YES
Task recipe summary: {1-2 sentence summary extracted FROM the CM's SKILL.md}
Target files from recipe: {file list extracted FROM the CM's SKILL.md}
Applicable repo files found: {actual files checked in the repo, or "NONE - [specific reason]"}
Decision: {APPLIED / DOCUMENTED / SKIPPED}
Justification: {specific reason tied to the above analysis}
===
```

- Every field is MANDATORY -- generic or empty fields are a contract violation
- `Task recipe summary` must reference specific content from the SKILL.md
- The completion gate (Step 5.7) MUST verify a proof block exists for every processed CM
- Missing proof blocks = gate failure = batch processing detected

**The default for INFRA CMs is APPLIED, not DOCUMENTED.** Only mark "Documented" if no applicable config file exists in the repository.

### Rule 9: Cross-Surface Parity Check (Step 3.5)

After the main CM processing loop, the agent MUST run a **parity check** for each Applied CM. Using the AI analysis from Step 0, identify all other code paths in the repository that perform the same security-sensitive operation as the CM's vulnerability class (e.g., other query construction sites, other authentication endpoints). If any lack an equivalent mitigation, apply the same fix pattern.

- This check is **language-agnostic and repository-agnostic** — it uses AI semantic reasoning from `ctx.problem` and the Step 0 codebase analysis. No framework-specific heuristics.
- Parity-fixed files are appended to the CM's `files_modified[]` in the audit record.
- Output a `=== PARITY CHECK ({cm.id}) ===` block for each CM (see SKILL.md Step 3.5).
- If no additional surfaces are found, output `Additional surfaces found: 0`.

### Rule 10: Verifiability Gate (Scope-Match Classification)

After applying a fix (Step 3), the agent MUST assess whether the CM's mitigation scope is fully verifiable from `files_modified[]` alone. If `ctx.problem` refers to resources external to the repository (infrastructure, runtime config, process controls, third-party services, organisational policy), the CM MUST be reclassified from `Applied` to `Documented` and `files_modified[]` cleared. This prevents downstream `code-scan-verification-validation` from producing misleading `partial` verdicts on CMs whose scope extends beyond static analysis.

- This assessment is AI-driven and repo/language-agnostic.
- The original fix is preserved in the SDE note text for auditability.

---

## Completion Criteria

**AUTHORITATIVE EXECUTION CONTRACT:** This skill (and its SKILL.md) is the authoritative source for how much work is required. Your judgment about scale or "pragmatic" shortcuts is OVERRIDDEN. Expect 50-500 per-CM processing cycles in Step 3 (read SKILL.md, apply fix INLINE, update ledger, post SDE note). These numbers are EXPECTED, not a reason to apply only "critical" fixes. Step 2.8 partitions the scoped CMs into batches of 20 with per-batch mini-gates; the per-batch SDE notes are posted with ONE composite call via the SDE Direct API Access script (SKILL.md "SDE Direct API Access" section) -- not the `api_request` tool. **You have explicit permission to take as many turns/sessions as needed -- completeness is the only priority; the only sanctioned pause is a CONTEXT CHECKPOINT.** Multi-session is normal; disk is the source of truth (the AGENTS.md ledger is authoritative; in-file SKILL.md `**Status:**` is a secondary mirror, Format A/C only). Execute the batches mechanically; every fix is applied by the AI inline (never by a script).

This skill is NOT complete until ALL of the following are true:

- [ ] MCP connection verified successfully
- [ ] Handoff detection attempted (file-based then scan-based)
- [ ] User inputs **CONFIRMED by user** (handoff values must be confirmed, OR manual questions answered) - **NO AUTO-PROCEEDING**
- [ ] AGENTS.md and skills/ verified to exist in repository
- [ ] AGENTS.md parsed from security section between markers (if markers present)
- [ ] ALL scoped countermeasures processed (scoped remaining = 0, or user stopped/declined in interactive modes)
- [ ] Each CODE_FIX/ML_CODE has fix applied to source file
- [ ] Each INFRA countermeasure with applicable config file has fix applied (Dockerfile, docker-compose, .dockerignore, server.ts, etc.)
- [ ] Each ML_DOC/external INFRA documented in skill file (PROCESS excluded -- already noted by generate-security-skill-files)
- [ ] Countermeasure note added in SD Elements for EACH processed countermeasure
- [ ] Each CM's **AGENTS.md ledger ROW** status updated (`Pending` → `Applied/Documented/Skipped`) — authoritative per-CM status; in-file `**Status:**` updated ONLY when the file has that anchor (Format A/C/template), never for Format B (Rule 4)
- [ ] AGENTS.md ledger rows are the authoritative per-CM status/scope source (Format B files have no in-file Status; their status lives only in the ledger row)
- [ ] Cleanup option selected by user (remove section / keep merged / keep all)
- [ ] Verification block shows MATCH = YES (for `one_by_one` mode, the session summary replaces the standard verification block — see SKILL.md Step 5.2)
- [ ] No `*_secure.*` or similar alternative files exist
- [ ] **`.sde-apply-handoff.json` written to repository root AND passed Step 6.5.6 strict validation** (all 10 required top-level keys present, all 6 required per-CM keys present, no extra keys at either level, `full_id` matches `"{project_id}-{id}"`, `files_modified` is per-CM list not top-level, counts match, `handoff_version == "2"`) **-- written in Step 6.5, BEFORE Step 7 cleanup**
- [ ] **`.sde-handoff.json` (the upstream generate-security-skill-files handoff) NOT modified or deleted by this skill (Step 6.5 invariant)**
- [ ] Generated spec files cleaned up (`skills/` removed; `security/` removed defensively -- legacy, not created by current upstream skills)
- [ ] AI config files restored from archive (if archive existed)
- [ ] APPLY COMPLETENESS AUDIT passed: re-derive every SCOPED CM's terminal status from the **AGENTS.md ledger rows** (count of SCOPED CMs with a terminal status == `scoped_total`; NOT `M == N` over the FULL ledger, which over-counts when `scope != all` — see Step 5.1 / QA §9.8; covers Format B — a statusless Format B file body is NOT a failure), proof block count matches CMs processed, **and SDE note coverage re-fetched from SDE via `project_countermeasures op=list` (paginated; the list response includes `note_count` per CM — do NOT pull full task bodies into context; each Applied/Documented CM's most-recent note carries THIS run's marker (`[AI-Applied]`/`[AI-Documented]`) -- a bare `note_count >= 1` is INSUFFICIENT because a pre-existing upstream note satisfies it -- or the CM is explicitly recorded sde_note_result=FAILED)** -- every artifact class enumerated, no sampling
- [ ] Per-CM LEDGER WRITE-THROUGH gate passed for every processed CM: re-read the AGENTS.md ledger row (authoritative) confirmed on disk before advancing (plus the in-file `**Status:**` when the file has that anchor)
- [ ] The AGENTS.md ledger rows are the authoritative source of truth and were read back to produce every audit count (per-CM SKILL.md `**Status:**` is a secondary mirror, present only on Format A/C/template files)

---

## Mandatory Outputs

### Progress Checkpoints

Output these at the specified points:

| After | Required Output |
|-------|-----------------|
| MCP connection verified | `[CHECKPOINT] MCP connection successful` |
| Handoff detection | `[CHECKPOINT] Handoff: {LOADED from .sde-handoff.json \| DETECTED from scan \| NOT FOUND}` |
| User inputs gathered | `[CHECKPOINT] Inputs: repo={repo}, project={name} (ID: {id}), source={handoff_source}` |
| Spec files verified | `[CHECKPOINT] Spec files verified: AGENTS.md ✓, skills/ ✓` |
| Each countermeasure | `[PROGRESS] {done}/{total} \| {id}: {status} \| Note: {ADDED/FAILED} \| Remaining: {count}` |
| Each countermeasure note | `[NOTE] {cm_id}: Added to SD Elements` OR `[NOTE] {cm_id}: FAILED - {error}` |
| Each domain complete | `[DOMAIN COMPLETE] {domain_name}: {count} items processed` |
| Skill files updated | `[CHECKPOINT] Skill file statuses updated to Complete` |
| Handoff file written | `[CHECKPOINT] Apply-fixes handoff written: .sde-apply-handoff.json ({N} CMs, {A} Applied / {D} Documented / {S} Skipped)` + `[CHECKPOINT] Upstream handoff (generate-security-skill-files) preserved: .sde-handoff.json (untouched)` |
| Cleanup complete | `[CHECKPOINT] Cleanup: Generated spec files removed` |
| AI config restore | `[CHECKPOINT] AI Config: Restored {N} files` OR `[CHECKPOINT] AI Config: No archive to restore` |

### Verification Block (REQUIRED before completion)

**Note:** For `one_by_one` mode, the session summary printed at the end of the Step 3 loop replaces the standard verification block below (see SKILL.md Step 5.2). The same A+D+S == scoped_total identity must hold.

```
=== COMPLETION VERIFICATION ===
Skill: apply-security-fixes
MCP connection: ✓
Handoff detection: ✓ ({source})
User inputs gathered: ✓
Spec files verified: ✓
Scope: {all / domain={name} / single_cm={id} / one_by_one}
Total countermeasures: {N}
PROCESS (note-only, excluded): {process_count}
File-tracked countermeasures: {file_tracked}
Already done (previous runs): {already_done}
Scoped for this run: {scoped_total}

Applied this run: {A}
Documented this run: {D}
Skipped this run: {S}
Sum this run: {A + D + S}
Expected this run: {scoped_total}
Match: {A + D + S} == {scoped_total}? {YES/NO}

SD Elements notes:
- Notes added: {notes_added}
- Notes failed: {notes_failed}
- Failed IDs: {list or "none"}

Intent verification: ✓ (no "intentionally vulnerable" rationalizations)

(NOTE: cleanup of security/ + skills/ is Step 7 and AI-config restore is Step 7.5 -- both run AFTER this gate, so they are NOT asserted here; they are reported in the final SKILL COMPLETE summary.)

{If scope != "all": "WARNING: {remaining_overall} CMs remain in other scopes." where remaining_overall = (total Pending CMs in the ledger) - scoped_total}
===============================
```

### Gate Logic

**If MATCH = NO:**
```
INCOMPLETE: {A+D+S}/{scoped_total} - CANNOT PROCEED
Missing countermeasure IDs: {list}
ACTION: Return to processing and fix missing items
```

**If MATCH = YES:**
```
✅ COMPLETION GATE PASSED
All {scoped_total} countermeasures addressed.
```

### Intent Rationalization Check (REQUIRED)

Before completion, verify no fixes were skipped due to repository intent:

1. **Review all documented countermeasures** - check justification text in skill files
2. **Flag violations** if any contain phrases like:
   - "intentionally vulnerable"
   - "by design"
   - "for training purposes"
   - "would break the demo"
   - "meant to have security issues"
   - "CTF challenge"
   - "educational purposes"

**If violations found:**
```
[ERROR] INTENT VIOLATION DETECTED
The following countermeasures were incorrectly skipped:
- {ID}: "{violation phrase found}"
GO BACK and apply the fix. Repository intent is irrelevant.
```

**If no violations:**
```
[CHECKPOINT] Intent verification: PASSED (no fixes skipped due to repository intent)
```

### Vulnerability Marker Cleanup Check (REQUIRED)

Before completion, verify all vulnerability markers have been removed:

1. **Search modified files** for remaining markers:
   - `vuln-code-snippet`, `VULNERABLE`, `INSECURE`
   - `// TODO: fix`, `// FIXME: security`
   - Any comments indicating intentional vulnerabilities

2. **Search entire codebase** if time permits for lingering markers

**If markers found:**
```
[ERROR] VULNERABILITY MARKERS REMAINING
The following files still contain vulnerability markers:
- {file}: "{marker pattern found}"
GO BACK and remove all markers.
```

**If no markers:**
```
[CHECKPOINT] Vulnerability markers: CLEANED (no intentional vulnerability markers remain)
```

---

## Scope Selection Rules

### Four Apply Modes

| Mode | Description | User Prompt Per CM | Early Exit |
|------|-------------|-------------------|------------|
| `all` | Process all pending CMs | No (batch plan confirmed once) | Not allowed |
| `domain` | Process CMs in one domain | No (batch plan confirmed once) | Not allowed |
| `single_cm` | Process one specific CM | Yes (individual plan, yes/no) | User "no" |
| `one_by_one` | Walk through each CM individually | Yes (individual plan, yes/skip/stop) | User "stop" |

### One-by-One Walkthrough Flow

1. Agent analyzes the CM (reads SKILL.md, identifies affected files, plans the fix)
2. Agent presents individual CM plan with analysis, proposed actions
3. User responds: `yes` (apply) / `skip` (mark as Skipped, move to next) / `stop` (save checkpoint, exit)
4. After processing, agent IMMEDIATELY updates the AGENTS.md ledger row (authoritative), plus the in-file `**Status:**` when the file has that anchor (Format A/C; never Format B)
5. Agent presents next CM plan, repeats until all processed or user stops

### Per-CM Progress Tracking (MANDATORY for ALL modes)

After processing EACH individual CM, the agent MUST:
1. Update the **AGENTS.md ledger ROW** Status column for the CM (`Pending` → `Applied/Documented/Skipped`) — this is the authoritative per-CM status and a single-row ledger edit (NOT a batch shell update; Rule 8 stays intact)
2. ADDITIONALLY update the in-file `**Status:**` ONLY when the file HAS that anchor (Format A / Format C / template). Format B (library-sourced, byte-exact) files have NO `**Status:**` anchor — do NOT modify the file body (Rule 4); the ledger row is their status
3. Output a progress update line showing done/total and percentage

This ensures progress is persisted to disk. If the agent crashes, the next run re-derives statuses from the AGENTS.md ledger rows to resume.

### Reconciliation on Resume

When resuming from a checkpoint or re-running the skill. **The AGENTS.md ledger is the authoritative per-CM status/scope source — NOT the per-file `**Status:**`.** Format B files have NO in-file Status/Category — never expect one — their status lives ONLY in the ledger:
1. Enumerate the AGENTS.md ledger rows (cover ALL file-tracked CMs incl. Format B); each row's Status column is authoritative
2. Ensure every `skills/*/*/SKILL.md` file on disk has a ledger row (add a `Pending` row if missing). Do NOT require a per-file `**Status:**` anchor — Format B has none, and that is not a missing-status error
3. For files that DO carry an in-file `**Status:**` (Format A / C / template), if it disagrees with the ledger row, the ledger wins — update the in-file anchor to match
4. Auto-skip (treat as already done) ONLY CMs whose ledger Status is `Applied` or `Skipped`
5. For `Documented` **INFRA** CMs, RE-RUN the Step 3.2 INFRA file-inventory pre-check and REOPEN the CM (set its ledger row back to `Pending`) **ONLY when the CM's own RECIPE/text references an in-repo config surface that ACTUALLY EXISTS** (the CM names a config the repo has, e.g. Dockerfile / docker-compose.yml / .dockerignore / server.ts) so "INFRA default = APPLIED when config exists" is honored. Do NOT reopen merely because SOME config file exists somewhere (that is repo-level-coarse and causes reopen churn). Genuinely out-of-repo INFRA (DNS / LB / WAF / TLS-inspection / LLM-provider settings) and Documented non-INFRA CMs stay done

---

## Forbidden Behaviors

| Action | Why Forbidden | Consequence |
|--------|---------------|-------------|
| **A script that applies code fixes, decides what to fix, or analyzes code** | Code analysis + fixes are AI-only inline work. Mechanical scripts (partition, count, verify) + SDE note posting (composite, verify+retry) + git/build/test ARE allowed per the SHELL TOOL USAGE POLICY | Apply fixes inline; use scripts only for mechanical/IO + SDE notes |
| **Delegating code analysis, fix application, or file generation to external programs** | The AI agent must do all work itself | Redo the step using AI reasoning and IDE tools |
| **Executing any step or batch from memory without reloading its section from the pinned `.sde-security/contract/apply-security-fixes/SKILL.md`** | The contract is pinned to disk at CONTRACT BOOTSTRAP. Every step preflight and every Step 3 batch MUST reload that step's section and quote a verbatim sentinel line as proof | STOP, reload the section from disk, re-emit with the sentinel quote |
| **Skipping Step 0 (AI Code Analysis)** | Must analyze ALL files FIRST | Run Step 0 before MCP connection |
| **Using ONLY grep for vulnerability detection** | Grep misses unmarked vulnerabilities | Use AI analysis to READ and UNDERSTAND code |
| **Starting MCP before Step 0 complete** | Wrong execution order | Step 0 → Step 1 → Step 0.5 → Step 1.5 → Step 2 → ... |
| **Skipping files because grep found nothing** | Unmarked code can be vulnerable | AI must analyze ALL source files |
| **Relying only on markers to find vulnerabilities** | Many vulns have no markers | AI analyzes code semantics |
| Skipping MCP verification | Connection must be confirmed | Verify before proceeding |
| Skipping handoff detection | Must check for file-based handoff before asking questions | Attempt detection first |
| Skipping user input gathering | Skill must be repository/project agnostic | Gather all inputs (from handoff or manual) |
| **Auto-proceeding with handoff without user confirmation** | User MUST confirm they want to use detected values | Always ask user to confirm or override |
| **Assuming repository from handoff without asking** | User may want different repository | Ask user to confirm repository selection |
| **Using detected project without confirmation** | User may want different project | Ask user to confirm project selection |
| Skipping spec file verification | Files must exist before processing | Verify AGENTS.md and skills/ |
| Stopping before scoped remaining = 0 | Core contract violation (user "stop" in one-by-one excepted) | Must resume immediately |
| Skipping per-CM progress update after any CM | Status must be persisted to disk immediately | Update the AGENTS.md ledger row (authoritative) after each CM, plus in-file Status when the file has that anchor |
| Agent-initiated early stop in scoped mode | Only user "stop" (one-by-one) or "no" (single_cm) is valid | Continue processing |
| Creating `*_secure.*` files | Violates in-place rule | Delete and fix original |
| Skipping progress output | Contract violation | Output for ALL items |
| Saying "critical fixes done" | Rationalization | ALL fixes are critical |
| Summary before gate | Premature completion | Gate must pass first |
| **Declaring apply complete while any file-tracked CM (incl. Format B) lacks a terminal LEDGER status** | Every CM must be processed and have a terminal status in its AGENTS.md ledger row (Format B has no in-file status -- the ledger row is authoritative) | Re-derive terminal status from the AGENTS.md ledger rows in the APPLY COMPLETENESS AUDIT; block completion until all ledger rows are terminal |
| **Spot-checking / sampling a subset in the final audit, or trusting in-memory loop counts instead of re-deriving from disk + SDE** | The APPLY COMPLETENESS AUDIT must enumerate every artifact class (terminal statuses re-derived from the AGENTS.md ledger rows, proof blocks, SDE note coverage re-fetched via `project_countermeasures op=list` — paginated, note_count per CM, no full task bodies) — no sampling, no memory-based counts | Re-derive from the ledger and re-fetch note_count via op=list for every CM before completion |
| **Tracking CM progress only in memory / chat / TodoWrite** | The on-disk AGENTS.md ledger rows are the authoritative single source of truth (in-file SKILL.md `**Status:**` is a secondary mirror on Format A/C only) | All audit/progress counts must be re-derived from the ledger on disk |
| **Batch-updating statuses at the end instead of per-CM write-through** | Each CM status must be persisted immediately after processing | Use LEDGER WRITE-THROUGH gate per CM |
| **Advancing to the next CM before the ledger write is confirmed on disk** | The re-read must confirm the write landed | Re-read the AGENTS.md ledger row (authoritative) before loop advances (plus in-file SKILL.md Status when the file has that anchor) |
| Asking "should I continue?" | Never ask | Always continue |
| Leaving skill files with Pending status | Status must reflect work done | Must update to Applied/Documented/Skipped |
| Skipping fixes because "intentionally vulnerable" | Repository intent is irrelevant | Apply ALL fixes regardless |
| **Leaving vulnerability markers in code** | All traces of intentional vulnerabilities must be removed | Remove ALL `vuln-code-snippet` and similar markers |
| **Keeping "educational" vulnerability comments** | No exceptions for training/demo purposes | Clean ALL vulnerability-related comments |
| **Rationalizing markers for "CTF/challenge" purposes** | Skill is repository-agnostic | Treat all repos as production systems |
| **Skipping countermeasure audit note posts** | Audit trail in SD Elements Notes section is required | Log failure, retry at end, report in verification |
| **Posting only `[AI-Documented] {reason}. See skills/...` for Documented CMs** | The `skills/` directory is deleted in Step 7 — that pointer dangles. Detailed `Why Not Code-Fixable` / `Recommended Action` analysis is lost forever | Embed verbatim sections inline in the note (Step 3.4); read local SKILL.md BEFORE Step 7. Fallback to brief note only if local file is unreadable |
| **Requesting elevated shell permissions for local file operations** | Sandbox-bypass permissions (`required_permissions: ["all"]`, `["full_network"]`) trigger approval prompts that can be aborted, killing the command | Use default sandbox; only escalate for actual external network access |
| **Batch status updates (`sed`, `find -exec`, shell loops on SKILL.md files)** | Bypasses per-CM analysis, causes misclassification (Rule 8) | Process each CM individually through the Step 3 loop |
| **Blanket category-to-status mapping (e.g., "all INFRA = Documented")** | Misclassifies CMs that have applicable config files | Evaluate each CM individually against actual repo files |
| **Skipping SKILL.md reading for any CM** | Cannot produce CM PROCESSING PROOF block; misses task recipe | Read every CM's SKILL.md completely before processing |
| **Processing CMs outside the main Step 3 loop** | Circumvents progress tracking, proof blocks, and per-CM verification | All CM processing happens inside the loop |
| **Writing `.sde-apply-handoff.json` with any schema other than Step 6.5.3** (missing required keys, extra keys, wrong types, `files_modified` at top level instead of per-CM, `summary` instead of `totals`, adding `domain`/`skill_file`/`project_name`/`business_unit_id`/`timestamp` to any level) | Downstream `code-scan-verification-validation` depends on the exact closed schema; non-conformant handoff causes silent data loss, incorrect verification verdicts, or HARD STOP | Delete the file, rebuild from `audit_records` using Step 6.5.5 pseudocode verbatim, re-validate with Step 6.5.6 |
| **Skipping a library-sourced SKILL.md because it lacks "Code to Fix" section** | Library-sourced files use different section headings (Decision Table, Gotchas, Quick Verification) — see SKILL.md Step 3.1 Format Detection | Detect YAML front-matter, use library-format sections (Decision Table + Gotchas + Quick Verification) instead of Code to Fix / Required Fix |
| **Spawning a subagent on Composer 2 (`composer-2.5-fast`) or any model other than the parent's** | Composer 2 / weaker models silently abandon CM loops, skip CMs, use wrong endpoints, lose context, falsely claim completion | Any subagent MUST use the parent agent's model (set `model` explicitly); in Cursor override the Composer-2 default or run inline |
| **Delegating in a way that lets CMs be silently skipped, or treating delegation as transferring completeness** | The parent ALWAYS re-derives terminal status for every scoped CM from disk + SDE; delegation never transfers the completeness obligation | Delegate only bounded, verifiable sub-tasks; every subagent emits `[PROGRESS]`; the parent verifies every CM |
| **Processing a "representative sample" of scoped CMs instead of all** | Observed failure pattern: agent applies fixes to a subset and claims "representative coverage." EVERY scoped CM must be individually processed through the Step 3 loop | Re-derive the scoped set, process every remaining CM |
| **Stopping the Step 3 batch loop before running total == scoped_total** | The batch loop MUST run for every scoped CM. "Context constraints," "representative sample," or "critical ones done" are not valid exit conditions -- only a CONTEXT CHECKPOINT is | Resume from the first batch with un-done CMs (re-derive from disk ledger) |
| **Rationalizing sampling with "pragmatic," "representative," "efficient," "critical only," or "context constraints"** | These words appearing in reasoning about loop scope are a red flag. The correct response to scale is to execute the batches, not to sample them | Drop the rationalization; execute the remaining batches |
| **Marking the Step 3 processing step as "completed" in TodoWrite before the APPLY COMPLETENESS AUDIT passes** | After context summarization, a continuation agent that sees status=completed will skip the remainder. The step stays "in_progress" until the audit shows all scoped CMs have terminal status on disk | Keep the step in_progress; only mark completed after the audit gate passes |
| **Using "key CMs," "across all categories," or "across categories" to rationalize partial coverage** | Observed failure: agent wrote "queried 25+ key CMs across all categories" and declared coverage for ~6% of CMs. These phrases are sampling tells — if they appear in your reasoning, STOP and return to the BATCH PLAN | Discard the conclusion, return to BATCH PLAN, process every remaining CM |
| **Using "the pattern is clear," "the rest have," or "the rest are" to infer results for unprocessed CMs** | You cannot know the outcome for CMs you haven't processed. Process every CM individually | Return to loop and continue |
| **Using "only N CMs..." or "only N have..." to justify stopping a loop early** | "only" + a count + early stop = sampling. Every scoped CM must be processed | Continue processing all remaining CMs |
| **Writing "queried N+ CMs" (with a plus sign) as a substitute for full coverage** | "N+" means "I stopped counting" — which means you stopped processing | Use exact counts only |
| **Writing "Let me finalize" before the loop is complete** | You may only "finalize" when running_total == scoped_total | Continue processing |
| **Filling in the APPLY COMPLETENESS AUDIT without per-CM terminal-status files matching scoped_total** | The audit now has a PRECONDITION requiring batch plan + all mini-gates emitted. A typed YES with fewer files than scoped_total is a contract violation | Run audit only after all batches pass |
| **Posting SDE notes one CM at a time instead of batching via a single composite call** | The per-batch SDE notes MUST be posted with ONE `POST /api/v2/composite/` call (up to 50 sub-requests) issued by the **SDE Direct API Access script** (SKILL.md "SDE Direct API Access" section) -- NOT the `api_request` MCP tool, NOT per-CM `addNote` looping (which burns context and API round-trips) | Accumulate `pending_notes[]` per batch, write the composite body to disk, run the direct-API script once at the batch boundary |
| **A script applying/generating/rewriting CODE FIXES, or deciding what to fix** | Code analysis + fixes are AI-only inline work (read recipe, locate vulnerable code, edit via Write/StrReplace). Mechanical scripts (partition, count, verify) and SDE note posting (composite, with verify+retry) ARE allowed; git/build/test ARE allowed | Apply every fix inline; use scripts only for mechanical/IO + SDE notes |
| **Scripted SDE note posting without completeness-verification + retry** | A note-flush script MUST reconcile every `reference_id` and retry transient/partial failures; silently dropping a note is a contract violation | Verify the composite response per reference_id; retry the failed subset |
| **Verification that reads file BODIES into context instead of script/grep counts** | The APPLY COMPLETENESS AUDIT + verify-apply-output.sh + from-scratch verification MUST count terminal-status LEDGER rows via shell/grep and re-fetch `note_count` via `project_countermeasures op=list` (paginated; note_count per CM), parsing counts to disk -- never by reading full task bodies / file bodies into context | Count terminal-status ledger rows via shell/grep + re-fetch note_count via op=list |

**Note:** User "skip" and "stop" in one-by-one mode, and user "no" in single-CM mode, are NOT forbidden behaviors. They are explicit user decisions and valid control flow.

---

### Subagent / Delegation Policy -- Detailed Rationale

Subagents reduce the parent's context-window strain and ARE allowed. The failure modes below were observed with Composer 2 / wrong-model subagents -- using the PARENT agent's model removes them:

| Failure Mode | Impact |
|---|---|
| Subagent silently abandoned CM processing loop after ~15 CMs | Remaining CMs left unprocessed; agent falsely reported completion |
| Subagent skipped CMs and falsely claimed "all applied" | No applied fixes for skipped CMs; silent data loss in handoff |
| Subagent lost context mid-loop | Repeated identical processing; missed CMs entirely |
| Composer 2 delegated fix application | Produced incomplete fixes; missed cross-surface parity |
| Subagent used wrong SDE API endpoint for verification notes | Notes posted to wrong field or silently dropped |

**Enforcement summary:**
- Subagents MAY be used to reduce context strain, but the subagent `model` MUST be set explicitly to the PARENT agent's model -- NEVER `composer-2.5-fast` (Composer 2). In Cursor the DEFAULT subagent is Composer 2, so you MUST override the model; if you cannot, run inline.
- The parent ALWAYS owns completeness: re-derive terminal status for every scoped CM from disk + SDE; every subagent emits `[PROGRESS]` and returns a verifiable result.
- Code analysis + fix application are AI work -- done by the parent OR a same-model subagent (NEVER a script and NEVER a non-parent model); the parent re-verifies every CM's terminal status on disk.
- **No exception lets a CM be silently skipped** -- scale is handled by bounded, verified delegation or multi-session execution, never by sampling.

---

## Handoff Consumption

**Why this matters:** Each skill runs in a new agent context with no conversation history. The previous skill writes a handoff file to pass data.

### Detection Order

1. **Scan workspace** for directories containing `.sde-handoff.json`
   - If found with `source_skill` in (`"generate-security-skill-files"`, `"setup-security-plan-from-repo"`, `"create-security-plan-from-specs"`): Load values from `{repo}/.sde-handoff.json`. In the current chain the handoff is written by `generate-security-skill-files` (`stage: "skill-files-generated"`); the legacy combined skills are accepted for backward compatibility.
   - Verify files still exist before using
   - **Set `mode = greenfield` when the handoff's `evidence_source == "specs"` (or, when `evidence_source` is absent, legacy `source_skill == "create-security-plan-from-specs"` or skill files are Format C); else `mode = brownfield` (`evidence_source == "codebase"`).** In greenfield mode: Step 0 master vuln list is expected empty (placeholders, not vulnerable code) — NOT a failure; Step 3.1 CODE_FIX = "implement the Secure Implementation Pattern into the placeholder"; Step 3.5 cross-surface parity is N/A (`0 (greenfield)`); Step 5.6 marker deletion is N/A. See SKILL.md Step 0.0 GREENFIELD MODE.
   
2. **Scan workspace** for directories with `AGENTS.md` + `skills/` (fallback if no handoff file found)
   - If exactly one found: Offer to use it
   - If multiple found: Ask user to select

3. **Fall back to manual questions** if nothing detected

### Checkpoint Output

```
[CHECKPOINT] Handoff: LOADED from .sde-handoff.json
```
OR
```
[CHECKPOINT] Handoff: DETECTED from scan
```
OR
```
[CHECKPOINT] Handoff: NOT FOUND - manual input required
```

### User Confirmation (MANDATORY)

**You MUST ALWAYS ask the user to confirm detected values - NEVER auto-proceed.**

Even when handoff is detected, **ALWAYS** ask the user:
- "Found handoff from previous skill. Use these values? [Yes / Choose different]"
- **Wait for user response** - do not proceed without explicit confirmation

**This is NOT optional.** The user must explicitly confirm before proceeding, even if handoff data looks correct.

This ensures the skill remains repository/project agnostic while benefiting from handoff when available.

---

## Context Limit Handling

If approaching context limits:

```
=== CONTEXT CHECKPOINT ===
Skill: apply-security-fixes
Progress: {done}/{total}
Applied so far: {A}
Documented so far: {D}
Last completed: {countermeasure_id}
Remaining items: [{id1}, {id2}, ...]
Status: INCOMPLETE - requires continuation
===========================

To resume: Say "continue"
```

**On resume:** Continue from exact position, DO NOT restart.

---

## Handoff Requirements

**Only after the completion gate passes (Step 5 MATCH = YES or `one_by_one` session summary) AND Steps 6–8 have completed (handoff file written, cleanup done, commit if git enabled):**

```
HANDOFF DATA:
- repository_path: {path}
- project_id: {id}
- project_name: {name}
- risk_policy_id: {id or N/A}
- scope: {all / domain={name} / single_cm={id} / one_by_one}
- Applied: {A} countermeasures
- Documented: {D} countermeasures
- Skipped: {S} countermeasures
- Total: {A+D+S}/{scoped_total}
- Files modified: {list}
- Handoff file: .sde-apply-handoff.json ({A+D+S} CMs recorded, written in Step 6.5)
- Upstream handoff: .sde-handoff.json (generate-security-skill-files, preserved)

Next skill: @sde-skills/code-scan-verification-validation
```

**Handoff file contract (`.sde-apply-handoff.json`) -- CLOSED SCHEMA:**
- Written in Step 6.5, BEFORE Step 7 cleanup deletes `skills/` and `security/`
- `source_skill` MUST equal `"apply-security-fixes"`
- `handoff_version` MUST equal `"2"`
- **Distinct from `.sde-handoff.json`** (which is owned by `generate-security-skill-files` and must not be touched by this skill)
- `countermeasures[]` has one entry per scoped CM (Applied, Documented, Skipped)
- **Required top-level keys (exactly these 10, no more):** `source_skill`, `handoff_version`, `generated_at`, `upstream_handoff`, `repository_path`, `project_id`, `security_branch`, `scope`, `totals`, `countermeasures`
- **Required per-CM keys (exactly these 6, no more):** `id`, `full_id`, `status`, `category`, `files_modified`, `sde_note_result`
- `full_id` MUST equal `"{project_id}-{id}"` for every CM
- `files_modified` is **per-CM only** (a list of file paths modified for that specific CM) -- there MUST NOT be a top-level `files_modified` key
- `totals` is the correct key for the counts object -- NEVER use `summary` as the key name
- **NO additional keys allowed** in the top-level object or per-CM objects. The schema is closed. Do NOT add `project_name`, `business_unit_id`, `domain`, `skill_file`, `title`, `note_text`, `timestamp`, or any other key. Everything not listed above is fetched live from SDE by `code-scan-verification-validation` via `project_countermeasures op=get`
- Downstream skill (`code-scan-verification-validation`) depends on this exact schema and will HARD STOP if missing, malformed, or containing unexpected keys
- Step 6.5.6 runs a strict validation gate that rejects non-conformant files; see SKILL.md for the full validation pseudocode

**Invariant:** `.sde-handoff.json` (the upstream generate-security-skill-files handoff) is READ-ONLY for this skill. Step 0.5 reads it; no other step may write, rename, or delete it.

---

## Contract Acceptance

By reading this file, you agree to:
1. Verify MCP connection before proceeding
2. Attempt handoff detection (file-based then scan-based) before asking questions
3. **ALWAYS ask user to confirm detected handoff values** - never auto-proceed
4. **Gather user inputs with explicit confirmation** (user must confirm handoff OR answer manual questions) - **NEVER assume**
5. Verify AGENTS.md and skills/ exist before processing
6. Output progress after EVERY countermeasure
7. **Post an audit comment (Notes section) in SD Elements for EACH countermeasure processed** — in the Step 3 batch loop these per-CM notes are accumulated in `pending_notes` and posted via ONE composite call at each batch boundary (do NOT call `op=addNote` once per CM inside a batch); in `one_by_one`/`single_cm` mode post immediately via `project_countermeasures op=addNote`. The `note` parameter is a plain string containing the audit text. For ML_DOC / external-INFRA (Documented) CMs, the note MUST embed the verbatim `Why Not Code-Fixable` and `Recommended Action` sections read inline from `skills/{domain}/{cm-slug}/SKILL.md` **before** Step 7 deletes the `skills/` directory — this is the only durable persistence path for that analysis. If the local file is unreadable, fall back to a brief `[AI-Documented] {reason}` note rather than skipping the call. Verification verdicts (pass/partial/fail) are NOT posted here — those are the responsibility of `code-scan-verification-validation` downstream via the `verification` MCP tool. See SKILL.md Step 3.4 for the full template.
8. Loop until scoped remaining = 0 (user "stop"/"no" are valid early exits in one-by-one/single_cm modes)
9. Output verification block before ANY completion claim
10. Fix files in-place, never create alternatives
11. Never stop for "critical fixes done" or similar reasoning
12. Use checkpoint pattern if hitting context limits
13. Provide stored values for next skill in handoff
14. **Apply ALL fixes regardless of repository intent** - no "intentionally vulnerable" exceptions
15. **Remove ALL vulnerability markers** - `vuln-code-snippet`, `VULNERABLE`, etc.
16. **Treat every repository as production** - no educational/training/CTF exceptions
17. **Run the Verifiability Gate (Step 3.V)** for each Applied CM inside the loop — reclassify to Documented if the CM's scope extends beyond repository files; clear `files_modified[]` to prevent misleading downstream verification
18. **Run the Cross-Surface Parity Check (Step 3.5)** after the main CM processing loop — identify and fix all other code paths performing the same security-sensitive operation; merge parity-fixed files back into `audit_records` for the handoff
19. **Process CMs one at a time with proof blocks (Rule 8)** — never batch-read skill files; emit a per-CM `CM PROCESSING PROOF` block showing the CM ID, analysis, files modified, and status for every CM processed in the loop
20. **Subagents MAY be used to reduce context strain, but ONLY with `model` set explicitly to the parent agent's model — NEVER Composer 2 (`composer-2.5-fast`); if you cannot set the model, run inline. The parent always owns completeness (re-derive every scoped CM's terminal status from disk + SDE); code fixes are AI work (parent or same-model subagent), never a script or non-parent model**

**There are NO exceptions to these rules. This skill is REPOSITORY-AGNOSTIC.**

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│ APPLY FIXES AGENT - EXECUTION RULES                         │
├─────────────────────────────────────────────────────────────┤
│ ⚠️ STEP 0: AI Code Analysis FIRST (before MCP!)             │
│   - READ each source file with AI                           │
│   - ANALYZE for ALL vulnerability types                     │
│   - CREATE checklist of ALL files to fix                    │
│   - DO NOT rely on grep alone!                              │
├─────────────────────────────────────────────────────────────┤
│ ✓ Verify MCP connection (after Step 0)                      │
│ ✓ Scan repos for handoff file ({repo}/.sde-handoff.json)    │
│ ✓ Scan for repos with AGENTS.md if no handoff file          │
│ ✓ ALWAYS ASK USER TO CONFIRM detected values                │
│ ✓ Gather user inputs (confirmed by user, not assumed)       │
│ ✓ Verify spec files exist (AGENTS.md, skills/)              │
│ ✓ Output [PROGRESS] after EACH countermeasure               │
│ ✓ Add countermeasure note in SDE after each fix             │
│ ✓ Loop until scoped remaining = 0                            │
│ ✓ Output verification block before "complete"               │
│ ✓ Fix files in-place only                                   │
│ ✓ Use checkpoint if hitting limits                          │
│ ✓ Remove ALL vulnerability markers (vuln-code-snippet, etc) │
│ ✓ Treat EVERY repo as production (no "educational" excuses) │
├─────────────────────────────────────────────────────────────┤
│ ✗ Do NOT skip Step 0 (AI Code Analysis)                     │
│ ✗ Do NOT use ONLY grep - must use AI analysis               │
│ ✗ Do NOT start MCP before Step 0 is complete                │
│ ✗ Do NOT skip handoff detection                             │
│ ✗ Do NOT auto-proceed with handoff without user confirm     │
│ ✗ Do NOT skip input gathering or confirmation               │
│ ✗ Do NOT assume repository or project from context          │
│ ✗ Do NOT stop before 100%                                   │
│ ✗ Do NOT create *_secure.* files                            │
│ ✗ Do NOT skip progress output                               │
│ ✗ Do NOT ask "should I continue?"                           │
│ ✗ Do NOT claim complete without verification                │
│ ✗ Do NOT skip fixes for "intentionally vulnerable" repos    │
│ ✗ Do NOT leave vulnerability marker comments in code        │
│ ✗ Do NOT skip verification note posts (log failures, retry) │
│ ✗ Do NOT request elevated shell permissions for local file ops│
│ ✗ Do NOT use batch ops (sed, shell loops) for status updates │
│ ✗ Do NOT classify by category alone - evaluate each CM      │
│ ✗ Do NOT skip reading each CM's SKILL.md task recipe        │
│ ✓ MUST output CM PROCESSING PROOF block for every CM        │
└─────────────────────────────────────────────────────────────┘
```
