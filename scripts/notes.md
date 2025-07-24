# Detailed Description of `create_simulated_l1_files.sh`

This script orchestrates the generation of simulated Level 1 (L1) files for
Roman telescope data. It runs a sequence of scripts to create input
catalogs, simulate photometry, update catalogs, generate images, and prepare
association files. Below is a breakdown of the steps:

## 1. Create Romanisim Input Catalog

- **Command:** `python -m make_romanisim_input_catalog`
- **Description:** Generates an initial input catalog of galaxies using the
  `romanisim.make_galaxies(n)` method. This catalog serves as the base for
  subsequent simulations.

## 2. Simulate Photometry Catalog

- **Command:**

  `sh python -m roman_photoz.create_simulated_catalog --output-path .`

- **Description:** Creates a simulated photometric catalog using COSMOS
  templates and the `lephare.prepare` method. No additional photometric errors are
  added at this stage.

## 3. Update Romanisim Catalog with Simulated Fluxes

- **Command:**

  ````sh python -m update_romanisim_catalog_fluxes \ --target-catalog
  romanisim_input_catalog.ecsv \ --flux-catalog roman_simulated_catalog.parquet
  \ --output-filename romanisim_input_catalog_fluxes_updated.ecsv ```

  ````

- **Description:** Updates the initial Romanisim catalog with fluxes from the
  simulated photometry catalog, producing an updated catalog for image simulation.

## 4. Generate Simulated Images

- **Command:** `./run_romanisim.sh`
- **Description:** Runs Romanisim to generate simulated images based on the
  updated catalog.

## 5. Create Association Files for ELP and Run ELP

- **Commands:**

  `sh ./create_asn_files_for_elp.sh ./run_elp.sh`

- **Description:** Prepares association files for the ELP pipeline and executes
  it.

## 6. Create Association Files for Skycells

- **Command:** `./create_skycell_asn.sh`
- **Description:** Generates association files for skycell processing.

## 7. Run MOS Pipeline

- **Command:** `./run_mos.sh`
- **Description:** Runs the MOS pipeline using the previously generated
  association files.

## 8. Create Association Files for Multiband Catalog

- **Command:** `./create_asn_for_mbandcatalog.sh`
- **Description:** Prepares association files for multiband catalog generation.

## 9. Run Multiband Catalog Step

- **Command:**

  ````sh strun romancal.step.MultibandCatalogStep mbcat_270p65x49y70_wfi01.json
  --deblend True --fit_psf False ```

  ````

- **Description:** Executes the MultibandCatalogStep to produce the final
  multiband catalog, with deblending enabled and PSF fitting disabled.

## Completion Message

- **Command:** `echo "All steps completed successfully."`
- **Description:** Prints a message indicating successful completion of all
  steps.

---

## Additional Notes and Comments

- The script contains commented instructions and alternative commands for
  advanced usage, such as:
  - Determining which skycells are touched.
  - Creating associations for each filter.
  - Running MOS and MultibandCatalogStep for specific products.
  - Handling masked sources in PSF fitting.

- These comments provide guidance for troubleshooting and customizing the
  workflow for specific scenarios.

---

## Summary

This script provides a reproducible workflow for generating simulated Roman
telescope L1 files, integrating catalog creation, photometric simulation, image
generation, and catalog association steps. It is intended for use in data
analysis pipelines and can be customized as needed for specific science cases or
troubleshooting.
