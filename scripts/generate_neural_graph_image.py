#!/usr/bin/env python3
"""
Generate ultra-high resolution screenshot/graphic of the Cyber Neural Knowledge Graph (사이버 신경망 지식 그래프)
matching the Obsidian D3 Force Graph in dashboard/templates/index.html.
Output: docs/assets/cyber_neural_knowledge_graph.png
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent.parent.resolve()
OUTPUT_PATH = BASE_DIR / "docs" / "assets" / "cyber_neural_knowledge_graph.png"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

FONT_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_REG = "C:/Windows/Fonts/malgun.ttf"
FONT_MONO = "C:/Windows/Fonts/consola.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = bbox
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

def main():
    W, H = 1920, 1080
    im = Image.new("RGBA", (W, H), (11, 15, 25, 255)) # Dark slate bg
    draw = ImageDraw.Draw(im)

    f_title = get_font(FONT_BOLD, 22)
    f_sub = get_font(FONT_REG, 15)
    f_badge = get_font(FONT_BOLD, 13)
    f_node = get_font(FONT_BOLD, 14)
    f_node_sub = get_font(FONT_REG, 12)
    f_mono = get_font(FONT_MONO, 14)
    f_mono_sm = get_font(FONT_REG, 12) # Korean regular for small text
    f_korean_bold = get_font(FONT_BOLD, 14)
    f_korean_lg = get_font(FONT_BOLD, 18)

    # 1. Outer Container Card
    pad = 30
    draw_rounded_rect(draw, (pad, pad, W - pad, H - pad), radius=16, fill=(15, 23, 42, 255), outline=(30, 41, 59, 255), width=2)

    # 2. Panel Header
    h_y = pad + 15
    # Pulsing dot
    draw.ellipse([pad + 25, h_y + 8, pad + 37, h_y + 20], fill=(6, 182, 212, 255))
    draw.text((pad + 48, h_y + 4), "사이버 신경망 지식 그래프", font=f_title, fill=(255, 255, 255))
    draw.text((pad + 345, h_y + 8), "|  Obsidian-Style Interactive Threat Topology", font=f_sub, fill=(56, 189, 248))

    # Badge: D3 FORCE SIMULATION ACTIVE
    draw_rounded_rect(draw, (pad + 730, h_y + 6, pad + 970, h_y + 30), radius=12, fill=(8, 51, 68, 255), outline=(14, 116, 144, 255))
    draw.text((pad + 745, h_y + 9), "D3 FORCE SIMULATION ACTIVE", font=f_badge, fill=(34, 211, 238))

    # Toolbar Controls (Right side of header)
    # Search Box
    s_x = W - pad - 570
    draw_rounded_rect(draw, (s_x, h_y + 3, s_x + 200, h_y + 33), radius=8, fill=(15, 23, 42, 255), outline=(51, 65, 85, 255))
    draw.text((s_x + 12, h_y + 9), "IP, SID, TTP 검색...", font=f_mono_sm, fill=(203, 213, 225))

    # Trace Button
    t_x = s_x + 215
    draw_rounded_rect(draw, (t_x, h_y + 3, t_x + 140, h_y + 33), radius=8, fill=(69, 10, 10, 255), outline=(153, 27, 27, 255))
    draw.text((t_x + 15, h_y + 8), "⚡ 침투 경로 추적", font=f_badge, fill=(252, 165, 165))

    # Freeze Button
    fr_x = t_x + 150
    draw_rounded_rect(draw, (fr_x, h_y + 3, fr_x + 100, h_y + 33), radius=8, fill=(30, 41, 59, 255), outline=(71, 85, 105, 255))
    draw.text((fr_x + 15, h_y + 8), "❄️ 물리 고정", font=f_badge, fill=(226, 232, 240))

    # Reset Button
    r_x = fr_x + 110
    draw_rounded_rect(draw, (r_x, h_y + 3, r_x + 80, h_y + 33), radius=8, fill=(30, 41, 59, 255), outline=(71, 85, 105, 255))
    draw.text((r_x + 12, h_y + 8), "🔄 뷰 리셋", font=f_badge, fill=(226, 232, 240))

    # Separator Line
    draw.line([(pad, h_y + 48), (W - pad, h_y + 48)], fill=(30, 41, 59, 255), width=2)

    # 3. Sub-header Legend Bar
    leg_y = h_y + 58
    draw.text((pad + 25, leg_y + 4), "노드 범례 (Node Legend):", font=f_korean_bold, fill=(148, 163, 184))

    legends = [
        ("공격자 (Attacker)", (239, 68, 68), (69, 10, 10)),
        ("게이트웨이 (Gateway)", (245, 158, 11), (69, 26, 3)),
        ("피해자/자산 (Victim)", (16, 185, 129), (6, 78, 59)),
        ("센서 (Sensor)", (14, 165, 233), (12, 74, 110)),
        ("Suricata 룰 (Rule)", (168, 85, 247), (59, 7, 100)),
        ("MITRE TTP", (234, 179, 8), (66, 32, 6)),
        ("HITL 차단 승인", (16, 185, 129), (6, 78, 59))
    ]
    cur_x = pad + 200
    for name, border_col, bg_col in legends:
        bbox = draw.textbbox((0, 0), name, font=f_mono_sm)
        bw = (bbox[2] - bbox[0]) + 24
        draw_rounded_rect(draw, (cur_x, leg_y + 2, cur_x + bw, leg_y + 24), radius=10, fill=bg_col + (255,), outline=border_col + (255,))
        # Dot
        draw.ellipse([cur_x + 6, leg_y + 8, cur_x + 14, leg_y + 16], fill=border_col + (255,))
        draw.text((cur_x + 18, leg_y + 4), name, font=f_mono_sm, fill=(241, 245, 249))
        cur_x += bw + 8

    # 4. Main Split: Left Graph Area (8 cols = ~1280px) | Right Inspector Panel (4 cols = ~550px)
    split_x = pad + 1280
    graph_top = leg_y + 35
    graph_bottom = H - pad - 15

    # Graph canvas background with subtle grid dots
    draw_rounded_rect(draw, (pad + 15, graph_top, split_x - 15, graph_bottom), radius=12, fill=(8, 12, 22, 255), outline=(30, 41, 59, 255))

    # Grid background dots
    for gx in range(pad + 35, split_x - 20, 60):
        for gy in range(graph_top + 20, graph_bottom - 20, 60):
            draw.ellipse([gx, gy, gx + 2, gy + 2], fill=(30, 41, 59, 120))

    # --- DEFINE NEURAL NETWORK NODES & LINKS ---
    nodes = {
        "attacker": {"pos": (pad + 160, graph_top + 340), "color": (239, 68, 68), "r": 34, "label": "soc-attacker", "sub": "10.77.20.20"},
        "recon_rule": {"pos": (pad + 380, graph_top + 160), "color": (168, 85, 247), "r": 26, "label": "SID:9000001", "sub": "Nmap Recon"},
        "brute_rule": {"pos": (pad + 440, graph_top + 280), "color": (168, 85, 247), "r": 26, "label": "SID:9020001", "sub": "SSH Brute"},
        "sqli_rule": {"pos": (pad + 420, graph_top + 420), "color": (168, 85, 247), "r": 28, "label": "SID:9010001", "sub": "SQLi UNION"},
        "c2_rule": {"pos": (pad + 390, graph_top + 550), "color": (168, 85, 247), "r": 26, "label": "SID:9030001", "sub": "Reverse Shell"},
        
        "ttp_recon": {"pos": (pad + 640, graph_top + 120), "color": (234, 179, 8), "r": 24, "label": "T1046", "sub": "Network Discovery"},
        "ttp_brute": {"pos": (pad + 680, graph_top + 240), "color": (234, 179, 8), "r": 24, "label": "T1110.001", "sub": "Password Guess"},
        "ttp_sqli": {"pos": (pad + 660, graph_top + 390), "color": (234, 179, 8), "r": 26, "label": "T1190", "sub": "Exploit App"},
        "ttp_c2": {"pos": (pad + 620, graph_top + 530), "color": (234, 179, 8), "r": 24, "label": "T1059.004", "sub": "Unix Shell"},
        
        "gateway": {"pos": (pad + 860, graph_top + 340), "color": (245, 158, 11), "r": 36, "label": "soc-gateway", "sub": "10.77.10.1 / 20.1"},
        "sensor": {"pos": (pad + 860, graph_top + 160), "color": (14, 165, 233), "r": 30, "label": "soc-sensor", "sub": "AF_PACKET"},
        
        "victim": {"pos": (pad + 1120, graph_top + 340), "color": (16, 185, 129), "r": 38, "label": "soc-victim", "sub": "10.77.30.20 (Web)"},
        "hitl": {"pos": (pad + 1100, graph_top + 520), "color": (16, 185, 129), "r": 28, "label": "APR-87727348", "sub": "nftables Block"}
    }

    links = [
        ("attacker", "recon_rule", False),
        ("attacker", "brute_rule", False),
        ("attacker", "sqli_rule", True), # In Attack Path
        ("attacker", "c2_rule", False),
        ("recon_rule", "ttp_recon", False),
        ("brute_rule", "ttp_brute", False),
        ("sqli_rule", "ttp_sqli", True),  # In Attack Path
        ("c2_rule", "ttp_c2", False),
        ("sqli_rule", "gateway", True),   # In Attack Path
        ("gateway", "sensor", False),
        ("gateway", "victim", True),      # In Attack Path
        ("victim", "hitl", True),         # In Attack Path
        ("sensor", "victim", False),
    ]

    # Draw Links
    for u, v, is_active in links:
        p1 = nodes[u]["pos"]
        p2 = nodes[v]["pos"]
        if is_active:
            # Active attack pulse link (thick red glowing line)
            draw.line([p1, p2], fill=(239, 68, 68, 255), width=4)
            # Midpoint pulse dot
            mx = (p1[0] + p2[0]) // 2
            my = (p1[1] + p2[1]) // 2
            draw.ellipse([mx - 6, my - 6, mx + 6, my + 6], fill=(255, 255, 255, 255), outline=(239, 68, 68, 255), width=2)
        else:
            # Normal neural connection link
            draw.line([p1, p2], fill=(51, 65, 85, 200), width=2)

    # Draw Nodes with glowing rings
    for n_id, n in nodes.items():
        x, y = n["pos"]
        r = n["r"]
        col = n["color"]
        # Outer glow ring
        draw.ellipse([x - r - 8, y - r - 8, x + r + 8, y + r + 8], fill=None, outline=col + (90,), width=3)
        draw.ellipse([x - r - 4, y - r - 4, x + r + 4, y + r + 4], fill=None, outline=col + (160,), width=2)
        # Inner body
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(15, 23, 42, 255), outline=col + (255,), width=3)
        # Center core dot
        draw.ellipse([x - 7, y - 7, x + 7, y + 7], fill=col + (255,))

        # Text labels below node
        bbox1 = draw.textbbox((0, 0), n["label"], font=f_node)
        tw1 = bbox1[2] - bbox1[0]
        draw.text((x - tw1 // 2, y + r + 6), n["label"], font=f_node, fill=(255, 255, 255))
        bbox2 = draw.textbbox((0, 0), n["sub"], font=f_node_sub)
        tw2 = bbox2[2] - bbox2[0]
        draw.text((x - tw2 // 2, y + r + 24), n["sub"], font=f_node_sub, fill=(148, 163, 184))

    # Attack Path Floating Banner inside Canvas
    draw_rounded_rect(draw, (pad + 35, graph_bottom - 60, pad + 650, graph_bottom - 20), radius=8, fill=(15, 23, 42, 240), outline=(239, 68, 68, 200))
    draw.text((pad + 50, graph_bottom - 47), "⚡ 침투 경로 실시간 추적: Attacker ➔ SQLi (SID 9010001) ➔ Gateway ➔ Victim ➔ HITL 격리", font=f_mono_sm, fill=(252, 165, 165))

    # 5. Right: Deep Entity Inspector Panel
    insp_left = split_x
    insp_right = W - pad - 15
    draw_rounded_rect(draw, (insp_left, graph_top, insp_right, graph_bottom), radius=12, fill=(15, 23, 42, 255), outline=(30, 41, 59, 255))

    # Inspector Header
    iy = graph_top + 18
    draw.text((insp_left + 20, iy), "개체 심층 인스펙터 (Entity Inspector)", font=f_title, fill=(255, 255, 255))
    draw.text((insp_left + 20, iy + 30), "선택된 신경망 노드 분석 및 인과관계 매핑", font=f_sub, fill=(148, 163, 184))

    # Selected Node Card
    cy = iy + 65
    draw_rounded_rect(draw, (insp_left + 20, cy, insp_right - 20, cy + 90), radius=10, fill=(30, 41, 59, 200), outline=(239, 68, 68, 255), width=2)
    # Target icon & title
    draw.ellipse([insp_left + 35, cy + 20, insp_left + 85, cy + 70], fill=(69, 10, 10), outline=(239, 68, 68), width=2)
    draw.text((insp_left + 46, cy + 26), "🎯", font=f_korean_lg)
    draw.text((insp_left + 105, cy + 20), "soc-attacker (10.77.20.20)", font=f_korean_lg, fill=(255, 255, 255))
    draw.text((insp_left + 105, cy + 50), "역할: 외부 공격 발원지 (공격존 ZONE-ATTACK)", font=f_mono_sm, fill=(252, 165, 165))

    # Attributes Grid
    ay = cy + 110
    attrs = [
        ("위협 점수 (Threat Score)", "95 / 100 (CRITICAL - 긴급 대응)", (239, 68, 68)),
        ("킬체인 진행 단계 (Kill Chain)", "Recon ➔ Exploitation ➔ C2", (245, 158, 11)),
        ("탐지된 총 알람 수 (Alerts)", "37건 (Suricata 24, Snort 13)", (56, 189, 248)),
        ("주요 공격 기법 (MITRE TTP)", "T1046, T1190, T1110.001, T1059", (234, 179, 8)),
        ("인과관계 연결 노드 수 (Links)", "8개 노드 연결 (규칙, 게이트웨이, 자산)", (168, 85, 247)),
        ("PolicyValidator 검증 상태", "격리 대상 확인 (Inbound Drop 승인 대기)", (16, 185, 129))
    ]

    for label, val, col in attrs:
        draw_rounded_rect(draw, (insp_left + 20, ay, insp_right - 20, ay + 62), radius=8, fill=(11, 15, 25, 220), outline=(30, 41, 59, 255))
        draw.text((insp_left + 32, ay + 10), label, font=f_mono_sm, fill=(148, 163, 184))
        draw.text((insp_left + 32, ay + 32), val, font=f_korean_bold, fill=col)
        ay += 72

    # Action Recommendation Box
    ry = ay + 10
    draw_rounded_rect(draw, (insp_left + 20, ry, insp_right - 20, ry + 120), radius=10, fill=(6, 78, 59, 200), outline=(16, 185, 129, 255), width=2)
    draw.text((insp_left + 32, ry + 14), "🛡️ AI & PolicyValidator 권고 조치:", font=f_korean_bold, fill=(167, 243, 208))
    draw.text((insp_left + 32, ry + 42), "nft add element inet filter blocklist { 10.77.20.20 }", font=f_mono, fill=(255, 255, 255))
    draw.text((insp_left + 32, ry + 75), "✔ 보호 인프라 검증 통과 (게이트웨이/DNS 아님) ➔ HITL 승인 큐 대기 중", font=f_mono_sm, fill=(167, 243, 208))

    im.save(OUTPUT_PATH, quality=95)
    print(f"[+] Saved Cyber Neural Knowledge Graph image to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
