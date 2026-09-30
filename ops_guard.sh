#!/bin/bash
# Operator identity check shared by the deployment scripts.
#
# These scripts start and stop the application's containers and create the
# directory holding the database volume, so running one is a privileged act.
# The check lives here rather than being repeated in each script: three
# copies drift, and the copy that drifts is the one nobody notices.
#
# SDE_DEPLOY_ROLE is expected to be set by the operator's own environment or
# by the CI/CD system that has already authenticated them. This guard does
# not authenticate anybody by itself; it refuses to act when no identity has
# been established upstream.

require_operator() {
    local script_name="${1:-$(basename "${BASH_SOURCE[1]}")}"

    if [ "${SDE_DEPLOY_ROLE:-}" != "operator" ]; then
        echo "${script_name}: refusing to run without an authorized operator identity." >&2
        echo "Set SDE_DEPLOY_ROLE=operator only from an authenticated context." >&2
        return 1
    fi

    return 0
}

# Resolve an external command to an absolute path under the fixed PATH.
#
# The scripts set PATH themselves and mark it readonly, so resolution here
# cannot be redirected by the caller. Resolving rather than hardcoding
# /usr/local/bin/docker: the binary lives in different places on different
# hosts (Homebrew on Apple silicon puts it under /opt/homebrew), and a
# hardcoded path that is wrong fails closed in a way that looks like the
# guard misfiring. What is checked is the property that matters -- the
# result is absolute, is executable, and sits in a directory that is not
# writable by other users, since a writable directory means the name can be
# replaced between resolution and execution.
resolve_binary() {
    local name="$1" path dir mode

    path="$(command -v "$name" 2>/dev/null || true)"

    if [ -z "$path" ] || [ "${path#/}" = "$path" ]; then
        echo "ops_guard.sh: $name did not resolve to an absolute path." >&2
        return 1
    fi

    if [ ! -x "$path" ]; then
        echo "ops_guard.sh: $path is not executable." >&2
        return 1
    fi

    # Parameter expansion rather than dirname: resolving a binary should not
    # itself depend on resolving a binary, and with PATH already narrowed
    # the external would be the next thing to fail.
    dir="${path%/*}"
    [ -n "$dir" ] || dir=/

    mode="$(stat -f '%Lp' "$dir" 2>/dev/null || stat -c '%a' "$dir" 2>/dev/null || echo 777)"

    # The group- and other-write bits, checked from the mode rather than
    # with `[ -w ]`. `-w` answers "can *I* write here", which is true for a
    # directory the current user owns and says nothing about whether anyone
    # else can -- and "anyone else can replace this binary between resolving
    # it and running it" is the question.
    if [ $(( 8#$mode & 8#022 )) -ne 0 ]; then
        echo "ops_guard.sh: $dir is writable by others; refusing $name." >&2
        return 1
    fi

    printf '%s\n' "$path"
}

# A bounded wait for the docker commands, resolved once.
#
# `timeout` is GNU coreutils and is absent from a stock macOS, where it
# arrives as `gtimeout` if it arrives at all. Calling it unconditionally
# turned a hang into "timeout: command not found" followed by the script
# drawing a conclusion from a command that never ran, which is worse than
# the hang it was meant to prevent. When neither is present the command
# runs unbounded: an operator at a terminal can interrupt it, and silently
# skipping the command instead would be a false result.
if command -v timeout >/dev/null 2>&1; then
    run_bounded() { timeout "$@"; }
elif command -v gtimeout >/dev/null 2>&1; then
    run_bounded() { gtimeout "$@"; }
else
    run_bounded() { shift; "$@"; }
fi
