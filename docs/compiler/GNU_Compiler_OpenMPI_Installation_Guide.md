# GNU Compiler 및 OpenMPI 설치 가이드

## 1. 문서 목적

본 문서는 Rocky Linux 9 계열 환경에서 대기질 모델링 시스템 구축에 필요한 기본 GNU Compiler와 OpenMPI를 설치하고, Windows와 Linux 간 파일 전송 환경을 구성한 뒤 실제 C/C++/Fortran 및 MPI 동작 여부를 확인하는 절차를 정리한다.

주요 대상은 다음과 같다.

- Windows ↔ Linux 파일 전송 환경 구성
- GNU C Compiler (`gcc`)
- GNU C++ Compiler (`g++`)
- GNU Fortran Compiler (`gfortran`)
- GNU Make
- OpenMPI
- MPI용 Fortran wrapper compiler (`mpifort`)
- MPI 병렬 실행 (`mpirun`)

본 문서는 특정 설치 작업의 진행 기록이 아니라, 동일 환경을 재구축하거나 유지보수할 때 재사용할 수 있는 설치 및 검증 가이드로 작성한다.

---

## 2. 설치 원칙

본 환경에서는 다음 원칙을 적용한다.

- GNU Compiler와 기본 개발도구는 시스템 패키지로 설치한다.
- 설치 작업은 root 권한으로 수행할 수 있다.
- 실제 모델 및 라이브러리 컴파일·실행은 일반 사용자 계정에서 수행한다.
- C, C++, Fortran compiler는 같은 GCC family를 사용한다.
- OpenMPI가 실제로 동일한 GNU Fortran compiler를 사용하는지 확인한다.
- 설치 후에는 버전 확인뿐 아니라 실제 compile 및 parallel run test를 수행한다.

권장 계정 구분:

```text
root
 └─ 시스템 패키지 설치

일반 사용자
 ├─ 컴파일 테스트
 ├─ MPI 테스트
 ├─ 라이브러리 구축
 ├─ WRF/CMAQ 컴파일
 └─ 모델 실행
```

---

# 3. Windows ↔ Linux 파일 전송 환경

## 3.1 FTP보다 SFTP 사용 권장

Windows에서 Linux로 소스 코드, 설정 파일, 결과 파일 등을 전송할 때 일반 FTP보다 **SFTP** 사용을 권장한다.

SFTP는 SSH 기반으로 통신하므로 전송 구간이 암호화되며, 별도의 FTP 서버를 구성하지 않아도 Linux의 SSH 서비스를 이용할 수 있다.

본 환경에서는 Windows에서 **WinSCP**와 같은 SFTP 클라이언트를 사용할 수 있다.

---

## 3.2 Linux SSH 서비스 확인

Linux에서 SSH 서비스 상태를 확인한다.

```bash
systemctl status sshd
```

서비스가 비활성 상태이면 root 권한으로 활성화한다.

```bash
systemctl enable --now sshd
```

다시 확인:

```bash
systemctl status sshd
```

정상적인 경우 `active (running)` 상태로 표시된다.

---

## 3.3 Linux IP 주소 확인

Linux에서 다음 명령을 실행한다.

```bash
ip addr
```

또는 간단히:

```bash
hostname -I
```

Windows에서 접속할 때 이 IP 주소를 사용한다.

---

## 3.4 WinSCP 접속 예

Windows의 WinSCP에서 다음과 같이 설정한다.

```text
파일 프로토콜 : SFTP
호스트 이름   : Linux IP 주소
포트 번호     : 22
사용자 이름   : Linux 일반 사용자 계정
비밀번호      : 해당 사용자 계정 비밀번호
```

접속 후 일반 사용자 홈 디렉터리로 파일을 전송한다.

예:

```text
/home/<username>/
```

Linux에서 전송 여부 확인:

```bash
cd ~
ls -l
```

---

## 3.5 Windows 텍스트 파일의 줄바꿈

Windows에서 만든 소스 파일은 CRLF 줄바꿈을 사용할 수 있다.

대부분의 Fortran 컴파일에는 문제가 없지만, shell script나 일부 설정 파일에서 문제가 발생하면 `dos2unix`를 사용할 수 있다.

설치:

```bash
sudo dnf install dos2unix
```

변환:

```bash
dos2unix filename
```

---

# 4. GNU Compiler 설치

## 4.1 설치 패키지

root 계정에서는 `sudo` 없이 다음 명령을 실행할 수 있다.

```bash
dnf install gcc gcc-c++ gcc-gfortran make
```

일반 사용자 계정에서 설치하는 경우:

```bash
sudo dnf install gcc gcc-c++ gcc-gfortran make
```

설치되는 주요 구성요소:

| 패키지 | 용도 |
|---|---|
| gcc | C Compiler |
| gcc-c++ | C++ Compiler |
| gcc-gfortran | Fortran Compiler |
| make | Build automation |

---

# 5. GNU Compiler 설치 확인

설치 후 일반 사용자 계정에서 다음 명령을 실행한다.

