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

3. Install package in editable mode.

   Using ``uv`` (recommended):

   .. code-block:: bash

      uv sync --all-extras

   Without ``uv``, using a plain virtual environment and ``pip``. For example, on macOS:

   .. code-block:: bash

      python -m venv .venv
      source .venv/bin/activate
      pip install -e ".[dev]"

   The rest of this guide uses ``uv run <command>`` to invoke CLI tools and
   scripts. If you're not using ``uv``, activate your virtual environment and
   drop the ``uv run`` prefix -- the commands (e.g. ``roman-photoz``,
   ``roman-photoz-create-simulated-catalog``) are installed as regular
   executables on your ``PATH``. For the bootstrap script, pass
   ``--python-runner python`` (or the path to your environment's ``python``)
   instead of the default ``uv run``.

===========================
Bootstrap data/model setup
===========================

Use the pars-driven bootstrap flow as the canonical setup path:

1. Edit ``bootstrap_roman_photoz.pars`` with your desired setup (data root,
   simulated catalog size, model build/cleanup options, etc.). Defaults are
   reasonable for a first run.

2. Run the bootstrap script. This downloads the LePhare auxiliary data
   required by the Roman config, optionally builds the Roman model (informer
   stage), applies the configured cleanup policy, and (optionally) verifies
   required assets:

   .. code-block:: bash

      bash bootstrap_roman_photoz.sh --pars-file ./bootstrap_roman_photoz.pars

   Useful overrides:

   - ``--python-runner "uv run"`` -- runner used for python/CLI invocation
     (defaults to ``uv run``; use ``--python-runner python`` if you're not
     using ``uv``).
   - ``--build-model`` -- build the Roman model; omit to skip.
   - ``--force-refresh`` -- force refresh of model/lib_mag assets; omit to disable.
   - ``--verify-assets`` -- validate required artifacts after bootstrap; omit to skip.
   - ``--dry-run`` -- preview the resolved configuration/actions without mutating files.

   Run ``bash bootstrap_roman_photoz.sh --help`` for the full list of options.

3. In a new shell, source the generated runtime env before running
   ``roman-photoz``:

   .. code-block:: bash

      source ./.env && export LEPHAREDIR LEPHAREWORK INFORMER_MODEL_PATH

4. If you don't already have an input catalog, create a simulated one. The
   output catalog will be saved to
   ``$LEPHAREWORK/roman_photoz_simulated_catalog.parquet``:

   .. code-block:: bash

      uv run roman-photoz-create-simulated-catalog \
        --output-filename roman_photoz_simulated_catalog.parquet \
        --refresh-lib-mag

   To change the physical parameters used to generate the simulated catalog
   (e.g. redshift range/step), edit ``roman_photoz/default_config_file.py``.

5. Run ``roman-photoz``. Assuming there is a folder named ``OUTPUT`` in the
   current working directory where the updated catalog containing the
   redshift results will be saved to:

   .. code-block:: bash

      uv run roman-photoz \
        --input-filename $LEPHAREWORK/roman_photoz_simulated_catalog.parquet \
        --output-filename ./OUTPUT/roman_photoz_simulated_catalog.parquet

Cleanup modes in the pars file:

- ``trimmed``: remove intermediate files and trim ``LEPHAREDIR`` to estimator essentials.
- ``full`` (default): remove intermediate files but keep full ``LEPHAREDIR`` contents.
- ``none``: keep all intermediate files and full ``LEPHAREDIR`` contents.
