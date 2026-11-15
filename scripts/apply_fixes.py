#!/usr/bin/env python3
"""
apply_fixes.py — Apply the production-hardening fixes to the Packet Tracer lab.

The lab file is decrypted to its plaintext XML, every defect listed in
``docs/AUDIT-FINDINGS.md`` is corrected in place, and the result is re-encrypted
into a valid ``.pkt`` container.

The original lab is never modified: read it, write a new file.

Usage
-----
    python scripts/apply_fixes.py lab/main_project-original.pkt --out lab/main_project.pkt
    python scripts/apply_fixes.py lab/main_project.pkt --out lab/main_project.pkt --dry-run
"""

from __future__ import annotations

import argparse
import copy
import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pkt_core import decode_bytes, encode_bytes  # noqa: E402

# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #

#: Packet Tracer display name -> professional device name
RENAME = {
    "Multilayer Switch0": "access-sales-01",
    "Multilayer Switch1": "access-hr-01",
    "Multilayer Switch2": "access-accounts-01",
    "1.1.1.1": "BR1-WAN-RTR",
    "1.1.1.2": "BR1-ACCESS",
    "2.1.1.1": "BR2-WAN-RTR",
    "2.1.1.2": "BR2-ACCESS",
    "3.1.1.1": "BR3-WAN-RTR",
    "3.1.1.2": "BR3-ACCESS",
    "4.1.1.1": "BR4-WAN-RTR",
    "4.1.1.2": "BR4-ACCESS",
    "central router": "HQ-WAN-RTR",
    "192.168.10.1": "SALES-PC1",
    "192.168.10.2": "SALES-PC2",
    "192.168.10.3": "SALES-PC3",
    "192.168.11.1": "HR-PC1",
    "192.168.11.2": "HR-PC2",
    "192.168.11.3": "HR-PC3",
    "192.168.12.1": "ACCOUNTS-PC1",
    "192.168.12.2": "ACCOUNTS-PC2",
    "192.168.12.3": "ACCOUNTS-PC3",
    "192.186.13.1": "BR1-PC1",
    "192.186.13.2": "BR1-PC2",
    "192.186.14.1": "BR2-PC1",
    "192.186.14.2": "BR2-PC2",
    "192.186.15.1": "BR3-PC1",
    "192.186.15.2": "BR3-PC2",
    "192.186.16.1": "BR4-PC1",
    "192.186.16.2": "BR4-PC2",
}

#: New device name -> IOS hostname
HOSTNAME = {
    "access-sales-01": "access-sales-01",
    "access-hr-01": "access-hr-01",
    "access-accounts-01": "access-accounts-01",
    "core-01": "core-01",
    "core-02": "core-02",
    "leaf-01": "leaf-01",
    "leaf-02": "leaf-02",
    "HQ-WAN-RTR": "HQ-WAN-RTR",
    "BR1-WAN-RTR": "BR1-WAN-RTR",
    "BR2-WAN-RTR": "BR2-WAN-RTR",
    "BR3-WAN-RTR": "BR3-WAN-RTR",
    "BR4-WAN-RTR": "BR4-WAN-RTR",
    "BR1-ACCESS": "BR1-ACCESS",
    "BR2-ACCESS": "BR2-ACCESS",
    "BR3-ACCESS": "BR3-ACCESS",
    "BR4-ACCESS": "BR4-ACCESS",
    "EDGE-RTR": "EDGE-RTR",
    "ISP": "ISP",
}

#: Device name -> purpose, used in the login banner
ROLE = {
    "access-sales-01": "HQ access switch - Sales VLAN 10",
    "access-hr-01": "HQ access switch - HR VLAN 11",
    "access-accounts-01": "HQ access switch - Accounts VLAN 12",
    "core-01": "HQ core layer 1 - HSRP active, DHCP server, OSPF",
    "core-02": "HQ core layer 2 - HSRP standby, OSPF",
    "leaf-01": "HQ leaf layer 1 - dual-homed uplink",
    "leaf-02": "HQ leaf layer 2 - dual-homed uplink",
    "HQ-WAN-RTR": "HQ WAN edge - OSPF area 0 and IPsec hub",
    "BR1-WAN-RTR": "Branch 1 WAN router - IPsec peer",
    "BR2-WAN-RTR": "Branch 2 WAN router - IPsec peer",
    "BR3-WAN-RTR": "Branch 3 WAN router - IPsec peer",
    "BR4-WAN-RTR": "Branch 4 WAN router - IPsec peer",
    "BR1-ACCESS": "Branch 1 access switch - VLAN 13, DHCP relay",
    "BR2-ACCESS": "Branch 2 access switch - VLAN 14, DHCP relay",
    "BR3-ACCESS": "Branch 3 access switch - VLAN 15, DHCP relay",
    "BR4-ACCESS": "Branch 4 access switch - VLAN 16, DHCP relay",
    "EDGE-RTR": "Internet edge router - NAT/PAT to ISP",
    "ISP": "Upstream ISP router (simulated)",
}

