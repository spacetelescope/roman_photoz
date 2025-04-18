import logging
from pathlib import Path

import pytest

from roman_photoz.logger import setup_logging


@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file path for testing."""
    return tmp_path / "test_roman_photoz.log"


def test_setup_logging_creates_logger_with_correct_name():
    """Test that setup_logging creates a logger with the correct name."""
    logger = setup_logging()
    assert logger.name == "roman_photoz"


@pytest.mark.parametrize(
    "log_level, level_name",
    [
        (logging.NOTSET, "NOTSET"),
        (logging.DEBUG, "DEBUG"),
        (logging.INFO, "INFO"),
        (logging.WARNING, "WARNING"),
        (logging.ERROR, "ERROR"),
        (logging.CRITICAL, "CRITICAL"),
    ],
    ids=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
)
def test_setup_logging_sets_correct_level(log_level, level_name):
    """Test that setup_logging sets the correct log level for all available levels."""
    # Clear existing handlers and reset for clean test
    logger_instance = logging.getLogger("roman_photoz")
    logger_instance.handlers.clear()

    # Test the specified log level
    logger = setup_logging(level=log_level)
    assert (
        logger.level == log_level
    ), f"Logger level should be {level_name} ({log_level})"


def test_setup_logging_creates_handlers():
    """Test that setup_logging creates file and console handlers."""
    # Clear existing handlers for clean test
    logging.getLogger("roman_photoz").handlers.clear()

    logger = setup_logging()

    # Should have 2 handlers (console and file)
    assert len(logger.handlers) == 2

    # Check handler types
    handler_types = [type(h) for h in logger.handlers]
    assert logging.StreamHandler in handler_types
    assert logging.FileHandler in handler_types


def test_setup_logging_uses_correct_formatter():
    """Test that setup_logging uses the correct formatter."""
    # Clear existing handlers for clean test
    logging.getLogger("roman_photoz").handlers.clear()

    logger = setup_logging()

    # All handlers should have the same formatter
    for handler in logger.handlers:
        formatter = handler.formatter
        assert formatter._fmt == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def test_setup_logging_only_configures_once():
    """Test that setup_logging doesn't add handlers if already configured."""
    # Clear existing handlers for clean test
    logging_instance = logging.getLogger("roman_photoz")
    logging_instance.handlers.clear()

    # First call should add handlers
    logger1 = setup_logging()
    initial_handler_count = len(logger1.handlers)

    # Second call should not add more handlers
    logger2 = setup_logging()
    assert len(logger2.handlers) == initial_handler_count


def test_setup_logging_creates_file_handler_with_correct_path(temp_log_file):
    """Test that setup_logging creates a file handler with the correct path."""
    # Clear existing handlers for clean test
    logging.getLogger("roman_photoz").handlers.clear()

    logger = setup_logging(log_file=str(temp_log_file))

    # Find the FileHandler
    file_handler = next(
        h for h in logger.handlers if isinstance(h, logging.FileHandler)
    )

    # Check that the path matches
    assert Path(file_handler.baseFilename).resolve() == temp_log_file.resolve()


def test_logger_writes_to_file(temp_log_file):
    """Test that logger writes messages to the specified file."""
    # Clear existing handlers for clean test
    logging.getLogger("roman_photoz").handlers.clear()

    # Create logger with test file
    logger = setup_logging(log_file=str(temp_log_file))

    # Log a test message
    test_message = "Test log message"
    logger.info(test_message)

    # Check that the message was written to the file
    with open(temp_log_file) as f:
        log_content = f.read()

    assert test_message in log_content


@pytest.mark.parametrize(
    "log_level, message_level, should_log",
    [
        (logging.INFO, logging.DEBUG, False),  # DEBUG shouldn't be logged at INFO level
        (logging.INFO, logging.INFO, True),  # INFO should be logged at INFO level
        (logging.INFO, logging.WARNING, True),  # WARNING should be logged at INFO level
        (logging.INFO, logging.ERROR, True),  # ERROR should be logged at INFO level
        (logging.DEBUG, logging.DEBUG, True),  # DEBUG should be logged at DEBUG level
    ],
    ids=[
        "info_rejects_debug",
        "info_accepts_info",
        "info_accepts_warning",
        "info_accepts_error",
        "debug_accepts_debug",
    ],
)
def test_logger_respects_log_level(temp_log_file, log_level, message_level, should_log):
    """Test that logger respects the configured log level."""
    # Clear existing handlers for clean test
    logging.getLogger("roman_photoz").handlers.clear()

    # Create logger with specified level and test file
    logger = setup_logging(log_file=str(temp_log_file), level=log_level)

    # Log a test message at the specified level
    test_message = "Test log message for level testing"

    # Use the appropriate logging method based on the message level
    if message_level == logging.DEBUG:
        logger.debug(test_message)
    elif message_level == logging.INFO:
        logger.info(test_message)
    elif message_level == logging.WARNING:
        logger.warning(test_message)
    elif message_level == logging.ERROR:
        logger.error(test_message)

    # Check if the message was logged to the file
    with open(temp_log_file) as f:
        log_content = f.read()

    if should_log:
        assert test_message in log_content
    else:
        assert test_message not in log_content
