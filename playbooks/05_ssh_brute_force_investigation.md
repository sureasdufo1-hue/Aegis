# 🛡️ SOC Playbook 05: 무차별 대입 인증 공격(SSH & Web Auth Brute Force) 분석 가이드

---

## 1. 개요 (Overview)
- **위협 정의**: 공격자가 자동화 도구(Hydra, Medusa, Ncrack)를 사용하여 알려진 기본 계정(root, admin) 및 사전(Dictionary) 기반 패스워드를 고빈도로 대입하여 관리자 권한을 탈취하려는 공격.
- **MITRE ATT&CK**: `T1110` (Brute Force), `T1110.001` (Password Guessing)
- **탐지 룰 ID**: Suricata `sid:9020001` (SSH), `sid:9020010` (Web Login), Snort `sid:9100025`

---

## 2. 1차 관제 분석 절차 (Triage Steps)

### Step 1: 인증 실패 빈도 및 접속 대상 계정 식별
- **SSH 인증 로그(`auth.log` / `secure`)와 교차 분석**:
  ```bash
  # 희생 서버에서 최근 실패한 로그인 시도 추출
  grep "Failed password" /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -nr
  ```
- **성공(Accepted) 이벤트 발생 여부 확인 (최우선)**:
  ```bash
  grep "Accepted password" /var/log/auth.log
  ```
  - 만약 수많은 `Failed` 이후 `Accepted`가 발견되면 -> **즉시 침해사고(CRITICAL Incident) 격상**.

### Step 2: 출발지 IP 평판 및 공격 패턴 분석
- 외부 공인 IP인 경우 AbuseIPDB, Shodan 등에서 'SSH Brute-Force Botnet' 이력 확인.
- 내부망 IP인 경우 내부 호스트 감염 후 Lateral Movement(횡적 이동) 여부 조사.

---

## 3. 침해 대응 및 완화 조치 (Containment & Mitigation)

1. **공격자 IP 즉각 차단**:
   - 방화벽(`nftables`) 또는 `iptables`에서 해당 IP 차단.
2. **Fail2ban 연동 자동 차단**:
   - 5회 이상 인증 실패 시 24시간 자동 차단 정책 활성화:
     ```ini
     [sshd]
     enabled = true
     port = 22
     maxretry = 5
     bantime = 86400
     ```
3. **SSH 보안 하드닝**:
   - 루트 원격 로그인 금지: `/etc/ssh/sshd_config` ➔ `PermitRootLogin no`
   - 패스워드 인증 비활성화 및 공개키(ED25519) 인증 의무화.

---

## 4. 탐지 룰 튜닝 가이드 (Rule Tuning)
- 개발자/엔지니어의 자동화 배포 스크립트(Ansible, Terraform)에 의한 오탐 시:
  ```suricata
  # 배포 관리 서버 IP에 대한 임계치 예외 처리
  pass tcp 10.77.10.10 any -> $HOME_NET 22 (msg:"Whitelisted CI/CD Deployment Server"; sid:9020099; rev:1;)
  ```
