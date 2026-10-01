#!/usr/bin/env python3
"""Per-CM ledger write-through helper (mechanical IO only).

Usage: python3 .sde-security/apply/ledger.py <CM_ID> <Applied|Documented|Skipped>

Updates EXACTLY ONE AGENTS.md ledger row (the authoritative per-CM status) and,
when that CM's SKILL.md carries a `**Status:**` anchor (Format A/C only), the
in-file mirror. Then re-reads both from disk and prints the read-back so the
caller can verify the write landed. Never touches any other CM's row.
"""
import re
import sys

cm_id, new_status = sys.argv[1], sys.argv[2]
assert new_status in {"Applied", "Documented", "Skipped"}, new_status

ledger = open("AGENTS.md").read().splitlines(keepends=True)
row_idx = [
    i for i, l in enumerate(ledger) if re.match(r"^\|\s*%s\s*\|" % re.escape(cm_id), l)
]
assert len(row_idx) == 1, f"expected 1 ledger row for {cm_id}, found {len(row_idx)}"
i = row_idx[0]
cells = ledger[i].rstrip("\n").split("|")
# cells: ['', ' ID ', ' Title ', ' Skill File ', ' Priority ', ' Category ', ' Status ', ' Source ', '']
assert cells[6].strip() in {"Pending", "Applied", "Documented", "Skipped"}, cells[6]
cells[6] = f" {new_status} "
ledger[i] = "|".join(cells) + "\n"
open("AGENTS.md", "w").write("".join(ledger))

skill_path = re.search(r"\((skills/[^)]+SKILL\.md)\)", cells[3]).group(1)
body = open(skill_path).read()
has_anchor = "**Status:**" in body
if has_anchor:
    body = re.sub(
        r"\*\*Status:\*\* *(Pending|Applied|Documented|Skipped)",
        f"**Status:** {new_status}",
        body,
    )
    open(skill_path, "w").write(body)

# read-back from disk
reread = open("AGENTS.md").read().splitlines()
ledger_status = reread[i].split("|")[6].strip()
m = re.search(r"\*\*Status:\*\* *(\w+)", open(skill_path).read())
file_status = m.group(1) if m else "N/A (Format B, no anchor)"
print(f"{cm_id}\tledger={ledger_status}\tin_file={file_status}\tpath={skill_path}")
