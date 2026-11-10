#!/bin/csh -f
# Busan SMOKE case 2023capss_cb6 - foreign anthropogenic emissions, HTAP_v3.2 2020 (gridded NetCDF inventory)
# Based on example 2022he_cb6_22m/scripts/htap/Annual_htap_12LISTOS.csh
# Inputs made by make_busan_htap_v32_inputs.py (window 90-162E 18-56N, South Korea = CAPSS 2023 coverage set to 0)
# Usage (bash, from this folder):
#   GRID=27KM HTAP_GROUP=ENERGY ./Annual_htap_2023capss_cb6.csh
#   GRID       = 27KM | 09KM | 03KM | 01KM
#   HTAP_GROUP = INTSHIP | AVIATION | ENERGY | INDUSTRY | TRANSPORT | RESIDENT | WASTE | AGRICULTURE | ALL
#                one SMOKE sector per group: htap_<group> (lower case)
# Programs can be switched off in ../run_settings.txt

limit stacksize unlimited
limit memoryuse unlimited
if (! $?HTAP_GROUP ) setenv HTAP_GROUP "ENERGY"
setenv SECTOR "htap_`echo $HTAP_GROUP | tr '[:upper:]' '[:lower:]'`"
if ($?SLURM_SUBMIT_DIR) then
  cd $SLURM_SUBMIT_DIR
endif
source ../directory_definitions.csh

setenv SPINUP_DURATION "0"
setenv SPINUP_MONTH_END "Y"
setenv EPI_STDATE_TIME "${BASE_YEAR}-01-01 00:00:00.0"
setenv EPI_ENDATE_TIME "${BASE_YEAR}-12-31 23:59:00.0"

## Common inputs (same as domestic sectors)
setenv GRIDDESC      "${GE_DAT}/gridding/griddesc_busan_4domains.txt"
setenv INVTABLE      "${GE_DAT}/invtable_busan_htap_20261110.txt"   # domestic INVTABLE + PEC/POC (made by the HTAP generator)
setenv HOLIDAYS      "${GE_DAT}/temporal/holidays_korea_2012_2026_20261021.txt"
setenv MRGDATE_FILES "${INSTALL_DIR}/smoke5.2/scripts/smk_dates/${BASE_YEAR}/smk_merge_dates_${BASE_YEAR}01.txt"   # folder is used; one file per month
setenv AGREF         "${GE_DAT}/gridding/agref_kor_area_2023capss_20261022.txt"   # not used by gridded inventories (set as in the example)

## Emission input (NEW: HTAP_v3.2 2020, Busan window)
setenv EMISLST "${CASEINPUTS}/htap/arinv.HTAPv32.${HTAP_GROUP}.lst"
setenv ARINV   "$EMISLST"

## Temporal (example HTAPv3 profiles; NEW rows for detailed sectors in TREF)
setenv ATREF         "${GE_DAT}/EDGAR/HTAPv32_profiles/tref_HTAPv32_busan_20261110.txt"
setenv ATPRO_HOURLY  "${GE_DAT}/EDGAR/HTAPv32_profiles/HTAP_2011_BaseA_tpro_hourly_24oct2022_nf_v1"
setenv ATPRO_WEEKLY  "${GE_DAT}/EDGAR/HTAPv32_profiles/HTAP_2011_BaseA_tpro_weekly_24oct2022_nf_v1"
setenv ATPRO_MONTHLY "${GE_DAT}/EDGAR/HTAPv32_profiles/HTAP_2011_BaseA_tpro_monthly_24oct2022_nf_v1"

