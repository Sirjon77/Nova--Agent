import os
import datetime
import jwt
import bcrypt

SECRET = os.getenv('JWT_SECRET', 'nova-secret')
ALG = 'HS256'
ACCESS_TTL = int(os.getenv('ACCESS_TTL_MIN', 15))
REFRESH_TTL = int(os.getenv('REFRESH_TTL_MIN', 1440))

def _now(): return datetime.datetime.utcnow()

def hash_pw(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_pw(pw, hashed):
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def create_jwt(sub, role, ttl_min):
    exp = _now() + datetime.timedelta(minutes=ttl_min)
    return jwt.encode({'sub': sub, 'role': role, 'exp': exp}, SECRET, algorithm=ALG)

def verify(token):
    return jwt.decode(token, SECRET, algorithms=[ALG])
