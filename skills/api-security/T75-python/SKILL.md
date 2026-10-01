---
name: use-regular-expressions-that-are-not-vulnerable-to-denial-of-service
description: Use when Python code compiles or executes variable or externally influenced regular expression patterns and must reject ReDoS-prone constructs before re.compile or matching.
---

# Use Regular Expressions That Are Not Vulnerable to Denial of Service

## What This Skill Does
This skill fixes Regular Expression Denial of Service in Python by enforcing one central validation path for regex pattern strings before any `re.compile()` or regex execution occurs. It rejects known unsafe exact patterns, repeated groups, repeated groups with alternation, and `(.*a){x}` when `x > 10`, then fails closed so attacker-controlled patterns are never compiled or run.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code passes variable, config-driven, request-derived, CLI-derived, or database-loaded pattern strings into `re.compile()` | Add a central validator and require validation before compilation |
| Code calls `re.search()`, `re.match()`, `re.fullmatch()`, `re.findall()`, `re.finditer()`, `re.split()`, `re.sub()`, or `re.subn()` with a non-literal pattern | Route through a safe wrapper that validates the pattern string first |
| Code uses exact unsafe forms like `(a+)+`, `([a-zA-Z]+)*`, `(a|aa)+`, `(a|a?)+`, or `(.*a){11}` | Reject immediately and do not compile or execute the regex |
| Code builds patterns from configuration or user input in multiple places | Consolidate regex construction into one shared helper and remove direct calls |
| Pattern is hardcoded, reviewed, and not externally influenced | No action needed |

## Boundaries

### Can Do
- Add a Python validation helper that rejects ReDoS-prone pattern strings before `re.compile()`
- Replace direct dynamic use of Python `re` APIs with a guarded wrapper such as `safe_search()`
- Apply the same validation to patterns from requests, config files, CLI args, environment variables, or database values

### Cannot Do
- Prove every possible regex is safe; this skill enforces explicit deny rules and centralized validation
- Secure code that bypasses the validator and still calls `re.compile()` or other `re` APIs directly
- Fix performance issues caused by trusted hardcoded regexes unless they are also routed through the guarded path

## Gotchas
- Validating after `re.compile()`: too late, because the dangerous pattern was already compiled
- Guarding only `re.compile()`: unsafe code can still bypass the fix by calling `re.search(pattern, text)` and similar APIs directly
- Allowing alternate regex construction paths: one missed helper, config loader, or utility function can reintroduce the vulnerability

## Quick Verification
```bash
# Confirm the central guard/wrapper exists
rg -n "def (validate_safe_pattern|safe_search)\b|_EXACT_UNSAFE_PATTERNS|_REPEATED_GROUPS_WITH_REPETITION|_REPEATED_GROUPS_WITH_ALTERNATION|_WILDCARD_GROUP_REPETITION" .

# Find UNGUARDED dangerous Python regex API use that should be reviewed or replaced
rg -n "\bre\.(compile|search|match|fullmatch|findall|finditer|split|sub|subn)\s*\(" . \
  -g '!**/tests/**' -g '!**/test_*.py' -g '!**/*_test.py'

# Build/check syntax for Python source
python -m compileall .

# Run tests if present; works for apps, libraries, CLIs, and services that use pytest
python -m pytest -q
```