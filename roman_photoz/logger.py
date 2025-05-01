import logging


def setup_logging(level=logging.INFO):
    """Set up logging configuration for roman_photoz module"""
    # Create a logger specific to our module instead of configuring the root logger
    logger = logging.getLogger("roman_photoz")

    # Only configure if it hasn't been configured yet
    if not logger.handlers:
        # Set propagate to False to prevent messages from being passed to the root logger
        logger.propagate = False

        # Set the level
        logger.setLevel(level)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Create handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

    return logger


# Create the default logger instance
logger = setup_logging()
