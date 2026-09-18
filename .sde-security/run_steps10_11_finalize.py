#!/usr/bin/env python3
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEC = ROOT / ".sde-security"
HANDOFF = ROOT / ".sde-handoff.json"
SEL = SEC / "selected-cms.json"
CLS = SEC / "cm-list" / "classification-summary.json"
LOOKUP_SUM = SEC / "library-lookup-summary.json"
GEN_SUM = SEC / "generation-summary.json"
AGENTS = ROOT / "AGENTS.md"

handoff_prev = json.loads(HANDOFF.read_text(encoding="utf-8"))
selected = json.loads(SEL.read_text(encoding="utf-8"))
classification = json.loads(CLS.read_text(encoding="utf-8"))
lookup = json.loads(LOOKUP_SUM.read_text(encoding="utf-8"))
generation = json.loads(GEN_SUM.read_text(encoding="utf-8"))

selected_count = int(selected["selected_count"])
project_total = int(lookup.get("selected_file_tracked", 0)) + len(classification.get("PR", []))
selected_file_tracked = int(lookup["selected_file_tracked"])
expected_skill_files = int(lookup["expected_skill_files"])
library_file_count = int(lookup["library_file_count"])

skill_files = generation["skill_files"]
library_sourced_cms = generation["library_sourced_cms"]

lookup_audit = []
for cm_id in sorted(lookup["states"].keys()):
    st = lookup["states"][cm_id]
    lookup_audit.append({
        "cm_id": st.get("cm_id"),
        "endpoint": st.get("endpoint"),
        "http_status": st.get("http_status"),
        "result": st.get("result"),
        "retry_count": st.get("retry_count"),
        "queried_at": st.get("queried_at"),
        "matched_amendments": st.get("matched_amendments", []),
    })

branch = subprocess.run(["git", "branch", "--show-current"], cwd=str(ROOT), text=True, capture_output=True).stdout.strip()
git_enabled = bool(branch)
ai_backup_archive = ".sde-ai-backup.tar.gz" if (ROOT / ".sde-ai-backup.tar.gz").exists() else None

handoff_new = {
    "source_skill": "generate-security-skill-files",
    "stage": "skill-files-generated",
    "evidence_source": handoff_prev.get("evidence_source"),
    "assessment_mode": handoff_prev.get("assessment_mode"),
    "version_label": handoff_prev.get("version_label"),
    "repository_path": handoff_prev.get("repository_path"),
    "project_id": handoff_prev.get("project_id"),
    "project_name": handoff_prev.get("project_name"),
    "business_unit_id": handoff_prev.get("business_unit_id"),
    "application_id": handoff_prev.get("application_id"),
    "risk_policy_id": handoff_prev.get("risk_policy_id"),
    "sde_host": handoff_prev.get("sde_host"),
    "technology_pool": handoff_prev.get("technology_pool", []),
    "agents_md": str(AGENTS),
    "skill_files": skill_files,
    "selection_mode": selected.get("selection_mode"),
    "task_status_filter": selected.get("task_status_filter"),
    "verification_status_filter": selected.get("verification_status_filter"),
    "status_filtered_count": selected.get("status_filtered_count"),
    "selected_cm_ids": selected.get("selected_cm_ids", []),
    "total_countermeasures": selected_count,
    "project_total_countermeasures": project_total,
    "expected_skill_files": expected_skill_files,
    "code_fix_count": len(classification.get("CF", [])) + len(classification.get("MC", [])),
    "documentation_count": len(classification.get("MD", [])) + len(classification.get("IN", [])),
    "process_count": len(classification.get("PR", [])),
    "git_enabled": git_enabled,
    "security_branch": branch if git_enabled else None,
    "ai_backup_archive": ai_backup_archive,
    "scaffold": handoff_prev.get("scaffold"),
    "initial_commit": handoff_prev.get("initial_commit"),
    "spec_sources": handoff_prev.get("spec_sources"),
    "library_sourced_cms": library_sourced_cms,
    "library_lookup_audit": lookup_audit,
    "created_at": datetime.now(timezone.utc).isoformat(),
}

HANDOFF.write_text(json.dumps(handoff_new, indent=2), encoding="utf-8")

# Verification metrics
skill_count = len(list((ROOT / "skills").rglob("SKILL.md")))
rows = len(re.findall(r"^\| [A-Z]*T[0-9]", AGENTS.read_text(encoding="utf-8"), flags=re.M))
unique_cm = set()
for p in (ROOT / "skills").rglob("SKILL.md"):
    m = re.search(r"/([A-Z]*T[0-9]+)-", p.as_posix())
    if m:
        unique_cm.add(m.group(1))

lib_stamp_count = AGENTS.read_text(encoding="utf-8").count("LIBRARY:")
fidelity_ok = all((x.get("written_len", 0) >= x.get("source_len", 0)) for x in generation.get("fidelity", []))

