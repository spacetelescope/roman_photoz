#!/bin/bash

filter_list=${1}
pids=()
for x in "${filter_list[@]}"; do
  echo "Processing input file: $x"
  skycell_asn \
    r*_"${x}"_cal.asdf \
    -o r00001
  pids+=($!)
done

for pid in "${pids[@]}"; do
  wait "$pid"
done
