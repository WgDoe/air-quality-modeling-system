#!/bin/csh -f
# Busan SMOKE case 2023capss_cb6 - domestic sea (CAPSS 2023 sea m-file, region 90100)
# Based on example 2022he_cb6_22m/scripts/nonpoint/Annual_nonpt_12US1_2022he_cb6_22m.csh
# Usage (bash, from this folder):  GRID=09KM ./Annual_kor_sea_2023capss_cb6.csh     GRID = 27KM | 09KM | 03KM | 01KM
# Programs can be switched off in ../run_settings.txt

limit stacksize unlimited
setenv SECTOR "kor_sea"
if ($?SLURM_SUBMIT_DIR) then
  cd $SLURM_SUBMIT_DIR
endif
source ../directory_definitions.csh

setenv SPINUP_DURATION "0"
setenv SPINUP_MONTH_END "Y"
setenv EPI_STDATE_TIME "${BASE_YEAR}-01-01 00:00:00.0"
setenv EPI_ENDATE_TIME "${BASE_YEAR}-12-31 23:59:00.0"

## Common inputs
setenv GRIDDESC      "${GE_DAT}/gridding/griddesc_busan_4domains.txt"
setenv COSTCY        "${GE_DAT}/costcy_busan_2023capss_20261022.txt"              # NEW
setenv INVTABLE      "${GE_DAT}/invtable_busan_2017capss_20261021.txt"
setenv SCCDESC       "${GE_DAT}/smkreport/sccdesc_busan_2023capss_20261022.txt"   # NEW
setenv HOLIDAYS      "${GE_DAT}/temporal/holidays_korea_2012_2026_20261021.txt"
setenv MRGDATE_FILES "${INSTALL_DIR}/smoke5.2/scripts/smk_dates/${BASE_YEAR}/smk_merge_dates_${BASE_YEAR}01.txt"   # folder is used; one file per month
setenv GSCNV         "${GE_DAT}/speciation/gscnv_SPECIATE_5_3_fromS2S_20230911_16jun2025_v1.txt"

## Spatial (NEW: CAPSS 2023 1 km cell surrogates, one file per sector and domain)
setenv SRGDESC "${GE_DAT}/gridding/srgdesc_kor_2023capss_${GRID}_20261022.txt"
setenv AGREF   "${GE_DAT}/gridding/agref_kor_sea_2023capss_20261022.txt"   # per-sector AGREF (2026-10-24)
setenv SRGPRO  "${GE_DAT}/gridding/surrogates/kor_2023capss_${GRID}/srg_kor_sea_2023capss_${GRID}.txt"
setenv SMK_DEFAULT_SRGID "902"                 # sector-wide CAPSS 2023 distribution

## Temporal (legacy profiles, UTC-shifted; NEW SCC10 references)
setenv ATREF          "${GE_DAT}/temporal/tref_kor_nonpoint_2023capss_20261022.csv"
setenv ATPRO_MONTHLY  "${GE_DAT}/temporal/tpro_monthly_busan_2020ver_20261021.csv"
setenv ATPRO_WEEKLY   "${GE_DAT}/temporal/tpro_weekly_busan_2020ver_20261021.csv"
setenv ATPRO_HOURLY   "${GE_DAT}/temporal/tpro_hourly_busan_2020ver_UTC_20261021.csv"

## Speciation
setenv GSREFTMP_A "${GE_DAT}/speciation/gsref_kor_nonpoint_2023capss_20261022.csv"   # NEW
setenv GSPROTMP_A "${GE_DAT}/speciation/gspro_static_cmaq_21feb2012_v13.txt"
setenv GSPROTMP_C "${GE_DAT}/speciation/gspro_PM2_5_AE6_Spec_5_3_S2S_20230911_01nov2023_v0.txt"
setenv GSPROTMP_D "${GE_DAT}/speciation/gspro_CB6R3_AE7_criteria_Spec_5_3_S2S_20230911_01nov2023_v0.txt"
setenv GSPROTMP_G "${GE_DAT}/speciation/gspro_nox_hono_pf4_06aug2008_v0.txt"

## Reports (example)
setenv REPCONFIG_INV  "${GE_DAT}/smkreport/repconfig/repconfig_area_inv_2016beta_15nov2021_nf_v3.txt"
setenv REPCONFIG_GRID "${GE_DAT}/smkreport/repconfig/repconfig_area_inv_grid_2016beta_15nov2021_nf_v2.txt"
setenv REPCONFIG_TEMP "${GE_DAT}/smkreport/repconfig/repconfig_area_temporal_2016beta_15nov2021_nf_v1.txt"

## Emission input (NEW)
setenv EMISINV_A "${CASEINPUTS}/kor_sea/kor_sea_CAPSS2023_ff10_20261022.csv"

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
setenv RUN_PYTHON_ANNUAL "Y"
setenv NO_SPC_ZERO_EMIS "Y"
setenv DEFAULT_CONV_FAC_ERROR "Y"
setenv OUTPUT_FORMAT "$EMF_AQM"
setenv SMKMERGE_CUSTOM_OUTPUT "Y"
setenv MRG_REPSTA_YN "N"
setenv MRG_REPCNY_YN "Y"
setenv IOAPI_ISPH "20"
setenv POLLUTANT_CONVERSION "Y"
setenv RENORM_TPROF "Y"
setenv OUTZONE "0"
setenv WEST_HSPHERE "N"
setenv MRG_MARKETPEN_YN "N"
setenv HOURLY_TPROF_BASE "MONTH"
setenv SMK_ARTOPNT_YN "N"

$RUNSCRIPTS/emf/smk_ar_annual_emf.csh $REGION_ABBREV $REGION_IOAPI_GRIDNAME -m "$RUN_MONTHS" $SPINUP_DURATION all
