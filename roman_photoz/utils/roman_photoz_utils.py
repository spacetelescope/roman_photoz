import os
from pathlib import Path

import lephare as lp
import numpy as np
from astropy.table import Table

from roman_photoz.default_config_file import default_roman_config
from roman_photoz.logger import logger

LEPHAREDIR = os.environ.get("LEPHAREDIR", lp.LEPHAREDIR)
LEPHAREWORK = os.environ.get(
    "LEPHAREWORK", (Path(LEPHAREDIR).parent / "work").as_posix()
)
DEFAULT_OUTPUT_CATALOG_FILENAME = "roman_simulated_catalog.parquet"

# Extinction coefficients (A_filter / SFD) from Schlafly+2016 calibrated to SFD
ROMAN_EXTINCTION_COEFFICIENTS: dict[str, float] = {
    "f062": 2.2662,
    "f087": 1.2895,
    "f106": 0.8506,
    "f129": 0.5757,
    "f146": 0.4427,
    "f158": 0.3755,
    "f184": 0.2680,
    "f212": 0.2039,
    "f213": 0.2039,
}


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


def get_extinction_coefficient(filter_name: str) -> float:
    """
    Get the A/SFD dust extinction coefficient for a given Roman filter.

    Parameters
    ----------
    filter_name : str
        The filter identifier (e.g. 'F062', 'f062', 'roman_f062', etc.).

    Returns
    -------
    float
        The extinction coefficient A/SFD for the filter.

    Raises
    ------
    KeyError
        If the filter name is not recognized.
    """
    cleaned = (
        filter_name.lower()
        .replace("roman_", "")
        .replace("roman/", "")
        .replace(".pb", "")
    )
    if cleaned in ROMAN_EXTINCTION_COEFFICIENTS:
        return ROMAN_EXTINCTION_COEFFICIENTS[cleaned]
    raise KeyError(f"Extinction coefficient not found for filter: {filter_name}")


def deredden_flux(
    flux: np.ndarray,
    dust_ebv: np.ndarray,
    filter_name: str,
) -> np.ndarray:
    """
    Apply dust extinction correction (dereddening) to observed flux or flux error.

    flux_dered = flux_observed * 10 ** (dust_ebv * coefficient[filter] / 2.5)

    Parameters
    ----------
    flux : np.ndarray
        Observed flux or flux error values.
    dust_ebv : np.ndarray
        Galactic E(B-V) color excess values (from SFD dust map).
    filter_name : str
        Filter name or identifier.

    Returns
    -------
    np.ndarray
        Dereddened flux or flux error values.
    """
    coeff = get_extinction_coefficient(filter_name)
    factor = 10.0 ** (np.asarray(dust_ebv) * coeff / 2.5)
    return np.asarray(flux) * factor
