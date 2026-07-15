# roman_photoz

Tool for determining photometric redshift from Roman catalogs.

## Installation

```bash
pip install roman_photoz
```

## Setup and run: step-by-step

### 1. Set the required environment variables (recommended)

`roman-photoz` uses `LEPHAREDIR` and `LEPHAREWORK` to determine where to
store the LePhare data and work directories. Set them explicitly before
running any commands:

```bash
export LEPHAREDIR=/path/to/lephare_data
export LEPHAREWORK=/path/to/lephare_work
```

If you don't set them, `lephare` will fall back to its own default cache
directories (typically under `~/Library/Caches/lephare` on macOS or the
platform equivalent elsewhere) and print a notice showing the full paths it
chose. Setting the variables yourself gives you control over where these
(potentially large) files are stored.

### 2. Run the setup command

This downloads the LePhare auxiliary data required by the Roman config,
creates a simulated catalog and Roman filter files, builds the informer
model, trims `LEPHAREDIR` to the files needed by the estimator, and verifies
that the required artifacts are present:

```bash
roman-photoz --setup
```

Options:

- `--nobj N` — number of objects in the simulated catalog (default: 1000).
- `--simulated-catalog-filename FILE` — simulated catalog filename (default:
  `roman_simulated_catalog.parquet`).

### 3. Create a simulated input catalog (if you don't already have one)

If you don't already have an input catalog, you can create a simulated one
with the following command. The output catalog will be saved to
`$LEPHAREWORK/roman_photoz_simulated_catalog.parquet`:

```bash
roman-photoz-create-simulated-catalog \
  --output-filename roman_photoz_simulated_catalog.parquet \
  --refresh-lib-mag
```

> To change the physical parameters used to generate the simulated catalog
> (e.g. redshift range/step), edit `roman_photoz/default_config_file.py`.

### 4. Run roman-photoz

Assuming there is a folder named `OUTPUT` in the current working directory
where the updated catalog containing the redshift results will be saved to,
run:

```bash
roman-photoz \
  --input-filename $LEPHAREWORK/roman_photoz_simulated_catalog.parquet \
  --output-filename ./OUTPUT/roman_photoz_simulated_catalog.parquet
```

## Development

To install the development version, clone the repository and install it in
editable mode:

```bash
git clone https://github.com/spacetelescope/roman_photoz.git
cd roman_photoz
pip install -e ".[dev]"
```
