#!/usr/bin/env python3
"""
pkt_export.py — Extract readable content from a Cisco Packet Tracer ``.pkt`` file.

Packet Tracer saves labs in an encrypted container.  This tool decrypts the
container to its inner XML representation and exports the parts a reviewer
actually cares about:

* the plaintext XML of the lab
* the running-config of every infrastructure device
* a device inventory (model, hostname, IP, role)
* the cabling table
* the IP addressing plan

Usage
-----
    python pkt_export.py lab/main_project.pkt --list
    python pkt_export.py lab/main_project.pkt --xml-only --xml-out lab.xml
    python pkt_export.py lab/main_project.pkt --out configs/
    python pkt_export.py lab/main_project.pkt --links --ipam
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import Any

try:
    from pkt_core import decode_bytes
except ImportError:  # pragma: no cover - guidance for a missing dependency
    sys.stderr.write(
        "error: the 'pkt-core' package is required to read .pkt files.\n"
        "       install it with:  pip install -r scripts/requirements.txt\n"
    )
    raise SystemExit(2)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

INFRA_TYPES = {"Router", "MultiLayerSwitch", "Switch", "Hub", "WirelessRouter"}
ENDPOINT_TYPES = {"Pc", "Server"}

#: Packet Tracer display name  ->  human readable device name
DEVICE_NAME_MAP = {
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

#: Packet Tracer display name  ->  exported config file name
#: Both the original display names and the renamed production names are listed
#: so the exporter produces identical file names before and after the fix pass.
CONFIG_FILE_MAP = {
    "Multilayer Switch0": "access-sales.cfg",
    "Multilayer Switch1": "access-hr.cfg",
    "Multilayer Switch2": "access-accounts.cfg",
    "access-sales-01": "access-sales.cfg",
    "access-hr-01": "access-hr.cfg",
    "access-accounts-01": "access-accounts.cfg",
    "core-01": "core-01.cfg",
    "core-02": "core-02.cfg",
    "leaf-01": "leaf-01.cfg",
    "leaf-02": "leaf-02.cfg",
    "central router": "hq-wan-router.cfg",
    "HQ-WAN-RTR": "hq-wan-router.cfg",
    "1.1.1.1": "branch1-router.cfg",
    "1.1.1.2": "branch1-access.cfg",
    "2.1.1.1": "branch2-router.cfg",
    "2.1.1.2": "branch2-access.cfg",
    "3.1.1.1": "branch3-router.cfg",
    "3.1.1.2": "branch3-access.cfg",
    "4.1.1.1": "branch4-router.cfg",
    "4.1.1.2": "branch4-access.cfg",
    "BR1-WAN-RTR": "branch1-router.cfg",
    "BR1-ACCESS": "branch1-access.cfg",
    "BR2-WAN-RTR": "branch2-router.cfg",
    "BR2-ACCESS": "branch2-access.cfg",
    "BR3-WAN-RTR": "branch3-router.cfg",
    "BR3-ACCESS": "branch3-access.cfg",
    "BR4-WAN-RTR": "branch4-router.cfg",
    "BR4-ACCESS": "branch4-access.cfg",
    "EDGE-RTR": "edge-router.cfg",
    "ISP": "isp-router.cfg",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _text(node: ET.Element | None, default: str = "") -> str:
    """Return the stripped text of *node* or *default* when it is missing."""
    if node is None or node.text is None:
        return default
    return node.text.strip()


def load_xml(pkt_path: str) -> ET.Element:
    """Decrypt *pkt_path* and return the parsed root element."""
    with open(pkt_path, "rb") as handle:
        raw = handle.read()
    container = decode_bytes(raw)
    return ET.fromstring(container.xml)


def devices(root: ET.Element) -> list[dict[str, Any]]:
    """Return every device in the lab as a dictionary."""
    result: list[dict[str, Any]] = []
    network = root.find("NETWORK")
    if network is None:
        return result
    devices_node = network.find("DEVICES")
    if devices_node is None:
        return result

    for device in devices_node.findall("DEVICE"):
        engine = device.find("ENGINE")
        if engine is None:
            continue
        type_node = engine.find("TYPE")
        dev_type = _text(type_node)
        model = type_node.get("model", "") if type_node is not None else ""
        display_name = _text(engine.find("NAME"))

        hostname = ""
        running: list[str] = []
        # Only the RUNNINGCONFIG block holds the device configuration.  The
        # STARTUPCONFIG block uses the same <LINE> element name, so walking
        # every <LINE> in the engine would duplicate the whole config.
        running_node = engine.find("RUNNINGCONFIG")
        if running_node is None:
            for candidate in engine.iter("RUNNINGCONFIG"):
                running_node = candidate
                break
        if running_node is not None:
            running = [(line.text or "").rstrip() for line in running_node.findall("LINE")]
        for line in running:
            if line.startswith("hostname "):
                hostname = line.split(None, 1)[1].strip()
                break

        result.append(
            {
                "display_name": display_name,
                "name": DEVICE_NAME_MAP.get(display_name, display_name),
                "type": dev_type,
                "model": model,
                "hostname": hostname,
                "running_config": "\n".join(running),
            }
        )
    return result


def server_services(root: ET.Element) -> dict[str, dict[str, Any]]:
    """Return the service configuration of every ``Server-PT`` device."""
    result: dict[str, dict[str, Any]] = {}
    network = root.find("NETWORK")
    if network is None:
        return result
    for device in network.find("DEVICES").findall("DEVICE"):
        engine = device.find("ENGINE")
        type_node = engine.find("TYPE")
        if type_node is None or _text(type_node) != "Server":
            continue
        display_name = _text(engine.find("NAME"))

        dns_records: list[dict[str, str]] = []
        dns_server = engine.find("DNS_SERVER")
        dns_enabled = False
        if dns_server is not None:
            dns_enabled = _text(dns_server.find("ENABLED")) == "1"
            for record in dns_server.iter("RESOURCE-RECORD"):
                dns_records.append(
                    {
                        "name": _text(record.find("NAME")),
                        "type": _text(record.find("TYPE")),
                        "ttl": _text(record.find("TTL")),
                        "ip": _text(record.find("IPADDRESS")),
                    }
                )

        email: dict[str, Any] = {}
        email_node = engine.find("EMAIL_SERVER")
        if email_node is not None:
            email = {child.tag: _text(child) for child in email_node}
            email["users"] = []
            count = int(email.get("NO_OF_USERS", "0") or 0)
            for index in range(count):
                email["users"].append(
                    {
                        "username": email.get(f"USER{index}", ""),
                        "password": email.get(f"PASSWORD{index}", ""),
                    }
                )

        http_enabled = False
        http_node = engine.find("HTTP_SERVER")
        if http_node is not None:
            http_enabled = _text(http_node.find("ENABLED")) == "1"
        https_enabled = False
        https_node = engine.find("HTTPS_SERVER")
        if https_node is not None:
            https_enabled = _text(https_node.find("HTTPSENABLED")) == "1"
        ftp_enabled = False
        ftp_node = engine.find("FTP_SERVER")
        if ftp_node is not None:
            ftp_enabled = _text(ftp_node.find("ENABLED")) == "1"
        tftp_enabled = False
        tftp_node = engine.find("TFTP_SERVER")
        if tftp_node is not None:
            tftp_enabled = _text(tftp_node.find("ENABLED")) == "1"

        result[display_name] = {
            "display_name": display_name,
            "name": DEVICE_NAME_MAP.get(display_name, display_name),
            "ip": _text(engine.find("IP_ADDRESS")),
            "gateway": _text(engine.find("GATEWAY")),
            "dns_client": _text(engine.find("DNS_CLIENT/SERVER_IP")),
            "dns_enabled": dns_enabled,
            "dns_records": dns_records,
            "email": email,
            "http_enabled": http_enabled,
            "https_enabled": https_enabled,
            "ftp_enabled": ftp_enabled,
            "tftp_enabled": tftp_enabled,
        }
    return result


def client_emails(root: ET.Element) -> list[dict[str, Any]]:
    """Return the e-mail client configuration of every ``PC-PT`` device."""
    result: list[dict[str, Any]] = []
    network = root.find("NETWORK")
    if network is None:
        return result
    for device in network.find("DEVICES").findall("DEVICE"):
        engine = device.find("ENGINE")
        type_node = engine.find("TYPE")
        if type_node is None or _text(type_node) != "Pc":
            continue
        display_name = _text(engine.find("NAME"))
        client = engine.find("EMAIL_CLIENT")
        if client is None:
            continue
        result.append(
            {
                "display_name": display_name,
                "name": DEVICE_NAME_MAP.get(display_name, display_name),
                "enabled": _text(client.find("ENABLED")) == "1",
                "display_name_of_user": _text(client.find("NAME")),
                "mail_id": _text(client.find("MAIL_ID")),
                "pop3_server": _text(client.find("POP3_SERVER")),
                "smtp_server": _text(client.find("SMTP_SERVER")),
                "username": _text(client.find("USER")),
                "password": _text(client.find("PASSWORD")),
                "messages": int(_text(client.find("NO_OF_MAILS"), "0") or 0),
            }
        )
    return result


def link_table(root: ET.Element) -> list[dict[str, str]]:
    """Return every cable in the lab as ``from -> to``."""
    network = root.find("NETWORK")
    if network is None:
        return []
    ref_to_device: dict[str, str] = {}
    for device in network.find("DEVICES").findall("DEVICE"):
        engine = device.find("ENGINE")
        display_name = _text(engine.find("NAME"))
        ref_node = engine.find("SAVE_REF_ID")
        if ref_node is None:
            for candidate in engine.iter("SAVE_REF_ID"):
                ref_node = candidate
                break
        if ref_node is not None:
            ref_to_device[ref_node.text.strip()] = DEVICE_NAME_MAP.get(
                display_name, display_name
            )

    rows: list[dict[str, str]] = []
    links = network.find("LINKS")
    if links is None:
        return rows
    for link in links.findall("LINK"):
        cable = link.find("CABLE")
        if cable is None:
            continue
        ports = [_text(p) for p in cable if p.tag == "PORT"]
        src_ref = _text(cable.find("FROM"))
        dst_ref = _text(cable.find("TO"))
        rows.append(
            {
                "from_device": ref_to_device.get(src_ref, src_ref),
                "from_port": ports[0] if len(ports) > 0 else "",
                "to_device": ref_to_device.get(dst_ref, dst_ref),
                "to_port": ports[1] if len(ports) > 1 else "",
                "media": _text(link.find("TYPE")),
            }
        )
    rows.sort(key=lambda row: (row["from_device"], row["to_device"]))
    return rows


def ip_addresses(devices_list: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Return every IPv4 address configured on an interface or SVI."""
    rows: list[dict[str, str]] = []
    for device in devices_list:
        if device["type"] not in INFRA_TYPES:
            continue
        current_interface = ""
        for line in device["running_config"].splitlines():
            if line.startswith("interface "):
                current_interface = line.split(None, 1)[1].strip()
            elif line.strip().startswith("ip address ") and current_interface:
                parts = line.split()
                if len(parts) >= 4:
                    rows.append(
                        {
                            "device": device["name"],
                            "interface": current_interface,
                            "address": parts[2],
                            "mask": parts[3],
                        }
                    )
                current_interface = ""
    return rows


