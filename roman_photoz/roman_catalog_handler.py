import os
from pathlib import Path

import numpy as np
from roman_datamodels import datamodels as rdm

from .default_config_file import default_roman_config


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
                filter_list.replace(".pb", "").replace("roman/", "").split(",")
            )
        else:
            raise ValueError("Filter list not found in default config file.")

    def format_catalog(self):
        """
        Format the catalog by appending necessary fields and columns.
        """
        print("Formatting catalog...")
        # self.format_colnames()

        self.catalog = self.cat_array[["id"]].copy()

        for filter_name in self.filter_names:
            self.catalog = np.lib.recfunctions.append_fields(
                self.catalog,
                f"flux_psf_{filter_name}",
                self.cat_array[f"{filter_name.replace('roman_', '')}_flux_psf"],
            )
            self.catalog = np.lib.recfunctions.append_fields(
                self.catalog,
                f"flux_psf_err_{filter_name}",
                self.cat_array[f"{filter_name.replace('roman_', '')}_flux_psf_err"],
            )

        # populate additional required columns
        self.catalog = np.lib.recfunctions.append_fields(
            self.catalog,
            "context",
            self.cat_array["context"],
            usemask=False,
        )
        self.catalog = np.lib.recfunctions.append_fields(
            self.catalog,
            "zspec",
            self.cat_array["zspec"],
            usemask=False,
        )
        self.catalog = np.lib.recfunctions.append_fields(
            self.catalog,
            "string_data",
            self.cat_array["string_data"].astype(str),
            usemask=False,
        )
        print("Done.")

    def read_catalog(self):
        """
        Read the catalog file and convert it to a numpy structured array.
        """
        print(f"Parsing catalog {self.cat_name}...")
        dm = rdm.open(self.cat_name)
        self.cat_array = (
            dm.source_catalog.as_array()
        )  # Convert Table to numpy structured array

        print("Done.")

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
