"""
Logging configuration for X-Factor
Uses loguru for better logging experience
"""

import sys
from loguru import logger
from pathlib import Path
from src.config.settings import settings

# Remove default handler
logger.remove()

# Add console handler with colors
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True,
)

# Add file handler with rotation
log_file = Path(settings.LOG_FILE)
log_file.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    settings.LOG_FILE,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.LOG_LEVEL,
    rotation="100 MB",  # Rotate when file reaches 100MB
    retention="30 days",  # Keep logs for 30 days
    compression="zip",  # Compress rotated logs
    enqueue=True,  # Thread-safe
)

# Add error-only file
error_log_file = log_file.parent / "errors.log"
logger.add(
    str(error_log_file),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="50 MB",
    retention="90 days",
    compression="zip",
    enqueue=True,
)

# Export logger
__all__ = ["logger"]