#: Interface descriptions for the routed / uplinked ports
DESCRIPTIONS = {
    ("core-01", "GigabitEthernet0/1"): "uplink to HQ-WAN-RTR (10.1.1.0/24)",
    ("core-01", "GigabitEthernet0/2"): "trunk to LEAF-02",
    ("core-01", "FastEthernet0/3"): "uplink to EDGE-RTR (10.3.3.0/24)",
    ("core-01", "FastEthernet0/4"): "Server1 - DNS 172.10.10.2",
    ("core-01", "FastEthernet0/5"): "Server0 - WEB 172.10.10.1",
    ("core-01", "FastEthernet0/6"): "Server2 - MAIL 172.10.10.3",
    ("core-02", "GigabitEthernet0/1"): "uplink to HQ-WAN-RTR (10.2.2.0/24)",
    ("core-02", "FastEthernet0/1"): "trunk to LEAF-01",
    ("core-02", "FastEthernet0/2"): "trunk to LEAF-02",
    ("leaf-01", "FastEthernet0/1"): "trunk to ACCESS-SALES-01",
    ("leaf-01", "FastEthernet0/2"): "trunk to ACCESS-HR-01",
    ("leaf-01", "FastEthernet0/3"): "trunk to ACCESS-ACCOUNTS-01",
    ("leaf-01", "FastEthernet0/7"): "trunk to CORE-01",
    ("leaf-01", "FastEthernet0/8"): "trunk to CORE-02",
    ("leaf-02", "FastEthernet0/1"): "trunk to ACCESS-SALES-01",
    ("leaf-02", "FastEthernet0/2"): "trunk to ACCESS-HR-01",
    ("leaf-02", "FastEthernet0/3"): "trunk to ACCESS-ACCOUNTS-01",
    ("leaf-02", "FastEthernet0/7"): "trunk to CORE-01",
    ("leaf-02", "FastEthernet0/8"): "trunk to CORE-02",
    ("access-sales-01", "GigabitEthernet0/1"): "trunk to LEAF-01",
    ("access-sales-01", "GigabitEthernet0/2"): "trunk to LEAF-02",
    ("access-hr-01", "GigabitEthernet0/1"): "trunk to LEAF-01",
    ("access-hr-01", "GigabitEthernet0/2"): "trunk to LEAF-02",
    ("access-accounts-01", "GigabitEthernet0/1"): "trunk to LEAF-01",
    ("access-accounts-01", "GigabitEthernet0/2"): "trunk to LEAF-02",
    ("HQ-WAN-RTR", "FastEthernet0/0"): "uplink to CORE-01 (10.1.1.0/24)",
    ("HQ-WAN-RTR", "FastEthernet0/1"): "uplink to CORE-02 (10.2.2.0/24)",
    ("HQ-WAN-RTR", "Serial1/0"): "IPsec tunnel to BR1-WAN-RTR (5.1.1.0/24)",
    ("HQ-WAN-RTR", "Serial1/1"): "IPsec tunnel to BR2-WAN-RTR (6.1.1.0/24)",
    ("HQ-WAN-RTR", "Serial1/2"): "IPsec tunnel to BR3-WAN-RTR (7.1.1.0/24)",
    ("HQ-WAN-RTR", "Serial1/3"): "IPsec tunnel to BR4-WAN-RTR (8.1.1.0/24)",
    ("EDGE-RTR", "GigabitEthernet0/0"): "inside interface - enterprise side",
    ("EDGE-RTR", "GigabitEthernet0/1"): "outside interface - ISP facing (PAT)",
    ("ISP", "GigabitEthernet0/0"): "uplink to EDGE-RTR (200.1.1.0/30)",
    ("ISP", "GigabitEthernet0/1"): "simulated Internet (203.0.113.0/24)",
    ("BR1-WAN-RTR", "FastEthernet0/0"): "uplink to BR1-ACCESS (1.1.1.0/24)",
    ("BR1-WAN-RTR", "Serial1/0"): "IPsec tunnel to HQ-WAN-RTR (5.1.1.0/24)",
    ("BR2-WAN-RTR", "FastEthernet0/0"): "uplink to BR2-ACCESS (2.1.1.0/24)",
    ("BR2-WAN-RTR", "Serial1/0"): "IPsec tunnel to HQ-WAN-RTR (6.1.1.0/24)",
    ("BR3-WAN-RTR", "FastEthernet0/0"): "uplink to BR3-ACCESS (3.1.1.0/24)",
    ("BR3-WAN-RTR", "Serial1/0"): "IPsec tunnel to HQ-WAN-RTR (7.1.1.0/24)",
    "BR4-WAN-RTR": None,
    "BR4-WAN-RTR": "BR4-WAN-RTR",
}
DESCRIPTIONS.update(
    {
        ("BR4-WAN-RTR", "FastEthernet0/0"): "uplink to BR4-ACCESS (4.1.1.0/24)",
        ("BR4-WAN-RTR", "Serial1/0"): "IPsec tunnel to HQ-WAN-RTR (8.1.1.0/24)",
        ("BR1-ACCESS", "GigabitEthernet0/1"): "uplink to BR1-WAN-RTR (1.1.1.0/24)",
        ("BR2-ACCESS", "GigabitEthernet0/1"): "uplink to BR2-WAN-RTR (2.1.1.0/24)",
        ("BR3-ACCESS", "GigabitEthernet0/1"): "uplink to BR3-WAN-RTR (3.1.1.0/24)",
        ("BR4-ACCESS", "GigabitEthernet0/1"): "uplink to BR4-WAN-RTR (4.1.1.0/24)",
    }
)

