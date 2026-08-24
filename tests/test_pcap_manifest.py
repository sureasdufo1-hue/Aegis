import json
import hashlib
from pathlib import Path


def test_pcap_files_and_manifest_integrity():
    manifest_path = Path("pcaps/metadata/pcap_manifest.json")
    assert manifest_path.exists(), "pcap_manifest.json must exist"

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest_data) >= 6, "Expected at least 6 scenario PCAPs"

    for entry in manifest_data:
        pcap_file = Path("pcaps/samples") / entry["filename"]
        assert pcap_file.exists(), f"PCAP file {pcap_file} must exist"
        
        # Verify SHA-256 integrity
        content = pcap_file.read_bytes()
        calculated_sha = hashlib.sha256(content).hexdigest()
        assert calculated_sha == entry["sha256"], f"SHA-256 mismatch for {entry['filename']}"
        assert entry["src_ip"] == "10.77.20.20"
        assert entry["dest_ip"] == "10.77.30.20"
