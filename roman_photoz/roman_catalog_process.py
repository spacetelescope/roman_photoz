### COSMOS example with rail+lephare ###
import argparse
import json
import os
from collections import OrderedDict
from pathlib import Path
from typing import Union

import lephare as lp
import numpy as np
import pkg_resources
from asdf import AsdfFile
from astropy.table import Table
from rail.core.stage import RailStage
from rail.estimation.algos.lephare import LephareEstimator, LephareInformer

from .default_config_file import default_roman_config
from .roman_catalog_handler import RomanCatalogHandler

DS = RailStage.data_store
DS.__class__.allow_overwrite = True

LEPHAREDIR = os.environ.get("LEPHAREDIR", lp.LEPHAREDIR)
LEPHAREWORK = os.environ.get(
    "LEPHAREWORK", (Path(LEPHAREDIR).parent / "work").as_posix()
)
# default paths and filenames
DEFAULT_INPUT_FILENAME = "roman_simulated_catalog.in"
DEFAULT_INPUT_PATH = LEPHAREWORK
DEFAULT_OUTPUT_FILENAME = "roman_photoz_results.asdf"
DEFAULT_OUTPUT_PATH = LEPHAREWORK

CWD = os.getcwd()


class RomanCatalogProcess:

    def __init__(self, config_filename: str = ""):
        self.data: dict = OrderedDict()
        # set configuration file (roman will have its own)
        self.set_config_file(config_filename)
        # set attributes used for determining the redshift
        self.flux_cols: list = []
        self.flux_err_cols: list = []
        self.inform_stage = None
        self.estimated = None
        # read in the elements from default_roman_output.para
        default_output_file = Path(
            pkg_resources.resource_filename(__name__, "data/default_roman_output.para")
        )
        if default_output_file.exists():
            with open(default_output_file) as f:
                self.default_roman_output_keys = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]

    def set_config_file(self, config_filename: Union[dict, str] = ""):
        if isinstance(config_filename, str):
            if config_filename:
                # a config filename was provided in JSON format
                with open(config_filename) as f:
                    self.config = json.load(f)
            else:
                # use default Roman config file
                self.config = default_roman_config
        else:
            # a config was provided in dict format
            self.config = config_filename

    def get_data(
        self,
        input_filename: str = DEFAULT_INPUT_FILENAME,
        input_path: str = DEFAULT_INPUT_PATH,
    ):
        # N.B.: This is the method that will fetch multiband
        # roman catalog when it is available by using
        # the roman_catalog_handler.py module.
        # For now, just for the sake of implementation, we'll
        # be using data from the COSMOS example.

        if not input_filename:
            raise ValueError("Input filename is required.")

        # read custom input_filename
        filename = Path(input_path, input_filename).as_posix()

        # get filters
        bands = self.config["FILTER_LIST"].split(",")
        print(len(bands))

        # read catalog data
        if Path(input_path).suffix == ".asdf":
            handler = RomanCatalogHandler(input_path)
            cat_data = handler.process()
        else:
            cat_data = Table.read(filename, format="ascii.no_header")

        # loop over the filters we want to keep to get
        # the number of the filter, n, and the name, b
        # (the final data has to have  2 * n_bands + 4 columns)
        for n, b in enumerate(bands):
            flux = cat_data[cat_data.colnames[1 + 2 * n]].astype(float)
            flux_err = cat_data[cat_data.colnames[2 + 2 * n]].astype(float)
            self.data[f"flux_{b.split("_")[1].split(".")[0]}"] = flux
            self.flux_cols.append(f"flux_{b.split("_")[1].split(".")[0]}")
            self.data[f"flux_err_{b.split("_")[1].split(".")[0]}"] = flux_err
            self.flux_err_cols.append(f"flux_err_{b.split("_")[1].split(".")[0]}")
        self.data["context"] = np.array(cat_data[cat_data.colnames[-3]]).astype(int)
        self.data["redshift"] = np.array(cat_data[cat_data.colnames[-2]]).astype(float)
        self.data["string_data"] = np.array(cat_data[cat_data.colnames[-1]]).astype(
            bytes
        )

    def create_informer_stage(self):
        # use the inform stage to create the library of SEDs with
        # various redshifts, extinction parameters, and reddening values.
        # -> Informer will produce as output a generic “model”,
        #    the details of which depends on the sub-class.
        # |we use rail's interface here to create the informer stage
        # |https://rail-hub.readthedocs.io/en/latest/api/rail.estimation.informer.html
        self.inform_stage = LephareInformer.make_stage(
            name="inform_roman",
            nondetect_val=np.nan,
            model=f"{Path(LEPHAREWORK, 'roman_model.pkl').as_posix()}",
            hdf5_groupname="",
            lephare_config=self.config,
            bands=self.flux_cols,
            err_bands=self.flux_err_cols,
            ref_band=self.flux_cols[0],
        )
        self.inform_stage.inform(self.data)

    def create_estimator_stage(self):
        # take the sythetic test data, and find the best
        # fits from the library. This results in a PDF, zmode,
        # and zmean for each input test data.
        # -> Estimators use a generic “model”, apply the photo-z estimation
        #    and provide as “output” a QPEnsemble, with per-object p(z).
        # |we use rail's interface here to create the estimator stage
        # |https://rail-hub.readthedocs.io/en/latest/api/rail.estimation.estimator.html
        estimate_lephare = LephareEstimator.make_stage(
            name="estimate_roman",
            nondetect_val=np.nan,
            model=self.inform_stage.get_handle("model"),
            hdf5_groupname="",
            aliases=dict(input="test_data", output="lephare_estim"),
            bands=self.flux_cols,
            err_bands=self.flux_err_cols,
            ref_band=self.flux_cols[0],
            output_keys=self.default_roman_output_keys,
            lephare_config=self.config,
        )

        self.estimated = estimate_lephare.estimate(self.data)

    def save_results(
        self,
        output_filename: str = DEFAULT_OUTPUT_FILENAME,
        output_path: str = LEPHAREWORK,
    ):

        output_filename = Path(output_path, output_filename).as_posix()
        ancil_data = self.estimated.data.ancil

        tree = {"roman_photoz_results": ancil_data}
        with AsdfFile(tree) as af:
            af.write_to(output_filename)

    def process(
        self,
        input_filename: str = DEFAULT_INPUT_FILENAME,
        input_path: str = DEFAULT_INPUT_PATH,
        output_filename: str = DEFAULT_OUTPUT_FILENAME,
        output_path: str = DEFAULT_OUTPUT_PATH,
    ):
        self.get_data(input_filename=input_filename, input_path=input_path)
        self.create_informer_stage()
        self.create_estimator_stage()
        self.save_results(output_filename=output_filename, output_path=output_path)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process Roman catalog data.")
    parser.add_argument(
        "--config_filename",
        type=str,
        default="",
        help="Path to the configuration file (default: use default Roman config).",
    )
    parser.add_argument(
        "--input_path",
        type=str,
        default=DEFAULT_INPUT_PATH,
        help=f"Path to the catalog file (default: {DEFAULT_INPUT_PATH}).",
    )
    parser.add_argument(
        "--input_filename",
        type=str,
        default=DEFAULT_INPUT_FILENAME,
        help=f"Input catalog filename (default: {DEFAULT_INPUT_FILENAME}).",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to where the results will be saved (default: {DEFAULT_OUTPUT_PATH}).",
    )
    parser.add_argument(
        "--output_filename",
        type=str,
        default=DEFAULT_OUTPUT_FILENAME,
        help=f"Output filename (default: {DEFAULT_OUTPUT_FILENAME}).",
    )

    args = parser.parse_args()

    rcp = RomanCatalogProcess(config_filename=args.config_filename)

    rcp.process(
        input_filename=args.input_filename,
        input_path=args.input_path,
        output_filename=args.output_filename,
        output_path=args.output_path,
    )

    print("Done.")
