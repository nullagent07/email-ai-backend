import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import colorama

# Initialize colorama for cross-platform colored output
colorama.init()

class ColorFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    # Color codes
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self):
        super().__init__()
        self.fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging with colors and rotation."""
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
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
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