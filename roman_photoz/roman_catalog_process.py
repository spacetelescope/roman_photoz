### COSMOS example with lephare ###
import argparse
import json
import os
import pickle
from collections import OrderedDict
from importlib.resources import files
from pathlib import Path
from typing import Optional, Union

import astropy.table
import lephare as lp
import numpy as np
from asdf import AsdfFile
from astropy.table import Table
from roman_datamodels import datamodels

from roman_photoz.default_config_file import default_roman_config
from roman_photoz.logger import logger
from roman_photoz.roman_catalog_handler import RomanCatalogHandler
from roman_photoz.utils import read_output_keys

LEPHAREDIR = Path(os.environ.get("LEPHAREDIR", lp.LEPHAREDIR))
LEPHAREWORK = os.environ.get("LEPHAREWORK", (LEPHAREDIR / "work").as_posix())
INFORMER_STAGE_NAME = "inform_roman"

# default paths and filenames
DEFAULT_OUTPUT_KEYWORDS = str(
    files(__package__ + ".data") / "default_roman_output.para"
)


def get_informer_run_dir(lepharework: Optional[str] = None) -> str:
    """
    Return the LePhare informer run directory for the current work tree.

    RAIL's LephareInformer writes intermediate libraries under
    ``dirname(LEPHAREWORK)/inform_roman``. Estimation must use that same
    local path rather than any absolute ``run_dir`` baked into a relocated
    model pickle.
    """
    work_dir = lepharework or os.environ.get("LEPHAREWORK", LEPHAREWORK)
    return str(Path(work_dir).resolve().parent / INFORMER_STAGE_NAME)


def _make_model_portable(model: dict, run_dir: str) -> dict:
    """
    Rewrite absolute paths stored in a LePhare model so it can be relocated.

    Parameters
    ----------
    model : dict
        Model dictionary loaded from ``roman_model.pkl``.
    run_dir : str
        Local informer run directory that should replace any baked-in path.
        ``FILTER_REP`` is rewritten to ``$run_dir/filt`` because setup keeps
        the compiled filter files there (and trims ``LEPHAREDIR/filt`` away).

    Returns
    -------
    dict
        Updated model dictionary.
    """
    portable = dict(model)
    portable["run_dir"] = run_dir

    lephare_config = portable.get("lephare_config")
    if isinstance(lephare_config, dict):
        portable_config = dict(lephare_config)
        portable_config["FILTER_REP"] = str(Path(run_dir) / "filt")
        # Always use the package PARA_OUT so relocated installs do not depend
        # on the absolute source path captured during --setup.
        portable_config["PARA_OUT"] = DEFAULT_OUTPUT_KEYWORDS
        portable["lephare_config"] = portable_config

    return portable


def load_portable_informer_model(
    model_path: str,
    run_dir: Optional[str] = None,
) -> dict:
    """
    Load an informer model pickle and rewrite non-portable absolute paths.

    Purpose: allow prebuilt ``roman_model.pkl`` assets to be copied to a new
    machine/directory (for example AWS) without retaining the original host
    paths for ``run_dir``, ``FILTER_REP``, or ``PARA_OUT``.
    """
    with open(model_path, "rb") as handle:
        model = pickle.load(handle)

    if not isinstance(model, dict):
        raise TypeError(
            f"Expected informer model at {model_path} to be a dict, got {type(model)!r}"
        )

    resolved_run_dir = run_dir or get_informer_run_dir()
    return _make_model_portable(model, run_dir=resolved_run_dir)


