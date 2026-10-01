---
name: use-indirect-object-reference-maps-if-accessing-files
description: Use server-side indirect file reference mapping to prevent access control bypass through user-controlled file IDs, filenames, or paths. Use when Python code reads files based on request or CLI supplied identifiers.
---
# Use indirect object reference maps if accessing files

## What This Skill Does
This skill fixes access control bypass through user-controlled file keys by replacing direct use of client-supplied filenames, file IDs, or paths with a server-side indirect reference map. In Python, the secure pattern is to resolve a client-visible document reference to a known server-side path, verify the current user is authorized for that mapped object, and only then call file APIs such as `open()` or `Path.open()`. If direct filenames must still be accepted, this skill also supports fixed-directory enforcement and strict filename allowlists.

## Decision Table
| Situation | Action |
|-----------|--------|
| User input is passed directly into `open()`, `os.path.join()`, `Path(...)`, or `Path.open()` for file lookup | Apply an indirect object reference map and resolve only known server-side mappings |
| The feature returns file content based on request params, form fields, route values, query strings, or CLI args | Replace client-visible filenames/paths with high-entropy indirect references tied to the authorized file |
| Direct filenames must be accepted for a limited file-serving feature | Restrict access to one fixed base directory, normalize with `Path.resolve()`, and reject names that escape it |
| A small known set of files is valid | Add a strict server-side allowlist for filenames and extensions before any file access |
| Code already resolves a server-side mapping, checks authorization, and rejects unknown references | No action needed |

## Boundaries

### Can Do
- Replace direct user-controlled file identifiers with server-side indirect references
- Add authorization checks before resolving and opening mapped files
- Harden direct filename handling with fixed-directory checks and filename allowlists

### Cannot Do
- Infer the correct business authorization model without application context
- Secure file access if other code paths still open user-controlled paths directly
- Prevent exposure caused by overly broad file permissions or insecure file contents

## Gotchas
- Using readable keys like `"public"` or sequential IDs as the only references: these are easy to enumerate; prefer high-entropy IDs such as `uuid.uuid4().hex`
- Checking authorization after `open()`: this is too late because the file path was already resolved and accessed
- Joining a base directory with untrusted input and stopping there: `os.path.join()` alone does not prevent traversal or access to another user's file

## Quick Verification
```bash
# Confirm an indirect resolver or mapping exists
rg -n "INDIRECT_DOC_MAP|indirect_map|resolve_indirect_doc_id|uuid\.uuid4\(\)|uuid\.uuid4\(\)\.hex" .

# Find likely unguarded dangerous file access that may still use request/CLI controlled values
rg -n "open\s*\(\s*(filename|file_name|path|file_path|doc_id|doc_ref|user_input|sys\.argv\[|request\.(args|form|json)|input\()|Path\s*\(\s*(filename|file_name|path|file_path|doc_id|doc_ref|user_input)|\.open\s*\(\s*['\"]r['\"]" .

# Parse Python files to catch syntax issues after edits
python -m compileall .

# Run project tests if present; works across apps, CLIs, libraries, and services
python -m pytest -q
```