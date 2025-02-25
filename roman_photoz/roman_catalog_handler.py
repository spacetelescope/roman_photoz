import os
from pathlib import Path

import numpy as np
from roman_datamodels import datamodels as rdm

from .default_config_file import default_roman_config


class RomanCatalogHandler:
    def __init__(self, catname: str = ""):
        self.cat_name = catname
        self.cat_df = None
        self.catalog = None
        self.cat_temp_filename = "cat_temp_file.csv"
        # get Roman's filter names from default config file
        self.filter_names = (
            default_roman_config.get("FILTER_LIST")
            .replace(".pb", "")
            .replace("roman/", "")
            .split(",")
        )

    def format_colnames(self):
        # TODO: implement logic to handle the order of the bands
        # (the hack below is just because we only have synthetic images for F158)
        new_cols = {
            old_col: f"{old_col}_{self.filter_names[5]}"
            for old_col in self.cat_df.columns[-2:]
        }
        self.cat_df.rename(columns=new_cols, inplace=True)

    def format_catalog(self):
        def calculate_context(row):
            # calculate context for each row
            non_zero_indices = []
            for i in range(0, len(row), 2):
                # check if either column in the pair is non-zero
                if row[i] != 0 or (i + 1 < len(row) and row[i + 1] != 0):
                    non_zero_indices.append(i // 2)
            return sum(2**idx for idx in non_zero_indices)

        print("Formatting catalog...")
        self.format_colnames()
        self.catalog = self.cat_df.loc[
            :,
            [
                f"flux_psf_{self.filter_names[5]}",
                f"flux_psf_err_{self.filter_names[5]}",
            ],
        ].copy()
        # Create new zeroed columns for other filters
        for filter_name in self.filter_names:
            if filter_name != "roman_F158":
                self.catalog[f"flux_psf_{filter_name}"] = 0
                self.catalog[f"flux_psf_err_{filter_name}"] = 0

        # context is a binary flag that indicates which bands are used
        self.catalog["context"] = self.catalog.apply(calculate_context, axis=1)
        self.catalog["zspec"] = np.nan
        self.catalog["string_data"] = "arbitrary info"
        print("Done.")

    def save_catalog(self):
        print(f"Saving catalog {self.cat_temp_filename}...")
        if self.catalog is not None:
            # save as CSV
            output_filename = self.cat_temp_filename
            self.catalog.to_csv(output_filename, index=True, sep=" ", header=False)
            print(f"Catalog saved as CSV format: {output_filename}")
        else:
            print("No catalog to save.")

    def read_catalog(self):
        print(f"Parsing catalog {self.cat_name}...")
        dm = rdm.open(self.cat_name)
        self.cat_df = dm.source_catalog.to_pandas()

        print("Done.")

    def add_to_phot_par(self):
        pass

    def process(self):
        self.read_catalog()
        self.format_catalog()
        self.save_catalog()
        self.add_to_phot_par()


if __name__ == "__main__":

    test_bigdata = os.getenv("TEST_BIGDATA")
    if test_bigdata is None:
        raise ValueError("Environment variable TEST_BIGDATA is not set")
    reg_test_data = Path(test_bigdata)

    test_cat = reg_test_data / "r0000101001001001001_0001_wfi01_cat.asdf"

    catalog_handler = RomanCatalogHandler(test_cat.as_posix())

    catalog_handler.process()

    print("Done.")
