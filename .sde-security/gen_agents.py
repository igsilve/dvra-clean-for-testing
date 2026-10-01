#!/usr/bin/env python3
"""Assemble the AGENTS.md security block from on-disk artifacts.

Mechanical only: every value comes from classification.json, cm-list/index.json,
library-lookup/*.json and code-map.json. This script authors no guidance text
beyond the fixed section headings the contract prescribes.
"""
import json, os, glob, collections, datetime, re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC = os.path.join(REPO, ".sde-security")
START = "<!-- SDE-SECURITY-HARDENING-START -->"
END = "<!-- SDE-SECURITY-HARDENING-END -->"

handoff = json.load(open(os.path.join(REPO, ".sde-handoff.json"), encoding="utf-8"))
cls = json.load(open(os.path.join(SEC, "classification.json"), encoding="utf-8"))
selected = json.load(open(os.path.join(SEC, "selected-cms.json"), encoding="utf-8"))
idx = json.load(open(os.path.join(SEC, "cm-list", "index.json"), encoding="utf-8"))
if isinstance(idx, dict):
    idx = list(idx.values())
T = {r["cm_id"]: r for r in idx}

HOST = handoff["sde_host"].rstrip("/")
PID = handoff["project_id"]


def sanitize_title(t):
    s = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return s


def cm_link(cm):
    return f"{HOST}/bunits/{handoff['business_unit_id']}/projects/{PID}/tasks/{PID}-{cm}/"


# ---- rows: one per skill FILE ----
rows = []
for f in sorted(glob.glob(os.path.join(SEC, "library-lookup", "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    cm = d["cm_id"]
    dom = cls[cm]["domain"]
    cat = cls[cm]["category"]
    rec = T[cm]
    if d["result"] == "LIBRARY_SOURCED":
        for m in d["matched_amendments"]:
            slug = re.sub(r"[^a-z0-9]+", "-", m["technology"].lower().replace("+", "p").replace("#", "sharp")).strip("-")
            rows.append({
                "cm_id": cm, "title": rec["title"], "domain": dom,
                "skill_file": f"skills/{dom}/{cm}-{slug}/SKILL.md",
                "priority": rec["priority"], "category": cat,
                "source": f"LIBRARY:{m['amendment_id']}",
            })
    else:
        slug = sanitize_title(rec["title"])[:48].strip("-")
        rows.append({
            "cm_id": cm, "title": rec["title"], "domain": dom,
            "skill_file": f"skills/{dom}/{cm}-{slug}/SKILL.md",
            "priority": rec["priority"], "category": cat,
            "source": "TEMPLATE",
        })

assert len({r["skill_file"] for r in rows}) == len(rows), "duplicate skill file path"

by_domain = collections.defaultdict(list)
for r in rows:
    by_domain[r["domain"]].append(r)
for d in by_domain:
    by_domain[d].sort(key=lambda r: (-r["priority"], r["cm_id"]))

cats = collections.Counter(cls[c]["category"] for c in selected["selected_cm_ids"])
ft = sum(1 for c in selected["selected_cm_ids"] if cls[c]["category"] != "PROCESS")
lib_files = sum(1 for r in rows if r["source"] != "TEMPLATE")
tmpl_files = sum(1 for r in rows if r["source"] == "TEMPLATE")

def esc(s):
    return s.replace("|", "\\|")

L = []
a = L.append
a(START)
a("")
a("# Security Hardening — SD Elements")
a("")
a("## Project Overview")
a("")
a("| Field | Value |")
a("|-------|-------|")
a(f"| Application | {handoff['project_name']} |")
a(f"| SD Elements project | {HOST}/bunits/{handoff['business_unit_id']}/projects/{PID}/ |")
a(f"| Project ID | {PID} |")
a(f"| Total Countermeasures | {selected['selected_count']} (selected scope) |")
a("| Source | Codebase |")
a(f"| Repository path | {handoff['repository_path']} |")
a("")
a("## Countermeasure Summary by Category")
a("")
a("| Category | Count | Handling |")
a("|----------|-------|----------|")
a(f"| CODE_FIX | {cats.get('CODE_FIX', 0)} | Skill file with a code fix |")
a(f"| INFRA | {cats.get('INFRA', 0)} | Documentation-only skill file |")
a(f"| PROCESS | {cats.get('PROCESS', 0)} | Noted in SD Elements, no skill file |")
a(f"| **File-tracked total** | **{ft}** | **{len(rows)} skill files** ({lib_files} library-sourced, {tmpl_files} template) |")
a("")
a("## Countermeasure Index")
a("")
a(f"One row per skill file. A countermeasure with library content for several technologies has one row per technology.")
a("")
for dom in sorted(by_domain):
    a(f"### {dom} ({len(by_domain[dom])} files)")
    a("")
    a("| ID | Title | Skill File | Priority | Category | Status | Source |")
    a("|----|-------|------------|----------|----------|--------|--------|")
    for r in by_domain[dom]:
        a(f"| {r['cm_id']} | {esc(r['title'])} | [{r['skill_file']}]({r['skill_file']}) | {r['priority']} | {r['category']} | Pending | {r['source']} |")
    a("")
a("## Completion Requirements")
a("")
a(f"- Every one of the {len(rows)} skill files listed above must reach a terminal status.")
a("- A CODE_FIX file is complete when its Required Fix is implemented and its Success Criteria hold.")
a("- An INFRA file is complete when its guidance has been documented and routed to the owning team.")
a("- Library-sourced files carry SD Elements' own content; apply them as written and do not edit the library text.")
a("- Update the Status column in this table and the `**Status:**` line in each template file together.")
a("")
a("## Progress Tracking")
a("")
a("| Metric | Count |")
a("|--------|-------|")
a(f"| Total skill files | {len(rows)} |")
a(f"| Pending | {len(rows)} |")
a("| Applied | 0 |")
a("| Documented | 0 |")
a("")
a("## Verification Checklist")
a("")
a(f"- [ ] All {len(rows)} skill files exist at the paths listed above")
a(f"- [ ] All {ft} file-tracked countermeasures are represented by at least one file")
a(f"- [ ] The {lib_files} library-sourced files match their SD Elements amendment byte for byte")
a("- [ ] Every template file carries Category, SD Elements link, Priority and Status")
a("- [ ] No countermeasure classified PROCESS has a skill file")
a("- [ ] Status values in this index agree with the status inside each file")
a("")
a(END)

block = "\n".join(L)

path = os.path.join(REPO, "AGENTS.md")
if os.path.exists(path):
    existing = open(path, encoding="utf-8").read()
    if START in existing and END in existing:
        pre = existing.split(START)[0]
        post = existing.split(END, 1)[1]
        out = pre + block + post
    else:
        out = existing.rstrip("\n") + "\n\n" + block + "\n"
else:
    out = block + "\n"
open(path, "w", encoding="utf-8").write(out)

json.dump(rows, open(os.path.join(SEC, "ledger-rows.json"), "w", encoding="utf-8"), indent=2)
print(f"rows={len(rows)} library={lib_files} template={tmpl_files} domains={len(by_domain)}")
print(f"AGENTS.md bytes={len(out)}")
