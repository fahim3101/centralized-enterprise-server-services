"""Tests for the Packet Tracer lab parsers.

Run with::

    python -m pytest scripts/tests -q
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

import pytest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(SCRIPTS)
sys.path.insert(0, SCRIPTS)

from pkt_export import (  # noqa: E402
    CONFIG_FILE_MAP,
    DEVICE_NAME_MAP,
    client_emails,
    decode_bytes,
    devices,
    link_table,
    server_services,
)

LAB = os.path.join(REPO, "lab", "main_project.pkt")
ORIGINAL = os.path.join(REPO, "lab", "main_project-original.pkt")


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def root():
    with open(LAB, "rb") as handle:
        return ET.fromstring(decode_bytes(handle.read()).xml)


@pytest.fixture(scope="module")
def original_root():
    with open(ORIGINAL, "rb") as handle:
        return ET.fromstring(decode_bytes(handle.read()).xml)


@pytest.fixture(scope="module")
def device_list(root):
    return devices(root)


@pytest.fixture(scope="module")
def services(root):
    return server_services(root)


# --------------------------------------------------------------------------- #
# Container
# --------------------------------------------------------------------------- #


def test_lab_file_exists():
    assert os.path.isfile(LAB), "lab/main_project.pkt is missing"


def test_lab_decrypts_to_packettracer5(root):
    assert root.tag == "PACKETTRACER5"


def test_lab_reports_its_version(root):
    version = root.findtext("VERSION")
    assert version, "the lab has no version element"
    assert version.startswith("9."), f"unexpected Packet Tracer version {version}"


def test_original_and_patched_are_different():
    with open(LAB, "rb") as a, open(ORIGINAL, "rb") as b:
        assert a.read() != b.read(), "the patched lab is identical to the original"


# --------------------------------------------------------------------------- #
# Inventory
# --------------------------------------------------------------------------- #


def test_device_count(device_list):
    assert len(device_list) == 42, f"expected 42 devices, found {len(device_list)}"


def test_infrastructure_device_count(device_list):
    infra = [d for d in device_list if d["type"] in ("Router", "MultiLayerSwitch")]
    assert len(infra) == 18, f"expected 18 infrastructure devices, found {len(infra)}"


def test_every_device_has_a_hostname(device_list):
    """Only infrastructure devices carry an IOS hostname."""
    missing = [
        d["name"]
        for d in device_list
        if d["type"] in ("Router", "MultiLayerSwitch") and not d["hostname"]
    ]
    assert not missing, f"devices without a hostname: {missing}"


def test_hostnames_are_unique(device_list):
    hostnames = [d["hostname"] for d in device_list if d["hostname"]]
    duplicates = {h for h in hostnames if hostnames.count(h) > 1}
    assert not duplicates, f"duplicate hostnames: {duplicates}"


def test_no_generic_hostnames_remain(device_list):
    generic = {
        d["name"] for d in device_list if d["hostname"] in ("Switch", "Router", "Server", "PC")
    }
    assert not generic, f"generic hostnames still in use: {generic}"


def test_running_config_is_not_duplicated(device_list):
    for device in device_list:
        config = device["running_config"]
        if not config:
            continue
        assert config.count("hostname ") == 1, f"{device['name']} has a duplicated running-config"


# --------------------------------------------------------------------------- #
# Naming
# --------------------------------------------------------------------------- #


def test_branch_workstations_are_renamed(device_list):
    names = {d["name"] for d in device_list}
    for stale in ("192.186.13.1", "192.186.16.2", "192.168.10.1", "central router"):
        assert stale not in names, f"the old device name {stale} is still present"


def test_new_device_names_exist(device_list):
    names = {d["name"] for d in device_list}
    for expected in (
        "core-01",
        "core-02",
        "leaf-01",
        "leaf-02",
        "access-sales-01",
        "access-hr-01",
        "access-accounts-01",
        "HQ-WAN-RTR",
        "EDGE-RTR",
        "ISP",
        "BR1-WAN-RTR",
        "BR4-ACCESS",
        "SALES-PC1",
        "HR-PC1",
        "BR4-PC2",
    ):
        assert expected in names, f"device {expected} is missing"


def test_name_maps_cover_every_renamed_device():
    assert set(DEVICE_NAME_MAP.values()) <= set(DEVICE_NAME_MAP.values())
    # every renamed target must be resolvable back to itself
    for value in DEVICE_NAME_MAP.values():
        assert value not in DEVICE_NAME_MAP or DEVICE_NAME_MAP[value] == value


def test_config_file_map_has_no_duplicate_targets():
    """The map holds both the old and the new name of the same device.

    Those two keys are allowed to point at the same file - they are the same
    device before and after the rename.  Two *different* devices may never
    share a file.
    """
    targets = list(CONFIG_FILE_MAP.values())
    duplicates = {t for t in targets if targets.count(t) > 1}
    for target in duplicates:
        owners = [k for k, v in CONFIG_FILE_MAP.items() if v == target]
        assert len(owners) == 2, f"{target} is claimed by {owners}"
        old, new = owners
        assert DEVICE_NAME_MAP.get(old, old) == new, f"{old} and {new} are not the same device"


# --------------------------------------------------------------------------- #
# Cabling
# --------------------------------------------------------------------------- #


def test_cable_count(root):
    links = link_table(root)
    assert len(links) == 46, f"expected 46 cables, found {len(links)}"


def test_every_cable_has_both_ends(root):
    for link in link_table(root):
        assert link["from_device"] != "?"
        assert link["to_device"] != "?"
        assert link["from_port"]
        assert link["to_port"]


# --------------------------------------------------------------------------- #
# Services
# --------------------------------------------------------------------------- #


def test_exactly_one_dns_server(services):
    dns = [s for s in services.values() if s["dns_enabled"]]
    assert len(dns) == 1, f"expected one DNS server, found {[s['name'] for s in dns]}"


def test_dns_zone_contains_the_required_names(services):
    dns = [s for s in services.values() if s["dns_enabled"]][0]
    names = {record["name"] for record in dns["dns_records"]}
    assert "www.company.com" in names
    assert "mail.company.com" in names


def test_no_dns_record_has_surrounding_whitespace(services):
    for server in services.values():
        for record in server["dns_records"]:
            assert record["name"] == record["name"].strip(), (
                f"malformed DNS record name {record['name']!r}"
            )


def test_web_server_serves_the_company_portal(root):
    """Server0's index.html must be the corporate portal, not the PT default."""
    found = False
    for device in root.find("NETWORK").find("DEVICES").findall("DEVICE"):
        engine = device.find("ENGINE")
        type_node = engine.find("TYPE")
        if type_node is None or type_node.text != "Server":
            continue
        if engine.find("NAME").text != "Server0":
            continue
        for filesystem in engine.iter("FILE"):
            if filesystem.find("NAME").text != "http:":
                continue
            for entry in filesystem.find("FILES").findall("FILE"):
                if entry.find("NAME").text != "index.html":
                    continue
                text = entry.find("FILE_CONTENT/TEXT").text or ""
                found = True
                assert "Centralized Enterprise Server Services" in text
                assert "COMPANY.COM" in text
                # the stock Packet Tracer page must be gone
                assert "Quick Links" not in text
                assert "Abdullah Shanto" not in text
                assert "helloworld.html" not in text
    assert found, "Server0 has no index.html"


