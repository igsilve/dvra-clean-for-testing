#!/usr/bin/env bash
# Disk-only verification for the apply-security-fixes run.
# Never makes an HTTP call and never reads file bodies into agent context.
set -uo pipefail

LEDGER="AGENTS.md"
APPLY=".sde-security/apply"
# The scoped set for this run is the CMs that were Pending when it started
# (column 2 of the batch plan). T7357 was already Applied upstream, so it is
# deliberately outside scope and exempt from the note-coverage assertion.
SCOPE_SRC="$APPLY/pending_batches.tsv"
POSTED="$APPLY/note_posted.tsv"
COUNTS="$APPLY/note_counts.tsv"

EXPECTED_TOTAL=276
SCOPED_TOTAL=275

cut -f2 "$SCOPE_SRC" | sort -u > /tmp/sde_scoped_ids.txt

fail=0
reasons=""

note_fail() {
  fail=1
  reasons="${reasons}
  - $1"
}

# --- structural invariant: expected_total == ledger rows == SKILL.md files ---
ledger_rows=$(grep -cE '^\| [A-Z]*T[0-9]' "$LEDGER")
skill_files=$(find skills -name SKILL.md -type f | wc -l | tr -d ' ')

echo "ledger rows            : $ledger_rows"
echo "SKILL.md files on disk : $skill_files"
echo "expected_total         : $EXPECTED_TOTAL"

[ "$ledger_rows" -eq "$EXPECTED_TOTAL" ] || note_fail "ledger rows ($ledger_rows) != expected_total ($EXPECTED_TOTAL)"
[ "$skill_files" -eq "$EXPECTED_TOTAL" ] || note_fail "SKILL.md files ($skill_files) != expected_total ($EXPECTED_TOTAL)"

# --- terminal-status ledger rows (status is the 4th cell of a path row) ---
grep -oE 'SKILL\.md\) \| [0-9]+ \| [A-Z_]+ \| (Applied|Documented|Skipped)' "$LEDGER" \
  > /tmp/sde_terminal_rows.txt
terminal_rows=$(wc -l < /tmp/sde_terminal_rows.txt | tr -d ' ')

# Unique CM IDs carrying a terminal status.
awk -F'|' '/^\| [A-Z]*T[0-9]/ {
    id = $2; st = $7
    gsub(/^[ \t]+|[ \t]+$/, "", id)
    gsub(/^[ \t]+|[ \t]+$/, "", st)
    if (st == "Applied" || st == "Documented" || st == "Skipped") print id
  }' "$LEDGER" | sort -u > /tmp/sde_terminal_ids_all.txt

# Restrict the terminal set to the scoped CMs.
comm -12 /tmp/sde_terminal_ids_all.txt /tmp/sde_scoped_ids.txt > /tmp/sde_terminal_ids.txt
terminal_ids=$(wc -l < /tmp/sde_terminal_ids.txt | tr -d ' ')

echo "terminal ledger rows   : $terminal_rows"
echo "unique terminal CM IDs : $(wc -l < /tmp/sde_terminal_ids_all.txt | tr -d ' ') (scoped: $terminal_ids)"
echo "scoped_total           : $SCOPED_TOTAL"

# --- pending set: which scoped CMs still lack a terminal status ---
awk -F'|' '/^\| [A-Z]*T[0-9]/ {
    id = $2; st = $7
    gsub(/^[ \t]+|[ \t]+$/, "", id)
    gsub(/^[ \t]+|[ \t]+$/, "", st)
    if (st == "Pending") print id
  }' "$LEDGER" | sort -u > /tmp/sde_pending_ids_all.txt
comm -12 /tmp/sde_pending_ids_all.txt /tmp/sde_scoped_ids.txt > /tmp/sde_pending_ids.txt
pending_ids=$(wc -l < /tmp/sde_pending_ids.txt | tr -d ' ')
echo "unique pending CM IDs  : $pending_ids"

# --- SDE note coverage: every terminal CM needs a THIS-RUN ADDED row ---
# A missing note_posted.tsv means zero notes were posted; treat it as zero rows.
if [ -f "$POSTED" ]; then
  posted_rows=$(wc -l < "$POSTED" | tr -d ' ')
else
  posted_rows=0
fi
echo "note_posted.tsv rows   : $posted_rows"

missing_notes=""
while read -r id; do
  [ -n "$id" ] || continue
  status=$(awk -F'|' -v want="$id" '/^\| [A-Z]*T[0-9]/ {
      i = $2; s = $7
      gsub(/^[ \t]+|[ \t]+$/, "", i)
      gsub(/^[ \t]+|[ \t]+$/, "", s)
      if (i == want && (s == "Applied" || s == "Documented" || s == "Skipped")) { print s; exit }
    }' "$LEDGER")
  [ "$status" = "Skipped" ] && continue
  marker="[AI-Applied]"
  [ "$status" = "Documented" ] && marker="[AI-Documented]"
  # An ADDED row must carry the marker matching the ledger status; a FAILED
  # row is an accepted (recorded) outcome.
  if ! grep -qF "4560-${id}	ADDED	${marker}	" "$POSTED" 2>/dev/null \
     && ! grep -qE "^4560-${id}	FAILED	" "$POSTED" 2>/dev/null; then
    missing_notes="${missing_notes} ${id}"
  fi
done < /tmp/sde_terminal_ids.txt

if [ -n "$missing_notes" ]; then
  note_fail "terminal CMs with no note_posted.tsv row:${missing_notes}"
fi

# note_counts.tsv is written by the Step 5 SDE re-query; absent mid-run.
if [ -f "$COUNTS" ]; then
  echo "note_counts.tsv rows   : $(wc -l < "$COUNTS" | tr -d ' ')"
else
  echo "note_counts.tsv        : absent (Step 5 SDE re-query not yet run)"
fi

# --- surviving-source check for Applied CMs ---
if [ -f ".sde-apply-handoff.json" ]; then
  bad=$(python3 - <<'PY'
import json, os
h = json.load(open(".sde-apply-handoff.json"))
bad = []
for rec in h.get("audit_records", []):
    if rec.get("status") != "Applied":
        continue
    files = rec.get("files_modified") or []
    surviving = [
        f for f in files
        if os.path.exists(f)
        and not f.startswith(("security/", ".sde-security/"))
        and not any(t in os.path.basename(f) for t in ("_secure.", "_fixed.", "_safe.", "batch_"))
    ]
    if not surviving:
        bad.append(rec.get("id"))
print(" ".join(str(b) for b in bad))
PY
)
  if [ -n "$bad" ]; then
    note_fail "applied CM with no surviving source file:$bad"
  fi
  echo "surviving-source check : ran against .sde-apply-handoff.json"
else
  echo "surviving-source check : handoff absent (Step 6.5 not yet run)"
fi

# --- terminal-status shortfall gate ---
if [ "$terminal_ids" -lt "$SCOPED_TOTAL" ]; then
  short=$((SCOPED_TOTAL - terminal_ids))
  note_fail "terminal-status shortfall: $short scoped CM(s) still Pending"
  echo ""
  echo "First 20 CMs still lacking a terminal status:"
  head -20 /tmp/sde_pending_ids.txt
fi

echo ""
if [ "$fail" -eq 0 ]; then
  echo "VERIFY PASS"
  exit 0
fi
echo "VERIFY FAIL:${reasons}"
exit 1
