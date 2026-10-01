---
name: prevent-file-upload-vulnerabilities-bash-shell
description: Harden file upload handling to block Bash/Shell script abuse in apps that save uploads or pass them to shell; Use when code writes user uploads to disk or calls shell commands with upload-derived paths/content
---

# Prevent file upload vulnerabilities (Bash/Shell)

## What This Skill Does
Prevents arbitrary Bash/Shell execution via uploaded files. It detects when uploads are accepted without strict type/size/content checks, stored in unsafe locations, or later passed to shell commands (e.g., `bash filePath` or `child_process.exec` with concatenated paths). It then applies extension/MIME whitelisting, size caps, safe storage, content scanning for shell indicators, unique filenames, and removal of direct shell execution of uploaded content.

## Decision Table
| Situation | Action |
|-----------|--------|
| Upload handler writes request body to disk using user-controlled filename or path (no validation) | Introduce strict extension allow-list, block shell/script extensions, and generate random safe filenames under a fixed upload root |
| Code accepts any upload size or streams body directly to disk/memory without limits | Add explicit max-bytes checks before/while reading; abort the request and respond with 4xx when exceeded |
| Uploaded file paths or contents are used to build shell commands (e.g., `child_process.exec('/bin/bash ' + filePath + ' ' + analysis)`) | Remove shell execution of uploads; if necessary, switch to `execFile`/`spawn` with vetted binaries and argument arrays, never executing uploaded files themselves |
| Upload logic stores files under webroot or world-readable/executable directories | Move uploads into a dedicated non-webroot directory with restrictive permissions (e.g., `0o700`) and safe path construction from a trusted base |
| Text-like uploads (e.g., `text/plain`, `application/json`) are accepted without content checks | Add content scanning for shell shebangs and suspicious shell tokens; reject files that look like shell scripts even if the extension is allowed |
| Code already enforces strict allow-list, size limits, safe directory, no shell use on uploads, and content checks where relevant | No action needed; keep configuration and helper functions but avoid redundant changes |

## Boundaries

### Can Do
- Detect and refactor upload flows that:
  - Use user-controlled filenames/paths.
  - Lack extension/MIME/size/content validation.
  - Store files in generic or unsafe locations.
  - Use uploads as inputs to shell commands.
- Introduce reusable helpers for:
  - Extension/MIME allow-lists with hard-blocked shell/script types.
  - File size enforcement and early request termination.
  - Secure upload directories, unique filenames, and path normalization.
  - Basic shell-oriented content scanning for text-like uploads.
- Replace obviously dangerous shell execution of uploaded files with safe, non-executing behavior while preserving necessary business logic (e.g., metadata processing).

### Cannot Do
- Guarantee detection of all possible malicious payloads: heuristic content scans can miss cleverly obfuscated scripts.
- Decide business-appropriate allow-lists or size limits without app-specific context; you may need to adjust defaults.
- Fix OS-level or deployment misconfigurations (e.g., web server auto-executing files in upload directories) beyond what application code controls.
- Add heavyweight third-party scanning tools, antivirus, or DLP systems; only lightweight in-process checks are assumed.
- Preserve behavior that fundamentally requires executing user-supplied scripts; the secure approach is to remove that capability.

## Gotchas
- Assuming extension checks alone are sufficient: Attackers can rename scripts with allowed extensions (e.g., `evil.sh` → `evil.txt`). Combine extension allow-lists with MIME/signature checks and content scanning for shell indicators.
- Continuing to use `child_process.exec` with concatenated strings: Even when you validate uploads, building shell commands via string concatenation still allows injection through other parameters. Use `execFile`/`spawn` with argument arrays and avoid executing uploads entirely.
- Storing uploads under webroot with default permissions: Even if files are not executed via shell, direct HTTP access can still expose sensitive data or scripts. Always store uploads in a non-webroot directory with restrictive permissions and safe path construction.
- Trusting only declared MIME type from clients: Browsers/clients can lie about `Content-Type`. Always treat client MIME as untrusted and, where possible, validate via simple magic-byte checks or stricter server-side logic.

## Quick Verification
```bash
# 1. Oversized upload is rejected
curl -v -X POST "http://localhost:3000/upload?filename=big.txt&mimetype=text/plain" \
  --data-binary "@large_10mb_file.bin"

# Expect: 4xx/413-style error, connection closed early, file not stored.

# 2. Attempt to upload a Bash script by extension
echo -e '#!/bin/bash\nrm -rf /tmp/marker_from_upload' > evil.sh
curl -v -X POST "http://localhost:3000/upload?filename=evil.sh&mimetype=text/plain" \
  --data-binary "@evil.sh"

# Expect: 4xx error, file rejected, no script stored or executed.

# 3. Attempt to bypass via allowed extension but shell content
cp evil.sh disguised.txt
curl -v -X POST "http://localhost:3000/upload?filename=disguised.txt&mimetype=text/plain" \
  --data-binary "@disguised.txt"

# Expect: 4xx error due to content scan failing (shebang / suspicious tokens).

# 4. Confirm uploaded files are stored safely (after a valid upload)
# Replace safe.png with a small real PNG file
curl -v -X POST "http://localhost:3000/upload?filename=safe.png&mimetype=image/png" \
  --data-binary "@safe.png"

# Then inspect server-side:
ls -l ./uploads_secure
# Expect: files with random names, non-world-readable dir (mode 700), no .sh/.bash/etc.
```