"""Lightweight session model to attach a stable identifier to each chat visitor.

If you already use an ORM (SQLModel / SQLAlchemy), swap this out for an ORM model.
"""
from datetime import datetime
import uuid
from typing import Optional

class Session:
    def __init__(self, session_id: Optional[str] = None):
        self.id: str = session_id or str(uuid.uuid4())
        self.created_at: datetime = datetime.utcnow()
        self.last_seen: datetime = self.created_at

    def touch(self):
        """Update `last_seen` every time the user sends a message."""
        self.last_seen = datetime.utcnow()