## 5.1 GCC

```bash
gcc --version
```

확인된 환경:

```text
gcc (GCC) 11.5.0 20240719 (Red Hat 11.5.0-14)
```

---

## 5.2 G++

```bash
g++ --version
```

확인된 환경:

```text
g++ (GCC) 11.5.0 20240719 (Red Hat 11.5.0-14)
```

---

## 5.3 GFortran

```bash
gfortran --version
```

확인된 환경:

```text
GNU Fortran (GCC) 11.5.0 20240719 (Red Hat 11.5.0-14)
```

---

## 5.4 GNU Make

```bash
make --version
```

확인된 환경:

```text
GNU Make 4.3
x86_64-redhat-linux-gnu
```

---

## 5.5 Compiler version 일치 여부

확인 결과:

```text
gcc       11.5.0
g++       11.5.0
gfortran  11.5.0
GNU Make  4.3
```

C, C++, Fortran이 모두 GCC 11.5.0 계열이므로 compiler family가 일치한다.

이 일관성은 이후 OpenMPI, HDF5, netCDF, I/O API, WRF 및 CMAQ를 동일한 compiler 계열로 구축할 때 중요하다.

---

# 6. Compiler 버전 정보를 파일로 저장

설치 환경을 기록하기 위해 버전 정보를 텍스트 파일로 저장할 수 있다.

예:

```bash
echo "=== GCC ===" > compiler_version.txt
gcc --version >> compiler_version.txt

echo "=== G++ ===" >> compiler_version.txt
g++ --version >> compiler_version.txt

echo "=== GFortran ===" >> compiler_version.txt
gfortran --version >> compiler_version.txt

echo "=== GNU Make ===" >> compiler_version.txt
make --version >> compiler_version.txt
```

내용 확인:

```bash
cat compiler_version.txt
```

`>`는 새 파일을 만들거나 기존 내용을 덮어쓰고, `>>`는 기존 파일의 마지막에 내용을 추가한다.

---

# 7. GFortran 기본 컴파일 테스트

OpenMPI 설치 전에 Fortran compiler가 단독으로 정상 작동하는지 확인할 수 있다.

## 7.1 테스트 소스 작성

```fortran
program test_fortran
  implicit none
  print *, "Fortran compiler OK"
end program test_fortran
```

파일명:

```text
test_fortran.f90
```

## 7.2 컴파일

```bash
gfortran test_fortran.f90 -o test_fortran
```

## 7.3 실행

```bash
./test_fortran
```

정상 예:

```text
 Fortran compiler OK
```

---

# 8. OpenMPI 설치

## 8.1 설치

root 계정에서:

```bash
dnf install openmpi openmpi-devel
```

일반 사용자 계정에서는:

```bash
sudo dnf install openmpi openmpi-devel
```

주요 패키지:

| 패키지 | 역할 |
|---|---|
| openmpi | MPI 실행환경 |
| openmpi-devel | MPI header 및 개발용 라이브러리 |

---

# 9. OpenMPI 환경 활성화

Rocky Linux 패키지로 설치한 OpenMPI는 Environment Modules를 이용하여 경로를 활성화할 수 있다.

일반 사용자 계정에서:

```bash
source /etc/profile.d/modules.sh
module load mpi/openmpi-x86_64
```

활성화 후 주요 실행파일 위치를 확인한다.

```bash
which mpicc
which mpifort
which mpirun
```

확인된 경로 예:

```text
/usr/lib64/openmpi/bin/mpicc
/usr/lib64/openmpi/bin/mpifort
/usr/lib64/openmpi/bin/mpirun
```

---

# 10. OpenMPI 버전 확인

```bash
mpirun --version
```

확인된 환경:

```text
mpirun (Open MPI) 4.1.1
```

따라서 현재 확인된 구성은 다음과 같다.

```text
gcc       11.5.0
g++       11.5.0
gfortran  11.5.0
GNU Make  4.3
OpenMPI   4.1.1
```

---

# 11. OpenMPI가 사용하는 Fortran Compiler 확인

`mpifort`는 독립적인 Fortran compiler가 아니라 실제 compiler와 MPI 라이브러리를 연결해주는 wrapper이다.

실제 사용되는 compiler를 확인한다.

```bash
mpifort --showme:command
```

확인 결과:

```text
gfortran
```

즉, OpenMPI의 Fortran wrapper가 시스템에 설치한 GNU Fortran을 정상적으로 사용하고 있다.

추가 정보 확인:

```bash
mpifort --showme
```

---

# 12. MPI 병렬 실행 테스트

OpenMPI는 설치 여부만 확인하지 않고 실제 병렬 실행까지 확인해야 한다.

## 12.1 테스트 프로그램 작성

파일명 예:

```text
mpi_test.f90
```

파일 내용:

```fortran
program hello_mpi
  use mpi
  implicit none

  integer :: ierr, rank, nprocs

  call MPI_Init(ierr)
  call MPI_Comm_rank(MPI_COMM_WORLD, rank, ierr)
  call MPI_Comm_size(MPI_COMM_WORLD, nprocs, ierr)

  print *, 'Hello from rank', rank, 'of', nprocs

  call MPI_Finalize(ierr)
end program hello_mpi
```

