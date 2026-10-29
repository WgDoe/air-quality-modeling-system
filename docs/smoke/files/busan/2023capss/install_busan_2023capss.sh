#!/bin/bash
# =====================================================================
# Busan SMOKE 5.3 case 2023capss_cb6 - full input installation
#   * creates the EMIS folder structure (if missing)
#   * copies SMOKE example run system (smoke5.2) if missing
#   * installs all package files (common + CAPSS 2023 domestic inputs + scripts)
#   * copies required example files (speciation, point, report)
#   * removes obsolete files from the 2026-10-22 format test
#   * checks that every file referenced by the sector scripts exists (4 domains)
# Usage:  unzip busan_2023capss_full_setup_20261022.zip -d ~/busan_setup
#         bash ~/busan_setup/install_busan_2023capss.sh
# =====================================================================
set -euo pipefail
CASE_DIR=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901
EX=/home/woogon/CMAQ_MODEL/CASES/SMOKE_TEST/smoke_example_case_v3
PKG=$(cd "$(dirname "$0")" && pwd)
B=$CASE_DIR/EMIS
C=$B/2023capss_cb6
ok=0; ng=0
say() { echo "== $*"; }

say "1. folders"
[ -d $CASE_DIR/MCIP ] || { echo "ERROR: $CASE_DIR/MCIP not found"; exit 1; }
[ -d $EX/ge_dat ]    || { echo "ERROR: example case $EX not found"; exit 1; }
mkdir -p $B/ioapi $B/ge_dat/{gridding/surrogates,speciation,temporal,point,beis,smkreport} \
         $C/inputs $C/scripts/{point,nonpoint,logs} $C/{intermed,reports,logs}
if [ -e "$B/met" ] && [ ! -L "$B/met" ]; then echo "ERROR: met must be a symlink"; exit 1; fi
[ -L "$B/met" ] || ln -s ../MCIP "$B/met"
[ -L "$B/met" ] && [ "$(readlink -f "$B/met")" = "$(realpath "$CASE_DIR/MCIP")" ] || { echo "ERROR: invalid met link"; exit 1; }
ls -ld "$B/met"

say "2. SMOKE example run system (smoke5.2)"
if [ -d $B/smoke5.2/scripts/emf ]; then echo "   already installed"
else cp -a $EX/smoke5.2/. $B/smoke5.2/ && echo "   copied from example"; fi

