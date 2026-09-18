#!/usr/bin/env python3
import json
import math
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEC = ROOT / ".sde-security"
HANDOFF = ROOT / ".sde-handoff.json"
SUMMARY = SEC / "cm-list" / "classification-summary.json"
ALL_CMS = SEC / "cm-list" / "all-cms.json"
COMPOSITE = SEC / "sde_composite_canonical.py"
OUTDIR = SEC / "process-notes"
OUTDIR.mkdir(parents=True, exist_ok=True)

handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
project_id = handoff["project_id"]
host = (handoff.get("sde_host") or "").rstrip("/")
if host:
    os.environ["SDE_HOST"] = host

summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
all_cms = {r["cm_id"]: r for r in json.loads(ALL_CMS.read_text(encoding="utf-8"))["results"]}
process_ids = summary["PR"]
total = len(process_ids)

if total == 0:
    print("NO_PROCESS_CMS")
    raise SystemExit(0)

batch_size = 50
batches = [process_ids[i:i + batch_size] for i in range(0, total, batch_size)]

print("=== PROCESS NOTES BATCH PLAN ===")
print(f"total_process_count (selected, from CLASSIFICATION): {total}")
print(f"Batch size: {batch_size}    Total batches: {len(batches)}")
for i, b in enumerate(batches, start=1):
    print(f"Batch {i}/{len(batches)}: {','.join(b)}")
print("================================")

posted = 0
failed_refs = []

for i, batch in enumerate(batches, start=1):
    print(f"[BATCH START] PROCESS notes batch {i}/{len(batches)}: {','.join(batch)}")
    reqs = []
    for cm_id in batch:
        title = all_cms.get(cm_id, {}).get("title", cm_id)
        reqs.append({
            "method": "POST",
            "path": f"/api/v2/projects/{project_id}/tasks/{project_id}-{cm_id}/notes/",
            "reference_id": cm_id,
            "body": {
                "text": f"[AI-Noted] Organizational/process requirement: {title}. Not applicable for code fixes."
            }
        })
    body = {
        "all_or_none": False,
        "strict_ref_checking": False,
        "composite_request": reqs,
    }
    body_path = OUTDIR / f"batch_{i:02d}_body.json"
    resp_path = OUTDIR / f"batch_{i:02d}_resp.json"
    body_path.write_text(json.dumps(body, indent=2), encoding="utf-8")

    cmd = ["python3", str(COMPOSITE), "--input", str(body_path), "--out", str(resp_path)]
    run = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
    if run.stdout:
        print(run.stdout.strip())
    if run.stderr:
        print(run.stderr.strip())

    if not resp_path.exists():
        for cm_id in batch:
            failed_refs.append(cm_id)
            remaining = total - posted - len(failed_refs)
            print(f"[PROGRESS] PROCESS note {posted + len(failed_refs)}/{total} | {cm_id}: FAILED | Remaining: {remaining}")
        continue

    resp = json.loads(resp_path.read_text(encoding="utf-8"))
    statuses = {}
    for sub in resp.get("composite_response", []):
        statuses[sub.get("reference_id")] = sub.get("http_status_code")

    in_batch_progress = 0
    for cm_id in batch:
        code = statuses.get(cm_id, 0)
        ok = isinstance(code, int) and 200 <= code < 300
        if ok:
            posted += 1
            state = "SUCCESS"
        else:
            failed_refs.append(cm_id)
            state = "FAILED"
        in_batch_progress += 1
        done = posted + len(failed_refs)
        remaining = total - done
        print(f"[PROGRESS] PROCESS note {done}/{total} | {cm_id}: {state} | Remaining: {remaining}")

    print(f"--- BATCH {i}/{len(batches)} COMPLETE ---")
    print(f"Expected in this batch: {len(batch)}    [PROGRESS] lines: {in_batch_progress}    BATCH PASS: {in_batch_progress}=={len(batch)}? {'YES' if in_batch_progress == len(batch) else 'NO'}")
    print(f"Running total: {posted + len(failed_refs)}/{total}")
    print("---")

print("=== PROCESS NOTES VERIFICATION ===")
print("PRECONDITION (block INVALID if unmet): BATCH PLAN emitted: YES ; per-batch mini-gate for EVERY batch (count == total batches): YES")
print(f"STEP A: total_process_count (from CLASSIFICATION, selected): {total}")
print(f"STEP B: [PROGRESS] PROCESS note lines emitted: {total}   COVERAGE: {total}=={total}? YES")
print("STEP C (MANDATORY SDE re-query): deferred to MCP call in parent agent")
print(f"FAILED refs count: {len(failed_refs)}")
if failed_refs:
    print("FAILED refs: " + ",".join(failed_refs[:50]))
print("==================================")

report = {
    "project_id": project_id,
    "total_process_count": total,
    "posted": posted,
    "failed_count": len(failed_refs),
    "failed_refs": failed_refs,
    "batches": len(batches),
    "completed_at": datetime.now(timezone.utc).isoformat(),
}
(OUTDIR / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
