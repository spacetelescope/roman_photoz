#!/bin/bash

uncal_asn_files=("$(find . -type f -name "*_uncal.json")")
pids=()
for uncal_file in "${uncal_asn_files[@]}"; do
  echo "Processing file: $uncal_file"
  # spawn background processes for each file
  strun roman_elp "$uncal_file" &
  pids+=($!)
done

# wait for all background processes to finish
for pid in "${pids[@]}"; do
  wait "$pid"
done
