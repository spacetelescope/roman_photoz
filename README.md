# roman_photoz

Tool for determining photometric redshift from Roman catalogs.

## Setup and run: step-by-step

### 1. Install dependencies

**Using [`uv`](https://docs.astral.sh/uv/) (recommended):**

```bash
uv sync --all-extras
```

**Without `uv`**, using a plain virtual environment and `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

> The rest of this guide uses `uv run <command>` to invoke CLI tools and
> scripts. If you're not using `uv`, activate your virtual environment
> (e.g. `source .venv/bin/activate`) and drop the `uv run` prefix — the
> commands (e.g. `roman-photoz`, `roman-photoz-create-simulated-catalog`)
> are installed as regular executables on your `PATH`. For the bootstrap
> script, pass `--python-runner python` (or the path to your environment's
> `python`) instead of the default `uv run`.

### 2. Configure the bootstrap

Edit `bootstrap_roman_photoz.pars` with your desired setup (data root, simulated
catalog size, model build/cleanup options, etc.). Defaults are reasonable for a
first run.

### 3. Run the bootstrap script

This downloads the LePhare auxiliary data required by the Roman config,
optionally builds the Roman model (informer stage), applies the configured
cleanup policy, and (optionally) verifies required assets:

```bash
bash bootstrap_roman_photoz.sh --pars-file ./bootstrap_roman_photoz.pars
```

Useful overrides:

- `--python-runner "uv run"` — runner used for python/CLI invocation (defaults to
  `uv run`; use `--python-runner python` if you're not using `uv`).
- `--build-model` — build the Roman model; omit to skip.
- `--force-refresh` — force refresh of model/lib_mag assets; omit to disable.
- `--verify-assets` — validate required artifacts after bootstrap; omit to skip.
- `--dry-run` — preview the resolved configuration/actions without mutating files.

Run `bash bootstrap_roman_photoz.sh --help` for the full list of options.

### 4. Load the runtime environment

Do this in every new shell before running `roman-photoz`:

```bash
source ./.env && export LEPHAREDIR LEPHAREWORK INFORMER_MODEL_PATH
```

### 5. Create a simulated input catalog (if you don't already have one)

If you don't already have an input catalog, you can create a simulated
one with the following command. The output catalog will be saved to 
`$LEPHAREWORK/roman_photoz_simulated_catalog.parquet`.

```bash
uv run roman-photoz-create-simulated-catalog \
  --output-filename roman_photoz_simulated_catalog.parquet \
  --refresh-lib-mag
```

> To change the physical parameters used to generate the simulated catalog
> (e.g. redshift range/step), edit `roman_photoz/default_config_file.py`.

### 6. Run roman-photoz

Assuming there is a folder named OUTPUT in the current working directory 
where the updated catalog containing the redshift results will be saved to, run:

```bash
uv run roman-photoz \
  --input-filename $LEPHAREWORK/roman_photoz_simulated_catalog.parquet \
  --output-filename ./OUTPUT/roman_photoz_simulated_catalog.parquet
```

### Cleanup modes

- `trimmed`: removes intermediate files and trims `LEPHAREDIR` to estimator essentials.
- `full` (default): removes intermediate files but keeps the full `LEPHAREDIR` content tree.
- `none`: keeps all intermediate files and full `LEPHAREDIR` contents.
