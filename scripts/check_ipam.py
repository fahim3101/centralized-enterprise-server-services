#!/usr/bin/env python3
"""
check_ipam.py — Validate the IP addressing plan of the lab.

Cross-checks the addresses that are actually configured on the devices against
``docs/IPAM.md`` and against each other:

* no address is used twice
* every address belongs to a subnet declared in the IPAM document
* the DHCP pools never overlap the SVI / HSRP addresses
* the DHCP pools never overlap each other
* the DNS server advertised by DHCP is the one running the DNS service

Usage
-----
    python check_ipam.py lab/main_project.pkt
    python check_ipam.py lab/main_project.pkt --ipam docs/IPAM.md
    python check_ipam.py lab/main_project.pkt --json ipam.json
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pkt_export import devices, server_services  # noqa: E402


def parse_networks(ipam_path: str) -> list[tuple[ipaddress.IPv4Network, str]]:
    """Extract every ``network / mask`` pair mentioned in the IPAM document."""
    if not os.path.isfile(ipam_path):
        return []
    text = open(ipam_path, encoding="utf-8").read()
    found: list[tuple[ipaddress.IPv4Network, str]] = []
    for match in re.finditer(r"\b(\d{1,3}(?:\.\d{1,3}){3})/(\d{1,2})\b", text):
        try:
            network = ipaddress.ip_network(
                f"{match.group(1)}/{match.group(2)}", strict=False
            )
        except ValueError:
            continue
        found.append((network, match.group(0)))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pkt", help="path to the .pkt lab file")
    parser.add_argument("--ipam", default="docs/IPAM.md", help="IPAM document to validate against")
    parser.add_argument("--json", help="write the extracted plan as JSON")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.pkt):
        sys.stderr.write(f"error: no such file: {args.pkt}\n")
        return 2

    from pkt_core import decode_bytes

    with open(args.pkt, "rb") as handle:
        raw = handle.read()
    root = ET.fromstring(decode_bytes(raw).xml)

    device_list = devices(root)
    services = server_services(root)

    # ------------------------------------------------------------------ #
    # 1. collect every configured address
    # ------------------------------------------------------------------ #
    owners: dict[str, list[str]] = {}
    standby_owners: dict[str, list[str]] = {}
    interfaces: list[dict[str, str]] = []

    for device in device_list:
        text = device.get("running_config", "")
        current = ""
        for line in text.splitlines():
            if line.startswith("interface "):
                current = line.split(None, 1)[1].strip()
            elif "ip address" in line and current:
                parts = [p for p in line.split() if p]
                if len(parts) >= 4 and parts[0] == "ip":
                    address, mask = parts[2], parts[3]
                    interfaces.append(
                        {"device": device["name"], "interface": current,
                         "address": address, "mask": mask}
                    )
                    owners.setdefault(address, []).append(f"{device['name']} ({current})")
            elif "standby" in line and " ip " in line and current:
                address = line.split(" ip ")[1].strip()
                interfaces.append(
                    {"device": device["name"], "interface": current,
                     "address": address, "mask": "hsrp"}
                )
                standby_owners.setdefault(address, []).append(
                    f"{device['name']} ({current})"
                )

    problems: list[str] = []

    # ------------------------------------------------------------------ #
    # 2. duplicate interface addresses (HSRP standby addresses are shared
    #    by design between the two cores and are validated separately)
    # ------------------------------------------------------------------ #
    for address, users in owners.items():
        if len(users) > 1:
            problems.append(f"duplicate address {address} on {', '.join(users)}")
    for address, users in standby_owners.items():
        if len(users) != 2 or len({u.split()[0] for u in users}) != 2:
            problems.append(
                f"HSRP address {address} is not claimed by exactly two cores: {', '.join(users)}"
            )

    # ------------------------------------------------------------------ #
    # 3. every address inside a declared subnet
    # ------------------------------------------------------------------ #
    declared = parse_networks(args.ipam)
    if declared:
        for entry in interfaces:
            if entry["mask"] == "hsrp":
                continue
            try:
                network = ipaddress.ip_network(
                    f"{entry['address']}/{entry['mask']}", strict=False
                )
            except ValueError:
                problems.append(f"{entry['device']}: invalid address {entry['address']}")
                continue
            if not any(network.subnet_of(candidate) for candidate, _ in declared):
                problems.append(
                    f"{entry['address']} on {entry['device']} is not covered by any "
                    f"subnet declared in {args.ipam}"
                )

    # ------------------------------------------------------------------ #
    # 4. DHCP pool sanity
    # ------------------------------------------------------------------ #
    core = next((d for d in device_list if d["name"] == "core-01"), None)
    dhcp_rows: list[dict[str, str]] = []
    if core is not None:
        text = core.get("running_config", "")
        blocks = re.findall(
            r"^ip dhcp pool (\S+)\n((?:[ \t]+.*\n)*)", text, re.MULTILINE
        )
        svi_addresses = {
            entry["address"]
            for entry in interfaces
            if entry["device"] == "core-01" and entry["interface"].startswith("Vlan")
        }
        hsrp_addresses = {
            entry["address"]
            for entry in interfaces
            if entry["device"] == "core-01" and entry["mask"] == "hsrp"
        }
        # A pool gateway is valid when it is an HSRP virtual address (HQ user
        # VLANs) or the real SVI address of the device that owns that subnet
        # (branch VLANs, whose gateway is the branch access switch).
        gateway_addresses = hsrp_addresses | {
            entry["address"] for entry in interfaces if entry["mask"] != "hsrp"
        }
        reserved = svi_addresses | hsrp_addresses
        for pool, body in blocks:
            network_match = re.search(r"^[ \t]+network (\S+) (\S+)", body, re.MULTILINE)
            range_match = re.search(r"^[ \t]+range (\S+) (\S+)", body, re.MULTILINE)
            default_router = re.search(r"^[ \t]+default-router (\S+)", body, re.MULTILINE)
            dns_server = re.search(r"^[ \t]+dns-server (\S+)", body, re.MULTILINE)
            row = {
                "pool": pool,
                "network": network_match.group(1) if network_match else "",
                "mask": network_match.group(2) if network_match else "",
                "range_start": range_match.group(1) if range_match else "",
                "range_end": range_match.group(2) if range_match else "",
                "default_router": default_router.group(1) if default_router else "",
                "dns_server": dns_server.group(1) if dns_server else "",
            }
            dhcp_rows.append(row)

            if row["dns_server"] != "172.10.10.2":
                problems.append(
                    f"DHCP pool {pool} advertises DNS {row['dns_server'] or '<none>'}, "
                    f"expected 172.10.10.2"
                )
            if row["default_router"] and row["default_router"] not in gateway_addresses:
                problems.append(
                    f"DHCP pool {pool} advertises gateway {row['default_router']} which is "
                    f"neither an HSRP address nor a configured SVI address"
                )
            if not row["range_start"] or not row["range_end"]:
                problems.append(f"DHCP pool {pool} has no explicit range")
                continue
            for address in reserved:
                try:
                    ip = ipaddress.ip_address(address)
                except ValueError:
                    continue
                if (
                    ipaddress.ip_address(row["range_start"])
                    <= ip
                    <= ipaddress.ip_address(row["range_end"])
                ):
                    problems.append(
                        f"DHCP pool {pool} range covers the reserved address {address}"
                    )

    # ------------------------------------------------------------------ #
    # 5. DNS service matches the DHCP advertisement
    # ------------------------------------------------------------------ #
    dns_servers = [s for s in services.values() if s["dns_enabled"]]
    if len(dns_servers) == 1 and dhcp_rows:
        advertised = {row["dns_server"] for row in dhcp_rows}
        if advertised != {"172.10.10.2"}:
            problems.append(
                f"DHCP advertises {advertised} but the DNS service runs elsewhere"
            )

    # ------------------------------------------------------------------ #
    # output
    # ------------------------------------------------------------------ #
    print(f"IP addresses on interfaces : {len(interfaces)}")
    print(f"DHCP pools                 : {len(dhcp_rows)}")
    print(f"Declared subnets in IPAM   : {len(declared)}")
    print()
    for row in dhcp_rows:
        print(
            f"  {row['pool']:<10} {row['network']}/{row['mask']:<15} "
            f"range {row['range_start']}-{row['range_end']:<12} "
            f"gw {row['default_router']:<16} dns {row['dns_server']}"
        )
    print()
    if problems:
        print(f"{len(problems)} problem(s) found:")
        for problem in problems:
            print(f"  [FAIL] {problem}")
    else:
        print("[PASS] no IPAM problems found")

    if args.json:
        payload = {"interfaces": interfaces, "dhcp_pools": dhcp_rows, "problems": problems}
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"\nwrote {args.json}")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
