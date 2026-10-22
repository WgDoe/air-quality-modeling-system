#!/bin/csh -f
# Busan SMOKE case 2023capss_cb6 - domestic point sector (CAPSS 2023), daily programs (Temporal, Smkmerge by day)
# Based on example 2022he_cb6_22m/scripts/point/Annual_ptnonipm_onetime_12US1_2022he_cb6_22m.csh
# Usage (from this folder):  GRID=09KM ./Annual_kor_point_daily_2023capss_cb6.csh   (bash)
# Programs can be switched off in ../run_settings.txt

limit stacksize unlimited

setenv SECTOR "kor_point"

if ($?SLURM_SUBMIT_DIR) then
  cd $SLURM_SUBMIT_DIR
endif

source ../directory_definitions.csh

## Months / spinup / modeling year (meteorological year)
setenv RUN_MONTHS "9"
setenv SPINUP_DURATION "0"
setenv SPINUP_MONTH_END "Y"
setenv BASE_YEAR "2026"
setenv EPI_STDATE_TIME "${BASE_YEAR}-01-01 00:00:00.0"
setenv EPI_ENDATE_TIME "${BASE_YEAR}-12-31 23:59:00.0"

## Inputs for all sectors
setenv GRIDDESC      "${GE_DAT}/gridding/griddesc_busan_4domains.txt"
setenv COSTCY        "${GE_DAT}/costcy_busan_2023capss_20261022.txt"              # NEW: CAPSS 2023 regions
setenv INVTABLE      "${GE_DAT}/invtable_busan_2017capss_20261021.txt"            # same 8 pollutants
setenv SCCDESC       "${GE_DAT}/smkreport/sccdesc_busan_2023capss_20261022.txt"   # NEW
setenv HOLIDAYS      "${GE_DAT}/temporal/holidays_korea_2012_2026_20261021.txt"
setenv MRGDATE_FILES "${INSTALL_DIR}/smoke5.2/scripts/smk_dates/2026/smk_merge_dates_202609.txt"
setenv GSCNV         "${GE_DAT}/speciation/gscnv_SPECIATE_5_3_fromS2S_20230911_16jun2025_v1.txt"
setenv ORISDESC      "${GE_DAT}/smkreport/orisdesc_04dec2006_v0.txt"              # example (report only)
setenv NAICSDESC     "${GE_DAT}/smkreport/naicsdesc_20220222_29feb2024_nf_v1.txt" # example (report only)

## Point source parameters
setenv PELVCONFIG    "${GE_DAT}/point/pelvconfig_elevate_everything_17apr2020_v0.txt"  # example: all sources elevated
setenv PSTK          "${GE_DAT}/point/pstk_13nov2018_v1.txt"                           # example defaults (stack gaps already filled in FF10)

## Temporal (legacy 2020-version profiles, hourly UTC-shifted; COSTCY GMT)
setenv PTREF         "${GE_DAT}/temporal/tref_kor_point_2023capss_20261022.csv"        # NEW
setenv PTPRO_MONTHLY "${GE_DAT}/temporal/tpro_monthly_busan_2020ver_20261021.csv"
setenv PTPRO_WEEKLY  "${GE_DAT}/temporal/tpro_weekly_busan_2020ver_20261021.csv"
setenv PTPRO_HOURLY  "${GE_DAT}/temporal/tpro_hourly_busan_2020ver_UTC_20261021.csv"

## Speciation
setenv GSREFTMP_A "${GE_DAT}/speciation/gsref_kor_point_2023capss_20261022.csv"        # NEW: SCC10 -> legacy profiles
setenv GSPROTMP_A "${GE_DAT}/speciation/gspro_static_cmaq_21feb2012_v13.txt"
setenv GSPROTMP_C "${GE_DAT}/speciation/gspro_PM2_5_AE6_Spec_5_3_S2S_20230911_01nov2023_v0.txt"
setenv GSPROTMP_D "${GE_DAT}/speciation/gspro_CB6R3_AE7_criteria_Spec_5_3_S2S_20230911_01nov2023_v0.txt"
setenv GSPROTMP_G "${GE_DAT}/speciation/gspro_nox_hono_pf4_06aug2008_v0.txt"

## Reports (example)
setenv REPCONFIG_INV  "${GE_DAT}/smkreport/repconfig/repconfig_point_inv_2016beta_13nov2023_v2.txt"
setenv REPCONFIG_GRID "${GE_DAT}/smkreport/repconfig/repconfig_point_invgrid_2011platform_11aug2014_v0.txt"
setenv REPCONFIG_TEMP "${GE_DAT}/smkreport/repconfig/repconfig_point_temporal_2016beta_15nov2021_nf_v1.txt"

## Emission inputs
setenv EMISINV_A "${CASEINPUTS}/kor_point/kor_point_CAPSS2023_ff10_20261022.csv"      # NEW: CAPSS 2023 point (make_busan_2023_domestic_inputs.py)

## Parameters
setenv L_TYPE "all"
setenv M_TYPE "all"
setenv M3XTRACT_LENGTH "240000"
setenv PLATFORM "v9.2"
setenv SPC "$EMF_SPC"
setenv FILL_ANNUAL "N"
setenv SMKINVEN_FORMULA "PMC=PM10-PM2_5"
setenv REPORT_DEFAULTS "Y"
setenv SMK_AVEDAY_YN "N"
setenv SMK_MAXWARNING "10"
setenv SMK_MAXERROR "10000"
setenv FULLSCC_ONLY "Y"
setenv RUN_HOLIDAYS "Y"
setenv RAW_DUP_CHECK "N"
setenv SMK_SPECELEV_YN "Y"
setenv SMK_PING_METHOD "0"
setenv INLINE_MODE "only"                 # CMAQ inline plume rise
setenv RUN_PYTHON_ANNUAL "Y"
setenv NO_SPC_ZERO_EMIS "Y"
setenv DEFAULT_CONV_FAC_ERROR "Y"
setenv OUTPUT_FORMAT "$EMF_AQM"
setenv SMKMERGE_CUSTOM_OUTPUT "Y"
setenv MRG_REPSTA_YN "N"
setenv IOAPI_ISPH "20"
setenv POLLUTANT_CONVERSION "Y"
setenv RENORM_TPROF "Y"
setenv OUTZONE "0"
setenv MRG_REPCNY_YN "Y"
setenv WEST_HSPHERE "N"                   # Korea: eastern hemisphere
setenv MRG_MARKETPEN_YN "N"
setenv MRG_BYDAY "P"

$RUNSCRIPTS/emf/smk_pt_annual_byday_emf.csh $REGION_ABBREV $REGION_IOAPI_GRIDNAME -m "$RUN_MONTHS" $SPINUP_DURATION byday
