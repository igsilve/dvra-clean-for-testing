---
name: apply-security-fixes
description: Reads generated AGENTS.md and per-countermeasure skill files, then applies all security fixes to source code in-place with progress tracking and SD Elements audit notes. Use when security spec files have been generated and fixes need to be applied to a repository.
---

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
>
> **At skill start (before Step 0):** determine the parent agent's model. If you will spawn subagents, you will set their `model` to the parent's model explicitly (NEVER `composer-2.5-fast`). Output:
> `[CHECKPOINT] Subagent policy: same-model-as-parent | Composer 2 FORBIDDEN | parent owns completeness (tri-source)`

# Apply Security Fixes from Generated Specifications

This skill reads the generated AGENTS.md and domain skill files, then applies ALL fixes to the source code. This is the execution phase where vulnerabilities are actually fixed.

## Execution Contract

**REQUIRED:** Read and follow the [./AGENTS.md](./AGENTS.md) execution contract.

**THIS SKILL HAS THE STRONGEST ENFORCEMENT** because it's where execution most commonly fails.

---

## AUTHORITATIVE EXECUTION CONTRACT

**This skill is the authoritative source for what to do and how much work is required. Your own judgment about feasibility, scale, or "pragmatic" shortcuts is OVERRIDDEN by this document.**

This skill involves a high-volume per-CM loop. Expect:
- **Fix application + SDE note posting (Step 3):** One full processing cycle per scoped CM -- read SKILL.md, apply fix, update ledger, post SDE note (typically 50-500 cycles)

These numbers are CORRECT and EXPECTED. They are NOT a sign that something is wrong, NOT a reason to sample, and NOT a reason to seek shortcuts. The batch structure (Step 2.8) breaks the work into groups of 20 (each apply CM is heavy AI work -- read recipe, locate code, apply fix) with per-batch verification -- follow it mechanically. The SDE note for every CM in a batch is posted with ONE Composite API call (`POST /api/v2/composite/`, up to 50 sub-requests), so the API cost is ~1 call per batch, not 1 per CM. Multi-session execution is normal for large projects; disk state is the source of truth across sessions (the AGENTS.md ledger is authoritative; the in-file SKILL.md `**Status:**` is a secondary mirror present only on Format A/C -- Format B has none).

## SHELL TOOL USAGE POLICY (CANONICAL)

**Scripts are allowed for mechanical/IO work; the AI owns all analysis and especially the CODE FIXES. There are NO content/file-generation helper routines in this skill -- it edits existing code.**

| Work | Owner | Rule |
|------|-------|------|
| Applying security CODE FIXES | **AI only** | every fix applied manually/inline (read recipe, locate vulnerable code, edit via Write/StrReplace). A script may NEVER apply/generate/rewrite fix code in bulk -- content integrity is paramount |
| Deciding what to fix / analyzing code | **AI only** | no grep/keyword script substitutes for understanding the code |
| Partition scoped CMs into batches; count + verify on disk | **script OK** | mechanical |
| SDE note posting / note_count re-query | **script OK** | via the SDE Direct API Access script (see the section below) -- direct `POST /api/v2/composite/`, ONLY WITH completeness-verification (every `reference_id` reconciled) + retry (429/5xx/timeout/partial). Do NOT use the `api_request` MCP tool. |
| `git`, build, test, lint | **OK** | this skill applies real code |
| `/tmp` scratch | **OK** |

Parsing `composite_response` JSON in your reasoning is expected AI work, NOT scripting. Do NOT improvise a bulk script that edits code.

## SDE Direct API Access (batch/composite via a script)

<!-- SDE-DIRECT-API-BLOCK v1 -- KEEP BYTE-IDENTICAL across apply-security-fixes, setup-security-plan-from-repo, create-security-plan-from-specs, generate-security-skill-files. Edit all copies together. -->

**Batch/composite SDE work (2+ sub-requests: note posting, survey comments, library-amendment lookups) is done by the reference SCRIPT below -- NOT the `api_request` MCP tool and NOT inline `curl`.** Dedicated MCP tools (`project`, `project_survey`, `project_countermeasures`, `verification`, `library_search`, ...) remain the way to do single/interactive calls. A bare one-line `curl` is acceptable ONLY for a single trivial reference GET with nothing to reconcile.

**Runtime selection (in order)** -- save the chosen reference to a file (`sde_composite.py` or `sde_composite.js`) and run it (`--input <body>.json --out <resp>.json`):
1. If `python3`/`python` is available -> use the **Python reference** below verbatim.
2. Else if `node` is available -> run the **Node reference** below verbatim.
3. Else -> translate the Python reference into an available runtime (bash+`curl`, or `curl.exe` in PowerShell -- bare `curl` in Windows PowerShell 5.1 is an `Invoke-WebRequest` alias, so call `curl.exe`), preserving the behavioral-contract header. Then SELF-TEST it once (a GET or a single note) before real batch use.

**Auth:** the scripts read `SDE_HOST` + `SDE_API_KEY` from the environment, falling back to `.cursor/mcp.json` (`mcpServers.sdelements.env`). Never hardcode or print the key. Direct calls use normal TLS verification. **When a handoff is in play, EXPORT `SDE_HOST` from the handoff's `sde_host` (the authoritative project host derived from the project `url`) before running the script — the `mcp.json` `SDE_HOST` may be an ALIAS pointing at a different instance/tenant, so reconcile to the handoff host so direct-API calls hit the same tenant the MCP/handoff read and write.**

**Contract (both references enforce it):** POST `https://$SDE_HOST/api/v2/composite/` -> write the full response to disk (keeps the bulk payload OUT of the context window) -> reconcile every `reference_id` -> retry the failed subset once -> print only a compact `posted/failed` summary -> exit non-zero on unresolved failures. You supply the composite body as a JSON file (`{all_or_none:false, strict_ref_checking:false, composite_request:[{method,path,reference_id,body?}...]}`), then read the on-disk response only for any failed `reference_id`. For a GET lookup (e.g. amendments) put query params IN THE URL (`.../amendments/?expand=text`) inside the sub-request `path`.

**Delegation:** running this script is a NON-REASONING action and MAY be delegated to a subagent (set `model` explicitly; NEVER `composer-2.5-fast`); the subagent returns only the summary and the parent re-derives success from disk. Authoring note/comment/fix CONTENT and any analysis/verdict is REASONING -- never delegated.

### Python 3 reference (canonical -- stdlib only)

```python
#!/usr/bin/env python3
"""
SD Elements Composite/Batch helper -- CANONICAL REFERENCE (Python 3, stdlib only).

BEHAVIORAL CONTRACT (every runtime/port of this script MUST preserve ALL of it):
  1. AUTH: read SDE_HOST + SDE_API_KEY from the environment. If either is unset,
     read them from the MCP config -- ./.cursor/mcp.json then ~/.cursor/mcp.json --
     at mcpServers.sdelements.env.{SDE_HOST,SDE_API_KEY}. NEVER hardcode the key;
     NEVER print it.
  2. INPUT: read a composite request body (JSON) from --input. Shape:
       { "all_or_none": false, "strict_ref_checking": false,
         "composite_request": [ {"method","path","reference_id","body"?}, ... ] }
  3. SEND: POST it to  https://$SDE_HOST/api/v2/composite/  with header
       Authorization: Token $SDE_API_KEY   (normal TLS verification -- no -k).
  4. OFFLOAD: write the FULL response JSON to --out (the bulk payload stays on
     disk, NOT on stdout / NOT in the agent context window).
  5. RECONCILE: inspect EVERY reference_id in composite_response.
       http_status_code 2xx  => ok
       otherwise             => failed[]
  6. RETRY: re-POST ONLY the failed sub-requests ONCE, as a single follow-up
     composite call (same paths/bodies). Merge the retry outcome back in.
  7. SUMMARY: print ONLY a compact summary to stdout
       (posted / failed counts + the failed reference_ids).
  8. EXIT: non-zero if ANY reference_id is still unresolved after the retry.

Usage:
  SDE_HOST=https://demo.sdelements.com SDE_API_KEY=xxxx \
    python3 sde_composite.py --input body.json --out resp.json
  # or omit the env vars and rely on .cursor/mcp.json

Dependencies: none (urllib, json, os, sys, argparse). Cross-platform (Win/macOS/Linux).
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _load_from_mcp_json():
    """Return (host, key) from the first mcp.json found, or (None, None)."""
    candidates = [
        os.path.join(os.getcwd(), ".cursor", "mcp.json"),
        os.path.expanduser(os.path.join("~", ".cursor", "mcp.json")),
    ]
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
        except (OSError, ValueError):
            continue
        env = (
            cfg.get("mcpServers", {})
            .get("sdelements", {})
            .get("env", {})
        )
        host = env.get("SDE_HOST")
        key = env.get("SDE_API_KEY")
        if host and key:
            return host, key
    return None, None


def load_auth():
    """Resolve (host, key): environment first, then mcp.json. Exit if missing."""
    host = os.environ.get("SDE_HOST")
    key = os.environ.get("SDE_API_KEY")
    if not (host and key):
        m_host, m_key = _load_from_mcp_json()
        host = host or m_host
        key = key or m_key
    if not (host and key):
        sys.stderr.write(
            "[sde_composite] ERROR: SDE_HOST/SDE_API_KEY not found in env or "
            ".cursor/mcp.json (mcpServers.sdelements.env)\n"
        )
        sys.exit(2)
    return host.rstrip("/"), key


def post_composite(host, key, body):
    """POST a composite body; return the parsed JSON response dict."""
    url = host + "/api/v2/composite/"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", "Token " + key)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:  # normal TLS verification
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # The composite endpoint may return a non-2xx OUTER status while still
        # providing per-reference_id detail in the body. Parse it so we can
        # reconcile; only treat as a hard failure when there is no
        # composite_response to inspect.
        raw = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = None
        if isinstance(parsed, dict) and "composite_response" in parsed:
            return parsed
        raise


def reconcile(response):
    """Return {reference_id: http_status_code} for every sub-response."""
    out = {}
    for sub in response.get("composite_response", []):
        out[sub.get("reference_id")] = sub.get("http_status_code")
    return out


def main():
    ap = argparse.ArgumentParser(description="SDE composite batch helper")
    ap.add_argument("--input", required=True, help="path to composite body JSON")
    ap.add_argument("--out", required=True, help="path to write the full response JSON")
    args = ap.parse_args()

    host, key = load_auth()

    with open(args.input, "r", encoding="utf-8") as fh:
        body = json.load(fh)

    subs_by_ref = {s.get("reference_id"): s for s in body.get("composite_request", [])}
    total = len(subs_by_ref)

    try:
        response = post_composite(host, key, body)
    except urllib.error.HTTPError as exc:
        sys.stderr.write("[sde_composite] outer HTTP %s\n" % exc.code)
        sys.exit(1)
    except urllib.error.URLError as exc:
        sys.stderr.write("[sde_composite] transport error: %s\n" % exc.reason)
        sys.exit(1)

    statuses = reconcile(response)
    failed = [ref for ref, code in statuses.items() if not (code and 200 <= code < 300)]

    # RETRY the failed subset ONCE, in a single follow-up composite call.
    if failed:
        retry_body = {
            "all_or_none": False,
            "strict_ref_checking": False,
            "composite_request": [subs_by_ref[ref] for ref in failed if ref in subs_by_ref],
        }
        try:
            retry_resp = post_composite(host, key, retry_body)
            merged = {s.get("reference_id"): s for s in response.get("composite_response", [])}
            for s in retry_resp.get("composite_response", []):
                merged[s.get("reference_id")] = s
            response["composite_response"] = list(merged.values())
            statuses = reconcile(response)
            failed = [ref for ref, code in statuses.items() if not (code and 200 <= code < 300)]
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            sys.stderr.write("[sde_composite] retry call failed: %s\n" % exc)

    # OFFLOAD the full response to disk (keep it out of stdout/context).
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(response, fh, indent=2)

    posted = total - len(failed)
    print("[sde_composite] posted=%d failed=%d total=%d" % (posted, len(failed), total))
    if failed:
        print("[sde_composite] failed_reference_ids=%s" % ",".join(str(f) for f in failed))
        print("[sde_composite] full response written to %s" % args.out)
        sys.exit(1)
    print("[sde_composite] full response written to %s" % args.out)
    sys.exit(0)


if __name__ == "__main__":
    main()
```

### Node reference (stdlib only)

```javascript
#!/usr/bin/env node
/*
 * SD Elements Composite/Batch helper -- REFERENCE (Node.js, stdlib only).
 * Identical BEHAVIORAL CONTRACT to the canonical Python reference above:
 *   1. AUTH: SDE_HOST + SDE_API_KEY from env; else ./.cursor/mcp.json then
 *      ~/.cursor/mcp.json at mcpServers.sdelements.env. Never hardcode/print the key.
 *   2. INPUT: composite body JSON from --input.
 *   3. SEND: POST https://$SDE_HOST/api/v2/composite/ with Authorization: Token
 *      (normal TLS verification).
 *   4. OFFLOAD full response to --out (bulk stays on disk, not stdout).
 *   5. RECONCILE every reference_id (2xx => ok; else => failed[]).
 *   6. RETRY the failed subset ONCE.
 *   7. SUMMARY: compact posted/failed + failed ids only.
 *   8. EXIT non-zero if any reference_id is still unresolved.
 * Usage: node sde_composite.js --input body.json --out resp.json
 * Dependencies: none (https, fs, path, os). Cross-platform.
 */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const https = require("https");

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 1) {
    if (argv[i] === "--input") args.input = argv[i + 1];
    else if (argv[i] === "--out") args.out = argv[i + 1];
  }
  if (!args.input || !args.out) {
    process.stderr.write("[sde_composite] usage: --input body.json --out resp.json\n");
    process.exit(2);
  }
  return args;
}

function loadFromMcpJson() {
  const candidates = [
    path.join(process.cwd(), ".cursor", "mcp.json"),
    path.join(os.homedir(), ".cursor", "mcp.json"),
  ];
  for (const p of candidates) {
    try {
      const cfg = JSON.parse(fs.readFileSync(p, "utf8"));
      const env = ((cfg.mcpServers || {}).sdelements || {}).env || {};
      if (env.SDE_HOST && env.SDE_API_KEY) return { host: env.SDE_HOST, key: env.SDE_API_KEY };
    } catch (e) {
      /* try next candidate */
    }
  }
  return { host: null, key: null };
}

function loadAuth() {
  let host = process.env.SDE_HOST;
  let key = process.env.SDE_API_KEY;
  if (!host || !key) {
    const m = loadFromMcpJson();
    host = host || m.host;
    key = key || m.key;
  }
  if (!host || !key) {
    process.stderr.write(
      "[sde_composite] ERROR: SDE_HOST/SDE_API_KEY not found in env or .cursor/mcp.json\n"
    );
    process.exit(2);
  }
  return { host: host.replace(/\/+$/, ""), key: key };
}

function postComposite(host, key, body) {
  return new Promise((resolve, reject) => {
    const url = new URL(host + "/api/v2/composite/");
    const payload = Buffer.from(JSON.stringify(body), "utf8");
    const req = https.request(
      {
        method: "POST",
        hostname: url.hostname,
        port: url.port || 443,
        path: url.pathname,
        headers: {
          Authorization: "Token " + key,
          "Content-Type": "application/json",
          "Content-Length": payload.length,
        },
      },
      (res) => {
        let raw = "";
        res.on("data", (chunk) => {
          raw += chunk;
        });
        res.on("end", () => {
          let parsed = null;
          try {
            parsed = JSON.parse(raw);
          } catch (e) {
            parsed = null;
          }
          if (parsed && parsed.composite_response) {
            resolve(parsed);
          } else if (res.statusCode >= 200 && res.statusCode < 300 && parsed) {
            resolve(parsed);
          } else {
            reject(new Error("outer HTTP " + res.statusCode));
          }
        });
      }
    );
    req.on("error", reject);
    req.write(payload);
    req.end();
  });
}

function reconcile(response) {
  const out = {};
  for (const sub of response.composite_response || []) {
    out[sub.reference_id] = sub.http_status_code;
  }
  return out;
}

function failedRefs(statuses) {
  return Object.keys(statuses).filter((ref) => {
    const code = statuses[ref];
    return !(code && code >= 200 && code < 300);
  });
}

async function main() {
  const args = parseArgs(process.argv);
  const { host, key } = loadAuth();

  const body = JSON.parse(fs.readFileSync(args.input, "utf8"));
  const subsByRef = {};
  for (const s of body.composite_request || []) subsByRef[s.reference_id] = s;
  const total = Object.keys(subsByRef).length;

  let response;
  try {
    response = await postComposite(host, key, body);
  } catch (e) {
    process.stderr.write("[sde_composite] " + e.message + "\n");
    process.exit(1);
  }

  let statuses = reconcile(response);
  let failed = failedRefs(statuses);

  if (failed.length) {
    const retryBody = {
      all_or_none: false,
      strict_ref_checking: false,
      composite_request: failed.filter((r) => subsByRef[r]).map((r) => subsByRef[r]),
    };
    try {
      const retryResp = await postComposite(host, key, retryBody);
      const merged = {};
      for (const s of response.composite_response || []) merged[s.reference_id] = s;
      for (const s of retryResp.composite_response || []) merged[s.reference_id] = s;
      response.composite_response = Object.keys(merged).map((k) => merged[k]);
      statuses = reconcile(response);
      failed = failedRefs(statuses);
    } catch (e) {
      process.stderr.write("[sde_composite] retry call failed: " + e.message + "\n");
    }
  }

  fs.writeFileSync(args.out, JSON.stringify(response, null, 2), "utf8");

  const posted = total - failed.length;
  process.stdout.write(
    "[sde_composite] posted=" + posted + " failed=" + failed.length + " total=" + total + "\n"
  );
  if (failed.length) {
    process.stdout.write("[sde_composite] failed_reference_ids=" + failed.join(",") + "\n");
    process.stdout.write("[sde_composite] full response written to " + args.out + "\n");
    process.exit(1);
  }
  process.stdout.write("[sde_composite] full response written to " + args.out + "\n");
  process.exit(0);
}

main();
```

