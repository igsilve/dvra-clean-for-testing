#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# Set before any external command runs, including the sibling script below.
export PATH=/usr/local/bin:/usr/bin:/bin
# readonly, so nothing sourced or called later can put a writable directory
# back at the front of it.
readonly PATH

umask 077

# Resolved from this script's own location, not the caller's working
# directory. `./start_app.sh` executed whatever start_app.sh happened to be in
# the directory the operator was standing in, which is the whole attack: drop
# a file with that name anywhere writable, persuade someone to run this from
# there, and the privileged script is yours.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# shellcheck source=ops_guard.sh
source "$SCRIPT_DIR/ops_guard.sh"

require_operator "start_game.sh"

# Every file this script executes is checked for existence and type before it
# runs. A missing dependency must be a refusal rather than a shell error
# message followed by the rest of the script carrying on, and a symlink in
# place of the expected script is a substitution, not a convenience.
GAME=/app/game.py

if [ -L "$SCRIPT_DIR/start_app.sh" ]; then
    echo "start_game.sh: start_app.sh is a symlink; refusing to run it." >&2
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/start_app.sh" ] || [ ! -x "$SCRIPT_DIR/start_app.sh" ]; then
    echo "start_game.sh: start_app.sh is missing or not executable." >&2
    exit 1
fi

# Resolved after the file checks, not before: a missing dependency should be
# reported as a missing dependency, and looking for the container runtime
# first would report the absence of docker instead.
DOCKER="$(resolve_binary docker)"

"$SCRIPT_DIR/start_app.sh" -d

# Kill the container's process group if this script is interrupted. Without
# the trap, Ctrl-C detaches the terminal and leaves the spawned process
# running inside the container unsupervised, with nothing left watching it.
trap '"$DOCKER" compose kill web >/dev/null 2>&1 || true' INT TERM

# -T allocates no TTY, so the child cannot read from this terminal and is not
# holding it open; timeout bounds a run that would otherwise never end.
# `set -e` would abort before the status could be propagated, so the failure
# is captured rather than raised.
# The file inside the container is checked too. Without this, a missing or
# renamed game.py becomes a python3 error inside the container that reads as
# an application failure rather than as a deployment one.
if ! run_bounded 30 "$DOCKER" compose exec -T web test -f "$GAME"; then
    echo "start_game.sh: $GAME not found in the running image." >&2
    exit 1
fi

status=0
run_bounded 300 "$DOCKER" compose exec -T web python3 "$GAME" || status=$?

trap - INT TERM

# The caller, or CI, sees the child's outcome rather than this script's.
exit "$status"
