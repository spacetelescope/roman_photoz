=====================
Roman Catalog Process
=====================

This module provides functionality for processing catalog data from the Roman Space Telescope to estimate photometric redshift.

Module API
----------

.. automodule:: roman_photoz.roman_catalog_process
   :members:
   :undoc-members:
   :show-inheritance:

Command-line Interface
---------------------

The module provides a command-line interface with automatically documented arguments:

.. argparse::
   :module: roman_photoz.roman_catalog_process
   :func: _get_parser
   :prog: python -m roman_photoz.roman_catalog_process

Examples
--------

Basic usage::

    from roman_photoz.roman_catalog_process import RomanCatalogProcess

    # Create processor with default configuration
    rcp = RomanCatalogProcess()

    # Process catalog with default parameters
    rcp.process()

Using custom model filename::

    # Specify a custom model filename
    rcp = RomanCatalogProcess(model_filename="custom_model.pkl")
    rcp.process()

Using the command-line interface::

    python -m roman_photoz.roman_catalog_process --model_filename custom_model.pkl

Notes
-----
This module integrates with the RAIL (Redshift Assessment Infrastructure Layers) framework for photometric redshift estimation.
