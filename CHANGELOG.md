# Changelog

All notable changes to this project are documented here.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-11-16

The first production-ready release. The original student lab was audited,
every defect was fixed, and the whole project was rebuilt as a documented,
tested, open-source repository.

### Added

**Documentation**

- `README.md` — the main project README with the architecture, the inventory,
  the IP plan and the verification matrix
- `README.bn.md` — the Bengali translation
- `docs/ARCHITECTURE.md` — the layered design and the design rationale
- `docs/DEVICE-INVENTORY.md` — every device, interface, role and cable
- `docs/IPAM.md` — the complete IP addressing plan
- `docs/CONFIGURATION.md` — step-by-step configuration of every service
- `docs/TESTING.md` — the 20-test verification matrix with expected output
- `docs/TROUBLESHOOTING.md` — symptom → diagnosis → fix for 12 real faults
- `docs/VIVA_QA.md` — 40 examination questions with model answers
- `docs/NAT-PAT-ISP.md` — the English, cleaned-up PAT/ISP demo script
- `docs/SECURITY.md` — the security model and the hardening roadmap
- `docs/AUDIT-FINDINGS.md` — every defect found in the original lab
- `docs/images/topology.md` — the Mermaid and ASCII topology diagrams
- `configs/servers/README.md` — the server service definitions

**Automation**

- `scripts/pkt_export.py` — decrypt a `.pkt` and export XML, configurations,
  the inventory, the cabling table and the IP plan
- `scripts/audit_lab.py` — 35 automated health checks against the lab
- `scripts/check_ipam.py` — IP plan validation, duplicate detection and
  DHCP-range overlap detection
- `scripts/apply_fixes.py` — reproduce the hardened lab from the pristine
  original, deterministically
- `scripts/tests/test_lab.py` — 35 unit tests over the parsers and the lab

**Project infrastructure**

- `LICENSE` — MIT
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- `.gitignore`, `.gitattributes`, `.editorconfig`
- `.github/workflows/ci.yml` — audit, unit tests, lint and link checking
- `.github/ISSUE_TEMPLATE/` — bug, feature and lab-issue templates
- `.github/PULL_REQUEST_TEMPLATE.md`

**Lab content**

- `assets/web/index.html` — a corporate intranet portal for the web server,
  replacing the Packet Tracer default page

### Fixed — critical

- **The Sales mail client used `sales@gmail.com`** instead of
  `sales@company.com`. The mail server's SMTP domain is `company.com`, so the
  central demonstration of the project — Sales sending mail to HR — did not
  work. The stored test message was updated too.
- **Split-brain DNS.** The DNS service was enabled on two servers with
  conflicting zone data. `Server1` is now the only authoritative resolver.
- **A malformed DNS record.** The mail server carried the record
  `" mail.company.com"` with a leading space, which never matches a query for
  `mail.company.com`.
- **DHCP could lease the core SVI addresses.** The exclusions covered only
  `.1`–`.20` and `.254`, leaving `.252` and `.253` — the two core SVI
  addresses — allocatable.

### Fixed — high

- **Duplicate hostnames.** Nine devices used the hostname `Switch` and five
  used `Router`, making every CLI prompt ambiguous. All hostnames are now
  unique and follow a documented naming convention.
- **Typoed device names.** The branch workstations were named `192.186.x.x`
  instead of `192.168.x.x`.
- **`core-02` had no DHCP relay**, so a core failover stopped new leases.
- **The web server served the Packet Tracer default splash page**, including
  the original author's name.
- **FTP and TFTP were enabled on every server.**
- **No `portfast` / `bpduguard` on the access ports.**
- **Port-security had no maximum and no violation action** on the Sales
  access switch, and was missing entirely on the HR and Accounts switches.

### Fixed — medium and low

- Explicit `range` added to all seven DHCP pools
- `service password-encryption` enabled on all 18 infrastructure devices
- `enable secret` added to all 18 infrastructure devices
- Login banners added
- Interface descriptions added on every routed and uplinked port
- Both cores now restrict trunks to VLANs 10-12 and 20
- Unused serial interfaces on the branch routers shut down
- `interface Vlan1` shut down on the layer-2 devices
- DHCP pools reordered logically
- `leaf-02`'s hostname unified from `leafSw02`
- The stored test message rewritten with professional content

### Changed

- Device display names modernised (`Multilayer Switch0` → `access-sales-01`,
  `central router` → `HQ-WAN-RTR`, and so on). The full mapping is in
  `docs/DEVICE-INVENTORY.md`.
- Every configuration exported from the lab into `configs/` with a header
  describing the device, its platform and its role.

---

## [0.1.0] — the original lab

The first working build, before the audit.

- 42 devices: 3-tier HQ campus, 4 branches, Internet edge
- Centralised DNS, HTTP/HTTPS and email in Server VLAN 20
- OSPF area 0, HSRP, IPsec site-to-site VPN, NAT/PAT
- 46 cables

---

[1.0.0]: https://github.com/fahim3101/centralized-enterprise-server-services/releases/tag/v1.0.0
[0.1.0]: https://github.com/fahim3101/centralized-enterprise-server-services/releases/tag/v0.1.0
