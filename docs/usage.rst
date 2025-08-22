.. _usage:

=====
Usage
=====

There are a few ways to run ``roman_photoz``:

1. Interactive (Python) Mode
----------------------------

.. code-block:: python

   from roman_photoz.roman_catalog_process import RomanCatalogProcess

   rcp = RomanCatalogProcess(
       config_filename="",  # use default config
       model_filename="custom_model.pkl"
   )

   rcp.process(
       input_filename="./roman_photoz/data/roman_catalog_template.parquet",
       output_filename="output_filename.parquet",
       fit_colname="segment_{}_flux",  # name of the column with flux values
       fit_err_colname="segment_{}_flux_err",  # name of the column with flux errors
   )

2. Non-interactive (Script) Mode
--------------------------------

.. code-block:: python

   from roman_photoz import roman_catalog_process

   argv = [
       "--model-filename", "custom_model.pkl",
       "--input-filename", "./roman_photoz/data/roman_catalog_template.parquet",
       "--output-filename", "output_filename.parquet",
       "--fit-colname", "segment_{}_flux",  # name of the column with flux values
       "--fit-err-colname", "segment_{}_flux_err",  # name of the column with flux errors
   ]
   roman_catalog_process.main(argv)

3. Python Module
----------------

.. code-block:: bash

   python -m roman_photoz \
     --model-filename=custom_model.pkl \
     --input-filename=./roman_photoz/data/roman_catalog_template.parquet \
     --output-filename=output_filename.parquet \
     --fit-colname=segment_{}_flux \
     --fit-err-colname=segment_{}_flux_err

4. CLI
------

``roman-photoz`` is also available as a command-line interface (CLI) tool.
After installing the package, two commands will be available in your environment:


- ``roman-photoz-create-simulated-catalog``: creates a simulated Roman multiband catalog.
- ``roman-photoz``: starts the processing of a Roman multiband catalog to estimate redshifts;

For instance, you can run the following command in your terminal to process a
template Roman multiband catalog provided with the roman-photoz package:

.. code-block:: bash

  $ roman-photoz \
    --input-filename ./roman_photoz/data/roman_catalog_template.parquet \
    --output-filename output_filename.parquet \
    --fit-colname segment_{}_flux \
    --fit-err-colname segment_{}_flux_err

See module docs for additional options and examples.