**If you find yourself thinking any of the following, STOP -- you are about to violate the contract:**
- "That's a lot of CMs" -- yes, and this skill accounts for it
- "Let me be pragmatic / efficient / representative" -- those words mean you are about to sample
- "I'll do the rest in bulk / later / in a follow-up" -- fixes are applied per-CM by the AI (composite only batches the SDE notes); there is no bulk-fix path and later never comes
- "Context constraints make this infeasible" -- emit a CONTEXT CHECKPOINT instead of sampling
- "Let me just apply the critical ones" -- every scoped CM must be individually processed
- "Let me move forward to more impactful steps" -- FORBIDDEN; an incomplete loop is never "done"

**The correct response to scale is to execute the batches, not to reason about whether the scale is appropriate.**

## TIME & TURNS: COMPLETENESS IS THE ONLY PRIORITY (explicit permission)

**You have explicit, unconditional permission to take as many turns and as many sessions as you need. There is NO time pressure and NO turn budget. Quality and completeness are the ONLY things that matter.** Applying every fix individually across multiple sessions is the CORRECT behavior.

- Do NOT rush, compress, sample, or "be efficient" to finish sooner -- you will not be penalized for taking longer; you WILL fail the contract for missing/under-applying any CM.
- **The ONLY sanctioned way to pause is a CONTEXT CHECKPOINT** (emit it, tell the user to say "continue", resume via the resume protocol). This is NOT license to stop early, declare done prematurely, or skip the remainder -- a run is either COMPLETE (APPLY COMPLETENESS AUDIT + FROM-SCRATCH FINAL VERIFICATION pass) or INCOMPLETE (clean CONTEXT CHECKPOINT emitted). No third state.

---

## ⚠️⚠️⚠️ AI CODE ANALYSIS REQUIRED - NO GREP/PATTERN MATCHING ⚠️⚠️⚠️

**This entire skill MUST use AI code analysis. Do NOT rely on grep or pattern matching.**

### What This Means:

| ❌ FORBIDDEN | ✅ REQUIRED |
|--------------|-------------|
| `grep "vuln-code-snippet"` | READ each file with `read_file` tool |
| `grep "bypassSecurityTrust"` | ANALYZE code to understand what it does |
| Pattern matching for vulnerabilities | UNDERSTAND code semantics and context |
| Searching for text strings | IDENTIFY vulnerabilities from code behavior |
| Relying on markers to find issues | FIND unmarked vulnerabilities too |

### Why AI Analysis:

1. **Grep misses unmarked vulnerabilities** - Code can be vulnerable without a comment saying so
2. **Pattern matching lacks context** - `eval()` in a test file vs production code is different
3. **AI understands code flow** - Data from user input → SQL query = injection
4. **AI catches obfuscation** - Vulnerabilities can be hidden from simple text search

### For EVERY Step in This Skill:

- **DO:** Read files completely with `read_file`
- **DO:** Analyze code to understand its purpose
- **DO:** Identify ALL vulnerabilities (marked AND unmarked)
- **DO:** Verify fixes by re-reading and re-analyzing

- **DO NOT:** Use grep as your primary detection method
- **DO NOT:** Skip files because pattern search found nothing
- **DO NOT:** Assume no marker = no vulnerability

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
while len(scoped_remaining) > 0:
    process_next_countermeasure()
    output_progress()
# User "stop" in one-by-one and "no" in single_cm are the ONLY valid early exits
```

### Rule 3: No Premature Completion Claims

Before using "complete", "finished", "done", "summary", or "report", you MUST:
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
- Context/token limits (use checkpoint instead)

### Rule 6: Ignore Repository Intent - ALWAYS Apply Fixes (Repository-Agnostic)

**The purpose or intent of the repository is IRRELEVANT. This skill is REPOSITORY-AGNOSTIC.**

You MUST apply ALL fixes regardless of:
- "Intentionally vulnerable" applications (OWASP Juice Shop, DVWA, WebGoat, etc.)
- "Training", "demo", or "educational" repositories
- "CTF challenges" or "security testing" codebases
- Any other rationalization

**FORBIDDEN REASONING:**
- "This is intentionally vulnerable for training"
- "Fixing this would break the demo/CTF"
- "This vulnerability is by design"

### Rule 7: Remove Vulnerability Markers and Comments

**ALL vulnerability marker comments MUST be removed when fixing code.**

Remove these patterns:
- `// vuln-code-snippet` and similar annotations
- `// VULNERABLE`, `// INSECURE`, `// TODO: fix vulnerability`
- `<!-- VULNERABLE -->` HTML comments
- Any comments marking code as intentionally insecure
- CTF/challenge markers

**The final code should have NO traces of intentional vulnerability.**

### Rule 8: Per-CM Processing Only -- No Batch Operations (Structural Enforcement)

**EVERY countermeasure MUST be individually processed through the Step 3 loop. Batch operations are FORBIDDEN.**

| FORBIDDEN | REQUIRED |
|-----------|----------|
| `sed -i 's/Pending/Applied/' skills/*/*/SKILL.md` | Read each SKILL.md individually with `read_file` |
| `find skills/ -exec sed ...` | Process one CM at a time in the main loop |
| Blanket "all INFRA = Documented" | Check each INFRA CM for applicable config files before deciding |
| `for category in ...; do batch_update ...` | Individual status decision based on per-CM analysis |
| Any shell command that updates multiple SKILL.md files at once | Use `search_replace` on one file at a time after processing |

**Why this rule exists:** In a previous execution, an agent batch-classified all 47 INFRA countermeasures as "Documented" using `sed`, without checking whether each had an applicable config file (Dockerfile, docker-compose.yml). 22 of those CMs had direct code fixes that should have been "Applied". This rule prevents that failure mode.

**STRUCTURAL ENFORCEMENT -- Mandatory Proof Block:**

Before updating ANY CM's status, you MUST output a **CM PROCESSING PROOF** block. This block requires content that can only come from reading the individual SKILL.md file. A batch operation cannot produce these blocks, so the completion gate catches any violation.

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

**Every field is MANDATORY. Generic or empty fields are a contract violation.**

- `Task recipe summary` must reference specific content from the SKILL.md (not generic descriptions)
- `Target files from recipe` must list files mentioned in the SKILL.md task recipe
- `Applicable repo files found` must show evidence of checking the actual repository
- `Justification` must explain why this specific CM is Applied, Documented, or Skipped

**The completion gate (Step 5) MUST verify that a CM PROCESSING PROOF block was output for every processed CM. Missing proof blocks = gate failure.**

---

## Prerequisites

- MCP Client (Cursor IDE, Claude Desktop, or compatible)
- SD Elements MCP server configured
- Target repository with `AGENTS.md` and `skills/{domain}/{cm-slug}/SKILL.md` files

## Completion Criteria

This skill is complete ONLY when:
- [ ] MCP connection verified
- [ ] User inputs **CONFIRMED by user** (handoff values must be confirmed, OR manual questions answered) - **NO AUTO-PROCEEDING**
- [ ] AGENTS.md and skills/ verified to exist in repository
- [ ] ALL scoped countermeasures processed (scoped remaining = 0, or user stopped/declined in interactive modes)
- [ ] Each CODE_FIX/ML_CODE has fix applied to source file
- [ ] Each INFRA countermeasure with applicable config file has fix applied
- [ ] Each ML_DOC/external INFRA is documented in skill file (PROCESS excluded -- already noted by generate-security-skill-files)
- [ ] Countermeasure audit note posted in SD Elements (Notes section) for EACH processed countermeasure
- [ ] Verification block shows MATCH = YES (for `one_by_one` mode, the session summary printed at end of Step 3 loop replaces the standard verification block — see Step 5.2)
- [ ] No `*_secure.*` or similar files exist
- [ ] **`.sde-apply-handoff.json` written to repository root AND passed Step 6.5.6 strict validation** (all 10 required top-level keys, all 6 required per-CM keys, no extra keys, `full_id` matches, `files_modified` per-CM only, counts match, `handoff_version == "2"`) **-- written in Step 6.5, BEFORE Step 7 cleanup**
- [ ] **`.sde-handoff.json` (the upstream generate-security-skill-files handoff) was NOT modified or deleted -- Step 6.5 invariant**
- [ ] Cleanup option selected by user (remove section / keep merged / keep all) — Step 7.3
- [ ] Generated spec files cleaned up (security/, skills/ directories removed)
- [ ] NO fixes skipped due to "intentionally vulnerable" rationalization
- [ ] ALL vulnerability markers removed (`vuln-code-snippet`, `VULNERABLE`, etc.)
- [ ] AI config files restored from archive (if archive existed)

**Output on completion:**

> **PRECONDITION — do NOT emit this block or `✅ SKILL COMPLETE` until the Step 5 scoped gate passes (`{A + D + S} == expected`, where `expected = file_tracked` on `scope=all`, else `scoped_total`).** In `one_by_one`/`single_cm` each per-CM `ask_question` ENDS the turn; on the user's reply you MUST continue to the NEXT scoped CM (re-derive the done-set from the AGENTS.md ledger on resume — never restart, never finalize). Processing ONE CM is NEVER completion; the only sanctioned pause is a CONTEXT CHECKPOINT.

```
=== COMPLETION VERIFICATION ===
Skill: apply-security-fixes
Total countermeasures: {N}
PROCESS (note-only, excluded from this skill): {process_count}
File-tracked countermeasures: {file_tracked}
Applied (CODE_FIX + ML_CODE + INFRA with files): {A}
Documented (ML_DOC + external INFRA): {D}
Skipped: {S}
Sum: {A + D + S}
Expected: {file_tracked} (or scoped_total when scope != all — see Step 5)
Match: {A + D + S} == {expected}? YES

SD Elements notes: {notes_added}/{file_tracked} added ({notes_failed} failed)

Cleanup:
- security/ directory: REMOVED
- skills/ directory: REMOVED

AI config restored: ✓ ({N} files restored / no archive)
===============================

✅ SKILL COMPLETE: All scoped fixes applied
- Applied: {A} countermeasures
- Documented: {D} countermeasures
- PROCESS (note-only, handled by generate-security-skill-files): {process_count}
- Notes added: {notes_added}/{file_tracked} in SD Elements
- Skipped: {S} countermeasures
- Total: {A + D + S}/{expected} (100%)
- Spec files: CLEANED UP
- Handoff file: .sde-apply-handoff.json written (for code-scan-verification-validation)
- Upstream handoff (generate-security-skill-files): .sde-handoff.json preserved

Ready for: @sde-skills/code-scan-verification-validation
```

---

## CONTRACT BOOTSTRAP (MANDATORY FIRST ACTION -- do this before Step 0)

> **Why:** This contract (SKILL.md + AGENTS.md) is large and WILL be partially evicted from your context during a long, multi-session run. A pinned on-disk copy is the durable source of truth you re-read at every step and every batch. If you skip this you WILL drift to memory and improvise (wrong endpoints, skipped CMs, invented results). Do not skip it.

**B0. Fresh-run cleanup vs resume (decide FIRST).** Determine whether this is a NEW apply run or a RESUME/continuation. This skill always CONSUMES the upstream `.sde-handoff.json` produced by `generate-security-skill-files` (`stage: "skill-files-generated"`; legacy: setup-security-plan-from-repo / create-security-plan-from-specs) -- **NEVER delete, rename, or overwrite `.sde-handoff.json`** (the Step 6.5 invariant); the apply-fixes handoff goes to the distinct `.sde-apply-handoff.json`.
- **NEW apply run:** this skill writes its OWN scratch under the namespaced path `.sde-security/apply/...` (e.g. `.sde-security/apply/<project_id>/`). Clear ONLY that apply-owned path (plus a stale root-level `.sde-apply-handoff.json`), or namespace it per `project_id`. **MUST NOT delete `.sde-security/cm-work/` or `.sde-security/library-lookup/`** — those are created by the upstream `generate-security-skill-files` skill and are inputs to this run. **MUST NOT delete `.sde-handoff.json`.** Leave the upstream `.sde-handoff.json` and all upstream `.sde-security/` subdirectories UNTOUCHED.
- **RESUME:** keep all prior artifacts -- they are your durable state; resume from disk.
- Also: the security branch may ALREADY exist from the prior skill -- do NOT assume the repo is on `main`; switch to / stay on the existing security branch (Step 1 git handling) rather than creating a new one.
(Reading/writing/removing these files is mechanical IO and is explicitly allowed.)

**B1. Fetch the EXACT served contract for THIS skill** (not your memory of it): call MCP `prompts op=get prompt=apply-security-fixes`.

**B2. Pin it to disk VERBATIM** (create dirs; do NOT paraphrase/summarize):
- `.sde-security/contract/apply-security-fixes/SKILL.md`
- `.sde-security/contract/apply-security-fixes/AGENTS.md`
- If the served text concatenates both files with `==== <name> BEGIN/END ====` markers, split on those markers and write each separately.

**B3. Record a manifest** at `.sde-security/contract/apply-security-fixes/manifest.json`:
`{ "skill": "apply-security-fixes", "fetched_at": "ISO8601", "sha256_skill": "...", "sha256_agents": "...", "skill_chars": N, "agents_chars": N }`

**B4. Staleness / integrity check (WARN -- do NOT deadlock):** The contract text you were GIVEN to execute for this run is authoritative -- pin THAT. `prompts op=get` is only a convenience for obtaining verbatim text. If it errors, returns empty, or returns text that does NOT contain this `CONTRACT BOOTSTRAP` section, the served MCP prompt is STALE/behind the contract you are executing -- emit `[WARN] served MCP prompt appears stale (missing CONTRACT BOOTSTRAP); rebuild+reload recommended` and pin from the BEST available verbatim source, in order: (1) the served text IF it contains this section; (2) the on-disk skill source if you can locate it; (3) the contract text you were given to execute. Then PROCEED with the run. Only HARD STOP if you cannot obtain the contract text from ANY source. (Reading/writing these files is mechanical IO and is explicitly allowed.)

**B5. Emit:** `[CONTRACT PINNED] skill=apply-security-fixes | path=.sde-security/contract/apply-security-fixes/ | SKILL chars={n} sha256={short} | AGENTS chars={n}`

### STEP PREFLIGHT CONVENTION (applies to EVERY step and EVERY batch)

The pinned copy -- NOT your memory -- is the source of truth for how to execute each step.

- **Before each step:** reload that step's section from `.sde-security/contract/apply-security-fixes/SKILL.md` (read ONLY that step's heading->next-heading range -- context-light), THEN emit the step's `[STEP] entering ...` line. That line MUST include: `reloaded §{step} from disk? YES | sentinel: "{a verbatim line copied from that step's section on disk}"`. You cannot produce the correct sentinel without having re-read the section.
- **Heavy/looping steps** (survey fill, classification, PROCESS notes, library lookup, file/spec generation, apply loop): the step text is evicted MID-step as the loop runs, so ALSO reload that step's section from disk **at every batch boundary**, and include `reloaded §{step} from disk? YES | sentinel: "{verbatim line}"` in that batch's RUNNING CHECK line.
- A missing or incorrect sentinel = you are running from memory = CONTRACT VIOLATION. STOP and reload from disk.

---

## Step 0: AI Code Analysis (DO THIS FIRST - BEFORE EVERYTHING)

**This step happens BEFORE MCP connection. BEFORE handoff detection. BEFORE anything else.**

### 0.0 Why AI Analysis First

You must know what vulnerabilities exist BEFORE you start the fixing process. This prevents:
- Missing files that have vulnerabilities
- Skipping unmarked vulnerabilities
- Incomplete fixes

> **GREENFIELD MODE (handoff `evidence_source == "specs"`).** When the handoff detected in Step 0.5 has `evidence_source == "specs"` (produced by `generate-security-skill-files` from a `create-security-plan-from-specs` survey), OR legacy `source_skill == "create-security-plan-from-specs"`, OR the skill files are **Format C** — "Spec Context" + "Secure Implementation Pattern" — see Step 3.1, the repository is a **freshly scaffolded placeholder**, not existing vulnerable code. In that case:
> - **Step 0 master vuln list is expected to be EMPTY or near-empty** — that is correct, NOT a failure. Do not invent vulnerabilities to fill it.
> - **Step 3.1 CODE_FIX means "implement the Secure Implementation Pattern into the placeholder file"**, not search-and-replace of vulnerable code.
> - **Step 3.5 cross-surface parity is N/A** (no pre-existing vulnerable surfaces to keep in parity) — record `Additional surfaces found: 0 (greenfield)` and proceed.
> - **Step 5.6 marker deletion is N/A** (placeholders contain no `vuln-code-snippet` markers).
>
> **Sequencing note:** Step 0 runs BEFORE handoff detection (Step 0.5), so you will not yet know `evidence_source` when you build the master vuln list. That is fine — a greenfield scaffold naturally yields an empty/near-empty Step 0 list. Do NOT force-fill it; once Step 0.5 confirms `evidence_source == "specs"` (or legacy `source_skill == "create-security-plan-from-specs"`), reconcile by treating that empty list as expected (not a failure) and applying the greenfield rules above.
>
> Brownfield mode (handoff `evidence_source == "codebase"`, legacy upstream = `setup-security-plan-from-repo`, or no handoff) keeps the full vulnerability-centric behavior below.

