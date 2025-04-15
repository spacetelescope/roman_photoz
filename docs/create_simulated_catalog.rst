========================
Create Simulated Catalog
========================

This module provides functionality to create a simulated catalog using data from the Roman Space Telescope. It leverages the LePhare photometric redshift estimation tool and other utilities to generate simulated data, process it, and save it in a structured format.

Module API
----------

.. automodule:: create_simulated_catalog
   :members:
   :undoc-members:
   :show-inheritance:

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
