#!/bin/bash
# Fail on error, on an unset variable, and on any failure in a pipeline, so
# the guard below aborts the script rather than being logged and stepped over.
set -euo pipefail

# Word-splitting on newline and tab only. The default IFS includes the space,
# so an unquoted expansion of a path containing one silently becomes two
# arguments; and IFS is inherited, so the caller can otherwise choose how this
# script parses its own variables.
IFS=$'\n\t'

# An absolute, fixed PATH set before any external command runs. Inherited
# otherwise, which means a writable directory early in the caller's PATH
# decides which "docker" this privileged script executes.
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

require_operator "start_app.sh"

# Resolved once, by absolute path, under the fixed PATH above.
DOCKER="$(resolve_binary docker)"
ENV_BIN="$(resolve_binary env)"

# The database volume, at an absolute path resolved from this script's own
# directory rather than from wherever the caller was standing. 0700 rather
# than the default: the database files are readable only by the owner, not by
# the owner's group and not by every account on the host.
DATA_DIR="$(pwd -P)/postgres_data"
mkdir -m 0700 -p "$DATA_DIR"

# An existing directory keeps the mode and owner it already had, so creating
# it correctly says nothing about the one that is actually there. Someone
# else's postgres_data, or a symlink pointing at somewhere else, is refused
# rather than written into.
if [ -L "$DATA_DIR" ]; then
    echo "start_app.sh: postgres_data is a symlink; refusing to use it." >&2
    exit 1
fi

if [ "$(stat -f '%u' "$DATA_DIR" 2>/dev/null || stat -c '%u' "$DATA_DIR")" != "$(id -u)" ]; then
    echo "start_app.sh: postgres_data is not owned by the current user." >&2
    exit 1
fi

# env -i discards the caller's environment rather than handing it to the
# container runtime, which reads settings from variables the caller could
# otherwise set. Only what compose genuinely needs is passed back in: the
# secrets come from the env file the platform supplies at deploy time, not
# from the invoking shell, so nothing here needs to carry them.
#
# "$@" rather than $1, so arguments are passed through as given instead of
# being split on whitespace and glob-expanded.
exec "$ENV_BIN" -i \
    PATH="$PATH" \
    HOME="${HOME:-/tmp}" \
    DOCKER_HOST="${DOCKER_HOST:-}" \
    DOCKER_CONTEXT="${DOCKER_CONTEXT:-}" \
    "$DOCKER" compose up "$@"
