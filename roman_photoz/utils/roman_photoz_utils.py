import os
from pathlib import Path

import lephare as lp
from astropy.table import Table

from roman_photoz.default_config_file import default_roman_config
from roman_photoz.logger import logger

LEPHAREDIR = os.environ.get("LEPHAREDIR", lp.LEPHAREDIR)
LEPHAREWORK = os.environ.get(
    "LEPHAREWORK", (Path(LEPHAREDIR).parent / "work").as_posix()
)
DEFAULT_OUTPUT_CATALOG_FILENAME = "roman_simulated_catalog.parquet"


def read_output_keys(output_keys_filename: str) -> list[str]:
    """
    Read the Roman output keys from the provided file.

    Parameters
    ----------
    output_keys_filename : str
        The filename of the file containing the output keys.

    Returns
    -------
    output_keys : list of str
        List of output key names read from the file.

    Raises
    ------
    FileNotFoundError
        If the output keys file is not found.
    """

    default_output_file = Path(output_keys_filename)

    if not default_output_file.exists():
        logger.error("Output keys file not found.")
        raise FileNotFoundError

    with open(default_output_file) as f:
        output_keys = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    return output_keys


def save_catalog(
    catalog: Table = None,
    output_path: str = LEPHAREWORK,
    output_filename: str = DEFAULT_OUTPUT_CATALOG_FILENAME,
    overwrite: bool = False,
):
    """
    Save the given catalog to a file.

    Parameters
    ----------
    catalog : astropy.table.Table
        The catalog to save.
    output_path : str or Path, optional
        Directory where the catalog file will be saved. Defaults to LEPHAREWORK if not specified.
    output_filename : str, optional
        Name of the output file. Defaults to 'roman_simulated_catalog.parquet' if not specified.
    """
    logger.info(f"Saving catalog to {Path(output_path)}/{output_filename}...")
    catalog.write(
        Path(output_path, output_filename), overwrite=overwrite, format="parquet"
    )
    logger.info("Catalog saved successfully")


def get_roman_filter_list(uppercase: bool = False) -> list[str]:
    """
    Get the filter names from the default Roman configuration in format 'fNNN'.

    Parameters
    ----------
    uppercase : bool, optional
        If True, return filter names in uppercase.
        If False, return in lowercase (default).

    Returns
    -------
    list of str
        List of filter names.
    """
    filter_list = default_roman_config.get("FILTER_LIST")
    if filter_list is not None:
        filters = filter_list.replace(".pb", "").replace("roman/roman_", "").split(",")
        if uppercase:
            return [f.upper() for f in filters]
        else:
            return [f.lower() for f in filters]
    else:
        raise ValueError("Filter list not found in default config file.")
