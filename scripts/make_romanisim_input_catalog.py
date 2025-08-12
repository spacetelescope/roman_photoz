from romanisim.catalog import make_cosmos_galaxies
from astropy.coordinates import SkyCoord
from roman_photoz.utils import get_roman_filter_list


if __name__ == "__main__":
    ra_ref = 270.0  # RA in degrees
    dec_ref = 66.0  # Dec in degrees
    output_catalog_filename = "romanisim_input_catalog.ecsv"
    output_catalog_format = "ascii.ecsv"

    bandpasses = get_roman_filter_list()
    # romanisim uses uppercase bandpass names
    bandpasses = [bp.upper() for bp in bandpasses]

    coords = SkyCoord(ra=ra_ref, dec=dec_ref, unit="deg", frame="icrs")

    # the result from this method will be in maggies (1 maggy = 3631 Jy)
    catalog = make_cosmos_galaxies(
        coord=coords, bandpasses=bandpasses, seed=42, radius=1.0, cat_area=1.0
    )

    catalog.write(output_catalog_filename, format=output_catalog_format, overwrite=True)

    print(f"Catalog saved to {output_catalog_filename}. Total sources: {len(catalog)}.")
