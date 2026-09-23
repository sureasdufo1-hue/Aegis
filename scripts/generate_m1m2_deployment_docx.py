# -*- coding: utf-8 -*-
"""
Generates the comprehensive Enterprise SOC Deployment Manual in Microsoft Word (.docx) format
modeled after the structure, tables, code blocks, and styling of the reference document.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="CBD5E1", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def format_cell(cell, text, bold=False, color="1E293B", size_pt=9.5, align=WD_ALIGN_PARAGRAPH.LEFT, font_name="맑은 고딕"):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    # Convert hex to RGBColor
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    run.font.color.rgb = RGBColor(r, g, b)

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "맑은 고딕"
    run.font.size = Pt(16.0)
    run.bold = True
    run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A) # Slate-900

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "맑은 고딕"
    run.font.size = Pt(13.0)
    run.bold = True
    run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A) # Blue-900

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "맑은 고딕"
    run.font.size = Pt(11.0)
    run.bold = True
    run.font.color.rgb = RGBColor(0x33, 0x41, 0x55) # Slate-700

def add_body_paragraph(doc, text, bold_prefix=None, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.2
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "맑은 고딕"
        r_pre.font.size = Pt(10.0)
        r_pre.bold = True
        r_pre.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    run = p.add_run(text)
    run.font.name = "맑은 고딕"
    run.font.size = Pt(10.0)
    run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    return p

def add_code_block(doc, code_text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Inches(0.15)
    p.paragraph_format.line_spacing = 1.15
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:left w:val="single" w:sz="18" w:space="10" w:color="3B82F6"/></w:pBdr>')
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F1F5F9"/>')
    pPr.append(pBdr)
    pPr.append(shd)
    run = p.add_run(code_text.strip())
    run.font.name = 'Consolas'
    run.font.size = Pt(9.0)
    run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

def add_callout(doc, title, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Inches(0.15)
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="10" w:color="2563EB"/></w:pBdr>')
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="EFF6FF"/>')
    pPr.append(pBdr)
    pPr.append(shd)
    r_title = p.add_run(f"[{title}] ")
    r_title.bold = True
    r_title.font.name = '맑은 고딕'
    r_title.font.size = Pt(9.5)
    r_title.font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)
    r_text = p.add_run(text)
    r_text.font.name = '맑은 고딕'
    r_text.font.size = Pt(9.5)
    r_text.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

def style_table(table, col_widths, headers, rows_data):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, color="CBD5E1")
    
    # Header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        format_cell(hdr_cells[i], h, bold=True, color="FFFFFF", size_pt=9.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_background(hdr_cells[i], "404040")
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
    
    # Body rows
    for r_idx, r_data in enumerate(rows_data):
        row_cells = table.add_row().cells
        bg_color = "F8FAFC" if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, val in enumerate(r_data):
            align = WD_ALIGN_PARAGRAPH.CENTER if (c_idx in [0, 1] or "PASS" in val or "FAIL" in val or "TCP" in val or "UDP" in val or "IP" in val) else WD_ALIGN_PARAGRAPH.LEFT
            format_cell(row_cells[c_idx], val, bold=("PASS" in val or "FAIL" in val), color="1E293B", size_pt=9.0, align=align)
            set_cell_background(row_cells[c_idx], bg_color)
            set_cell_margins(row_cells[c_idx], top=100, bottom=100, left=140, right=140)

    # Set column widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = Inches(width)

def generate_docx(output_path):
    print(f"[*] Creating document: {output_path}")
    doc = docx.Document()
    
    # Set standard margins (1 inch)
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # =========================================================================
    # 표지 (Cover Page)
    # =========================================================================
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(36)
    p_meta.paragraph_format.space_after = Pt(12)
    r_meta = p_meta.add_run("ENTERPRISE SOC DETECTION & INCIDENT MONITORING PLATFORM")
    r_meta.font.name = "맑은 고딕"
    r_meta.font.size = Pt(11.0)
    r_meta.bold = True
    r_meta.font.color.rgb = RGBColor(0x25, 0x63, 0xEB) # Blue-600

    p_title1 = doc.add_paragraph()
    p_title1.paragraph_format.space_after = Pt(2)
    r_t1 = p_title1.add_run("M1·M2 통합 네트워크 보안 인프라 기반")
    r_t1.font.name = "맑은 고딕"
    r_t1.font.size = Pt(26.0)
    r_t1.bold = True
    r_t1.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    p_title2 = doc.add_paragraph()
    p_title2.paragraph_format.space_after = Pt(48)
    r_t2 = p_title2.add_run("차세대 SOC 관제 시스템 구축 및 현장 배포 가이드")
    r_t2.font.name = "맑은 고딕"
    r_t2.font.size = Pt(22.0)
    r_t2.bold = True
    r_t2.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    # Metadata Table
    t_cover = doc.add_table(rows=1, cols=2)
    t_cover_data = [
        ["대상 인프라", "M1·M2 통합 네트워크 보안 인프라 (Cisco L3/L2, AhnLab TrusGuard, VMware)"],
        ["관제 플랫폼 스택", "Suricata 8.0.6, Snort 3.12.2, ELK 8.17.3, Wazuh 4.14.7, FastAPI AI Web Console"],
        ["기준 네트워크", "VLAN 10/20/30, DMZ(172.16.10.0/24), SPAN 미러링(L3 Gi1/0/13)"],
        ["문서 버전", "v2.0 (상세 배포 및 다운로드 가이드 포함본)"],
        ["작성 일자", "2026-09-23"],
        ["작성자 / 부서", "SOC 보안엔지니어링팀"]
    ]
    style_table(t_cover, [1.8, 4.6], ["항목", "세부 내용"], t_cover_data)

    doc.add_page_break()

    # =========================================================================
    # 목차 (Table of Contents)
    # =========================================================================
    p_toc_title = doc.add_paragraph()
    p_toc_title.paragraph_format.space_before = Pt(12)
    p_toc_title.paragraph_format.space_after = Pt(18)
    r_toc = p_toc_title.add_run("목차")
    r_toc.font.name = "맑은 고딕"
    r_toc.font.size = Pt(18.0)
    r_toc.bold = True
    r_toc.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    toc_items = [
        ("1. 사업 및 구축 개요", "1.1 구축 목적 및 배경 / 1.2 배포 대상 및 범위 / 1.3 기본 원칙"),
        ("2. 배포 사전 준비 및 소프트웨어 다운로드 가이드", "2.1 하드웨어 사양 / 2.2 핵심 소프트웨어 공식 다운로드 명세표 / 2.3 포트 개방"),
        ("3. 네트워크 및 IP 주소 체계 매핑표", "3.1 Lab ↔ M1·M2 1:1 매핑표 / 3.2 물리 포트 및 가상 스위치 결선"),
        ("4. 단계별 상세 구축 및 배포 절차 (Step-by-Step)", "단계 1~7 상세 CLI 명령어, 파이프라인 구성 및 웹 콘솔 실행"),
        ("5. 네트워크 IP 변경 시 필수 수정 파일 가이드", "suricata.yaml, Logstash 파이프라인, provision script, app.py 수정"),
        ("6. 품질 검증 게이트 및 합격 판정표 (Quality Gates)", "GATE-NET-01 ~ GATE-SOAR-01 검증 기준 및 21개 자동화 테스트"),
        ("7. 장애 대응 및 롤백 가이드 (Troubleshooting & Rollback)", "주요 장애 원인별 조치표 및 비상 롤백 표준 절차")
    ]
    t_toc = doc.add_table(rows=1, cols=2)
    style_table(t_toc, [2.4, 4.0], ["장 번호 및 명칭", "주요 포함 내용"], toc_items)

    doc.add_page_break()

    # =========================================================================
    # 제1장. 사업 및 구축 개요
    # =========================================================================
    add_heading_1(doc, "1. 사업 및 구축 개요")
    
    add_heading_2(doc, "1.1 구축 목적 및 배경")
    add_body_paragraph(doc, 
        "본 매뉴얼은 'M1·M2 통합 네트워크 보안 인프라 구축 및 재구축 매뉴얼'에 명시된 물리·가상망 환경(AhnLab TrusGuard 차세대 방화벽, Cisco L3/L2 스위치, DMZ 웹 서버, VLAN 10/20/30 서버팜, VMware 게스트 가상망)에 최신 엔터프라이즈 보안관제(SOC) 플랫폼을 완벽히 이식하기 위한 표준 지침서입니다.")
    add_body_paragraph(doc,
        "단순한 도구 설치에 그치지 않고, '네트워크 트래픽 미러링 ➔ 듀얼 IDS(Suricata/Snort) 실시간 패킷 센싱 ➔ ELK/Wazuh SIEM 중앙 집중화 ➔ 다크모드 실시간 위협 지도 시각화 ➔ 로컬 AI 기반 4단계 심층 침해조사 ➔ SOAR 인간 승인 기반 원클릭 방화벽 차단'에 이르는 전주기 방어 체계를 다른 엔지니어가 처음부터 끝까지 혼자서 완벽하게 재현할 수 있도록 구체적인 명령어와 다운로드 경로를 제공합니다.")

    add_heading_2(doc, "1.2 배포 대상 및 시스템 구성")
    t_scope = doc.add_table(rows=1, cols=3)
    scope_data = [
        ["경계 방화벽", "AhnLab TrusGuard (eth0~eth3)", "외부망(eth1), 내부Transit(eth2), DMZ(eth3), 관리(eth0)"],
        ["백본 스위치", "Cisco Catalyst L3SW (cb-l3sw01)", "SVI 10/20/30 라우팅, Transit(Gi1/0/24), SPAN(Gi1/0/13)"],
        ["워크그룹 스위치", "Cisco L2SW1 / L2SW2", "L2SW1(업무망 Trunk 10,20), L2SW2(서버팜 Trunk 10,20,30)"],
        ["가상화 호스트", "Windows 10/11 (VMware Workstation)", "물리 Ethernet 2 전용 Bridged(VMnet2), 게스트 802.1Q 태깅"],
        ["네트워크 센서", "[soc-sensor] (구 Analyse PC 2)", "무IP 캡처 NIC (AF_PACKET) + Suricata 8.0.6 + Snort 3.12.2"],
        ["통합 SIEM 및 관제", "[soc-siem] (구 Analyse PC 1 / LOG)", "Docker ELK 8.17.3 + Wazuh 4.14.7 + FastAPI 웹 콘솔(8501)"]
    ]
    style_table(t_scope, [1.5, 2.4, 2.5], ["영역 구분", "대상 장비 및 시스템", "주요 역할 및 포트 구성"], scope_data)

    add_heading_2(doc, "1.3 기본 원칙 및 패킷 가시성 기준선")
    add_callout(doc, "핵심 원칙 1: 패킷 가시성 우선 (Visibility Before IDS)",
                "L3 스위치의 SPAN 트래픽이 센서의 캡처 인터페이스에서 tcpdump로 온전히 수신되기 전에는 다운스트림 IDS 및 SIEM 작업을 진행하지 않습니다. (GATE-NET-01 필수)")
    add_callout(doc, "핵심 원칙 2: 캡처 인터페이스 무IP 원칙 (Zero-IP Promiscuous)",
                "센서의 패킷 수집 전용 NIC에는 IP 주소를 일체 부여하지 않고 순수 수신(Promiscuous) 전용으로 운영하여 센서 자체의 네트워크 노출 및 공격을 원천 차단합니다.")
    add_callout(doc, "핵심 원칙 3: 고정 버전 정책 (Strict Pinned Versioning)",
                "실무 운영 안정성을 위해 모든 소프트웨어와 Docker 이미지는 검증된 고정 버전을 사용하며, 임의로 floating latest 태그를 사용하지 않습니다.")

    # =========================================================================
    # 제2장. 배포 사전 준비 및 소프트웨어 다운로드 가이드
    # =========================================================================
    add_heading_1(doc, "2. 배포 사전 준비 및 소프트웨어 다운로드 가이드")
    
    add_heading_2(doc, "2.1 하드웨어 및 운영체제 사전 요구사항")
    t_hw = doc.add_table(rows=1, cols=4)
    hw_data = [
        ["관제 서버 (soc-siem)\n(구 Analyse PC 1 / LOG)", "CPU 6코어 이상\nRAM 16GB~24GB\nSSD 100GB 이상", "Ubuntu 22.04 LTS 또는\nWindows 11 (WSL2)", "NIC 1개: L3SW Gi1/0/4 관리망(.40.6/30) 또는 VLAN 30(.30.3) 연결"],
        ["네트워크 센서 (soc-sensor)\n(구 Analyse PC 2)", "CPU 4코어 이상\nRAM 8GB~16GB\nSSD 50GB 이상", "Ubuntu 22.04 LTS Server", "NIC 2개 필수:\n• NIC 1 (수집용): L3SW Gi1/0/13 연결 (IP 없음)\n• NIC 2 (관리용): 관리망 연결"]
    ]
    style_table(t_hw, [1.8, 1.5, 1.5, 1.6], ["시스템 구분", "권장 하드웨어 사양", "권장 운영체제(OS)", "필수 네트워크 인터페이스(NIC)"], hw_data)

    add_heading_2(doc, "2.2 핵심 소프트웨어 및 도구 공식 다운로드 명세표")
    add_body_paragraph(doc, "공인된 공식 미러 및 패키지 관리자를 통해 각 소프트웨어의 정품 패키지를 다운로드합니다:")
    
    t_sw = doc.add_table(rows=1, cols=4)
    sw_data = [
        ["Git for Windows / Linux", "2.40+", "https://git-scm.com/downloads\n`sudo apt update && sudo apt install -y git`", "프로젝트 저장소 소스코드 복제"],
        ["Docker Desktop / Engine", "26.0+", "https://www.docker.com/products/docker-desktop/\n`curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh`", "ELK 및 Wazuh 컨테이너 런타임"],
        ["Python", "3.11.x", "https://www.python.org/downloads/\n`sudo apt install -y python3 python3-pip python3-venv`", "대시보드 프로비저닝 및 FastAPI 콘솔"],
        ["본 관제 시스템 저장소", "v1.0", "`git clone https://github.com/sureasdufo1-hue/Aegis.git Suricata-Snort-SOC-Lab`", "전체 룰셋, 파이프라인, 웹 콘솔 소스"],
        ["Suricata IDS", "8.0.6", "PPA: `sudo add-apt-repository ppa:oisf/suricata-stable -y`\n`sudo apt update && sudo apt install -y suricata jq`", "실시간 패킷 침해 탐지 (Primary IDS)"],
        ["Snort IDS & libDAQ", "3.12.2.0\n(DAQ 3.0.27)", "https://github.com/snort3/snort3/releases\nhttps://github.com/snort3/libdaq/releases", "오프라인 PCAP 검증 및 룰 교차 분석"],
        ["Elasticsearch", "8.17.3", "`docker.elastic.co/elasticsearch/elasticsearch:8.17.3`", "분산 보안 빅데이터 색인 엔진"],
        ["Logstash", "8.17.3", "`docker.elastic.co/logstash/logstash:8.17.3`", "실시간 EVE/Syslog 파이프라인 파싱"],
        ["Kibana", "8.17.3", "`docker.elastic.co/kibana/kibana:8.17.3`", "16개 패널 관제 대시보드 & 위협 지도"],
        ["Wazuh Manager/Indexer", "4.14.7", "`wazuh/wazuh-manager:4.14.7`, `wazuh-indexer:4.14.7`", "호스트 엔드포인트 SIEM 통합"],
        ["Wazuh Agent (Linux)", "4.14.7", "https://packages.wazuh.com/4.x/apt/\n`curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | sudo apt-key add -`", "DMZ Web, DB 서버 호스트 감사 로그 수집"],
        ["Ollama (로컬 LLM)", "0.3.0+", "https://ollama.com/download\n`curl -fsSL https://ollama.com/install.sh | sh`", "AI 심층 침해조사 파이프라인 추론 엔진"],
        ["Qwen 추론 모델", "7B / 9B", "`ollama pull qwen2.5:7b` (또는 `qwen2.5-coder:7b`)", "온프레미스 폐쇄망 보안 인과관계 분석"],
        ["Wireshark & Npcap", "최신 안정판", "https://www.wireshark.org/download.html\nhttps://npcap.com/#download", "패킷 로우레벨 디버깅 및 포렌식"]
    ]
    style_table(t_sw, [1.5, 0.9, 2.5, 1.5], ["소프트웨어 명칭", "권장 버전", "공식 다운로드 경로 및 명령어", "주요 역할 및 비고"], sw_data)

    add_heading_2(doc, "2.3 네트워크 포트 및 방화벽 개방 요구사항")
    t_ports = doc.add_table(rows=1, cols=4)
    ports_data = [
        ["센서 (soc-sensor)", "관제 서버 (soc-siem)", "5044 / TCP", "Suricata EVE 로그 전송 (Logstash Beats)"],
        ["센서 (soc-sensor)", "관제 서버 (soc-siem)", "5045 / TCP", "Snort 3 알림 로그 스트림 전송"],
        ["TrusGuard 방화벽", "관제 서버 (soc-siem)", "5514 / UDP", "방화벽 차단/세션 Syslog 수신"],
        ["DMZ Web / DB 서버", "관제 서버 (soc-siem)", "1514 / TCP", "Wazuh Agent 이벤트 보고"],
        ["DMZ Web / DB 서버", "관제 서버 (soc-siem)", "1515 / TCP", "Wazuh Agent 자동 등록 (Enrollment)"],
        ["보안 분석가 PC", "관제 서버 (soc-siem)", "5602 / TCP", "Kibana 엔터프라이즈 관제 대시보드 웹 접속"],
        ["보안 분석가 PC", "관제 서버 (soc-siem)", "8501 / TCP", "FastAPI AI 관제 포털 및 인간 승인 큐 접속"],
        ["관제 서버 내부", "로컬호스트", "11434 / TCP", "Ollama LLM 추론 API (내부 전용 바인딩)"]
    ]
    style_table(t_ports, [1.6, 1.6, 1.2, 2.0], ["출발지 (Source)", "목적지 (Destination)", "포트 / 프로토콜", "용도"], ports_data)

    # =========================================================================
    # 제3장. 네트워크 및 IP 주소 체계 매핑표
    # =========================================================================
    add_heading_1(doc, "3. 네트워크 및 IP 주소 체계 매핑표")
    
    add_heading_2(doc, "3.1 Lab 격리망 ↔ M1·M2 실제 인프라 1:1 대응표")
    t_map = doc.add_table(rows=1, cols=4)
    map_data = [
        ["외부 / 공격망", "10.77.20.0/24", "10.10.70.128/25", "TrusGuard eth1 (10.10.70.214, 상위 GW .129)"],
        ["방화벽 SNAT_IP", "N/A", "10.10.70.163", "내부망에서 외부 나갈 때 출발지 변환 객체"],
        ["방화벽 WEB_VIP", "N/A", "10.10.70.164", "외부에서 DMZ Web 접근 시 목적지 변환 객체"],
        ["방화벽 Transit", "10.77.10.1 ↔ .20.1", "192.168.40.1/30 ↔ .40.2/30", "TrusGuard eth2 ↔ Cisco L3SW Gi1/0/24"],
        ["DMZ 웹 서버", "N/A", "172.16.10.10/24", "TrusGuard eth3 (GW: 172.16.10.1)"],
        ["VLAN 10 (관리망)", "10.77.10.0/24", "192.168.10.0/24", "L3 SVI .10.1 (Admin PC: .10.2, VM1: .10.101)"],
        ["VLAN 20 (내부망)", "10.77.20.0/24", "192.168.20.0/24", "L3 SVI .20.1 (User PC: .20.2, VM2: .20.101)"],
        ["VLAN 30 (서버팜)", "10.77.30.0/24", "192.168.30.0/24", "L3 SVI .30.1 (DB: .30.2, LOG/SIEM: .30.3)"],
        ["Analyse 관리망", "N/A", "192.168.40.4/30", "L3SW Gi1/0/4 (.40.5) ↔ 관제 서버 (.40.6)"],
        ["SPAN 패킷 미러링", "Hyper-V Port Mirror", "Cisco SPAN (Gi1/0/13)", "Source: Gi1/0/24 (양방향) ➔ Dest: Gi1/0/13"]
    ]
    style_table(t_map, [1.4, 1.4, 1.7, 1.9], ["영역 구분", "기존 실습 Lab 기준", "M1·M2 실제 환경 IP / 객체명", "비고 및 연결 인터페이스"], map_data)

    # =========================================================================
    # 제4장. 단계별 상세 구축 및 배포 절차 (Step-by-Step)
    # =========================================================================
    add_heading_1(doc, "4. 단계별 상세 구축 및 배포 절차 (Step-by-Step)")
    
    add_heading_2(doc, "단계 1: L3 스위치 SPAN 포트 미러링 활성화 (Cisco cb-l3sw01)")
    add_body_paragraph(doc, "Cisco L3 스위치 콘솔 케이블 연결 후 방화벽 Transit 트래픽(Gi1/0/24)을 센서 연결 포트(Gi1/0/13)로 복제 송출합니다:")
    add_code_block(doc, """cb-l3sw01# configure terminal

