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
    # Check if flux_catalog is invalid to provide a better error message
    if flux_catalog is None or len(flux_catalog) == 0:
        raise ValueError(
            "flux_catalog is invalid. This likely indicates that the SimulatedCatalog.process() "
            "method did not return a catalog. Make sure to call process(return_catalog=True) "
            "when you need the catalog returned instead of saved to file."
        )

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
