# 1 - create romanisim input catalog
# (romanisim.make_galaxies(n))
# python -m make_romanisim_input_catalog

# 2 - create roman_photoz simulated catalog (using COSMOS templates and lephare.prepare method)
# (roman_photoz.create_simulated_catalog.py -- no errors added to the simulated catalog)
# python -m roman_photoz.create_simulated_catalog --output-path .

# 3 - update catalog from step 1 with the fluxes from the catalog from step 2
# (roman_photoz.update_romanisim_catalog_fluxes.py)
# python -m update_romanisim_catalog_fluxes --target-catalog romanisim_input_catalog.ecsv --flux-catalog roman_simulated_catalog.parquet --output-filename romanisim_input_catalog_fluxes_updated.ecsv

# 4 - run romanisim-make-image and provide the catalog from step 3
filter_list=("F062" "F087" "F106" "F129" "F158" "F184" "F213" "F146")
for filter in "${filter_list[@]}"; do
  echo "Processing filter: $filter"
  romanisim-make-image \
    --radec 270.0 66.0 \
    --level 1 \
    --sca -1 \
    --bandpass "$filter" \
    --catalog "romanisim_input_catalog.ecsv" \
    --stpsf \
    --usecrds \
    --ma_table_number 109 \
    --date 2027-06-01T00:00:00 \
    --rng_seed 1 \
    --drop-extra-dq \
    "r0000101001001001001_0001_{}_{bandpass}_uncal.asdf" &
done

# 5 - create association files
./create_asn_files.sh
