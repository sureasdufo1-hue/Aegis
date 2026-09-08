# Korean Localization & Terminology Specification

## 1. Scope & Architecture

The Korean Localization layer provides unambiguous, standardized translations for security concepts, severities, attack phases, policy verdicts, and approval workflows.

### Architectural Separation:
- **Presentation Layer**: Localization is purely a rendering concern.
- **Evidence Immutability**: Underlying data objects (`NormalizedAlert`, `Incident`, `SecurityEvidence`, `ActionApprovalRecord`) retain their original English identifiers, SIDs, IPs, and raw JSON logs.

```text
[ Raw Telemetry / Evidence ] (Immutable English / SIDs / IPs)
              │
              ▼
[ Deterministic Korean Dictionary ] (analyzer/ai/localization/korean_dict.py)
              │
              ▼
[ View Mode Segmented Control ]
   ├── Original (EN): Raw English signatures and codes
   ├── Korean (KO): Translated Korean labels
   └── Split View: Side-by-side Korean title with English signature
```

---

## 2. Core Terminology Mappings

### 2.1 Severities (위험도 매핑)

| English Identifier | Korean Label | Operational Definition |
|---|---|---|
| `CRITICAL` | **심각 (Critical)** | 즉각적인 격리 및 차단이 필요한 긴급 침해 사고 (RCE, C2 역방향 셸 등) |
| `HIGH` | **높음 (High)** | 활성 공격 시도 및 웹 취약점 악용 (SQL 인젝션, 무차별 대입 등) |
| `MEDIUM` | **보통 (Medium)** | 정찰 행위, 비정상 스캔 및 의심스러운 트래픽 활동 |
| `LOW` | **낮음 (Low)** | 보안 정책 위반 가능성 및 비인가 프로토콜 접근 |
| `INFORMATIONAL` | **정보 (Info)** | 시스템 감사 로그 및 일반 보안 통계 |

### 2.2 Attack Stages (공격 단계 매핑)

| English Stage | Korean Stage Label | Operational Meaning |
|---|---|---|
| `1. Reconnaissance` | **1단계: 정보 수집 및 정찰** | 열린 포트, 실행 서비스 및 취약점을 파악하기 위한 사전 스캔 단계 |
| `2. Initial Access / Exploitation` | **2단계: 초기 침투 및 취약점 악용** | 웹 애플리케이션 취약점이나 계정 대입을 통해 내부 진입을 시도하는 단계 |
| `3. Command & Control / Execution` | **3단계: 명령제어(C2) 및 악성코드 실행** | 타깃 시스템에 리버스 셸을 수립하거나 제어권을 탈취하는 고위험 단계 |
| `4. Exfiltration` | **4단계: 데이터 유출** | 내부 중요 자산이나 데이터베이스를 외부로 반출하는 단계 |

### 2.3 Policy Verdicts (결정론적 정책 검증 결과)

| Verdict Code | Korean Label | Safety Guard Meaning |
|---|---|---|
| `ALLOWED` | **정책 검증 통과 (승인 가능)** | 대상 IP가 보호 인프라와 겹치지 않으며 구문이 안전함 |
| `DENIED_PROTECTED_ASSET` | **정책 거부: 보호 인프라 차단 불가** | 게이트웨이, SIEM, DNS 등 운영 필수 자원은 차단 불가 |
| `DENIED_SYNTAX_ERROR` | **정책 거부: 비정상 구문 / 인젝션 감지** | 셸 메타문자(; & \| ` $ > <)가 포함되어 안전을 위해 차단 |
| `DENIED_INVALID_TARGET` | **정책 거부: 유효하지 않은 대상** | IPv4 주소 또는 CIDR 포맷 오류 |
| `DENIED_FAIL_CLOSED` | **정책 거부: 안전 기본값(Fail-Closed)** | 예외 또는 비정상 입력 발생 시 차단 |

### 2.4 Approval Status & Execution Modes

| Status Code | Korean Label | Meaning |
|---|---|---|
| `PENDING` | **분석가 검토 대기** | 분석가의 명시적 승인 전까지 대기 중 |
| `APPROVED` | **조치 승인됨** | 분석가가 정책 통과 조치를 승인함 |
| `REJECTED` | **분석가 반려됨** | 오탐 의심 또는 조치 불필요로 반려 |
| `EXECUTED` | **모의 실행 완료** | Dry-Run 시뮬레이션 규칙 생성 완료 |
| `EXPIRED` | **기한 만료** | 60분 TTL 초과로 승인 무효화 |

---

## 3. View Mode Mechanics

The segmented view mode is configured via client-side JavaScript and persisted in `localStorage`:

```javascript
// Example Translation Dispatcher
function getLocalizedSignature(sig) {
    const info = localizationDict?.signatures?.[sig];
    if (!info) return escapeHTML(sig);

    if (currentViewMode === 'original') {
        return escapeHTML(sig);
    } else if (currentViewMode === 'korean') {
        return `<span class="text-white font-medium">${escapeHTML(info.ko_title)}</span>`;
    } else {
        // Split View
        return `
            <div class="space-y-0.5">
                <span class="text-white font-medium">${escapeHTML(info.ko_title)}</span>
                <span class="block text-[11px] text-slate-400 font-mono">↳ ${escapeHTML(sig)}</span>
            </div>
        `;
    }
}
```
