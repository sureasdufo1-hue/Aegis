from fastapi.testclient import TestClient

from dashboard.app import app

client = TestClient(app)


def test_pcap_list_scenarios():
    """Verify GET /api/pcap/list returns verified scenarios with SHA-256 integrity."""
    res = client.get("/api/pcap/list")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) >= 6

    # Verify key scenarios exist
    filenames = [s["filename"] for s in scenarios]
    assert "PCAP-20260824-ATK-001-ICMP.pcap" in filenames
    assert "PCAP-20260824-ATK-002-SQLI.pcap" in filenames
    assert "PCAP-20260824-ATK-005-BRUTEFORCE.pcap" in filenames

    # Verify SHA-256 presence and validity
    for s in scenarios:
        assert len(s["sha256"]) == 64
        assert s["integrity_verified"] is True
        assert s["download_url"].startswith("/api/pcap/download/")


def test_pcap_download_valid_file():
    """Verify GET /api/pcap/download/{filename} streams verified binary pcap with header."""
    filename = "PCAP-20260824-ATK-002-SQLI.pcap"
    res = client.get(f"/api/pcap/download/{filename}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/vnd.tcpdump.pcap"
    assert "X-PCAP-SHA256" in res.headers
    assert len(res.headers["X-PCAP-SHA256"]) == 64
    assert len(res.content) == 607


def test_pcap_download_path_traversal_guards():
    """Verify path traversal attacks and non-existent files are blocked."""
    # 1. Non-existent file
    res1 = client.get("/api/pcap/download/NON_EXISTENT.pcap")
    assert res1.status_code == 404

    # 2. Non-pcap extension
    res2 = client.get("/api/pcap/download/app.py")
    assert res2.status_code == 400

    # 3. Path traversal attack
    res3 = client.get("/api/pcap/download/..%2F..%2Fetc%2Fpasswd.pcap")
    assert res3.status_code in (400, 404)


def test_pcap_inspect_frames():
    """Verify GET /api/pcap/inspect/{filename} returns parsed Wireshark frames and hex dumps."""
    filename = "PCAP-20260824-ATK-002-SQLI.pcap"
    res = client.get(f"/api/pcap/inspect/{filename}?max_packets=10")
    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == filename
    assert data["packet_count"] >= 5
    assert len(data["frames"]) >= 5

    # Check frame structure and Wireshark hex dump
    first_frame = data["frames"][0]
    assert first_frame["frame_no"] == 1
    assert "src_ip" in first_frame
    assert "dst_ip" in first_frame
    assert first_frame["protocol"] == "TCP"
    assert "hex_dump" in first_frame
    assert "0000" in first_frame["hex_dump"]


def test_pcap_carve_session():
    """Verify POST /api/pcap/carve dynamically maps query/alert to packet capture."""
    # 1. Carve by SQLI keyword
    res_sqli = client.post("/api/pcap/carve", json={"scenario": "SQLI", "query": "union select"})
    assert res_sqli.status_code == 200
    d1 = res_sqli.json()
    assert d1["status"] == "success"
    assert "SQLI" in d1["carved_file"]
    assert d1["packet_count"] > 0
    assert d1["download_url"].startswith("/api/pcap/download/")

    # 2. Carve by SSH port 22
    res_ssh = client.post("/api/pcap/carve", json={"dest_port": 22})
    assert res_ssh.status_code == 200
    d2 = res_ssh.json()
    assert "BRUTEFORCE" in d2["carved_file"]


def test_pcap_modal_ui_in_index_html():
    """Verify PCAP Forensic Evidence Modal UI, buttons, and JS functions exist in index.html."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Modal container and header
    assert 'id="pcapForensicModal"' in html
    assert "PCAP 패킷 포렌식 증적 뷰어" in html
    assert "Wireshark-in-Browser & Session Carver" in html

    # Meta elements
    assert 'id="pcap-scenario-select"' in html
    assert 'id="pcap-meta-size"' in html
    assert 'id="pcap-meta-pkts"' in html
    assert 'id="pcap-meta-sha256"' in html

    # Wireshark-style table and hex dump
    assert 'id="pcap-packet-tbody"' in html
    assert 'id="pcap-hex-dump-view"' in html
    assert 'id="btn-pcap-download"' in html

    # Entity Inspector button
    assert 'id="insp-pcap-btn"' in html
    assert "세션 PCAP 증적 검사 & 다운로드" in html

    # JS functions
    assert "openPcapForensicModal" in html
    assert "loadPcapScenario" in html
    assert "selectPacketFrame" in html
    assert "downloadCurrentPcapFile" in html

