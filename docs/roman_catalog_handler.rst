=====================
Roman Catalog Handler
=====================

The ``roman_catalog_handler`` module provides functionality for handling
catalog data from the Roman Space Telescope.

Module API
----------

.. automodule:: roman_photoz.roman_catalog_handler
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

.. code-block:: python

   import os
   from pathlib import Path
   from roman_photoz.roman_catalog_handler import RomanCatalogHandler

   test_bigdata = os.getenv("TEST_BIGDATA")
   if test_bigdata is None:
       raise ValueError("Environment variable TEST_BIGDATA is not set")
   reg_test_data = Path(test_bigdata)

   test_cat = reg_test_data / "r0000101001001001001_0001_wfi01_cat.parquet"
   catalog_handler = RomanCatalogHandler(test_cat.as_posix())
   formatted_catalog = catalog_handler.process()
   print("Catalog processing complete.")