! 1. 방화벽 Transit 인터페이스 확인 (Source 대상)
interface GigabitEthernet1/0/24
 description TRANSIT_TO_TRUSGUARD_ETH2
 no switchport
 ip address 192.168.40.2 255.255.255.252
 no shutdown
exit

! 2. 센서 연결 포트 설정 (Destination 대상 - IP 설정 제거 및 활성화)
interface GigabitEthernet1/0/13
 description SPAN_DESTINATION_TO_SOC_SENSOR
 no shutdown
exit

! 3. SPAN 모니터 세션 구성 (양방향 트래픽 미러링)
monitor session 1 source interface GigabitEthernet1/0/24 both
monitor session 1 destination interface GigabitEthernet1/0/13
end

! 4. 설정 검증 및 메모리 저장
show monitor session all
copy running-config startup-config""")

    add_heading_2(doc, "단계 2: 관제 소스코드 다운로드 및 환경 변수 구성")
    add_body_paragraph(doc, "관제 서버(soc-siem) 및 센서 서버(soc-sensor)에서 프로젝트 소스코드를 다운로드하고 인증 환경 변수를 구성합니다:")
    add_code_block(doc, """# 1. 작업 디렉터리 생성 및 소스코드 Clone
mkdir -p /opt/soc-platform
cd /opt/soc-platform
git clone https://github.com/sureasdufo1-hue/Aegis.git Suricata-Snort-SOC-Lab
cd Suricata-Snort-SOC-Lab