#: Host -> logical description of the site it belongs to
BANNER_TEMPLATE = (
    "AUTHORIZED ACCESS ONLY - Centralized Enterprise Server Services | "
    "{device} | {role}"
)

#: The corporate intranet page served by Server0.  It is read from
#: ``assets/web/index.html`` so that the page in the repository and the page
#: inside the lab can never drift apart.
INTRANET_HTML_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "web",
    "index.html",
)


def intranet_html() -> str:
    """Return the corporate intranet page, with the XML markup escaped."""
    with open(INTRANET_HTML_FILE, encoding="utf-8") as handle:
        page = handle.read()
    # Packet Tracer stores the page body as XML text, so the markup has to be
    # escaped.  The resulting text is what the web browser renders.
    return (
        page.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# --------------------------------------------------------------------------- #
# Low level helpers
# --------------------------------------------------------------------------- #

def text_of(node: ET.Element | None, default: str = "") -> str:
    if node is None or node.text is None:
        return default
    return node.text.strip()


def config_lines(engine: ET.Element) -> list[str]:
    """Return the running-config of a device as a list of lines."""
    for node in engine.iter("RUNNINGCONFIG"):
        return [(line.text or "").rstrip() for line in node.findall("LINE")]
    return []


def set_config(engine: ET.Element, lines: list[str]) -> None:
    """Replace the running-config of a device with *lines*."""
    for node in list(engine.iter("RUNNINGCONFIG")):
        for line in list(node.findall("LINE")):
            node.remove(line)
        for line in lines:
            element = ET.SubElement(node, "LINE")
            element.text = line
        break


def insert_after(lines: list[str], pattern: str, new_lines: list[str], once: bool = True) -> None:
    """Insert *new_lines* right after the first line matching *pattern*."""
    regex = re.compile(pattern)
    for index, line in enumerate(lines):
        if regex.search(line):
            lines[index + 1 : index + 1] = new_lines
            if once:
                return


def insert_before(lines: list[str], pattern: str, new_lines: list[str]) -> None:
    """Insert *new_lines* right before the first line matching *pattern*."""
    regex = re.compile(pattern)
    for index, line in enumerate(lines):
        if regex.search(line):
            lines[index:index] = new_lines
            return


def map_interface_blocks(
    lines: list[str], transform: Callable[[list[str], str], list[str]]
) -> list[str]:
    """Apply *transform* to every ``interface <name>`` block of a config.

    A Packet Tracer configuration is a flat list of lines.  An interface block
    starts at the ``interface`` line and ends at the terminating ``!``.  The
    transform receives the block (including the ``interface`` line) and the
    interface name, and returns the replacement block.
    """
    output: list[str] = []
    index = 0
    total = len(lines)
    while index < total:
        line = lines[index]
        if line.startswith("interface "):
            name = line.split(None, 1)[1].strip()
            end = index + 1
            while end < total and lines[end] != "!":
                end += 1
            block = lines[index:end]
            output.extend(transform(block, name))
            index = end
        else:
            output.append(line)
            index += 1
    return output


def block_contains(block: list[str], needle: str) -> bool:
    """Return True when *needle* appears in *block*."""
    return any(needle in line for line in block)


# --------------------------------------------------------------------------- #
# Per-device configuration fixes
# --------------------------------------------------------------------------- #

def harden_device(device: str, lines: list[str]) -> list[str]:
    """Apply the generic and device specific configuration fixes."""
    lines = list(lines)

    # -- service password-encryption ------------------------------------- #
    for index, line in enumerate(lines):
        if line.strip() == "no service password-encryption":
            lines[index] = "service password-encryption"
            break

    # -- hostname + banner + enable secret -------------------------------- #
    for index, line in enumerate(lines):
        if line.startswith("hostname "):
            lines[index] = f"hostname {HOSTNAME.get(device, device)}"
            break
    if device in ROLE and not any(l.startswith("banner motd") for l in lines):
        insert_after(
            lines,
            r"^hostname ",
            [
                f"banner motd ^{BANNER_TEMPLATE.format(device=device, role=ROLE[device])}^",
                "enable secret 5 $1$Centr4l1z3d$Lab0nly$ChangeMe2026",
            ],
        )

    # -- interface level fixes --------------------------------------------- #
    def transform(block: list[str], interface: str) -> list[str]:
        # shut the unused management SVI
        if interface == "Vlan1" and device in (
            "access-hr-01",
            "access-accounts-01",
            "BR1-ACCESS",
            "BR2-ACCESS",
            "BR3-ACCESS",
            "BR4-ACCESS",
            "BR1-WAN-RTR",
            "BR2-WAN-RTR",
            "BR3-WAN-RTR",
            "BR4-WAN-RTR",
        ):
            if not block_contains(block, " shutdown"):
                block = block + [" shutdown"]

        # description
        description = DESCRIPTIONS.get((device, interface))
        if description and not block_contains(block, "description"):
            block = block[:1] + [f" description {description}"] + block[1:]

        # access port hardening
        if block_contains(block, "switchport access vlan"):
            additions: list[str] = []
            if not block_contains(block, "spanning-tree portfast"):
                additions.append(" spanning-tree portfast")
            if not block_contains(block, "spanning-tree bpduguard enable"):
                additions.append(" spanning-tree bpduguard enable")
            if not block_contains(block, "switchport port-security"):
                additions.append(" switchport port-security")
            if not block_contains(block, "port-security maximum"):
                additions.append(" switchport port-security maximum 1")
            if not block_contains(block, "port-security violation"):
                additions.append(" switchport port-security violation shutdown")
            if additions:
                block = block[:1] + additions + block[1:]

        # trunk VLAN scope
        if block_contains(block, "switchport mode trunk") and not block_contains(
            block, "trunk allowed vlan"
        ):
            block = block[:1] + [" switchport trunk allowed vlan 10-12,20"] + block[1:]

        # unused serial interfaces on the branch routers
        if (
            device.startswith("BR")
            and device.endswith("-WAN-RTR")
            and interface.startswith("Serial")
            and not block_contains(block, "crypto map")
            and block_contains(block, "no ip address")
            and not block_contains(block, " shutdown")
        ):
            block = block + [" shutdown"]

        return block

    return map_interface_blocks(lines, transform)


def fix_core_dhcp(lines: list[str]) -> list[str]:
    """Extend the DHCP exclusions and give every pool an explicit range."""
    lines = list(lines)

    # replace the single .254 exclusion with a .252-.254 exclusion
    for third in range(10, 17):
        old = f"ip dhcp excluded-address 192.168.{third}.254"
        if old in lines:
            lines[lines.index(old)] = (
                f"ip dhcp excluded-address 192.168.{third}.252 192.168.{third}.254"
            )

    # split the configuration into the pool blocks and the surrounding text
    head: list[str] = []
    pools: list[tuple[str, list[str]]] = []
    tail: list[str] = []
    index = 0
    total = len(lines)
    while index < total:
        line = lines[index]
        if line.startswith("ip dhcp pool "):
            name = line.split()[3]
            end = index + 1
            # a pool ends at the next pool definition or at a '!' separator
            while end < total and lines[end] != "!" and not lines[end].startswith("ip dhcp pool "):
                end += 1
            pools.append((name, lines[index:end]))
            index = end
        elif pools:
            tail.append(line)
            index += 1
        else:
            head.append(line)
            index += 1

    rebuilt: list[str] = []
    order = ["SALES", "HR", "ACCOUNTS", "BRANCH1", "BRANCH2", "BRANCH3", "BRANCH4"]
    ordered = [p for name in order for p in pools if p[0] == name]
    ordered += [p for p in pools if p[0] not in order]

    for name, block in ordered:
        rebuilt.append(block[0])
        if not any(re.match(r"^[ \t]+range ", l) for l in block):
            network_line = next(
                (l for l in block if re.match(r"^[ \t]+network ", l)), None
            )
            if network_line:
                subnet = network_line.split()[1]
                third = subnet.split(".")[2]
                rebuilt.append(f" range 192.168.{third}.21 192.168.{third}.251")
        rebuilt.extend(block[1:])
        rebuilt.append("!")

    return head + rebuilt + tail

def fix_core_02_relay(lines: list[str]) -> list[str]:
    """Give core-02 a DHCP relay path so it can serve clients when active."""

    def transform(block: list[str], interface: str) -> list[str]:
        if interface in ("Vlan10", "Vlan11", "Vlan12") and not block_contains(
            block, "ip helper-address"
        ):
            block = block[:1] + [" ip helper-address 10.1.1.1"] + block[1:]
        return block

    return map_interface_blocks(lines, transform)


# --------------------------------------------------------------------------- #
# Server side fixes
# --------------------------------------------------------------------------- #

def fix_servers(root: ET.Element) -> list[str]:
    """Apply the server service fixes and return a log of what changed."""
    changes: list[str] = []
    network = root.find("NETWORK")
    for device in network.find("DEVICES").findall("DEVICE"):
        engine = device.find("ENGINE")
        type_node = engine.find("TYPE")
        if type_node is None or text_of(type_node) != "Server":
            continue
        display_name = text_of(engine.find("NAME"))
        name = RENAME.get(display_name, display_name)

        # -- single authoritative DNS ------------------------------------- #
        dns_server = engine.find("DNS_SERVER")
        if dns_server is not None:
            enabled = dns_server.find("ENABLED")
            if enabled is not None and enabled.text == "1" and name != "Server1":
                enabled.text = "0"
                database = dns_server.find("NAMESERVER-DATABASE")
                if database is not None:
                    for record in list(database.findall("RESOURCE-RECORD")):
                        database.remove(record)
                changes.append(f"{name}: DNS service disabled (single authoritative DNS)")

        # -- FTP / TFTP off ----------------------------------------------- #
        for tag, label in (("FTP_SERVER", "FTP"), ("TFTP_SERVER", "TFTP")):
            node = engine.find(tag)
            if node is not None:
                enabled = node.find("ENABLED")
                if enabled is not None and enabled.text == "1":
                    enabled.text = "0"
                    changes.append(f"{name}: {label} service disabled")

        # -- the corporate intranet page ---------------------------------- #
        if name == "Server0":
            changes.extend(replace_index_page(engine))

    return changes


def replace_index_page(engine: ET.Element) -> list[str]:
    """Replace the default Packet Tracer ``index.html`` with the portal page."""
    changes: list[str] = []
    for filesystem in engine.iter("FILE"):
        if text_of(filesystem.find("NAME")) != "http:":
            continue
        files = filesystem.find("FILES")
        if files is None:
            continue
        for entry in files.findall("FILE"):
            if text_of(entry.find("NAME")) != "index.html":
                continue
            content = entry.find("FILE_CONTENT")
            if content is None:
                continue
            page = content.find("TEXT")
            if page is None:
                page = ET.SubElement(content, "TEXT")
            page.text = intranet_html()
            changes.append("Server0: index.html replaced with the corporate portal")
    return changes


def fix_clients(root: ET.Element) -> list[str]:
    """Fix the mail client identities and the stored test message."""
    changes: list[str] = []
    network = root.find("NETWORK")
    for device in network.find("DEVICES").findall("DEVICE"):
        engine = device.find("ENGINE")
        type_node = engine.find("TYPE")
        if type_node is None or text_of(type_node) != "Pc":
            continue
        display_name = text_of(engine.find("NAME"))
        name = RENAME.get(display_name, display_name)

        for client in engine.iter("EMAIL_CLIENT"):
            mail_id = client.find("MAIL_ID")
            if mail_id is not None and mail_id.text == "sales@gmail.com":
                mail_id.text = "sales@company.com"
                changes.append(f"{name}: mail identity corrected to sales@company.com")
            display = client.find("NAME")
            if display is not None:
                if display.text == "sales user":
                    display.text = "Sales User"
                elif display.text == "hr":
                    display.text = "HR User"
            sender = client.find("MAIL_FROM0")
            if sender is not None and sender.text == "sales@gmail.com":
                sender.text = "sales@company.com"
            subject = client.find("MAIL_SUBJECT0")
            if subject is not None and subject.text == "jii":
                subject.text = "Centralized Email Service Test"
            body = client.find("MAIL_CONTENT0")
            if body is not None and body.text == "zdfnhzxfgbzxfgb":
                body.text = (
                    "Hello HR, this is a test message from the Sales department, "
                    "delivered by the centralised company mail server "
                    "(SMTP for sending, POP3 for retrieval)."
                )
    return changes


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #

def apply_fixes(root: ET.Element, verbose: bool = True) -> list[str]:
    """Apply every fix to the decrypted lab and return a change log."""
    log: list[str] = []
    network = root.find("NETWORK")
    for device in network.find("DEVICES").findall("DEVICE"):
        engine = device.find("ENGINE")
        type_node = engine.find("TYPE")
        if type_node is None:
            continue
        dev_type = text_of(type_node)
        display_name = text_of(engine.find("NAME"))
        name = RENAME.get(display_name, display_name)

        # -- rename the device -------------------------------------------- #
        if display_name in RENAME:
            engine.find("NAME").text = RENAME[display_name]
            log.append(f"{display_name} -> {RENAME[display_name]}")

        if dev_type not in ("Router", "MultiLayerSwitch", "Switch"):
            continue

        lines = config_lines(engine)
        if not lines:
            continue
        lines = harden_device(name, lines)
        if name == "core-01":
            lines = fix_core_dhcp(lines)
        if name == "core-02":
            lines = fix_core_02_relay(lines)
        set_config(engine, lines)
        log.append(f"{name}: configuration hardened")

    log.extend(fix_servers(root))
    log.extend(fix_clients(root))
    return log


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pkt", help="source .pkt file")
    parser.add_argument("--out", help="destination .pkt file")
    parser.add_argument("--dry-run", action="store_true", help="report the changes without writing")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.pkt):
        sys.stderr.write(f"error: no such file: {args.pkt}\n")
        return 2

    with open(args.pkt, "rb") as handle:
        raw = handle.read()
    container = decode_bytes(raw)
    root = ET.fromstring(container.xml)

    changes = apply_fixes(root)

    for change in changes:
        print(f"  * {change}")
    print(f"\n{len(changes)} change(s) applied")

    if args.dry_run:
        return 0

    if not args.out:
        parser.error("--out is required unless --dry-run is given")

    # ET.tostring keeps the document structurally identical to the original.
    patched = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    if not patched.startswith(b"<PACKETTRACER5>"):
        patched = b"<PACKETTRACER5>" + patched.split(b">", 1)[1]
    rebuilt = encode_bytes(patched, container.format_name)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "wb") as handle:
        handle.write(rebuilt)
    print(f"wrote {args.out} ({len(rebuilt):,} bytes)")

    # self check: the result must decode again to the patched XML
    with open(args.out, "rb") as handle:
        verify = decode_bytes(handle.read())
    if verify.xml != patched:
        sys.stderr.write("error: the rebuilt file does not round-trip\n")
        return 1
    print("self check OK: the rebuilt file decodes back to the patched XML")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
