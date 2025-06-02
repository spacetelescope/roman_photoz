import os
from pathlib import Path

import numpy as np
from astropy.table import Table
from numpy.lib import recfunctions as rfn
from roman_datamodels import datamodels as rdm

from roman_photoz.default_config_file import default_roman_config
from roman_photoz.logger import logger


class RomanCatalogHandler:
    """
    A class to handle Roman catalog operations including reading, formatting, and processing.

    Parameters
    ----------
    catname : str, optional
        The name of the catalog file (default is an empty string).
    """

    def __init__(self, catname: str = ""):
        """
        Initialize the RomanCatalogHandler with a catalog name.

        Parameters
        ----------
        catname : str, optional
            The name of the catalog file (default is an empty string).
        """
        self.cat_name = catname
        self.cat_array = None
        self.catalog = None
        self.cat_temp_filename = "cat_temp_file.csv"
        # get Roman's filter names from default config file
        filter_list = default_roman_config.get("FILTER_LIST")
        if filter_list is not None:
            self.filter_names = (
                filter_list.replace(".pb", "")
                .replace("roman/roman_", "")
                .lower()
                .split(",")
            )
        else:
            raise ValueError("Filter list not found in default config file.")

    def format_catalog(self):
        """
        Format the catalog by appending necessary fields and columns.
        """
        logger.info("Formatting catalog...")

        self.catalog = np.empty(0, dtype=[])
        self.catalog = rfn.append_fields(self.catalog, "label", self.cat_array["label"])

        for filter_id in self.filter_names:
            # Roman filter ID in format "fNNN"
            flux_col_name = f"psf_{filter_id}_flux"
            if flux_col_name in self.cat_array.dtype.names:
                self.catalog = rfn.append_fields(
                    self.catalog,
                    f"psf_{filter_id}_flux",
                    np.array(self.cat_array[flux_col_name]),
                )
                self.catalog = rfn.append_fields(
                    self.catalog,
                    f"psf_{filter_id}_flux_err",
                    np.array(self.cat_array[f"{flux_col_name}_err"]),
                )

        # populate additional required columns
        self.catalog = rfn.append_fields(
            self.catalog,
            "context",
            self.cat_array["context"]
            if "context" in self.cat_array.dtype.names
            else np.zeros(len(self.cat_array), dtype=int),
            usemask=False,
        )
        self.catalog = rfn.append_fields(
            self.catalog,
            "zspec",
            self.cat_array["zspec"]
            if "zspec" in self.cat_array.dtype.names
            else np.zeros(len(self.cat_array), dtype=int),
            usemask=False,
        )
        self.catalog = rfn.append_fields(
            self.catalog,
            "string_data",
            self.cat_array["string_data"]
            if "string_data" in self.cat_array.dtype.names
            else np.full(len(self.cat_array), ""),
            usemask=False,
        )

        logger.info("Catalog formatting completed")

    def read_catalog(self):
        """
        Read the catalog file and convert it to a numpy structured array.
        """
        logger.info(f"Reading catalog {self.cat_name}...")

        if Path(self.cat_name).suffix == ".asdf":
            dm = rdm.open(self.cat_name)
            # Convert Table to numpy structured array
            self.cat_array = dm.source_catalog.as_array()
        elif Path(self.cat_name).suffix == ".parquet":
            self.cat_array = Table.read(self.cat_name)

        logger.info("Catalog read successfully")

    def process(self):
        """
        Process the catalog by reading and formatting it.

        Returns
        -------
        numpy.ndarray
            The formatted catalog.
        """
        self.read_catalog()
        self.format_catalog()

        return self.catalog


if __name__ == "__main__":
    test_bigdata = os.getenv("TEST_BIGDATA")
    if test_bigdata is None:
        raise ValueError("Environment variable TEST_BIGDATA is not set")
    reg_test_data = Path(test_bigdata)

    test_cat = reg_test_data / "r0000101001001001001_0001_wfi01_cat.asdf"

    catalog_handler = RomanCatalogHandler(test_cat.as_posix())

    catalog_handler.process()

    print("Done.")
