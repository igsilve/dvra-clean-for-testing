#!/usr/bin/env python3
"""Content offload + assemble_skill_files.

Phase 1 (offload): writes .sde-security/cm-work/{CM_ID}.json for every template
CM from the AI-authored content modules. Library CMs already have their
cm-work/{CM_ID}__{tech-slug}.json from Step 6.3 and are never rewritten here.

Phase 2 (assemble): writes one SKILL.md per offload file. Library files are the
amendment text byte-exact plus render_additional_requirements(); template files
are render_template() over the AI-authored fields. This module authors no
content -- it only copies and assembles.
"""
import json, os, re, glob, importlib.util, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC = os.path.join(REPO, ".sde-security")
CW = os.path.join(SEC, "cm-work")
SKILLS = os.path.join(REPO, "skills")

handoff = json.load(open(os.path.join(REPO, ".sde-handoff.json"), encoding="utf-8"))
cls = json.load(open(os.path.join(SEC, "classification.json"), encoding="utf-8"))
idx = json.load(open(os.path.join(SEC, "cm-list", "index.json"), encoding="utf-8"))
if isinstance(idx, dict):
    idx = list(idx.values())
T = {r["cm_id"]: r for r in idx}
code_map = json.load(open(os.path.join(SEC, "code-map.json"), encoding="utf-8"))
rows = json.load(open(os.path.join(SEC, "ledger-rows.json"), encoding="utf-8"))
ROW_BY_PATH = {r["skill_file"]: r for r in rows}

HOST = handoff["sde_host"].rstrip("/")
BU = handoff["business_unit_id"]
PID = handoff["project_id"]


def load(name, attr):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SEC, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, attr)


CODEFIX = load("content-codefix", "CODEFIX")
INFRA = load("content-infra", "INFRA")

FORBIDDEN_MARKERS = ["vuln-code-snippet", "intentionally vulnerable", "by design"]


def cm_link(cm):
    return f"{HOST}/bunits/{BU}/projects/{PID}/tasks/{PID}-{cm}/"


