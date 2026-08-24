#!/usr/bin/env bash
# ==============================================================================
# Network Setup for soc-attacker (Kali Linux)
# Reference: SOC Lab LLD v1.0 & Implementation Plan Phase 4.5
# ==============================================================================
set -euo pipefail

ATTACK_IF="${1:-eth0}"

echo "[*] Configuring static IP 10.77.20.20/24 on interface: ${ATTACK_IF}"

sudo nmcli con delete soc-attack 2>/dev/null || true
sudo nmcli con add \
    type ethernet \
    ifname "${ATTACK_IF}" \
    con-name soc-attack \
    ipv4.method manual \
    ipv4.addresses 10.77.20.20/24 \
    ipv4.gateway 10.77.20.1 \
    ipv6.method disabled

sudo nmcli con up soc-attack
ip -br addr show dev "${ATTACK_IF}"
echo "[+] soc-attacker network configured successfully."
