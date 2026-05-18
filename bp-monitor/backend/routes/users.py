from fastapi import APIRouter, Depends

from backend.database import get_db, get_current_user
from backend.models import UserProfile, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_me(user: dict = Depends(get_current_user)):
    return UserProfile(**user)


@router.put("/me", response_model=UserProfile)
async def update_me(
    body: UserUpdate,
    user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return UserProfile(**user)

    set_clauses = []
    values = []
    for key, val in updates.items():
        set_clauses.append(f"{key} = ?")
        values.append(val)
    values.append(user["id"])

    conn.execute(
        f"UPDATE users SET {', '.join(set_clauses)}, updated_at = datetime('now','localtime') WHERE id = ?",
        values,
    )
    conn.commit()

    updated = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user["id"],)
    ).fetchone()
    return UserProfile(**dict(updated))
