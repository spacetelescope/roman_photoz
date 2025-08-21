========================
Create Simulated Catalog
========================

This module provides functionality to create a simulated catalog using data
from the Roman Space Telescope. It leverages the LePhare photometric redshift
estimation tool and other utilities to generate simulated data, process it, and
save it in a structured format.

Module API
----------

.. automodule:: roman_photoz.create_simulated_catalog
   :members:
   :undoc-members:
   :show-inheritance:

Command-Line Usage
------------------

.. code-block:: bash

   python -m roman_photoz.create_simulated_catalog
   --output_path=/path/to/output/ --output_filename=simulated_catalog.asdf

Usage Examples
--------------

.. code-block:: python

   from roman_photoz.create_simulated_catalog import CreateSimulatedCatalog

   creator = CreateSimulatedCatalog()
   catalog = creator.create_catalog(n_sources=100)
   creator.save_catalog(
       catalog,
       output_path="/path/to/output/",
       output_filename="simulated_catalog.asdf"
   )
   print(f"Simulated catalog with {len(catalog)} sources created successfully.")
