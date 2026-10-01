---
name: test-prevention-of-injection-attacks-bash-shell
description: Hardens Bash/Shell command execution against injection by validating inputs, avoiding shells/eval, and restricting commands; Use when user or external data can influence shell commands or subprocess execution.
---

# Test prevention of injection attacks (Bash/Shell)

## What This Skill Does
Prevents shell injection in scripts and applications that invoke Bash/Shell by finding places where untrusted input reaches shell commands or dynamic evaluation, then enforcing strict input validation, argument-based execution (no `shell=True` / backticks), removal of `eval` on untrusted data, and command allow-lists with size limits to avoid arbitrary command execution and resource abuse.

## Decision Table
| Situation | Action |
|-----------|--------|
| Python/Node/other code builds a command string with user input and runs it via `shell=True`, `exec`, backticks, or `/bin/sh -c` | Replace with APIs that take an argument list (`shell=False`, `execFile`, `spawn`), and pass user input only as validated arguments |
| Script or app concatenates user input directly into a shell command (e.g., `"cmd " + user_input` or `"cmd $user_input"`) | Introduce strict allow-list validation + size limits, and refactor to treat user data as data only (no command string building) |
| Code uses `eval`, `bash -c`, or similar dynamic evaluation on expressions derived from external input | Remove or block dynamic evaluation; replace with explicit parsing/branching or lookup tables over allowed operations |
| User can choose arbitrary commands, flags, or subcommands to execute | Map user choices to a predefined allow-list of safe commands/operations and reject anything not in the list; avoid free-form flags |
| Inputs are already validated with allow-lists, size limits, and executed with `shell=False` / argument arrays | No action needed (but keep an eye on future changes that reintroduce dynamic shells or eval) |

## Boundaries

### Can Do
- Detect and refactor vulnerable patterns like `subprocess.run(cmd, shell=True)` or `exec("... " + user_input)`.
- Introduce centralized validation helpers that enforce positive (allow-list) checks and per-field size limits before command execution.
- Replace free-form command execution with operation/command allow-lists and fixed argument templates, while preserving expected behavior where feasible.

### Cannot Do
- Automatically infer business-appropriate allow-list rules or what exact commands/flags should be considered “safe” without human input.
- Protect code that is entirely outside the calling context (e.g., separate services that are only reachable over the network) without corresponding API-level validation there.
- Eliminate all denial-of-service risks (e.g., running a “safe” command on huge data sets) without additional resource and concurrency controls.

## Gotchas
- Assuming escaping is enough: Relying only on quoting or escaping user input in a command string is brittle; prefer no-shell APIs (`shell=False`, argument lists) so the shell never parses user data at all.
- Overly broad regex validation: Using patterns like `^[\s\S]*$` or allowing metacharacters (`;`, `&`, `|`, `>`, `*`, `?`, `$`, `(`, `)`) defeats the purpose of positive validation—inputs must be constrained to what is actually needed.
- Forgetting length limits: Even with good character validation, unbounded input size can still cause resource exhaustion or timeouts when commands process large data; always enforce max lengths before expensive work.

## Quick Verification
```bash
# 1. Run the vulnerable Python example with an injection payload
python app_vulnerable_code.py "hello; echo HACKED"   # EXPECT: contains "HACKED" (demonstrates vulnerability)

# 2. Run the fixed Python code with the same payload
python app_fix_python_code.py "hello; echo HACKED"   # EXPECT: "Invalid input" or benign output; no extra command runs

# 3. Test oversized input rejection
python app_fix_python_code.py "$(python - << 'EOF'
print('A' * 10000)
EOF
)"   # EXPECT: "Invalid input" (fails size limit)

# 4. Smoke-test allowed operations
python app_fix_python_code.py "status"               # EXPECT: "User requested: status status" (or similar safe echo)
python app_fix_python_code.py "rm -rf /"             # EXPECT: "Invalid input" or harmless echo; no deletion occurs
```