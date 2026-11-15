#!/usr/bin/env python3
"""
audit_lab.py -------- Automated health check for the Centralized Enterprise Server Services lab.

Decrypts a Packet Tracer ``.pkt`` file and validates it against the design
rules documented in ``docs/ARCHITECTURE.md``.  Every check returns one of:

    PASS  the rule is satisfied
    WARN  the rule is violated but the lab still works
    FAIL  the rule is violated and the lab is broken

Exit code is ``0`` when there are no FAIL results, ``1`` otherwise.
``--strict`` additionally turns WARN results into failures.

Usage
-----
    python audit_lab.py lab/main_project.pkt
    python audit_lab.py lab/main_project.pkt --strict
    python audit_lab.py lab/main_project.pkt --json report.json
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

# The tools must be able to print on a legacy Windows console (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pkt_export import (  # noqa: E402
    INFRA_TYPES,
    client_emails,
    devices,
    link_table,
    server_services,
)

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"

#: Every rule the audit can report, so that "--allow-warning list" is
#: discoverable without reading the source.
RULE_NAMES = (
    "device inventory",
    "cabling",
    "unique hostnames",
    "hostnames set",
    "password encryption",
    "enable secret",
    "login banner",
    "DHCP pools",
    "DHCP ranges",
    "DHCP -> DNS integration",
    "DHCP exclusions",
    "single authoritative DNS",
    "DNS zone content",
    "DNS record names",
    "www record target",
    "mail record target",
    "single mail domain",
    "mail domain",
    "POP3 enabled",
    "mailbox 'sales'",
    "mailbox 'hr'",
    "client mail identity",
    "FTP disabled",
    "TFTP disabled",
    "web service",
    "edge port protection",
    "trunk VLAN scope",
    "unique interface addresses",
    "HSRP standby pairs",
    "OSPF coverage",
    "default route origination",
    "PAT configuration",
    "NAT interface roles",
    "IPsec coverage",
    "IPsec DH group",
)


@dataclass
class Report:
    """Collects the results of every audit rule."""

    rows: list[tuple[str, str, str]] = field(default_factory=list)
    #: Rules whose warnings have been reviewed and accepted on purpose.
    allowed: set[str] = field(default_factory=set)

    def add(self, status: str, rule: str, detail: str) -> None:
        if status == WARN and rule in self.allowed:
            status = PASS
            detail = f"{detail} (accepted by policy)"
        self.rows.append((status, rule, detail))

    def check(self, ok: bool, rule: str, ok_msg: str, bad_msg: str) -> None:
        self.add(PASS if ok else FAIL, rule, ok_msg if ok else bad_msg)

    def warn(self, ok: bool, rule: str, ok_msg: str, bad_msg: str) -> None:
        self.add(PASS if ok else WARN, rule, ok_msg if ok else bad_msg)

    @property
    def failures(self) -> int:
        return sum(1 for status, _, _ in self.rows if status == FAIL)

    @property
    def warnings(self) -> int:
        return sum(1 for status, _, _ in self.rows if status == WARN)

    def render(self) -> str:
        icons = {PASS: "[PASS]", WARN: "[WARN]", FAIL: "[FAIL]"}
        width = max(len(rule) for _, rule, _ in self.rows) if self.rows else 10
        lines = []
        for status, rule, detail in self.rows:
            lines.append(f"{icons[status]} {rule.ljust(width)}  {detail}")
        lines.append("")
        lines.append(
            f"{len(self.rows)} checks - "
            f"{len(self.rows) - self.failures - self.warnings} passed, "
            f"{self.warnings} warnings, {self.failures} failures"
        )
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Rule helpers
# --------------------------------------------------------------------------- #


def config_of(device: dict[str, Any]) -> str:
    return device.get("running_config", "")


def has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.MULTILINE | re.IGNORECASE) is not None


#: A configuration sub-command is indented by one space in Packet Tracer configs.
SUBCMD = r"^[ \t]+"


def audit(root: ET.Element) -> Report:
    """Run every audit rule against the decrypted lab and return the report."""
    report = Report()
    device_list = devices(root)
    services = server_services(root)
    links = link_table(root)

    infra = [d for d in device_list if d["type"] in INFRA_TYPES]

    # -- inventory --------------------------------------------------------- #
    report.check(
        len(infra) > 0,
        "device inventory",
        f"{len(infra)} infrastructure devices present",
        "no infrastructure devices found",
    )
    report.check(
        len(links) >= 40,
        "cabling",
        f"{len(links)} cables connected",
        f"only {len(links)} cables found - the topology looks incomplete",
    )

    # -- hostnames --------------------------------------------------------- #
    hostnames = [d["hostname"] for d in infra]
    duplicates = {h for h in hostnames if hostnames.count(h) > 1}
    report.check(
        not duplicates,
        "unique hostnames",
        f"all {len(infra)} device hostnames are unique",
        f"duplicate hostname(s): {', '.join(sorted(duplicates))}",
    )
    unnamed = [d["name"] for d in infra if not d["hostname"]]
    report.check(
        not unnamed,
        "hostnames set",
        "every device sets a hostname",
        f"device(s) without a hostname: {', '.join(unnamed)}",
    )

    # -- credentials ------------------------------------------------------- #
    no_enc = [d["name"] for d in infra if not has(config_of(d), r"^service password-encryption")]
    report.check(
        not no_enc,
        "password encryption",
        f"service password-encryption enabled on all {len(infra)} devices",
        f"missing on: {', '.join(no_enc)}",
    )
    no_secret = [d["name"] for d in infra if not has(config_of(d), r"^enable secret")]
    report.check(
        not no_secret,
        "enable secret",
        "every device protects the enable mode",
        f"missing on: {', '.join(no_secret)}",
    )
    no_banner = [d["name"] for d in infra if not has(config_of(d), r"^banner motd")]
    report.warn(
        not no_banner,
        "login banner",
        "every device presents a login banner",
        f"missing on: {', '.join(no_banner)}",
    )

    # -- DHCP -------------------------------------------------------------- #
    core = next((d for d in infra if d["name"] == "core-01"), None)
    if core is None:
        report.add(FAIL, "DHCP pools", "core-01 not found - cannot validate DHCP")
    else:
        text = config_of(core)
        pools = re.findall(r"^ip dhcp pool (\S+)", text, re.MULTILINE)
        report.check(
            len(pools) >= 7,
            "DHCP pools",
            f"{len(pools)} pools defined: {', '.join(pools)}",
            f"only {len(pools)} DHCP pools found, expected at least 7",
        )
        without_range = re.findall(
            r"^ip dhcp pool (\S+)\n((?:[ \t]+.*\n)*)",
            text,
            re.MULTILINE,
        )
        missing_range = [
            name
            for name, body in without_range
            if not re.search(r"^[ \t]+range ", body, re.MULTILINE)
        ]
        report.check(
            not missing_range,
            "DHCP ranges",
            "every DHCP pool declares an explicit range",
            f"pool(s) without an explicit range: {', '.join(missing_range)}",
        )
        dns_options = re.findall(r"^[ \t]+dns-server (\S+)", text, re.MULTILINE)
        expected_dns = "172.10.10.2"
        bad_dns = sorted({d for d in dns_options if d != expected_dns})
        report.check(
            bool(dns_options) and not bad_dns,
            "DHCP -> DNS integration",
            f"all {len(dns_options)} pools advertise the authoritative DNS server {expected_dns}",
            f"pool(s) advertise a different DNS server: {', '.join(bad_dns) or '<none advertised>'}",
        )

        # Excluded addresses must cover every SVI / HSRP address that lives in
        # a subnet that is actually served by DHCP.  Ranges are expanded so a
        # statement such as "excluded-address .252 .254" covers .252 as well.
        excluded_ranges: list[tuple[int, int]] = []
        for start, end_addr in re.findall(
            r"^ip dhcp excluded-address (\S+) (\S+)$", text, re.MULTILINE
        ):
            try:
                excluded_ranges.append(
                    (
                        int(ipaddress.IPv4Address(start)),
                        int(ipaddress.IPv4Address(end_addr)),
                    )
                )
            except ipaddress.AddressValueError:
                continue

        pooled_subnets: list[str] = []
        for _name, body in re.findall(
            r"^ip dhcp pool (\S+)\n((?:[ \t]+.*\n)*)", text, re.MULTILINE
        ):
            network_line = re.search(r"^[ \t]+network (\S+) ", body, re.MULTILINE)
            if network_line:
                pooled_subnets.append(network_line.group(1))

        def is_excluded(address: str) -> bool:
            try:
                value = int(ipaddress.IPv4Address(address))
            except ipaddress.AddressValueError:
                return True
            return any(low <= value <= high for low, high in excluded_ranges)

        svi_addresses = re.findall(
            r"^interface Vlan\d+\n(?:[ \t]+.*\n)*?[ \t]+ip address (\S+) ",
            text,
            re.MULTILINE,
        )
        hsrp_addresses = re.findall(r"^[ \t]+standby \d+ ip (\S+)", text, re.MULTILINE)
        pooled_prefixes = {".".join(network.split(".")[:3]) for network in pooled_subnets}
        relevant = [
            a
            for a in svi_addresses + hsrp_addresses
            if ".".join(a.split(".")[:3]) in pooled_prefixes
        ]
        uncovered = [a for a in relevant if not is_excluded(a)]
        report.check(
            not uncovered,
            "DHCP exclusions",
            "every SVI/HSRP address in a pooled subnet is excluded from DHCP",
            f"address(es) not excluded from DHCP: {', '.join(sorted(set(uncovered)))}",
        )

    # -- DNS --------------------------------------------------------------- #
    dns_servers = [s for s in services.values() if s["dns_enabled"]]
    report.check(
        len(dns_servers) == 1,
        "single authoritative DNS",
        f"exactly one DNS service enabled ({dns_servers[0]['name']})"
        if dns_servers
        else "no DNS service enabled",
        f"{len(dns_servers)} DNS services enabled - split-brain DNS: "
        + ", ".join(s["name"] for s in dns_servers),
    )
    zone_records: dict[str, str] = {}
    for server in dns_servers:
        for record in server["dns_records"]:
            zone_records[record["name"].strip()] = record["ip"]
    report.check(
        "www.company.com" in zone_records and "mail.company.com" in zone_records,
        "DNS zone content",
        "zone contains www.company.com and mail.company.com",
        f"zone is missing required records (found: {', '.join(zone_records) or 'none'})",
    )
    malformed = [
        record["name"]
        for server in services.values()
        for record in server["dns_records"]
        if record["name"] != record["name"].strip()
    ]
    report.check(
        not malformed,
        "DNS record names",
        "every DNS record name is well formed",
        f"record name(s) with leading/trailing whitespace: {malformed}",
    )
    if "www.company.com" in zone_records:
        report.check(
            zone_records["www.company.com"] == "172.10.10.1",
            "www record target",
            "www.company.com resolves to the web server 172.10.10.1",
            f"www.company.com resolves to {zone_records['www.company.com']}, expected 172.10.10.1",
        )
    if "mail.company.com" in zone_records:
        report.check(
            zone_records["mail.company.com"] == "172.10.10.3",
            "mail record target",
            "mail.company.com resolves to the mail server 172.10.10.3",
            f"mail.company.com resolves to {zone_records['mail.company.com']}, expected 172.10.10.3",
        )

    # -- Mail -------------------------------------------------------------- #
    mail_servers = [
        s
        for s in services.values()
        if s.get("email", {}).get("SMTP_ENABLED") == "1" and s.get("email", {}).get("SMTP_DOMAIN")
    ]
    mail_summary = (
        f"exactly one mail server with a domain ({mail_servers[0]['name']})"
        if mail_servers
        else "no mail server with an SMTP domain"
    )
    report.check(
        len(mail_servers) == 1,
        "single mail domain",
        mail_summary,
        f"{len(mail_servers)} mail servers define an SMTP domain",
    )
    if mail_servers:
        mail = mail_servers[0]
        domain = mail["email"]["SMTP_DOMAIN"]
        report.check(
            domain == "company.com",
            "mail domain",
            f"SMTP domain is {domain}",
            f"SMTP domain is {domain!r}, expected 'company.com'",
        )
        report.check(
            mail["email"].get("POP3_ENABLED") == "1",
            "POP3 enabled",
            "POP3 retrieval is enabled on the mail server",
            "POP3 is disabled on the mail server",
        )
        users = [u["username"] for u in mail["email"].get("users", [])]
        for required in ("sales", "hr"):
            report.check(
                required in users,
                f"mailbox '{required}'",
                f"mailbox {required} exists on {mail['name']}",
                f"mailbox {required} is missing on {mail['name']}",
            )

    # -- client mail identity ---------------------------------------------- #
    identity_issues: list[str] = []
    for client in client_emails(root):
        if not client["enabled"] or not client["mail_id"]:
            continue
        if not client["mail_id"].endswith("@company.com"):
            identity_issues.append(f"{client['name']} -> {client['mail_id']}")
    report.check(
        not identity_issues,
        "client mail identity",
        "every configured mail client uses the company.com domain",
        "wrong mail identity: " + ", ".join(identity_issues),
    )

    # -- server services ---------------------------------------------------- #
    ftp_on = [s["name"] for s in services.values() if s["ftp_enabled"]]
    report.check(
        not ftp_on,
        "FTP disabled",
        "FTP is disabled on every server",
        f"FTP still enabled on: {', '.join(ftp_on)}",
    )
    tftp_on = [s["name"] for s in services.values() if s["tftp_enabled"]]
    report.check(
        not tftp_on,
        "TFTP disabled",
        "TFTP is disabled on every server",
        f"TFTP still enabled on: {', '.join(tftp_on)}",
    )
    web_servers = [s for s in services.values() if s["http_enabled"]]
    report.check(
        bool(web_servers),
        "web service",
        "at least one HTTP server is enabled",
        "no HTTP server is enabled",
    )

    # -- spanning tree ------------------------------------------------------ #
    access_ports = 0
    protected_ports = 0
    for device in infra:
        text = config_of(device)
        current = ""
        for line in text.splitlines():
            if line.startswith("interface "):
                current = line.split(None, 1)[1].strip()
                portfast = False
                bpduguard = False
            elif current and "switchport access vlan" in line:
                access_ports += 1
                portfast = "spanning-tree portfast" in text
                bpduguard = "spanning-tree bpduguard enable" in text
                if portfast and bpduguard:
                    protected_ports += 1
                current = ""
    report.warn(
        access_ports == 0 or protected_ports == access_ports,
        "edge port protection",
        f"all {access_ports} access ports enable portfast/bpduguard",
        f"only {protected_ports}/{access_ports} access ports enable portfast/bpduguard",
    )

    # -- trunk consistency --------------------------------------------------- #
    core_texts = [config_of(d) for d in infra if d["name"] in ("core-01", "core-02")]
    restricted = [
        has(text, r"^[ \t]+switchport trunk allowed vlan 10-12,20") for text in core_texts
    ]
    report.check(
        core_texts and all(restricted),
        "trunk VLAN scope",
        "both cores restrict trunks to VLAN 10-12,20",
        "the two cores do not agree on the trunk VLAN list",
    )

    # -- unique IP addresses ------------------------------------------------- #
    # A configured interface address must be unique.  An HSRP standby address is
    # deliberately shared by the two cores, so it is validated separately.
    addresses: list[str] = []
    standby: dict[str, list[str]] = {}
    for device in infra:
        text = config_of(device)
        for match in re.finditer(r"^[ \t]+ip address (\S+) (\S+)", text, re.MULTILINE):
            addresses.append(match.group(1))
        for match in re.finditer(r"^[ \t]+standby (\d+) ip (\S+)", text, re.MULTILINE):
            standby.setdefault(match.group(2), []).append(
                f"{device['name']} (group {match.group(1)})"
            )

    dupes = sorted({a for a in addresses if addresses.count(a) > 1})
    report.check(
        not dupes and bool(addresses),
        "unique interface addresses",
        f"all {len(addresses)} configured interface addresses are unique",
        f"duplicate address(es): {', '.join(dupes) if dupes else 'none found (is the config empty?)'}",
    )

    bad_hsrp = {
        address: owners
        for address, owners in standby.items()
        if len(owners) != 2 or len({o.split()[0] for o in owners}) != 2
    }
    report.check(
        not bad_hsrp,
        "HSRP standby pairs",
        f"all {len(standby)} standby addresses are claimed by exactly two cores",
        "HSRP address(es) not claimed by exactly two devices: "
        + "; ".join(f"{a} -> {', '.join(o)}" for a, o in bad_hsrp.items()),
    )

    # -- OSPF / routing ------------------------------------------------------ #
    ospf_devices = [d for d in infra if "router ospf" in config_of(d)]
    report.check(
        len(ospf_devices) >= 10,
        "OSPF coverage",
        f"OSPF is configured on {len(ospf_devices)} devices",
        f"OSPF is only configured on {len(ospf_devices)} devices",
    )
    originators = [
        d["name"] for d in infra if has(config_of(d), r"^ default-information originate")
    ]
    report.check(
        bool(originators),
        "default route origination",
        f"default-information originate present on: {', '.join(originators)}",
        "no device originates a default route - branches cannot reach the Internet",
    )

    # -- NAT / PAT ------------------------------------------------------------ #
    edge = next((d for d in infra if d["name"] == "EDGE-RTR"), None)
    report.check(
        edge is not None
        and has(config_of(edge), r"^ip nat inside source list \d+ interface .* overload"),
        "PAT configuration",
        "EDGE-RTR performs PAT with overloading",
        "EDGE-RTR is missing 'ip nat inside source list ... overload'",
    )
    if edge is not None:
        inside = has(config_of(edge), r"^[ \t]+ip nat inside\s*$")
        outside = has(config_of(edge), r"^[ \t]+ip nat outside\s*$")
        report.check(
            inside and outside,
            "NAT interface roles",
            "EDGE-RTR marks one interface inside and one outside",
            "EDGE-RTR does not mark both a NAT inside and a NAT outside interface",
        )

    # -- IPsec ---------------------------------------------------------------- #
    vpn_devices = [d for d in infra if "crypto ipsec transform-set" in config_of(d)]
    report.check(
        len(vpn_devices) >= 5,
        "IPsec coverage",
        f"IPsec is configured on {len(vpn_devices)} devices",
        f"IPsec is only configured on {len(vpn_devices)} devices, expected at least 5",
    )
    weak_group = [d["name"] for d in vpn_devices if has(config_of(d), r"^[ \t]+group 2\s*$")]
    report.warn(
        not weak_group,
        "IPsec DH group",
        "all tunnels use a modern Diffie-Hellman group",
        f"weak IKE group 2 used on: {', '.join(weak_group)} - see docs/SECURITY.md",
    )

    return report


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("pkt", help="path to the .pkt lab file")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument(
        "--allow-warning",
        action="append",
        default=[],
        metavar="RULE",
        help=(
            "accept a warning for this rule (repeatable). "
            "Use 'list' to print the available rule names."
        ),
    )
    parser.add_argument("--json", help="write the report as JSON to this path")
    args = parser.parse_args(argv)

    if "list" in args.allow_warning:
        print("\n".join(sorted(RULE_NAMES)))
        return 0

    if not os.path.isfile(args.pkt):
        sys.stderr.write(f"error: no such file: {args.pkt}\n")
        return 2

    try:
        from pkt_core import decode_bytes
    except ImportError:
        sys.stderr.write(
            "error: install the dependencies with: pip install -r scripts/requirements.txt\n"
        )
        return 2

    with open(args.pkt, "rb") as handle:
        raw = handle.read()
    root = ET.fromstring(decode_bytes(raw).xml)

    report = audit(root)
    report.allowed.update(args.allow_warning)
    report.rows = [
        (PASS if status == WARN and rule in report.allowed else status, rule, detail)
        for status, rule, detail in report.rows
    ]
    print(report.render())

    if args.json:
        payload = [
            {"status": status, "rule": rule, "detail": detail}
            for status, rule, detail in report.rows
        ]
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"\nwrote {args.json}")

    if report.failures:
        return 1
    if args.strict and report.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
