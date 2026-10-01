---
name: prevent-path-traversal-file-path-manipulation-bash-shell
description: Prevents path traversal and unsafe file path use in Bash/shell scripts; use when untrusted input influences filesystem paths or shell-accessible paths.
---

# Prevent path traversal and file path manipulation (Bash/Shell)

## What This Skill Does
Helps detect and fix Bash/shell code where user-controlled input (CLI args, env vars, API params, config) is used to build file paths or shell-accessible paths without proper restriction. It guides the assistant to normalize and constrain paths to trusted directories, validate filenames, apply allowlists, and enforce safe permissions so attackers cannot use `../`, absolute paths, or crafted names to read, write, or execute unintended files.

## Decision Table
| Situation | Action |
|-----------|--------|
| Script concatenates user input into a path (e.g., `file="$LOG_DIR/$1"` or `cat "$1"`) | Introduce a fixed base directory and a validator that normalizes and rejects paths that escape that base; use `basename` or realpath checks instead of raw concatenation. |
| Script allows arbitrary filenames or subpaths from user input (e.g., `"$1.log"` or `logs/$1`) | Add strict validation: reject empty/absolute paths and `..` segments; optionally constrain with a filename regex and use only the validated result. |
| Script chooses among a small, known set of files based on user input (e.g., `case "$1" in app|error|access)`) | Replace ad‑hoc checks with a whitelist/allowlist mapping input keys to exact filenames or paths; refuse any non-whitelisted value. |
| Script passes user-controlled paths into other tools or subshells (e.g., `cmd="cat $1"; eval "$cmd"` or `tar -xf "$archive"` from user input) | Remove `eval`, avoid building shell strings; validate the path, then pass it as a single, quoted argument to the tool. Add traversal/regex checks before use. |
| Script already normalizes with `realpath`, compares against a trusted base, and rejects out-of-tree results | No action needed beyond style improvements; preserve the security checks and avoid loosening validation. |

## Boundaries

### Can Do
- Identify unsafe use of user-controlled input in Bash/shell file operations (`cat`, `cp`, `mv`, `rm`, `tar`, `find`, redirections, etc.).
- Propose safe patterns using a fixed base directory, `realpath`, `basename`, and explicit checks for traversal (`..`) and absolute paths.
- Introduce simple whitelists/allowlists and regex-based filename validation where only a few files or formats are intended.
- Suggest permission-related safeguards (e.g., `umask`, `chmod 600`) for sensitive files and directories.

### Cannot Do
- Prove complete absence of path traversal in complex multi-script systems or when external tools expand paths further.
- Automatically infer the correct allowed directory tree or full whitelist when business rules are unclear.
- Fix deeper command injection issues unrelated to paths (e.g., arbitrary flags or arguments beyond filenames) without additional guidance.
- Guarantee that OS-level permissions, SELinux/AppArmor, or mount options are correctly configured outside the script.

## Gotchas
- Assuming `basename` alone is enough: stripping directories with `basename "$user"` avoids obvious `../` but still allows unexpected filenames unless you also validate characters and, if needed, apply a whitelist.
- Relying only on string checks for `../`: blocking the literal substring `../` can be bypassed with patterns like `.. //` or encoded paths; prefer `realpath` (or `readlink -f`) and ensure the resolved path stays under a trusted base directory.
- Forgetting absolute paths: validation must explicitly reject inputs starting with `/` (and sometimes `~`) if the script is intended to operate only inside a specific application directory; otherwise users can jump outside the sandbox.

## Quick Verification
```bash
# 1) Basic traversal test against a fixed-directory script
# Expect: script rejects or errors, not reading /etc/passwd
./script.sh "../../etc/passwd" || echo "Traversal blocked"

# 2) Absolute path test
# Expect: script rejects absolute paths
./script.sh "/etc/passwd" || echo "Absolute path blocked"

# 3) Valid relative filename test
# Assume logs/app.log exists under the allowed directory
./script.sh "app.log"

# 4) Permission enforcement test (if script checks permissions)
touch secret.txt
chmod 600 secret.txt
./script.sh "secret.txt"   # should succeed if inside allowed dir

chmod 644 secret.txt
./script.sh "secret.txt"   # should now reject due to permissive mode
```