### 주의

프로그램 unit 이름을 단순히 `mpi_test`로 지정하면 사용 중인 MPI module의 내부 symbol과 이름 충돌이 발생할 수 있으므로, 테스트 프로그램 이름은 `hello_mpi`와 같이 구분되는 이름을 사용하는 것이 안전하다.

---

## 12.2 컴파일

```bash
mpifort mpi_test.f90 -o hello_mpi
```

컴파일 후 파일 확인:

```bash
ls -l
```

정상적인 경우:

```text
mpi_test.f90
hello_mpi
```

실행파일에는 실행 권한이 표시된다.

예:

```text
-rwxr-xr-x ... hello_mpi
```

---

## 12.3 4개 MPI process로 실행

```bash
mpirun -np 4 ./hello_mpi
```

정상 예:

```text
Hello from rank 0 of 4
Hello from rank 1 of 4
Hello from rank 2 of 4
Hello from rank 3 of 4
```

MPI 병렬 프로그램에서는 각 process의 출력 순서가 항상 0, 1, 2, 3 순서로 표시되지는 않는다.

출력 순서가 달라도 각 rank가 모두 실행되면 정상이다.

---

# 13. MPI 테스트 결과 파일 저장

MPI 결과를 텍스트 파일로 저장하려면 shell redirection을 사용한다.

```bash
mpirun -np 4 ./hello_mpi > mpitest_result.txt
```

확인:

```bash
cat mpitest_result.txt
```

표준 오류까지 함께 저장하려면:

```bash
mpirun -np 4 ./hello_mpi > mpitest_result.txt 2>&1
```

---

# 14. 대표적인 테스트 오류와 해결

## 14.1 실행파일을 찾을 수 없는 경우

오류 예:

```text
mpirun was unable to launch the specified application as it could not access
or execute an executable:

Executable: ./mpi_test
```

원인:

소스 파일 `mpi_test.f90`만 존재하고 실행파일을 아직 컴파일하지 않은 상태에서 `mpirun`을 실행한 경우이다.

해결:

먼저 컴파일한다.

```bash
mpifort mpi_test.f90 -o hello_mpi
```

이후 실행:

```bash
mpirun -np 4 ./hello_mpi
```

---

## 14.2 프로그램 이름 충돌

오류 예:

```text
'mpi_test' of module 'mpi' ... is also the name of the current program unit
```

또는:

```text
Name 'mpi_test' ... is an ambiguous reference
```

해결:

Fortran program unit의 이름을 다음과 같이 변경한다.

잘못된 예:

```fortran
program mpi_test
  use mpi
```

권장 예:

```fortran
program hello_mpi
  use mpi
```

마지막도 동일하게 변경한다.

```fortran
end program hello_mpi
```

---

## 14.3 module 명령을 찾을 수 없는 경우

먼저 modules 환경을 불러온다.

```bash
source /etc/profile.d/modules.sh
```

그 후:

```bash
module load mpi/openmpi-x86_64
```

---

## 14.4 mpirun 명령을 찾을 수 없는 경우

OpenMPI module이 로드되었는지 확인한다.

```bash
module list
```

필요하면:

```bash
module load mpi/openmpi-x86_64
```

그 후:

```bash
which mpirun
```

---

# 15. 설치 완료 확인 체크리스트

다음 항목을 모두 확인하면 GNU Compiler 및 OpenMPI 기본 환경 구축이 완료된 것으로 판단할 수 있다.

```text
[ ] gcc --version 정상
[ ] g++ --version 정상
[ ] gfortran --version 정상
[ ] make --version 정상
[ ] gcc/g++/gfortran 버전 family 일치
[ ] OpenMPI 설치 완료
[ ] module load mpi/openmpi-x86_64 성공
[ ] which mpicc 정상
[ ] which mpifort 정상
[ ] which mpirun 정상
[ ] mpirun --version 정상
[ ] mpifort --showme:command 결과가 gfortran
[ ] Fortran 단독 compile/run 성공
[ ] MPI Fortran compile 성공
[ ] mpirun -np 4 병렬 실행 성공
```

---

# 16. 현재 검증된 환경

본 설치에서 확인된 구성:

```text
OS             : Rocky Linux 9 계열
Platform       : x86_64
gcc            : 11.5.0
g++            : 11.5.0
gfortran       : 11.5.0
GNU Make       : 4.3
OpenMPI        : 4.1.1
MPI Fortran    : mpifort → gfortran
MPI Test       : 4 process 병렬 실행 성공
File Transfer  : SFTP 사용 가능
```

---

## 문서 정보

```text
문서명   : GNU_Compiler_OpenMPI_Installation_Guide.md
문서유형 : Compiler / MPI 설치 및 검증 가이드
적용대상 : Rocky Linux 9 계열 x86_64
```
