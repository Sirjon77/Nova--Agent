"""Run Alembic migrations programmatically."""
import os, sys
from alembic import command
from alembic.config import Config

cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
command.upgrade(cfg, "head")
