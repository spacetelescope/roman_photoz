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
     (default: ``roman_simulated_catalog.parquet``).

3. If you don't already have an input catalog, create a simulated one. The
   output catalog will be saved to
   ``$LEPHAREWORK/roman_photoz_simulated_catalog.parquet``:

   .. code-block:: bash

      roman-photoz-create-simulated-catalog \
        --output-filename roman_photoz_simulated_catalog.parquet \
        --refresh-lib-mag

   To change the physical parameters used to generate the simulated catalog
   (e.g. redshift range/step), edit ``roman_photoz/default_config_file.py``.

4. Run ``roman-photoz``. Assuming there is a folder named ``OUTPUT`` in the
   current working directory where the updated catalog containing the
   redshift results will be saved to:

   .. code-block:: bash

      roman-photoz \
        --input-filename $LEPHAREWORK/roman_photoz_simulated_catalog.parquet \
        --output-filename ./OUTPUT/roman_photoz_simulated_catalog.parquet
