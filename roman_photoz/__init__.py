# Import after logger setup to avoid circular imports
from .create_simulated_catalog import SimulatedCatalog
from .default_config_file import *

# Import logger from the dedicated logger module
from .logger import logger, setup_logging
from .roman_catalog_handler import RomanCatalogHandler
from .roman_catalog_process import RomanCatalogProcess

__all__ = [
    "RomanCatalogHandler",
    "RomanCatalogProcess",
    "SimulatedCatalog",
    "logger",
    "setup_logging",
]