# --------------------------------------------------------------------------- #
# Output helpers
# --------------------------------------------------------------------------- #

def write_configs(devices_list: list[dict[str, Any]], out_dir: str) -> list[str]:
    """Write one ``.cfg`` file per infrastructure device into *out_dir*."""
    os.makedirs(out_dir, exist_ok=True)
    written: list[str] = []
    for device in devices_list:
        if device["type"] not in INFRA_TYPES:
            continue
        filename = CONFIG_FILE_MAP.get(
            device["display_name"], f"{device['name']}.cfg"
        )
        path = os.path.join(out_dir, filename)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(device["running_config"].rstrip() + "\n")
        written.append(filename)
    return written


def write_csv(rows: list[dict[str, str]], path: str, fieldnames: list[str]) -> None:
    """Write *rows* as CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pkt", help="path to the .pkt lab file")
    parser.add_argument("--list", action="store_true", help="print the device inventory")
    parser.add_argument("--xml-only", action="store_true", help="only dump the decrypted XML")
    parser.add_argument("--xml-out", help="where to write the decrypted XML")
    parser.add_argument("--out", help="directory to write per-device configs into")
    parser.add_argument("--links", action="store_true", help="print the cabling table")
    parser.add_argument("--ipam", action="store_true", help="print the IP addressing table")
    parser.add_argument("--services", action="store_true", help="print server service state")
    parser.add_argument("--json", help="write a JSON summary to this path")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.pkt):
        sys.stderr.write(f"error: no such file: {args.pkt}\n")
        return 2

    with open(args.pkt, "rb") as handle:
        raw = handle.read()
    from pkt_core import decode_bytes

    container = decode_bytes(raw)
    root = ET.fromstring(container.xml)

    if args.xml_only or args.xml_out:
        target = args.xml_out or os.path.splitext(args.pkt)[0] + ".xml"
        with open(target, "wb") as handle:
            handle.write(container.xml)
        print(f"wrote {target} ({len(container.xml):,} bytes of XML)")
        if args.xml_only and not args.xml_out:
            return 0

    device_list = devices(root)
    services = server_services(root)
    links = link_table(root)
    ipam = ip_addresses(device_list)

    if args.out:
        written = write_configs(device_list, args.out)
        print(f"wrote {len(written)} device configs to {args.out}")

    if args.list:
        print(f"\n{'DEVICE':<20} {'TYPE':<16} {'MODEL':<22} HOSTNAME")
        print("-" * 88)
        for device in device_list:
            print(
                f"{device['name']:<20} {device['type']:<16} "
                f"{device['model']:<22} {device['hostname']}"
            )
        print(f"\n{len(device_list)} devices total")

    if args.links:
        print(f"\n{'FROM DEVICE':<20} {'PORT':<16} {'MEDIA':<16} {'PORT':<16} TO DEVICE")
        print("-" * 88)
        for row in links:
            print(
                f"{row['from_device']:<20} {row['from_port']:<16} "
                f"{row['media']:<16} {row['to_port']:<16} {row['to_device']}"
            )
        print(f"\n{len(links)} cables")

    if args.ipam:
        print(f"\n{'DEVICE':<20} {'INTERFACE':<22} {'ADDRESS':<16} MASK")
        print("-" * 78)
        for row in ipam:
            print(f"{row['device']:<20} {row['interface']:<22} {row['address']:<16} {row['mask']}")

    if args.services:
        print("\nSERVER SERVICES")
        print("=" * 78)
        for name, service in services.items():
            print(f"\n{service['name']}  ({name})")
            print(f"  IP            : {service['ip']}")
            print(f"  Gateway       : {service['gateway']}")
            print(f"  HTTP / HTTPS  : {service['http_enabled']} / {service['https_enabled']}")
            print(f"  FTP / TFTP    : {service['ftp_enabled']} / {service['tftp_enabled']}")
            print(f"  DNS enabled   : {service['dns_enabled']}")
            for record in service["dns_records"]:
                print(f"      A {record['name']:<26} -> {record['ip']}  (TTL {record['ttl']})")
            email = service.get("email", {})
            print(f"  SMTP domain   : {email.get('SMTP_DOMAIN', '')}")
            print(f"  SMTP / POP3   : {email.get('SMTP_ENABLED', '0')} / {email.get('POP3_ENABLED', '0')}")
            for user in email.get("users", []):
                print(f"      mailbox {user['username']} / {user['password']}")

    if args.json:
        payload = {
            "devices": [
                {key: value for key, value in device.items() if key != "running_config"}
                | {"running_config": device["running_config"]}
                for device in device_list
            ],
            "servers": services,
            "links": links,
            "ipam": ipam,
        }
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"wrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
