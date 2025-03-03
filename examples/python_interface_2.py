from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt

from roman_photoz import default_roman_config
from roman_photoz.roman_catalog_process import RomanCatalogProcess

# set the output path to the directory
# where this script is located
output_path = Path(__file__).resolve().parent.as_posix()

# we will use the default Roman config
# and the default input path/filename
# we will save the results
# to a file called "output_file_2.asdf"
argv = [
    "--config_filename",
    default_roman_config,
    "--input_path",
    "/Users/mteodoro/Library/Caches/lephare/work/",
    "--input_filename",
    "roman_simulated_catalog.in",
    "--output_path",
    output_path,
    "--output_filename",
    "output_file_2.asdf",
    "--save_results",
    "True",
]

####
# this approach will process the catalog
# and save the results to a file
# and will return an instance of RomanCatalogProcess
# that contains the results

# create a RomanCatalogProcess object
rcp = RomanCatalogProcess(config_filename=argv[1])

# and process the catalog
rcp.process(
    input_path=argv[3],
    input_filename=argv[5],
    output_path=argv[7],
    output_filename=argv[9],
    save_results=argv[11],
)

# plot the estimated PDF for the first object
zgrid = np.linspace(0, 7, 200)
plt.plot(zgrid, np.squeeze(rcp.estimated.data.pdf(zgrid)[0]))

# plot the estimated redshift ("Z_BEST") vs. the actual redshift ("ZSPEC")
plt.plot(rcp.estimated.data.ancil["ZSPEC"], rcp.estimated.data.ancil["Z_BEST"], "o")

# plot the redshift vs. the simulated magnitude in all filters
plt.plot(rcp.estimated.data.ancil["ZSPEC"], rcp.estimated.data.ancil["MAG_OBS()"], "o")

print("Done!")
