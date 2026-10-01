---
name: t175-test-that-the-client-validates-digital-certificates
description: Prove with a test that the client rejects an invalid or untrusted certificate.
---

# T175: Test that the client validates digital certificates

**Category:** CODE_FIX
**SD Elements:** [T175](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T175/)
**Priority:** 7

**Finding:** The outbound client's certificate validation behavior is left entirely to defaults and is never asserted.

**Code to Fix:**
```python
# app/apis/menu/utils.py lines 9-11
def _image_url_to_base64(image_url: str):
    response = requests.get(image_url, stream=True)
    encoded_image = base64.b64encode(response.content).decode()
```

**Required Fix:**
```python
# app/tests/security/test_tls_validation.py
@pytest.mark.security
def test_untrusted_certificate_is_rejected():
    with pytest.raises(requests.exceptions.SSLError):
        session.get("https://untrusted-root.badssl.com/", timeout=5)


@pytest.mark.security
def test_expired_certificate_is_rejected():
    with pytest.raises(requests.exceptions.SSLError):
        session.get("https://expired.badssl.com/", timeout=5)
```

**Success Criteria:**
- Automated tests cover untrusted, expired and hostname-mismatched certificates.
- The tests fail if verification is disabled anywhere.

**Status:** Applied
