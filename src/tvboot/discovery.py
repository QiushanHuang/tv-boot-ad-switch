"""Limited SSDP discovery; never scan or fetch non-local addresses."""

import http.client
import ipaddress
import socket
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import urlsplit


PRIVATE_NETWORKS = tuple(ipaddress.ip_network(n) for n in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
))
MAX_DESCRIPTION = 256 * 1024


@dataclass(frozen=True)
class Candidate:
    ip: str
    name: str


def default_candidate(candidates):
    return candidates[0] if len(candidates) == 1 else None


def valid_ipv4(value):
    try:
        addr = ipaddress.IPv4Address(value)
        return any(addr in network for network in PRIVATE_NETWORKS)
    except (ipaddress.AddressValueError, ValueError, TypeError):
        return False


def location_from_response(data, sender):
    if not valid_ipv4(sender) or len(data) > 16384:
        return None
    try:
        lines = data.decode("iso-8859-1").splitlines()
        if not lines or not lines[0].startswith("HTTP/1."):
            return None
        locations = [line.split(":", 1)[1].strip() for line in lines[1:] if line.lower().startswith("location:")]
        if len(locations) != 1 or len(locations[0]) > 2048:
            return None
        parts = urlsplit(locations[0])
        if (parts.scheme != "http" or parts.hostname != sender or parts.username is not None
                or parts.password is not None or parts.fragment or not parts.port):
            return None
        if any(ord(ch) < 32 for ch in parts.path + parts.query):
            return None
        return locations[0]
    except (ValueError, UnicodeError):
        return None


def parse_description(data, ip):
    if not valid_ipv4(ip) or len(data) > MAX_DESCRIPTION:
        return None
    try:
        text = data.decode("utf-8-sig")
        if "<!DOCTYPE" in text.upper():
            return None
        root = ET.fromstring(text)
        names, makers = [], []
        for element in root.iter():
            tag = element.tag.rsplit("}", 1)[-1].lower()
            if tag == "friendlyname" and element.text:
                names.append(element.text.strip())
            if tag == "manufacturer" and element.text:
                makers.append(element.text.strip())
        name = names[0] if names else ""
        marker = " ".join(names + makers).lower()
        if not name or not any(brand in marker for brand in ("xiaomi", "redmi", "小米", "红米")):
            return None
        name = "".join(c for c in name if c.isprintable())[:100]
        return Candidate(ip, name) if name else None
    except (ET.ParseError, ValueError, UnicodeError):
        return None


def _fetch_description(location, sender):
    parts = urlsplit(location)
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    conn = http.client.HTTPConnection(sender, parts.port, timeout=1.2)
    try:
        conn.request("GET", path, headers={"Accept": "text/xml, application/xml"})
        response = conn.getresponse()
        if response.status != 200:
            return None
        return parse_description(response.read(MAX_DESCRIPTION + 1), sender)
    finally:
        conn.close()


def discover(timeout=3.0):
    message = (b"M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n"
               b'MAN: "ssdp:discover"\r\nMX: 2\r\nST: upnp:rootdevice\r\n\r\n')
    locations = {}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.bind(("", 0))
        sock.sendto(message, ("239.255.255.250", 1900))
        deadline = time.monotonic() + max(0.2, min(timeout, 6.0))
        while time.monotonic() < deadline and len(locations) < 12:
            sock.settimeout(max(0.05, deadline - time.monotonic()))
            try:
                data, (sender, _) = sock.recvfrom(16385)
            except socket.timeout:
                break
            location = location_from_response(data, sender)
            if location:
                locations.setdefault(sender, location)
    found = []
    for ip, location in locations.items():
        try:
            candidate = _fetch_description(location, ip)
            if candidate:
                found.append(candidate)
        except (OSError, ValueError, http.client.HTTPException):
            continue
    return sorted(found, key=lambda item: (item.name.casefold(), item.ip))
