---
name: t279-avoid-dynamically-loading-any-code-without-proper-security
description: Constrain what the service loads at runtime to a reviewed, trusted set.
---

# T279: Avoid dynamically loading any code without proper security considerations

**Category:** CODE_FIX
**SD Elements:** [T279](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T279/)
**Priority:** 8

**Finding:** Arbitrary remote bytes are pulled in at request time and stored for later use with no source restriction.

**Code to Fix:**
```python
# app/apis/menu/utils.py lines 9-13
def _image_url_to_base64(image_url: str):
    response = requests.get(image_url, stream=True)
    encoded_image = base64.b64encode(response.content).decode()

    return encoded_image
```

**Required Fix:**
```python
# app/apis/menu/utils.py
# Content is fetched only from the approved CDN, over HTTPS, with its digest
# verified against a signed manifest before it is stored:
content = _fetch_verified(_safe_image_url(image_url))
```

**Success Criteria:**
- Runtime loading of remote content is restricted to an allow-list.
- Loaded content is integrity-checked before use.
- No module is imported or code evaluated from a path derived from request data.

**Status:** Applied
