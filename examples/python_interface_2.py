from roman_photoz.roman_catalog_process import RomanCatalogProcess
from roman_photoz import default_roman_config
from pathlib import Path
import numpy as np
from matplotlib import pyplot as plt

output_path = Path("./").resolve().as_posix()

argv = [
    "--config_filename", default_roman_config,
    "--input_path", "/Users/mteodoro/Library/Caches/lephare/work/",
    "--input_filename", "roman_simulated_catalog.in",
    "--output_path", output_path,
    "--output_filename", "output_file.asdf",
    "--save_results", "True"
]

rcp = RomanCatalogProcess(config_filename=argv[1])

rcp.process(
    input_path=argv[3],
    input_filename=argv[5],
    output_path=argv[7],
    output_filename=argv[9],
    save_results=argv[11]
)

zgrid = np.linspace(0, 7, 100)
plt.plot(zgrid, np.squeeze(rcp.estimated.data.pdf(zgrid)[0]))

print("Done!")