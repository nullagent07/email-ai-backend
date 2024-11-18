import sys
from pathlib import Path
from loguru import logger

def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging with loguru"""
    
    # Remove default handler
    logger.remove()
    
    # Configure console logging
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level=log_level,
        colorize=True,
    )
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure file logging with rotation
    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level=log_level,
    )

# Export logger instance
log = logger
