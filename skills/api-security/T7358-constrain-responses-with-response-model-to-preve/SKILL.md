---
name: t7358-constrain-responses-with-response-model-to-prevent-sensiti
description: Declare an explicit response_model on every route so only the intended fields are serialized to the client.
---

# T7358: Constrain responses with response_model to prevent sensitive-data exposure (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7358](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7358/)
**Priority:** 9

**Finding:** The route declares no response_model, so whatever the handler builds — including the environment dump — is serialized to the client unfiltered.

**Code to Fix:**
```python
# app/apis/debug/services/get_debug_info_service.py lines 11-12
@router.get("/debug", status_code=status.HTTP_200_OK)
def get_debug_info_service():
```

**Required Fix:**
```python
# app/apis/debug/services/get_debug_info_service.py
class StatusResponse(BaseModel):
    status: str
    version: str


@router.get("/internal/status", response_model=StatusResponse)
def get_status(...):
    return StatusResponse(status="ok", version=settings.VERSION)
```

**Success Criteria:**
- Every route declares a response_model.
- No response model exposes password hashes, reset codes or environment values.
- Adding a sensitive column to a model does not change any API response.

**Status:** Applied
