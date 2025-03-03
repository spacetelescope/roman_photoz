from roman_photoz import roman_catalog_process
from roman_photoz import default_roman_config
from pathlib import Path

output_path = Path(".").resolve().as_posix()

argv = [
    "--config_filename", default_roman_config,
    "--input_path", "/Users/mteodoro/Library/Caches/lephare/work/",
    "--input_filename", "roman_simulated_catalog.in",
    "--output_path", output_path,
    "--output_filename", "output_file.asdf",
    "--save_results", "True"
]

roman_catalog_process.main(argv)

print("Done!")