def test_web_page_is_not_double_escaped(root):
    """The stored page must be the raw HTML, escaped exactly once by the XML.

    If the page were escaped before it was assigned to the XML text node, the
    browser would render the markup source instead of the portal.
    """
    page_file = os.path.join(REPO, "assets", "web", "index.html")
    with open(page_file, encoding="utf-8") as handle:
        expected = handle.read()

    for device in root.find("NETWORK").find("DEVICES").findall("DEVICE"):
        engine = device.find("ENGINE")
        type_node = engine.find("TYPE")
        if type_node is None or type_node.text != "Server":
            continue
        if engine.find("NAME").text != "Server0":
            continue
        for filesystem in engine.iter("FILE"):
            if filesystem.find("NAME").text != "http:":
                continue
            for entry in filesystem.find("FILES").findall("FILE"):
                if entry.find("NAME").text != "index.html":
                    continue
                text = entry.find("FILE_CONTENT/TEXT").text or ""
                assert text == expected, "the stored page is not the raw HTML"
                assert "&lt;!DOCTYPE" not in text, "the page is double escaped"
                assert "<!DOCTYPE html>" in text


def test_mail_server_has_the_company_domain(services):
    mail = [s for s in services.values() if s["email"].get("SMTP_DOMAIN")]
    assert len(mail) == 1
    assert mail[0]["email"]["SMTP_DOMAIN"] == "company.com"
    assert mail[0]["email"]["POP3_ENABLED"] == "1"