say "3. package files"
cp -r $PKG/EMIS/. $B/
chmod +x $C/scripts/point/*.csh $C/scripts/nonpoint/*.csh
echo "   $(cd $PKG && find EMIS -type f | wc -l) files installed"

say "4. example files (unchanged)"
copy_example() {
  local src=$1 dst=$2
  [ -f "$src" ] || { echo "ERROR: missing example input: $src"; exit 1; }
  if [ -e "$dst" ]; then
    cmp -s "$src" "$dst" || { echo "ERROR: existing example differs: $dst (back up and resolve before reinstall)"; exit 1; }
  else
    cp "$src" "$dst"
  fi
}
for f in gscnv_SPECIATE_5_3_fromS2S_20230911_16jun2025_v1.txt gspro_static_cmaq_21feb2012_v13.txt \
         gspro_PM2_5_AE6_Spec_5_3_S2S_20230911_01nov2023_v0.txt \
         gspro_CB6R3_AE7_criteria_Spec_5_3_S2S_20230911_01nov2023_v0.txt gspro_nox_hono_pf4_06aug2008_v0.txt; do
  copy_example "$EX/ge_dat/speciation/$f" "$B/ge_dat/speciation/$f"
done
for f in pelvconfig_elevate_everything_17apr2020_v0.txt pstk_13nov2018_v1.txt; do
  copy_example "$EX/ge_dat/point/$f" "$B/ge_dat/point/$f"
done
for f in orisdesc_04dec2006_v0.txt naicsdesc_20220222_29feb2024_nf_v1.txt; do
  copy_example "$EX/ge_dat/smkreport/$f" "$B/ge_dat/smkreport/$f"
done
[ -d $B/ge_dat/smkreport/repconfig ] || cp -r $EX/ge_dat/smkreport/repconfig $B/ge_dat/smkreport/
echo "   done"

say "5. remove obsolete files (format test 2026-10-22, East Asia 2010)"
# Preserve existing results unless cleanup is explicitly requested.
if [ "${BUSAN_REMOVE_OBSOLETE:-NO}" = YES ]; then
  expected=/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6
  [ "$(realpath -e -- "$C")" = "$expected" ] && [ ! -L "$C" ] || { echo "ERROR: unsafe cleanup path"; exit 1; }
  for target in "$C/intermed/09KM/kor_point" "$C/inputs/kor_point/scc10_reference_map_20261022.csv" "$C/inputs/asia"; do
    resolved=$(realpath -m -- "$target") || exit 1
    case "$resolved" in "$expected"/*) ;; *) echo "ERROR: unsafe cleanup target: $target"; exit 1 ;; esac
  done
  echo "WARNING: deleting old point intermediates and obsolete inputs under $C"
  rm -rf -- "$C/intermed/09KM/kor_point" "$C/inputs/kor_point/scc10_reference_map_20261022.csv" "$C/inputs/asia" || exit 1
else
  echo "WARNING: old results preserved; set BUSAN_REMOVE_OBSOLETE=YES only after backup to remove obsolete files."
fi
echo "   done"

say "6. check files referenced by sector scripts"
for g in 27KM 09KM 03KM 01KM; do
  python3 "$C/scripts/utils/mcip_period.py" "$CASE_DIR/MCIP/$g" > /dev/null
done
PERIOD=$(python3 "$C/scripts/utils/mcip_period.py" "$CASE_DIR/MCIP/09KM")
YR=$(printf '%s\n' "$PERIOD" | awk '{print $3}')
[[ "$YR" =~ ^[0-9]{4}$ ]] || { echo "ERROR: invalid MCIP year"; exit 1; }
echo "   run period from MCIP: $PERIOD"
CHECK_FILE=$(mktemp)
trap 'rm -f -- "$CHECK_FILE"' EXIT
for s in $C/scripts/point/*.csh $C/scripts/nonpoint/*.csh; do
  for g in 27KM 09KM 03KM 01KM; do
    grep -E '^setenv [A-Z_0-9]+ +"\$\{(GE_DAT|CASEINPUTS|INSTALL_DIR)\}' $s | awk '{print $2, $3}' | tr -d '"' |
    while read v p; do
      f=$(echo "$p" | sed -e "s|\${GE_DAT}|$B/ge_dat|" -e "s|\${CASEINPUTS}|$C/inputs|" -e "s|\${INSTALL_DIR}|$B|" -e "s|\${GRID}|$g|g" -e "s|\${BASE_YEAR}|$YR|g")
      [ -e "$f" ] || echo "   MISSING  $(basename $s)  $g  $v  $f"
    done
  done
done > "$CHECK_FILE"
if [ -s "$CHECK_FILE" ]; then cat "$CHECK_FILE"; echo "ERROR: required inputs missing"; exit 1
else echo "   all referenced files exist (5 scripts x 4 domains)"; fi
for f in $B/smoke5.2/scripts/emf/smk_pt_annual_onetime_emf.csh $B/smoke5.2/scripts/emf/smk_pt_annual_byday_emf.csh \
         $B/smoke5.2/scripts/emf/smk_ar_annual_emf.csh $C/scripts/directory_definitions.csh $C/scripts/run_settings.txt; do
  [ -e "$f" ] || { echo "ERROR: MISSING $f"; exit 1; }
  echo "   ok  $(basename "$f")"
done

say "7. summary"
du -sh $B/ge_dat/gridding/surrogates/kor_2023capss_* 2>/dev/null
find $C/inputs -name "*ff10*" -exec ls -l {} \; | awk '{print "   " $5, $9}'
echo "installation finished: $(date '+%F %T')"
