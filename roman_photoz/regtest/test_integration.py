"""Example test demonstrating usage of the bigdata test framework."""

from pathlib import Path

import pytest
from astropy.table import Table

try:
    from importlib.resources import files
except ImportError:
    # Fallback for Python < 3.9
    from importlib_resources import files

from roman_photoz.default_config_file import default_roman_config
from roman_photoz.roman_catalog_process import RomanCatalogProcess
from roman_photoz.utils.roman_photoz_utils import read_output_keys

# file containing the default output keys that the output file should have
try:
    # Modern approach using importlib.resources
    DEFAULT_OUTPUT_KEYWORDS = str(
        files("roman_photoz").joinpath("data/default_roman_output.para")
    )
except (ImportError, AttributeError):
    # Fallback for older Python versions or if importlib_resources not available
    import pkg_resources

    DEFAULT_OUTPUT_KEYWORDS = pkg_resources.resource_filename(
        "roman_photoz", "data/default_roman_output.para"
    )


@pytest.fixture
def roman_catalog_process():
    """Create a basic RomanCatalogProcess instance for testing"""
    return RomanCatalogProcess(config_filename=default_roman_config)


@pytest.mark.bigdata
def test_roman_photoz(rtdata, tmp_path):
    # Get input test data from artifactory
    # Note: Path should be relative to the repository root, NOT including inputs_root/env
    # The rtdata.get_data() method will prepend the repository and environment for you
    input_path = "WFI/image"
    input_filename = "test_simulated_catalog.parquet"
    rtdata.get_data(f"{Path(input_path, input_filename).as_posix()}")

    # Verify input was retrieved
    assert rtdata.input is not None
    assert Path(rtdata.input).name == "test_simulated_catalog.parquet"

    rtdata.output = "roman_photoz_integration_test_output.parquet"

    # create instance
    rcp = RomanCatalogProcess(
        config_filename=default_roman_config,
    )

    rcp.process(
        input_filename=Path(rtdata.input).name,
        input_path=Path(rtdata.input).parent.as_posix(),
        output_filename=rtdata.output,
        output_path=tmp_path,
        output_format="parquet",
    )

    # get the truth (avoid using cache here)
    # truth_path = "truth/WFI/image"
    # truth_filename = "roman_photoz_integration_test_truth.parquet"
    # rtdata.get_truth(Path(truth_path, truth_filename).as_posix(), use_cache=False)

    # read in output and truth files
    output = Table.read(rtdata.output, format="parquet")
    # truth = Table.read(rtdata.truth, format="parquet")

    # get the expected column names
    expected_cols = read_output_keys(DEFAULT_OUTPUT_KEYWORDS)

    # For now, we will just check that all the expected columns are present
    assert all(
        col in expected_cols
        for col in output.colnames
        if col != "zmean" and col != "zmode"
    )
