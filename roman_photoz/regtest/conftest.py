"""Pytest configuration and fixtures for regression tests."""

import os
from datetime import datetime

import pytest

from roman_photoz.regtest.regtestdata import RegtestData

TODAYS_DATE = datetime.now().strftime("%Y-%m-%d")


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "bigdata: tests that require access to large data sets"
    )


def pytest_addoption(parser):
    """Add pytest command line options."""
    # Check if --bigdata option already exists before adding it
    # This prevents conflicts with other packages that might define the same option
    try:
        parser.getgroup("bigdata")
    except ValueError:
        # Option doesn't exist, safe to add
        try:
            parser.addoption(
                "--bigdata",
                action="store_true",
                help="run tests that require access to big data repos",
            )
        except ValueError:
            # Option might exist but not as a group
            pass

    # Add options for configuring artifactory access
    parser.addini(
        "inputs_root",
        help="artifactory folder for input files",
        default="roman-pipeline",
    )
    parser.addini(
        "results_root",
        help="artifactory folder for result/truth files",
        default="roman-pipeline-results/regression-tests/runs/",
    )


@pytest.fixture(scope="session")
def envopt(pytestconfig):
    """Fixture to provide the 'env' artifactory option."""
    env = pytestconfig.getoption("env", default="dev")
    return env


@pytest.fixture(scope="session")
def artifactory_repos(pytestconfig):
    """Provides Artifactory inputs_root and results_root"""
    inputs_root = pytestconfig.getini("inputs_root")
    if isinstance(inputs_root, (list, tuple)) and inputs_root:
        inputs_root = inputs_root[0]
    elif not inputs_root:
        inputs_root = "roman-pipeline"

    results_root = pytestconfig.getini("results_root")
    if isinstance(results_root, (list, tuple)) and results_root:
        results_root = results_root[0]
    elif not results_root:
        results_root = "roman-pipeline-results/regression-tests/runs/"

    return inputs_root, results_root


def _rtdata_fixture_implementation(artifactory_repos, envopt, request):
    """Provides the RegtestData class"""
    inputs_root, results_root = artifactory_repos
    rtdata = RegtestData(env=envopt, inputs_root=inputs_root, results_root=results_root)

    yield rtdata


@pytest.fixture(scope="function")
def rtdata(artifactory_repos, envopt, request, tmpdir):
    """Fixture providing the regression test data access object.

    This fixture provides an object to help manage test data files, including
    both input files for tests and truth files for comparison.
    """
    # Change to a temporary directory to avoid polluting the local workspace
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
