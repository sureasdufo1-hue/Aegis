from pathlib import Path

import yaml
from cryptography import x509
from cryptography.hazmat.primitives import serialization

from scripts.simulate_tls_decryption_pipeline import simulate_tls_pipeline

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_nginx_ssl_configuration_syntax():
    conf_path = REPO_ROOT / "infrastructure" / "docker" / "nginx" / "nginx.conf"
    assert conf_path.exists(), "nginx.conf must exist"

    content = conf_path.read_text(encoding="utf-8")
    assert "listen 443 ssl http2;" in content
    assert "ssl_protocols TLSv1.2 TLSv1.3;" in content
    assert "ssl_certificate /etc/nginx/ssl/server.crt;" in content
    assert "ssl_certificate_key /etc/nginx/ssl/server.key;" in content
    assert "proxy_pass http://victim_backend;" in content
    assert "upstream victim_backend" in content
    assert "victim-web:3000" in content
    assert "proxy_set_header X-SSL-Decrypted \"true\";" in content


def test_tls_certificates_validity():
    ssl_dir = REPO_ROOT / "infrastructure" / "docker" / "ssl"
    cert_path = ssl_dir / "server.crt"
    key_path = ssl_dir / "server.key"

    assert cert_path.exists(), "server.crt must exist"
    assert key_path.exists(), "server.key must exist"

    # Verify Certificate
    cert_data = cert_path.read_bytes()
    cert = x509.load_pem_x509_certificate(cert_data)
    assert "victim-app.soc-lab.local" in cert.subject.rfc4514_string()

    # Verify Private Key
    key_data = key_path.read_bytes()
    key = serialization.load_pem_private_key(key_data, password=None)
    assert key.key_size == 2048


def test_docker_compose_reverse_proxy_service():
    compose_path = REPO_ROOT / "docker-compose.yml"
    assert compose_path.exists()

    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get("services", {})
    assert "soc-reverse-proxy" in services, "soc-reverse-proxy must be defined in docker-compose.yml"

    proxy = services["soc-reverse-proxy"]
    assert "nginx" in proxy["image"]
    assert "443:443" in proxy["ports"]
    assert "80:80" in proxy["ports"]
    assert any("nginx.conf" in v for v in proxy["volumes"])
    assert any("ssl" in v for v in proxy["volumes"])


def test_tls_decryption_simulation_data_integrity():
    data = simulate_tls_pipeline(save_evidence=False)
    assert "case_a" in data
    assert "case_b" in data
    assert "case_c" in data

    # Case A: Encrypted (L7 Blind Spot)
    case_a = data["case_a"]
    assert case_a["tls"]["version"] == "TLSv1.3"
    assert case_a["dest_port"] == 443
    assert len(case_a["alerts_triggered"]) == 0

    # Case B: Plaintext HTTP Mirroring after SSL Termination
    case_b = data["case_b"]
    assert case_b["alert"]["signature_id"] == 9010001
    assert "UNION SELECT" in case_b["http"]["url"]
    assert case_b["dest_port"] == 3000
    assert case_b["proxy_metadata"]["ssl_terminated_by"] == "soc-reverse-proxy (Nginx 1.27)"

    # Case C: Passive TLS Handshake Inspection (SNI Domain)
    case_c = data["case_c"]
    assert case_c["alert"]["signature_id"] == 9030025
    assert "beacon.evil-c2.lab" in case_c["tls"]["sni"]
