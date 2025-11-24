"""
Structured Logging Configuration for Artify Platform
Provides centralized logging with rotation, formatting, and multiple handlers
"""
import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
import json
import os
from typing import Optional


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    Outputs logs in JSON format for easy parsing and analysis
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code

        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output
    Makes logs easier to read during development
    """

    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{self.BOLD}{record.levelname}{self.RESET}"
        record.name = f"{self.BOLD}{record.name}{self.RESET}"
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_json: bool = False,
    enable_file: bool = True,
    enable_console: bool = True
) -> logging.Logger:
    """
    Setup structured logging with multiple handlers

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        enable_json: Enable JSON formatting for file logs
        enable_file: Enable file logging
        enable_console: Enable console logging

    Returns:
        Configured logger instance
    """

    # Create logs directory if it doesn't exist
    if enable_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger("artify")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console Handler (for development)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Use colored formatter for console
        console_format = "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s"
        console_formatter = ColoredFormatter(
            console_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File Handlers
    if enable_file:
        # General log file (rotating by size)
        general_log_file = Path(log_dir) / "artify.log"
        file_handler = RotatingFileHandler(
            general_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)

        # Error log file (daily rotation)
        error_log_file = Path(log_dir) / "error.log"
        error_handler = TimedRotatingFileHandler(
            error_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)

        # Choose formatter based on enable_json
        if enable_json:
            file_formatter = JSONFormatter()
            error_formatter = JSONFormatter()
        else:
            file_format = "%(asctime)s | %(levelname)-8s | %(name)-15s | %(module)s:%(funcName)s:%(lineno)d | %(message)s"
            file_formatter = logging.Formatter(
                file_format,
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            error_formatter = file_formatter

        file_handler.setFormatter(file_formatter)
        error_handler.setFormatter(error_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(error_handler)

    # Don't propagate to root logger
    logger.propagate = False

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (uses module name if not provided)

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"artify.{name}")
    else:
        return logging.getLogger("artify")


# Initialize default logger
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "logs")
ENABLE_JSON_LOGS = os.getenv("ENABLE_JSON_LOGS", "false").lower() == "true"
ENABLE_FILE_LOGS = os.getenv("ENABLE_FILE_LOGS", "true").lower() == "true"
ENABLE_CONSOLE_LOGS = os.getenv("ENABLE_CONSOLE_LOGS", "true").lower() == "true"

# Setup default logger
default_logger = setup_logging(
    log_level=LOG_LEVEL,
    log_dir=LOG_DIR,
    enable_json=ENABLE_JSON_LOGS,
    enable_file=ENABLE_FILE_LOGS,
    enable_console=ENABLE_CONSOLE_LOGS
)


# Request logging middleware helper
class RequestLogger:
    """Helper class for logging HTTP requests"""

    @staticmethod
    def log_request(
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Log HTTP request with details"""
        logger = get_logger("api")

        extra = {
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2)
        }

        if user_id:
            extra["user_id"] = user_id

        if status_code >= 500:
            logger.error(
                f"{method} {path} - {status_code} - {duration_ms:.2f}ms - ERROR: {error}",
                extra=extra
            )
        elif status_code >= 400:
            logger.warning(
                f"{method} {path} - {status_code} - {duration_ms:.2f}ms",
                extra=extra
            )
        else:
            logger.info(
                f"{method} {path} - {status_code} - {duration_ms:.2f}ms",
                extra=extra
            )


if __name__ == "__main__":
    # Test logging
    test_logger = get_logger("test")

    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")

    # Test with extra fields
    test_logger.info(
        "User logged in",
        extra={"user_id": 123, "request_id": "abc-123"}
    )

    # Test exception logging
    try:
        1 / 0
    except ZeroDivisionError:
        test_logger.exception("Math error occurred")

    print("\n✅ Logging test completed. Check logs/ directory for output.")
