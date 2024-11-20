import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import colorama

# Initialize colorama for cross-platform colored output
colorama.init()

class ColorFormatter(logging.Formatter):
    """Custom formatter with colors only for log level"""
    
    # Color codes
    grey = "\x1b[38;21m"
    green = "\x1b[38;5;28m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    # Color mapping for different log levels
    level_colors = {
        logging.DEBUG: grey,
        logging.INFO: green,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red
    }

    def __init__(self):
        super().__init__()
        self.fmt = "%(asctime)s | %(colored_levelname)s | %(message)s"
        self.default_formatter = logging.Formatter(self.fmt, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record):
        # Add colored level name to the record
        levelname = record.levelname
        color = self.level_colors.get(record.levelno, self.reset)
        record.colored_levelname = f"{color}{levelname:8}{self.reset}"
        
        return self.default_formatter.format(record)

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging with colored level names and rotation."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Clear existing handlers
    logging.getLogger().handlers.clear()

    # Setup console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter())

    # Setup rotating file handler (without colors)
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=500 * 1024 * 1024,  # 500 MB
        backupCount=10,  # Keep 10 backup files
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    )

    # Configure loggers
    loggers = ["uvicorn", "uvicorn.access", "uvicorn.error", "assistant"]
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(getattr(logging, log_level))
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.propagate = False

    # Get the main logger
    main_logger = logging.getLogger("assistant")
    return main_logger

# Create a global logger instance
logger = setup_logging()