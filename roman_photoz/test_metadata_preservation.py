#!/usr/bin/env python
"""
Test script to verify that metadata (units and descriptions) are properly
preserved in parquet files, regardless of whether they are read with
PyArrow or Astropy.

Run this script on a multiband catalog parquet file that has been
processed by the photo-z pipeline. It will check for the presence
of metadata for the key photo-z columns and compare the results
between PyArrow and Astropy reads.

Usage:
  python test_metadata_preservation.py <parquet_file>
"""

import sys
import pyarrow.parquet as pq
from astropy.table import Table

PHOTOZ_COLS = [
    "photoz",
    "photoz_gof",
    "photoz_high68",
    "photoz_high90",
    "photoz_high99",
    "photoz_low68",
    "photoz_low90",
    "photoz_low99",
    "photoz_sed",
]


def print_metadata(col_name, unit, description, found):
    status = "✓ FOUND" if found else "✗ MISSING"
    print(f"\n{col_name}: {status}")
    print(f"  Unit: {unit}")
    desc_short = f"{description[:60]}{'...' if len(description) > 60 else ''}"
    print(f"  Description: {desc_short}")


def extract_metadata(filename, backend):
    if backend == "pyarrow":
        tab = pq.read_table(filename)
        schema = tab.schema
        colnames = schema.names

        def get_field(name):
            return schema.field(name)

        def get_unit(meta):
            return meta.get(b"unit", b"NOT FOUND").decode("utf-8")

        def get_desc(meta):
            return meta.get(b"description", b"NOT FOUND").decode("utf-8")

    else:
        tab = Table.read(filename)
        colnames = tab.colnames

        def get_field(name):
            return tab[name]

        def get_unit(col):
            return str(col.unit) if col.unit is not None else "NOT FOUND"

        def get_desc(col):
            return col.info.description if col.info.description else "NOT FOUND"

    metadata_dict = {}
    for col_name in PHOTOZ_COLS:
        if col_name in colnames:
            field = get_field(col_name)
            if backend == "pyarrow":
                meta = field.metadata if field.metadata else {}
                unit = get_unit(meta)
                description = get_desc(meta)
            else:
                unit = get_unit(field)
                description = get_desc(field)
            found = unit != "NOT FOUND" and description != "NOT FOUND"
            metadata_dict[col_name] = {
                "unit": unit,
                "description": description,
                "found": found,
            }
            print_metadata(col_name, unit, description, found)
        else:
            print(f"\n{col_name}: ✗ COLUMN NOT FOUND")
            metadata_dict[col_name] = {"found": False, "column_exists": False}
    return metadata_dict


def compare_metadata(pyarrow_meta, astropy_meta):
    print("\n" + "=" * 70)
    print("METADATA COMPARISON")
    print("=" * 70)
    all_cols = set(pyarrow_meta.keys()) | set(astropy_meta.keys())
    consistent = True
    for col_name in sorted(all_cols):
        pa_found = pyarrow_meta.get(col_name, {}).get("found", False)
        astropy_found = astropy_meta.get(col_name, {}).get("found", False)
        if pa_found and astropy_found:
            pa_unit = pyarrow_meta[col_name]["unit"]
            astropy_unit = astropy_meta[col_name]["unit"]
            units_match = (
                pa_unit == astropy_unit
                or (
                    pa_unit == "none" and astropy_unit in ["", "dimensionless_unscaled"]
                )
                or (
                    astropy_unit == "none" and pa_unit in ["", "dimensionless_unscaled"]
                )
            )
            desc_match = (
                pyarrow_meta[col_name]["description"]
                == astropy_meta[col_name]["description"]
            )
            if units_match and desc_match:
                print(f"✓ {col_name}: CONSISTENT")
            else:
                print(f"✗ {col_name}: INCONSISTENT")
                if not units_match:
                    print(
                        f"    Unit mismatch: PA='{pa_unit}' vs Astropy='{astropy_unit}'"
                    )
                if not desc_match:
                    print("    Description mismatch")
                consistent = False
        elif pa_found and not astropy_found:
            print(f"⚠ {col_name}: Found in PyArrow but NOT in Astropy")
            consistent = False
        elif astropy_found and not pa_found:
            print(f"⚠ {col_name}: Found in Astropy but NOT in PyArrow")
            consistent = False
        else:
            print(f"✗ {col_name}: NOT FOUND in either")
            consistent = False
    return consistent


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_metadata_preservation.py <parquet_file>")
        print("\nExample:")
        print("  python test_metadata_preservation.py output_catalog.parquet")
        sys.exit(1)
    filename = sys.argv[1]
    print("\n" + "=" * 70)
    print("METADATA PRESERVATION TEST")
    print("=" * 70)
    print(f"\nTesting file: {filename}\n")
    try:
        print("\n" + "=" * 70)
        print("CHECKING METADATA WITH PYARROW")
        print("=" * 70)
        pyarrow_meta = extract_metadata(filename, "pyarrow")
        print("\n" + "=" * 70)
        print("CHECKING METADATA WITH ASTROPY")
        print("=" * 70)
        astropy_meta = extract_metadata(filename, "astropy")
        consistent = compare_metadata(pyarrow_meta, astropy_meta)
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        pyarrow_count = sum(1 for m in pyarrow_meta.values() if m.get("found", False))
        astropy_count = sum(1 for m in astropy_meta.values() if m.get("found", False))
        print("\nPhotoz columns with metadata:")
        print(f"  PyArrow:  {pyarrow_count}/9")
        print(f"  Astropy:  {astropy_count}/9")
        if consistent and pyarrow_count == 9 and astropy_count == 9:
            print("\n✓ SUCCESS: Metadata is fully preserved and consistent!")
            return 0
        elif astropy_count == 9 and pyarrow_count == 0:
            print("\n⚠ WARNING: Metadata only preserved for Astropy reads!")
            print("  PyArrow reads will NOT have column metadata.")
            print("  Consider adding column-level metadata to PyArrow fields.")
            return 1
        elif not consistent:
            print("\n✗ FAIL: Metadata is inconsistent between PyArrow and Astropy!")
            return 2
        else:
            print("\n✗ FAIL: Metadata is incomplete!")
            return 3
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 4


if __name__ == "__main__":
    sys.exit(main())