### 0.1 Get Repository Path

Ask the user:
> "What is the path to the repository I should analyze for vulnerabilities?"

### 0.2 List All Source Files

Use the list_dir tool recursively or find command to get all source files. **This skill is language-agnostic — do NOT hardcode JS/TS extensions.** Determine the relevant extensions from the actual repository and the upstream handoff tech stack:
- **Ordering note:** Step 0 runs BEFORE Step 0.5 (handoff detection), so the handoff tech stack is normally NOT yet loaded here. If the handoff has not been detected yet at Step 0, use repo auto-detection (manifests + predominant source extensions) to choose extensions now, then REFINE the extension set after Step 0.5 loads the handoff tech stack (re-list any additional source files the refined extensions reveal).
- If a handoff (`.sde-handoff.json` / `.sde-apply-handoff.json`) is present, use its tech-stack / language fields to drive which extensions to include (e.g., Python repo → `.py`; Go → `.go`; Java → `.java`; Ruby → `.rb`; JS/TS → `.ts/.js/.tsx/.jsx`; etc.).
- Otherwise, detect languages from the repo itself (manifest files like `requirements.txt`, `pyproject.toml`, `go.mod`, `pom.xml`, `Gemfile`, `package.json`, and the predominant source extensions present).
- When in doubt, include **all source files** and let the AI analysis in Step 0.3 decide relevance.
- Exclude vendored/build dirs: `node_modules/`, `dist/`, `build/`, `.git/`, `vendor/`, `.venv/`, `venv/`, `target/`, `__pycache__/`.

### 0.3 AI Analysis of EACH File (REQUIRED)

For EACH source file, you MUST:

1. **READ the entire file** using `read_file` tool
2. **ANALYZE the code** with your AI understanding - look for:
   
   | Category | What AI Should Look For |
   |----------|-------------------------|
   | **Injection** | String concatenation in queries, user input in commands |
   | **XSS** | `bypassSecurityTrust*`, `innerHTML`, unsanitized output |
   | **Code Execution** | `eval()`, `vm.run()`, `Function()`, `new Function()` |
   | **Weak Crypto** | `MD5`, `SHA1` for passwords, `Math.random()` for security |
   | **Secrets** | Hardcoded API keys, passwords, tokens in code |
   | **Redirects** | Unvalidated URLs in redirects |
   | **File Access** | Path traversal (`../`), unvalidated file paths |
   | **Auth Issues** | Missing auth checks, privilege escalation |
   | **Markers** | `vuln-code-snippet`, `VULNERABLE`, `INSECURE`, `intentional` |

3. **DOCUMENT each finding** with:
   - File path
   - Line number(s)
   - Vulnerability type
   - Severity (HIGH/MEDIUM/LOW)
   - Whether it has a marker (to DELETE)

### 0.4 Create Master Vulnerability List

```
=== STEP 0: AI CODE ANALYSIS COMPLETE ===
Repository: {path}
Files analyzed: {count}
Method: AI semantic analysis (NOT grep)

MASTER VULNERABILITY LIST:

1. {file}:{line} - {type} [{severity}]
   Issue: {AI explanation}
   Marker: {yes/no - DELETE if yes}

2. {file}:{line} - {type} [{severity}]
   Issue: {AI explanation}
   Marker: {yes/no}

... (list ALL findings)

SUMMARY:
- Files with vulnerabilities: {N}
- Total vulnerabilities: {M}
- Markers to DELETE: {K}

FILES TO PROCESS (checklist):
□ {file1}: {count} issues
□ {file2}: {count} issues
...
===========================================
```

### Step 0 Checkpoint (0.C)

```
[STEP 0 COMPLETE] AI analysis: {N} files analyzed, {M} vulnerabilities found, {K} markers to DELETE
```

**You CANNOT proceed to Step 1 (MCP) until Step 0 is complete.**

---

## Step 1: Verify MCP Connection

### 1.1 Detect MCP Client

Determine which client is running this skill:

- Check if `user_info` mentions "Cursor" → **Cursor IDE**
- Check workspace path patterns (`.cursor/` directories) → **Cursor IDE**
- Check for Claude Desktop environment → **Claude Desktop**
- If unable to determine → **Unknown client**

### 1.2 Check Server Availability

Call `test_connection` or `business_unit` op `list`.

- **If successful**: Proceed to Step 0.5
- **If fails with "tool not found"**: MCP server not installed, provide installation guide
- **If fails with auth error**: Guide user to check credentials

### 1.3 Installation Guide (if needed)

**For Cursor IDE:**
```json
{
  "mcpServers": {
    "sdelements": {
      "command": "npx",
      "args": ["-y", "github:sdelements/sde-mcp"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**For Claude Desktop:**
Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows) with the same configuration.

---

## Step 0.5: Detect Handoff Data

**Why this step exists:** Each skill runs in a new agent context with no conversation history. The previous skill may have written a handoff file to pass data.

### 0.5.1 Check for Handoff File

```python
# Scan workspace for directories containing .sde-handoff.json
handoff_data = None
for dir in list_dir("."):
    handoff_path = f"{dir}/.sde-handoff.json"
    try:
        handoff = read_file(handoff_path)
        handoff_data = json.loads(handoff)
        break
    except:
        continue
```

**If handoff file found AND `source_skill` is one of `"generate-security-skill-files"`, `"setup-security-plan-from-repo"`, or `"create-security-plan-from-specs"`:**

> **NOTE — handoff producer.** In the current skill chain the handoff consumed here is written by `@sde-skills/generate-security-skill-files` (`stage: "skill-files-generated"`). The legacy combined skills (`setup-security-plan-from-repo` / `create-security-plan-from-specs`) are accepted for backward compatibility. Determine greenfield vs brownfield from the `evidence_source` field (`"specs"` → greenfield, `"codebase"` → brownfield); fall back to `source_skill == "create-security-plan-from-specs"` or Format C skill files when `evidence_source` is absent.

1. Load all values from handoff:
   - `repository_path`
   - `project_id`, `project_name`
   - `business_unit_id`, `application_id`
   - `risk_policy_id` (may be null if not set)
   - `evidence_source` (`codebase` | `specs` — drives greenfield/brownfield mode)
   - `agents_md`, `skill_files` (per-file paths `skills/{domain}/{CM_ID}-{tech-slug}/SKILL.md`; a CM may have MULTIPLE files — Fix E)
   - `security_branch` (the branch generate-security-skill-files created; null if no git)
   - `ai_backup_archive` (path to the archived AI config, for Step 7.5 restore; null if none)
   - `total_countermeasures`

2. Verify files still exist:
   ```python
   if not exists(handoff_data["agents_md"]):
       # File missing, fall back to manual input
       continue_to_step_1_5()
   ```

3. **ALWAYS ask user to confirm (MANDATORY - NEVER SKIP):**
   - **Prompt**: "Found handoff from previous skill. Use these values?"
   - **Options**:
     - `{"id": "use_handoff", "label": "Yes, use: {repository_path} (Project: {project_name})"}`
     - `{"id": "manual", "label": "No, I'll provide different values"}`
   - **Wait for user response** - do NOT auto-proceed even if handoff looks valid

4. **If user confirms**: 
   - Store all values
   - Output: `[CHECKPOINT] Handoff: LOADED from .sde-handoff.json (USER CONFIRMED)`
   - Skip to Step 2 (verify spec files)

5. **If user declines**: Continue to Step 1.5 (full questions)

**CRITICAL:** You MUST wait for user response. Never assume they want to use handoff data.

**If handoff file not found:** Continue to 0.5.2

### 0.5.2 Auto-Detect Repositories (Fallback)

Scan workspace for directories containing `AGENTS.md` + `skills/`:

```python
candidates = []
for dir in list_dir(workspace_root):
    if is_directory(dir):
        agents_path = f"{dir}/AGENTS.md"
        skills_path = f"{dir}/skills/"
        if exists(agents_path) and exists(skills_path):
            candidates.append(dir)
```

**If exactly ONE candidate found:**
- **ALWAYS ask the user (MANDATORY)**: "Found repository with spec files at `{path}`. Use this?"
- **Options**:
  - `{"id": "use_detected", "label": "Yes, use {path}"}`
  - `{"id": "manual", "label": "No, I'll choose a different repository"}`
- **Wait for user response** - do NOT auto-proceed
- **If user confirms**:
  - Store `repository_path = candidate`
  - Output: `[CHECKPOINT] Handoff: DETECTED from scan (USER CONFIRMED)`
  - Continue to Step 1.5 Question 2 (project selection only)

**If MULTIPLE candidates found:**
- Ask: "Multiple repositories with spec files found. Select one:"
- **Options**: Each candidate as an option
- Store selected as `repository_path`
- Output: `[CHECKPOINT] Handoff: DETECTED from scan (user selected)`
- Continue to Step 1.5 Question 2 (project selection only)

**If NO candidates found:**
- Output: `[CHECKPOINT] Handoff: NOT FOUND - manual input required`
- Continue to Step 1.5 (full question flow)

### 0.5.3 Handoff Detection Summary

| Detection Result | Next Step | Questions Skipped |
|-----------------|-----------|-------------------|
| Loaded from `.sde-handoff.json` | Step 2 | All (repo + project) |
| Detected via scan (single) | Step 1.5 Q2 | Repository only |
| Detected via scan (multiple) | Step 1.5 Q2 | Repository only |
| Not found | Step 1.5 Q1 | None |

---

## Step 1.5: Gather User Inputs (Conditional)

**Skip this step ONLY if handoff was loaded from file AND user explicitly confirmed they want to use those values.**

> **⚠️ CRITICAL - USER CONFIRMATION IS MANDATORY**
>
> Even when handoff data exists, the user MUST explicitly confirm before proceeding.
> **NEVER** auto-proceed with detected values without asking the user first.

Ask questions **one at a time**, validate each answer before proceeding.

### Question 1: Repository Selection (MANDATORY - ALWAYS ASK)

**You MUST ask this question - do not skip even if context seems obvious.**

1. Call `list_dir` on workspace root to get directories
2. **ALWAYS ask the user** using `ask_question`:
   - **Prompt**: "Which repository would you like to apply security fixes to?"
   - **Options**: Each subdirectory + `{"id": "manual", "label": "Enter path manually"}`
3. **Wait for user response** - do not proceed without it
4. Validate the path exists
5. Store as `repository_path`

### Question 2: Project Mode (MANDATORY - ALWAYS ASK)

**You MUST ask this question - never assume the user wants to create or use existing.**

**ALWAYS ask the user** using `ask_question`:
- **Prompt**: "SD Elements project for cross-reference:"
- **Options**:
  - `{"id": "create_new", "label": "Create new SD Elements project"}`
  - `{"id": "use_existing", "label": "Use existing SD Elements project"}`
- **Wait for user response** - do not proceed without it
- Store as `project_mode`

### Question 3a: Business Unit Selection (if creating new) (MANDATORY - ALWAYS ASK)

**You MUST ask this question even if only one business unit exists.**

1. Call `business_unit` with `op: "list"`
2. **ALWAYS ask the user** using `ask_question`:
   - **Prompt**: "Select the Business Unit for the new project:"
   - **Options**: Each BU + `{"id": "create_new_bu", "label": "Create a new Business Unit"}`
3. **Wait for user response** - do not auto-select
4. If "create_new_bu" selected, prompt for name and call `business_unit` with `op: "create"`
5. Store as `business_unit_id` and `business_unit_name`

### Question 3b: Existing Project Selection (if using existing) (MANDATORY - ALWAYS ASK)

**You MUST ask this question - do not auto-select a project.**

1. Call `project` with `op: "list"` and `page_size: 100`
2. **ALWAYS ask the user** using `ask_question`:
   - **Prompt**: "Select the SD Elements project to cross-reference countermeasures:"
   - **Options**: Each project with `{"id": "[project_id]", "label": "[project_name] (ID: [project_id])"}`
3. **Wait for user response** - do not proceed without it
4. Validate with `project` op `get`
5. Store as `project_id` and `project_name`
6. Skip to Step 2

### Question 4: Application Selection (if creating new) (MANDATORY - ALWAYS ASK)

**You MUST ask this question - do not auto-select an application.**

1. Call `application` with `op: "list"` to retrieve applications in the selected business unit
2. **ALWAYS ask the user** using `ask_question`:
   - **Prompt**: "Select or create an Application for the new project:"
   - **Options**:
     - For each application: `{"id": "[app_id]", "label": "[app_name]"}`
     - Add option: `{"id": "create_new_app", "label": "Create a new Application"}`
3. **Wait for user response** - do not proceed without it
4. If "create_new_app" selected:
   - Prompt for application name (suggest repository name as default, but **ask user to confirm**)
   - Call `application` with `op: "create"`, `name`, and `business_unit_id`
5. Store as `application_id` and `application_name`

### Question 5: Project Name (if creating new) (MANDATORY - ALWAYS ASK)

**You MUST ask this question - do not use a default name without user confirmation.**

1. Suggest repository directory name as default
2. **ALWAYS ask the user** using `ask_question`:
   - **Prompt**: "Enter a name for the new SD Elements project:"
   - **Options**: Suggested name + custom option
3. **Wait for user response** - do not use default without explicit confirmation
4. Check for duplicate names with `project` op `list`
5. If duplicate exists, offer: use existing, use suggested alternative, or enter custom
6. Store as `project_name`
7. Call `project` with `op: "create"` to create the project
8. Store returned `project_id`

### Stored Configuration

After completing handoff detection and/or questions **(each confirmed or answered by user, not assumed)**, you should have:

- `repository_path` → Target repository with spec files **(USER CONFIRMED)**
- `project_mode` → "create_new" or "use_existing" (or "from_handoff" if loaded) **(USER CONFIRMED)**
- `business_unit_id` + `business_unit_name` → (if creating new or from handoff) **(USER CONFIRMED)**
- `application_id` + `application_name` → (if creating new or from handoff) **(USER CONFIRMED)**
- `project_id` + `project_name` → SD Elements project for cross-reference **(USER CONFIRMED)**
- `handoff_source` → "file" | "scan" | "manual"
- `git_enabled` → true/false (whether git is initialized in repo)
- `security_branch` → Branch name for security changes (if git enabled)

**If any of these values were assumed rather than explicitly confirmed by the user, GO BACK and ask the user.**

**Output checkpoint:**
```
[CHECKPOINT] Inputs gathered:
- Repository: {repository_path}
- Project: {project_name} (ID: {project_id})
- Source: {handoff_source}
```

---

## Step 2: Verify Specification Files Exist

Before proceeding, verify that the required specification files exist in the selected repository.

### 2.0 Handle Security Branch (Git Operations)

**If handoff was loaded with `git_enabled = true` and `security_branch`:**

```bash
cd {repository_path}

# Check if we're already on the security branch
CURRENT_BRANCH=$(git branch --show-current)

if [ "$CURRENT_BRANCH" != "{security_branch}" ]; then
    # Switch to the security branch created by the previous skill
    git checkout {security_branch}
fi
```

Output: `[CHECKPOINT] Git: Switched to branch {security_branch}`

**If no handoff OR handoff has no branch info:**

Check if git is initialized and create a branch:

```bash
cd {repository_path}

# Check if git is initialized
if [ -d ".git" ]; then
    git_enabled=true
    
    # Create branch for fixes if not already on a security branch
    CURRENT_BRANCH=$(git branch --show-current)
    if [[ ! "$CURRENT_BRANCH" =~ ^security-hardening/ ]]; then
        BRANCH_NAME="security-hardening/fixes-$(date +%Y%m%d)"
        git checkout -b "$BRANCH_NAME"
        echo "[CHECKPOINT] Git: Created branch $BRANCH_NAME"
    else
        echo "[CHECKPOINT] Git: Already on security branch $CURRENT_BRANCH"
    fi
else
    git_enabled=false
    echo "[CHECKPOINT] Git: NOT INITIALIZED - skipping branch operations"
