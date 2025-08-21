=====
Usage
=====

To use ``roman_photoz``, follow the workflows below.

1. Interactive (Python) Mode
----------------------------

.. code-block:: python

   from roman_photoz.roman_catalog_process import RomanCatalogProcess

   rcp = RomanCatalogProcess(
       config_filename="",  # use default config
       model_filename="custom_model.pkl"
   )

   rcp.process(
       input_filename="roman_simulated_catalog.parquet",
       output_filename="output_filename.parquet",
       fit_colname="segment_{}_flux",  # name of the column with flux values
       fit_err_colname="segment_{}_flux_err",  # name of the column with flux errors
   )

   # Example visualization
   import matplotlib.pyplot as plt
   import numpy as np
   zgrid = np.linspace(0, 7, 200)
   plt.plot(zgrid, rcp.estimated.data.pdf(zgrid)[0])

2. Non-interactive (Script) Mode
--------------------------------

.. code-block:: python

   from roman_photoz import roman_catalog_process

   argv = [
       "--model_filename", "custom_model.pkl",
       "--input_filename", "roman_simulated_catalog.parquet",
       "--output_filename", "output_filename.asdf",
       "--fit_colname", "segment_{}_flux",  # name of the column with flux values
       "--fit_err_colname", "segment_{}_flux_err",  # name of the column with flux errors
   ]
   roman_catalog_process.main(argv)

3. Command-Line Mode
--------------------

.. code-block:: bash

   python -m roman_photoz \
     --model_filename=custom_model.pkl \
     --input_filename=roman_simulated_catalog.asdf \
     --output_filename=output_filename.asdf \
     --fit_colname=segment_{}_flux \
     --fit_err_colname=segment_{}_flux_err

See module docs for additional options and examples.
