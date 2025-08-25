=====================
Roman Catalog Handler
=====================

This module is responsible for reading, processing, and formatting source
catalogs from the Roman Space Telescope. Its main purposes are:

- **Reading Catalogs:** It supports reading catalogs in ASDF and Parquet
  formats;

- **Formatting Data:** It reformats the Roman catalog to ensure required
  columns (such as fluxes, errors, labels, and redshifts) are present and
  properly named for downstream processing;

- **Unit Conversion:** It handles unit conversions as required by LePhare;

- **Handling Missing Data:** If expected columns are missing, it fills them
  with default values so the catalog remains usable;

Module API
----------

.. automodule:: roman_photoz.roman_catalog_handler
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

.. code-block:: python

   from roman_photoz.roman_catalog_handler import RomanCatalogHandler

   catalog_filename = "roman_catalog.parquet"

   # creating an instance of RomanCatalogHandler
   handler = RomanCatalogHandler()
   # read and format the catalog
   formatted_catalog = handler.process(catalog_handler)


Alternatively, you can read and format the catalog directly during instantiation:

.. code-block:: python

   from roman_photoz.roman_catalog_handler import RomanCatalogHandler

   catalog_filename = "roman_catalog.parquet"

   # read, format, and store the catalog as an object attribute
   handler = RomanCatalogHandler(catalog_filename)
   formatted_catalog = handler.catalog
