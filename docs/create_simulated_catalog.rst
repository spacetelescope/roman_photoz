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

Once ``roman-photoz`` is installed, you can create a simulated catalog using
the CLI command ``roman-photoz-create-simulated-catalog``. For example, to
create a Roman multiband catalog with 1000 simulated objects and have it saved
in the current directory under the name ``simulated_catalog.parquet``, run the
following command:

.. code-block:: bash

  $ roman-photoz-create-simulated-catalog \
   --output-path ./ \
   --output-filename simulated_catalog.parquet \
   --nobj=1000


Usage Examples
--------------

Another way to create a simulated catalog is to use the
``SimulatedCatalog`` class directly in your Python code. For example:

.. code-block:: python

   from roman_photoz.create_simulated_catalog import SimulatedCatalog

   # simulate 1000 objects and add a gaussian noise with sigma=0.15 mag
   simulated_catalog1 = SimulatedCatalog(1000, mag_noise=0.15)

   # simulate 5000 objects and add a gaussian noise with sigma=0.05 mag
   simulated_catalog2 = SimulatedCatalog(5000, mag_noise=0.05)

   # create the simulated catalogs and save them in the current directory
   simulated_catalog1.process(output_filename="roman_simulated_catalog1.parquet")
   simulated_catalog2.process(output_filename="roman_simulated_catalog2.parquet")
