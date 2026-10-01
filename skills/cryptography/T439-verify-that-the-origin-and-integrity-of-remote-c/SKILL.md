---
name: t439-verify-that-the-origin-and-integrity-of-remote-code-and-upd
description: Check the integrity of content retrieved from a remote origin before it is accepted.
---

# T439: Verify that the origin and integrity of remote code and updates are checked (client side)

**Category:** CODE_FIX
**SD Elements:** [T439](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T439/)
**Priority:** 9

**Finding:** Content retrieved from a remote origin is accepted without any integrity verification before it is persisted and later served.

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
EXPECTED_DIGESTS = load_content_manifest()      # signed manifest, refreshed out of band


def _fetch_verified(url: str) -> bytes:
    content = _fetch_image(url)
    digest = hashlib.sha256(content).hexdigest()
    if digest != EXPECTED_DIGESTS.get(url):
        raise HTTPException(status_code=400, detail="Content integrity check failed")
    return content
```

**Success Criteria:**
- Retrieved content is compared against a digest from a trusted, signed manifest.
- A mismatch aborts the operation and is logged.

**Status:** Applied
