#!/usr/bin/env bash
set -euo pipefail
cd "/Users/isilveira/dvra-clean-for-testing"

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

if [[ "${#reasons[@]}" -gt 0 ]]; then
  echo "VERIFY FAIL: ${reasons[*]}"
  exit 1
fi

echo "VERIFY PASS"
