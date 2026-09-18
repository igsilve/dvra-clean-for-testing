---
name: use-recommended-settings-and-latest-patches
description: Use when Python applications rely on third-party packages or framework defaults and need startup version enforcement, secure configuration, and fail-closed secret validation for P728/CWE-1104.
---

# Use recommended settings and the latest patches for third party libraries and software

## What This Skill Does
This skill hardens Python applications against outdated or insecure third-party components by adding startup checks for minimum approved package versions, explicitly setting secure framework options instead of relying on defaults, rejecting weak or placeholder secrets before startup, and optionally building a normalized dependency inventory for advisory review. Apply it when code uses external packages, exposes runtime versions without enforcement, or depends on framework defaults for security-sensitive behavior.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code imports third-party packages but does not enforce approved minimum versions at startup | Add a `MINIMUM_PATCHED_VERSIONS` mapping and call `assert_patched_dependencies()` before serving requests or running main app logic |
| Code uses Flask or similar framework defaults for security-sensitive behavior | Explicitly set secure config such as `DEBUG=False`, `TESTING=False`, secure cookie flags, and no-store response headers |
| Code reads `SECRET_KEY` or similar signing/session secret without validation | Add fail-closed validation that rejects missing, placeholder, or too-short values before app initialization |
| Code exposes package versions via `requests.__version__` or similar but does not block insecure versions | Replace passive version reporting with enforced checks using `importlib.metadata.version()` and `packaging.version.Version` |
| Code already enforces minimum versions, secure settings, and strong secret validation | No action needed |

## Boundaries

### Can Do
- Add Python startup guards that block execution when required packages are missing or below approved minimum versions
- Replace insecure framework defaults with explicit secure application settings in code
- Add secret validation and optional dependency inventory functions using standard Python package metadata APIs

### Cannot Do
- Determine the correct minimum safe version numbers without a maintained approved-version policy or vendor advisory input
- Guarantee every installed dependency is free of vulnerabilities solely from version comparisons in application code
- Fix vulnerabilities inside third-party packages without upgrading or replacing the affected package

## Gotchas
- Using string comparison for versions: `"2.10"` and `"2.9"` compare incorrectly as strings, so use `packaging.version.Version`
- Checking versions too late: if the guard runs after app creation or after request handling starts, vulnerable code may already execute
- Reading `SECRET_KEY` but allowing defaults like `dev` or `changeme`: this leaves signing and session protection weak even if dependency checks exist

## Quick Verification
```bash
# Confirm the secure dependency/version guard exists
rg -n "MINIMUM_PATCHED_VERSIONS|APPROVED_VERSIONS|assert_patched_dependencies|get_unpatched_packages|PackageNotFoundError|importlib\.metadata\.version|Version\(" .

# Find unguarded dangerous version usage that reports or trusts package versions without enforcement
rg -n "requests\.__version__|[A-Za-z0-9_]+\.__version__|importlib\.metadata\.version\(" . 

# Find insecure Flask defaults or missing explicit secure settings in Python code
rg -n "DEBUG\s*=\s*True|TESTING\s*=\s*True|SESSION_COOKIE_SECURE\s*=\s*False|SESSION_COOKIE_HTTPONLY\s*=\s*False|SECRET_KEY\s*=\s*[\"'](dev|development|changeme|default|secret)?[\"']" .

# Build + test using common Python toolchain commands
python -m compileall .
python -m pytest -q
```