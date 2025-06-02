# Regression Test Framework

This package provides a regression test framework for the Roman Photoz pipeline, with support for retrieving test data from Artifactory.

## Overview

The regression test framework provides:

1. A pytest marker (`@pytest.mark.bigdata`) to identify tests that require large datasets
2. A fixture (`rtdata`) that manages test data retrieval and comparison
3. Integration with Artifactory for storing and retrieving test datasets
4. Utilities for comparing output files with truth files
5. File caching to improve test performance

## Setup for Development

### 1. Test Data Location

The framework looks for test data in a location specified by the `TEST_BIGDATA` environment variable. For development, you can set this up locally:

```bash
# Create a local directory for test data
mkdir -p $HOME/REGTEST_FILES

# Set the environment variable (add to your .bashrc/.zshrc for persistence)
export TEST_BIGDATA=$HOME/REGTEST_FILES
```

### 2. Directory Structure

For development, create this directory structure:

```
$HOME/REGTEST_FILES/
└── roman-pipeline/
    └── dev/
        ├── test_data/
        │   └── example_input.fits  # Input files for tests
        └── truth/
            └── test_data/
                └── example_truth.fits  # Truth files for comparison
```

### 3. Sample Test Data

For development purposes, you can create sample test files:

```bash
# Create directories
mkdir -p $HOME/REGTEST_FILES/roman-pipeline/dev/test_data
mkdir -p $HOME/REGTEST_FILES/roman-pipeline/dev/truth/test_data

# Create sample FITS files for testing (using Python)
python -c "
import numpy as np
from astropy.io import fits

# Create sample input data
data = np.random.random((10, 10))
hdu = fits.PrimaryHDU(data)
hdu.writeto('$HOME/REGTEST_FILES/roman-pipeline/dev/test_data/example_input.fits', overwrite=True)

# Create slightly different truth data
data[5,5] += 0.1  # Make a small change
hdu = fits.PrimaryHDU(data)
hdu.writeto('$HOME/REGTEST_FILES/roman-pipeline/dev/truth/test_data/example_truth.fits', overwrite=True)
"
```

## Writing Tests

### Basic Example

```python
import pytest

@pytest.mark.bigdata
def test_my_feature(rtdata):
    # Get input data from Artifactory
    rtdata.get_data("test_data/example_input.fits")

    # Process the input data using your pipeline
    result = run_my_pipeline(rtdata.input)
    output_file = "processed_output.fits"
    result.write_to(output_file)
    rtdata.output = output_file

    # Get truth data for comparison
    rtdata.get_truth("truth/test_data/example_truth.fits")

    # Compare output with truth
    assert rtdata.compare_files(rtdata.output, rtdata.truth)
```

### Important Notes

1. Always use paths relative to the repository root (not including inputs_root/env)
2. The framework will prepend the repository and environment paths
3. Files are automatically cached after first retrieval
4. Use `rtdata_module` fixture when multiple tests need the same data

## Running Tests

Tests with the `@pytest.mark.bigdata` decorator are skipped by default. To run them:

```bash
# Skip bigdata tests (fast, for regular development)
pytest roman_photoz/regtest/test_example.py -v

# Run including bigdata tests
pytest roman_photoz/regtest/test_example.py -v --bigdata

# Run specific test with bigdata
pytest --bigdata path/to/test_file.py::test_my_feature
```

## Configuration

The framework can be configured in your pytest.ini file:

```ini
[pytest]
# Configuration for artifactory repositories
inputs_root = roman-pipeline
results_root = roman-pipeline-results/regression-tests/runs/
```

## Production/CI Environment

For production or continuous integration:

1. Set `TEST_BIGDATA` to the artifactory URL
2. Configure artifactory access credentials:
   - For Jenkins, use an API key in `/eng/ssb2/keys/svc_rodata.key`
   - For local use, set the `API_KEY_FILE` environment variable

## Framework Components

- `regtestdata.py`: Core data management class with caching and comparison functions
- `conftest.py`: Pytest configuration and fixtures
- `test_example.py`: Usage examples and tests

## API Reference

### RegtestData

The `rtdata` fixture provides an instance of `RegtestData` with these key methods:

- `get_data(path)`: Retrieve input data from Artifactory
- `get_truth(path)`: Retrieve truth data from Artifactory
- `compare_files(output, truth)`: Compare output file with truth file

Properties:
- `input`: Local path to input file
- `output`: Local path to output file
- `truth`: Local path to truth file
- `input_remote`: Remote path in Artifactory to input file
- `truth_remote`: Remote path in Artifactory to truth file

Cache Control:
- `cache_enabled`: Enable/disable caching
- `clear_cache()`: Clear the cache
- `cache_info()`: Get cache statistics

## Common Issues

1. "File not found" errors usually indicate:
   - `TEST_BIGDATA` environment variable isn't set correctly
   - The test is using incorrect path formats
   - The data files don't exist in the expected location

2. Skip markers: Tests with `@pytest.mark.bigdata` decorator will be skipped unless you use `--bigdata` option

3. Cache issues: Clear the cache using `rtdata.clear_cache()` if you suspect outdated files

## Differences from romancal

This implementation is based on romancal's regression test framework but includes several improvements:

1. Enhanced error messages for file comparison
2. File caching with control functions
3. Better handling of binary vs text file differences
4. More robust pytest configuration
5. Comprehensive documentation and examples

## Extending

To add support for comparing specific file formats, add methods to the `RegtestData` class.
