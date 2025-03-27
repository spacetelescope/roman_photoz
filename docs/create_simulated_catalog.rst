========================
Create Simulated Catalog
========================

This module provides functionality to create a simulated catalog using data from the Roman Space Telescope. It leverages the LePhare photometric redshift estimation tool and other utilities to generate simulated data, process it, and save it in a structured format.

Module Contents
---------------

Classes
-------

SimulatedCatalog
~~~~~~~~~~~~~~~~

A class to create a simulated catalog using the Roman telescope data.

**Attributes**

- **data** (:class:`collections.OrderedDict`)  
  A dictionary to store the data.

- **lephare_config** (:class:`dict`)  
  Configuration for LePhare.

- **nobj** (:class:`int`)  
  Maximum number of objects to process from the input catalog.

- **flux_cols** (:class:`list`)  
  List of flux columns.

- **flux_err_cols** (:class:`list`)  
  List of flux error columns.

- **inform_stage** (:class:`None`)  
  Placeholder for inform stage.

- **estimated** (:class:`None`)  
  Holds all the results from `roman_photoz`.

- **filter_lib** (:class:`None`)  
  Placeholder for the filter library.

- **simulated_data_filename** (:class:`str`)  
  Filename for the simulated data.

- **simulated_data** (:class:`None`)  
  Placeholder for simulated data.

- **roman_catalog_template** (:class:`roman_datamodels.datamodels`)  
  Template catalog for the Roman telescope.

**Methods**

.. method:: __init__()

   Initializes the SimulatedCatalog class.

.. method:: read_roman_template_catalog()

   Reads the Roman catalog template from a predefined file.

   :return: The loaded Roman catalog template.
   :rtype: :class:`roman_datamodels.datamodels`

.. method:: is_folder_not_empty(folder_path: str, partial_text: str) -> bool

   Checks if a folder exists and contains files with the specified partial text.

   :param folder_path: The path to the folder.
   :type folder_path: str
   :param partial_text: The partial text to look for in filenames.
   :type partial_text: str
   :return: ``True`` if the folder contains matching files, ``False`` otherwise.
   :rtype: bool

.. method:: get_filters()

   Retrieves or generates the filter files for the Roman telescope and creates a filter library.

.. method:: create_simulated_data()

   Creates simulated data using the LePhare configuration.

.. method:: create_simulated_input_catalog(output_filename: str = DEFAULT_OUTPUT_CATALOG_FILENAME, output_path: str = "")

   Creates a simulated input catalog from the generated simulated data.

   :param output_filename: The filename for the output catalog.
   :type output_filename: str
   :param output_path: The path to save the output catalog.
   :type output_path: str

.. method:: update_roman_catalog_template(catalog)

   Updates the Roman catalog template with the simulated data.

   :param catalog: The catalog data to update the template with.
   :type catalog: :class:`numpy.ndarray`

.. method:: save_catalog(output_path: str = LEPHAREWORK, output_filename: str = DEFAULT_OUTPUT_CATALOG_FILENAME)

   Saves the simulated catalog to a file.

   :param output_path: The directory to save the catalog.
   :type output_path: str
   :param output_filename: The filename for the catalog.
   :type output_filename: str

.. method:: add_ids(catalog)

   Adds an ID column to the catalog.

   :param catalog: The catalog data.
   :type catalog: :class:`numpy.ndarray`
   :return: The catalog with an ID column added.
   :rtype: :class:`numpy.ndarray`

.. method:: add_error(catalog)

   Adds Gaussian errors to each magnitude column in the catalog.

   :param catalog: The catalog data.
   :type catalog: :class:`numpy.ndarray`
   :return: The catalog with error columns added.
   :rtype: :class:`numpy.ndarray`

.. method:: create_header(catalog_name: str)

   Creates the header for the catalog.

   :param catalog_name: The name of the catalog file.
   :type catalog_name: str
   :return: A list of column names for the catalog.
   :rtype: list

.. method:: pick_random_lines(num_lines: int)

   Picks random lines from the simulated data array.

   :param num_lines: The number of random lines to pick.
   :type num_lines: int
   :return: An array containing the randomly picked lines.
   :rtype: :class:`numpy.ndarray`

.. method:: process(output_path: str = "", output_filename: str = DEFAULT_OUTPUT_CATALOG_FILENAME)

   Runs the entire process to create the simulated catalog.

   :param output_path: The directory to save the catalog.
   :type output_path: str
   :param output_filename: The filename for the catalog.
   :type output_filename: str

Command-Line Usage
------------------

The module can also be executed as a standalone script to create a simulated catalog. It provides command-line arguments for specifying the output path and filename.

**Arguments**

- ``--output_path`` (:class:`str`)  
  Path to save the output catalog (default: ``LEPHAREWORK``).

- ``--output_filename`` (:class:`str`)  
  Filename for the output catalog (default: ``roman_simulated_catalog.asdf``).

**Example**

.. code-block:: bash

   python create_simulated_catalog.py --output_path /path/to/output --output_filename my_catalog.asdf

Dependencies
------------

- ``argparse``
- ``os``
- ``collections.OrderedDict``
- ``pathlib.Path``
- ``lephare``
- ``numpy``
- ``rail.core.stage``
- ``roman_datamodels``