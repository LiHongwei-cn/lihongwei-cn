import httpx

from backend.config import WECHAT_APPID, WECHAT_SECRET

WECHAT_API = "https://api.weixin.qq.com/sns/jscode2session"


async def code2session(code: str) -> dict:
    """Exchange WeChat login code for openid and session_key."""
    params = {
        "appid": WECHAT_APPID,
        "secret": WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(WECHAT_API, params=params)
        resp.raise_for_status()
        data = resp.json()

    if "errcode" in data and data["errcode"] != 0:
        errmsg = data.get("errmsg", "unknown error")
        raise RuntimeError(f"微信登录失败: {errmsg} (code={data['errcode']})")

    return data
