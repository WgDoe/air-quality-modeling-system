#!/usr/bin/env bash
# MEGAN 3.2 전처리 도구 설치·컴파일 + 공용 원자료 준비 (한 번만 실행)
#   사용법: bash setup_megan32.sh
#   결과  : $MODEL/MEGAN/      (전처리기·txt2ioapi·EFP)
#           $MODEL/DATA/EMIS/MEGAN/ (원자료, efp_utf8/, cantype_EA/)
# 이미 받은 파일·만든 폴더는 건너뛰므로 중간에 끊겨도 다시 실행하면 된다.
set -euo pipefail

MODEL=${MODEL:-$HOME/CMAQ_MODEL}
FILES=$(cd -P "$(dirname "$0")" && pwd)          # 이 스크립트가 있는 files/ 폴더
PROGRAM=$MODEL/MEGAN
RAW=$MODEL/DATA/EMIS/MEGAN
NETCDF=$MODEL/libs/netCDF-WRF
IOAPI=$MODEL/libs/ioapi-3.2-20200828
IOBIN=$IOAPI/Linux2_x86_64gfort10
export LC_ALL=C

mkdir -p "$PROGRAM/archives" "$RAW/NCAR_d312006"

# ---------------------------------------------------------------- 1. 내려받기
get() {   # get <저장경로> <md5> <URL>
  local f=$1 md5=$2 url=$3
  if [[ ! -f $f ]]; then
    echo "download $(basename "$f")"
    curl -fL --retry 3 -C - -o "$f.part" "$url"
    echo "$md5  $f.part" | md5sum -c
    mv "$f.part" "$f"
  fi
  echo "$md5  $f" | md5sum -c
}
Z=https://zenodo.org/records
get "$PROGRAM/archives/MEGAN32_Prep_Code_Jan_2022.tar.gz" 74ce3cb0d51c36491aee1f154aea5f2c \
    "$Z/19478384/files/MEGAN32_Prep_Code_Jan_2022.tar.gz"
get "$PROGRAM/archives/MEGANv3.21.tar.gz" c0b414050ded9a0ec729c9de535d4272 \
    "$Z/10526206/files/MEGANv3.21.tar.gz"
get "$PROGRAM/archives/MEGEFP321.zip" d508f490f21d9c2dbfa07e26b4f7e058 \
    "https://drive.usercontent.google.com/download?id=1ZAkE1osXK6Gl0GEzfGyTDGm17PfwfxDL&export=download&confirm=t"
get "$RAW/EFP240120.zip" 6386b90e27c2e6257bb8566d91f30f4c "$Z/10939297/files/EFP240120.zip"
get "$RAW/EVT3d.zip"     802690a4ff267389efe2cfc68539fdac "$Z/10939297/files/EVT3d.zip"
get "$RAW/GFv7nc.zip"    536817caab2c66f78d48d969e9bfe4d7 "$Z/10939297/files/GFv7nc.zip"
get "$RAW/NCAR_d312006/veg_GrowthFormFracions.nc" 4ce552caa67171b68652406d219235cb \
    "https://tds.gdex.ucar.edu/thredds/fileServer/files/d312006/veg_GrowthFormFracions.nc"

# ---------------------------------------------------------------- 2. 압축 풀기
cd "$PROGRAM"
[[ -d MEGAN32_Prep_Code_Jan_2022 ]] || tar xzf archives/MEGAN32_Prep_Code_Jan_2022.tar.gz
[[ -d MEGANv3.21 ]]                 || tar xzf archives/MEGANv3.21.tar.gz
[[ -d MEGEFP32 ]]                   || unzip -q archives/MEGEFP321.zip -d .

# ---------------------------------------------------------------- 3. 전처리기(Fortran) 수정·컴파일
P=$PROGRAM/MEGAN32_Prep_Code_Jan_2022
cd "$P"
# (1) cantype: 출력 형식 'I' → 'I0' (gfortran은 폭 없는 I 형식을 허용하지 않음)
sed -i 's/(3(I,","), 6(F10.4,","))/(3(I0,","), 6(F10.4,","))/' prepmegan4cmaq_cantype.f90
grep -q '(3(I0,","), 6(F10.4,","))' prepmegan4cmaq_cantype.f90
# (2) growthform 저메모리판: 입력 변수마다 격자 캐시 해제 (7GB 메모리에서 27KM 실행용)
[[ -f prepmegan4cmaq_grwform_lowmem.f90 ]] || \
  patch -o prepmegan4cmaq_grwform_lowmem.f90 prepmegan4cmaq_grwform.f90 \
        < "$FILES/patches/prepmegan4cmaq_grwform_lowmem.patch"
