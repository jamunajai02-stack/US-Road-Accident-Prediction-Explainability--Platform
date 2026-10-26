"""Structured contextual JSON logging helper with seamless fallback across stdlib and structlog."""

import json
import logging
import sys
from typing import Any

try:
    import structlog
except ImportError:
    structlog = None


class JsonFormatter(logging.Formatter):
    """Custom standard library formatter outputting JSON records."""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_data.update(record.extra_data)
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


class StructuredLoggerAdapter:
    """Wrapper around standard library Logger allowing structlog-style keyword arguments."""
    def __init__(self, stdlib_logger: logging.Logger):
        self._logger = stdlib_logger

    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        if kwargs:
            extra = {"extra_data": kwargs}
            self._logger.log(level, msg, extra=extra)
        else:
            self._logger.log(level, msg)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def warn(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def exception(self, msg: str, **kwargs: Any) -> None:
        self._logger.exception(msg, extra={"extra_data": kwargs} if kwargs else None)


def setup_logger(name: str = "accident_platform", log_level: str = "INFO") -> Any:
    """Configure structured logging pipeline with JSON output for production observability."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    if structlog is not None:
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=level,
        )
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        return structlog.get_logger(name)
    else:
        stdlib_logger = logging.getLogger(name)
        stdlib_logger.setLevel(level)
        if not stdlib_logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JsonFormatter())
            stdlib_logger.addHandler(handler)
        return StructuredLoggerAdapter(stdlib_logger)


logger = setup_logger()