class RomanCatalogProcess:
    """
    A class to process a Roman Telescope multiband catalog data using rail and lephare.

    Attributes
    ----------
    data : dict
        Dictionary to store the processed data.
    flux_cols : list
        List of flux column names.
    flux_err_cols : list
        List of flux error column names.
    inform_stage : RailStage
        Informer stage for creating the library of SEDs.
    estimated : RailStage
        Estimator stage for finding the best fits from the library.
    model_filename : str
        Name of the pickle model file to use.
    """

    def __init__(
        self,
        config_filename: Union[dict, str] = "",
        model_filename: str = "roman_model.pkl",
    ):
        """
        Initialize the RomanCatalogProcess instance.

        Parameters
        ----------
        config_filename : Union[dict, str], optional
            Path to the configuration file or a configuration dictionary.
        model_filename : str, optional
            Name of the pickle model file (default: "roman_model.pkl").
        """
        self.data: dict = OrderedDict()
        # set configuration file (roman will have its own)
        self._set_config_file(config_filename)
        # set model filename
        self.model_filename = model_filename
        # set attributes used for determining the redshift
        self.flux_cols: list = []
        self.flux_err_cols: list = []
        self.inform_stage = None
        self.estimated = None
        self.default_roman_output_keys = read_output_keys(DEFAULT_OUTPUT_KEYWORDS)

        self.input_filename = None
        self.output_filename = None
        self.output_format = None

    def _set_config_file(self, config_filename: Union[dict, str] = ""):
        """
        Set the configuration file.

        Parameters
        ----------
        config_filename : Union[dict, str], optional
            Path to the configuration file in JSON format or a configuration dictionary.
        """
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

    def _get_data(
        self,
        input_filename,
        fit_colname: str = "segment_{}_flux",
        fit_err_colname: str = "segment_{}_flux_err",
    ) -> Table:
        """
        Fetch the data from the input file.

        Parameters
        ----------
        input_filename : str, optional
            Name of the input file.

        Returns
        -------
        Table
            The catalog data.
        """
        # full qualified path to the catalog file
        logger.info(f"Reading catalog from {input_filename}")

        # read in catalog data
        handler = RomanCatalogHandler(
            input_filename, fit_colname=fit_colname, fit_err_colname=fit_err_colname
        )

        # Populate flux_cols and flux_err_cols from the handler's filter names
        self.flux_cols = [
            fit_colname.format(filter_id) for filter_id in handler.filter_names
        ]
        self.flux_err_cols = [
            fit_err_colname.format(filter_id) for filter_id in handler.filter_names
        ]

        # Convert numpy structured array to astropy Table
        return Table(handler.catalog)

    def _format_lephare_input(self) -> Table:
        """
        Format the catalog data into the table structure required by LePhare.
        """
        ng = len(self.data)
        input_table = Table()
        if "label" in self.data.colnames:
            input_table["id"] = [str(x) for x in self.data["label"]]
        elif "id" in self.data.colnames:
            input_table["id"] = [str(x) for x in self.data["id"]]
        else:
            input_table["id"] = [str(x) for x in range(ng)]

        context = np.full(ng, 0)
        for n in range(len(self.flux_cols)):
            col = self.flux_cols[n]
            err_col = self.flux_err_cols[n]
            flux_val = np.array(self.data[col], dtype=float)
            err_val = np.array(self.data[err_col], dtype=float)
            input_table[col] = flux_val
            input_table[err_col] = err_val
            mask = (flux_val > 0) & (~np.isnan(flux_val))
            mask &= (err_val > 0) & (~np.isnan(err_val))
            context += mask.astype(int) * (2**n)

        if "context" in self.data.colnames:
            input_table["context"] = self.data["context"]
        else:
            input_table["context"] = context

        if "redshift" in self.data.colnames:
            input_table["zspec"] = np.array(self.data["redshift"], dtype=float)
        elif "redshift_true" in self.data.colnames:
            input_table["zspec"] = np.array(self.data["redshift_true"], dtype=float)
        else:
            input_table["zspec"] = np.full(ng, -99.0, dtype=float)

        input_table["string_data"] = [" "] * ng
        return input_table

    def _create_informer_stage(self):
        """
        Create the informer stage to generate the library of SEDs with various parameters.
        """
        star_overrides = {}
        gal_overrides = {
            "MOD_EXTINC": "18,26,26,33,26,33,26,33",
            "EXTINC_LAW": "SMC_prevot.dat,SB_calzetti.dat,SB_calzetti_bump1.dat,SB_calzetti_bump2.dat",
            "EM_LINES": "EMP_UV",
            "EM_DISPERSION": "0.5,1.,1.5",
        }
        qso_overrides = {
            "MOD_EXTINC": "0,1000",
            "EB_V": "0.,0.1,0.2,0.3",
            "EXTINC_LAW": "SB_calzetti.dat",
        }

        lp.prepare(
            self.config,
            star_config=star_overrides,
            gal_config=gal_overrides,
            qso_config=qso_overrides,
        )

        Path(self.informer_model_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.informer_model_path, "wb") as f:
            pickle.dump({"config": self.config}, f)

    def _create_estimator_stage(self):
        """
        Create the estimator stage to find the best fits from the library.
        """
        input_table = self._format_lephare_input()
        output, _ = lp.process(self.config, input_table, write_outputs=False)
        self.estimated = output

    def _save_results(
        self,
    ):
        """
        Save the results to the specified output file.

        Raises
        ------
        ValueError
            If there are no results to save.
        """

        if self.output_filename is None:
            logger.info("No output filename provided. Updating input file in place.")
            self._update_input(self.input_filename, save_results=True)
            self.output_filename = self.input_filename
        elif self.output_filename is not None and self.output_format.lower() in [
            "parquet",
            "asdf",
        ]:
            if self.estimated is not None:
                self._update_input(self.input_filename, save_results=False)
            else:
                logger.error("No results to save")
                raise ValueError("No results to save.")

            if self.output_format.lower() == "parquet":
                import pyarrow.parquet as pq

                pq.write_table(self.results, self.output_filename)
            elif self.output_format.lower() == "asdf":
                tree = {"roman_photoz_results": self.results.to_pydict()}
                with AsdfFile(tree) as af:
                    af.write_to(self.output_filename)
        else:
            logger.error(
                f"Unsupported output format: {self.output_format}. Supported formats are 'parquet' and 'asdf'."
            )
            raise ValueError(
                f"Unsupported output format: {self.output_format}. Supported formats are 'parquet' and 'asdf'."
            )
        logger.info(f"Results saved to {self.output_filename}.")

    def _update_input(self, input_filename, save_results=False):
        # TODO: this can be done with the Table class
        # directly; no need for pyarrow
        import pyarrow as pa
        import pyarrow.parquet as pq

        tab = pq.read_table(input_filename)
        tab_astro = Table.read(input_filename)
        meta = dict(tab.schema.metadata)

        # Create a MultibandSourceCatalogModel instance to access RAD schema definitions
        catalog_model = datamodels.MultibandSourceCatalogModel()

        namedict = {
            "photoz": "Z_BEST",
            "photoz_high68": "Z_BEST68_HIGH",
            "photoz_high90": "Z_BEST90_HIGH",
            "photoz_high99": "Z_BEST99_HIGH",
            "photoz_low68": "Z_BEST68_LOW",
            "photoz_low90": "Z_BEST90_LOW",
            "photoz_low99": "Z_BEST99_LOW",
            "photoz_gof": "CHI_BEST",
            "photoz_sed": "MOD_BEST",
        }
        for newname, oldname in namedict.items():
            # Get column definition from RAD schema
            col_def = catalog_model.get_column_definition(newname)

            # get unit and description from the column definition, if available
            # (since all the photoz columns are unitless, we will just set unit to None for now)
            description = col_def.get("description", "")

            # Create PyArrow field with metadata
            arr = pa.array(self.estimated[oldname])
            field = pa.field(newname, arr.type, metadata={"description": description})

            if newname not in tab.column_names:
                tab = tab.append_column(field, arr)
            else:
                tab = tab.set_column(tab.schema.get_field_index(newname), field, arr)

            # Also add to Astropy table with metadata
            tab_astro[newname] = self.estimated[oldname]
            tab_astro[newname].info.description = description

            logger.info(
                f"Applied RAD schema metadata to column '{newname}': "
                f"description={description}"
            )

        extra_astropy_metadata = astropy.table.meta.get_yaml_from_table(tab_astro)
        meta[b"table_meta_yaml"] = "\n".join(extra_astropy_metadata).encode("utf-8")
        self.results = tab.replace_schema_metadata(meta)
        if save_results:
            pq.write_table(self.results, self.input_filename)

    def process(
        self,
        input_filename,
        output_filename: Optional[str] = None,
        output_format: str = "parquet",
        fit_colname: str = "segment_{}_flux",
        fit_err_colname: str = "segment_{}_flux_err",
    ):
        """
        Process the Roman catalog data.

        Parameters
        ----------
        input_filename : str
            Name of the input file.
        output_filename : str, optional
            Name of the output file.
            If none is provided (default), the input file will be updated in place.
        output_format : str, optional
            Format to save the results.
            Supported formats are "parquet" (default) and "asdf."
        flux_type : str, optional
            The type of flux to use for fitting.
            Options are "psf" (default), "kron", "segment", or "aperture."
        """

        self.input_filename = input_filename
        if output_filename is not None:
            self.output_filename = output_filename
            self.output_format = output_format

        self.data = self._get_data(
            input_filename=self.input_filename,
            fit_colname=fit_colname,
            fit_err_colname=fit_err_colname,
        )

        if not self.informer_model_exists:
            print(
                "Warning: The informer model file does not exist. Creating a new one..."
            )
            self._create_informer_stage()
        self._create_estimator_stage()

        self._save_results()

    @property
    def informer_model_exists(self):
        """
        Check if the informer model file exists.

        Returns
        -------
        bool
            True if the model file exists, False otherwise.
        """
        if os.path.exists(self.informer_model_path):
            print(
                f"The informer model file {self.informer_model_path} exists. Using it..."
            )
            return True
        return False

    @property
    def informer_run_dir(self):
        """
        Local LePhare informer run directory used for estimation.

        This is always derived from the current ``LEPHAREWORK`` location so a
        relocated model pickle cannot force estimation back onto the original
        absolute host path.
        """
        return get_informer_run_dir()

    @property
    def informer_model_path(self):
        """
        Get the path to the informer model file used.

        ``INFORMER_MODEL_PATH`` may be either the model file itself or the
        directory containing it. When unset, ``LEPHAREWORK`` is used as the
        model directory.

        Returns
        -------
        str
            The path to the informer model file.
        """
        informer_path = os.environ.get(
            "INFORMER_MODEL_PATH", os.environ.get("LEPHAREWORK", "")
        )
        path = Path(informer_path)
        if path.suffix == ".pkl" or path.name == self.model_filename:
            return path.as_posix()
        return (path / self.model_filename).as_posix()


