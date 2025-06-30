from romanisim.catalog import make_galaxies
from astropy.coordinates import SkyCoord


if __name__ == "__main__":
    ra_ref = 270.0  # RA in degrees
    dec_ref = 66.0  # Dec in degrees
    output_catalog_filename = "romanisim_input_catalog.ecsv"
    output_catalog_format = "ascii.ecsv"

    bandpasses = ["F062", "F087", "F106", "F129", "F158", "F184", "F213", "F146"]
    coords = SkyCoord(ra=ra_ref, dec=dec_ref, unit="deg", frame="icrs")

    catalog = make_galaxies(coords, n=75000, bandpasses=bandpasses, seed=42, radius=5.0)

    catalog.write(output_catalog_filename, format=output_catalog_format, overwrite=True)

    print(f"Catalog saved to {output_catalog_filename}. Total sources: {len(catalog)}.")
