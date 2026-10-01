---
name: test-prevention-of-path-traversal-and-file-path-manipulation-bash-shell
description: Secure shell-invoking code and file operations against path traversal and unsafe path manipulation in Bash/Shell; Use when untrusted input can influence paths, filenames, or shell commands
---

# Test prevention of path traversal and file path manipulation (Bash/Shell)

## What This Skill Does
Detects and fixes cases where untrusted input controls file paths or directory names used by Bash/shell or filesystem operations, and could enable path traversal (e.g., `../`, absolute paths) or unintended file access. Guides you to normalize and constrain paths to a safe base directory, validate filenames, avoid `shell=True` / raw shell execution, and apply whitelist and permission checks around file access.

## Decision Table
| Situation | Action |
|-----------|--------|
| Python/Node/other code builds a shell command string like `ls -1 ${userInput}` or `f"ls -1 {target_path}"` and executes it with `shell=true` / `shell=True` | Replace with an argument list (no shell), and route `userInput` through a safe path validator + base-directory containment check |
| User-controlled value is joined/concatenated into a filesystem path (e.g., `base + "/" + user`, `path.join(BASE, userPath)`) | Introduce a shared helper that validates segments, rejects `..`, absolute paths, and dangerous prefixes, then resolves against a fixed base and enforces containment |
| User provides filenames or keys selecting files (e.g., logs, configs, exports) | Replace free-form filenames with either: (1) strict regex-validated filenames (no separators), or (2) identifiers mapped to a whitelist of canonical paths under a fixed base |
| Code already canonicalizes with `os.path.abspath`/`path.resolve` and checks that the result is under an allowed base directory, and does not invoke a shell | No action needed; keep existing helper, but ensure all file operations consistently use it |
| Sensitive files are read/written in shared directories (e.g., temp, shared volumes) | Add explicit permission checks (ownership and mode) around file access, and fail closed when checks or stats fail |

## Boundaries

### Can Do
- Detect and refactor vulnerable patterns where untrusted input reaches shell commands (`shell=True`, `bash -c`, backticks) or file operations without path validation.
- Introduce centralized helpers in Python/Node/other languages that: normalize paths, enforce base-directory containment, validate filenames via regex, and apply whitelists.
- Replace path-based user control with identifier-based whitelists mapping to canonical, safe paths.

### Cannot Do
- Cannot guarantee OS-level hardening (mount options, chroot, container sandboxing); only constrains paths at the application level.
- Cannot safely allow arbitrary user-specified absolute paths; the approach assumes you can define trusted base directories or whitelists.
- Cannot retrofit correctness if the functional requirements explicitly demand unrestricted filesystem access across arbitrary directories (that’s a product decision).

## Gotchas
- Assuming that removing `../` strings is enough: Attackers can still break out using encoded traversal, mixed separators, or absolute paths; always normalize then enforce that the resolved path stays within a fixed base directory.
- Relying only on `os.path.basename` or similar: While it strips directory components, it can silently change the intended target (e.g., `/etc/passwd` → `passwd` in your data dir); ensure this behavior is acceptable and combine with strict filename regexes.
- Fixing the path but keeping `shell=True`: Even with sanitized paths, `shell=True` (or equivalent) still exposes command injection risks; for simple operations like `ls`, `cat`, or `cp`, switch to argument lists and disable the shell.

## Quick Verification
```bash
# 1) Basic traversal attempt against the fixed app:
python app_fix_original_code.py ../
python app_fix_original_code.py "../../etc"
python app_fix_original_code.py "/etc/passwd"

# Expectation: each command raises a clear error (path traversal or absolute path not allowed)
# and does not list or touch files outside the allowed base directory.

# 2) Normal usage within allowed directory:
python app_fix_original_code.py .
python app_fix_original_code.py some_safe_subdir

# Expectation: directory contents are listed correctly.

# 3) Compare vulnerable vs. fixed behavior:
python app_vulnerable_code.py "../"             # Typically lists parent directory
python app_fix_original_code.py "../"           # Should fail with validation error

# 4) Permission enforcement check (POSIX):
# Create a world-readable directory and a restricted one, then test:
mkdir -p test_world test_private
chmod 0777 test_world
chmod 0700 test_private

# Point your validated-and-permission-checked helper at each directory
# Expectation: it should reject the world-accessible directory and allow the private one
```