---
name: t1392-test-for-server-side-request-forgery
description: Validate the outbound request target against an allow-list and block requests to internal addresses.
---

# T1392: Test for Server Side Request Forgery

**Category:** CODE_FIX
**SD Elements:** [T1392](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1392/)
**Priority:** 8

**Finding:** requests.get is issued against an unvalidated caller-supplied URL, reaching internal addresses and non-HTTP schemes.

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
import ipaddress, socket
from urllib.parse import urlparse

ALLOWED_IMAGE_HOSTS = {"cdn.restaurant.com"}


def _safe_image_url(image_url: str) -> str:
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_IMAGE_HOSTS:
        raise HTTPException(status_code=400, detail="Image host not allowed")

    for info in socket.getaddrinfo(parsed.hostname, 443):
        address = ipaddress.ip_address(info[4][0])
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
            raise HTTPException(status_code=400, detail="Image host not allowed")

    return image_url


# and the fetch itself:
response = requests.get(_safe_image_url(url), timeout=5, allow_redirects=False, stream=True)
```

**Success Criteria:**
- Only HTTPS URLs on the allow-list are fetched.
- Every resolved address is checked against private, loopback, link-local and reserved ranges.
- Redirects are not followed, so the validated target is the one contacted.
- A request for `http://169.254.169.254/latest/meta-data/` is rejected.

**Status:** Applied
