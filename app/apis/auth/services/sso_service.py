import os

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()

oauth = OAuth()
oauth.register(
    name="sso",
    server_metadata_url=os.getenv("SSO_DISCOVERY_URL"),
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/auth/sso/login")
async def sso_login(request: Request):
    redirect_uri = request.url_for("sso_callback")
    return await oauth.sso.authorize_redirect(request, redirect_uri)


@router.get("/auth/sso/callback", name="sso_callback")
async def sso_callback(request: Request):
    token = await oauth.sso.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info:
        user_info = await oauth.sso.userinfo(token=token)
    return {"access_token": token.get("access_token"), "userinfo": user_info}
