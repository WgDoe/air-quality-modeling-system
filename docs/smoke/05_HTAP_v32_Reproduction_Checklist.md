# HTAP_v3.2 국외배출량 재현 및 검증 체크리스트

> 갱신: 2026-11-10. 원칙: 국내 CAPSS 처리에 사용한 SMOKE 5.3 환경을 유지하고, **국외 HTAP_v3.2 입력의 생성·설치·실행·검증**을 별도로 추적한다. 27KM 8개 묶음 완료는 사용자 제공 실행 기록에 근거하며, 이 문서 자체가 다른 시스템에서의 재실행 성공을 뜻하지 않는다.

## 0. 먼저 읽을 문서

1. [01 SMOKE 설치·공식 예제](01_SMOKE_Installation_Guide.md)
2. [03 배출량 개선 계획](03_SMOKE_Emission_Improvement_Plan.md) — HTAP_v3.2 선정 및 변환 원칙
3. [04 부산 사례 실행 가이드](04_SMOKE_Busan_Case_Run_Guide.md) — §3.4 원자료, §6.5 생성, §7.2·7.3 패치와 설치, §8.6 실행·검증
4. [91 Smkinven 오류 수정](91_SMOKE_smkinven_Fix.md)

## 1. 실행 조건 고정

- 기준 운영환경: Rocky Linux 9.8, SMOKE 5.3, CMAQ 5.5 환경, Python 3 + netCDF4·numpy·pandas·pyproj.
- 사례 기준: `/home/woogon/CMAQ_MODEL/CASES/BUSAN/TEST_20260901`, 시나리오 `2023capss_cb6`; 다른 시스템에서는 **경로를 그대로 가정하지 말고 수정**한다.
- HTAP 원자료: HTAP_v3.2 **2020년**, 9종(CO/NH3/NMVOC/NOx/PM10/PM2.5/SO2/BC/OC), 전지구 0.1° NetCDF가 담긴 개별 ZIP 9개.
- CAPSS 2023 1km 원자료, SMOKE 공식 예제(HTAP GRIDMASK·시간·종분배 참조 포함), 국내 INVTABLE, MCIP 도메인별 GRIDCRO2D가 필요하다.
- 원자료·대용량 생성 파일은 GitHub 저장소에 포함되지 않는다. 04 §3, §6의 지정 위치로 별도 준비한다.

## 2. 필수 실행 순서

### A. 기존 환경 검증

```bash
which python3
python3 -c 'import netCDF4,numpy,pandas,pyproj; print("python modules OK")'
which tcsh
which ncdump
```

국내 CAPSS 사례와 일치하는 `SMK_HOME`, `SMKROOT`, `GRIDDESC`, `MCIP`, `ASSIGNS.emf`, `directory_definitions.csh` 경로를 먼저 확인한다.

### B. 국외 입력 생성 (04 §6.5)

국외 입력 생성 스크립트 `make_busan_htap_v32_inputs.py`를 **04 §3.1에 기록한 저장소 경로**에서 준비한다. 아래 예의 `ROOT`, `F`, `--htap`, `--capss`, `--example`, `--invtable` 및 `--final`을 로컬 시스템에 맞게 고친다.

```bash
set -o pipefail
ROOT="$HOME/CMAQ_MODEL"
F="$HOME/busan_smoke_files"
PKG="$HOME/busan_htap_pkg"
CASE="$ROOT/CASES/BUSAN/TEST_20260901"
test ! -e "$PKG" || { echo "기존 생성 패키지를 먼저 백업하세요: $PKG"; exit 1; }
python3 "$F/2023capss/generators/make_busan_htap_v32_inputs.py" \
  --htap "$ROOT/DATA/EMIS/HTAPv32/2020" --year 2020 \
  --capss "$ROOT/DATA/EMIS/CAPSS2023" \
  --example "$ROOT/CASES/SMOKE_TEST/smoke_example_case_v3" \
  --invtable "$F/invtable_busan_2017capss_20261021.txt" \
  --final "$CASE/EMIS" --out "$PKG" \
  2>&1 | tee "$HOME/busan_htap_generate.log"
```

**중요:** 파이프 앞의 Python 실행 실패를 놓치지 않으려면 `set -o pipefail`을 사용한다. `--final`은 목록 파일에 들어갈 **최종 설치 경로**이므로 설치 위치와 반드시 같아야 한다.

### C. 결과 사전 점검

```bash
grep -nE 'South Korea mask|BC/OC read|list files|INVTABLE|WARNING|ERROR|done' "$HOME/busan_htap_generate.log"
find "$PKG" -type f | sort | tail -30
```

2026-11-10 기록상의 생성 기준은 영역 90~162°E / 18~56°N, 720×380셀, 남한 마스크 3,176개 셀, 8개 묶음 목록, 탄소분리 `PEC`·`POC`, 마지막 로그 `done`이다. 이는 특정 원자료·입력의 참고값으로, 버전이 다르면 결과도 달라질 수 있다. 자세한 비교값과 물질별 질량표는 04 §6.5에 있다.

