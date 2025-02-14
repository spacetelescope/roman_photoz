### COSMOS example with rail+lephare ###
import json
import sys
from rail.estimation.algos.lephare import LephareInformer, LephareEstimator
import numpy as np
import lephare as lp
from rail.core.stage import RailStage
from astropy.table import Table
from collections import OrderedDict
import os
from pathlib import Path
from default_config_file import default_roman_config
from typing import Union


DS = RailStage.data_store
DS.__class__.allow_overwrite = True


class RomanCatalogProcess:

    def __init__(self, config_filename: str = ""):
        self.data: dict = OrderedDict()
        # set configuration file (roman will have its own)
        self.set_config_file(config_filename)
        # max number of objects to process from input catalog
        # TODO: remove object limit
        self.nobj = 100
        # set attributes used for determining the redshift
        self.flux_cols: list = []
        self.flux_err_cols: list = []
        self.inform_stage = None
        self.estimated = None

    def set_config_file(self, config_filename: Union[dict, str] = ""):
        if isinstance(config_filename, str):
            if config_filename:
                # a config filename was provided in JSON format
                with open(config_filename, "r") as f:
                    self.config = json.load(f)
            else:
                # use default Roman config file
                self.config = default_roman_config
        else:
            # a config was provided in dict format
            self.config = config_filename

    def get_data(self, input_filename: str = "", input_path=""):
        # N.B.: This is the method that will fetch multiband
        # roman catalog when it is available by using
        # the roman_catalog_handler.py module.
        # For now, just for the sake of implementation, we'll
        # be using data from the COSMOS example.

        if input_filename == "":
            lp.data_retrieval.get_auxiliary_data(
                keymap=self.config,
                additional_files=["examples/COSMOS.in", "examples/output.para"],
            )
            filename = Path(lp.LEPHAREDIR, "examples/COSMOS.in")
            format = "ascii"
        else:
            # read custom input_filename
            filename = Path(input_path, input_filename)
            format = "csv"

        # get filters
        bands = self.config["FILTER_LIST"].split(",")
        print(len(bands))

        # set limit to the first 100 objects
        # TODO: remove object limit
        cat_data = Table.read(filename, format=format)[: self.nobj]

        # loop over the filters we want to keep to get
        # the number of the filter, n, and the name, b
        for n, b in enumerate(bands):
            flux = cat_data[cat_data.colnames[1 + 2 * n]]
            flux_err = cat_data[cat_data.colnames[2 + 2 * n]]
            self.data[f"flux_{b}"] = flux
            self.flux_cols.append(f"flux_{b}")
            self.data[f"flux_err_{b}"] = flux_err
            self.flux_err_cols.append(f"flux_err_{b}")
        self.data["redshift"] = np.array(cat_data[cat_data.colnames[-2]])

    def create_informer_stage(self):
        # use the inform stage to create the library of SEDs with
        # various redshifts, extinction parameters, and reddening values.
        # -> Informer will produce as output a generic “model”,
        #    the details of which depends on the sub-class.
        # |we use rail's interface here to create the informer stage
        # |https://rail-hub.readthedocs.io/en/latest/api/rail.estimation.informer.html
        self.inform_stage = LephareInformer.make_stage(
            name="inform_COSMOS",
            nondetect_val=np.nan,
            model="lephare.pkl",
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
            name="test_Lephare_COSMOS",
            nondetect_val=np.nan,
            model=self.inform_stage.get_handle("model"),
            hdf5_groupname="",
            aliases=dict(input="test_data", output="lephare_estim"),
            bands=self.flux_cols,
            err_bands=self.flux_err_cols,
            ref_band=self.flux_cols[0],
        )

        self.estimated = estimate_lephare.estimate(self.data)

    def process(self, input_filename="", input_path=""):
        self.get_data(input_filename=input_filename, input_path=input_path)
        self.create_informer_stage()
        self.create_estimator_stage()


if __name__ == "__main__":

    # get config file
    config_filename = sys.argv[1] if len(sys.argv) > 1 else ""
    # get path where the results will be saved to
    input_path = sys.argv[2] if len(sys.argv) > 2 else "examples"
    # get effective area filename
    input_filename = sys.argv[3] if len(sys.argv) > 3 else "roman_simulated_catalog.in"

    rcp = RomanCatalogProcess(config_filename=config_filename)

    rcp.process(input_filename=input_filename, input_path=input_path)

    print("Done.")
