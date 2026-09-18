#!/usr/bin/env python3
"""
SD Elements Composite/Batch helper -- CANONICAL REFERENCE (Python 3, stdlib only).
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _load_from_mcp_json():
    candidates = [
        os.path.join(os.getcwd(), ".cursor", "mcp.json"),
        os.path.expanduser(os.path.join("~", ".cursor", "mcp.json")),
    ]
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
        except (OSError, ValueError):
            continue
        env = (
            cfg.get("mcpServers", {})
            .get("sdelements", {})
            .get("env", {})
        )
        host = env.get("SDE_HOST")
        key = env.get("SDE_API_KEY")
        if host and key:
            return host, key
    return None, None


def load_auth():
    host = os.environ.get("SDE_HOST")
    key = os.environ.get("SDE_API_KEY")
    if not (host and key):
        m_host, m_key = _load_from_mcp_json()
        host = host or m_host
        key = key or m_key
    if not (host and key):
        sys.stderr.write(
            "[sde_composite] ERROR: SDE_HOST/SDE_API_KEY not found in env or "
            ".cursor/mcp.json (mcpServers.sdelements.env)\n"
        )
        sys.exit(2)
    return host.rstrip("/"), key


def post_composite(host, key, body):
    url = host + "/api/v2/composite/"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", "Token " + key)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def reconcile(response):
    out = {}
    for sub in response.get("composite_response", []):
        out[sub.get("reference_id")] = sub.get("http_status_code")
    return out


def main():
    ap = argparse.ArgumentParser(description="SDE composite batch helper")
    ap.add_argument("--input", required=True, help="path to composite body JSON")
    ap.add_argument("--out", required=True, help="path to write the full response JSON")
    args = ap.parse_args()

    host, key = load_auth()

    with open(args.input, "r", encoding="utf-8") as fh:
        body = json.load(fh)

    subs_by_ref = {s.get("reference_id"): s for s in body.get("composite_request", [])}
    total = len(subs_by_ref)

    try:
        response = post_composite(host, key, body)
    except urllib.error.HTTPError as exc:
        sys.stderr.write("[sde_composite] outer HTTP %s\n" % exc.code)
        sys.exit(1)
    except urllib.error.URLError as exc:
        sys.stderr.write("[sde_composite] transport error: %s\n" % exc.reason)
        sys.exit(1)

    statuses = reconcile(response)
    failed = [ref for ref, code in statuses.items() if not (code and 200 <= code < 300)]

    if failed:
        retry_body = {
            "all_or_none": False,
            "strict_ref_checking": False,
            "composite_request": [subs_by_ref[ref] for ref in failed if ref in subs_by_ref],
        }
        try:
            retry_resp = post_composite(host, key, retry_body)
            merged = {s.get("reference_id"): s for s in response.get("composite_response", [])}
            for s in retry_resp.get("composite_response", []):
                merged[s.get("reference_id")] = s
            response["composite_response"] = list(merged.values())
            statuses = reconcile(response)
            failed = [ref for ref, code in statuses.items() if not (code and 200 <= code < 300)]
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            sys.stderr.write("[sde_composite] retry call failed: %s\n" % exc)

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(response, fh, indent=2)

    posted = total - len(failed)
    print("[sde_composite] posted=%d failed=%d total=%d" % (posted, len(failed), total))
    if failed:
        print("[sde_composite] failed_reference_ids=%s" % ",".join(str(f) for f in failed))
        print("[sde_composite] full response written to %s" % args.out)
        sys.exit(1)
    print("[sde_composite] full response written to %s" % args.out)
    sys.exit(0)


if __name__ == "__main__":
    main()
