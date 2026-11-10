#!/usr/bin/env python3
"""Apply the two 2026-11-10 Busan HTAP fixes to existing SMOKE example/source files.

Usage:
 python3 apply_htap_v32_patches.py --smkinven /path/to/SMOKEv5.3/src/smkinven/smkinven.f \
   --assigns /path/to/CASE/EMIS/smoke5.2/assigns/ASSIGNS.emf

Idempotent and fail-closed. Original files are backed up with .before_htap_v32.
"""
import argparse
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--smkinven", type=Path, required=True)
ap.add_argument("--assigns", type=Path, required=True)
args = ap.parse_args()

def patch(path, old, new, already, label):
    if not path.is_file():
        raise SystemExit(f"ERROR: not found: {path}")
    data = path.read_bytes()
    if already.encode("ascii") in data:
        print(f"Already patched: {label}: {path}")
        return
    if data.count(old.encode("ascii")) != 1:
        raise SystemExit(f"ERROR: expected one unpatched {label} line in {path}, found {data.count(old.encode('ascii'))}; inspect manually")
    backup = path.with_name(path.name + ".before_htap_v32")
    if backup.exists():
        raise SystemExit(f"ERROR: backup exists, inspect before proceeding: {backup}")
    backup.write_bytes(data)
    path.write_bytes(data.replace(old.encode("ascii"), new.encode("ascii"), 1))
    print(f"Patched: {label}: {path}; backup: {backup}")

patch(
    args.smkinven,
    "        LOGICAL         NONPOINT         ! true: importing nonpoint inventory",
    "C.........  Busan patch (2026-11-10): NONPOINT is set only by RDINVDATA (ASCII inventories).\n"
    "C           For gridded NetCDF/I-O API inventories it was left undefined; with gfortran it can\n"
    "C           be .TRUE. and WRINVCHR then reads unallocated CMACT/CNAICS (Segmentation fault).\n"
    "        LOGICAL      :: NONPOINT = .FALSE. ! true: importing nonpoint inventory",
    "LOGICAL      :: NONPOINT = .FALSE.",
    "SMKINVEN NONPOINT initialization",
)
patch(
    args.assigns,
    "       setenv GRID_CRO_2D $MET_ROOT/GRIDCRO2D.\${GRID}.35L.$locyr2$locmon$locday",
    "       # Busan patch (2026-11-10): keep GRID_CRO_2D set in directory_definitions.csh (actual MCIP file name)\n"
    "       if (! $?GRID_CRO_2D ) setenv GRID_CRO_2D $MET_ROOT/GRIDCRO2D.\${GRID}.35L.$locyr2$locmon$locday",
    "if (! $?GRID_CRO_2D ) setenv GRID_CRO_2D",
    "ASSIGNS MCIP GRID_CRO_2D",
)
