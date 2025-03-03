from pathlib import Path

from roman_photoz import default_roman_config, roman_catalog_process

# set the output path to the directory
# where this script is located
output_path = Path(__file__).resolve().parent.as_posix()

# we will use the default Roman config
# and the default input path/filename
# we will save the results
# to a file called "output_file_1.asdf"
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
    "output_file_1.asdf",
    "--save_results",
    "True",
]

####
# this approach will process the catalog
# and save the results to a file
# but will not return anything

# process the catalog
roman_catalog_process.main(argv)

print("Done!")
