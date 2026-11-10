# SMOKE 5.3 국외 격자 인벤토리 `smkinven.f` NONPOINT 초기화 오류 수정 (2026-11-10)

> 사용자 제공 HTAP_v3.2 시험 기록에 기반한 수정 이력. 실행 및 설치 명령의 기준은 [04 §7.2](04_SMOKE_Busan_Case_Run_Guide.md), 다른 시스템 재현은 [05 체크리스트](05_HTAP_v32_Reproduction_Checklist.md) 참조.

## 증상과 환경

- SMOKE 5.3 (공식 태그 `SMOKEv5.3_June2026`, 커밋 `f29374b`), Rocky Linux 9.8, GNU Fortran 11.5.
- 국외 `htap_energy` 27KM에서 `IMPORT_GRDNETCDF_YN Y` 경로로 격자 NetCDF를 읽을 때 `Smkinven`이 `SIGSEGV`로 종료. 인벤토리 273,600개 셀을 읽고 `CELLID`를 기록한 다음 ASCII 소스 쓰기 과정에서 실패.
- `smkinven.f`의 `NONPOINT` 지역 `LOGICAL` 변수가 초기화되지 않는다. FF10 텍스트 경로 `RDINVDATA`는 값을 지정하지만, 격자 NetCDF 경로 `RDGRDNCF`는 값을 지정하지 않는다. 이후 `WRINVCHR`가 초기화되지 않은 값을 받으면 `CMACT`/`CNAICS` 할당되지 않은 배열을 참조할 수 있다.

## 최소 변경

```diff
-        LOGICAL         NONPOINT         ! true: importing nonpoint inventory
+C.........  Busan patch (2026-11-10): initialize before gridded input.
+        LOGICAL      :: NONPOINT = .FALSE. ! true: importing nonpoint inventory
```

SMOKE 공식 태그 원본과 다른 부분을 확인한 뒤 **한 줄만** 수정한다. 공식 원본 `smkinven.f`의 MD5는 `0a1c220d886eb812c76ad028f44fbfe4`, 사용자 제공 패치본의 MD5는 `23530fc0a55cd5dcdef6c3a314510dc9`. 해시가 다르면 기존 수정사항을 확인하고 맹목적으로 덮어쓰지 않는다.

다른 시스템에서 적용할 때:

```bash
# 실제 위치로 치환
SMKINVEN_SRC="$SMK_HOME/src/smkinven/smkinven.f"
test -f "$SMKINVEN_SRC"
md5sum "$SMKINVEN_SRC"
cp -p "$SMKINVEN_SRC" "$SMKINVEN_SRC.before_htap_$(date +%Y%m%d)"
# 파일에서 LOGICAL NONPOINT 선언을 위의 패치처럼 수정한다.
# 컴파일과 실행파일 배치는 04 §7.2에 명시된 해당 SMOKE 설치 절차를 따른다.
```

## 검증 경과

| 확인항목 | 사용자 제공 2026-11-10 결과 |
|---|---|
| 수정 후 컴파일 | Fortran `Error:` 0건, 실행파일 갱신 |
| 27KM HTAP ENERGY | Smkinven 정상 종료, Spcmat까지 통과 |
| 별도 Grdmat 오류 | `GRID_CRO_2D` MCIP 경로 수정으로 해결(04 §7.3) |
| 27KM 8개 묶음 | 오류 0건, 각 묶음에 결과 파일 2개 |
| 수정 후 국내 부문 재실행 | 아직 독립 확인하지 않음 |

이 수정은 GNU Fortran의 비초기화 지역 변수 문제를 막기 위한 것으로, 국내 배출량 수치 또는 다른 컴파일러의 동일성을 별도로 검증했다는 뜻은 아니다. 이전의 `sizgmat.f` 배열 확장 패치는 폐기된 상태이며 [04 §7.1](04_SMOKE_Busan_Case_Run_Guide.md) 원인 해결 방법을 유지한다.


## GitHub 재현용 소스

재현에 필요한 변경 내용은 [원본 대비 패치](files/busan/2023capss/smoke_patch/smkinven_htap_v32.patch)와 [패치 적용 생성기](files/busan/2023capss/smoke_patch/apply_htap_v32_patches.py)로 저장되어 있다. **SMOKE 공식 배포 소스 자체를 중복 업로드하지 않으므로**, 다른 시스템에서는 SMOKEv5.3_June2026 태그의 `smkinven.f`를 설치한 뒤 패치를 적용하고 재컴파일한다. ZIP에 포함된 사용자 시험용 수정본의 SHA-256은 `ff192e11ec8ed8bd0ae1a2b2f0106c785ab36c15e5e38c19ca3f8f48f65d8ef4`다.
