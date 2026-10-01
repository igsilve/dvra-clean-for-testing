#!/usr/bin/env python3
"""Mechanical Step 6.2/6.3 processor.

Reads a composite `op=execute` amendments response (JSON file), and for each
sub-request result:
  * writes .sde-security/library-lookup/{CM}.json  (one per CM)
  * writes .sde-security/cm-work/{CM}__{slug}.json (one per matched amendment,
    `content` copied BYTE-EXACT from amendment.text -- never edited)
  * prints a [PROGRESS] line per CM

It makes no decisions beyond the deterministic title/technology match defined in
the contract; it authors no content.
"""
import json, os, re, sys, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC = os.path.join(REPO, ".sde-security")
LL = os.path.join(SEC, "library-lookup")
CW = os.path.join(SEC, "cm-work")
os.makedirs(LL, exist_ok=True)
os.makedirs(CW, exist_ok=True)

handoff = json.load(open(os.path.join(REPO, ".sde-handoff.json"), encoding="utf-8"))
POOL = {" ".join(t.lower().split()) for t in handoff.get("technology_pool") or []}
ALIASES = {
    "python": {"python", "python/django", "python/flask"},
    "node.js": {"node", "express"},
    "javascript": {"javascript"},
}
CLS = json.load(open(os.path.join(SEC, "classification.json"), encoding="utf-8"))


def tech_slug(s):
    s = s.lower().replace("+", "p").replace("#", "sharp")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def matches_pool(suffix):
    n = " ".join(suffix.lower().split())
    if n in POOL:
        return True
    al = ALIASES.get(n)
    return bool(al and (al & POOL))


def req_count(cm):
    p = os.path.join(SEC, "project-requirements", f"{cm}.json")
    if not os.path.exists(p):
        return 0
    return json.load(open(p, encoding="utf-8")).get("count", 0)


def write_lookup(cm, status, result, matched):
    art = {
        "cm_id": cm,
        "endpoint": f"library/tasks/{cm}/amendments/",
        "http_status": status,
        "result": result,
        "retry_count": 0,
        "queried_at": datetime.datetime.now(datetime.timezone.utc)
                         .isoformat().replace("+00:00", "Z"),
        "matched_amendments": matched,
        "additional_requirements_count": req_count(cm),
    }
    json.dump(art, open(os.path.join(LL, f"{cm}.json"), "w", encoding="utf-8"), indent=2)


def main(path):
    raw = json.load(open(path, encoding="utf-8"))
    failed_ids = set(raw.get("failed_ids") or [])
    results = raw.get("results") or []

    # 401/403 anywhere is a HARD STOP, checked before stamping any CM.
    for r in results:
        if r.get("http_status_code") in (401, 403):
            print(f"HARD STOP: {r['reference_id']} returned {r['http_status_code']}")
            sys.exit(2)

    for r in results:
        cm = r["reference_id"]
        status = r.get("http_status_code")
        body = r.get("body")

        if status == 404:
            write_lookup(cm, status, "TEMPLATE_404", [])
            print(f"[PROGRESS] {cm}: TEMPLATE (404)")
            continue
        if cm in failed_ids or not (200 <= (status or 0) < 300) \
           or not isinstance(body, dict) or "results" not in body:
            write_lookup(cm, status, "TEMPLATE_API_ERROR", [])
            print(f"[PROGRESS] {cm}: TEMPLATE (API error)")
            continue

        pat = re.compile(r"^" + re.escape(cm) + r" - SKILL\.md - (.+)$")
        matched, seen_am, seen_slug = [], set(), {}
        for a in body.get("results") or []:
            m = pat.match(a.get("title") or "")
            if not m:
                continue
            suffix = m.group(1).strip()
            if not matches_pool(suffix):
                continue
            text = a.get("text") or ""
            if not text.startswith("---"):        # invalid YAML front matter -> drop
                continue
            am_id = a.get("id")
            if am_id in seen_am:
                continue
            seen_am.add(am_id)
            slug = tech_slug(suffix)
            if slug in seen_slug:
                print(f"STOP: {cm} has two amendments for slug '{slug}': "
                      f"{seen_slug[slug]} and {am_id}")
                sys.exit(3)
            seen_slug[slug] = am_id

            src_len = len(text)
            out = os.path.join(CW, f"{cm}__{slug}.json")
            json.dump({"cm_id": cm, "tech_slug": slug,
                       "category": CLS.get(cm, {}).get("category"),
                       "library_sourced": True, "amendment_id": am_id,
                       "technology": suffix, "content": text,
                       "source_len": src_len},
                      open(out, "w", encoding="utf-8"), indent=2)
            rb = json.load(open(out, encoding="utf-8"))
            if len(rb["content"]) != src_len:     # read-back assertion
                json.dump({"cm_id": cm, "tech_slug": slug,
                           "category": CLS.get(cm, {}).get("category"),
                           "library_sourced": True, "amendment_id": am_id,
                           "technology": suffix, "content": text,
                           "source_len": src_len},
                          open(out, "w", encoding="utf-8"), indent=2)
                rb = json.load(open(out, encoding="utf-8"))
                assert len(rb["content"]) == src_len, f"{cm}/{slug} persist mismatch"
            matched.append({"amendment_id": am_id, "technology": suffix,
                            "source_amendment_char_count": src_len})

        if matched:
            write_lookup(cm, status, "LIBRARY_SOURCED", matched)
            print(f"[PROGRESS] {cm}: LIBRARY_SOURCED -> "
                  + ", ".join(f"{m['technology']}({m['amendment_id']})" for m in matched))
        else:
            write_lookup(cm, status, "TEMPLATE_NO_MATCH", [])
            print(f"[PROGRESS] {cm}: TEMPLATE_NO_MATCH")


if __name__ == "__main__":
    main(sys.argv[1])
