============
Installation
============

To install ``roman_photoz``, simply use pip:

  .. code-block:: bash

      pip install roman_photoz

===========
Development
===========

To install the development version of ``roman_photoz``, you can clone the repository and install it in editable mode:

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/spacetelescope/roman_photoz.git

2. Navigate to the project directory:

   .. code-block:: bash

      cd roman_photoz

3. Install package in editable mode. For example, on macOS:

   .. code-block:: bash

      pip install -e ".[dev]"

===========================
Bootstrap data/model setup
===========================

Run ``roman-photoz --setup`` to download the LePhare auxiliary data required
by the Roman config, create a simulated catalog and Roman filter files,
build the model (informer stage), trim ``LEPHAREDIR`` to the files needed by
the estimator, and verify that the required artifacts are present:

1. Set the environment variables (recommended). ``roman-photoz`` uses
   ``LEPHAREDIR`` and ``LEPHAREWORK`` to determine where to store the
   LePhare data and work directories:

   .. code-block:: bash

      export LEPHAREDIR=/path/to/lephare_data
      export LEPHAREWORK=/path/to/lephare_work

   If you don't set them, ``lephare`` falls back to its own default cache
   directories (typically under ``~/Library/Caches/lephare`` on macOS, or
   the platform equivalent elsewhere) and prints a notice showing the full
   paths it chose. Setting the variables yourself gives you control over
   where these (potentially large) files are stored.

2. Run:

   .. code-block:: bash

      roman-photoz --setup

   Options:

   - ``--nobj N`` -- number of objects in the simulated catalog (default: 1000).
   - ``--simulated-catalog-filename FILE`` -- simulated catalog filename
     (default: ``roman_photoz_simulated_catalog.parquet``).

   This leaves a catalog behind at
   ``$LEPHAREWORK/roman_photoz_simulated_catalog.parquet`` (it already has
   redshift estimates added by setup's own model-building pass). This
   catalog isn't meant to be your real input data -- it's a fallback you
   can use in step 3 below if you don't have your own catalog yet (see
   "Creating a fresh simulated catalog" below for another option).

3. Run ``roman-photoz``. Assuming there is a folder named ``OUTPUT`` in the
   current working directory where the updated catalog containing the
   redshift results will be saved to:

   .. code-block:: bash

      roman-photoz \
        --input-filename <path/to/your_catalog.parquet> \
        --output-filename ./OUTPUT/<path/to/your_catalog.parquet>

   ``--input-filename`` should point to your own input catalog. If you
   don't have one, you can pass in the catalog created in step 2 instead:
   ``$LEPHAREWORK/roman_photoz_simulated_catalog.parquet``.

   **Creating a fresh simulated catalog (optional)**

   If you'd rather not reuse the catalog from step 2 -- for example, you
   want a different number of objects or different physical parameters --
   generate a fresh one:

   .. code-block:: bash

      roman-photoz-create-simulated-catalog \
        --output-filename roman_photoz_simulated_catalog.parquet \
        --refresh-lib-mag

   To change the physical parameters used to generate the simulated catalog
   (e.g. redshift range/step), edit ``roman_photoz/default_config_file.py``.