# 2. 배포 환경 변수 템플릿 복사 및 권한 제한
cp .env.example .env
chmod 600 .env

# 3. .env 파일 내 ELASTIC_PASSWORD 및 인증 정보 설정
sed -i 's/ELASTIC_PASSWORD=.*/ELASTIC_PASSWORD=changeme_soc_lab_strong_pass_2026/' .env""")

    add_heading_2(doc, "단계 3: 네트워크 패킷 센서(soc-sensor / 구 Analyse PC 2) 설치 및 설정")
    add_body_paragraph(doc, "센서 서버의 ens33 인터페이스가 L3SW Gi1/0/13에 연결된 상태에서 패킷 수집 및 탐지 엔진을 가동합니다:")
    add_code_block(doc, """# 3.1 캡처 인터페이스 무IP 및 프로미스큐어스 모드 설정
sudo ip -4 addr flush dev ens33
sudo ip -6 addr flush dev ens33
sudo ip link set ens33 promisc on
sudo ip link set ens33 up

# 3.2 패킷 미러링 수신 확인 (GATE-NET-01 게이트 검증)
sudo tcpdump -eni ens33 -c 10

# 3.3 Suricata 최신 안정판 설치
sudo add-apt-repository ppa:oisf/suricata-stable -y
sudo apt update && sudo apt install -y suricata jq

