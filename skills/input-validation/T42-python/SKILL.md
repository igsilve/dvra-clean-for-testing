---
name: avoid-untrusted-server-side-selection
description: Use when Python code lets request or other untrusted input choose a server-side page, view, template, include target, or file-backed template resource.
---

# Avoid relying on untrusted data for server-side selection

## What This Skill Does
This skill fixes cases where untrusted input controls which server-side page, view, template, or file-backed template resource gets selected. In Python, the safe pattern is to treat user input only as a lookup key into a fixed server-defined mapping, validate it with a strict full-input allowlist, enforce membership in an approved set, and fail closed for unknown values instead of concatenating input into template names, file paths, include targets, or `open()` calls.

## Decision Table
| Situation | Action |
|-----------|--------|
| User input is passed to `open()`, template loaders, or path-building code to choose a page/template | Replace direct selection with a fixed server-side mapping such as `TEMPLATES[validated_key]` |
| A selector comes from request params, route params, CLI args, env vars, or job payloads | Validate type, length, and full-input allowlist before any selection logic |
| Selector format is valid but value is not one of the known server-defined choices | Reject with a safe error or use a fixed safe default chosen by server code |
| Code uses Flask/Jinja rendering such as `render_template_string()` after reading a file chosen by input | Remove the file selection path and select only from approved in-memory or server-defined templates |
| Code already validates with `fullmatch()` and checks membership in a fixed set/map before selection | No action needed |

## Boundaries

### Can Do
- Replace untrusted selector-driven resource selection with a fixed mapping
- Add strict selector validation using `re.fullmatch()` plus length/type checks
- Add explicit membership checks against a server-defined allowed set

### Cannot Do
- Prove a selector is safe if it still directly controls file paths, template names, or include targets
- Infer the correct business-approved selector list without project knowledge
- Fix unrelated template injection, XSS, or authorization flaws beyond selector handling

## Gotchas
- Using regex validation alone: syntactically valid but unknown values can still select unintended resources unless membership is checked too
- Using `re.match()` instead of `fullmatch()`: partial matches can allow dangerous trailing content such as traversal or markup
- Falling back to `open(page_name)` or dynamic template names on validation failure: this reintroduces untrusted server-side selection instead of failing closed

## Quick Verification
```bash
# Confirm a strict validator or approved mapping exists
rg -n "fullmatch\(|re\.compile\(|ALLOWED_SELECTORS|TEMPLATES\s*=\s*\{|validate_page_name\(" .

# Find unguarded dangerous file/template selection patterns driven by input
rg -n "open\s*\(|render_template\s*\(|render_template_string\s*\(" . 

# Build + test using common Python entry points across app types
python -m compileall . && (python -m pytest -q || python -m unittest discover -v)
```