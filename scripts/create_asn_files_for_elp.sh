#!/bin/bash

filter_list=${1}
pids=()
for x in "${filter_list[@]}"; do
  echo "Processing input file: $x"
  asn_from_list \
    -o "cosmos_catalog_270_66_wfi01_${x}_uncal.json" \
    --product-name "r0000101001001001001_0001_${x}_uncal" \
    "r0000101001001001001_0001_wfi01_${x}_uncal.asdf"
  pids+=($!)
done

for pid in "${pids[@]}"; do
  wait "$pid"
done
