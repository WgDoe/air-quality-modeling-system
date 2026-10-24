#!/bin/csh -f
# Busan SMOKE case: based on SMOKE-ExampleCase-v3 directory_definitions.csh
# Location: CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts

if (! $?SECTOR ) setenv SECTOR ''

## Domain (MCIP grid name: 27KM, 09KM, 03KM, 01KM)
if (! $?GRID ) setenv GRID "09KM"

setenv INSTALL_DIR "/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS"
setenv MET_ROOT    "$INSTALL_DIR/met/$GRID"
setenv MET_ROOT_3D $MET_ROOT

setenv CASE "2023capss_cb6"

setenv REGION                "Busan $GRID"
setenv REGION_ABBREV         "$GRID"      # affects filename labeling
setenv REGION_IOAPI_GRIDNAME "$GRID"      # must match GRIDDESC
setenv EMF_SPC               "cmaq_cb6ae7"

setenv SMOKE_LOCATION /home/woogon/CMAQ_MODEL/SMOKEv5.3/subsys/smoke/Linux2_x86_64gfort10
setenv IOAPI_LOCATION /home/woogon/CMAQ_MODEL/libs/ioapi-3.2-20200828/Linux2_x86_64gfort10

setenv MODEL_LABEL  "SMOKE5.2"
setenv PROJECT      "$CASE"
setenv OUT_ROOT     "$INSTALL_DIR"
setenv PROJECT_ROOT "$INSTALL_DIR"
setenv CASE_ROOT    "$PROJECT_ROOT/$CASE"
setenv IMD_ROOT     "$PROJECT_ROOT/$CASE/intermed/$GRID"
setenv DAT_ROOT     $PROJECT_ROOT
setenv SMK_HOME     "$INSTALL_DIR"
setenv CASEINPUTS   "$INSTALL_DIR/$CASE/inputs"
setenv GE_DAT       "$INSTALL_DIR/ge_dat"
setenv CASESCRIPTS  "$PROJECT_ROOT/$CASE/scripts"
setenv RUNSCRIPTS   "$INSTALL_DIR/smoke5.2/scripts"
setenv RUNSET       "$CASESCRIPTS/run_settings.txt"
setenv ASSIGNS_FILE "$INSTALL_DIR/smoke5.2/assigns/ASSIGNS.emf"

setenv EMF_CLIENT false
setenv EMF_AQM "CMAQ v5.2"
setenv EMF_JOBNAME "Annual_area"
setenv EMF_SCRIPTDIR  "${CASESCRIPTS}"
setenv EMF_SCRIPTNAME "${CASESCRIPTS}/${EMF_JOBNAME}.csh"
setenv EMF_LOGNAME    "${CASESCRIPTS}/logs/$EMF_SCRIPTNAME.log"
setenv EMF_JOBKEY "busan_2023capss_cb6"
setenv EMF_LOGGERPYTHONDIR "$EMF_SCRIPTDIR/case_logs_python"
setenv EMF_JOBID "1"

## Run period from MCIP (all domains share the same period; read from the selected domain)
##   RUN_SDATE/RUN_EDATE (YYYYDDD) limit the "all" dates in smoke5.2/scripts/run/set_days_v5.csh (Busan patch)
set _per = ( `python3 $CASESCRIPTS/utils/mcip_period.py $MET_ROOT` )
if ( $#_per < 4 ) then
  echo "ERROR: cannot read run period from MCIP files in $MET_ROOT"; exit 1
endif
setenv RUN_SDATE  $_per[1]
setenv RUN_EDATE  $_per[2]
setenv BASE_YEAR  $_per[3]
setenv RUN_MONTHS "$_per[4-]"
echo "Run period from MCIP: $RUN_SDATE - $RUN_EDATE (months: $RUN_MONTHS)"
