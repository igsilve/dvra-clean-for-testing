#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# See start_app.sh: an inherited PATH lets the caller choose which binary this
# privileged script runs.
export PATH=/usr/local/bin:/usr/bin:/bin
# readonly, so nothing sourced or called later can put a writable directory
# back at the front of it.
readonly PATH

# Anything this script creates is owner-only. Set before the first file is
# created, not after: a permissive mode at creation is a window, and
# chmod afterwards does not close it.
umask 077

cd "$(dirname "$0")"
# shellcheck source=ops_guard.sh
source ./ops_guard.sh

require_operator "stop_app.sh"

DOCKER="$(resolve_binary docker)"

# One teardown at a time. Two concurrent `compose down` runs interleave
# container and volume removal, and the second can delete a volume the first
# has already begun recreating. The lock lives beside the script rather than
# in /var/lock so it does not need privileges the operator may not have.
#
# mkdir rather than a test for the file: creating a directory either succeeds
# or fails atomically, so there is no gap between checking and taking. `[ -e
# ]` followed by `touch` is two steps and the race lives between them.
# mkdir is also everywhere, which flock is not.
LOCK="$(pwd)/.deploy.lock.d"

if ! mkdir "$LOCK" 2>/dev/null; then
    # A lock held by a process that no longer exists is not a lock. Without
    # this check one crashed teardown blocks every later one until somebody
    # deletes the directory by hand.
    if [ -f "$LOCK/pid" ] && kill -0 "$(cat "$LOCK/pid")" 2>/dev/null; then
        echo "stop_app.sh: another deploy action holds the lock; not proceeding." >&2
        exit 1
    fi

    rm -rf "$LOCK"
    mkdir "$LOCK" || {
        echo "stop_app.sh: could not take the deploy lock." >&2
        exit 1
    }
fi

echo $$ >"$LOCK/pid"

# Runs on every exit path, including the error exits that set -e produces, so
# the lock is not left behind for the liveness check to clean up later.
trap 'rm -rf "$LOCK"' EXIT

# A bounded wait. Without it a container that ignores SIGTERM leaves this
# script blocked indefinitely while holding the lock, so the timeout is what
# keeps a stuck teardown from also blocking every later one.
run_bounded 120 "$DOCKER" compose down "$@"