def skill_name(cm, title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    name = f"{cm.lower()}-{slug}"
    return name[:64].rstrip("-")


def render_additional_requirements(cm_id, reqs):
    if not reqs:
        return ""
    s = "\n\n---\n\n## Additional Requirements (SD Elements project)\n\n"
    s += f"These requirements apply to {cm_id} in this project because of its survey answers. Copied verbatim from SD Elements.\n"
    for r in reqs:
        s += f"\n### {r['title']}\n\n{r['text'].rstrip()}\n"
    return s


def load_reqs(cm):
    p = os.path.join(SEC, "project-requirements", f"{cm}.json")
    if not os.path.exists(p):
        return []
    data = json.load(open(p, encoding="utf-8")).get("additional_requirements", [])
    return sorted(data, key=lambda r: r.get("ordinal", 0))


# ------------------------------------------------------------------ phase 1
def offload_templates():
    written = 0
    for f in sorted(glob.glob(os.path.join(SEC, "library-lookup", "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        if d["result"] == "LIBRARY_SOURCED":
            continue
        cm = d["cm_id"]
        cat = cls[cm]["category"]
        rec = T[cm]
        if cat == "INFRA":
            c = INFRA[cm]
            fields = {
                "format": "documentation",
                "title": rec["title"],
                "priority": rec["priority"],
                "category": cat,
                "link": cm_link(cm),
                "description": c["description"],
                "guidance": c["guidance"],
                "searched": c["searched"],
                "found": c["found"],
                "missing": c["missing"],
                "conclusion": c["conclusion"],
                "action": c["action"],
            }
        else:
            c = CODEFIX[cm]
            cm_entry = code_map[cm]
            fields = {
                "format": "code",
                "title": rec["title"],
                "priority": rec["priority"],
                "category": cat,
                "link": cm_link(cm),
                "description": c["description"],
                "language": cm_entry["language"],
                "file": cm_entry["file"],
                "start_line": cm_entry["start_line"],
                "end_line": cm_entry["end_line"],
                "finding": cm_entry["finding"],
                "current_code": cm_entry["snippet"],
                "required_fix": c["fix"],
                "criteria": c["criteria"],
            }
        json.dump(
            {"cm_id": cm, "category": cat, "library_sourced": False, "content_fields": fields},
            open(os.path.join(CW, f"{cm}.json"), "w", encoding="utf-8"), indent=2,
        )
        written += 1
    return written


# ------------------------------------------------------------------ phase 2
def render_template(cm, f):
    if f["format"] == "documentation":
        return (
            f"---\n"
            f"name: {skill_name(cm, f['title'])}\n"
            f"description: {f['description']}\n"
            f"---\n\n"
            f"### Task {cm}: {f['title']} (DOCUMENTATION ONLY)\n\n"
            f"**Category:** {f['category']}\n"
            f"**SD Elements:** [{cm}]({f['link']})\n"
            f"**Priority:** {f['priority']}\n\n"
            f"**Guidance:** {f['guidance']}\n\n"
            f"**Why Not Code-Fixable:**\n"
            f"- Searched: {f['searched']}\n"
            f"- Found: {f['found']}\n"
            f"- Missing: {f['missing']}\n"
            f"- Conclusion: {f['conclusion']}\n\n"
            f"**Recommended Action:** {f['action']}\n\n"
            f"**Status:** Pending\n"
        )

    line_ref = f"{f['file']} line {f['start_line']}"
    if f["end_line"] != f["start_line"]:
        line_ref = f"{f['file']} lines {f['start_line']}-{f['end_line']}"
    criteria = "\n".join(f"- {c}" for c in f["criteria"])
    return (
        f"---\n"
        f"name: {skill_name(cm, f['title'])}\n"
        f"description: {f['description']}\n"
        f"---\n\n"
        f"# {cm}: {f['title']}\n\n"
        f"**Category:** {f['category']}\n"
        f"**SD Elements:** [{cm}]({f['link']})\n"
        f"**Priority:** {f['priority']}\n\n"
        f"**Finding:** {f['finding']}\n\n"
        f"**Code to Fix:**\n"
        f"```{f['language']}\n"
        f"# {line_ref}\n"
        f"{f['current_code']}\n"
        f"```\n\n"
        f"**Required Fix:**\n"
        f"```{f['language']}\n"
        f"{f['required_fix']}\n"
        f"```\n\n"
        f"**Success Criteria:**\n"
        f"{criteria}\n\n"
        f"**Status:** Pending\n"
    )


def assemble():
    fidelity = []
    written = 0
    for f in sorted(glob.glob(os.path.join(CW, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        cm = d["cm_id"]
        dom = cls[cm]["domain"]

        if d.get("library_sourced"):
            slug = d["tech_slug"]
            path = os.path.join(SKILLS, dom, f"{cm}-{slug}", "SKILL.md")
            content = d["content"]
            appended = render_additional_requirements(cm, load_reqs(cm))
            for line in appended.split("\n"):
                for anchor in ("**Status:**", "**Category:**", "**Spec Context:**"):
                    if anchor in line:
                        print(f"STOP: {cm} additional requirement line contains {anchor}: {line}")
                        sys.exit(4)
            body = content + appended
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "w", encoding="utf-8").write(body)
            back = open(path, encoding="utf-8").read()
            ok = back[:len(content)] == content and back[len(content):] == appended
            if not ok:
                os.remove(path)
                open(path, "w", encoding="utf-8").write(body)
                back = open(path, encoding="utf-8").read()
                ok = back[:len(content)] == content and back[len(content):] == appended
            fidelity.append(
                f"[FIDELITY] {cm}/{slug}: source={len(content)}ch appended={len(appended)}ch "
                f"written={len(back)}ch {'PASS' if ok else 'FAIL'}"
            )
        else:
            fields = d["content_fields"]
            slug = re.sub(r"[^a-z0-9]+", "-", T[cm]["title"].lower()).strip("-")[:48].strip("-")
            path = os.path.join(SKILLS, dom, f"{cm}-{slug}", "SKILL.md")
            body = render_template(cm, fields)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "w", encoding="utf-8").write(body)

        rel = os.path.relpath(path, REPO)
        assert rel in ROW_BY_PATH, f"{cm}: generated path {rel} has no ledger row"
        # Vulnerability markers must not survive from the repository into a
        # generated file. SD Elements' own text is copied byte-exact and is
        # never screened -- only AI-authored template bodies are.
        if not d.get("library_sourced"):
            lower = body.lower()
            for marker in FORBIDDEN_MARKERS:
                assert marker not in lower, f"{cm}: forbidden marker {marker!r}"
        written += 1
    return written, fidelity


if __name__ == "__main__":
    n = offload_templates()
    print(f"[OFFLOAD] template content files written: {n}")
    total, fid = assemble()
    for line in fid:
        print(line)
    print(f"[ASSEMBLE] SKILL.md files written: {total}")
    print(f"[ASSEMBLE] FIDELITY FAIL count: {sum(1 for l in fid if l.endswith('FAIL'))}")
