#!/usr/bin/env bash
# 도메인별 CMAQ 인라인 MEGAN 3.2 입력(MEGAN_CTS/EFS/LDF) 생성
#   사용법: bash run_megan_domain.sh <사례폴더> <도메인> [<도메인> ...]
#   예    : WRF_START=2026-08-31_00:00:00 MCIP_STAMP=2026083100 bash run_megan_domain.sh "$C" 01KM 03KM
#   선행  : setup_megan32.sh 완료, 사례폴더의 WRF/wrfout_<dNN>_* 와 MCIP/<도메인>/ 존재
#   결과  : <사례>/EMIS/MEGAN/<도메인>/  중간 산출물(CSV·기록)
#           $MODEL/DATA/EMIS/MEGAN/GRID/<격자>_<도메인>/  최종 NetCDF 3개 + GRIDDESC + md5
set -euo pipefail

(( $# >= 2 )) || { echo "Usage: WRF_START=<YYYY-MM-DD_HH:MM:SS> MCIP_STAMP=<YYYYMMDDHH> bash $0 CASE DOMAIN [DOMAIN ...]" >&2; exit 2; }
: "${WRF_START:?Set WRF_START to the timestamp in the WRF filename}"
: "${MCIP_STAMP:?Set MCIP_STAMP to the timestamp in the MCIP filename}"
[[ $WRF_START =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}:[0-9]{2}:[0-9]{2}$ && $MCIP_STAMP =~ ^[0-9]{10}$ ]] ||
  { echo "Invalid WRF_START or MCIP_STAMP format" >&2; exit 2; }

MODEL=${MODEL:-$HOME/CMAQ_MODEL}
FILES=$(cd -P "$(dirname "$0")" && pwd)
CASE=$(cd -P "$1" && pwd); shift
PROGRAM=$MODEL/MEGAN
RAW=$MODEL/DATA/EMIS/MEGAN
PREP=$PROGRAM/MEGAN32_Prep_Code_Jan_2022
WORK=$CASE/EMIS/MEGAN
LOG=$CASE/LOG
mkdir -p "$WORK/EFP/outputs" "$WORK/EFP/database" "$LOG"
ln -sfn "$PROGRAM/MEGEFP32/src" "$WORK/EFP/src"

for DOM in "$@"; do
  case $DOM in                      # 도메인 ↔ WRF 영역 번호
    27KM) WRFD=d01 ;; 09KM) WRFD=d02 ;; 03KM) WRFD=d03 ;; 01KM) WRFD=d04 ;;
    *) echo "unknown domain $DOM"; exit 1 ;;
  esac
  MC=$CASE/MCIP/$DOM
  NML=$MC/namelist.mcip
  # MCIP이 WRF 격자에서 잘라낸 창(btrim=-1일 때 x0,y0,ncolsin,nrowsin)을 그대로 쓴다
  val() { awk -F= -v k="$1" 'tolower($1) ~ "^ *"k" *$" {gsub(/[ ,]/,"",$2); print $2; exit}' "$NML"; }
  [[ $(val btrim) == -1 ]] || { echo "$NML: btrim=-1 이 아님 - x0/y0 직접 확인 필요"; exit 1; }
  X0=$(val x0); Y0=$(val y0); NX=$(val ncolsin); NY=$(val nrowsin)
  GRIDCRO=$MC/GRIDCRO2D_${DOM}.$MCIP_STAMP.nc
  GRIDDESC=$MC/GRIDDESC_$DOM
  WRF=$CASE/WRF/wrfout_${WRFD}_$WRF_START
  for input in "$NML" "$GRIDCRO" "$GRIDDESC" "$WRF"; do
    [[ -f $input && -r $input ]] || { echo "Missing or unreadable input: $input" >&2; exit 1; }
  done
  D=$WORK/$DOM
  mkdir -p "$D/filled"
  echo "== $DOM  WRF=$(basename "$WRF")  window x0=$X0 y0=$Y0 ${NX}x${NY}  $(date -Is)"

  # ---- 1) 생태유형 / 생육형 / 캐노피 유형 (Fortran 전처리기)
  cat > "$D/ecotype.inp" <<CFG
