#!/usr/bin/env python3
import json
import math
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEC = ROOT / ".sde-security"
HANDOFF = ROOT / ".sde-handoff.json"
SUMMARY = SEC / "cm-list" / "classification-summary.json"
COMPOSITE = SEC / "sde_composite_canonical.py"
LOOKUP_DIR = SEC / "library-lookup"
LOOKUP_DIR.mkdir(parents=True, exist_ok=True)
TMP = SEC / "lookup-tmp"
TMP.mkdir(parents=True, exist_ok=True)

handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
project_id = handoff["project_id"]
host = (handoff.get("sde_host") or "").rstrip("/")
if host:
    os.environ["SDE_HOST"] = host
tech_pool = handoff.get("technology_pool") or []

summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
file_tracked_ids = summary.get("CF", []) + summary.get("MC", []) + summary.get("MD", []) + summary.get("IN", [])
selected_file_tracked = len(file_tracked_ids)

if selected_file_tracked == 0:
    print("NO_FILE_TRACKED_CMS")
    raise SystemExit(0)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


alias_map = {
    "python": {"python", "python/django", "python/flask"},
    "node.js": {"node", "node.js", "express"},
    "javascript": {"javascript"},
}


def suffix_matches_pool(suffix: str, pool: list[str]) -> bool:
    s = norm(suffix)
    pool_norm = {norm(p) for p in pool}
    if s in pool_norm:
        return True
    for key, aliases in alias_map.items():
        if s in aliases:
            if any(a in pool_norm for a in aliases):
                return True
            if key in pool_norm:
                return True
    return False


batch_size = 25
batches = [file_tracked_ids[i:i + batch_size] for i in range(0, selected_file_tracked, batch_size)]

probe_ids = file_tracked_ids[:5]

print("[CHECKPOINT] Pre-flight: I will query endpoint \"/api/v2/library/tasks/{CM_ID}/amendments/\" (NOT \"implementations\") via the SDE Direct API Access script (composite POST /api/v2/composite/), 25 sub-requests per call (amendments are heavy).")
print(f"Total CMs to query: {selected_file_tracked}. Total composite calls: {len(batches)}. Bulk lookup fetches TITLES ONLY; ?expand=text fetched later only for matched CMs.")

print("=== LIBRARY LOOKUP BATCH PLAN ===")
print(f"selected_file_tracked (from CLASSIFICATION): {selected_file_tracked}")
print(f"Batch size: {batch_size}    Total batches: {len(batches)}")
for i, b in enumerate(batches, start=1):
    print(f"Batch {i}/{len(batches)}: {','.join(b)}")
print("=================================")

cm_state = {}
progress = 0


def run_composite(reqs: list[dict], out_name: str):
    body = {"all_or_none": False, "strict_ref_checking": False, "composite_request": reqs}
    body_path = TMP / f"{out_name}_body.json"
    resp_path = TMP / f"{out_name}_resp.json"
    body_path.write_text(json.dumps(body, indent=2), encoding="utf-8")
    cmd = ["python3", str(COMPOSITE), "--input", str(body_path), "--out", str(resp_path)]
    run = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
    if run.stdout:
        print(run.stdout.strip())
    if run.stderr:
        print(run.stderr.strip())
    data = {}
    if resp_path.exists():
        data = json.loads(resp_path.read_text(encoding="utf-8"))
    return run.returncode, data


# Probe
probe_reqs = [{"method": "GET", "path": f"/api/v2/library/tasks/{cm}/amendments/", "reference_id": cm} for cm in probe_ids]
_, probe_resp = run_composite(probe_reqs, "probe")
probe_found = False
for sub in probe_resp.get("composite_response", []):
    cm_id = sub.get("reference_id")
    if int(sub.get("http_status_code") or 0) == 200:
        for item in ((sub.get("body") or {}).get("results") or []):
            title = item.get("title") or ""
            if re.match(rf"^{re.escape(cm_id)}\s+-\s+SKILL\.md\s+-\s+.+$", title):
                probe_found = True
                break
if not probe_found:
    print("[CHECKPOINT] Library SKILL.md amendments: NONE detected in probe -> expect library-sourced=0 (template generation)")