# 3.4 홈 네트워크 기준선을 M1·M2 환경으로 수정 (/etc/suricata/suricata.yaml)
sudo tee -a /etc/suricata/suricata.yaml > /dev/null << 'EOF'
vars:
  address-groups:
    HOME_NET: "[192.168.10.0/24,192.168.20.0/24,192.168.30.0/24,172.16.10.0/24,192.168.40.0/30]"
    EXTERNAL_NET: "!$HOME_NET"
    HTTP_SERVERS: "[172.16.10.10]"
    SQL_SERVERS: "[192.168.30.2]"

af-packet:
  - interface: ens33
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes
    use-mmap: yes

default-log-dir: /var/log/suricata
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types: [alert, http, dns, tls]
EOF

# 3.5 구문 검증 및 서비스 기동
sudo suricata -T -c /etc/suricata/suricata.yaml
sudo systemctl restart suricata && sudo systemctl enable suricata""")

    add_heading_2(doc, "단계 4: 중앙 SIEM 플랫폼(soc-siem) 기동 (Docker ELK 8.17.3 + Wazuh)")
    add_body_paragraph(doc, "관제 서버(192.168.40.6 또는 192.168.30.3)에서 Docker Compose를 사용하여 컨테이너 스택을 기동합니다:")
    add_code_block(doc, """cd /opt/soc-platform/Suricata-Snort-SOC-Lab

