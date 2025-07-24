#!/bin/bash

selected_target=${1}
cal_asn_files=("$(find . -type f -name "*${selected_target}*_asn.json")")
pids=()
for cal_file in "${cal_asn_files[@]}"; do
  echo "Processing file: $cal_file"
  # spawn background processes for each file
  strun roman_mos "$cal_file" || echo "Failed to process $cal_file"
  pids+=($!)
done

# wait for all background processes to finish
for pid in "${pids[@]}"; do
  wait "$pid"
done
