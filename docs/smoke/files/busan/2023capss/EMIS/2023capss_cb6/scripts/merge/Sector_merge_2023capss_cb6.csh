#!/bin/csh -f
# Busan SMOKE case 2023capss_cb6 - final sector merge (Mrggrid)
# Based on example 2022he_cb6_22m/scripts/merge/Sector_merge_12US1_2022he_cb6_22m_withbeis_withrwc.csh
# Merged (2-D, layer 1): kor_area, kor_mobile, kor_sea, htap_<8 groups>
#   01KM uses sectorlist_2023capss_cb6_01KM (HTAP excluded for 01KM, see 05 guide 8.4)
# Not merged: kor_point (CMAQ inline: stack_groups + inln_mole files in smoke_out)
#             biogenic (CMAQ 5.5 inline MEGAN 3.2)
# Run period (RUN_MONTHS, RUN_SDATE..RUN_EDATE) comes from the MCIP files via ../directory_definitions.csh;
#   smoke5.2/scripts/emf/smk_sectormerge_emf.csh must have the Busan date patch (06 guide 5.2)
# Usage (bash, from this folder):
#   GRID=27KM ./Sector_merge_2023capss_cb6.csh      (GRID = 27KM | 09KM | 03KM | 01KM)

limit stacksize unlimited

setenv SECTOR "mrggrid"

if ($?SLURM_SUBMIT_DIR) then
  cd $SLURM_SUBMIT_DIR
endif

source ../directory_definitions.csh

setenv SPINUP_DURATION "0"
setenv SPINUP_MONTH_END "Y"
setenv EPI_STDATE_TIME "${BASE_YEAR}-01-01 00:00:00.0"
setenv EPI_ENDATE_TIME "${BASE_YEAR}-12-31 23:59:00.0"

## Inputs for all sectors
setenv MRGDATE_FILES "${INSTALL_DIR}/smoke5.2/scripts/smk_dates/${BASE_YEAR}/smk_merge_dates_${BASE_YEAR}01.txt"   # folder is used; one file per month
if ( $GRID == "01KM" ) then
  setenv SECTORLIST "$CASESCRIPTS/sectorlist_2023capss_cb6_01KM"
else
  setenv SECTORLIST "$CASESCRIPTS/sectorlist_2023capss_cb6"
endif

## Parameters (as in the example)
setenv OUTPUT_FORMAT "$EMF_AQM"
setenv PLATFORM "v7.5"
setenv SPC "$EMF_SPC"
setenv EXT ".ncf"
setenv GZIP_OUTPUTS "N"

if (! -e $SECTORLIST) then
  echo "ERROR: sector list not found: $SECTORLIST"; exit 1
endif
grep -q 'Busan patch (2026-11-24)' $RUNSCRIPTS/emf/smk_sectormerge_emf.csh
if ( $status != 0 ) then
  echo "ERROR: Busan date patch not applied: $RUNSCRIPTS/emf/smk_sectormerge_emf.csh"; exit 1
endif

echo "Sector merge, grid $GRID, sector list $SECTORLIST"
echo "Months $RUN_MONTHS, dates $RUN_SDATE - $RUN_EDATE"
$RUNSCRIPTS/emf/smk_sectormerge_emf.csh $REGION_ABBREV -m "$RUN_MONTHS" $SPINUP_DURATION all
exit $status
