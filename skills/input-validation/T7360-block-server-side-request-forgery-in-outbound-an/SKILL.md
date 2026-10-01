---
name: t7360-block-server-side-request-forgery-in-outbound-and-backgrou
description: Validate and pin outbound request targets so request data cannot steer the service to an internal address.
---

# T7360: Block server-side request forgery in outbound and background-task calls (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7360](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7360/)
**Priority:** 10

**Finding:** The outbound request target comes straight from the request body with no scheme, host or address validation.

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
response = requests.get(
    _safe_image_url(image_url),     # scheme + host allow-list + resolved-IP check
    timeout=(3, 5),
    allow_redirects=False,
    stream=True,
    verify=certifi.where(),
)
```

**Success Criteria:**
- Target validation happens before the request and after DNS resolution.
- Redirects are disabled.
- Connect and read timeouts are set.
- Background tasks use the same validated client.

**Status:** Applied
