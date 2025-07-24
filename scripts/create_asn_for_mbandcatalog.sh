#!/bin/bash

skycell_id=${1}
asn_from_list \
  r*_"${skycell_id}"_f*_coadd.asdf \
  -o mbcat_"${skycell_id}"_wfi01.json \
  --product-name r0000101001001001001_0001_wfi01
