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
