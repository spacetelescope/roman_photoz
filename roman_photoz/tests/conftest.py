"""Pytest configuration for integration tests."""

import sys
import os
import pytest
from pathlib import Path

# Add the regtest directory to the path if needed
regtest_path = Path(__file__).parent.parent / "regtest"
if str(regtest_path) not in sys.path:
    sys.path.insert(0, str(regtest_path))

# Import the regtest fixtures
from roman_photoz.regtest.regtestdata import RegtestData

# Set up Artifactory environment
@pytest.fixture(scope="session")
def envopt():
    """Fixture to provide the 'env' artifactory option."""
    return "dev"


@pytest.fixture(scope="session")
def artifactory_repos():
    """Provides Artifactory inputs_root and results_root"""
    inputs_root = "roman-pipeline"
    results_root = "roman-pipeline-results/regression-tests/runs/"
    return inputs_root, results_root


def _rtdata_fixture_implementation(artifactory_repos, envopt, request):
    """Provides the RegtestData class"""
    inputs_root, results_root = artifactory_repos
    rtdata = RegtestData(env=envopt, inputs_root=inputs_root, results_root=results_root)
    yield rtdata


@pytest.fixture(scope="function")
def rtdata(artifactory_repos, envopt, request, tmpdir):
    """Fixture providing the regression test data access object."""
    # Change to a temporary directory
    old_dir = os.getcwd()
    tmpdir.chdir()
    
    # Get rtdata instance
    yield from _rtdata_fixture_implementation(artifactory_repos, envopt, request)
    
    # Change back to original directory
    os.chdir(old_dir)


@pytest.fixture(scope="module")
def rtdata_module(artifactory_repos, envopt, request, tmpdir_factory):
    """Module-scoped version of the rtdata fixture."""
    module_tmpdir = tmpdir_factory.mktemp("module")
    old_dir = os.getcwd()
    module_tmpdir.chdir()
    
    yield from _rtdata_fixture_implementation(artifactory_repos, envopt, request)
    
    os.chdir(old_dir)


# Register the bigdata marker
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "bigdata: tests that require access to large data sets"
    )


# Add --bigdata option if not already added by another plugin
def pytest_addoption(parser):
    """Add pytest command line options."""
    # Check if --bigdata option already exists before adding it
    try:
        parser.getgroup("bigdata")
    except ValueError:
        try:
            parser.addoption(
                "--bigdata",
                action="store_true",
                help="run tests that require access to big data repos",
            )
        except ValueError:
            # Option might exist but not as a group
            pass


# Skip bigdata tests unless --bigdata is specified
def pytest_runtest_setup(item):
    """Skip tests that require bigdata if not explicitly enabled."""
    bigdata_marker = item.get_closest_marker("bigdata")
    
    if bigdata_marker:
        try:
            option = item.config.getoption("--bigdata")
        except ValueError:
            # If the option doesn't exist, treat it as False
            option = False
        
        if not option:
            pytest.skip("need --bigdata option to run")

