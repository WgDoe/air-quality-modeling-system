# SMOKE 2023capss_cb6 입력자료 생성·설치 가이드

> **작업 기준일:** 2026-10-22. **목적:** [배출량 개선 계획](SMOKE_Emission_Improvement_Plan.md)에 따라 `CASES/BUSAN/TEST_20260901`에 CAPSS 2023 기반 국내 점·면·이동·바다 배출량과 4개 도메인 입력자료를 준비한다.  
> **검증 구분:** 입력자료 일괄 생성과 설치 스크립트의 가상 경로 시험은 사용자 제공 작업 기록 기준이다. Linux에서 **국내 점 Smkinven 형식 시험(①)은 정상 종료**, 점 전체 및 기타 부문의 **전체 SMOKE 실행(③)은 아직 미수행**이다. 이 페이지의 설치방법은 실행절차 기록이지 이번 GitHub 등록으로 Linux 서버에 설치했다는 뜻은 아니다.  
> 관련: [부산 사례 주 실행 가이드](SMOKE_Busan_Case_Run_Guide.md) · [배출량 개선 계획](SMOKE_Emission_Improvement_Plan.md) · [CAPSS 2017 기준선 보존본](SMOKE_Busan_Case_2017_Baseline_Archive.md)

## 1. 완료/미완료 구분

| 구간 | 내용 | 상태 |
|---|---|---|
| 사전 | SMOKE 5.3 설치·공식 예제 검증 | 완료 |
| 공통 기반 | 부산 EMIS 폴더, MCIP 링크, 공통 입력 준비 | 완료(기존 기록) |
| ① | CAPSS 2023 점 FF10의 09KM Smkinven 형식 시험 | **Linux 정상 종료** |
| ② | 국내 4개 부문 FF10, 공간 대리자료·참조, 실행 스크립트 등 입력 일괄 생성 | 작성 환경에서 생성·검사 |
| 설치 | ZIP 설치 스크립트 및 5개 스크립트×4개 도메인 파일 참조 검사 | **작성 환경의 가상 경로 시험 완료**; 실제 Linux 전체 설치 결과는 이 기록만으로 확인 불가 |
| ③ | 국내 점 onetime/daily와 면·이동·바다 전 부문 실행 | **미실행** |

작업 방법은 ① 형식 시험 → ② 입력 일괄 생성 → ③ 부문별 실행·검증으로 정리했다. 문제 발생 시 생성기를 수정하여 다시 작성한다.

## 2. 원자료 및 입력 생성기

| 자료 | 파일 | 규모 |
|---|---|---|
| CAPSS 2023 점 | `점오염원_2023_전국__1_기본.txt` | 14,437줄 |
| 면 | `면오염원(2023).zip`의 `전국a(2023).txt` | 9,615,471줄, 853 MB; 시도 결합 머리줄 16개 포함 |
| 이동 | `이동오염원(2023).zip`의 `전국m(2023).txt` | 7,612,113줄, 710 MB |
| 바다 | `바다m(2023).txt` | 820,602줄; 지역 9010000000; NOX·SOX 대문자 |
| 코드표 | `코드리스트(2023).xlsx`, `02_코드리스트(2017).xlsx` | 2017 번호 대응용 |
| 참조 | 기존 점·면 시간/종분배 참조, 국외/생물성 지역코드 자료 | 2020년 버전 |

생성기는 ZIP의 `generators/make_busan_2023_domestic_inputs.py`이며 기존 코드리스트, 시간·종분배 참조 원본이 필요하다. 원문 기록의 생성 시간은 약 5분, 메모리 1.3 GB.

```bash
# capss/ 하위에 point.txt, area.txt, mobile.txt, sea.txt 준비
python3 make_busan_2023_domestic_inputs.py --capss capss \
  --code2017 코드리스트_2017.xlsx \
  --code2023 코드리스트_2023.xlsx \
  --legacy <기존_참조_폴더> --out <출력_폴더>
```

필요 Python 패키지: `pandas`, `numpy`, `openpyxl`, `pyproj`.

## 3. 설치 패키지 및 자료 배치

