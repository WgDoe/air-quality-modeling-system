# SMOKE 5.3 국외 격자 인벤토리 `smkinven.f` NONPOINT 초기화 오류 수정 (2026-11-10)

> 사용자 제공 HTAP_v3.2 시험 기록에 기반한 수정 이력. 실행 및 설치 명령의 기준은 [04 §11.3](04_SMOKE_Busan_Case_Run_Guide.md), 다른 시스템 재현은 [05 체크리스트](05_HTAP_v32_Reproduction_Checklist.md) 참조.

## 증상과 환경

- SMOKE 5.3 (공식 태그 `SMOKEv5.3_June2026`, 커밋 `f29374b`), Rocky Linux 9.8, GNU Fortran 11.5.
- 국외 `htap_energy` 27KM에서 `IMPORT_GRDNETCDF_YN Y` 경로로 격자 NetCDF를 읽을 때 `Smkinven`이 `SIGSEGV`로 종료. 인벤토리 273,600개 셀을 읽고 `CELLID`를 기록한 다음 ASCII 소스 쓰기 과정에서 실패.
- `smkinven.f`의 `NONPOINT` 지역 `LOGICAL` 변수가 초기화되지 않는다. FF10 텍스트 경로 `RDINVDATA`는 값을 지정하지만, 격자 NetCDF 경로 `RDGRDNCF`는 값을 지정하지 않는다. 이후 `WRINVCHR`가 초기화되지 않은 값을 받으면 `CMACT`/`CNAICS` 할당되지 않은 배열을 참조할 수 있다.

## 최소 변경과 재현 절차

기존 선언 1줄을 초기화 선언으로 바꾸고 설명 주석 3줄을 추가한다. GitHub의 [`smkinven_htap_v32.patch`](files/busan/2023capss/smoke_patch/smkinven_htap_v32.patch)와 일치하는 변경이며 **수작업 편집 대신 [`apply_htap_v32_patches.py`](files/busan/2023capss/smoke_patch/apply_htap_v32_patches.py)를 사용**한다.

```diff
-        LOGICAL         NONPOINT         ! true: importing nonpoint inventory
+C.........  Busan patch (2026-11-10): NONPOINT is set only by RDINVDATA (ASCII inventories).
+C           For gridded NetCDF/I-O API inventories it was left undefined; with gfortran it can
+C           be .TRUE. and WRINVCHR then reads unallocated CMACT/CNAICS (Segmentation fault).
+        LOGICAL      :: NONPOINT = .FALSE. ! true: importing nonpoint inventory
```

공식 SMOKE 태그 원본의 `smkinven.f` MD5는 `0a1c220d886eb812c76ad028f44fbfe4`, 패치 후 MD5는 `23530fc0a55cd5dcdef6c3a314510dc9`(사용자 제공 2026-11-10 재현 시험). 해시가 다르면 다른 변경·소스 버전을 먼저 조사한다.

**패치 → MD5 검사 → 재컴파일 → 사례 설치**의 전체 명령은 [04 §11.3](04_SMOKE_Busan_Case_Run_Guide.md)의 블록을 그대로 사용한다. 실제 소스 경로는 `$SMK_HOME/subsys/smoke/src/smkinven/smkinven.f`다.

**컴파일러 차이(사용자 제공 분석):** EPA의 Intel `Linux2_x86_64ifx` 실행환경에는 Intel `Makeinclude`의 `-zero` 옵션이 적용되어 초기화되지 않은 지역 변수가 0으로 채워질 수 있지만, GNU 설정에는 해당 옵션이 없어 오류가 드러났다. 이 설명은 제공된 환경·설정에 대한 분석으로, 모든 Intel 빌드에서 문제없다는 의미는 아니다.
## 검증 경과

| 확인항목 | 사용자 제공 2026-11-10 결과 |
|---|---|
| 수정 후 컴파일 | Fortran `Error:` 0건, 실행파일 갱신 |
| 27KM HTAP ENERGY | Smkinven 정상 종료, Spcmat까지 통과 |
| 별도 Grdmat 오류 | `GRID_CRO_2D` MCIP 경로 수정으로 해결(04 §11.3) |
| 27KM 8개 묶음 | 오류 0건, 각 묶음에 결과 파일 2개 |
| 수정 후 국내 부문 재실행 | 아직 독립 확인하지 않음 |

이 수정은 GNU Fortran의 비초기화 지역 변수 문제를 막기 위한 것으로, 국내 배출량 수치 또는 다른 컴파일러의 동일성을 별도로 검증했다는 뜻은 아니다. 이전의 `sizgmat.f` 배열 확장 패치는 폐기된 상태이며 [04 §7.1](04_SMOKE_Busan_Case_Run_Guide.md) 원인 해결 방법을 유지한다.


## GitHub 재현용 소스

재현에 필요한 변경 내용은 [원본 대비 패치](files/busan/2023capss/smoke_patch/smkinven_htap_v32.patch)와 [패치 적용 생성기](files/busan/2023capss/smoke_patch/apply_htap_v32_patches.py)로 저장되어 있다. **SMOKE 공식 배포 소스 자체를 중복 업로드하지 않으므로**, 다른 시스템에서는 SMOKEv5.3_June2026 태그의 `smkinven.f`를 설치한 뒤 패치를 적용하고 재컴파일한다. ZIP에 포함된 사용자 시험용 수정본의 SHA-256은 `ff192e11ec8ed8bd0ae1a2b2f0106c785ab36c15e5e38c19ca3f8f48f65d8ef4`다.
