
from loguru import logger
import sys
import os

logger.remove()
logger.add(
    sys.stdout,
    serialize=True,
    backtrace=True,
    diagnose=True,
    level=os.getenv('LOG_LEVEL', 'INFO')
)
