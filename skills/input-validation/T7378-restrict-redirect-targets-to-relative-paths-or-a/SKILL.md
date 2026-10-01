---
name: t7378-restrict-redirect-targets-to-relative-paths-or-an-allowlis
description: Do not follow redirects to a target the caller chose; keep navigation targets relative or on an allow-list.
---

# T7378: Restrict redirect targets to relative paths or an allowlist (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7378](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7378/)
**Priority:** 8

**Finding:** requests.get follows redirects by default from a caller-supplied URL, so the final target is attacker-chosen.

**Code to Fix:**
```python
# app/apis/menu/utils.py lines 9-11
def _image_url_to_base64(image_url: str):
    response = requests.get(image_url, stream=True)
    encoded_image = base64.b64encode(response.content).decode()
```

**Required Fix:**
```python
# app/apis/menu/utils.py
response = requests.get(
    _safe_image_url(image_url),
    timeout=5,
    allow_redirects=False,      # the validated host is the one contacted
    stream=True,
)
if response.is_redirect:
    raise HTTPException(status_code=400, detail="Redirects are not permitted for image sources")
```

**Success Criteria:**
- `allow_redirects=False` is set on outbound requests driven by request data.
- Any redirect response is treated as a failure rather than followed.
- Application-level redirects accept only relative paths or allow-listed absolute URLs.

**Status:** Applied
