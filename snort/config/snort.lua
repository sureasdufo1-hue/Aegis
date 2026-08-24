-- Snort 3 Configuration for SOC Lab

HOME_NET = '192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,127.0.0.1/32'
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

-- Detection Engine
ips = {
    enable_builtin_rules = true,
    include = '/etc/snort/rules/local.rules',
    rules = [[
        include /etc/snort/rules/web_attacks.rules
        include /etc/snort/rules/c2_malware.rules
        include /etc/snort/rules/scan_recon.rules
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
