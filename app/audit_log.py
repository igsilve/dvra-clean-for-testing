"""Structured audit logging.

Two problems are solved together here, because solving either one alone
produces something worse than nothing.

The first is that the application configured no logging at all, so an
authentication failure, a privilege change or an administrative action left
no record anywhere. There was nothing to consult after an incident.

The second is that the obvious fix -- log the request -- is how credentials
end up in a log aggregator that is backed up, replicated and readable by
more people than the database is. So the record is built from an explicit
list of fields rather than from whatever the caller happens to pass, and a
field carrying a name that looks like a secret is dropped rather than
truncated or masked: a masked value still tells a reader the length, and a
truncated one is often still enough to use.
"""

import json
import logging
import sys
from typing import Any, Mapping

AUDIT_LOGGER_NAME = "audit"

# Names whose values never reach the log, matched as substrings so
# `new_password`, `password_confirm` and `POSTGRES_PASSWORD` are all covered
# without anyone having to list them.
SENSITIVE_FIELD_MARKERS = (
    "password",
    "secret",
    "token",
    "authorization",
    "credential",
    "cookie",
    "api_key",
    "apikey",
    "private",
    "hmac",
    "otp",
    # The specific code-bearing names rather than a bare "code": that
    # matched `status_code` as a substring and silently withheld the status
    # from every access record -- a redaction control quietly eating the
    # data it exists to keep.
    "reset_code",
    "auth_code",
    "verification_code",
)

# The fields an audit record may carry. An allow-list rather than a
# deny-list: a new caller passing something sensitive under an unfamiliar
# name is dropped by default, which is the direction the mistake should go.
ALLOWED_FIELDS = frozenset(
    {
        "event",
        "outcome",
        "actor",
        "actor_role",
        "subject",
        "subject_role",
        "resource",
        "resource_id",
        "action",
        "reason",
        "client_ip",
        "method",
        "path",
        "status_code",
    }
)


def _is_sensitive(name: str) -> bool:
    lowered = name.lower()
    return any(marker in lowered for marker in SENSITIVE_FIELD_MARKERS)


def redact(fields: Mapping[str, Any]) -> dict:
    """Reduce caller-supplied fields to the ones an audit record may carry.

    Anything not on the allow-list is dropped, and a name that looks like a
    secret is reported as having been dropped rather than being silently
    absent -- a reader needs to be able to tell "nothing was sent" from
    "something was sent and withheld".
    """
    record = {}
    withheld = []

    for name, value in fields.items():
        if _is_sensitive(name):
            withheld.append(name)
            continue
        if name not in ALLOWED_FIELDS:
            continue
        record[name] = value

    if withheld:
        record["withheld_fields"] = sorted(withheld)

    return record


class JsonFormatter(logging.Formatter):
    """One JSON object per line.

    Plain text makes an audit trail expensive to query and easy to forge by
    writing a newline into a field; json.dumps escapes the newline, so a
    value cannot fabricate a second record.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extra = getattr(record, "audit", None)
        if isinstance(extra, Mapping):
            payload.update(redact(extra))

        if record.exc_info:
            # The type and message, not the traceback: file paths and local
            # variables in a shared log store are their own disclosure.
            exc_type, exc_value, _ = record.exc_info
            payload["error"] = getattr(exc_type, "__name__", str(exc_type))
            payload["error_detail"] = str(exc_value)

        return json.dumps(payload, default=str, sort_keys=True)


def configure_logging(level: int = logging.INFO) -> None:
    """Install the JSON formatter on the root handler.

    Called from the application factory so that every logger in the process
    -- including the ones the earlier countermeasures added in
    apis/menu/utils.py and apis/admin/utils.py -- is structured and
    redacted, rather than only the records written through audit().

    Idempotent: repeated calls replace the handler instead of stacking a
    second one, which would otherwise duplicate every line under a test
    runner that builds the app more than once.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)

    # uvicorn's access log repeats the query string, which is where a reset
    # code or a token lands when a client puts one there. The application's
    # own records carry the path without it.
    logging.getLogger("uvicorn.access").disabled = True


def audit(event: str, outcome: str = "success", **fields: Any) -> None:
    """Emit one audit record.

    `event` and `outcome` are positional-ish rather than free-form fields so
    that every record has both: a trail of events with no outcome cannot
    answer the only question anyone asks of it.
    """
    logging.getLogger(AUDIT_LOGGER_NAME).info(
        event,
        extra={"audit": {"event": event, "outcome": outcome, **fields}},
    )
