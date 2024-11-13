import logging

from pythonjsonlogger import jsonlogger

def setup_json_logging() -> None:
    """Set up JSON logging."""
    logging.getLogger().handlers.clear()  # Очистка существующих обработчиков

    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    log_handler = logging.StreamHandler()
    log_handler.setFormatter(formatter)

    # Отключение наследования обработчиков для логгеров "uvicorn"
    logging.getLogger("uvicorn").propagate = False
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").propagate = False

    # Установка обработчика и форматтера для логгеров "uvicorn" и "uvicorn.access"
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "assistant"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()  # Очистка существующих обработчиков, если они есть
        logger.setLevel(logging.INFO)
        logger.addHandler(log_handler)