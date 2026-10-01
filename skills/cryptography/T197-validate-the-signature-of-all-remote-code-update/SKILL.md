---
name: t197-validate-the-signature-of-all-remote-code-updates-to-verify
description: Verify a signature over any remote content before the service stores or serves it.
---

# T197: Validate the signature of all remote code/updates to verify their origin and integrity

**Category:** CODE_FIX
**SD Elements:** [T197](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T197/)
**Priority:** 9

**Finding:** Remote content is fetched and stored with no signature or integrity check on its origin.

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
def _fetch_verified_image(image_url: str, signature_b64: str) -> bytes:
    content = _fetch_image(image_url)
    try:
        settings.CONTENT_SIGNING_PUBLIC_KEY.verify(
            base64.b64decode(signature_b64),
            content,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
    except InvalidSignature:
        raise HTTPException(status_code=400, detail="Image failed integrity verification")
    return content
```

**Success Criteria:**
- Remote content is rejected when its signature does not verify.
- The verification key is distributed out of band, not alongside the content.
- Verification happens before the content is persisted.

**Status:** Applied
