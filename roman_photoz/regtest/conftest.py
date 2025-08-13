import logging
import sys

import pytest
from romancal.regtest.conftest import *


@pytest.fixture(scope="session")
def dms_logger():
    """Set up a 'DMS' logger for use in tests.

    The primary use is to report DMS requirement log
    messages to stderr but can also be used for general
    stderr logging in tests.
    """
    logger = logging.getLogger("DMS")
    # Don't propagate to root logger to avoid double reporting
    # during stpipe API calls (like Step.call).
    logger.propagate = False
    if not logger.hasHandlers():
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
