# 🛡️ SOC Investigation Playbooks Master Catalog (보안관제 대응 절차서)

> **시스템 역할**: 본 디렉토리의 플레이북 문서들은 AI-Orchestrated SOC Copilot의 **로컬 RAG(Retrieval-Augmented Generation) 지식 저장소(`KnowledgeStore`)**에 실시간 인덱싱되어, 로컬 LLM(Qwen 3.5)이 보안 침해사고를 분석하고 대응 권고안을 제시할 때 직접 참조하는 내부 공식 표준 절차서입니다.

---

## 📚 플레이북 목록 (Playbook Index)

| 번호 | 문서 파일 | 공격 유형 및 범위 | 주요 탐지 기법 & MITRE ATT&CK | 주요 권고 조치 |
|:---:|---|---|---|---|
| **01** | [01_port_scan_investigation.md](01_port_scan_investigation.md) | **포트 스캔 & 네트워크 정찰** | `T1595` Active Scanning<br>`T1046` Network Service Discovery | IP 평판 분석, 인바운드 차단, 내부 점검도구 화이트리스트 |
| **02** | [02_dos_flood_investigation.md](02_dos_flood_investigation.md) | **서비스 거부 공격 (DoS / SYN Flood)** | `T1498` Network Denial of Service<br>`T1498.001` Direct Network Flood | nftables 패킷 임계치 제어(Rate Limit), SYN Cookies 활성화 |
| **03** | [03_web_attack_investigation.md](03_web_attack_investigation.md) | **웹 애플리케이션 침해 (SQLi / RCE / Log4j)** | `T1190` Exploit Public-Facing App<br>`T1059` Command & Scripting | 200/500 응답코드 검증, 아웃바운드 C2 역접속 차단, 호스트 격리 |
| **04** | [04_malware_c2_investigation.md](04_malware_c2_investigation.md) | **악성코드 C2 통신 & DNS 터널링** | `T1071` Application Layer Protocol<br>`T1048` Exfiltration Over Protocol | C2 블랙리스트 등록, EDR 엔드포인트 네트워크 격리, 프로세스 포렌식 |
| **05** | [05_ssh_brute_force_investigation.md](05_ssh_brute_force_investigation.md) | **무차별 대입 인증 (SSH Brute Force)** | `T1110` Brute Force<br>`T1110.001` Password Guessing | auth.log 성공 여부 확인, Fail2ban 연동 자동 차단, 루트 로그인 차단 |

---

## 🔍 로컬 RAG 인덱싱 구조 및 동작 원리

1. **자동 문서 분할 (Chunking)**:
   - 각 플레이북 마크다운 파일의 `##` 대단락을 기준으로 청크(Chunk)를 자동 분할합니다.
   - 키워드(Keywords) 및 SHA-256 해시를 산출하여 무결성을 보장합니다.
2. **사고 시그니처 매칭 (Hybrid Keyword Match)**:
   - 침해사고의 시그니처명(예: `SQL Injection`, `Port Scan`, `Reverse Shell`)과 공격 단계(Recon, Exploitation, C2)를 기반으로 가장 적합한 플레이북 상위 2~3개 청크를 자동 검색합니다.
3. **LLM 프롬프트 주입 ([PLAYBOOK KNOWLEDGE])**:
   - 검색된 절차서 내용이 로컬 Qwen 3.5 모델의 컨텍스트로 전달되어, **사내 보안 정책과 100% 일치하는 일관된 대응 권고안(BLOCK_IP, ISOLATE_HOST 등)**을 도출합니다.
