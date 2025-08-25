=====================
Roman Catalog Process
=====================

This module provides functionality for processing a Roman Telescope multiband
catalog to obtain photometric redshifts for cataloged galaxies.

Module API
----------

.. automodule:: roman_photoz.roman_catalog_process
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

For a quick start, we can use the roman-photoz CLI to create a Roman multiband catalog containing 2000
simulated objects through the ``roman-photoz-create-simulated-catalog`` command:

.. code-block:: bash

  $ roman-photoz-create-simulated-catalog \
     --output-path ./ \
     --output-filename roman_photoz_simulated_catalog.parquet \
     --nobj 2000

Then, use the ``RomanCatalogProcess`` class to process the catalog and estimate
the redshifts through the ``roman-photoz`` command:

.. code-block:: bash

   $ roman-photoz \
     --input-filename roman_photoz_simulated_catalog.parquet \
     --output-filename roman_photoz_results.parquet \
     --fit-colname segment_{}_flux \
     --fit-err-colname segment_{}_flux_err

Additional examples of how to use this module can be found in the :ref:`usage`
section.