사용자 제공 `busan_2023capss_full_setup_20261022.zip`에 다음을 포함한다. ZIP은 압축 기준 약 **28.3 MB**, 압축해제 후 약 **154.9 MB**이며 85개 디렉터리/파일 항목이 확인됐다(이번 첨부 검사 기준). ZIP 구조 점검은 통과했으며, SHA-256은 `34f5c8b7b8134cf2867de44cff0e1a838a8caa4831a35bce88179e2abddfb367`이다. 실제 인벤토리·surrogate 등 대용량 자료는 ZIP으로 별도 전달·보관하고 GitHub에는 설치 절차와 핵심 스크립트 위치를 기록한다.

### 3.1 공통 입력 및 지역코드

| 경로(EMIS 기준) | 역할 |
|---|---|
| `ge_dat/gridding/griddesc_busan_4domains.txt` | 27/09/03/01KM 정의(기존) |
| `ge_dat/costcy_busan_2023capss_20261022.txt` | 2023 지역 251(바다 포함) + 국외 7 + 생물성 1; GMT |
| `ge_dat/invtable_busan_2017capss_20261021.txt` | 기존 8물질 정의 |
| `ge_dat/temporal/holidays_korea_2012_2026_20261021.txt` | 한국 공휴일(공식 달력 QA 대기) |
| `ge_dat/temporal/tpro_monthly_*`, `tpro_weekly_*`, `tpro_hourly_*UTC_*` | 기존 시간 프로파일 유지 |
| `smoke5.2/scripts/smk_dates/2026/` | 월별 날짜 파일 12개 |
| `ge_dat/smkreport/sccdesc_busan_2023capss_20261022.txt` | SCC10·연료 설명 |

### 3.2 국내 점오염원

| 위치 | 파일 및 내용 |
|---|---|
| `2023capss_cb6/inputs/kor_point/` | `kor_point_CAPSS2023_ff10_20261022.csv` (89,319줄, 굴뚝 14,289개), `stack_fill_log_20261022.csv` |
| `ge_dat/temporal/` | `tref_kor_point_2023capss_20261022.csv` |
| `ge_dat/speciation/` | `gsref_kor_point_2023capss_20261022.csv` |
| `ge_dat/point/` | 예제 `pelvconfig_elevate_everything_17apr2020_v0.txt`, `pstk_13nov2018_v1.txt` |
| `2023capss_cb6/scripts/point/` | `Annual_kor_point_onetime_2023capss_cb6.csh` (Smkinven·Spcmat·Grdmat·Smkreport·Elevpoint), `Annual_kor_point_daily_2023capss_cb6.csh` (Temporal·Smkmerge) |

### 3.3 국내 면·이동·바다

| 부문 | FF10 파일 | 줄 수 |
|---|---|---:|
| 면 | `2023capss_cb6/inputs/kor_area/kor_area_CAPSS2023_ff10_20261022.csv` | 145,564 |
| 이동 | `2023capss_cb6/inputs/kor_mobile/kor_mobile_CAPSS2023_ff10_20261022.csv` | 163,810 |
| 바다 | `2023capss_cb6/inputs/kor_sea/kor_sea_CAPSS2023_ff10_20261022.csv` | 63 |

4개 영역 × 3부문의 신규 `ge_dat/gridding/surrogates/kor_2023capss_<GRID>/srg_<부문>_2023capss_<GRID>.txt` **12개**, `srgdesc_kor_2023capss_<GRID>_20261022.txt` **4개**, `agref_kor_nonpoint_2023capss_20261022.txt` 및 `tref_kor_nonpoint_*`·`gsref_kor_nonpoint_*`를 작성했다. 공간 ID는 면 1001~, 이동 3001~, 바다 5001~이며 기본값 900/901/902를 사용한다.

실행 파일은 `2023capss_cb6/scripts/nonpoint/Annual_kor_area_2023capss_cb6.csh`, `Annual_kor_mobile_2023capss_cb6.csh`, `Annual_kor_sea_2023capss_cb6.csh`이다.

### 3.4 예제에서 참조하는 파일 및 설정

종분배 예제 원본: `gscnv_SPECIATE_5_3_*`, `gspro_CB6R3_AE7_criteria_*`, `gspro_PM2_5_AE6_*`, `gspro_static_cmaq_*`, `gspro_nox_hono_*`. 보고서 `smkreport/repconfig/`와 `orisdesc`, `naicsdesc`도 활용한다.