fi
```

### 2.1 Check for AGENTS.md

```bash
ls {repository_path}/AGENTS.md
```

- **If exists**: Read and extract countermeasure summary
- **If missing**: STOP - run the survey skill (`@sde-skills/setup-security-plan-from-repo` for an existing repo or `@sde-skills/create-security-plan-from-specs` for greenfield) then `@sde-skills/generate-security-skill-files` to produce AGENTS.md + skill files

### 2.2 Check for skills/ Directory

```bash
ls {repository_path}/skills/
```

- **If exists with SKILL.md files**: Continue to Step 2.5
- **If missing or empty**: STOP - run the survey skill (`@sde-skills/setup-security-plan-from-repo` or `@sde-skills/create-security-plan-from-specs`) then `@sde-skills/generate-security-skill-files` to produce the skill files

### 2.3 Validation Output

```
[CHECKPOINT] Specification files verified:
- AGENTS.md: ✓ (found at {repository_path}/AGENTS.md)
- skills/: ✓ ({count} domain skill files found)
```

---

## Step 2.5: Read Generated Specification Files

### 2.5.1 Read AGENTS.md

1. Read `AGENTS.md` at repository root
2. Check for `<!-- SDE-SECURITY-HARDENING-START -->` marker
3. If markers found: extract ONLY the content between `SDE-SECURITY-HARDENING-START` and `SDE-SECURITY-HARDENING-END` for parsing
4. If no markers found: parse entire file (backward compatibility)
5. From the security section, extract:
   - Total countermeasure count
   - List of countermeasure IDs
   - Domain skill file paths (now per-CM: `skills/{domain}/{cm-slug}/SKILL.md`)
   - Progress Tracking table / Countermeasure Index (per-CM format)

### 2.5.2 List All Per-CM Skill Files

```bash
find skills/ -path "skills/*/*/SKILL.md" -type f
```

### 2.5.3 Initialize Tracking

Record `expected_total` = count of all `skills/**/SKILL.md` files on disk (including Format B / library-sourced). Classify each by format (A = template, B = library/amendments with YAML front matter + Decision Table/Gotchas/Quick Verification, C = spec-based).

**The AGENTS.md ledger is the authoritative per-row status/scope source.** Derive the file set AND each file's status and category from the **AGENTS.md ledger rows** (the Countermeasure Index / Progress Tracking table), which covers ALL file-tracked CMs including Format B. Do NOT derive status/category by parsing a per-file `**Status:**` / `**Category:**` field: Format B (library-sourced, byte-exact) SKILL.md files have NO such field, so per-file status parsing silently drops them. Each ledger row maps to exactly one `skills/**/SKILL.md` file on disk; if a CM's file exists on disk but is missing from the ledger, add its row (reconciliation, Step 2.6).

> **MULTIPLE FILES PER CM (Fix E, from `generate-security-skill-files`).** A single countermeasure may have MORE THAN ONE skill file when the SDE library matched it for multiple technologies — e.g. `skills/{domain}/T1541-python/SKILL.md` AND `skills/{domain}/T1541-javascript/SKILL.md`. There is **one ledger row per FILE** (same CM `ID`, distinct Skill File path). When processing: APPLY each file (each carries its own tech-specific secure pattern). But the per-CM **SDE note** and the `.sde-apply-handoff.json` `countermeasures[]` entry remain **ONE per CM** (`full_id` is unique) — aggregate that CM's `files_modified` across all of its files and post a single note. So: rows/files denominator = `expected_total` (file count); CM-entry denominator = unique CM IDs.

```
[CHECKPOINT] Total countermeasures from AGENTS.md: {N}
expected_total SKILL.md files on disk: {expected_total} (Format A: {a}, Format B/library: {b}, Format C: {c})

Domains to process:
- {domain1}: {count} countermeasures
- {domain2}: {count} countermeasures
...

Initializing: Applied=0, Documented=0, Skipped=0, Remaining={N}
```

---

## Step 2.6: Reconciliation on Resume

When resuming from a checkpoint or re-running the skill, reconcile statuses. **The AGENTS.md ledger is the authoritative per-CM status/scope source — NOT the per-file `**Status:**`.** Format B (library-sourced, byte-exact) SKILL.md files have NO in-file Status/Category field — never expect one — their status lives ONLY in the ledger.

1. Enumerate the AGENTS.md ledger rows (the per-file index table; a CM may have multiple rows — Fix E) — these are authoritative and cover ALL file-tracked CMs (Format A, B, and C). Each row's Status column is that file's status; all rows of one CM share the CM's terminal status.
2. List ALL `skills/*/*/SKILL.md` files on disk. Every disk file MUST have a ledger row; if a file exists with no row, add its row (default Status `Pending`). Do NOT require a per-file `**Status:**` anchor — Format B files do not have one, and that is NOT a missing-status error.
3. For files that DO carry an in-file `**Status:**` anchor (Format A / Format C / template), if the in-file anchor disagrees with the ledger row, **the ledger wins**: update the in-file anchor to match the ledger row.
4. **Auto-skip (treat as already done) ONLY CMs whose ledger Status is `Applied` or `Skipped`.**
5. For CMs whose ledger Status is `Documented`: if the CM is an **INFRA** CM, RE-RUN the Step 3.2 INFRA file-inventory pre-check. **REOPEN the CM** — set its ledger Status back to `Pending` so the "INFRA default = APPLIED when config exists" rule (Step 3.2 / Step 4) is honored on this run — **ONLY when the CM's own RECIPE/text references an in-repo config surface that ACTUALLY EXISTS in the repo** (i.e. the CM names a config the repo has, e.g. Dockerfile / docker-compose.yml / .dockerignore / server.ts). Do NOT reopen a Documented INFRA CM merely because SOME config file exists somewhere in the repo — match the CM's *referenced* config surface to a present in-repo file, otherwise the reopen is repo-level-coarse and reopens unrelated INFRA CMs (reopen churn). Genuinely out-of-repo INFRA CMs (DNS / LB / WAF / TLS-inspection / LLM-provider settings and the like, whose mitigation lives outside this repo) remain `Documented`. Documented non-INFRA CMs (and Documented INFRA CMs whose referenced config surface is not present in the repo) remain done and are skipped.

---

## Step 2.7: Select Apply Scope

Present the inventory and ask the user to choose a scope.

### 2.7.1 Inventory Summary

```
=== APPLY SCOPE SELECTION ===
Total countermeasures: {N}
Already done: {X} (Applied/Documented from previous runs)
Remaining to process: {N-X}

Domains:
  1. {domain1} ({total} CMs, {done} done, {remaining} remaining)
  2. {domain2} ({total} CMs, {done} done, {remaining} remaining)
  ...
```

### 2.7.2 Scope Selection

Ask via `ask_question` -- four options:
- `{"id": "all", "label": "Apply ALL countermeasures at once"}`
- `{"id": "domain", "label": "Apply fixes for one specific domain"}`
- `{"id": "single_cm", "label": "Apply fix for one specific countermeasure"}`
- `{"id": "one_by_one", "label": "Walk through CMs one at a time (approve each individually)"}`

### 2.7.3 Scope Refinement

- For `domain`: present domain list, user picks one, filter CMs to that domain
- For `single_cm`: present CM list grouped by domain, user picks one
- For `all` or `domain`: present batch execution plan (below), wait for confirmation:

```
=== EXECUTION PLAN ===
Scope: {all / domain: {name}}
Total in scope: {scoped_total}
Already done: {already_done}
To process this run: {to_process}

Plan:
  1. {ID}: {title} [{category}] -> {APPLY/DOCUMENT}
  2. {ID}: {title} [{category}] -> {APPLY/DOCUMENT}
  ...
  (Already done CMs are excluded from this list)

Proceed? (yes/no)
```

- For `all`/`domain`: if the user answers `no` to the batch plan → clean non-error abort — emit `[ABORT] User declined the batch plan; no countermeasures processed.` and STOP (apply no fixes, write no handoff, make no commit). A declined plan is a valid terminal, NOT an error or an incomplete run.
- For `single_cm`: present individual CM plan (same format as one-by-one below) with `yes/no` only (no skip)
- For `one_by_one`: enter guided walkthrough mode (Step 3 handles this)

Store as `scope`, `selected_domain` (if domain), `selected_cm_id` (if single_cm).

---

## Step 2.8: Partition Scoped CMs into Batches (MANDATORY for scope=all and scope=domain)

For `scope=all` and `scope=domain`, partition the scoped CMs into batches BEFORE entering the Step 3 loop. (For `single_cm` there is one CM -- no partition needed. For `one_by_one` the user controls pacing -- no partition needed, but Rule 5 "No Stopping Early" still applies.)

Divide scoped CMs into batches of 20 (aligned with the Composite API limit and the config skills). Output the batch plan:

```
=== FIX APPLICATION BATCH PLAN ===
scoped_total: {N}
Batch size: 20
Total batches: {ceil(N/20)}

Batch 1/{total}: {CM_ID_1}, ... {CM_ID_20}
Batch 2/{total}: {CM_ID_21}, ... {CM_ID_40}
...
Batch {total}/{total}: {CM_ID_last_batch_start}, ... {CM_ID_N}
================================
```

This batch plan is your execution contract. Step 3 works through it sequentially -- one batch at a time, in order, with a per-batch mini-gate after each.

---

## Step 3: Process Countermeasures (Scoped)

> **SCALE IS EXPECTED.** This step processes one CM at a time: read SKILL.md, apply fix,
> update ledger, post SDE note. For a typical project this means 50-500 individual CM
> processing cycles. This is NORMAL and EXPECTED -- it is NOT "too many CMs," NOT a
> reason to apply only "critical" fixes, and NOT a reason to batch-classify categories.
> Budget 30-90 minutes for this step.
>
> **DEPTH OVER BREADTH:** Processing each CM individually with its proof block is more
> important than reaching the completion gate quickly. Do NOT rationalize skipping CMs
> to "focus on the important ones." If context limits approach, emit a CONTEXT CHECKPOINT.

**For `scope=all` and `scope=domain`, work through the Step 2.8 batch plan one batch at a time.** For EACH batch:

1. Output: `[BATCH START] Fix application batch {B}/{total}: {list the CM IDs in this batch}`
2. Process EACH CM in the batch through the per-CM procedure below (full proof block, ledger write-through, SDE note).
3. After the batch's CMs are all processed, output the per-batch mini-gate:

```
--- BATCH {B}/{total} COMPLETE ---
CMs in batch: {batch_size}
Applied: {a}, Documented: {d}, Skipped: {s}
Proof blocks emitted in this batch: {count}
BATCH PASS: {count} == {batch_size}? {YES/NO}
Running total: {cumulative}/{scoped_total}
---
```

   Then emit the cumulative RUNNING CHECK. **Two denominators (Fix E):** CM progress uses `scoped_total` (unique CMs); the terminal-status FILE count uses `expected_total` (total skill files/ledger rows — a CM with N files flips N rows). Count files via shell, NOT in-context:
```
[RUNNING CHECK] CMs done {cumulative}/{scoped_total} | terminal-status SKILL.md files {disk_count}/{expected_total} | batches {B}/{total} | on track? {YES/NO} | reloaded this step from disk? {YES} | sentinel: "{verbatim line from this step's section in .sde-security/contract/<skill>/SKILL.md}"
```
   If "on track" is NO, a prior batch under-produced -- STOP and reconcile before continuing.

4. If BATCH PASS = NO: process the missing CMs in THIS batch, then re-run the mini-gate. Do NOT move on until BATCH PASS = YES.
5. If BATCH PASS = YES: proceed to the next batch.

**SAMPLING LANGUAGE = IMMEDIATE STOP.** If ANY of the following phrases appear in your reasoning about this loop's scope, you are sampling. STOP immediately, discard the conclusion, return to the BATCH PLAN, and process every remaining CM:
- "key CMs" / "across all categories" / "across categories"
- "the pattern is clear" / "the rest have" / "the rest are"
- "only N CMs need fixes... the rest" / "only N CMs..."
- "applied N+ fixes" or any "N+" summary standing in for full coverage
- "Let me finalize" before the loop is complete
- "representative" / "pragmatic" / "efficient" (in the context of loop scope)
The count of individually processed CMs (with per-CM proof blocks and terminal-status SKILL.md files on disk) is the ONLY basis for the APPLY COMPLETENESS AUDIT.

**PROCESS countermeasures are excluded** -- they have no skill files (already noted in SD Elements by the generate-security-skill-files). Only CODE_FIX, ML_CODE, ML_DOC, and INFRA countermeasures appear in the processing loop.

**MANDATORY PATTERN:**

```python
# Filter CMs by selected scope, EXCLUDING already-done CMs.
# PROCESS CMs have no skill files -- they were noted in SD Elements by generate-security-skill-files.
#
# AUTHORITATIVE SOURCE = the AGENTS.md ledger rows. Derive the file set AND each row's
# status + category FROM THE LEDGER ROWS (the per-file index table), which cover ALL
# file-tracked CMs including Format B. Do NOT derive status/category from a per-file
# `**Status:**` / `**Category:**` field: Format B (library-sourced, byte-exact) files
# have NO such field, so per-file status parsing silently DROPS them.
ledger_rows = parse_agents_md_ledger_rows()   # ONE row per skill FILE: id, domain, skill_file, category, status
#
# ⚠️ MULTIPLE FILES PER CM (Fix E): generate-security-skill-files may emit MORE THAN ONE
# skill file for a single CM (one per matched library technology, `{CM_ID}-{tech-slug}`),
# so a CM can have MULTIPLE ledger rows. GROUP the rows by CM id: each CM = {id, category,
# status, files: [skill_file per row]}. A CM is "Pending" if ANY of its rows is Pending.
cms_by_id = group_rows_by_cm_id(ledger_rows)   # {cm_id: {id, category, status, files:[...]}}
pending_cms = [cm for cm in cms_by_id.values() if any(row Pending for that cm)]

if scope == "all":
    scoped_cms = pending_cms
elif scope == "domain":
    scoped_cms = [cm for cm in pending_cms if cm.domain == selected_domain]
elif scope == "single_cm":
    scoped_cms = [cm for cm in pending_cms if cm.id == selected_cm_id]
elif scope == "one_by_one":
    scoped_cms = pending_cms  # All pending, processed with individual approval

# TWO denominators (Fix E):
scoped_total = len(scoped_cms)            # unique CMs in scope -> ONE note + ONE handoff entry each
expected_total = len(ledger_rows)         # total skill FILES/rows -> file/ledger/proof checks
# Each scoped CM: APPLY EVERY file in cm.files (each carries its own tech-specific pattern),
# then emit ONE audit_records entry per CM with files_modified = union across its files,
# and ONE SDE note per CM. NEVER one note/entry per file.
applied = 0
documented = 0
skipped = 0
notes_added = 0
notes_failed = []
pending_notes = []   # accumulates per-batch notes; flushed via ONE composite call at each batch boundary
done = 0

# Audit trail for Step 6.5 handoff to code-scan-verification-validation.
# This list MUST be appended to inside the loop for every processed CM
# (including skipped ones in one_by_one) so the handoff captures the
# per-CM record. The schema is intentionally minimal: title, domain,
# fix text, etc. are live-fetchable from SDE by code-scan-verification-validation.
# We persist what SDE cannot reconstruct (local-only identifiers, status,
# files_modified, note result) PLUS `category` (saves a subagent launch).
audit_records = []

