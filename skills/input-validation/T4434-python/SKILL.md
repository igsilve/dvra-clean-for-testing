---
name: prevent-injection-attacks-bash-shell
description: Prevents Bash/shell command injection in JavaScript/Node apps that build shell commands from external input; Use when code concatenates user data into command strings or invokes shells without validation.
---

# Prevent injection attacks (Bash/Shell)

## What This Skill Does
Helps rewrite JavaScript/Node.js code that builds or executes shell commands so that untrusted input cannot inject additional commands or shell metacharacters. It introduces strict input validation, argument-size limits, non-shell execution APIs (e.g., `execFileSync`, `spawnSync` with `shell: false`), removal of `eval` on user data, and allowlisting of commands and operations.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code concatenates untrusted input into a shell command string (e.g., `execSync("cmd " + userInput)`) | Replace with non-shell API (`execFileSync`/`spawnSync`), static executable name, and pass validated input as array arguments |
| Code uses `child_process.exec`/`execSync` with untrusted data | Prefer `execFile`/`execFileSync`/`spawn`/`spawnSync` with `shell: false`, plus strict validation and length limits on all user-influenced args |
| Code calls `eval` or similar dynamic evaluation based on user input (e.g., `eval(userOp)`) | Replace with a fixed dispatch table mapping safe keys to functions; reject unknown keys |
| Code allows arbitrary command names or options from users (e.g., `child_process.exec(userCmd)`) | Introduce an allowlist: expose only logical operation keys, map them to fixed binaries and argument builders, validate arguments per command |
| Inputs to shell-related logic are accepted without type, character, or length checks | Add centralized validators to enforce type, safe character allowlists, and strict size limits before any shell or process execution call |
| Code already uses `execFile`/`spawn` with `shell: false` and validated, bounded arguments | No action needed beyond confirming validation coverage and size limits |

## Boundaries

### Can Do
- Detect and refactor JavaScript/Node patterns where untrusted input is concatenated into shell command strings.
- Introduce and wire up centralized validators (type, whitelist regex, length limits) for shell-related inputs and arguments.
- Replace unsafe `exec`/`execSync` calls with safer `execFile`/`execFileSync`/`spawnSync` using static command names and argument arrays.
- Remove or replace `eval` and similar dynamic evaluation on user-provided strings with explicit dispatch tables.
- Implement per-command allowlists and input caps to prevent both command injection and resource exhaustion.

### Cannot Do
- Guarantee safety of commands themselves (e.g., running `rm` is still dangerous even if not injectable); human review of allowed commands is still required.
- Automatically infer all trust boundaries; you must confirm which inputs are externally controllable (HTTP, CLI, env, config).
- Fix injection risks in non-JavaScript environments or shells embedded through other languages without language-specific changes.
- Prevent all OS-level attacks (e.g., vulnerabilities in the called binary); it only addresses command construction and invocation patterns.
- Decide business-level behavior for rejected inputs or logging policies; these need application-specific choices.

## Gotchas
- Assuming quoting alone is enough: Relying only on shell quoting or escaping (`"echo " + JSON.stringify(userInput)`) still keeps the shell in play and is fragile; prefer non-shell APIs with argument arrays so the shell never parses user data.
- Validating format but not size: Applying a regex allowlist without maximum length or argument-count limits leaves the code open to resource exhaustion via extremely long or numerous arguments.
- Partial allowlists: Allowing user-controlled command names with a “soft” check (e.g., `if (!cmd.includes('rm'))`) is not an allowlist; only accept known logical keys mapped to fixed binaries, and reject everything else.
- Trusting “internal” inputs: Treat CLI args, config files, and environment variables as untrusted for shell execution contexts; they can be manipulated in many deployment setups.

## Quick Verification
```bash
# 1. Run vulnerable version with an injection payload (should FAIL after fix)
node app_vulnerable_code.js "host; rm -rf /" || echo "vulnerable path executed"

# 2. Run fixed version with benign input (should succeed, no injection)
node app_fix_original_code.js "localhost"

# 3. Test injection string against fixed version (should reject, non-zero exit or error)
node app_fix_original_code.js "host; rm -rf /" && echo "UNEXPECTED: injection passed" || echo "OK: injection blocked"

# 4. HTTP route check (from another terminal, app listening on 3000 by default)
curl "http://localhost:3000/check?target=localhost"
curl "http://localhost:3000/check?target=host;rm%20-rf%20/" -v

# 5. Optional: Search for remaining risky patterns
grep -R "child_process.exec" -n .
grep -R "eval(" -n .
```