신규 `2023capss_cb6/scripts/directory_definitions.csh`, `run_settings.txt`, `inputs/scc10_reference_map_20261022.csv`(4부문 802 SCC/연료 조합 및 출처), `inputs/generation_summary_20261022.csv`를 함께 준비했다. ZIP의 `generators/`에는 생성기 3개가 있다.

## 4. 설치 절차 (Linux 실제 설치 여부 별도 확인)

ZIP 파일과 설치 스크립트의 원문을 사용한다. 기존 파일을 덮어쓰며 **다음 경로를 삭제**하므로 재설치·재실행 전에 해당 경로의 자료가 필요한지 확인한다:

- `2023capss_cb6/intermed/09KM/kor_point`
- `2023capss_cb6/inputs/kor_point/scc10_reference_map_20261022.csv`
- `2023capss_cb6/inputs/asia` (기존 2010 국외 자료)

```bash
unzip -o ~/busan_2023capss_full_setup_20261022.zip -d ~/busan_setup
bash ~/busan_setup/install_busan_2023capss.sh 2>&1 | tee ~/busan_install.log
```

설치 스크립트는 폴더 및 MCIP 링크 생성 → 예제 `smoke5.2/` 필요 시 복사 → 패키지의 EMIS 55개 파일 복사 → 예제 종분배·점·보고서 파일 복사 → 이전 시험 결과 삭제 → 5개 실행 스크립트×4개 영역 파일 존재 검사 → surrogate·FF10 현황 출력 순서다.

**설치 스크립트 검사 범위:** 존재 여부 확인 위주이며, 형식·값·질량 보존 및 부문별 정상 실행을 보증하지 않는다. 파일이 없을 때 `MISSING`을 출력해도 해당 스크립트가 반드시 비정상 종료하는 구조는 아니므로 로그 내용을 확인한다. 정상 검사 예시는 `all referenced files exist (5 scripts x 4 domains)`, 개별 `ok` 5줄, surrogate 폴더 4개, FF10 4개다.

## 5. 입력 변환 원칙 및 생성 수치

- 단위: **kg/yr ÷ 907.18474 = short ton/yr**. FF10 저감효율 칸은 `0`.
- 지역: 시군구 앞 5자리(바다 `90100`), `#COUNTRY=ASIA`, GMT와 UTC 이동 시간 프로파일 동시 사용.
- SCC10: SCC 8자리 + 기존 연료 2자리. 기존 연료 예외 `20500→44`, `999xx→99`; 신규 G1~G6, S1~S2와 CNG `41300→C1`은 LNG 또는 유연탄 참조를 차용했다.
- 참조 매핑 순서: 정확 일치 → 빌린 연료 → 같은 SCC/같은 연료 계열 → 같은 SCC 다른 연료 → 같은 상위 SCC 6자리 → 기본값. **이동·바다는 원자료에 도로 코드가 없어 연료 기반 SCC10을 구성한 것**으로 향후 검증한다.
- 굴뚝: 같은 굴뚝 값 → SCC·연료 중앙값 → SCC 중앙값 → 전체 중앙값. 중복 148줄 병합. FF10 굴뚝 단위는 ft, °F, ft/s.
- 격자: TM(Bessel/Tokyo) → 위경도 → 모델 Lambert. (지역, SCC10)의 1km 공간분포를 모델 격자로 교차할당(모델 크기별 다중 샘플링), 경계 밖 몫은 제외. 기본 surrogate 900/901/902.

**FF10 생성 결과 — short ton/yr (사용자 작성 기록):**

| 부문 | 줄 | CO | NOx | SO2 | PM10 | PM2.5 | VOC | NH3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| kor_point | 89,319 | 347,311 | 201,410 | 106,298 | 12,258 | 9,071 | 221,154 | 25,362 |
| kor_area | 145,564 | 214,732 | 139,736 | 25,210 | 56,848 | 15,844 | 668,272 | 240,057 |
| kor_mobile | 163,810 | 275,848 | 459,587 | 4,059 | 58,424 | 24,527 | 86,731 | 1,909 |
| kor_sea | 63 | 46,890 | 90,191 | 3,609 | 3,678 | 3,422 | 15,324 | 8 |

종분배 참조(배출량 기준) 정확 일치/같은 연료 계열/기타/기본값 비율:

