from collections import deque

_history = deque(maxlen=50)

def add(message: str):
    _history.append(message)

def get():
    return list(_history)