def _get_parser():
    """
    Main function to process Roman catalog data using command-line arguments.
    This function parses command-line arguments for input/output files, configuration,
    model files, and processing options, then runs the RomanCatalogProcess accordingly.
    """

    parser = argparse.ArgumentParser(description="Process Roman catalog data.")
    parser.add_argument(
        "--setup",
        action="store_true",
        help=(
            "Bootstrap the LePhare data/model needed to run roman-photoz: "
            "download the LePhare auxiliary data, create a simulated catalog, "
            "build the informer model, trim LEPHAREDIR to estimator "
            "essentials, and verify the required artifacts are present. "
            "All other arguments below are ignored when --setup is used."
        ),
    )
    parser.add_argument(
        "--nobj",
        type=int,
        default=1000,
        help="Number of objects in the simulated catalog used by --setup (default: 1000).",
    )
    parser.add_argument(
        "--simulated-catalog-filename",
        type=str,
        default="roman_photoz_simulated_catalog.parquet",
        help=(
            "Simulated catalog filename used by --setup "
            "(default: roman_photoz_simulated_catalog.parquet)."
        ),
    )
    parser.add_argument(
        "--config-filename",
        type=str,
        default="",
        help="Path to the configuration file (default: use default Roman config).",
        required=False,
    )
    parser.add_argument(
        "--model-filename",
        type=str,
        default="roman_model.pkl",
        help="Name of the pickle model file (default: roman_model.pkl).",
        required=False,
    )
    parser.add_argument(
        "--input-filename",
        type=str,
        help="Input catalog filename",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        default="parquet",
        help='Format in which to save the results. Supported formats are "parquet" (default) and "asdf".',
    )
    parser.add_argument(
        "--output-filename",
        type=str,
        default=None,
        help="Output filename (default: None).  If None, update input filename in place.",
    )
    parser.add_argument(
        "--fit-colname",
        type=str,
        default="segment_{}_flux",
        help="Template for the column name to be used for fitting fluxes/mags. It should contain a pair of curly braces as a placeholder for the filter ID, e.g., 'segment_{}_flux'.",
    )
    parser.add_argument(
        "--fit-err-colname",
        type=str,
        default="segment_{}_flux_err",
        help="Template for the column name containing the error corresponding to fit_colname. It should contain a pair of curly braces as a placeholder for the filter ID, e.g., 'segment_{}_flux_err'.",
    )
    return parser


