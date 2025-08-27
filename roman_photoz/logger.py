import sys
import logging


def setup_logging(level=logging.INFO, log_file="roman_photoz.log"):
    """Set up logging configuration for roman_photoz module"""
    logger = logging.getLogger("roman_photoz")

    if not logger.handlers:
        logger.propagate = False
        logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console handler for INFO only
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)
        console_handler.addFilter(lambda record: record.levelno == logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler for everything else (including other packages)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
        logging.getLogger().setLevel(logging.DEBUG)

    return logger
