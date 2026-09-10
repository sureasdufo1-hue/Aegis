#!/usr/bin/env python3
"""
scripts/generate_tls_certs.py
Generates a self-signed X.509 certificate and private key for the Nginx SSL Termination Proxy.
Subject: CN=victim-app.soc-lab.local, O=Aegis SOC Lab, C=KR
"""

from __future__ import annotations

import datetime
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

REPO_ROOT = Path(__file__).resolve().parent.parent
SSL_DIR = REPO_ROOT / "infrastructure" / "docker" / "ssl"


def generate_certificates(output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cert_path = output_dir / "server.crt"
    key_path = output_dir / "server.key"

    # 1. Generate RSA Private Key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 2. Build X.509 Certificate Subject & Issuer
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "KR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Seoul"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Aegis SOC Lab"),
        x509.NameAttribute(NameOID.COMMON_NAME, "victim-app.soc-lab.local"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("victim-app.soc-lab.local"),
                x509.DNSName("localhost"),
                x509.IPAddress(datetime.ip_address("10.77.30.20") if hasattr(datetime, "ip_address") else __import__("ipaddress").ip_address("10.77.30.20")),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    # Write Private Key
    with open(key_path, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Write Certificate
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return cert_path, key_path


def main() -> None:
    cert_path, key_path = generate_certificates(SSL_DIR)
    print(f"✓ SSL Certificate generated: {cert_path}")
    print(f"✓ Private Key generated:     {key_path}")


if __name__ == "__main__":
    main()
