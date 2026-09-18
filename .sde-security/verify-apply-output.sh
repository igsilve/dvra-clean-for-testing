#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
python3 - <<'PY'
import json, re, sys
from pathlib import Path
root=Path.cwd(); errors=[]
def fail(msg): errors.append(msg)
expected_top={'source_skill','handoff_version','generated_at','upstream_handoff','repository_path','project_id','security_branch','scope','totals','countermeasures'}
expected_cm={'id','full_id','status','category','files_modified','sde_note_result'}
try: data=json.loads((root/'.sde-apply-handoff.json').read_text())
except Exception as e: fail(f'cannot read handoff: {e}'); data={}
if set(data)!=expected_top: fail('top-level keys mismatch')
if data.get('source_skill')!='apply-security-fixes': fail('source_skill mismatch')
if data.get('handoff_version')!='2': fail('handoff_version mismatch')
if not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z',str(data.get('generated_at',''))): fail('generated_at is not ISO8601 UTC')
if not (root/'.sde-handoff.json').is_file(): fail('upstream handoff missing')
t=data.get('totals',{}); cms=data.get('countermeasures',[])
if set(t)!={'applied','documented','skipped','scoped_total'}: fail('totals keys mismatch')
if not isinstance(cms,list): fail('countermeasures is not a list'); cms=[]
for i,c in enumerate(cms):
    if set(c)!=expected_cm: fail(f'CM {i}: keys mismatch'); continue
    cid=c.get('id'); status=c.get('status'); cat=c.get('category'); note=c.get('sde_note_result')
    if not re.fullmatch(r'T\d+',str(cid)): fail(f'CM {i}: invalid id')
    if c.get('full_id')!=f'4552-{cid}' or not re.fullmatch(r'4552-T\d+',str(c.get('full_id'))): fail(f'CM {i}: full_id mismatch')
    if status not in {'Applied','Documented','Skipped'}: fail(f'CM {i}: invalid status')
    if cat not in {'CODE_FIX','ML_CODE','INFRA','ML_DOC'}: fail(f'CM {i}: invalid category')
    if note not in {'ADDED','FAILED','NOT_SENT'}: fail(f'CM {i}: invalid note')
    if not isinstance(c.get('files_modified'),list): fail(f'CM {i}: files_modified not list'); continue
    if status in {'Documented','Skipped'} and c['files_modified']!=[]: fail(f'CM {i}: non-applied files')
    if status=='Applied':
        good=False
        for p in c['files_modified']:
            q=root/p
            forbidden=('/.sde-security/' in '/'+str(p) or str(p).startswith('security/') or re.search(r'(^|/)([^/]+_secure|[^/]+_fixed|[^/]+_safe)\.[^/]+$',str(p)) or Path(p).name.startswith('batch_'))
            if q.is_file() and not forbidden: good=True
        if not good: fail(f'CM {i}: no valid applied file')
if isinstance(t,dict):
    try:
        if t.get('scoped_total') != t.get('applied',0)+t.get('documented',0)+t.get('skipped',0) or t.get('scoped_total')!=len(cms): fail('totals integrity failure')
        for s in ('Applied','Documented','Skipped'):
            if t.get(s.lower()) != sum(c.get('status')==s for c in cms): fail(f'{s} total mismatch')
    except TypeError: fail('totals are not numeric')
rows=[]
for line in (root/'AGENTS.md').read_text().splitlines():
    a=[x.strip() for x in line.strip().split('|')[1:-1]] if line.strip().startswith('|') else []
    if len(a)==7 and re.fullmatch(r'T\d+',a[0]) and a[4] in ('CF','IN') and a[5] in ('Applied','Documented','Skipped'): rows.append(a)
skills=list((root/'skills').rglob('SKILL.md'))
ids={r[0] for r in rows}
if len(rows)!=len(skills): fail(f'AGENTS rows {len(rows)} != skills {len(skills)}')
if len(ids)!=t.get('scoped_total'): fail('unique terminal CM IDs mismatch')
if errors:
    print('VERIFY FAIL')
    for e in errors: print(' - '+e)
    sys.exit(1)
print('VERIFY PASS')
PY
