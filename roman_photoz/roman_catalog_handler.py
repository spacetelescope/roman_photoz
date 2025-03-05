import os
from pathlib import Path

import numpy as np
from roman_datamodels import datamodels as rdm

from .default_config_file import default_roman_config


class RomanCatalogHandler:
    def __init__(self, catname: str = ""):
        self.cat_name = catname
        self.cat_array = None
        self.catalog = None
        self.cat_temp_filename = "cat_temp_file.csv"
        # get Roman's filter names from default config file
        self.filter_names = (
            default_roman_config.get("FILTER_LIST")
            .replace(".pb", "")
            .replace("roman/", "")
            .split(",")
        )

    # def format_colnames(self):
    #     # TODO: implement logic to handle the order of the bands
    #     # (the hack below is just because we only have synthetic images for F158)
    #     new_cols = [
    #         f"{col}_{self.filter_names[5]}" for col in self.cat_array.dtype.names[-2:]
    #     ]
    #     self.cat_array.dtype.names = list(self.cat_array.dtype.names[:-2]) + new_cols

    def format_catalog(self):
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
        print(f"Parsing catalog {self.cat_name}...")
        dm = rdm.open(self.cat_name)
        self.cat_array = (
            dm.source_catalog.as_array()
        )  # Convert Table to numpy structured array

        print("Done.")

    def process(self):
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