FC="gfortran -O2 -fallow-argument-mismatch"
for s in misc_definitions_module constants_module bio_types area_mapper_grw \
         prepmegan4cmaq_ecotype prepmegan4cmaq_grwform_lowmem prepmegan4cmaq_cantype; do
  $FC -c -I"$NETCDF/include" $s.f90
done
COMMON="misc_definitions_module.o constants_module.o bio_types.o area_mapper_grw.o"
for x in ecotype grwform_lowmem cantype; do
  $FC -o prepmegan4cmaq_$x.x $COMMON prepmegan4cmaq_$x.o \
      -L"$NETCDF/lib" -Wl,-rpath,"$NETCDF/lib" -lnetcdff -lnetcdf
done
ls -l prepmegan4cmaq_ecotype.x prepmegan4cmaq_grwform_lowmem.x prepmegan4cmaq_cantype.x

# ---------------------------------------------------------------- 4. txt2ioapi 컴파일
T=$PROGRAM/MEGANv3.21/src/TXT2IOAPI
cd "$T"
# EFP CSV is gridID, EF1..EF19, LDF3..LDF6. The LDF columns start at 21.
sed -i 's/SEGMENT( 19+S )/SEGMENT( 20+S )/' cnvt_LDF.F
grep -Fq 'STR2REAL( SEGMENT( 20+S ) )' cnvt_LDF.F
mkdir -p ioapi_fixed ../../bin
# I/O API 헤더(.EXT)를 72열에서 잘라 고정형식 Fortran에서 읽히게 복사
for f in "$IOAPI"/ioapi/fixed_src/*.EXT; do cut -c1-72 "$f" > "ioapi_fixed/${f##*/}"; done
sed 's/ -qopenmp / -fopenmp /g' makefile > makefile.gcc
make -B -f makefile.gcc FC=gfortran \
     FFLAGS='-O2 -ffixed-line-length-132 -std=legacy -fallow-argument-mismatch -fopenmp' \
     INCLUDE="-I$T/ioapi_fixed -I$NETCDF/include -I$T/INCLDIR" \
     LIBS="-L$IOBIN -lioapi -L$NETCDF/lib -Wl,-rpath,$NETCDF/lib -lnetcdff -lnetcdf"
ln -sfn ../src/TXT2IOAPI/txt2ioapi "$PROGRAM/MEGANv3.21/bin/txt2ioapi"
test -x "$T/txt2ioapi"

# ---------------------------------------------------------------- 5. EFP(파이썬) 수정
# pandas 2.x에서 DataFrame.append가 없어져 pd.concat으로 교체 (원본은 .orig로 보관)
E=$PROGRAM/MEGEFP32/src/run_M3EFP.py
[[ -f $E.orig ]] || cp "$E" "$E.orig"
sed -i 's/df_ef = df_ef.append(df_mp, ignore_index=True)/df_ef = pd.concat([df_ef, df_mp], ignore_index=True)/' "$E"
grep -q 'pd.concat(\[df_ef, df_mp\]' "$E"

# ---------------------------------------------------------------- 6. 공용 원자료 준비
cd "$RAW"
[[ -f EVT3d.nc ]]       || unzip -q EVT3d.zip              # 생태유형 30초 전지구 (변수 EVT)
[[ -d GFv7nc ]]         || unzip -q GFv7nc.zip             # 생육형 4종 30초 전지구
[[ -d EFP240120 ]]      || unzip -q EFP240120.zip          # EFP240120/ 폴더로 풀림
# 배출계수·종구성표: 원본이 cp1252 인코딩이라 EFP(pandas)가 읽지 못함 → UTF-8로 변환
mkdir -p efp_utf8
for f in EFP240120/*.csv; do iconv -f cp1252 -t utf-8 "$f" > "efp_utf8/${f##*/}"; done
# 관목(SC30s7.nc) 변수 이름이 CCpercent로 잘못 들어 있어 SCpercent로 바꾼 복사본 생성
python3 "$FILES/megan_fix_sc30s7.py" GFv7nc/SC30s7.nc GFv7nc/SC30s7_SCpercent.nc
# 캐노피(CT3) 입력 6종을 동아시아 범위로 잘라 생성 → cantype_EA/
python3 "$FILES/make_megan_cantype_inputs.py" "$RAW"

echo "setup_megan32.sh 완료"
