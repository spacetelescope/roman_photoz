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

   python cm roman_photoz.reate_simulated_catalog. --output_path=/path/to/output/ --output_filename=simulated_catalog.asdf

Usage Examples
-------------

The following example demonstrates how to programmatically create a simulated catalog:

.. code-block:: python

    from roman_photoz.create_simulated_catalog import CreateSimulatedCatalog

    # Initialize the catalog creator with default parameters
    creator = CreateSimulatedCatalog()

    # Create a simulated catalog with 100 sources
    catalog = creator.create_catalog(n_sources=100)

    # Save the catalog to a file
    creator.save_catalog(
        catalog,
        output_path="/path/to/output/",
        output_filename="simulated_catalog.asdf"
    )

    print(f"Simulated catalog with {len(catalog)} sources created successfully")
