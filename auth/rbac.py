from fastapi import Request, HTTPException, Depends
from auth.roles import Role

def role_required(*allowed: Role):
    async def guard(request: Request):
        role = getattr(request.state, "role", None)
        if role is None or role not in set(a.value if isinstance(a, Role) else a for a in allowed):
            raise HTTPException(status_code=403, detail="Forbidden")
    return Depends(guard)