&control
 start_lai_mnth=1, end_lai_mnth=12,
 wrffile='$WRF', megan_dir='$RAW', out_dir='$D',
 inpname='EVT3d.nc', varname='EVT', fillvalue='65535',
/
&windowdefs
 x0=$X0,y0=$Y0,ncolsin=$NX,nrowsin=$NY,
/
CFG
  cat > "$D/growthform.inp" <<CFG
&control
 start_lai_mnth=1, end_lai_mnth=12,
 wrffile='$WRF', megan_dir='$RAW/GFv7nc', out_dir='$D',
/
&growthform
 treefilename='TC30s7.nc', treevarname='TCpercent', treefillvalue='127',
 shrubfilename='SC30s7_SCpercent.nc', shrubvarname='SCpercent', shrubfillvalue='127',
 grassfilename='GC30s7.nc', grassvarname='GCpercent', grassfillvalue='127',
 cropfilename='CC30s7.nc', cropvarname='CCpercent', cropfillvalue='127',
/
&windowdefs
 x0=$X0,y0=$Y0,ncolsin=$NX,nrowsin=$NY,
/
CFG
  cat > "$D/cantype.inp" <<CFG
&control
 start_lai_mnth=1, end_lai_mnth=12,
 wrffile='$WRF', megan_dir='$RAW/cantype_EA', out_dir='$D',
/
&cantype
 treefilename='TC30s7.nc', treevarname='TCpercent', treefillvalue='127',
 NTfilename='NTfrac_EA.nc', NTvarname='NTfrac', NTfillvalue='-1',
 TRTfilename='tropfrac_EA.nc', TRTvarname='tropfrac', TRTfillvalue='-1',
 shrubfilename='SC30s7.nc', shrubvarname='SCpercent', shrubfillvalue='127',
 grassfilename='GC30s7.nc', grassvarname='GCpercent', grassfillvalue='127',
 cropfilename='CC30s7.nc', cropvarname='CCpercent', cropfillvalue='127',
/
&windowdefs
 x0=$X0,y0=$Y0,ncolsin=$NX,nrowsin=$NY,