for cm in scoped_cms:
    # Define once per CM and reuse everywhere (skip path, note-failure cache, audit record).
    full_id = f"{project_id}-{cm.id}"

    # ONE-BY-ONE MODE: present plan and ask before each CM
    if scope == "one_by_one":
        plan = analyze_cm(cm)
        present_cm_plan(plan, done + 1, scoped_total)
        response = ask_question("Apply this fix?", options=["yes", "skip", "stop"])
        if response == "skip":
            update_agents_md_index_rows(cm, "Skipped")  # flip ALL of this CM's ledger rows (Fix E) + in-file status where present
            skipped += 1
            done += 1
            audit_records.append({
                "id": cm.id,
                "full_id": full_id,
                "status": "Skipped",
                "category": cm.category,
                "files_modified": [],
                "sde_note_result": "NOT_SENT",
            })
            output_progress_update(cm, "Skipped", done, scoped_total)
            continue
        elif response == "stop":
            save_checkpoint(done, scoped_cms[done:])
            break

    # SINGLE_CM MODE: present plan and ask yes/no
    if scope == "single_cm":
        plan = analyze_cm(cm)
        present_cm_plan(plan, 1, 1)
        response = ask_question("Apply this fix?", options=["yes", "no"])
        if response == "no":
            save_checkpoint(done, [cm])
            break

    # Process the CM (existing logic)
    if cm.category in ['CODE_FIX', 'ML_CODE']:
        apply_fix(cm)
        new_status = "Applied"
        applied += 1
        note_text = f"[AI-Applied] Fixed in {cm.file_path}: {cm.fix_description}"
    elif cm.category == 'INFRA' and has_config_file(cm):
        apply_infra_fix(cm)
        new_status = "Applied"
        applied += 1
        note_text = f"[AI-Applied] Infrastructure fix applied in {cm.file_path}"
    else:
        verify_documented(cm)
        new_status = "Documented"
        documented += 1
        # Read full Why Not Code-Fixable + Recommended Action sections from the local
        # skill file BEFORE Step 7's `rm -rf skills/` deletes it. This is the only
        # chance to embed that analysis durably into SDE.
        try:
            why_not, recommended = read_doc_sections(f"skills/{cm.domain}/{cm.slug}/SKILL.md")
            note_text = (
                f"[AI-Documented] {cm.doc_reason}\n\n"
                f"== Why Not Code-Fixable ==\n{why_not}\n\n"
                f"== Recommended Action ==\n{recommended}\n\n"
                f"-- Source: skills/{cm.domain}/{cm.slug}/SKILL.md (local artifact, not preserved after this run) --"
            )
        except Exception as e:
            print(f"[WARN] evidence post fallback for {cm.id}: local skill file unreadable ({e})")
            note_text = (
                f"[AI-Documented] {cm.doc_reason}\n\n"
                f"(Note: detailed Why Not Code-Fixable / Recommended Action sections were not "
                f"available from the local skill artifact at post time; refer to the CM's "
                f"`text` and `how_tos` fields in SDE for canonical guidance.)"
            )

    # Step 3.V: Verifiability Gate (scope-match classification)
    # After applying a fix, determine whether the CM's full mitigation scope
    # is verifiable from the modified files alone.  If the CM's problem
    # description (ctx.problem / task recipe) refers to resources that are
    # external to the repository (infrastructure, process controls, privacy
    # policies, third-party services, runtime configuration, etc.), the fix
    # cannot be fully verified by static analysis of `files_modified`.
    # In that case, reclassify from Applied to Documented so downstream
    # code-scan-verification-validation does not produce a misleading `partial` verdict.
    # This assessment is AI-driven and repo/language-agnostic.
    if new_status == "Applied":
        can_fully_verify = ai_assess(
            question=(
                "Can a static analysis tool fully verify this CM's mitigation by "
                "reading ONLY the files in {files_affected}?  Or does the CM's "
                "actual scope extend to resources outside this repository "
                "(infrastructure, runtime config, process controls, "
                "third-party services, organisational policy)?"
            ),
            context=cm.task_recipe_summary,
        )
        if not can_fully_verify:
            new_status = "Documented"
            applied -= 1
            documented += 1
            cm.files_affected = []
            note_text = (
                f"[AI-Documented] Fix applied but scope extends beyond repository files; "
                f"reclassified as Documented for accurate downstream verification.\n\n"
                f"Original fix: {note_text}"
            )

    # Step 3.X: Per-CM Progress Update (MANDATORY for ALL modes)
    # The AGENTS.md LEDGER ROWS are the authoritative status. Update the status for EVERY CM
    # (Pending -> Applied/Documented/Skipped). Fix E: a CM may have MULTIPLE ledger rows
    # (one per skill file / matched tech) -- set the SAME terminal status on ALL of the CM's
    # rows. This is a small per-CM ledger edit (allowed; NOT a batch shell update, Rule 8 intact).
    update_agents_md_index_rows(cm, new_status)           # MANDATORY: flip ALL of this CM's rows
    # ADDITIONALLY update the in-file `**Status:**` ONLY when the file HAS that anchor
    # (Format A / Format C / template). For Format B (byte-exact library) files there is NO
    # `**Status:**` anchor -- do NOT modify the file body (Rule 4); the ledger row is its status.
    if cm_skill_file_has_status_anchor(cm):               # Format A / C / template only
        update_cm_skill_file_status(cm, new_status)       # update in-file **Status:** to match the ledger

    # LEDGER WRITE-THROUGH (per CM) -- re-read from disk to confirm the write landed.
    agents_status_on_disk = re_read_agents_md_row(cm)     # AUTHORITATIVE: re-read AGENTS.md ledger row for this CM
    assert agents_status_on_disk == new_status, \
        f"Ledger write-through failed for {cm.id}: AGENTS.md row={agents_status_on_disk}"
    # For files that carry the in-file anchor, also confirm it matches; Format B has no anchor (skip that check).
    if cm_skill_file_has_status_anchor(cm):
        skill_status_on_disk = re_read_skill_md_status(cm)
        assert skill_status_on_disk == new_status, \
            f"In-file Status write-through failed for {cm.id}: SKILL.md={skill_status_on_disk}"
    # Output the gate:
    # === LEDGER WRITE-THROUGH (per CM) ===
    # {cm_id}: wrote {new_status} -> re-read AGENTS.md row: {value} | in-file Status: {value or "N/A (Format B, no anchor)"}
    # VERIFY: ledger row == {new_status} (and in-file anchor == {new_status} when present)? {YES/NO}
    # =====================================
    # If NO: re-write and re-read; do not advance until YES.
    # The [PROGRESS] line MUST be derived from this read-back, not from memory.

    # Post the audit comment. The note_text is built now (while the local SKILL.md still
    # exists -- Step 7 may delete it later). Transport depends on scope:
    if scope in ("one_by_one", "single_cm"):
        # NO batch boundary exists for these modes (Step 2.8 does not partition them), so POST
        # the note IMMEDIATELY per-CM via op=addNote (see the note-transport rule under Step 3.4).
        resp = project_countermeasures(op="addNote", project_id=project_id,
                                       countermeasure_id=full_id, note=note_text)
        if not resp.ok:   # agent-level retry ONCE with the SAME fully-embedded note_text (see the note-retry rule)
            resp = project_countermeasures(op="addNote", project_id=project_id,
                                           countermeasure_id=full_id, note=note_text)
        # note_status MUST be a VALID_NOTE_RESULTS token (ADDED / FAILED / NOT_SENT) for the Step 6.5
        # handoff schema -- do NOT embed the failure reason here.
        note_status = "ADDED" if resp.ok else "FAILED"
        if note_status == "ADDED":
            notes_added += 1                                  # immediate-post modes MUST increment here (the batch flush @ below only counts batched-mode notes)
        else:
            notes_failed.append({"id": cm.id, "full_id": full_id, "note_text": note_text})
    else:
        # BATCHED modes (scope=all / domain): accumulate for ONE composite POST at the batch
        # boundary (do NOT post inline per CM).
        pending_notes.append({"id": cm.id, "full_id": full_id, "note_text": note_text})
        note_status = "PENDING"   # MUST be finalized to ADDED/FAILED at the batch flush below; assert NO entry is still "PENDING" before Step 6.5 validation (a missed final-partial-batch flush / early break could leave it, and "PENDING" is NOT in VALID_NOTE_RESULTS)

    done += 1

    # MANDATORY: append per-CM record to the handoff audit trail.
    # Schema is minimal by design: code-scan-verification-validation fetches title,
    # domain, text, problem, how_tos, etc. live from SDE via
    # `project_countermeasures op=get`. We persist only what SDE cannot
    # reconstruct -- local identifiers, status, category, files_modified, note result.
    audit_records.append({
        "id": cm.id,
        "full_id": full_id,
        "status": new_status,
        "category": cm.category,
        "files_modified": list(cm.files_affected or []),
        "sde_note_result": note_status,
    })

    # MANDATORY PROGRESS OUTPUT
    print(f"""
=== PROGRESS UPDATE ===
CM: {cm.id} - {cm.title}
Status: Pending -> {new_status}
Progress: {done}/{scoped_total} ({done*100//scoped_total}%)
Remaining in scope: {scoped_total - done}
===
""")
    # Note-status label: batched modes show PENDING (flushed at batch end); one_by_one/single_cm
    # already POSTed above, so show the finalized status.
    _note_label = note_status if scope in ("one_by_one", "single_cm") else "PENDING (flushed at batch end)"
    print(f"[PROGRESS] {done}/{scoped_total} | {cm.id}: {new_status} | Note: {_note_label} | Remaining: {scoped_total - done}")

    # === BATCH NOTE FLUSH (Composite API) ===
    # `pending_notes` holds ONE entry per CM (Fix E: even a multi-file CM contributes a single
    # note whose text summarizes all of that CM's applied files). At each batch boundary
    # (every 20 CMs) AND once after the final partial batch, post ALL accumulated notes with
    # ONE composite call:
    #
    #   Write the composite body to disk, then run the SDE Direct API Access script
    #   (Python/Node reference in the "SDE Direct API Access" section) -- NOT the
    #   api_request MCP tool:
    #     body = {"all_or_none": False, "strict_ref_checking": False,
    #             "composite_request": [
    #               { "method": "POST",
    #                 "path": f"/api/v2/projects/{project_id}/tasks/{n['full_id']}/notes/",
    #                 "reference_id": n['id'],
    #                 "body": { "text": n['note_text'] } }
    #               for n in pending_notes ]}
    #     write body -> notes_body.json
    #     python3 sde_composite.py --input notes_body.json --out notes_resp.json   # (or: node sde_composite.js ...)
    #
    # The script reconciles every reference_id, RETRIES the failed subset ONCE, writes the
    # full response to notes_resp.json, and prints a compact `posted=/failed=` summary (exit
    # non-zero on unresolved failures). Then, from the on-disk notes_resp.json:
    #   - http_status_code 2xx -> notes_added += 1; set that CM's audit_records.sde_note_result = "ADDED"
    #   - otherwise -> append {id, full_id} to notes_failed[]; sde_note_result = "FAILED"
    # Then clear pending_notes = []. Emit a [PROGRESS] note-status update per CM from the response file.

# Report notes the script could not post after its built-in retry (read from the summary + response file).
# Do NOT re-read the local SKILL.md here: by report time, Step 7 may already have deleted it.
if notes_failed:
    print(f"[WARNING] {len(notes_failed)} note(s) could not be posted: {[f['id'] for f in notes_failed]}")
```

### One-by-One CM Plan Format

For each CM in `one_by_one` or `single_cm` mode, present:

```
=== CM PLAN ({current}/{total}) ===
ID: {cm.id}
Title: {cm.title}
Domain: {cm.domain}
Category: {cm.category}
Priority: {cm.priority}
Skill file: skills/{cm.domain}/{cm.slug}/SKILL.md

Analysis:
  - Files affected: {list}
  - Type of change: {description}
  - Risk: {LOW/MEDIUM/HIGH} ({reason})
  - Dependencies: {list or None}

Proposed actions:
  1. {action1}
  2. {action2}
  ...

Apply this fix? (yes / skip / stop)
===
```

### Session Summary (one_by_one mode)

After all CMs processed (or user stops), present:

```
=== ONE-BY-ONE SESSION SUMMARY ===
Total CMs: {scoped_total}
Applied: {applied}
Documented: {documented}
Skipped: {skipped}
Remaining: {scoped_total - done}

Applied:
  - {ID}: {title} [Applied]
Documented:
  - {ID}: {title} [Documented]
Skipped:
  - {ID}: {title} [Skipped]
Remaining (not yet presented):
  - {ID}: {title}
===
```

### 3.1 Apply Fix (CODE_FIX / ML_CODE)

For each code-applicable countermeasure:

1. **Read the task recipe** from skill file
2. **Locate vulnerable code** — see format detection below
3. **Apply the fix** using `search_replace`:
   ```
   search_replace(
     file: "{file_from_recipe}",
     old: "{vulnerable_code_pattern}",
     new: "{secure_code_pattern}"
   )
   ```
4. **Verify fix applied** - read file to confirm change
5. **Check success criteria** from recipe

**CRITICAL:** Apply fix to ORIGINAL file. Never create alternative files.

> **SKILL.md Format Detection (MANDATORY):** Task recipe files come in three formats. All are generated by `generate-security-skill-files` (Format A when `evidence_source == "codebase"`, Format C when `evidence_source == "specs"`, Format B for library-sourced amendments regardless of source); the legacy combined skills produced the same formats. Detection is content-based, so it works regardless of producer. Detect the format BEFORE locating vulnerable code:
>
> **Format A — codebase template ("Code to Fix"):** Uses "Code to Fix" (code snippets with file:line references) and "Required Fix" (secure code pattern) sections. Locate vulnerable code using the "Code to Fix" section; apply the pattern from "Required Fix".
>
> **Format B — Library-sourced from SDE amendments:** The file starts with YAML front-matter (`---` on the first line with `name:` and `description:` fields) and uses sections like "What This Skill Does", "Decision Table", "Boundaries", "Gotchas", and "Quick Verification". These files do NOT have "Code to Fix" or "Required Fix" sections. Instead: use the **"Decision Table"** to understand what situations require fixes, use **"Gotchas"** to identify common vulnerability patterns, use **"Quick Verification"** for validation commands, and use AI semantic analysis (Step 0) findings to locate the actual vulnerable code in the repository. Apply the fix pattern described in the Decision Table that matches the detected situation.
>
> **Format B may target a DIFFERENT language/stack than the repository.** Library-sourced recipes are generic and are often written for a different stack than the target (e.g. Node.js verification snippets, Java examples) — the snippets and `Quick Verification` commands are illustrative, NOT literal. You MUST **translate the intent** of the Decision Table, Gotchas, and secure pattern into the **TARGET tech stack from the handoff** (the language/framework of the repo being fixed). Do **NOT** copy foreign-language code or verification commands verbatim into a repo of a different stack. This translation applies ONLY to the **applied code** in the repository; the library CONTENT in the `SKILL.md` file MUST remain byte-exact (Rule 4) — never rewrite the stored skill file to "fix" its language.
>
> **Format C — specs/greenfield template ("Spec Context"):** Uses "Spec Context" (quoted spec text describing the feature) and "Secure Implementation Pattern" (secure code) instead of "Code to Fix" and "Required Fix". These are greenfield scaffolding recipes — there is no existing vulnerable code to locate. Use the "Spec Context" to understand what is being built, and apply the "Secure Implementation Pattern" directly.
>
> **Detection rule (evaluate in THIS order):** Note that BOTH the generated templates (Format A/C) AND library-sourced files (Format B) begin with a `---` YAML front-matter block, so a `---` prefix ALONE does NOT imply Format B. Discriminate by content:
> 1. If the body contains `**Spec Context:**` → **Format C**.
> 2. Else if the body contains a `**Category:**` line ANYWHERE (every generated template stamps `**Category:**` + `**Status:**`, typically a few lines below the `# {ID}: {Title}` heading — do NOT look only at the "next" line) → **Format A**.
> 3. Else (a `---` front-matter file with `name:`/`description:` and NO `**Category:**`/`**Status:**` anchor anywhere — a byte-exact library amendment using sections like "What This Skill Does" / "Decision Table" / "Gotchas") → **Format B**.

### 3.2 Apply INFRA Fixes to Infrastructure Files

For INFRA countermeasures, check if applicable config files exist and apply fixes directly:

| INFRA Category | Files to Check | Example Fixes |
|----------------|----------------|---------------|
| Container Security | `Dockerfile`, `docker-compose*.yml`, `.dockerignore` | HEALTHCHECK, resource limits, security_opt, cap_drop, cap_add |
| Network/Headers | `server.ts`, `app.ts`, `nginx.conf`, `vagrant/*.conf` | helmet config, security headers (X-Frame-Options, etc.) |
| Build Security | `.dockerignore`, `.gitignore` | Exclude sensitive files (.env, *.key, *.pem) |

**MANDATORY INFRA PRE-CHECK (run ONCE at the start of INFRA processing):**

Before processing any INFRA countermeasures, build a complete infrastructure file inventory:

```bash
# List ALL infrastructure files in the repository (run once, reuse for all INFRA CMs)
find {repository_path} -name "Dockerfile" -o -name "docker-compose*.yml" -o -name ".dockerignore" \
     -o -name "*.conf" -o -name "*.cfg" -o -name "*.ini" \
     -o -name "app.py" -o -name "server.ts" -o -name "server.js" -o -name "main.go" \
     -o -name "*.tf" -o -name "*.yml" -o -name "*.yaml" \
     2>/dev/null | grep -v node_modules | grep -v .git
```

**The default for INFRA CMs is APPLIED, not DOCUMENTED.** You must prove a CM cannot be applied before documenting it.

For each INFRA CM, cross-reference its requirement against this file list:
- If ANY applicable file exists in the list -> the CM **MUST** be marked "Applied" and the fix applied to that file
- Only mark "Documented" if you can state in the CM PROCESSING PROOF block: `"NONE - No file in this repository can implement this fix because [specific reason]"`
- Valid reasons for "Documented": requires cloud provider console (AWS/GCP/Azure), requires CI/CD pipeline not in repo, requires external network infrastructure, requires hardware security module

**Process for each INFRA countermeasure:**

1. **Search for applicable infrastructure files**:
   ```bash
   find . -name "Dockerfile" -o -name "docker-compose*.yml" -o -name ".dockerignore" \
          -o -name "*.conf" -o -name "server.ts" 2>/dev/null | grep -v node_modules
   ```

2. **If applicable file exists - APPLY the fix**:
   ```
   search_replace(
     file: "{infrastructure_file}",
     old: "{current_config}",
     new: "{secure_config}"
   )
   ```
   Mark as **APPLIED** (not DOCUMENTED)

3. **If no applicable file exists** - Document as external requirement:
   - Mark as **DOCUMENTED** with explanation
   - Note: "Requires external infrastructure configuration"

**Example INFRA fixes that CAN be applied:**
- Add HEALTHCHECK to Dockerfile
- Add resource limits to docker-compose.yml
- Add security_opt, cap_drop to docker-compose.yml
- Enhance helmet configuration in server.ts
- Add security headers to Apache/nginx config
- Exclude sensitive files in .dockerignore

### 3.3 Verify Documented (ML_DOC / External INFRA)

For countermeasures that truly cannot be code-fixed (PROCESS excluded -- no skill files):

1. Verify skill file contains:
   - "DOCUMENTATION ONLY" marker
   - "Why Not Code-Fixable" section with:
     - What was searched
     - What was found/not found
     - Why code fix is not possible
   - "Recommended Action" section

2. If missing, add documentation now

**Note:** INFRA countermeasures should only be documented if NO applicable infrastructure file exists in the repository.

### 3.4 Post Countermeasure Evidence in SD Elements

**For EACH countermeasure processed (applied or documented), an audit comment is posted to its countermeasure in SD Elements** — an audit trail in the task's **Notes section** showing exactly what was done. **Posting transport:** in the Step 3 batch loop these per-CM notes are ACCUMULATED in `pending_notes` and posted together via ONE composite call at each batch boundary (see the Step 3 loop / `pending_notes` flush — do NOT call `op=addNote` once per CM inside a batch); in `one_by_one` / `single_cm` mode (no batch) post the note immediately via `op=addNote`. Either way the note body uses the per-CM template below.