def run_setup(nobj: int = 1000, simulated_catalog_filename: str = "roman_photoz_simulated_catalog.parquet"):
    """
    Bootstrap the LePhare data/model needed to run roman-photoz.

    Uses the ``LEPHAREDIR`` and ``LEPHAREWORK`` environment variables to
    determine where to store the LePhare data and work directories. If they
    are not set, ``lephare`` falls back to its own default cache directories
    under ``~/Library/Caches/lephare`` (or the platform equivalent) and
    prints a notice to that effect; set these variables explicitly beforehand
    if you want to control where the LePhare data/model files are stored.
    It then:

    1. Downloads the LePhare auxiliary data required by the Roman config.
    2. Creates a simulated catalog and the Roman filter files (kept afterward
       so it can be reused directly as an input catalog; it will already
       contain the redshift-estimate columns added by step 3 below).
    3. Builds the informer model (removing any stale model/run directory first).
    4. Trims ``LEPHAREDIR`` down to the files needed by the estimator.
    5. Verifies that the required artifacts are present.

    Parameters
    ----------
    nobj : int, optional
        Number of objects in the simulated catalog (default: 1000).
    simulated_catalog_filename : str, optional
        Filename for the simulated catalog (default: roman_photoz_simulated_catalog.parquet).

    Raises
    ------
    RuntimeError
        If the required artifacts are missing after setup completes.
    """
    import shutil

    from lephare.data_retrieval import get_auxiliary_data

    from roman_photoz.create_simulated_catalog import SimulatedCatalog

    lepharedir = os.environ.get("LEPHAREDIR", str(LEPHAREDIR))
    lepharework = os.environ.get("LEPHAREWORK", LEPHAREWORK)

    os.makedirs(lepharedir, exist_ok=True)
    os.makedirs(lepharework, exist_ok=True)

    logger.info("Downloading LePhare auxiliary data...")
    get_auxiliary_data(
        lephare_dir=lepharedir,
        keymap=default_roman_config,
        additional_files=[
            "examples/COSMOS_MOD.list",  # needed for the simulated catalog
        ],
    )
    logger.info("Auxiliary data download complete.")

    logger.info("Creating simulated catalog and Roman filter files...")
    SimulatedCatalog(nobj=nobj).process(
        output_path=lepharework,
        output_filename=simulated_catalog_filename,
    )
    catalog_path = os.path.join(lepharework, simulated_catalog_filename)
    logger.info(f"Simulated catalog: {catalog_path}")

    # Remove stale informer artifacts to ensure a clean build. The model
    # pickle stores an absolute run_dir path from the original informer run;
    # if it's stale, the estimator will look in the wrong place unless the
    # runtime path rewrite in load_portable_informer_model() is used.
    model_pickle = os.path.join(lepharework, "roman_model.pkl")
    if os.path.exists(model_pickle):
        logger.info(f"Removing stale model pickle: {model_pickle}")
        os.remove(model_pickle)
    # LephareInformer creates its run directory at $LEPHAREWORK/../inform_roman
    informer_run_dir = get_informer_run_dir(lepharework)
    if os.path.isdir(informer_run_dir):
        logger.info(f"Removing stale informer run directory: {informer_run_dir}")
        shutil.rmtree(informer_run_dir)

    logger.info("Running informer + estimator stage...")
    RomanCatalogProcess().process(input_filename=catalog_path)
    logger.info(f"Model written to: {model_pickle}")

    # Rewrite absolute host paths in the published model so the three-tree
    # package (lephare_data, lephare_work, inform_roman) can be relocated.
    if os.path.exists(model_pickle):
        portable_model = load_portable_informer_model(
            model_pickle,
            run_dir=informer_run_dir,
        )
        with open(model_pickle, "wb") as handle:
            pickle.dump(portable_model, handle)
        logger.info(
            "Rewrote absolute paths in model pickle for relocatable packaging "
            f"(run_dir={informer_run_dir})."
        )

    logger.info("Removing intermediate files...")
    log_path = os.path.join(lepharework, "roman_photoz.log")
    if os.path.exists(log_path):
        os.remove(log_path)

    logger.info("Cleaning up LEPHAREDIR (keeping only opa/, ext/, vega/, alloutputkeys.txt)...")
    keep = {"opa", "ext", "vega", "alloutputkeys.txt"}
    for entry in os.listdir(lepharedir):
        if entry in keep:
            logger.info(f"    Keeping: {entry}")
            continue
        logger.info(f"    Removing: {entry}")
        entry_path = os.path.join(lepharedir, entry)
        if os.path.isdir(entry_path):
            shutil.rmtree(entry_path)
        else:
            os.remove(entry_path)

    logger.info("Verifying required assets...")
    missing = [
        path
        for path in (
            os.path.join(lepharedir, "opa"),
            os.path.join(lepharedir, "ext"),
            os.path.join(lepharedir, "alloutputkeys.txt"),
            model_pickle,
            informer_run_dir,
            os.path.join(informer_run_dir, "lib_mag"),
        )
        if not os.path.exists(path)
    ]
    if missing:
        missing_list = "\n".join(f"  - {path}" for path in missing)
        raise RuntimeError(
            f"Bootstrap verification failed. Missing artifacts:\n{missing_list}"
        )
    logger.info("All required artifacts are present.")

    logger.info("Setup complete.")
    logger.info(f"Model:       {model_pickle}")
    logger.info(f"Informer:    {informer_run_dir}")
    logger.info(f"Catalog:     {catalog_path} (kept, reusable as an input catalog)")
    logger.info(f"LEPHAREDIR:  {lepharedir} (trimmed to estimator essentials)")
    logger.info(f"LEPHAREWORK: {lepharework}")



def main(argv=None):
    """
    Main function to process Roman catalog data.
    """

    parser = _get_parser()
    args = parser.parse_args(argv)

    if args.setup:
        run_setup(
            nobj=args.nobj,
            simulated_catalog_filename=args.simulated_catalog_filename,
        )
        return

    logger.info("Starting Roman catalog processing")
    rcp = RomanCatalogProcess(
        config_filename=args.config_filename, model_filename=args.model_filename
    )
    rcp.process(
        input_filename=args.input_filename,
        output_filename=args.output_filename,
        output_format=args.output_format,
        fit_colname=args.fit_colname,
        fit_err_colname=args.fit_err_colname,
    )
    logger.info("Roman catalog processing completed")
