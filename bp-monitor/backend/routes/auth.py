from fastapi import APIRouter, Depends, HTTPException

from backend.database import get_db, generate_token, get_current_user
from backend.models import LoginRequest, TokenResponse, UserProfile
from backend.services.wechat import code2session

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, conn=Depends(get_db)):
    try:
        wx_data = await code2session(body.code)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    openid = wx_data["openid"]

    user = conn.execute(
        "SELECT * FROM users WHERE openid = ?", (openid,)
    ).fetchone()

    if user:
        token = generate_token()
        conn.execute(
            "UPDATE users SET session_token = ? WHERE id = ?",
            (token, user["id"]),
        )
        conn.commit()
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user["id"],)
        ).fetchone()
    else:
        token = generate_token()
        conn.execute(
            "INSERT INTO users (openid, session_token) VALUES (?, ?)",
            (openid, token),
        )
        conn.commit()
        user = conn.execute(
            "SELECT * FROM users WHERE openid = ?", (openid,)
        ).fetchone()

    return TokenResponse(
        token=token,
        user=UserProfile(**dict(user)),
    )


@router.get("/check")
async def check(user: dict = Depends(get_current_user)):
    return {"valid": True, "user": UserProfile(**user)}
