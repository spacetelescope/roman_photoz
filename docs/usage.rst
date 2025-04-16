=====
Usage
=====

To use `roman_photoz`, follow these steps:


1. Interactive mode:

    .. code-block:: python

        import matplotlib.pyplot as plt
        import numpy as np
        from roman_photoz.roman_catalog_process import RomanCatalogProcess

        # create a RomanCatalogProcess object with default configuration
        # and custom model filename
        rcp = RomanCatalogProcess(
            config_filename="",  # use default config
            model_filename="custom_model.pkl"  # specify custom model filename
        )

        # process the catalog
        rcp.process(
            input_path="/path/to/input/file/",
            input_filename="roman_simulated_catalog.asdf",
            output_path="/path/to/output/file/",
            output_filename="output_filename.asdf",
            save_results=True,
        )

        # examples of visualization
        # plot the estimated PDF for the first object
        zgrid = np.linspace(0, 7, 200)
        plt.plot(zgrid, np.squeeze(rcp.estimated.data.pdf(zgrid)[0]))

        # plot the estimated redshift ("Z_BEST") vs. the actual redshift ("ZSPEC")
        plt.plot(rcp.estimated.data.ancil["ZSPEC"], rcp.estimated.data.ancil["Z_BEST"], "o")

        # plot the redshift vs. the simulated magnitude in all filters
        plt.plot(rcp.estimated.data.ancil["ZSPEC"], rcp.estimated.data.ancil["MAG_OBS()"], "o")

2. Non-interactive mode:

    .. code-block:: python

        from roman_photoz import roman_catalog_process

        argv = [
            "--model_filename",
            "custom_model.pkl",
            "--input_path",
            "/path/to/input/file/",
            "--input_filename",
            "roman_simulated_catalog.asdf",
            "--output_path",
            "/path/to/output/file/",
            "--output_filename",
            "output_filename.asdf",
            "--save_results",
            "True",
        ]

        roman_catalog_process.main(argv)

3. Command line mode:

    .. code-block:: bash

        python -m roman_photoz --model_filename=custom_model.pkl --input_path=/path/to/input/file/ --input_filename=roman_simulated_catalog.asdf --output_path=/path/to/output/file/ --output_filename=output_filename.asdf --save_results=True