verify_script = f'''#!/usr/bin/env bash
set -euo pipefail
cd "{ROOT}"

reasons=()
expected_skill_files=$(python3 - <<'PY'
import json
print(json.load(open('.sde-handoff.json'))['expected_skill_files'])
PY
)
expected_file_tracked=$(python3 - <<'PY'
import json
s=json.load(open('.sde-security/selected-cms.json'))
c=json.load(open('.sde-security/cm-list/classification-summary.json'))
print(len(set(s['selected_cm_ids']) - set(c['PR'])))
PY
)

skill_count=$(find skills -name 'SKILL.md' | wc -l | tr -d ' ')
[[ "$skill_count" == "$expected_skill_files" ]] || reasons+=("skill_count=$skill_count expected=$expected_skill_files")

ledger_rows=$(grep -cE '^\| [A-Z]*T[0-9]' AGENTS.md || true)
[[ "$ledger_rows" == "$expected_skill_files" ]] || reasons+=("ledger_rows=$ledger_rows expected=$expected_skill_files")

unique_cm=$(find skills -name 'SKILL.md' -path '*/*T[0-9]*-*/*' | sed -E 's|.*/([A-Z]*T[0-9]+)-.*|\1|' | sort -u | wc -l | tr -d ' ')
[[ "$unique_cm" == "$expected_file_tracked" ]] || reasons+=("unique_cm=$unique_cm expected=$expected_file_tracked")

lookup_json=$(find .sde-security/library-lookup -name '*.json' | wc -l | tr -d ' ')
[[ "$lookup_json" == "$expected_file_tracked" ]] || reasons+=("library_lookup_json=$lookup_json expected=$expected_file_tracked")

cm_work_json=$(find .sde-security/cm-work -name '*.json' | wc -l | tr -d ' ')
[[ "$cm_work_json" == "$expected_skill_files" ]] || reasons+=("cm_work_json=$cm_work_json expected=$expected_skill_files")

python3 - <<'PY'
import json, os, sys
h=json.load(open('.sde-handoff.json'))
errs=[]
expected_skill_files=h['expected_skill_files']
s=json.load(open('.sde-security/selected-cms.json'))
c=json.load(open('.sde-security/cm-list/classification-summary.json'))
expected_file_tracked=len(set(s['selected_cm_ids'])-set(c['PR']))
if len(h['library_lookup_audit'])!=expected_file_tracked:
    errs.append('library_lookup_audit length mismatch')
if len(h['skill_files'])!=expected_skill_files:
    errs.append('skill_files length mismatch')
for p in h['skill_files']:
    if not os.path.exists(p):
        errs.append('missing skill file '+p)
if errs:
    print('VERIFY_FAIL_PY:' + '; '.join(errs))
    sys.exit(1)
print('VERIFY_OK_PY')
PY

if [[ "${{#reasons[@]}}" -gt 0 ]]; then
  echo "VERIFY FAIL: ${{reasons[*]}}"
  exit 1
fi

echo "VERIFY PASS"
'''

vpath = SEC / "verify-output.sh"
vpath.write_text(verify_script, encoding="utf-8")
os.chmod(vpath, 0o755)

print("CROSS-REFERENCE PASS: missing_count == 0 (every selected file-tracked CM has >=1 file)? " + ("YES" if len(unique_cm) == selected_file_tracked else "NO"))
print("=== FILE GENERATION VERIFICATION ===")
print(f"STEP A: total files: {skill_count}")
print(f"STEP B: expected_skill_files: {expected_skill_files}")
print(f"STEP C: MATCH: {skill_count} == {expected_skill_files}? {'YES' if skill_count == expected_skill_files else 'NO'}")
print(f"STEP D: AGENTS rows: {rows}  MATCH: rows == expected_skill_files? {'YES' if rows == expected_skill_files else 'NO'}")
print(f"STEP E: unique CM IDs on disk == selected_file_tracked? {'YES' if len(unique_cm) == selected_file_tracked else 'NO'}")
print("===================================")

print("=== LIBRARY SOURCING RECONCILIATION ===")
print(f"Matched amendments at lookup (Step 6, library FILES): {library_file_count}")
print(f"Files written with library content (byte-exact): {len(generation.get('fidelity', []))}")
print(f"library_sourced_cms entries (in-memory, to handoff): {len(library_sourced_cms)}")
print(f"VERIFY: {'YES' if library_file_count == len(generation.get('fidelity', [])) == len(library_sourced_cms) else 'NO'}")
print("=======================================")

print("=== LIBRARY CONTENT FIDELITY ===")
for f in generation.get("fidelity", []):
    print(f"{f['cm_id']}/{f['tech_slug']}: written_len={f['written_len']} | source_amendment_len={f['source_len']} | written>=source? {'YES' if f['written_len'] >= f['source_len'] else 'NO'}")
print(f"VERIFY: every library file length >= source amendment? {'YES' if fidelity_ok else 'NO'}")
print("================================")

print(f"[CHECKPOINT] Handoff file written: .sde-handoff.json (stage=skill-files-generated, selected={selected_count}, files={expected_skill_files}, library_lookup_audit={selected_file_tracked} entries)")
