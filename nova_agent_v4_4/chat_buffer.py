"""Store a rolling buffer of the last N turns per session in Redis."""
from .redis_client import r
MAX_TURNS = 20

def get_short(session_id: str):
    return r.lrange(f"hist:{session_id}", 0, -1)

def store_short(session_id: str, user_msg: str, assistant_msg: str):
    r.rpush(f"hist:{session_id}", f"USER: {user_msg}\nASSISTANT: {assistant_msg}\n")
    r.ltrim(f"hist:{session_id}", -MAX_TURNS, -1)
