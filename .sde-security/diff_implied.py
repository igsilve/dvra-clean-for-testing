import json
import sys

draft_path = sys.argv[1]
draft = json.load(open(draft_path))
req = json.load(open(".sde-security/survey-requests.json"))
idx = json.load(open(".sde-security/survey-index.json"))

qmeta = {q["qid"]: q for q in idx}
atext = {a["id"]: (q["qid"], a["text"], q["section"], q["qtext"])
         for q in idx for a in q["answers"]}

requested = set(req["requested"]) - set(req["deselected"])
selected = {a["id"] for a in draft["answers"] if a["selected"]}

cslr = {a["id"] for q in idx if q["section"] == "Changes Since Last Release"
        for a in q["answers"]}

extras = sorted(selected - requested - cslr)
missing = sorted(requested - selected)
print(f"selected_total={len(selected)} requested={len(requested)} "
      f"cslr_selected={len(selected & cslr)}")
print(f"requested_but_not_selected={missing}")
print(f"IMPLIED_EXTRAS ({len(extras)}):")
for a in extras:
    qid, txt, sec, qtxt = atext.get(a, ("?", "?", "?", "?"))
    print(f"  {a} | {qid} | {sec} > {qtxt} | {txt}")