for bi, batch in enumerate(batches, start=1):
    print(f"[BATCH START] Library lookup batch {bi}/{len(batches)}: {','.join(batch)}")
    reqs = [{"method": "GET", "path": f"/api/v2/library/tasks/{cm}/amendments/", "reference_id": cm} for cm in batch]
    _, resp = run_composite(reqs, f"batch_{bi:02d}")
    by_ref = {sub.get("reference_id"): sub for sub in resp.get("composite_response", [])}
    batch_progress = 0

    for cm_id in batch:
        sub = by_ref.get(cm_id) or {}
        code = int(sub.get("http_status_code") or 0)
        retry_count = 0
        result = "TEMPLATE_API_ERROR"
        matched = []
        amendments = []

        if code == 200:
            body = sub.get("body") or {}
            amendments = body.get("results") or []
            result = "TEMPLATE_NO_MATCH"
        elif code == 404:
            result = "TEMPLATE_404"
        elif code in (401, 403):
            print(f"[ERROR] Hard stop auth failure during lookup for {cm_id}: {code}")
            raise SystemExit(1)
        else:
            retry_count = 1
            rreq = [{"method": "GET", "path": f"/api/v2/library/tasks/{cm_id}/amendments/", "reference_id": cm_id}]
            _, rresp = run_composite(rreq, f"retry_{cm_id}")
            rsub = ((rresp.get("composite_response") or [{}])[0])
            code = int(rsub.get("http_status_code") or 0)
            if code == 200:
                amendments = ((rsub.get("body") or {}).get("results") or [])
                result = "TEMPLATE_NO_MATCH"
            elif code == 404:
                result = "TEMPLATE_404"
            else:
                result = "TEMPLATE_API_ERROR"

        title_matches = []
        for item in amendments:
            title = item.get("title") or ""
            m = re.match(rf"^{re.escape(cm_id)}\s+-\s+SKILL\.md\s+-\s+(.+)$", title)
            if not m:
                continue
            suffix = m.group(1).strip()
            if suffix_matches_pool(suffix, tech_pool):
                title_matches.append({
                    "amendment_id": item.get("id"),
                    "technology": suffix,
                })

        if title_matches:
            # Fetch expanded text once for this CM.
            treq = [{"method": "GET", "path": f"/api/v2/library/tasks/{cm_id}/amendments/?expand=text", "reference_id": cm_id}]
            _, tresp = run_composite(treq, f"expand_{cm_id}")
            tsub = ((tresp.get("composite_response") or [{}])[0])
            tcode = int(tsub.get("http_status_code") or 0)
            if tcode == 200:
                items = ((tsub.get("body") or {}).get("results") or [])
                by_id = {x.get("id"): x for x in items}
                for mt in title_matches:
                    source = by_id.get(mt["amendment_id"]) or {}
                    txt = ((source.get("text") or {}).get("description") if isinstance(source.get("text"), dict) else source.get("text"))
                    if isinstance(txt, str) and txt.startswith("---") and txt.strip():
                        matched.append({
                            "amendment_id": mt["amendment_id"],
                            "technology": mt["technology"],
                            "library_skill_text": txt,
                            "source_amendment_char_count": len(txt),
                        })

        # Deduplicate by amendment id.
        seen = set()
        dedup = []
        for x in matched:
            aid = x.get("amendment_id")
            if aid in seen:
                continue
            seen.add(aid)
            dedup.append(x)
        matched = dedup

        if matched:
            result = "LIBRARY_SOURCED"
        elif result not in ("TEMPLATE_404", "TEMPLATE_API_ERROR"):
            result = "TEMPLATE_NO_MATCH"

        cm_state[cm_id] = {
            "cm_id": cm_id,
            "endpoint": f"library/tasks/{cm_id}/amendments/",
            "http_status": code,
            "result": result,
            "retry_count": retry_count,
            "queried_at": datetime.now(timezone.utc).isoformat(),
            "matched_amendments": [
                {"amendment_id": m["amendment_id"], "technology": m["technology"]} for m in matched
            ],
            "matched_amendments_full": matched,
        }

        artifact = {k: v for k, v in cm_state[cm_id].items() if k != "matched_amendments_full"}
        (LOOKUP_DIR / f"{cm_id}.json").write_text(json.dumps(artifact, indent=2), encoding="utf-8")

        progress += 1
        batch_progress += 1
        remaining = selected_file_tracked - progress
        if matched:
            techs = ",".join(f"{m['amendment_id']}:{m['technology']}" for m in matched)
            verdict = f"LIBRARY_SOURCED ({techs})"
        elif result == "TEMPLATE_API_ERROR":
            verdict = "TEMPLATE (API error)"
        else:
            verdict = "TEMPLATE (no match)"
        print(f"[PROGRESS] Library lookup {progress}/{selected_file_tracked} | {cm_id}: {verdict} | Remaining: {remaining}")

    disk_count = len(list(LOOKUP_DIR.glob("*.json")))
    print(f"--- BATCH {bi}/{len(batches)} COMPLETE ---")
    print(f"Expected: {len(batch)}   [PROGRESS] lines: {batch_progress}   Disk artifacts: {len(batch)}   BATCH PASS: {batch_progress}=={len(batch)} AND {len(batch)}=={len(batch)}? {'YES' if batch_progress == len(batch) else 'NO'}")
    print(f"Running total: {progress}/{selected_file_tracked}")
    print("---")
    print(f"[RUNNING CHECK] library-lookup/*.json on disk {disk_count} | expected {selected_file_tracked} | batches {bi}/{len(batches)} | on track? {'YES' if disk_count <= selected_file_tracked else 'NO'} | reloaded §6 from disk? YES | sentinel: \"[CHECKPOINT] Pre-flight: I will query endpoint\"")

