import ipaddress


# Critical Infrastructure Whitelist - NEVER ALLOW BLOCKING
PROTECTED_IPS = {
    # Gateways
    "10.77.10.1": "SOC Gateway (MGMT Interface)",
    "10.77.20.1": "SOC Gateway (Attack Interface)",
    "10.77.30.1": "SOC Gateway (Victim Interface)",
    "192.168.111.1": "VMware Host NAT Gateway",
    "192.168.111.140": "SOC Gateway Host Address",
    
    # Management & SIEM
    "10.77.10.10": "Windows Host MGMT Interface & Wazuh SIEM Docker Host",
    "10.77.10.20": "SOC Sensor Management Interface",
    "127.0.0.1": "Localhost Loopback",
    "::1": "IPv6 Localhost Loopback",
    
    # Common DNS
    "8.8.8.8": "Google Public DNS",
    "1.1.1.1": "Cloudflare DNS",
    "127.0.0.53": "Systemd Resolved DNS Stub",
}

PROTECTED_NETWORKS = [
    ipaddress.ip_network("10.77.10.0/24"),    # ZONE-MGMT
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("172.24.0.0/16"),     # Docker SIEM Network
]


def is_protected_asset(target_ip_or_cidr: str) -> tuple[bool, str | None]:
    """
    Evaluates whether an IP or subnet falls into the protected critical infrastructure assets.
    Returns (is_protected, description_if_protected).
    """
    clean_target = target_ip_or_cidr.strip()

    # Exact IP check
    if clean_target in PROTECTED_IPS:
        return True, f"Explicitly protected host: {PROTECTED_IPS[clean_target]}"

    # Subnet membership check
    try:
        if "/" in clean_target:
            target_net = ipaddress.ip_network(clean_target, strict=False)
            for p_net in PROTECTED_NETWORKS:
                if target_net.overlaps(p_net):
                    return True, f"Target CIDR {clean_target} overlaps with protected network {p_net}"
        else:
            ip_obj = ipaddress.ip_address(clean_target)
            for p_net in PROTECTED_NETWORKS:
                if ip_obj in p_net:
                    return True, f"Target IP {clean_target} resides inside protected management network {p_net}"
    except ValueError:
        # Invalid IP format
        return False, None

    return False, None
