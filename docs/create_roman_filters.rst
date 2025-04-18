====================
Create Roman Filters
====================

This module provides functionality to process Roman Space Telescope filter data, create individual filter files, and generate a configuration file for use with `rail+lephare`.

Module API
----------

.. automodule:: create_roman_filters
   :members:
   :undoc-members:
   :show-inheritance:

Usage Example
-------------

To use this module, run it as a script with the following command:

.. code-block:: bash

    python create_roman_filters.py <output_path> <input_filename>

- `<output_path>`: The directory where the results will be saved.
- `<input_filename>`: The filename containing the monochromatic effective area of each filter per column.

The script will generate individual filter files and a configuration file (`roman_phot.par`) for use with `rail+lephare`.