| 부문 | NOx 정확 / VOC 정확 | NOx 같은 연료 / VOC 같은 연료 | NOx 기본 / VOC 기본 |
|---|---|---|---|
| kor_point | 83.5% / 96.2% | 0.1% / 3.4% | 0.2% / 0% |
| kor_area | 93.0% / 96.9% | 5.1% / 2.8% | 1.9% / 0.3% |
| kor_mobile | 0% / 0% | 96.8% / 90.5% | 0% / 0% |
| kor_sea | 0% / 0% | 99.9% / 100% | 0% / 0% |

surrogate 검사에서 12개 파일 모두 (지역, 번호) 비율 합 1 초과 0건; 27/09km 합 중앙값 1.0000. 바다 03km 16,562줄·01km 15,790줄로 기존 고해상도 바다 배분 공백을 보완했다. **이는 새 생성기 검증 결과이지 SMOKE 실행 성공 근거가 아니다.**

## 6. Linux ① 국내 점 Smkinven 형식 시험 — 완료 (2026-10-22)

2023 점 FF10의 저감효율 칸이 비어 있던 초기 파일을 09KM Smkinven으로 읽되, `run_settings.txt`에서 다른 프로그램을 꺼 두고 시험한 결과:

| 항목 | 사용자 제공 실행 결과 |
|---|---|
| Smkinven | **Normal Completion**, 배출원 14,289개, 오염물질 8개 + PMC |
| COSTCY/지역 코드 | 오류 없음 |
| 영문 SCC | `…G6`가 내부 20자리 SCC로 읽혀 통과 |
| 굴뚝 제원 | 결측 대체 0건; 높이 0.1~0.4m 69행이 0.5m 하한으로 조정됨(NOx 28.7 short ton) |
| 초기 경고 | 일배출량·저감효율 빈칸; 생성기에서 저감효율 0 기입으로 보완 |
| Smkreport | PSSUP 누락 오류: 시험 시 Spcmat 비활성으로 인한 것으로 기록; 전체 부문 실행 성공을 뜻하지 않음 |

**중요:** 최종 생성기로 수정한 저감효율 `0` 값이 포함된 **최종 패키지를 대상으로 전체 SMOKE 재실행한 결과는 아직 없다.**

## 7. 다음 실행: 국내 부문 ③

각 부문은 **09KM부터** 통과시킨 뒤 27·03·01KM으로 넓힌다. 아래 명령은 패키지 설치·경로·권한 검증 후 사용하는 **예정 명령**이다.

```bash
cd /home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901/EMIS/2023capss_cb6/scripts/point
GRID=09KM ./Annual_kor_point_onetime_2023capss_cb6.csh 2>&1 | tee ../logs/kor_point_onetime_09KM.log
GRID=09KM ./Annual_kor_point_daily_2023capss_cb6.csh 2>&1 | tee ../logs/kor_point_daily_09KM.log
cd ../nonpoint
GRID=09KM ./Annual_kor_area_2023capss_cb6.csh 2>&1 | tee ../logs/kor_area_09KM.log
GRID=09KM ./Annual_kor_mobile_2023capss_cb6.csh 2>&1 | tee ../logs/kor_mobile_09KM.log
GRID=09KM ./Annual_kor_sea_2023capss_cb6.csh 2>&1 | tee ../logs/kor_sea_09KM.log
```

Smkreport의 지역·SCC·물질 합계는 `generation_summary_20261022.csv`의 short ton 합계와 비교하며, 도메인 밖에 해당하는 몫은 별도 산출해 설명한다.

## 8. 아직 확인할 사항

- 점 날짜별 단계의 MCIP 파일명/기간, CMAQ inline 굴뚝 처리 및 병합 경로.
- 이동의 원자료 도로코드 부재와 SCC10 도로 구분의 영향.
- HTAP_v3.1 다운로드/남한 제외, 생물성 BEIS4 또는 MEGAN 3.x, CMAQ 5.5 배출물질 이름 대응.
- 2026년 한국 공휴일 및 노동절 공식 달력 대조.

**GitHub 파일 관리:** 이 페이지는 업로드된 Markdown·ZIP의 구조 확인에 근거한다. Linux 실행로그 원본을 직접 열거나 사용자의 서버에서 설치·재실행하지 않았다. 패키지 전체는 별도 ZIP으로 제공되며 GitHub 문서만으로 재설치할 때는 ZIP 원본이 필요하다.
