# Enterprise SOC Dashboard Design System

## 1. Design Philosophy

The design system for the **SOC Operations Console** is inspired by modern enterprise security monitoring platforms (CrowdStrike Falcon, Datadog Security, Splunk Enterprise Security).

### Core Design Invariants:
1. **Restrained Functional Palette**: Neon glows and decorative gradients are eliminated in favor of clean dark neutral surfaces (`#0b0f19`, `#0f172a`, `#1e293b`).
2. **Information Density with Breathing Room**: Tables and cards maximize screen utilization while maintaining comfortable padding and clear typography hierarchy.
3. **Dual Typography Standard**:
   - **Pretendard**: Used for Korean and English body copy, button labels, and explanatory prose.
   - **JetBrains Mono**: Used for IP addresses, CIDR blocks, ports, SIDs, rule IDs, and ISO timestamps.
4. **Multimodal Status Cues**: Statuses are never conveyed by color alone; text labels, badges, and icons are combined.

---

## 2. Color Palette & Semantic Tokens

| Token Name | Hex Code | Semantic Purpose | Example Component |
|---|---|---|---|
| `--color-bg-base` | `#0b0f19` | Main background viewport | `<body>` |
| `--color-surface-panel` | `#0f172a` (80% opacity) | Primary card surfaces & table backgrounds | `.soc-surface` |
| `--color-border-subtle` | `#1e293b` | Divider lines and container borders | `border-slate-800` |
| `--color-border-card` | `#334155` (50% opacity) | Card contours & hover borders | `.soc-surface-card` |
| `--color-severity-critical` | `#ef4444` | Urgent exploits, reverse shells, C2 beacons | Critical Badge / Metric |
| `--color-severity-high` | `#f97316` | Active attacks (SQLi, brute force) | High Severity Badge |
| `--color-severity-med` | `#eab308` | Scans, recon, anomaly alerts | Medium Severity Badge |
| `--color-severity-low` | `#3b82f6` | Policy deviations, protocol oddities | Low Severity Badge |
| `--color-ai-accent` | `#6366f1` / `#a855f7` | AI investigation reports & RAG citations | AI Card & Action Buttons |
| `--color-success-safe` | `#10b981` | Policy allowed, dry-run executed | Policy Allow Badge |
| `--color-telemetry-cyan` | `#06b6d4` | Live stream badges, Suricata alerts | Engine Badge & Live Pill |

---

## 3. Typography & Hierarchy

```text
Display Title      Pretendard Bold 16px / Leading 20px (#ffffff)
Section Headers    Pretendard Bold 14px / Leading 18px (#f8fafc)
Body Text          Pretendard Regular 12px / Leading 16px (#e2e8f0)
Muted Metadata     Pretendard Regular 11px (#94a3b8)
Technical Monospace JetBrains Mono Medium 11-12px (#38bdf8, #cbd5e1)
Code & Payloads    JetBrains Mono Regular 11px (#67e8f9)
```

---

## 4. UI Components

### 4.1 Segmented View Mode Toggle
Enables seamless switching between Original (EN), Korean (KO), and Split View:
```html
<div class="flex items-center rounded-lg bg-slate-800/80 p-0.5 border border-slate-700 text-xs">
    <button id="btn-mode-orig">원문 (EN)</button>
    <button id="btn-mode-ko">한국어 (KO)</button>
    <button id="btn-mode-split" class="bg-blue-600 text-white">나란히 보기 (Split)</button>
</div>
```

### 4.2 KPI Metric Cards
Structured with a distinct 4px colored accent bar on the left edge:
- **Total Alerts**: Blue accent
- **Critical Severity**: Red accent
- **High & Medium**: Yellow accent
- **Correlated Incidents**: Cyan accent
- **HITL Approvals**: Amber accent

### 4.3 Visual Attack Timeline
Renders killchain attack progression horizontally with clear sequence arrows:
```text
[⚡ 1단계: 정보 수집 및 정찰] ➔ [⚡ 2단계: 초기 침투 및 취약점 악용] ➔ [⚡ 3단계: 명령제어(C2)]
```

### 4.4 Data Table Standards
- Pinned header with semi-transparent background (`bg-slate-800/40`).
- Subtle row hover effect (`hover:bg-slate-800/30`).
- Monospace tabular alignment for timestamps and IP coordinates.
- Direct action buttons for Korean interpretation (`📖 해석`) and evidence inspection (`🔍 증적`).
