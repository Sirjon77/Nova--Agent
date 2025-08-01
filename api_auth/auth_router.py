from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .security import create_jwt, verify_pw, hash_pw

router = APIRouter()
USERS = {'admin': hash_pw('adminpw')}

class LoginForm(BaseModel):
    username: str
    password: str

@router.post('/login')
def login(form: LoginForm):
    hashed = USERS.get(form.username)
    if not hashed or not verify_pw(form.password, hashed):
        raise HTTPException(status_code=400, detail='bad creds')
    return {
        'access': create_jwt(form.username, 'admin', 15),
        'refresh': create_jwt(form.username, 'admin', 1440)
    }