### D. SMOKE 소스 수정 및 설치 (04 §7)

1. 기존 국내용 `genagmat.f` 수정 상태를 보존한다. **폐기한 `sizgmat.f` 여유 배열 패치를 다시 적용하지 않는다.**
2. 국외용 `smkinven.f`의 NONPOINT 초기화 문제는 [91](91_SMOKE_smkinven_Fix.md)에 따라 원본 보관·차이 확인·컴파일 검증 후 수정한다.
3. `directory_definitions.csh`에 실제 MCIP `GRIDCRO2D_<GRID>.*.nc`를 가리키는 `GRID_CRO_2D` 설정이 적용되었는지 확인한다.
4. `ASSIGNS.emf`의 참조 설정과 HTAP 입력·목록·프로파일을 04 §7.3의 명령대로 설치한다.
5. 동일 사례 폴더에 덮어쓰기 전 스크립트·입력·로그를 백업한다.

### E. 시험 실행 → 전체 실행 (04 §8.6)

```bash
# 사례 EMIS 실행 스크립트 디렉터리에서 수행
GRID=27KM HTAP_GROUP=ENERGY ./htap/Annual_htap_2023capss_cb6.csh
```

한 묶음이 성공한 후 `04 §8.6`의 8개 묶음 반복문을 이용해 27KM 전체를 수행한다. 나머지 도메인의 처리는 같은 구조로 확장하되 각 도메인의 `GRIDCRO2D`, 격자명, 출력 경로가 실제 파일과 맞는지 확인한다.

## 3. 필수 검증 (성공 조건 분리)

| 단계 | 최소 확인 | 판정 |
|---|---|---|
| 생성 | 종료코드 0, 로그 `done`, 경고·오류 검토, 9종 NetCDF와 8개 목록 | 생성 검증 |
| 마스크 | 남한 셀의 국외 배출량 0, 제거량 및 인접 지역 손실 확인 | 중복 제거 검증 |
| 성분 | 모든 셀에서 PM2.5 = PM2_5 + PEC + POC, 음수/NaN 없음 | 질량 보존 검증 |
| 실행 | 각 묶음 ERRLOG=0, 기대한 일별 파일 생성, 기간과 격자 일치 | SMOKE 실행 검증 |
| 수치 | 04 §8.6의 격자 합계·대표 도시 격자·부문별 결과 비교 | 결과 검증 |
| 통합 | CAPSS·HTAP 공간 중복, 병합 후 물질·시간·단위, CMAQ species 확인 | **별도 미검증** |

로그 오류 0건만으로 질량 보존이나 CMAQ 적용 성공을 선언하지 않는다. 27KM은 사용자 제공 2026-11-10 결과상 8개 묶음 완료; 나머지 도메인과 병합·CMAQ 연계는 이후 결과로 갱신한다.

## 4. 과학적 주의 및 후속 개선

- **남한 마스킹:** CAPSS 1km 셀이 닿는 HTAP 0.1° 셀 전체를 0으로 하므로 해안·접경 지역 국외 배출량 손실 가능. 남한 중복 제거와 국외 배출량 보존은 다른 검증 목표다.
- **BC·OC 비례 축소:** BC+OC > PM2.5 셀에서 두 탄소 성분을 줄여 PM2.5 총량을 보존한다. 성분별 질량은 조정되므로 원자료의 종별 배출을 그대로 보존한 것은 아니다.
- **시간·화학종:** 일부 하위 부문은 기존 상위 부문 프로파일로 대체한다. 이는 검증된 임시 매핑으로 기술하고 최신화 완료로 표시하지 않는다.
- **도메인 확대:** 완료/검증 중 상태는 [04 §9](04_SMOKE_Busan_Case_Run_Guide.md)에만 최신값으로 기록한다.

## 5. 재현 기록 양식

```text
작업일시 / 실행자:
호스트 / OS / Python 및 라이브러리 버전:
SMOKE / CMAQ / I/O API 버전 및 소스 커밋:
GitHub 저장소 커밋 SHA:
HTAP 원본 파일명 및 sha256sum (9개):
CAPSS 원본 파일명 및 sha256sum:
SMOKE 예제 및 프로파일 버전:
CASE / EMIS / MCIP / GRIDDESC / GRID_CRO_2D 실제 경로:
생성 명령 / 실행 명령 / 종료코드:
도메인 / 묶음 / 기간 / 기대파일 수 / 실제파일 수:
ERRLOG / PRIO01 / NaN·음수 / 질량 보존 / 남한 마스크:
수정 전후 소스 diff / 컴파일 로그:
관측된 문제 / 해결 / 잔여 검증 항목:
```

> 주의: 본 체크리스트는 첨부된 국외 처리 문서에 기록된 절차를 구조화한 것이다. 다른 호스트에서 생성부터 모델 실행까지 독립적으로 재현해 본 검증 기록은 별도로 남겨야 한다.
