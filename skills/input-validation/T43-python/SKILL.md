---
name: avoid-unsafe-operating-system-interaction
description: Use when Python code handles user-controlled values that influence OS command execution, process selection, or command arguments and must prevent command injection.
---

# Avoid unsafe operating system interaction

## What This Skill Does
This skill fixes command injection risks in Python by replacing dynamic OS command execution with native Python APIs whenever possible, validating and normalizing user-controlled values before any OS-related use, and requiring structured process execution with `subprocess` argument lists instead of shell-interpreted command strings. It also helps detect cases where shell use is still present and must be tightly constrained.

## Decision Table
| Situation | Action |
|-----------|--------|
| User input is used to build a shell command string for `os.system`, `os.popen`, `subprocess.*(..., shell=True)`, or similar | Replace with native Python logic or `subprocess.run([...], shell=False)` using structured arguments |
| User input selects a command, process, or resource name | Map the input to a fixed allowlist of approved operations; reject anything else |
| User input becomes an OS-related argument or filename | Normalize early if allowed, then validate with a strict allowlist such as `^[A-Za-z0-9.@]+$`; fail closed on mismatch |
| Shell interaction is truly unavoidable | Validate first, then escape each dynamic value only at the final shell boundary |
| Code already uses native APIs or `subprocess` with argument lists and strict validation | No action needed |

## Boundaries

### Can Do
- Replace shell-driven filesystem or process tasks with native Python APIs such as `os.listdir`, `os.path.isdir`, and other standard-library operations
- Refactor unsafe process execution to `subprocess.run([...], check=True, ...)` without shell interpretation
- Add early normalization, strict validation, and allowlist-based selection for user-controlled OS-related values

### Cannot Do
- Guarantee safety if the intended behavior fundamentally requires arbitrary user-selected executables or free-form shell syntax
- Infer business-safe allowlists for commands, paths, or process names without project context
- Make shell-based code safe by escaping alone when validation and command restriction are missing

## Gotchas
- Using `subprocess.run()` with a single command string: this is still risky when paired with `shell=True` or when developers assume the string is safely parsed
- Validating after command construction: this is too late because unsafe routing or command selection may already have happened
- Allowing spaces, slashes, or traversal fragments in a supposedly strict parameter: this weakens the boundary and reintroduces command or path manipulation risk

## Quick Verification
```bash
# Confirm a strict validator or allowlist exists for OS-related input
rg -n "re\.compile\(r\"\^\[A-Za-z0-9\.@\]\+\$\"\)|fullmatch\(|_ALLOWED_[A-Z_]+\s*=" .

# Find unguarded dangerous OS execution APIs and shell-enabled subprocess usage
rg -n "os\.system\(|os\.popen\(|subprocess\.(run|Popen|call|check_call|check_output)\([^)]*shell\s*=\s*True|popen2\.|commands\." .

# Build syntax check across Python code
python -m compileall .

# Run tests if present; works for apps, libraries, CLIs, and services that use pytest
python -m pytest -q
```