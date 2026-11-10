"""Executable *policy specification*, not a WebView interceptor or DNS resolver.

The caller supplies fixture DNS results. A real adapter must pin/revalidate the
actual connected peer and cover every frame/redirect/worker/request mechanism.
Merely calling this function before Navigate does NOT implement containment.
"""
import ipaddress
from urllib.parse import urlsplit


def decision(address, resolved_ips):
    """Deny by default; return stable copy suitable for trusted chrome."""
    try:
        u = urlsplit(address)
        if (u.scheme not in ("http", "https") or not u.hostname or
                u.username is not None or u.password is not None or
                any(ord(c) <= 32 or ord(c) == 127 or c == "\\" for c in address)):
            return "deny: unsupported address"
        host = u.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
            return "deny: local network"
        if "%" in host:
            return "deny: invalid host"
        # Validate literal addresses as well as every resolved address. Requiring
        # an answer also for literals models the connected-peer check.
        try:
            literal = ipaddress.ip_address(host)
        except ValueError:
            literal = None
        ips = [ipaddress.ip_address(ip) for ip in resolved_ips]
        if not ips:
            return "deny: peer unknown"
        if literal is not None:
            ips.append(literal)
        for ip in ips:
            mapped = getattr(ip, "ipv4_mapped", None)
            if not ip.is_global or (mapped is not None and not mapped.is_global):
                return "deny: local network"
        if u.port is not None and u.port not in (80, 443):
            return "deny: port not reviewed"
        return "allow: public web fixture"
    except (ValueError, TypeError, AttributeError):
        return "deny: invalid address"
