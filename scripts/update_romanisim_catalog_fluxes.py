import numpy as np
from astropy import units as u
from astropy.table import Table


def create_random_catalog(table: Table, n: int, seed: int = 13):
    """
    Select n rows from table, with replacement.  Optionally set a seed for reproducibility.
    """
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(table) - 1, size=n)

    return table[idx]


def njy_to_mgy(flux):
    zero_point_flux = u.zero_point_flux(3631 * u.Jy)  # 1 maggy = 3631 Jy
    return flux.to(u.mgy, zero_point_flux)


def update_fluxes(target_catalog: Table, flux_catalog: Table) -> Table:
    fudge_factor = 100
    # LePhare catalog magnitudes seem to peak out at an absolute galaxy magnitude of -15
    # or so, while an L* galaxy should be more like -21.
    # we artificially brighten by a factor of 100.
    # need to figure out what's the issue here.

    for colname in target_catalog.colnames:
        if colname not in [
            "F062",
            "F087",
            "F106",
            "F129",
            "F158",
            "F184",
            "F213",
            "F146",
        ]:
            continue
        fluxname = f"segment_{colname.lower()}_flux"
        # convert from nJy (Roman  to maggies (romanisim_input_catalog)
        target_catalog[colname] = njy_to_mgy(flux_catalog[fluxname]) * fudge_factor

    # Add source ID from roman_simulated_catalog
    target_catalog["label"] = flux_catalog["label"]
    target_catalog["redshift_true"] = flux_catalog["redshift_true"]

    return target_catalog


if __name__ == "__main__":

    def parse_args():
        import argparse

        parser = argparse.ArgumentParser(
            description="Update fluxes in a Romanisim catalog using a reference catalog."
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

        parser.add_argument(
            "--nobj",
            type=int,
            default=None,
            help=(
                "Number of sources to subselect from target catalog.  Must "
                "be smaller than the number of rows in the target catalog."
            ),
        )

        return parser.parse_args()

    args = parse_args()

    romanisim_catalog_filename = args.target_catalog
    roman_photoz_catalog_filename = args.flux_catalog
    output_filename = args.output_filename

    romanisim_cat = Table.read(romanisim_catalog_filename, format="ascii.ecsv")
    if args.nobj is not None:
        if args.nobj > len(romanisim_cat):
            raise ValueError(
                "number of objects must be smaller than the number of objects"
                "in the target catalog."
            )
        rng = np.random.default_rng()
        romanisim_cat = romanisim_cat[
            rng.choice(len(romanisim_cat), args.nobj, replace=False)
        ]
    rpz_cat = Table.read(roman_photoz_catalog_filename, format="parquet")
    # trim anything that is impossibly bright or faint
    # ugly here that we have a lot of different kinds of magnitudes now
    minmag = np.min(
        [
            -2.5 * np.log10(rpz_cat[x])
            for x in rpz_cat.dtype.names
            if x.endswith("_flux") and x.startswith("segment")
        ],
        axis=0,
    )
    rpz_cat = rpz_cat[(minmag > 0) & (minmag < 33)]
    rpz_cat = create_random_catalog(table=rpz_cat, n=len(romanisim_cat))

    update_fluxes_cat = update_fluxes(
        target_catalog=romanisim_cat, flux_catalog=rpz_cat
    )
    update_fluxes_cat.write(output_filename, format="ascii.ecsv", overwrite=True)

    print("Done")
