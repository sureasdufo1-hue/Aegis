from analyzer.ai.schemas.actions import ActionType, Direction


class FirewallRuleAdapter:
    """Generates standardized, syntactically correct firewall rule previews for nftables and iptables."""

    @staticmethod
    def generate_nftables_preview(action_type: ActionType, target: str, direction: Direction = Direction.INBOUND) -> str:
        if action_type == ActionType.BLOCK_IP:
            if direction == Direction.INBOUND:
                return f"nft add rule inet filter input ip saddr {target} counter drop"
            elif direction == Direction.OUTBOUND:
                return f"nft add rule inet filter output ip daddr {target} counter drop"
            else:
                return f"nft add rule inet filter forward ip saddr {target} counter drop; nft add rule inet filter forward ip daddr {target} counter drop"
        elif action_type == ActionType.RATE_LIMIT:
            return f"nft add rule inet filter input ip saddr {target} limit rate 10/second burst 20 packets accept; nft add rule inet filter input ip saddr {target} drop"
        elif action_type == ActionType.ISOLATE_HOST:
            return f"nft insert rule inet filter forward ip saddr {target} ip daddr != 10.77.10.10 drop"
        return f"# Action type {action_type.value} does not require direct packet filter rules."

    @staticmethod
    def generate_iptables_preview(action_type: ActionType, target: str, direction: Direction = Direction.INBOUND) -> str:
        if action_type == ActionType.BLOCK_IP:
            if direction == Direction.INBOUND:
                return f"iptables -I INPUT -s {target} -j DROP"
            elif direction == Direction.OUTBOUND:
                return f"iptables -I OUTPUT -d {target} -j DROP"
            else:
                return f"iptables -I FORWARD -s {target} -j DROP; iptables -I FORWARD -d {target} -j DROP"
        elif action_type == ActionType.RATE_LIMIT:
            return f"iptables -I INPUT -s {target} -m limit --limit 10/s --limit-burst 20 -j ACCEPT; iptables -A INPUT -s {target} -j DROP"
        elif action_type == ActionType.ISOLATE_HOST:
            return f"iptables -I FORWARD -s {target} ! -d 10.77.10.10 -j DROP"
        return f"# Action type {action_type.value} does not require direct packet filter rules."
