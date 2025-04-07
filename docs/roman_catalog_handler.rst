=====================
Roman Catalog Handler
=====================

The ``roman_catalog_handler`` module provides functionality for handling catalog data from the Roman Space Telescope.

Module API
----------

.. automodule:: roman_catalog_handler
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------
The following example demonstrates how to use the `RomanCatalogHandler` class to read and process a catalog file.

.. code-block:: python

     import os
     from pathlib import Path
     from roman_catalog_handler import RomanCatalogHandler

     # Ensure the TEST_BIGDATA environment variable is set
     test_bigdata = os.getenv("TEST_BIGDATA")
     if test_bigdata is None:
          raise ValueError("Environment variable TEST_BIGDATA is not set")
     reg_test_data = Path(test_bigdata)

     # Specify the catalog file
     test_cat = reg_test_data / "r0000101001001001001_0001_wfi01_cat.asdf"

     # Create an instance of RomanCatalogHandler
     catalog_handler = RomanCatalogHandler(test_cat.as_posix())

     # Process the catalog
     formatted_catalog = catalog_handler.process()

     print("Catalog processing complete.")
