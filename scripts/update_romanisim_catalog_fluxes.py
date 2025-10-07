import numpy as np
from astropy import units as u
from astropy.table import Table

from roman_photoz.utils import get_roman_filter_list


def create_random_catalog(table: Table, n: int, seed: int = 13):
    """
    Select n rows from the input table, with replacement.

    Parameters
    ----------
    table : Table
        The input Astropy Table to sample from.
    n : int
        Number of rows to select.
    seed : int, optional
        Random seed for reproducibility (default is 13).

    Returns
    -------
    Table
        A new Table containing n randomly selected rows from the input table.
    """
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(table) - 1, size=n)
    return table[idx]


def njy_to_mgy(flux):
    """
    Convert flux from nanoJanskys (nJy) to maggies (mgy).

    Parameters
    ----------
    flux : Quantity
        Flux value(s) in nJy.

    Returns
    -------
    Quantity
        Flux value(s) converted to maggies.
    """
    zero_point_flux = u.zero_point_flux(3631 * u.Jy)  # 1 maggy = 3631 Jy
    return flux.to(u.mgy, zero_point_flux)


def scale_flux(flux, scaling_factor=None):
    """
    Scale the input flux by a given scaling factor.

    Parameters
    ----------
    flux : Quantity or array-like
        Flux value(s) to scale.
    scaling_factor : np.ndarray, optional
        Factor(s) to scale the flux by (default is an array of ones).

    Returns
    -------
    Quantity or array-like
        Scaled flux value(s).
    """
    scaling_factor = np.ones_like(flux) if scaling_factor is None else scaling_factor
    return flux * scaling_factor


def update_fluxes(
    target_catalog: Table,
    flux_catalog: Table,
    apply_scaling: bool = False,
    ref_filter: str = "F213",
) -> Table:
    """
    Update flux columns in the target catalog using values from the flux catalog.

    Parameters
    ----------
    target_catalog : Table
        The catalog whose fluxes will be updated.
    flux_catalog : Table
        The reference catalog providing new flux values.
    apply_scaling : bool, optional
        Whether to apply a scaling factor (float or array) based on the reference filter (default is no scaling).
    ref_filter : str, optional
        The reference filter to use for scaling (default is "F213").

    Returns
    -------
    Table
        The updated target catalog with new fluxes and copied label/redshift columns.
    """
    fudge_factor = 100

    # Set reference filter for flux scaling
    ref_filter = ref_filter.upper()
    # Get romanisim fluxes in mgy
    ref_target_vals = np.asarray(target_catalog[ref_filter])
    # Get rpz simulated fluxes in mgy
    ref_flux_vals = np.asarray(
        njy_to_mgy(flux_catalog[f"segment_{ref_filter.lower()}_flux"])
    )
    # Determine scaling factor if requested
    scaling_factor = ref_target_vals / ref_flux_vals if apply_scaling else None

    filter_list = get_roman_filter_list(uppercase=True)

    # Make a copy to avoid modifying the input in place
    updated_catalog = target_catalog.copy()

    for colname in filter_list:
        if colname in updated_catalog.colnames:
            if colname == ref_filter:
                updated_catalog[colname] = target_catalog[ref_filter] * fudge_factor
            else:
                fluxname = f"segment_{colname.lower()}_flux"
                # convert from nJy (Roman) to maggies (romanisim_input_catalog)
                converted_flux = njy_to_mgy(flux_catalog[fluxname]) * fudge_factor
                # scale fluxes based on reference filter if requested
                if apply_scaling:
                    updated_catalog[colname] = scale_flux(
                        converted_flux, scaling_factor
                    )
                else:
                    updated_catalog[colname] = converted_flux

    # Add source ID from roman_simulated_catalog
    updated_catalog["label"] = flux_catalog["label"]
    updated_catalog["redshift_true"] = flux_catalog["redshift_true"]

    return updated_catalog


if __name__ == "__main__":

    def parse_args():
        """
        Parse command-line arguments for the script.

        Returns
        -------
        argparse.Namespace
            Parsed arguments.
        """
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

        parser.add_argument(
            "--apply-scaling",
            action="store_true",
            help="Whether to apply flux scaling based on reference filter.",
        )

        return parser.parse_args()

    args = parse_args()

    romanisim_catalog_filename = args.target_catalog
    roman_photoz_catalog_filename = args.flux_catalog
    output_filename = args.output_filename
    apply_scaling = args.apply_scaling

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
    # roman_photoz_catalog fluxes are in nJy
    rpz_cat = Table.read(roman_photoz_catalog_filename, format="parquet")
    # create an array of minimum magnitudes across all selected flux columns
    # (this will be used as a boolean mask to filter out invalid objects)
    minmag = np.min(
        [
            -2.5 * np.log10(njy_to_mgy(rpz_cat[x]).value)
            for x in rpz_cat.dtype.names
            if x.endswith("_flux") and x.startswith("segment")
        ],
        axis=0,
    )
    # Create a filter mask to filter out objects outside the valid magnitude range
    rpz_cat = rpz_cat[(minmag > 0) & (minmag < 33)]
    # create a random catalog from rpz_cat with the same number of rows as romanisim_cat
    rpz_cat = create_random_catalog(table=rpz_cat, n=len(romanisim_cat))

    update_fluxes_cat = update_fluxes(
        target_catalog=romanisim_cat,
        flux_catalog=rpz_cat,
        apply_scaling=args.apply_scaling,
    )
    update_fluxes_cat.write(output_filename, format="ascii.ecsv", overwrite=True)

    print("done")
