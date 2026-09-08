# Human-in-the-Loop (HITL) Containment Approval UX Design

## 1. Safety Principles for Action Interfaces

The containment approval interface is the most critical boundary in the SOC console. A UX mistake here could result in operational disruptions or accidental self-lockouts.

### Core UX Rules:
1. **Unambiguous Action Labeling**: Buttons must explicitly specify the operational mode. Generic `[승인]` buttons are forbidden; `[✅ 모의 실행 승인 (Dry-Run)]` is required.
2. **Deterministic Pre-requisite Gate**: If a proposal failed policy validation (`DENIED_PROTECTED_ASSET` or `DENIED_SYNTAX_ERROR`), the approval button is **strictly disabled** with an explanatory tooltip.
3. **Exploratory Previews**: Analysts must be able to inspect the exact `nftables` / `iptables` rule syntax before approving.
4. **Audit Attribution**: Rejections require an analyst reason code; approvals capture reviewer username and UTC timestamp.

---

## 2. Containment Queue Table Layout

| Column Header | Data Rendered | Safety & UX Details |
|---|---|---|
| **승인 번호 (ID)** | `APR-87727348-028` | Monospace purple accent identifier. |
| **사고 식별자** | `INC-10.77.20.20-1787727348` | Cross-links directly to incident details. |
| **제안 조치 및 대상** | `공격자 IP 차단 (10.77.20.20)` | Action type in Korean with target IP highlighted in bold red. |
| **정책 검증 상태** | `✅ ALLOW (정책 통과)` | Green badge if valid; Red `🛑 DENIED` badge if violated. |
| **규칙 구문 프리뷰** | `nft add element inet filter...` | Truncated preview clickable to open full syntax modal. |
| **승인 상태** | `승인 대기 (PENDING)` | Yellow pulsing badge for pending items; Green for executed. |
| **분석가 의사결정** | Action Buttons | `[✅ 모의 실행 승인]` / `[❌ 반려]` / `[📜 실행 증적]` |

---

## 3. Decision Flows & Dialogs

### 3.1 Approval Confirmation Dialog
Before execution, the browser displays a prominent confirmation prompt:
> **[주의: 모의 실행 안내]**
> 조치 'APR-87727348-028'를 승인하시겠습니까?
> 현재 모드는 DRY_RUN으로 실제 호스트 방화벽 규칙을 변경하지 않고 시뮬레이션 구문을 안전하게 검증합니다.

### 3.2 Rejection Reason Prompt
When clicking `[❌ 반려]`, the analyst is prompted for a justification:
> *"반려 사유를 입력하세요 (선택): 분석가 판단: 오탐 의심 또는 조치 불필요"*
This justification is persisted in `ActionApprovalRecord.review_notes`.

### 3.3 Rule Preview Modal
Clicking on the truncated syntax displays the complete generated rule in an isolated code container:
```text
nft add element inet filter blacklist { 10.77.20.20 }
Quarantine TTL: 60 minutes
Execution Mode: DRY_RUN
```