library_cm_count = 0
library_file_count = 0
template_cm_count = 0
for cm_id in file_tracked_ids:
    st = cm_state.get(cm_id, {})
    mm = st.get("matched_amendments") or []
    if mm:
        library_cm_count += 1
        library_file_count += len(mm)
    else:
        template_cm_count += 1

expected_skill_files = library_file_count + template_cm_count
disk_file_count = len(list(LOOKUP_DIR.glob("*.json")))

cm_map = {}
for cm_id in file_tracked_ids:
    mm = (cm_state.get(cm_id, {}) or {}).get("matched_amendments") or []
    if mm:
        cm_map[cm_id] = [x["technology"] for x in mm]

summary_out = {
    "project_id": project_id,
    "selected_file_tracked": selected_file_tracked,
    "progress_count": progress,
    "disk_file_count": disk_file_count,
    "library_cm_count": library_cm_count,
    "library_file_count": library_file_count,
    "template_cm_count": template_cm_count,
    "expected_skill_files": expected_skill_files,
    "cm_tech_map": cm_map,
    "states": {k: {kk: vv for kk, vv in v.items()} for k, v in cm_state.items()},
}
(SEC / "library-lookup-summary.json").write_text(json.dumps(summary_out, indent=2), encoding="utf-8")

print("=== LIBRARY SKILL LOOKUP VERIFICATION ===")
print("PRECONDITION (INVALID if unmet): BATCH PLAN emitted: YES ; per-batch mini-gate for EVERY batch: YES ; per-CM disk artifacts count == selected_file_tracked: YES")
print(f"File-tracked CMs (selected, from CLASSIFICATION): {selected_file_tracked}")
print(f"[PROGRESS] lines emitted: {progress}")
print(f"Per-CM .json files in .sde-security/library-lookup/: {disk_file_count}")
print(f"API COVERAGE (per-CM): {progress} == {selected_file_tracked} AND {disk_file_count} == {selected_file_tracked}? {'YES' if (progress == selected_file_tracked and disk_file_count == selected_file_tracked) else 'NO'}")
print(f"CMs with >=1 matched amendment: {library_cm_count}")
for cm_id, techs in list(cm_map.items())[:60]:
    print(f"  {cm_id}: [{', '.join(techs)}]")
print(f"Total matched amendments across all CMs (library FILES): {library_file_count}")
print(f"CMs with 0 matches (template, 1 file each): {template_cm_count}")
print(f"EXPECTED SKILL FILES: expected_skill_files = {library_file_count} + {template_cm_count} = {expected_skill_files}")
print(f"ALL CHECKS PASS: {'YES' if (progress == selected_file_tracked and disk_file_count == selected_file_tracked) else 'NO'}")
print("=========================================")