The per-CM note is posted via `project_countermeasures` `op: "addNote"` (individually in one_by_one/single_cm mode, or as the body of each sub-request in the batch composite flush):

```json
{
  "op": "addNote",
  "project_id": "{project_id}",
  "countermeasure_id": "{cm_id}",
  "note": "{note_text}"
}
```

The `note` parameter is a plain string containing the audit text. The tool auto-normalizes `countermeasure_id` — it accepts `"T287"`, `"107-T287"`, `287`, etc. Verification verdicts (pass/partial/fail) are NOT posted here; those are the responsibility of `code-scan-verification-validation` via the `verification` MCP tool downstream.

**Note content by category** (this text is the plain `note` string passed to `op=addNote` — NOT a `findings[]` object; `findings[]` belongs to the `verification` tool, not `addNote`):

| Category | Note Template |
|----------|--------------|
| CODE_FIX / ML_CODE | `[AI-Applied] Fixed in {file_path}: {brief description of fix}` |
| INFRA (with config file) | `[AI-Applied] Infrastructure fix applied in {file_path}` |
| ML_DOC / external INFRA | Full multi-section note with `Why Not Code-Fixable` and `Recommended Action` content embedded from local `skills/{domain}/{cm-slug}/SKILL.md` (see template below) |

**ML_DOC / external INFRA note template (multi-section, passed as the `note` string):**

```
[AI-Documented] {one-line reason why not code-fixable}

== Why Not Code-Fixable ==
{verbatim content of the "Why Not Code-Fixable" section from skills/{domain}/{cm-slug}/SKILL.md,
 including: what was searched, what was found/not found, why code fix is not possible}

== Recommended Action ==
{verbatim content of the "Recommended Action" section from skills/{domain}/{cm-slug}/SKILL.md}

-- Source: skills/{domain}/{cm-slug}/SKILL.md (local artifact, not preserved after this run) --
```

**Critical ordering — read BEFORE Step 7 deletes `skills/`:**

The full `Why Not Code-Fixable` and `Recommended Action` content is a **build artifact** that lives only in `skills/{domain}/{cm-slug}/SKILL.md` during this skill's run. **Step 7.1 (`rm -rf skills/`) wipes it** before any downstream skill can read it. Therefore, Step 3.4 MUST `read_file` the local skill file and extract both sections **inline, immediately before** the `project_countermeasures op=addNote` call. Reading later (e.g., during the retry loop, or in `code-scan-verification-validation`) is too late — the file is gone. This embed is the only durable persistence path for that analysis; without it, the user is left with a dangling `See skills/...` pointer to a deleted file.

**Fallback if local SKILL.md cannot be read:**

If `read_file skills/{domain}/{cm-slug}/SKILL.md` fails (file missing, corrupted, both sections absent, or read errors), the skill MUST fall back to a brief note rather than skipping the verification note entirely:

```
[AI-Documented] {one-line reason why not code-fixable}

(Note: detailed Why Not Code-Fixable / Recommended Action sections were not available
 from the local skill artifact at post time; refer to the CM's `text` and `how_tos`
 fields in SDE for canonical guidance.)
```

The fallback ensures the audit comment always succeeds (preserving the audit trail) even when the local file is unreadable, and is observable in the SDE UI's Notes section so users can see why the rich content is absent.

**Error handling:**

- If `read_file` of the local SKILL.md fails, use the fallback template above and log a warning (`[WARN] evidence post fallback for {cm_id}: local skill file unreadable`). Do not skip the `project_countermeasures op=addNote` call.
- If `project_countermeasures op=addNote` fails (network, 4xx, 5xx), log a warning and continue processing. The code fix is more important than the note.
- Track failed notes in a `notes_failed` list (cache the prepared `note_text` alongside the CM id and `full_id`).
- **Batch mode:** the SDE Direct API Access script already reconciles per `reference_id` and RETRIES the failed subset ONCE; read the still-failed entries from its response file into `notes_failed`. **`one_by_one` / `single_cm` mode** (immediate `op=addNote`): retry each failed note once at the agent level. **Either way the retry payload MUST be the same fully-embedded note prepared inline** (do NOT regenerate by reading the local file — by retry time you may be near/at Step 7; use the cached `note_text`).
- Report any remaining failures in the completion verification block.

**Output after each note:**
```
[NOTE] {cm_id}: {ADDED/FAILED} in SD Elements
```

---

## Step 3.5: Cross-Surface Parity Check

> **Greenfield: N/A.** If this run is greenfield (see Step 0.0 GREENFIELD MODE — handoff `evidence_source == "specs"`, or legacy `source_skill == "create-security-plan-from-specs"` / Format C), there are no pre-existing vulnerable surfaces to keep in parity. Emit `Additional surfaces found: 0 (greenfield)` and skip to the next step.

After the main CM processing loop completes, verify that security controls are applied consistently across **all code paths** performing the same security-sensitive operation, not just the paths identified in the CM's task recipe.

This step is **AI-driven, repository-agnostic, and language-agnostic**. It relies on semantic reasoning from the CM's vulnerability description (`ctx.problem`) and the codebase analysis performed in Step 0.

### 3.5.1 Procedure

For each CM that was marked **Applied** in Step 3:

1. **Recall the vulnerability class** from the CM's `ctx.problem` / task recipe (e.g., SQL injection, missing rate limiting, insecure deserialization, weak password hashing).
2. **Using the Step 0 AI analysis results**, identify ALL other code paths in the repository that perform the same security-sensitive operation (e.g., other query construction sites, other authentication endpoints, other file upload handlers).
3. **For each additional code path found:** determine whether it already has an equivalent mitigation. If NOT, apply the same fix pattern used for the primary CM.
4. **Track parity fixes** in the session output:

```
=== PARITY CHECK ({cm.id}) ===
Primary fix: {file}:{line} — {description}
Additional surfaces found: {N}
  - {file2}:{line2} — {status: ALREADY_MITIGATED | FIX_APPLIED | NOT_APPLICABLE}
  - {file3}:{line3} — {status}
===
```

### 3.5.2 Constraints

- This check uses AI code analysis from Step 0; it does NOT introduce framework-specific heuristics.
- Files modified by parity fixes MUST be merged back into the corresponding CM's entry in `audit_records[]` (the list populated during Step 3). After all parity fixes for a CM are complete, update that CM's `audit_records` entry:
  ```python
  for record in audit_records:
      if record["id"] == cm.id:
          record["files_modified"].extend(parity_files)
          break
  ```
  This ensures `.sde-apply-handoff.json` (written in Step 6.5 from `audit_records`) includes parity-fixed files so `code-scan-verification-validation` can verify them.
- If no additional surfaces are found, output `Additional surfaces found: 0` and proceed.
- This step MUST NOT reclassify CMs or change their Applied/Documented status.

---

## Step 4: Anti-Shortcut Verification

Before marking ANY countermeasure as documentation-only:

| If claiming... | You MUST have checked for... | Action if found |
|----------------|------------------------------|-----------------|
| ML_DOC | AI/ML imports, `ai/`, `ml/`, model files, tensorflow/pytorch | Apply fix |
| INFRA (container) | `Dockerfile`, `docker-compose*.yml`, `.dockerignore` | **APPLY fix to file** |
| INFRA (database) | DB connection code, ORM config, migration files | **APPLY fix to file** |
| INFRA (network) | `nginx.conf`, `server.ts`, `vagrant/*.conf`, proxy configs | **APPLY fix to file** |
| INFRA (headers) | `server.ts`, `app.ts` (helmet/security middleware) | **APPLY fix to file** |

**CRITICAL: If the relevant infrastructure file EXISTS, you MUST apply the fix to that file - do NOT just document it.**

Only document INFRA countermeasures when:
- The fix requires cloud provider console (AWS, GCP, Azure)
- The fix requires CI/CD pipeline configuration not in repo
- No applicable configuration file exists in the repository

### Repository Intent is IRRELEVANT

**NEVER skip a fix because:**
- The repository is "intentionally vulnerable" (Juice Shop, DVWA, WebGoat, etc.)
- The vulnerability is "by design" or "for training"
- Fixing it would "break the demo"
- The application is meant to have security issues

**The countermeasure says CODE_FIX → You MUST fix the code. No exceptions.**

The user explicitly asked you to apply fixes. Do NOT rationalize skipping them because of the repository's original purpose. If it breaks the intentionally-vulnerable training scenarios, that is expected and correct behavior.

---

## Step 5: Completion Gate (Scoped)

**THIS GATE CANNOT BE BYPASSED.** Totals always EXCLUDE already-done CMs (from previous runs). Only count CMs that entered this run as "Pending".

### 5.1 Scoped Verification

Completion gate adapts based on scope:

- **all**: `newly_applied + newly_documented == this_run_total` (where `this_run_total = total - already_done`)
- **domain**: `newly_applied + newly_documented == domain_remaining`, warn about remaining domains
- **single_cm**: `newly_applied + newly_documented == 1` -- OR the user DECLINED the single CM (a declined single_cm is a valid terminal: 0 applied/documented, analogous to a one_by_one early stop -- do NOT treat `0 == 1` as INCOMPLETE), warn about remaining CMs
- **one_by_one**: `newly_applied + newly_documented + newly_skipped == total_presented`. User-skipped CMs count as "addressed" (explicit user decision). If user stopped early, gate only covers presented CMs.

### 5.2 Output Verification Block

```
=== COMPLETION VERIFICATION ===
Skill: apply-security-fixes
Scope: {all / domain={name} / single_cm={id} / one_by_one}
Total countermeasures: {N}
PROCESS (note-only, excluded): {process_count}
File-tracked countermeasures: {file_tracked}
Already done (previous runs): {already_done}
Scoped for this run: {scoped_total}

Applied this run: {applied}
Documented this run: {documented}
Skipped this run: {skipped}
Sum this run: {applied + documented + skipped}
Expected this run: {scoped_total}
Match: {sum} == {scoped_total}? {YES/NO}

SD Elements notes:
- Notes added: {notes_added}
- Notes failed: {notes_failed}
- Failed IDs: {list or "none"}

Intent verification: ✓ (no "intentionally vulnerable" rationalizations)

(NOTE: AI-config restore is Step 7.5 and security/+skills/ cleanup is Step 7 -- both AFTER this gate; reported in the final SKILL COMPLETE summary, NOT asserted here.)

{If scope != "all": "WARNING: {remaining_overall} CMs remain in other scopes." where remaining_overall = (total Pending CMs in the ledger) - scoped_total}
===============================
```

For `one_by_one` mode, the session summary (printed at end of Step 3 loop) replaces the standard verification block.

### 5.3 Gate Logic

**If MATCH = NO:**
```
INCOMPLETE: {sum}/{scoped_total} - CANNOT PROCEED
Missing countermeasure IDs: {list}
ACTION: Return to Step 3 and process missing items
```

**If MATCH = YES:**
```
✅ COMPLETION GATE PASSED
Proceeding to handoff...
```

### 5.4 Verify No Alternative Files

```bash
# This MUST return no results
find . -name "*_secure.*" -o -name "*_fixed.*" -o -name "*_safe.*" | grep -v node_modules
```