# 1. Docker Compose 구성 사전 검증
docker compose -f infrastructure/elk/docker-compose.elk.yml config

# 2. ELK 스택 백그라운드 기동
docker compose -f infrastructure/elk/docker-compose.elk.yml up -d

# 3. 컨테이너 헬스체크 (모두 healthy 상태 확인)
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" """)

    add_heading_2(doc, "단계 5: 키바나 관제 대시보드 및 실시간 위협 지도 프로비저닝")
    add_body_paragraph(doc, "M1·M2 네트워크에 특화된 Ingest Pipeline, Data View, 16개 패널 대시보드, 전세계 실시간 위협 지도를 1회 자동 생성합니다:")
    add_code_block(doc, """# 프로비저닝 스크립트 실행
python3 infrastructure/elk/scripts/provision_kibana_dashboard.py""")
    add_callout(doc, "프로비저닝 성공 확인", 
                "스크립트 실행 완료 시 '>>> Phase ELK-11 Kibana Enterprise Threat Map Dashboard: PASS <<<' 문구가 출력되어야 합니다.")

    add_heading_2(doc, "단계 6: AhnLab TrusGuard 방화벽 Syslog 연동")
    add_body_paragraph(doc, "TrusGuard 관리자 웹 GUI(https://10.0.0.254)에 접속하여 방화벽 로그를 관제 서버로 실시간 전송합니다:")
    add_body_paragraph(doc, "1. '기본 설정' ➔ '로그/알람' ➔ 'Syslog 서버' 이동", bold_prefix="[1] 메뉴 이동: ")
    add_body_paragraph(doc, "서버 IP: 192.168.40.6 (또는 192.168.30.3) | 포트: 5514 (UDP) | 로그 유형: 보안정책(차단/허용), NAT 변환, 침입탐지(IPS) 전체 체크", bold_prefix="[2] 파라미터 등록: ")
    add_body_paragraph(doc, "'적용(Apply)'을 클릭하여 방화벽 룰에 즉시 반영", bold_prefix="[3] 정책 반영: ")

    add_heading_2(doc, "단계 7: AI 침해사고 조사 및 SOAR 웹 콘솔 가동 (FastAPI + Ollama)")
    add_body_paragraph(doc, "로컬 LLM 추론 엔진과 FastAPI 웹 관제 콘솔을 가동합니다:")
    add_code_block(doc, """# 7.1 로컬 LLM 추론 엔진 기동
sudo systemctl start ollama
ollama pull qwen2.5:7b

# 7.2 FastAPI 웹 콘솔 백그라운드 실행 (포트 8501)
source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8501 --reload &""")
    add_body_paragraph(doc, "• Kibana 대시보드 접속 URL: http://<관제서버IP>:5602/app/dashboards#/view/soc-unified-threat-dashboard\n• SOC 웹 포털 콘솔 접속 URL: http://<관제서버IP>:8501")

    # =========================================================================
    # 제5장. 네트워크 IP 변경 시 필수 수정 파일 가이드
    # =========================================================================
    add_heading_1(doc, "5. 네트워크 IP 변경 시 필수 수정 파일 가이드")
    add_body_paragraph(doc, "현장 네트워크 상황에 따라 서브넷이 변경될 경우, 아래 4개 핵심 파일만 수정하면 전체 관제 파이프라인이 자동 연동됩니다:")

    t_cheat = doc.add_table(rows=1, cols=4)
    cheat_data = [
        ["suricata/suricata.yaml", "vars.address-groups.HOME_NET", "[192.168.0.0/16, 172.16.10.0/24]", "M1·M2 내부망 서브넷 전체를 대괄호 내에 등록"],
        ["infrastructure/elk/scripts/\nprovision_kibana_dashboard.py", "provision_geoip_pipeline_and_mappings()\nPainless Script", "10.10.70.x, 172.16.10.10", "IP별 국가/도시명/위경도(GeoPoint) 매핑 수정"],
        ["infrastructure/elk/pipeline/\nfirewall.conf", "syslog udp port", "5514 / UDP", "TrusGuard Syslog 전송 포트와 일치시킴"],
        ["dashboard/app.py", "PROTECTED_SUBNETS", "['192.168.30.0/24', '172.16.10.0/24']", "SOAR IP 차단 시 보호해야 할 핵심 서버 대역 정의"]
    ]
    style_table(t_cheat, [1.8, 1.6, 1.4, 1.6], ["수정 대상 파일", "수정 대상 파라미터", "기본 설정값", "현장 변경 시 가이드"], cheat_data)

    # =========================================================================
    # 제6장. 품질 검증 게이트 및 합격 판정표
    # =========================================================================
    add_heading_1(doc, "6. 품질 검증 게이트 및 합격 판정표 (Quality Gates)")
    add_body_paragraph(doc, "모든 설치 및 설정이 완료된 후, 6대 품질 게이트를 점검하여 객관적인 배포 합격 여부를 판정합니다:")

    t_gate = doc.add_table(rows=1, cols=5)
    gate_data = [
        ["GATE-NET-01", "L3 SPAN 패킷 미러링", "sudo tcpdump -eni ens33 -c 10", "FW Transit 통과 패킷 10개 이상 관측", "PASS"],
        ["GATE-SURI-01", "Suricata 패킷 실시간 탐지", "curl 공격 시도 후 tail -n 1 eve.json", "event_type: 'alert' JSON 레코드 생성", "PASS"],
        ["GATE-SIEM-01", "ELK 인프라 컨테이너 상태", "docker ps 및 curl _cluster/health", "클러스터 상태 green, 3개 컨테이너 healthy", "PASS"],
        ["GATE-MAP-01", "실시간 전세계 위협 지도", "브라우저 키바나 맵 레이어 확인", "TOC 경고(⚠️) 0건, 레드 마커 정상 표시", "PASS"],
        ["GATE-AI-01", "AI 심층 침해조사 파이프라인", "FastAPI 콘솔에서 [AI 심층 조사] 클릭", "타이머 동작 후 4단계 스텝 모두 ✅ 완료 표시", "PASS"],
        ["GATE-SOAR-01", "인간 승인 큐 차단 연계", "[승인] 버튼 클릭 후 방화벽/L3 차단 명령", "nftables / Cisco ACL 차단 규칙 정상 주입", "PASS"]
    ]
    style_table(t_gate, [1.2, 1.4, 1.8, 1.4, 0.6], ["게이트 ID", "점검 대상 항목", "검증 기준 및 확인 명령어", "기대 결과 (PASS 기준)", "판정"], gate_data)

    add_body_paragraph(doc, "자동화 테스트 실행 결과 (단위/통합 테스트 21개 항목):", bold_prefix="[자동화 검증 스위트] ")
    add_code_block(doc, """pytest tests/test_elk_infrastructure.py tests/test_dashboard_track2_ux.py
======================= 21 passed, 3 warnings in 5.12s ========================""")

    # =========================================================================
    # 제7장. 장애 대응 및 롤백 가이드
    # =========================================================================
    add_heading_1(doc, "7. 장애 대응 및 롤백 가이드 (Troubleshooting & Rollback)")
    
    add_heading_2(doc, "7.1 주요 장애 증상별 원인 및 조치표")
    t_trb = doc.add_table(rows=1, cols=4)
    trb_data = [
        ["Kibana에 패킷 로그가 전혀 수집되지 않음", "센서 서버의 eve.json 파일 크기 증가 확인", "SPAN 세션 미러링 미동작 또는 포트 5044 차단", "1) L3SW `show monitor session 1` 확인\n2) 센서에서 `nc -zv <관제IP> 5044` 통신 점검"],
        ["세계 지도에 마커가 안 보이고 ⚠️ 아이콘 발생", "키바나 맵 레이어 TOC 경고 메시지 클릭", "Data View indexPatternId 불일치 또는 Fielddata 미적용", "python3 infrastructure/elk/scripts/provision_kibana_dashboard.py 재실행 후 Ctrl+F5"],
        ["AI 조사 모달창이 진행 중 상태로 멈춤", "개발자 도구(F12) 네트워크 응답 확인", "백엔드 조사 완료 후 UI 스텝 배지 업데이트 누락", "본 저장소 최신 버전 적용 확인 (커밋 5c9e947 적용 시 4단계 자동 완료)"],
        ["방화벽 Syslog가 Logstash에 안 들어옴", "sudo netstat -unlp | grep 5514 확인", "TrusGuard Syslog 전송 포트 불일치 또는 UDP 드롭", "TrusGuard 정책의 Syslog 서버 IP 및 포트 5514 재확인"]
    ]
    style_table(t_trb, [1.6, 1.4, 1.6, 1.8], ["증상 (Symptom)", "1차 점검 사항", "근본 원인", "권장 조치 및 복구 방법"], trb_data)

    add_heading_2(doc, "7.2 비상 롤백 표준 절차")
    add_body_paragraph(doc, "운영 환경에 예기치 못한 네트워크 지연이나 장애가 발생할 경우 아래 순서로 신속히 복구합니다:")
    add_code_block(doc, """! 1. L3 스위치 SPAN 포트 미러링 즉시 해제 (네트워크 부하 제거)
cb-l3sw01# configure terminal
no monitor session 1
end

# 2. 관제 서버 Docker 컨테이너 일괄 중지
docker compose -f infrastructure/elk/docker-compose.elk.yml down

# 3. TrusGuard 방화벽 Syslog 전송 중지
TrusGuard 웹 GUI ➔ 기본 설정 ➔ 로그/알람 ➔ 등록된 Syslog 서버 비활성화/삭제""")

    # Save document
    doc.save(output_path)
    print(f"[PASS] Successfully generated Word manual: {output_path}")

if __name__ == "__main__":
    out = os.path.abspath(r"docs/04-deployment/M1M2_SOC_INTEGRATION_DEPLOYMENT_MANUAL.docx")
    generate_docx(out)