def test_mail_server_has_the_expected_mailboxes(services):
    mail = [s for s in services.values() if s["email"].get("SMTP_DOMAIN")][0]
    users = {u["username"] for u in mail["email"]["users"]}
    assert {"sales", "hr"} <= users


def test_ftp_and_tftp_are_disabled(services):
    for server in services.values():
        assert not server["ftp_enabled"], f"FTP is still enabled on {server['name']}"
        assert not server["tftp_enabled"], f"TFTP is still enabled on {server['name']}"


def test_client_mail_identities_use_the_company_domain(root):
    for client in client_emails(root):
        if client["enabled"] and client["mail_id"]:
            assert client["mail_id"].endswith("@company.com"), (
                f"{client['name']} has the mail identity {client['mail_id']}"
            )


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #


def test_dhcp_pools_have_explicit_ranges(device_list):
    core = next(d for d in device_list if d["name"] == "core-01")
    config = core["running_config"]
    assert config.count("ip dhcp pool ") == 7
    assert config.count(" range ") == 7, "a DHCP pool has no explicit range"


def test_dhcp_pools_all_advertise_the_central_dns(device_list):
    core = next(d for d in device_list if d["name"] == "core-01")
    config = core["running_config"]
    assert config.count("dns-server 172.10.10.2") == 7
    # no pool may point at any other DNS server
    other = [
        line.strip()
        for line in config.splitlines()
        if "dns-server" in line and "dns-server 172.10.10.2" not in line
    ]
    assert not other, f"a pool advertises a different DNS server: {other}"


def test_dhcp_excludes_the_svi_and_hsrp_addresses(device_list):
    core = next(d for d in device_list if d["name"] == "core-01")
    config = core["running_config"]
    for third in range(10, 17):
        assert f"ip dhcp excluded-address 192.168.{third}.252 192.168.{third}.254" in config, (
            f"VLAN {third} does not exclude the SVI and HSRP addresses"
        )


def test_core_02_can_relay_dhcp(device_list):
    core = next(d for d in device_list if d["name"] == "core-02")
    assert core["running_config"].count("ip helper-address 10.1.1.1") == 3


def test_both_cores_restrict_the_trunks(device_list):
    for name in ("core-01", "core-02"):
        core = next(d for d in device_list if d["name"] == name)
        assert "switchport trunk allowed vlan 10-12,20" in core["running_config"]


def test_access_ports_are_hardened(device_list):
    """Every switch that terminates a workstation must harden its edge ports."""
    switches = [
        d
        for d in device_list
        if d["type"] == "MultiLayerSwitch"
        and (d["name"].startswith("access-") or d["name"].endswith("-ACCESS"))
    ]
    assert len(switches) == 7, f"expected 7 access switches, found {len(switches)}"
    for device in switches:
        config = device["running_config"]
        assert "spanning-tree portfast" in config, f"{device['name']} lacks portfast"
        assert "spanning-tree bpduguard enable" in config, f"{device['name']} lacks bpduguard"
        assert "switchport port-security maximum 1" in config
        assert "switchport port-security violation shutdown" in config


def test_all_devices_have_a_banner_and_an_enable_secret(device_list):
    for device in device_list:
        if device["type"] not in ("Router", "MultiLayerSwitch"):
            continue
        config = device["running_config"]
        assert "banner motd" in config, f"{device['name']} has no banner"
        assert "enable secret" in config, f"{device['name']} has no enable secret"
        assert "service password-encryption" in config
        assert "no service password-encryption" not in config


def test_interface_descriptions_exist_on_the_wan_links(device_list):
    for device in device_list:
        if device["name"] not in ("EDGE-RTR", "ISP", "HQ-WAN-RTR"):
            continue
        assert "description" in device["running_config"], (
            f"{device['name']} has no interface descriptions"
        )


def test_nat_is_configured_on_the_edge_router(device_list):
    edge = next(d for d in device_list if d["name"] == "EDGE-RTR")
    config = edge["running_config"]
    assert "ip nat inside source list 1 interface GigabitEthernet0/1 overload" in config
    assert "ip nat inside" in config
    assert "ip nat outside" in config


def test_ospf_covers_every_site(device_list):
    ospf = [d for d in device_list if "router ospf 1" in d["running_config"]]
    assert len(ospf) >= 10, f"only {len(ospf)} devices run OSPF"


def test_core_01_originates_the_default_route(device_list):
    core = next(d for d in device_list if d["name"] == "core-01")
    assert "default-information originate" in core["running_config"]
    assert "ip route 0.0.0.0 0.0.0.0 10.3.3.2" in core["running_config"]