**ALSO flag UNEXPECTED new code directories or per-batch modules** created during apply -- these indicate fixes were dumped to alt files instead of applied IN PLACE (the rogue-worker failure mode in the SUBAGENT / DELEGATION POLICY). Compare against the pre-apply file tree snapshot and flag any of:
- A new scratch/output code dir not present in the pre-apply tree (e.g. `security/applied/`, `security/fixes/`, any new top-level code dir that did not exist before this run -- the apply skill's own `.sde-security/` scratch is the ONLY sanctioned new dir).
- Per-batch code modules (e.g. `*/batch_*.py`, `*/batch_*.*`, files/dirs named after batch indices).

```bash
# These MUST return no results (exclude the sanctioned .sde-security scratch + vendored dirs)
find . -path ./node_modules -prune -o -path ./.sde-security -prune -o \
  \( -name 'batch_*' -o -path '*/security/applied/*' \) -print
```

**Finding ANY of the above = audit FAIL.** If any found:
1. DELETE them
2. Apply fixes to ORIGINAL files instead (IN PLACE)
3. Re-run gate

### 5.5 Intent Rationalization Check

Before outputting completion block, verify no fixes were skipped due to repository intent:

1. **Review all documented countermeasures** - check justification text in skill files
2. **Flag violations** if any "Why Not Code-Fixable" or status notes contain:
   - "intentionally vulnerable"
   - "by design"
   - "for training purposes"
   - "would break the demo"
   - "meant to have security issues"
   - "vulnerable on purpose"

**If violations found:**
```
[ERROR] INTENT VIOLATION DETECTED
The following countermeasures were incorrectly skipped:
- {ID}: "{violation phrase found}"
...

GO BACK and apply the fix. Repository intent is irrelevant.
```

**DO NOT PROCEED. Re-apply the skipped fixes.**

**If no violations:**
```
[CHECKPOINT] Intent verification: PASSED (no fixes skipped due to repository intent)
```

### 5.6 Marker Deletion Verification (AI Analysis)

> **Greenfield (create-security-plan upstream): N/A.** Scaffolded placeholders contain no `vuln-code-snippet`/`VULNERABLE` markers (see Step 0.0 GREENFIELD MODE). Emit `Markers to delete: 0 (greenfield)` and proceed.

**Use AI analysis to verify ALL markers have been deleted - do NOT just grep.**

For EACH file from your Step 0 master list:
1. **Re-read the file** using `read_file`
2. **AI scan for remaining markers:**
   - `vuln-code-snippet`
   - `VULNERABLE`, `INSECURE`
   - `intentional` (in context of vulnerabilities)
   - Any comment indicating code is deliberately insecure
3. **Verify the vulnerability was FIXED** (not just marker removed)

**Output:**
```
=== MARKER DELETION VERIFICATION (AI Analysis) ===
Files re-analyzed: {count}

VERIFICATION RESULTS:
✓ {file}: All markers DELETED, vulnerability FIXED
✓ {file}: All markers DELETED, vulnerability FIXED
...

Remaining markers found: {0 required}
=================================================
```

**If ANY markers remain:**
```
[ERROR] MARKERS STILL PRESENT
- {file}:{line}: "{marker text}"
GO BACK and DELETE all markers.
```

**If all clean:**
```
[CHECKPOINT] Marker verification: PASSED (all markers DELETED via AI analysis)
```

### 5.7 Proof Block Verification (Structural Enforcement Gate)

**MANDATORY: This check MUST pass before the completion gate can pass.**

Verify that a `CM PROCESSING PROOF` block was output for EVERY processed countermeasure:

1. Count the total CM PROCESSING PROOF blocks output during this run
2. Compare against the number of CMs processed (applied + documented + skipped)
3. Every processed CM MUST have exactly one proof block

**Output:**
```
=== PROOF BLOCK VERIFICATION ===
CMs processed this run: {count}
Proof blocks output: {count}
Match: {YES/NO}

Missing proof blocks for: {list of CM IDs, or "none"}
================================
```

**If MATCH = NO:**
```
[ERROR] PROOF BLOCKS MISSING
The following CMs were processed without proof blocks:
- {cm_id}: processed as {status} but no CM PROCESSING PROOF block found
...
ACTION: This indicates batch processing was used. Go back and individually
read each missing CM's SKILL.md, output the proof block, and verify the
status decision was correct.
```

**If MATCH = YES:**
```
[CHECKPOINT] Proof block verification: PASSED ({count}/{count} proof blocks present)
```

**This gate exists to enforce Rule 8. If proof blocks are missing, the agent used batch operations and the status decisions may be wrong.**

**DELEGATED runs (parent-enforceable):** when CMs were processed via delegated workers, the PARENT MUST collect and verify each worker's `CM PROCESSING PROOF` block for the worker's allow-listed CM-IDs — **a worker's self-reported proof / "pass" is NOT sufficient**. The parent re-derives each CM's terminal status from the AGENTS.md ledger row + the Step 5.8 surviving-source-file check, NOT from worker claims. Any CM-ID a worker reported but the parent cannot independently verify (missing/invalid proof, ledger row not written by the parent, or no surviving real source file) fails this gate and must be re-processed by the parent.

### 5.8 Apply Completeness Audit (re-read from disk)

Re-derive every CM's terminal status from the **AGENTS.md ledger rows** (the authoritative status source) and verify every SCOPED CM has a terminal status. This catches CMs that were silently dropped. **Two denominators (Fix E):** `scoped_total` = UNIQUE scoped CMs (one status decision / one handoff entry / one SDE note each); `expected_total` = total ledger ROWS = SKILL.md FILES on disk (a CM with N matched-tech files has N rows; applying that CM flips ALL N rows to its terminal status). So: `unique scoped CMs with a terminal ledger status == scoped_total` AND `terminal ledger rows == expected_total == SKILL.md files`. Count from the LEDGER rows, NOT per-file `**Status:**` — Format B (library-sourced, byte-exact) files have NO in-file `**Status:**`, so a statusless Format B file is NOT a failure; its status is its ledger row.

**Enumerate EVERY artifact class below -- do NOT sample or trust the in-memory loop counts; re-derive from the ledger on disk and re-fetch note coverage from SDE.**

```
=== APPLY COMPLETENESS AUDIT (re-derive from ledger + re-fetch from SDE) ===
PRECONDITION (this block is INVALID if unmet):
- The BATCH PLAN for Step 3 was emitted (paste its header line here): ____
- A per-batch mini-gate line was emitted for EVERY batch (count == Total batches): ____
If either is missing you did NOT run the loop. STOP, go to the partition step,
and execute all batches. Do NOT fill in this block from a "sample" or "key CMs".

SKILL.md files on disk: {N} (Format A: {a}, Format B/library: {b}, Format C: {c}) == expected_total
Ledger rows (AGENTS.md per-file index): {N_ledger}
UNIQUE SCOPED CMs with a terminal status (Applied/Documented/Skipped) IN THE LEDGER: {M_scoped} (scoped_total: {scoped_total})
Terminal-status ledger ROWS for the SCOPED CMs (files): {R_terminal} (scoped_file_total: {scoped_file_total} = Σ files/rows of the scoped CMs; == expected_total ONLY when scope=all)
VERIFY: M_scoped == scoped_total (every SCOPED CM has a terminal ledger status, none dropped)? {YES/NO}
VERIFY: R_terminal == scoped_file_total (every file/row of every SCOPED terminal CM flipped -- a scoped CM with N files has all N rows terminal; on scope=all scoped_file_total == expected_total, on a narrowed scope non-scoped rows legitimately stay Pending)? {YES/NO}
VERIFY: N_ledger == N (one ledger row per SKILL.md file on disk == expected_total)? {YES/NO}
VERIFY: every Format B (library-sourced) file is covered by a terminal LEDGER row
  (a statusless Format B file body is NOT a failure -- its status is the ledger row)? {YES/NO}
CM PROCESSING PROOF blocks emitted this run: {P}
VERIFY: P == number of CMs processed this run? {YES/NO}
SDE note coverage (re-fetch from SDE, NOT the in-memory sde_note_result): re-fetch
  note_count per CM via `project_countermeasures op=list` (paginated; the list response
  includes `note_count` per CM). Have the generated verification script parse the
  returned note_counts to disk -- do NOT pull full task bodies into context (keep
  consistent with the "no file BODIES into context" rule).
  NOTE: the `op=list` TOTAL includes PROCESS / note-only CMs (e.g. 490 total vs 459
  file-tracked) -- the note-coverage check MUST FILTER to the SCOPED file-tracked CMs
  (or the terminal CMs), NOT iterate all returned rows. Then PROVE THIS RUN posted the
  note: a bare note_count >= 1 is INSUFFICIENT because it can be satisfied by a
  pre-existing UPSTREAM note (a human note or a prior run). Assert each Applied/Documented
  (file-tracked) CM's most-recent note text carries THIS run's marker (`[AI-Applied]`
  for Applied, `[AI-Documented]` for Documented) -- match on that one latest note per CM
  (do NOT pull full task bodies into context) or reconcile against the per-CM markers
  recorded to disk at post time (e.g. `.sde-security/apply/note_posted.tsv`). A CM with
  notes but NO run-marker note FAILS (or is explicitly recorded sde_note_result=FAILED
  in the handoff)? {YES/NO}
SURVIVING-SOURCE CHECK (ledger-authoritative status A1 is NECESSARY but NOT SUFFICIENT --
  do NOT trust the ledger alone): for EVERY CM marked Applied, each recorded
  `files_modified[]` path EXISTS on disk AND is a REAL surviving source file -- i.e. NOT
  under a scratch/alt dir that Step 7 will delete (`security/`, `.sde-security/`) and NOT
  an alternative file (`*_secure.*` / `*_fixed.*` / `*_safe.*` / `batch_*`). A bulk-flipped
  ledger with no real source change MUST FAIL here? {YES/NO}
==================================================
```

If any VERIFY is NO: identify the unprocessed CM(s) / missing note(s) / Applied CM whose claimed fix has no surviving real source file, and run them through the Step 3 loop (or re-post the note / re-apply the fix IN PLACE); re-run the audit. Block completion until all YES.

### Generate and Run the Independent Verification Script

After the in-line audit above shows ALL CHECKS = YES, GENERATE a self-contained verification script at runtime and execute it. Do NOT ship or rely on a pre-built script — build it from THIS run's actual data.

1. Write the script to `{repository_path}/.sde-security/verify-apply-output.sh`. It is **DISK-ONLY and CONTEXT-LIGHT** (counts via shell/grep; NEVER reads file bodies into context). It MUST:
   - Count **AGENTS.md ledger rows** (one per skill FILE) that carry a terminal status (`Applied`, `Documented`, or `Skipped`) and assert the count equals `scoped_file_total` (the Σ of files/rows belonging to the SCOPED CMs; == `expected_total` ONLY when scope=`all` — on a narrowed scope the non-scoped CMs' rows legitimately remain Pending, so asserting `expected_total` would false-fail every `domain`/`single_cm`/`one_by_one` run). The ledger — NOT per-file `**Status:**` — is the source of truth (Format B files have no in-file status; a statusless Format B file is NOT a failure)
   - For each scoped CM ID, assert ALL of its ledger row(s) have a terminal status (a CM with N matched-tech files has N rows, all terminal); assert the count of UNIQUE scoped CMs with a terminal status equals `scoped_total`; list any missing
   - Assert `grep -cE '^\| [A-Z]*T[0-9]' AGENTS.md` (ledger rows; `[A-Z]*T` matches library `T#`, project-specific `PT#`, custom-library `CT#`, and any uppercase-prefixed CM ID) equals the count of `skills/**/SKILL.md` files on disk == `expected_total` (one ledger row per file), and unique terminal CM IDs == `scoped_total` (tri-source: expected_total == ledger rows == SKILL.md files; scoped_total == unique terminal CMs)
   - Parse the SDE per-CM note data that the audit fetched via `project_countermeasures op=list` (written to a small on-disk file, e.g. `.sde-security/apply/note_counts.tsv`) and **PROVE THIS RUN posted** — a bare `note_count >= 1` is INSUFFICIENT because it can be satisfied by a pre-existing UPSTREAM note (a human note or a prior run). Assert each Applied/Documented CM has a note bearing THIS run's marker — `[AI-Applied]` for Applied, `[AI-Documented]` for Documented — by matching the CM's most-recent note text (fetch only that one latest note per CM, never full task bodies) or by reconciling against the per-CM markers recorded to disk at post time (e.g. `.sde-security/apply/note_posted.tsv`); a CM with notes but no run-marker note FAILS (or is recorded `sde_note_result=FAILED`). **FILTER the `op=list` rows to the SCOPED file-tracked CMs (or terminal CMs) before checking coverage — the `op=list` total includes PROCESS / note-only CMs (e.g. 490 total vs 459 file-tracked), so iterating ALL rows would mis-count; only file-tracked/terminal CMs are in scope for note coverage**
   - **Surviving-source check (ledger status is NOT sufficient):** for every CM recorded `Applied` (read `files_modified[]` from the on-disk handoff / audit records), assert each path EXISTS on disk AND is NOT under a scratch/alt dir that Step 7 deletes (`security/`, `.sde-security/`) AND is NOT an alternative file (`*_secure.*` / `*_fixed.*` / `*_safe.*` / `batch_*`). Exit non-zero (`VERIFY FAIL: applied CM with no surviving source file`) if any Applied CM has zero surviving real source files — a bulk-flipped ledger with no real source change MUST fail here; do NOT trust the ledger alone
   - Exit non-zero (`VERIFY FAIL: terminal-status shortfall`) if any scoped CM lacks a terminal LEDGER status, or if the SCOPED CMs' terminal ledger rows != `scoped_file_total` (a multi-file scoped CM with some rows not flipped; on scope=all `scoped_file_total == expected_total`)
   - Print a final `VERIFY PASS` or `VERIFY FAIL: {reasons}` line and exit non-zero on failure
2. Run it: `cd {repository_path} && bash .sde-security/verify-apply-output.sh`
3. Paste the raw output. If `VERIFY FAIL`: fix, re-run. Do NOT print the completion message until `VERIFY PASS`.

### FROM-SCRATCH FINAL VERIFICATION (clean-room terminal gate -- trust nothing from this run)

Re-derive independently of any in-run claim/TodoWrite/memory; all counts via script/grep + SDE re-query, NEVER by reading file bodies into context.

```
=== FROM-SCRATCH FINAL VERIFICATION (apply) ===
A. SDE (note coverage), via MCP: `project_countermeasures op=list` (paginated; the list
   response carries `note_count` per CM). Parse the note data to disk via the generated
   script -- do NOT pull full task bodies into context. FILTER to the SCOPED file-tracked
   CMs (or terminal CMs) -- the `op=list` total includes PROCESS / note-only CMs (e.g. 490
   total vs 459 file-tracked), so do NOT iterate all rows. PROVE THIS RUN posted: a bare
   note_count >= 1 is INSUFFICIENT (a pre-existing upstream note satisfies it), so every
   Applied/Documented (file-tracked) CM must carry a note with THIS run's marker
   (`[AI-Applied]` / `[AI-Documented]`), matched on the CM's most-recent note text (or the
   disk-recorded post-time markers) (or sde_note_result=FAILED in handoff).
B. Disk (actual), via shell/grep ONLY: terminal-status LEDGER row count (AGENTS.md, authoritative);
   grep -c ledger rows; SKILL.md file count on disk; unique terminal CM IDs.
C. INVARIANT (Fix E, dual):
   (structural, always) expected_total == TOTAL LEDGER rows == SKILL.md files on disk;
   AND (terminal, scope-aware) terminal-status LEDGER rows for the scoped CMs == scoped_file_total (Σ files of scoped CMs; == expected_total ONLY when scope=all — non-scoped rows legitimately stay Pending);
   AND scoped_total == unique CMs with a terminal ledger status? {YES/NO}
D. SDE note coverage: every Applied/Documented CM carries a THIS-RUN marker note
   (`[AI-Applied]` / `[AI-Documented]`) on its most-recent note -- NOT merely
   note_count >= 1 (which a pre-existing upstream note can satisfy)? {YES/NO}
E. Every fix was applied by the AI inline (no scripted code edits)? {YES/NO}
F. verify-apply-output.sh = VERIFY PASS (exit 0)? {YES/NO}
G. SURVIVING-SOURCE (ledger status NECESSARY but NOT SUFFICIENT): every Applied CM's
   recorded files_modified[] point to REAL surviving non-alternative source files -- each
   path exists, is NOT under a Step-7-deleted scratch dir (security/, .sde-security/), and
   is NOT an alternative file (*_secure.*/*_fixed.*/*_safe.*/batch_*)? {YES/NO}
RESULT: ALL YES? {YES/NO}
If NO: fix the owning CM(s), RE-RUN this entire from-scratch verification. Completion forbidden until ALL YES.
================================================
```

---

## Step 6: Update Statuses (Ledger-Authoritative)

After all fixes applied, the per-CM status is recorded in the **AGENTS.md ledger row** — the authoritative per-CM status/scope source:

- **Update the AGENTS.md ledger ROW status for every CM** (`Pending` → `Applied` / `Documented` / `Skipped`). Each per-CM status write is a **single-row ledger edit** (allowed — NOT a batch shell update, so Rule 8 stays intact).
- **ADDITIONALLY** update the in-file `**Status:**` ONLY when the file HAS that anchor (Format A / Format C / template). For **Format B** (byte-exact, library-sourced) files there is NO `**Status:**` anchor — do **NOT** modify the file body (Rule 4); its status lives ONLY in the ledger row. A statusless Format B file is correct, not an error.
- This is done per-CM as part of the progress tracking (Step 3.X within the loop), not as a separate batch step.

---

## Step 6.5: Write Apply-Fixes Handoff File (`.sde-apply-handoff.json`)

**Purpose:** Persist a per-CM audit trail to disk **BEFORE Step 7 cleanup deletes `skills/` and `security/`**. The downstream `code-scan-verification-validation` skill runs in a fresh agent context with no conversation history and needs this file to know which CMs were processed and which files were modified. Most CM metadata (title, domain, fix text, problem, how-tos) is fetched **live from SDE** in code-scan-verification-validation Step B1 -- this handoff stores what SDE cannot reconstruct plus `category` (enables parent-side short-circuits in code-scan-verification-validation without a subagent launch).

### 6.5.1 CRITICAL: DO NOT Overwrite `.sde-handoff.json`

The upstream `generate-security-skill-files` skill writes `.sde-handoff.json` at the repository root. **This skill MUST NOT touch that file.** The apply-fixes handoff goes to a **distinct filename**: `.sde-apply-handoff.json`.

| File | Owner | This skill may |
|------|-------|----------------|
| `.sde-handoff.json` | `generate-security-skill-files` (legacy: setup-/create-security-plan) | **READ ONLY** (in Step 0.5). NEVER write, rename, or delete. |
| `.sde-apply-handoff.json` | `apply-security-fixes` (this skill, Step 6.5) | Create/overwrite at end of run. |

If you overwrite `.sde-handoff.json`, downstream re-runs of `apply-fixes` against the same repo will fail Step 0.5's `source_skill` check and the user will lose `business_unit_id`, `application_id`, `agents_md`, `skill_files_base`, domain list, category counts, etc.

### 6.5.2 Why This Step Is BEFORE Step 7

Step 7 deletes `skills/` and `security/`. Once those are gone, there is no way to reconstruct `files_modified[]` per CM. If this write happens after cleanup, the handoff becomes useless. **DO NOT reorder these steps.**

### 6.5.3 Required Output File

> **HANDOFF SCHEMA INVARIANTS (CLOSED SCHEMA -- NO DEVIATIONS)**
>
> **REQUIRED top-level keys (exactly these, nothing more):**
> `source_skill`, `handoff_version`, `generated_at`, `upstream_handoff`, `repository_path`, `project_id`, `security_branch`, `scope`, `totals`, `countermeasures`
>
> **REQUIRED per-CM keys (exactly these, nothing more):**
> `id`, `full_id`, `status`, `category`, `files_modified`, `sde_note_result`
>
> **FORBIDDEN top-level keys (common mistakes -- NEVER add these):**
> `project_name`, `business_unit_id`, `summary`, `files_modified` (top-level), `timestamp`, `domain`, `process_excluded`, or ANY key not listed above.
> The summary object MUST be keyed `totals`, not `summary`. Modified files are tracked **per-CM only**.
>
> **FORBIDDEN per-CM keys (common mistakes -- NEVER add these):**
> `domain`, `skill_file`, `title`, `note_text`, `fix_summary`, or ANY key not listed above.
> Domain, title, and fix text are fetched live from SDE by downstream skills; persisting them here is redundant and creates drift.
>
> **Violation of these invariants causes downstream `code-scan-verification-validation` to produce incorrect verdicts or HARD STOP.**

Write to `{repository_path}/.sde-apply-handoff.json` (minimal schema -- everything else is live-fetched from SDE):

```json
{
  "source_skill": "apply-security-fixes",
  "handoff_version": "2",
  "generated_at": "{iso8601_utc_timestamp}",
  "upstream_handoff": ".sde-handoff.json",
  "repository_path": "{repository_path}",
  "project_id": {project_id_integer},
  "security_branch": "{git_branch_or_null}",
  "scope": "{all | domain=<name> | single_cm=<id> | one_by_one}",
  "totals": {
    "applied": A,
    "documented": D,
    "skipped": S,
    "scoped_total": A_plus_D_plus_S
  },
  "countermeasures": [
    {
      "id": "T123",
      "full_id": "{project_id}-T123",
      "status": "Applied | Documented | Skipped",
      "category": "CODE_FIX | ML_CODE | INFRA | ML_DOC",
      "files_modified": ["src/auth.ts", "server.ts"],
      "sde_note_result": "ADDED | FAILED | NOT_SENT"
    }
    // one entry per scoped CM (including Skipped)
  ]
}
```

**Intentionally NOT persisted here** (re-fetchable from SDE by code-scan-verification-validation via `project_countermeasures op=get expand=text,problem,tags,how_tos,phase,name`): `title`, `domain`, `fix_summary`, `sde_note_text`, `project_name`, `risk_policy_id`.

### 6.5.4 Source of the `countermeasures[]` Array

The `countermeasures[]` array is built from the `audit_records[]` list populated inside the Step 3 loop. Every processed CM (Applied, Documented, **and** Skipped) MUST appear. Do not filter.

### 6.5.5 Pseudocode

```python
import json, datetime, os

handoff = {
    "source_skill": "apply-security-fixes",
    "handoff_version": "2",
    "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    "upstream_handoff": ".sde-handoff.json",
    "repository_path": repository_path,
    "project_id": project_id,
    "security_branch": security_branch,  # may be None if no branching
    "scope": scope_descriptor,
    "totals": {
        "applied": applied,
        "documented": documented,
        "skipped": skipped,
        "scoped_total": applied + documented + skipped,
    },
    "countermeasures": audit_records,
}

handoff_path = os.path.join(repository_path, ".sde-apply-handoff.json")
assert handoff_path.endswith(".sde-apply-handoff.json"), \
    "NEVER write to .sde-handoff.json -- that belongs to generate-security-skill-files"

with open(handoff_path, "w") as f:
    json.dump(handoff, f, indent=2)

print(f"[CHECKPOINT] Handoff written: {handoff_path} ({len(audit_records)} CMs)")
```

### 6.5.6 Verification (Strict Schema Validation Gate)

After writing the file, **read it back from disk** and run the validation below. Do NOT skip any check. Do NOT proceed to Step 7 until every assertion passes.

```python
import json

REQUIRED_TOP_KEYS = {
    "source_skill", "handoff_version", "generated_at", "upstream_handoff",
    "repository_path", "project_id", "security_branch", "scope",
    "totals", "countermeasures",
}
REQUIRED_CM_KEYS = {"id", "full_id", "status", "category", "files_modified", "sde_note_result"}
VALID_STATUSES = {"Applied", "Documented", "Skipped"}
VALID_CATEGORIES = {"CODE_FIX", "ML_CODE", "INFRA", "ML_DOC"}
VALID_NOTE_RESULTS = {"ADDED", "FAILED", "NOT_SENT"}

handoff_path = f"{repository_path}/.sde-apply-handoff.json"

# 1. File exists and is valid JSON
with open(handoff_path) as f:
    h = json.load(f)

errors = []

# 2. Top-level key check (closed schema -- no extra keys allowed)
actual_top = set(h.keys())
missing_top = REQUIRED_TOP_KEYS - actual_top
extra_top = actual_top - REQUIRED_TOP_KEYS
if missing_top:
    errors.append(f"Missing top-level keys: {missing_top}")
if extra_top:
    errors.append(f"FORBIDDEN extra top-level keys: {extra_top}")

# 3. Value assertions
if h.get("source_skill") != "apply-security-fixes":
    errors.append(f"source_skill must be 'apply-security-fixes', got {h.get('source_skill')!r}")
if h.get("handoff_version") != "2":
    errors.append(f"handoff_version must be '2', got {h.get('handoff_version')!r}")

# 4. Totals integrity
totals = h.get("totals", {})
expected_count = totals.get("applied", 0) + totals.get("documented", 0) + totals.get("skipped", 0)
if totals.get("scoped_total") != expected_count:
    errors.append(f"totals.scoped_total ({totals.get('scoped_total')}) != applied+documented+skipped ({expected_count})")
if len(h.get("countermeasures", [])) != expected_count:
    errors.append(f"countermeasures[] length ({len(h.get('countermeasures', []))}) != scoped_total ({expected_count})")
# 4b. full_id UNIQUENESS (Fix E guard): scoped_total counts UNIQUE CMs, and a multi-file CM
# (multiple skill files) MUST still produce exactly ONE countermeasures[] entry. Duplicate
# full_ids would mean per-file entries leaked through instead of per-CM aggregation.
full_ids = [cm.get("full_id") for cm in h.get("countermeasures", [])]
if len(set(full_ids)) != len(full_ids):
    dups = sorted({fid for fid in full_ids if full_ids.count(fid) > 1})
    errors.append(f"Duplicate full_id in countermeasures[] (multi-file CMs not aggregated to one entry): {dups}")

# 5. Per-CM field validation (closed schema -- no extra keys allowed)
for i, cm in enumerate(h.get("countermeasures", [])):
    cm_keys = set(cm.keys())
    cm_missing = REQUIRED_CM_KEYS - cm_keys
    cm_extra = cm_keys - REQUIRED_CM_KEYS
    if cm_missing:
        errors.append(f"CM[{i}] ({cm.get('id','?')}): missing keys {cm_missing}")
    if cm_extra:
        errors.append(f"CM[{i}] ({cm.get('id','?')}): FORBIDDEN extra keys {cm_extra}")
    if cm.get("full_id") != f"{h.get('project_id')}-{cm.get('id')}":
        errors.append(f"CM[{i}]: full_id mismatch: expected '{h.get('project_id')}-{cm.get('id')}', got '{cm.get('full_id')}'")
    if not isinstance(cm.get("files_modified"), list):
        errors.append(f"CM[{i}] ({cm.get('id','?')}): files_modified must be a list, got {type(cm.get('files_modified')).__name__}")
    if cm.get("status") not in VALID_STATUSES:
        errors.append(f"CM[{i}] ({cm.get('id','?')}): invalid status '{cm.get('status')}'")
    if cm.get("category") not in VALID_CATEGORIES:
        errors.append(f"CM[{i}] ({cm.get('id','?')}): invalid category '{cm.get('category')}'")
    if cm.get("sde_note_result") not in VALID_NOTE_RESULTS:
        errors.append(f"CM[{i}] ({cm.get('id','?')}): invalid sde_note_result '{cm.get('sde_note_result')}'")

# 6. Upstream handoff preserved
assert os.path.exists(f"{repository_path}/.sde-handoff.json"), \
    ".sde-handoff.json must still exist (generate-security-skill-files' handoff)"

if errors:
    print(f"[VALIDATION FAILED] {len(errors)} errors in .sde-apply-handoff.json:")
    for e in errors:
        print(f"  - {e}")
    # REBUILD AND RETRY (see below)
else:
    print("[VALIDATION PASSED] .sde-apply-handoff.json conforms to schema")
```

**Rebuild-and-retry gate:** If validation fails:

1. Log every error from the `errors` list.
2. Delete the malformed file.
3. Rebuild the handoff dict from `audit_records` using the Step 6.5.5 pseudocode **verbatim** (do not improvise a different structure).
4. Write the rebuilt file to disk.
5. Re-run the full validation above on the rebuilt file.
6. If the second validation also fails, **HARD STOP** -- do not proceed to Step 7. Print the errors and instruct the user to inspect `audit_records`.

**Output (on success):**
```
[CHECKPOINT] Apply-fixes handoff written: .sde-apply-handoff.json ({N} CMs, {A} Applied / {D} Documented / {S} Skipped)
[CHECKPOINT] Handoff schema validation: PASSED (10 top-level keys, 6 per-CM keys, 0 extra keys, counts match)
[CHECKPOINT] Upstream handoff (generate-security-skill-files) preserved: .sde-handoff.json (untouched)
```

**Gate:** If validation fails after rebuild, **DO NOT proceed to Step 7**. Step 7 is destructive (deletes `skills/` and `security/`) and cannot be undone without re-running the full skill.

---

## Step 7: Cleanup Generated Spec Files

**Purpose:** Generated spec files contain code examples (vulnerable patterns, SQL injection examples, eval() examples) that may trigger SAST false positives. Remove them after all fixes are applied.

### 7.1 Remove Generated Directories

```bash
cd {repository_path}

# Remove skills directory (contains generated skill files)
rm -rf skills/

# LEGACY/DEFENSIVE: neither create-security-plan-from-specs nor setup-security-plan-from-repo
# creates a `security/` directory (they only generate `skills/` + root AGENTS.md). This is kept
# only to clean up artifacts from older skill versions; it is a harmless no-op on current runs.
rm -rf security/
```

### 7.2 Verify Cleanup

```bash
ls security/ 2>/dev/null || echo "✓ security/ removed"
ls skills/ 2>/dev/null || echo "✓ skills/ removed"
```

**Output:**
```
[CHECKPOINT] Cleanup: Generated spec files removed
- security/: REMOVED
- skills/: REMOVED
```

### 7.3 AGENTS.md Cleanup Options

Ask the user via `ask_question`:
- **Prompt**: "How should the AGENTS.md file be handled?"
- **Options**:
  - `{"id": "remove_section", "label": "Remove only the security section (between markers), keep original content"}`
  - `{"id": "keep_merged", "label": "Keep the merged AGENTS.md as-is"}`
  - `{"id": "keep_all", "label": "Keep everything (no cleanup)"}`

If "remove_section": Delete content between `SDE-SECURITY-HARDENING-START` and `SDE-SECURITY-HARDENING-END` markers (inclusive). Keep all other content intact.
If "keep_merged" or "keep_all": Leave the file unchanged.

### 7.4 Important Notes

- This cleanup prevents SAST tools from flagging code examples in documentation as vulnerabilities
- All fixes have already been applied to actual source files, so spec files are no longer needed

---

## Step 7.5: Restore Archived AI Configuration Files

**Note:** AGENTS.md was NOT archived by `generate-security-skill-files` (it was merged instead). Do NOT attempt to restore AGENTS.md from the archive.

**Purpose:** Restore pre-existing AI assistant configuration files that were archived by `generate-security-skill-files` (its Step 7.5 repo-prep, MCP-116; the archive path comes from the handoff's `ai_backup_archive`).

### 7.5.1 Check for Archive

```bash
cd {repository_path}

# Prefer the handoff's ai_backup_archive path; fall back to the default filename.
ARCHIVE="${ai_backup_archive:-.sde-ai-backup.tar.gz}"

if [ -n "$ARCHIVE" ] && [ -f "$ARCHIVE" ]; then
    # Archive exists - restore files
    tar -xzvf "$ARCHIVE"
    rm "$ARCHIVE"
    echo "AI config files restored from $ARCHIVE"
else
    echo "No AI config archive found (handoff ai_backup_archive: ${ai_backup_archive:-null})"
fi
```

### 7.5.2 Verify Restoration

If archive existed, list restored files:

```bash
ls -la .cursor/rules .cursorrules .claude/CLAUDE.md CLAUDE.md \
       .codeium/instructions.md .continue/instructions.md \
       .github/copilot-instructions.md AGENTS.md 2>/dev/null || true
```

### ✅ CHECKPOINT

```
[CHECKPOINT] AI Config: Restored {N} files from .sde-ai-backup.tar.gz
```
OR
```
[CHECKPOINT] AI Config: No archive to restore
```

---

## Context Limit Handling

If approaching context limits mid-execution:

```
=== CONTEXT CHECKPOINT ===
Skill: apply-security-fixes
Scope: {all / domain={name} / single_cm={id} / one_by_one}
Progress: {done}/{scoped_total}
Applied so far: {A}
Documented so far: {D}
Skipped so far: {S}
Last completed: {countermeasure_id}
Remaining items: [{id1}, {id2}, ...]
Status: INCOMPLETE - requires continuation
===========================

To resume: Say "continue" and I will resume from {countermeasure_id}
```

**On resume (RESUME PROTOCOL -- verify FIRST, re-derive from disk; multi-session is normal):**
- **STEP 0 (FIRST ACTION):** if `.sde-security/verify-apply-output.sh` exists, run it and paste raw output; else regenerate + run it. Its output objectively identifies which scoped CMs still lack a terminal status (catches a context-death mid-run).
- Re-derive the done-set from COMPACT sources -- the **AGENTS.md ledger Status column** (`grep`; authoritative) -- NOT by reading file bodies. (In-file SKILL.md `**Status:**` stamps are a secondary mirror present only on Format A/C; Format B has none, so do NOT rely on in-file stamps for the done-set or you will silently drop Format B.) CMs with a terminal ledger Status are done.
- DO NOT restart from beginning; continue from exactly the incomplete CMs; skip already-processed ones.
- Run the APPLY COMPLETENESS AUDIT + FROM-SCRATCH FINAL VERIFICATION before completion.

---

## Forbidden Actions

| Action | Why Forbidden |
|--------|---------------|
| A script applying/generating/rewriting CODE FIXES, deciding what to fix, or analyzing code | Code analysis + fixes are AI-only inline work. (Mechanical scripts -- partition, count, verify, and SDE note posting WITH completeness-verify+retry -- are allowed per the SHELL TOOL USAGE POLICY; git/build/test are allowed.) Do NOT improvise a bulk code-editing script |
| Skipping MCP verification | Connection must be confirmed |
| Skipping user input gathering | Skill must be repository/project agnostic |
| **Auto-proceeding with handoff without user confirmation** | User MUST confirm they want to use detected values |
| **Assuming repository from handoff/scan without asking** | User may want different repository |
| **Using detected project without user confirmation** | User may want different project |
| **Using default values without user confirmation** | All inputs require explicit user approval |
| Stopping before scoped remaining = 0 | Contract violation (user "stop" in one-by-one excepted) |
| Skipping per-CM progress update after any CM | Status must be persisted to disk immediately |
| Agent-initiated early stop in scoped mode | Only user "stop" in one-by-one is valid early exit |
| Creating `*_secure.*` files | Violates in-place rule |
| Saying "critical fixes done" | Rationalization |
| Outputting summary before gate | Premature completion |
| Skipping progress output | Contract violation |
| Asking "should I continue?" | Never ask - always continue |
| Requesting elevated shell permissions for local file operations | Sandbox-bypass (`required_permissions: ["all"]`) causes permission prompts that can abort the command entirely. Use default sandbox permissions; only escalate for network access to external hosts |
| **Declaring apply complete while any file-tracked CM (incl. Format B library-sourced) lacks a terminal LEDGER status** | The APPLY COMPLETENESS AUDIT re-derives terminal status from the AGENTS.md ledger rows; every CM must be Applied/Documented/Skipped in its ledger row (Format B has no in-file status — the ledger row is authoritative) |
| **Tracking CM progress only in memory / chat / TodoWrite** | The on-disk AGENTS.md ledger rows are the authoritative single source of truth (in-file SKILL.md `**Status:**` is a secondary mirror on Format A/C only) |
| **Batch-updating statuses at the end instead of per-CM write-through** | Each CM status must be persisted immediately via LEDGER WRITE-THROUGH |
| **Advancing to the next CM before the ledger write is confirmed on disk** | Re-read the AGENTS.md ledger row (authoritative) before the loop advances (plus in-file SKILL.md Status when the file has that anchor) |
| Batch status updates (`sed`, `find -exec`, shell loops on SKILL.md files) | Bypasses per-CM analysis, causes misclassification (Rule 8) — process each CM individually through the Step 3 loop |
| Blanket category-to-status mapping (e.g., "all INFRA = Documented") | Misclassifies CMs that have applicable config files — evaluate each CM individually against actual repo files |
| Skipping SKILL.md reading for any CM | Misses task recipe details; cannot produce CM PROCESSING PROOF block — read every CM's SKILL.md completely before processing |
| Processing CMs outside the main Step 3 loop | Circumvents progress tracking, proof blocks, and per-CM verification — all CM processing happens inside the loop |
| Skipping a library-sourced SKILL.md because it lacks "Code to Fix" section | Library files use different sections (see Step 3.1 Format Detection) — detect YAML front-matter; use Decision Table + Gotchas + Quick Verification |
| **Spawning a subagent on Composer 2 (`composer-2.5-fast`) or any model other than the parent's** | Composer 2 / weaker models silently abandon loops, use wrong endpoints, skip CMs, lose context -- any subagent MUST use the parent agent's model (set `model` explicitly); in Cursor override the Composer-2 default or run inline |
| **Delegating in a way that lets CMs be silently skipped, or treating delegation as transferring completeness** | The parent ALWAYS re-derives terminal status for every scoped CM from disk + SDE; delegate only bounded, verifiable sub-tasks; every subagent emits `[PROGRESS]` and the parent verifies every CM |

---

## Step 8: Commit and Handoff

### 8.1 Commit Changes (If Git Enabled)

**If `git_enabled = true`:**

After all fixes applied, commit the changes:

```bash
cd {repository_path}

git add -A
git commit -m "[Security] Apply security hardening fixes

Applied {A} code fixes from SD Elements countermeasures.
Documented {D} non-code requirements.

SD Elements Project: {project_name} (ID: {project_id})
Total countermeasures addressed: {N}
"
```

Output: `[CHECKPOINT] Git: Changes committed to {security_branch}`

**Instruct user:**
```
Changes are on branch: {security_branch}
To merge into main branch:
  git checkout main
  git merge {security_branch}
```

**If `git_enabled = false`:**
- Skip commit, output: `[CHECKPOINT] Git: Skipped (not initialized)`

**Next skill expects:**
- All CODE_FIX/ML_CODE countermeasures have fixes in source files
- All ML_DOC/INFRA countermeasures documented (PROCESS already noted by generate-security-skill-files)
- `.sde-apply-handoff.json` written with per-CM audit data (Step 6.5, before cleanup)
- Countermeasure notes added in SD Elements for each processed countermeasure

---

## Handoff to Next Skill

**Only output this AFTER the completion gate passes (Step 5 MATCH = YES or `one_by_one` session summary) AND Steps 6–8 have completed (handoff file written, cleanup done, commit if git enabled):**

```
✅ SKILL COMPLETE: All scoped fixes applied

=== FINAL COUNTS ===
Applied: {A}
- CODE_FIX: {count}
- ML_CODE: {count}

Documented: {D}
- ML_DOC: {count}
- INFRA: {count}

Skipped: {S}

PROCESS (note-only, handled by generate-security-skill-files): {process_count}

SD Elements notes: {notes_added}/{file_tracked} added

Total: {A + D + S} / {file_tracked} (100%)
(When scope != all, replace file_tracked with scoped_total — see Step 5 Scoped gate)
====================

Stored values for next skill (persisted to `.sde-apply-handoff.json` in Step 6.5):
- repository_path: {path}
- project_id: {id}
- scope: {all / domain={name} / single_cm={id} / one_by_one}
- security_branch: {branch_name or N/A}
- notes_added: {notes_added}
- handoff_file: .sde-apply-handoff.json ({N} CMs recorded)
- upstream_handoff: .sde-handoff.json (generate-security-skill-files, preserved)

Files modified (per-CM in handoff):
- {file1}
- {file2}
...

Ready for: @sde-skills/code-scan-verification-validation

The next skill reads `.sde-apply-handoff.json` written in Step 6.5 to know
which CMs were applied, which files were modified, and each CM's category.
It fetches the remaining CM context (title, text, problem, tags, how_tos)
live from SDE via `project_countermeasures op=get`, verifies each fix via
AI code analysis, and posts Verification Notes to SDE via `verification op=create`.
```
