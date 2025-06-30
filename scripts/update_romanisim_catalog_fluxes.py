from astropy.table import Table
import numpy as np


def create_random_catalog(table: Table, n: int = 0, seed: int = 13):
    """
    Return a random row from an astropy Table object using numpy's choice. Optionally set a seed for reproducibility.
    """
    if len(table) == 0:
        return None
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n - 1, size=n)

    return table[idx]


def update_fluxes(target_catalog: Table, flux_catalog: Table) -> Table:
    for colname in flux_catalog.colnames:
        flux_catalog.rename_column(colname, colname.replace("magnitude_", ""))

    for colname in target_catalog.colnames:
        if colname in flux_catalog.colnames:
            breakpoint()
            target_catalog[colname] = 10 ** (-0.4 * flux_catalog[colname])

    return target_catalog


if __name__ == "__main__":

    def parse_args():
        import argparse

        parser = argparse.ArgumentParser(
            description="Update fluxes in a Romanisim catalog using a reference catalog."
        )
        parser.add_argument(
            "--n_sources",
            type=int,
            default=15000,
            help="Number of sources to select from the catalogs.",
        )
        parser.add_argument(
            "--target-catalog",
            type=str,
            default="romanisim_input_catalog.ecsv",
            help="Target catalog to update fluxes in.",
        )

        parser.add_argument(
            "--flux-catalog",
            type=str,
            default="roman_simulated_catalog.parquet",
            help="Reference catalog to use for updating fluxes.",
        )

        parser.add_argument(
            "--output-filename",
            type=str,
            default="romanisim_input_catalog_fluxes_updated.ecsv",
            help="Output filename for the updated catalog.",
        )

        return parser.parse_args()

    args = parse_args()

    romanisim_catalog_filename = args.target_catalog
    roman_photoz_catalog_filename = args.flux_catalog
    output_filename = args.output_filename

    romanisim_cat = Table.read(romanisim_catalog_filename, format="ascii.ecsv")
    rpz_cat = Table.read(roman_photoz_catalog_filename, format="parquet")

    n_sources = 50000

    if (n_sources > len(rpz_cat)) or (n_sources > len(romanisim_cat)):
        raise ValueError(
            "Requested number of sources is greater than the number of available sources in catalogs."
        )

    ref_cat = create_random_catalog(table=rpz_cat, n=n_sources)
    target_cat = create_random_catalog(table=romanisim_cat, n=n_sources)

    update_fluxes_cat = update_fluxes(target_catalog=target_cat, flux_catalog=ref_cat)
    update_fluxes_cat.write(output_filename, format="ascii.ecsv", overwrite=True)

    print("Done")
