-- ==============================================================================
-- Snort 3.12.2.0 Baseline Configuration for SOC Detection & Monitoring Lab
-- Reference: SOC Architecture HLD v1.0 / LLD v1.0 / Implementation Plan Phase 14
-- Completion Gate: GATE-SNORT-01
-- ==============================================================================

HOME_NET = '10.77.30.0/24'
EXTERNAL_NET = '!$HOME_NET'

HTTP_PORTS = '80,8080,8000,3000,8501,8443,443'
SSH_PORTS = '22'

-- Network inspectors
stream = { }
stream_ip = { }
stream_tcp = { }
stream_udp = { }
stream_icmp = { }

-- Application Inspectors
http_inspect = { }
http2_inspect = { }
dns = { }
ssl = { }
ssh = { }
ftp_server = { }
ftp_client = { }

-- Detection Engine & Rules
ips = {
    enable_builtin_rules = true,
    include = '/usr/local/etc/snort/rules/9100-local.rules',
    rules = [[
        include /usr/local/etc/snort/rules/9100-local.rules
    ]]
}

-- Alerts & Telemetry Outputs
alert_fast = {
    file = true,
    packet = false,
    limit = 0
}

alert_json = {
    file = true,
    limit = 0,
    fields = 'timestamp action class dir dst_addr dst_ap dst_port eth_dst eth_len eth_src eth_type gid sid rev msg b64_data pkt_gen pkt_len pkt_num proto rule service src_addr src_ap src_port target tcp_ack tcp_flags tcp_len tcp_seq tcp_win tos ttl type udp_len'
}

-- Logging stats
perf_monitor = {
    modules = { }
}
