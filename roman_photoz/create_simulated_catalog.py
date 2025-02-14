### COSMOS example with rail+lephare ###

from rail.estimation.algos.lephare import LephareInformer, LephareEstimator
import numpy as np
import lephare as lp
from rail.core.stage import RailStage
import matplotlib.pyplot as plt
from astropy.table import Table
from collections import OrderedDict
import os
from .default_config_file import default_roman_config
from pathlib import Path

from numpy.lib import recfunctions as rfn

ROMAN_DEFAULT_CONFIG = default_roman_config

DS = RailStage.data_store
DS.__class__.allow_overwrite = True


class SimulatedCatalog:
    def __init__(self):
        self.data = OrderedDict()
        # set configuration file (roman will have its own)
        self.lephare_config = ROMAN_DEFAULT_CONFIG

        # change some of the default parameters
        # set redshift grid (step, z_i, z_f)
        self.lephare_config["Z_STEP"] = ".1,0.,7."
        self.lephare_config["MOD_EXTINC"] = "18,26,26,33,26,33,26,33"
        self.lephare_config["EXTINC_LAW"] = (
            "SMC_prevot.dat,SB_calzetti.dat,SB_calzetti_bump1.dat,SB_calzetti_bump2.dat"
        )
        self.lephare_config["EM_LINES"] = "EMP_UV"
        self.lephare_config["EM_DISPERSION"] = "0.5,1.,1.5"

        # max number of objects to process from input catalog
        self.nobj = 100
        # set attributes used for determining the redshift
        self.flux_cols = []
        self.flux_err_cols = []
        self.inform_stage = None
        self.estimated = None
        self.filter_lib = None
        self.simulated_data_filename = ""
        self.simulated_data = None

    def get_data(self):
        # N.B.: This is the method that will fetch multiband
        # roman catalog when it is available by using
        # the roman_catalog_handler.py module.
        # For now, just for the sake of implementation, we'll
        # be using data from the COSMOS example.

        lp.data_retrieval.get_auxiliary_data(
            keymap=self.lephare_config,
            additional_files=["examples/COSMOS.in", "examples/output.para"],
        )

        bands = self.lephare_config["FILTER_LIST"].split(",")
        print(len(bands))

        # set limit to the first 100 objects
        cosmos = Table.read(
            os.path.join(lp.LEPHAREDIR, "examples/COSMOS.in"), format="ascii"
        )[: self.nobj]

        # loop over the filters we want to keep to get
        # the number of the filter, n, and the name, b
        for n, b in enumerate(bands):
            flux = cosmos[cosmos.colnames[1 + 2 * n]]
            flux_err = cosmos[cosmos.colnames[2 + 2 * n]]
            self.data[f"flux_{b}"] = flux
            self.flux_cols.append(f"flux_{b}")
            self.data[f"flux_err_{b}"] = flux_err
            self.flux_err_cols.append(f"flux_err_{b}")
        self.data["redshift"] = np.array(cosmos[cosmos.colnames[-2]])

    def get_filters(self):
        self.filter_lib = lp.FilterSvc.from_keymap(
            lp.all_types_to_keymap(self.lephare_config)
        )
        # plot filters transmission
        # from matplotlib import pylab as plt
        # fig = plt.figure(figsize=(15, 8))
        # for f in filter_lib:
        #     d = f.data()
        #     plt.semilogx(d[0], d[1] / d[1].max())
        print(
            f"Created filter library using the filter files in {self.lephare_config["FILTER_REP"]}."
        )

    def create_simulated_data(self):
        star_overrides = {
            # "STAR_LIB_IN": "LIB_STAR",
            # "STAR_LIB_OUT": "ROMAN_SIMULATED_MAGS_STAR",
            # "STAR_SED": "sed/STAR/STAR_MOD_ALL.list",
            # "LIB_ASCII": "YES",
        }
        qso_overrides = {
            # "QSO_LIB_IN": "LIB_QSO",
            # "QSO_LIB_OUT": "ROMAN_SIMULATED_MAGS_QSO",
            # "QSO_SED": "sed/QSO/SALVATO09/AGN_MOD.list",
            # "LIB_ASCII": "YES",
        }
        gal_overrides = {
            "GAL_LIB_IN": "LIB_CE",
            "GAL_LIB_OUT": "ROMAN_SIMULATED_MAGS_GAL",
            "GAL_SED": "examples/COSMOS_MOD.list",
            "LIB_ASCII": "YES",
        }

        lp.prepare(
            config=self.lephare_config,
            star_config=star_overrides,
            gal_config=gal_overrides,
            qso_config=qso_overrides,
        )

        self.simulated_data_filename = gal_overrides.get("GAL_LIB_OUT")

    def create_simulated_input_catalog(self):
        catalog_name = Path(
            lp.LEPHAREDIR, "WORK", "lib_mag", f"{self.simulated_data_filename}.dat"
        ).as_posix()
        colnames = self.create_header(catalog_name=catalog_name)

        self.simulated_data = np.genfromtxt(
            catalog_name, dtype=None, names=colnames, encoding="utf-8"
        )

        # select only the magnitude columns for the input catalog
        cols_to_keep = [
            name for name in self.simulated_data.dtype.names if "mag" in name
        ]

        # grab only this many objects
        num_lines = 100
        random_lines = self.pick_random_lines(num_lines)
        catalog = random_lines[cols_to_keep]

        # add a gaussian error to each magnitude column and the ID
        final_catalog = self.add_error(catalog)
        final_catalog = self.add_ids(final_catalog)

        # add final piece of info necessary
        # The context is a binary flag. Here we set it to use all filters.
        context = np.full((num_lines), np.sum(2 ** np.arange(len(self.filter_lib))))
        zspec = np.full((num_lines), np.nan)
        string_data = np.full((num_lines), "arbitrary info")
        final_catalog = rfn.append_fields(
            final_catalog, "context", context, usemask=False
        )
        final_catalog = rfn.append_fields(final_catalog, "zspec", zspec, usemask=False)
        final_catalog = rfn.append_fields(
            final_catalog, "string_data", string_data, usemask=False
        )

        self.save_catalog(final_catalog)

        print("Done.")

    def save_catalog(
        self, catalog=None, output_filename: str = "roman_simulated_catalog.in"
    ):
        if catalog is not None:
            np.savetxt(
                output_filename,
                catalog,
                fmt="%s",
                delimiter=" ",
                comments="",
            )

        print(f"Saved simulated input catalog to {output_filename}")

    def add_ids(self, catalog):
        # Add an ID column with running integers starting at 1
        ids = np.arange(1, len(catalog) + 1)
        catalog = rfn.append_fields(catalog, "id", ids, usemask=False)

        # Move the ID column to the first position
        new_dtype = [("id", catalog["id"].dtype)] + [
            (name, catalog[name].dtype) for name in catalog.dtype.names if name != "id"
        ]
        new_catalog = np.empty(catalog.shape, dtype=new_dtype)
        for name in new_catalog.dtype.names:
            new_catalog[name] = catalog[name]

        return new_catalog

    def add_error(self, catalog):
        # add corresponding error column
        new_fields = []
        for col in catalog.dtype.names:
            if "mag" in col:
                noise = np.abs(
                    np.random.normal(loc=0, scale=0.1, size=catalog[col].shape)
                )
                new_fields.append((f"{col}_err", noise))

            # Create a new structured array with the interleaved columns
            new_dtype = []
            for col in catalog.dtype.descr:
                if "mag" in col[0]:
                    new_dtype.append(col)
                    new_dtype.append((f"{col[0]}_err", col[1]))

            new_catalog = np.empty(catalog.shape, dtype=new_dtype)
            for col in catalog.dtype.names:
                new_catalog[col] = catalog[col]
                if "mag" in col:
                    new_catalog[f"{col}_err"] = noise

        return new_catalog

    def create_header(self, catalog_name: str):
        filter_list = (
            self.lephare_config.get("FILTER_LIST")
            .replace(".pb", "")
            .replace("roman/roman_", "")
            .split(",")
        )
        with open(catalog_name, "r") as f:
            colname_list = f.readline().strip().split(" ")
        colnames = [x for x in colname_list if "vector" not in x]
        colvector = [x for x in colname_list if "vector" in x]
        expanded_colvector = [
            x.replace("vector", filter_name)
            for x in colvector
            for filter_name in filter_list
        ]
        colnames.extend(expanded_colvector)

        # ignore comments and drop the age column
        # (SED model used doesn't have that info)
        colnames = [x for x in colnames if "#" not in x]
        colnames = [x for x in colnames if "age" not in x]
        return colnames

    def pick_random_lines(self, num_lines: int):
        """
        Pick random lines from the data array.

        Parameters
        ----------
        num_lines : int
            The number of random lines to pick.

        Returns
        -------
        np.ndarray
            An array containing the randomly picked lines.
        """
        if self.simulated_data is None:
            raise ValueError(
                "Data array is not initialized. Please run create_simulated_input_catalog first."
            )

        total_lines = len(self.simulated_data)
        if num_lines > total_lines:
            raise ValueError(
                f"Requested {num_lines} lines, but only {total_lines} lines are available."
            )

        random_indices = np.random.choice(total_lines, num_lines, replace=False)
        return self.simulated_data[random_indices]

    def process(self):
        self.get_data()
        self.get_filters()
        self.create_simulated_data()
        self.create_simulated_input_catalog()

        print("DONE")


if __name__ == "__main__":

    rcp = SimulatedCatalog()
    rcp.process()

    print("Done.")
