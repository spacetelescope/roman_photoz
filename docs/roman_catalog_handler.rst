=====================
Roman Catalog Handler
=====================

Overview
--------

The ``roman_catalog_handler`` module provides functionality for handling catalog data from the Roman Space Telescope. It includes the ``RomanCatalogHandler`` class which offers methods for reading, formatting, and processing catalog data files.

Module API
----------

.. py:module:: roman_catalog_handler

.. py:class:: RomanCatalogHandler(catname='')

    A class to handle Roman catalog operations including reading, formatting, and processing.

    :param str catname: The name of the catalog file. Defaults to an empty string.

    .. py:method:: __init__(catname='')

        Initialize the RomanCatalogHandler with a catalog name.

        :param str catname: The name of the catalog file. Defaults to an empty string.

    .. py:method:: read_catalog()

        Read the catalog file and convert it to a numpy structured array.

        :return: The catalog data as a numpy array
        :rtype: numpy.ndarray

    .. py:method:: format_catalog()

        Format the catalog by appending necessary fields and columns.

        :return: The formatted catalog
        :rtype: numpy.ndarray

    .. py:method:: process()

        Process the catalog by reading and formatting it.

        :return: The formatted catalog
        :rtype: numpy.ndarray

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
