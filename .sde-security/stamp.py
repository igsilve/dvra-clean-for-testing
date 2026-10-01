#!/usr/bin/env python3
"""Stamp library-lookup artifacts for CMs whose amendments response carried NO
matching SKILL.md amendment (so there is no library text to persist).

Usage: stamp.py RESULT CM_ID[:STATUS] ...
  e.g. stamp.py TEMPLATE_NO_MATCH T228 T2666 T3930 T7358
       stamp.py TEMPLATE_404 T999:404
Mechanical IO only -- writes no content and makes no decisions.
"""
import json, os, sys, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC = os.path.join(REPO, ".sde-security")
LL = os.path.join(SEC, "library-lookup")
os.makedirs(LL, exist_ok=True)


def req_count(cm):
    p = os.path.join(SEC, "project-requirements", f"{cm}.json")
    return json.load(open(p, encoding="utf-8")).get("count", 0) if os.path.exists(p) else 0


result = sys.argv[1]
for tok in sys.argv[2:]:
    cm, _, st = tok.partition(":")
    status = int(st) if st else 200
    art = {
        "cm_id": cm,
        "endpoint": f"library/tasks/{cm}/amendments/",
        "http_status": status,
        "result": result,
        "retry_count": 0,
        "queried_at": datetime.datetime.now(datetime.timezone.utc)
                         .isoformat().replace("+00:00", "Z"),
        "matched_amendments": [],
        "additional_requirements_count": req_count(cm),
    }
    json.dump(art, open(os.path.join(LL, f"{cm}.json"), "w", encoding="utf-8"), indent=2)
    print(f"[PROGRESS] {cm}: {result}")