/
CFG
  for step in ecotype:ecotype growthform:grwform_lowmem cantype:cantype; do
    inp=${step%%:*}; exe=${step##*:}
    echo "   $inp  $(date -Is)"
    /usr/bin/time -v "$PREP/prepmegan4cmaq_$exe.x" < "$D/$inp.inp" > "$LOG/megan_${DOM}_$inp.log" 2>&1
    grep -q 'megan_bio_emiss is done' "$LOG/megan_${DOM}_$inp.log"
  done
  N=$((NX*NY))
  [[ $(( $(wc -l < "$D/CT3.csv") - 1 )) -eq $N ]]
  [[ $(( $(wc -l < "$D/grid_growth_form.csv") - 1 )) -eq $N ]]

  # ---- 2) 생태유형 결측(65535) 채우기
  python3 "$FILES/fill_megan_ecotype.py" "$D/grid_ecotype.csv" "$D/grid_growth_form.csv" \
      "$GRIDCRO" "$NX" "$NY" "$D/filled/grid_ecotype.csv" "$D/filled/ecotype_fill_record.csv" \
      | tee "$LOG/megan_${DOM}_ecotype_fill.log"

  # ---- 3) 배출계수·광의존 비율 (EFP)
  SCEN=$DOM
  python3 "$FILES/make_efp_inputs.py" "$SCEN" "$D/filled/grid_ecotype.csv" "$D/grid_growth_form.csv" \
      "$WORK/EFP" "$PROGRAM/MEGEFP32" "$RAW/efp_utf8" | tee "$LOG/megan_${DOM}_efp_inputs.log"
  rm -f "$WORK/EFP/database/M3GEFP_database.$SCEN.db" "$WORK/EFP/outputs/OutputGridEF.$SCEN.csv"
  # 배출계수 없는 수종이 있으면 EFP가 계속 여부(Y/N)를 묻는다 → Y(0으로 처리). 목록은 위 로그에 남음
  (cd "$WORK/EFP" && echo Y | python3 "MEGAN_EFP_$SCEN.py") > "$LOG/megan_${DOM}_efp.log" 2>&1
  EFCSV=$WORK/EFP/outputs/OutputGridEF.$SCEN.csv
  [[ $(( $(wc -l < "$EFCSV") - 1 )) -eq $N ]] || { echo "EFP 출력 셀 수 불일치: $EFCSV"; exit 1; }

  # ---- 4) CSV → I/O API NetCDF (txt2ioapi)
  (
    export PROMPTFLAG=N GRIDDESC GDNAM3D=$DOM
    export EFSTXTF=$EFCSV LDFTXTF=$EFCSV CTTXTF=$D/CT3.csv
    export EFMAPS=$D/EFMAP_$DOM.ncf LDFILE=$D/LDF_$DOM.ncf CANTYPFILE=$D/CT3_$DOM.ncf
    export RUN_EFS=T RUN_LDF=T RUN_CANTYP=T
    export RUN_LAI=F RUN_W126=F RUN_ARID=F RUN_NONARID=F RUN_FERT=F RUN_NITROGEN=F RUN_LANDTYPE=F
    rm -f "$EFMAPS" "$LDFILE" "$CANTYPFILE"
    "$PROGRAM/MEGANv3.21/bin/txt2ioapi" > "$LOG/megan_${DOM}_txt2ioapi.log" 2>&1
  )
  grep -q "Normal Completion" "$LOG/megan_${DOM}_txt2ioapi.log"

  # The gridID in EFP is 1-based, with columns varying fastest.
  python3 - "$EFCSV" "$D/LDF_$DOM.ncf" <<'PY' | tee "$LOG/megan_${DOM}_ldf_validation.log"
import sys
from netCDF4 import Dataset
import numpy as np
import pandas as pd

csv_path, nc_path = sys.argv[1:]
source = pd.read_csv(csv_path).set_index("gridID").sort_index()
with Dataset(nc_path) as output:
    shape = (output.NROWS, output.NCOLS)
    if not np.array_equal(source.index, np.arange(1, np.prod(shape) + 1)):
        raise SystemExit("LDF validation failed: missing or duplicate gridID")
    for number in range(3, 7):
        name = f"LDF{number:02d}"
        expected = source[f"LDF{number}"].to_numpy().reshape(shape)
        actual = output[name][0, 0]
        for label, values in (("CSV", expected), ("NetCDF", actual)):
            if np.ma.count_masked(values) or not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
                raise SystemExit(f"{name}: {label} contains missing, non-finite or out-of-range values")
        if actual.shape != shape or not np.allclose(actual, expected, rtol=0, atol=1e-6):
            raise SystemExit(f"{name}: NetCDF grid values differ from the EFP CSV")
        print(f"{name}: CSV/NetCDF match, range {actual.min():.6f} to {actual.max():.6f}")
PY

  # ---- 5) 공용 폴더에 설치 (격자 이름 = GRIDDESC 좌표계 이름 + 도메인)
  PROJ=$(sed -n '2p' "$GRIDDESC" | tr -d "' ")
  G=$RAW/GRID/${PROJ}_$DOM
  mkdir -p "$G"
  cp -p "$D/CT3_$DOM.ncf" "$D/EFMAP_$DOM.ncf" "$D/LDF_$DOM.ncf" "$GRIDDESC" "$G/"
  (cd "$G" && md5sum *.ncf > md5sum.txt)
  echo "   installed -> $G  $(date -Is)"
done
echo "run_megan_domain.sh 완료"
