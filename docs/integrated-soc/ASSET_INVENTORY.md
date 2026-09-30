# ASSET_INVENTORY — 자산 현황

관측일: 2026-09-23 KST. `VMware Tools`가 보고한 한 주소는 전체 NIC 설정 증거가 아니다.

| 자산 | 관측/문서 상태 | OS·CPU·RAM·Disk / 역할 | 판정 |
|---|---|---|---|
| `DESKTOP-QIFELML` | Windows 11 Education build 26100; RAM 63.8GiB; C: 여유 1153.2GiB | 현 조사 호스트, VMware/Docker 실행 | VERIFIED |
| `soc-attacker` | `vmrun list` 실행 중, 2 vCPU·4GB VMX | 게스트 IP/OS 미확인 | VERIFIED(실행), UNKNOWN(게스트) |
| `soc-gateway` | 실행 중, 2 vCPU·4GB·2 NIC VMX | VMware Tools 보고 `192.168.111.140` | VERIFIED(보고값) |
| `soc-victim` | 실행 중, 2 vCPU·4GB VMX | 보고 `10.77.30.100`; AGENTS 고정값 `.30.20`과 불일치 | VERIFIED(보고값), BLOCKED(기준 충돌) |
| `soc-sensor` | 실행 중, 2 vCPU·4GB·3 NIC VMX | 보고 `10.77.10.20`; 실제 캡처 NIC/패킷 미확인 | VERIFIED(보고값), UNKNOWN(캡처) |
| `soc-siem` | 실행 중, 2 vCPU·4GB VMX | 보고 `10.77.10.30`; 서비스 위치 미확인 | VERIFIED(보고값), UNKNOWN(서비스) |
| Docker Desktop | 로컬 Windows PC에서 ELK 3개·Wazuh 3개 컨테이너 실행 | 물리 LOG 서버가 아님 | VERIFIED |
| 관리자 PC `192.168.10.2` | M1/M2·M3~M7 목표 | 실제 호스트/OS/자원/서비스 미접근 | TARGET, UNKNOWN(런타임) |
| LOG 서버 `192.168.30.3` | M1/M2·M5/M6 목표 | M5 제안 Ubuntu 22.04, 4 vCPU/8GB/40GB, 5GB×2 RAID1; 실제 사양·rsyslog·RAID·ELK 미확인 | TARGET, UNKNOWN(런타임) |
| Analyse PC1 `.40.6` | M1/M2 목표 | L3 Gi1/0/4 `.40.5/30` 피어; PC2와 다른 장비 | TARGET, UNKNOWN(런타임) |
| Analyse PC2 | M1/M2 목표 | Gi1/0/13 SPAN 목적지; 관리 IP/NIC/OS/사양 미확인 | TARGET, UNKNOWN(런타임) |
| Web `172.16.10.10` | M3 목표 | Ubuntu 22.04, 2 vCPU/4GB/40GB 제안; 실제 구축 미확인 | TARGET, UNKNOWN(런타임) |
| DB `192.168.30.2` | M4 목표 | Ubuntu 22.04, 2 vCPU/4GB/40GB 제안; 실제 구축 미확인 | TARGET, UNKNOWN(런타임) |
| TrusGuard·L3SW·L2SW1·L2SW2·VM1·VM2·User PC | M1/M2 문서 자산 | 장비 접근/현재 실행 설정/포트 점유 미확인 | TARGET, UNKNOWN(런타임) |

자산의 실제 소유자·시리얼·물리 연결·스토리지 여유·백업 책임자는 현장 자료가 없어 미기록이다. 새 VM/NIC가 필요하다는 결론도 PC2와 LOG의 자원 조사 전에는 확정하지 않는다.
