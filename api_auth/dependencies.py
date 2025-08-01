from fastapi.security import HTTPBearer
from fastapi import Depends, HTTPException, status
from .security import verify

bearer = HTTPBearer()
def current_user(token=Depends(bearer)):
    try:
        return verify(token.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')

def require_roles(roles):
    def wrapper(user=Depends(current_user)):
        if user.get('role') not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')
        return user
    return wrapper
