from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt

from roman_photoz import default_roman_config
from roman_photoz.roman_catalog_process import RomanCatalogProcess

# set the output path to the directory
# where this script is located
output_path = Path(__file__).resolve().parent.as_posix()

####
# This example shows how to create a RomanCatalogProcess instance directly
# with a custom model filename and use it to process a catalog

# create a RomanCatalogProcess object with a custom model filename
rcp = RomanCatalogProcess(
    config_filename=default_roman_config,
    model_filename="custom_roman_model.pkl",  # Using a custom model filename
)

# process the catalog
rcp.process(
    input_path="/Users/mteodoro/Library/Caches/lephare/work/",
    input_filename="roman_simulated_catalog.asdf",
    output_path=output_path,
    output_filename="output_file_2.asdf",
    save_results=True,
)

# plot the estimated PDF for the first object
zgrid = np.linspace(0, 7, 200)
plt.plot(zgrid, np.squeeze(rcp.estimated.data.pdf(zgrid)[0]))

# plot the estimated redshift ("Z_BEST") vs. the actual redshift ("ZSPEC")
plt.plot(rcp.estimated.data.ancil["ZSPEC"], rcp.estimated.data.ancil["Z_BEST"], "o")

# plot the redshift vs. the simulated magnitude in all filters
plt.plot(rcp.estimated.data.ancil["ZSPEC"], rcp.estimated.data.ancil["MAG_OBS()"], "o")

print("Done!")