## Speciation (example HTAPv3 CB6 profiles; NEW rows for detailed sectors in GSREF)
##   PM as in the EPA HTAP design: PEC/POC from HTAP BC/OC (profile 0), PM2_5 = PM2.5 - BC - OC ('other' profiles)
setenv GSREF "${GE_DAT}/EDGAR/HTAPv32_profiles/gsref_HTAPv32_busan_20261110.txt"
setenv GSPRO "${GE_DAT}/EDGAR/HTAPv32_profiles/gspro_HTAP_CB06_from_2011ei_corrected_20feb2024_nf_v1.txt"
setenv GSCNV "${GE_DAT}/EDGAR/HTAPv32_profiles/gscnv_edgar_HTAPv3_03Apr2024.txt"

## Country codes and time zones by 0.1 deg cell (example files; GRIDMASK cut to the Busan window)
setenv GEOCODE_LEVEL1 "${GE_DAT}/EDGAR/geocode1_edgar.txt"
setenv GEOCODE_LEVEL2 "${GE_DAT}/EDGAR/geocode2_edgar.txt"
setenv GEOCODE_LEVEL3 "${GE_DAT}/EDGAR/geocode3_edgar.txt"
setenv GEOCODE_LEVEL4 "${GE_DAT}/EDGAR/geocode4_edgar.txt"
setenv GRIDMASK       "${GE_DAT}/EDGAR/GRIDMASK_EDGAR_busan_window.ncf"

## Parameters (example htap settings; changed: WEST_HSPHERE N, NETCDF_INV_YEAR 2020, M/L_TYPE all as domestic)
setenv PLATFORM "v9.2"
setenv SPC "$EMF_SPC"
setenv FILL_ANNUAL "N"
setenv SMKINVEN_FORMULA "PMC=PM10-PM2_5"
setenv SMK_DEFAULT_SRGID "100"
setenv REPORT_DEFAULTS "Y"
setenv SMK_AVEDAY_YN "N"
setenv SMK_MAXWARNING "10"
setenv SMK_MAXERROR "10000"
setenv FULLSCC_ONLY "Y"
setenv RUN_HOLIDAYS "N"
setenv RAW_DUP_CHECK "N"
setenv SMK_SPECELEV_YN "Y"
setenv SMK_PING_METHOD "0"
setenv INLINE_MODE "only"
setenv RUN_PYTHON_ANNUAL "Y"
setenv NO_SPC_ZERO_EMIS "Y"
setenv MTMP_OUTPUT_YN "N"
setenv DEFAULT_CONV_FAC_ERROR "Y"
setenv OUTPUT_FORMAT "$EMF_AQM"
setenv SMKMERGE_CUSTOM_OUTPUT "Y"
setenv MRG_REPSTA_YN "N"
setenv IOAPI_ISPH "20"
setenv POLLUTANT_CONVERSION "Y"
setenv RENORM_TPROF "Y"
setenv OUTZONE "0"
setenv MRG_REPCNY_YN "Y"
setenv WEST_HSPHERE "N"
setenv MRG_MARKETPEN_YN "N"

## Gridded NetCDF inventory
setenv IMPORT_GRDNETCDF_YN Y               # import HTAP/EDGAR gridded inventories
setenv NETCDF_POL_UNIT 'kg m-2 s-1'        # unit of the HTAP variables
setenv NETCDF_INV_YEAR 2020                # HTAP_v3.2 inventory year
setenv IMPORT_GRDIOAPI_YN N
setenv SMK_BASEYR_OVERRIDE 0
setenv USE_EXP_GEO_CODES Y                 # country codes from GRIDMASK/GEOCODE files instead of COSTCY

setenv SMK_PROCESS_HAPS "NONE"
setenv M_TYPE "all"
setenv L_TYPE "all"

if (! -e $EMISLST) then
  echo "ERROR: list file not found: $EMISLST"; exit 1
endif
echo "HTAP group $HTAP_GROUP -> sector $SECTOR, grid $GRID"
$RUNSCRIPTS/emf/smk_ar_gridded_annual_emf.csh $REGION_ABBREV $REGION_IOAPI_GRIDNAME -m "$RUN_MONTHS" $SPINUP_DURATION all
