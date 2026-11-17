# Graph Report - Centralized Enterprise Server Services  (2026-11-18)

## Corpus Check
- Corpus is ~40,435 words - fits in a single context window. You may not need a graph.

## Summary
- 433 nodes · 645 edges · 41 communities (22 shown, 19 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 129 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Lab Tooling & Imports
- Test Suite & Fixtures
- Fix Pipeline & Config Helpers
- Configuration Guide Concepts
- Topology Diagram Entities
- CI Workflow Structure
- Corporate Portal Design
- Layered Architecture Concepts
- WAN Design Rationale
- CI Pipeline Metadata
- Community Files & Templates
- Hardening Overlays
- Audit Findings & Defects
- Reference Notes & Discrepancies
- Service & Traffic Paths
- Changelog & Versioning
- Audit Report Data Model
- DHCP & DNS Integration
- Central Server Services
- Device Inventory & Cabling
- NAT/PAT Demo Script
- Internet Edge Addressing
- IPsec & Security Gaps
- Access Port Hardening
- Device Naming & Typos
- PAT Proof & Internet Tests
- Viva & Q&A Content
- Management Baseline
- Subnet Mask & IPAM Rules
- Demo Closing Statements
- NAT Statistics
- Edge Security
- Short Demo Sequence
- Traffic Generation
- Troubleshooting Patterns
- Python Dependencies
- Feature Request Template
- Security Policy
- Unenforced Controls
- Troubleshooting Guide
- Diagnostic Cheat Sheet

## God Nodes (most connected - your core abstractions)
1. `docs/AUDIT-FINDINGS.md - Defect Record` - 24 edges
2. `README.md - Main Project README` - 20 edges
3. `docs/ARCHITECTURE.md - Layered Design` - 18 edges
4. `audit()` - 17 edges
5. `apply_fixes()` - 12 edges
6. `devices()` - 12 edges
7. `server_services()` - 12 edges
8. `link_table()` - 10 edges
9. `with` - 9 edges
10. `Report` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Service architecture - one DHCP server and one DNS server` --semantically_similar_to--> `Centralized DNS - Server1 at 172.10.10.2`  [INFERRED] [semantically similar]
  docs/ARCHITECTURE.md → README.md
- `One-sentence design statement` --semantically_similar_to--> `PAT (Port Address Translation)`  [INFERRED] [semantically similar]
  docs/reference/isp-nat-pat-live-demo.pdf → docs/NAT-PAT-ISP.md
- `Service architecture - one DHCP server and one DNS server` --semantically_similar_to--> `Centralized DHCP - core-01 for seven networks`  [INFERRED] [semantically similar]
  docs/ARCHITECTURE.md → README.md
- `C-02 Split-brain DNS on two servers` --semantically_similar_to--> `Why one authoritative DNS server`  [INFERRED] [semantically similar]
  docs/AUDIT-FINDINGS.md → README.md
- `NAT/PAT plus ISP live demo script (Bengali)` --semantically_similar_to--> `NAT/PAT plus ISP live demonstration script`  [INFERRED] [semantically similar]
  docs/reference/isp-nat-pat-live-demo.pdf → docs/NAT-PAT-ISP.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Centralized DNS, Web, Email and DHCP services** — readme_centralized_dns, readme_centralized_web, readme_centralized_email, readme_centralized_dhcp, assets_web_index_document [EXTRACTED 1.00]
- **Documented hardening path for production** — configs_hardened_overlays, docs_audit_findings_advisory_findings, configs_hardened_why_not_applied, security_document [INFERRED 0.85]
- **Verification commands shared by docs, PR template and CI** — contributing_audit_commands, _github_pull_request_template_document, configs_readme_ci_diff, readme_verification_matrix [INFERRED 0.75]
- **PAT demonstration flow across the documentation** — docs_nat_pat_isp_pat, docs_reference_isp_nat_pat_live_demo_pat_proof, docs_ipam_nat_translation_table, docs_testing_branch_internet_test, docs_configuration_nat_pat [INFERRED 0.85]
- **Centralized server services design** — docs_configuration_server_services, docs_reference_server_services_notes_dns, docs_reference_server_services_notes_http, docs_reference_server_services_notes_email, docs_configuration_dhcp_dns_integration, docs_configuration_ospf [INFERRED 0.85]
- **Defense-in-depth security controls** — docs_security_department_isolation, docs_security_ipsec_wan, docs_security_access_hardening, docs_configuration_hsrp, docs_nat_pat_isp_no_inbound_mapping [INFERRED 0.85]
- **Branch sites connected to HQ via IPsec site-to-site VPN** — docs_images_topology_br1_wan_rtr, docs_images_topology_br2_wan_rtr, docs_images_topology_br3_wan_rtr, docs_images_topology_br4_wan_rtr, docs_images_topology_hq_wan_rtr [EXTRACTED 1.00]
- **HQ dual-homed redundant access/leaf/core fabric** — docs_images_topology_access_sales_01, docs_images_topology_access_hr_01, docs_images_topology_access_accounts_01, docs_images_topology_leaf_01, docs_images_topology_leaf_02, docs_images_topology_core_01, docs_images_topology_core_02 [EXTRACTED 1.00]
- **Centralised services on Server VLAN 20 shared by HQ and all four branches** — docs_images_topology_server_vlan_20, docs_images_topology_server0, docs_images_topology_server1, docs_images_topology_server2, docs_images_topology_core_01, docs_images_topology_br1_pc, docs_images_topology_br2_pc, docs_images_topology_br3_pc, docs_images_topology_br4_pc [INFERRED 0.85]

## Communities (41 total, 19 thin omitted)

### Community 0 - "Lab Tooling & Imports"
Cohesion: 0.08
Nodes (22): main(), audit(), config_of(), has(), main(), main(), parse_networks(), load() (+14 more)

### Community 1 - "Test Suite & Fixtures"
Cohesion: 0.04
Nodes (12): device_list(), original_root(), root(), services(), test_access_ports_are_hardened(), test_cable_count(), test_client_mail_identities_use_the_company_domain(), test_config_file_map_has_no_duplicate_targets() (+4 more)

### Community 2 - "Fix Pipeline & Config Helpers"
Cohesion: 0.10
Nodes (17): apply_fixes(), block_contains(), config_lines(), fix_clients(), fix_core_02_relay(), transform(), fix_core_dhcp(), fix_servers() (+9 more)

### Community 3 - "Configuration Guide Concepts"
Cohesion: 0.06
Nodes (29): Configuration build order, HSRP first-hop gateway redundancy, Site-to-site IPsec VPN, Department isolation ACLs (named extended), NAT/PAT at the Internet edge, OSPF area 0 across all six sites, VLAN plan (10-16, 20), IP Addressing Plan (IPAM) (+21 more)

### Community 4 - "Topology Diagram Entities"
Cohesion: 0.10
Nodes (33): access-accounts-01 (VLAN 12 - ACCOUNTS-PC1,3), access-hr-01 (VLAN 11 - HR-PC1,3), access-sales-01 (VLAN 10 - SALES-PC1,3), BR1-ACCESS (VLAN 13), BR1-PC1 (192.168.13.x - DHCP), BR1-WAN-RTR, BR2-ACCESS (VLAN 14), BR2-PC1 (192.168.14.x - DHCP) (+25 more)

### Community 5 - "CI Workflow Structure"
Cohesion: 0.10
Nodes (28): name, runs-on, steps, name, runs-on, steps, jobs, audit (+20 more)

### Community 6 - "Corporate Portal Design"
Cohesion: 0.19
Nodes (10): Corporate Intranet Portal (assets/web/index.html), How to reach this portal - resolution path, Service Catalogue table on the portal, configs/servers/README.md - Server Service Definitions, Server service definitions for Server0 to Server3, C-01 Sales mail client used the wrong domain, H-04 Web server served the Packet Tracer default page, Centralized DNS - Server1 at 172.10.10.2 (+2 more)

### Community 7 - "Layered Architecture Concepts"
Cohesion: 0.21
Nodes (10): Access layer - dual-homed switches and port hardening, docs/ARCHITECTURE.md - Layered Design, Three-tier campus with routed WAN and PAT edge, Leaf/Core layer - spine-and-leaf, HSRP and SVIs, PortFast and BPDU guard on access ports, Routing design - OSPF default-route origination, Security architecture - ACLs, IPsec, HSRP, port-security, WAN/Distribution layer - HQ-WAN-RTR hub with four IPsec tunnels (+2 more)

### Community 8 - "WAN Design Rationale"
Cohesion: 0.21
Nodes (10): Automation and tooling (pkt_export, audit_lab, check_ipam), README.bn.md - Bengali Translation, 42-device inventory, README.md - Main Project README, Multi-site enterprise WAN architecture, HSRP first-hop redundancy, IPsec site-to-site VPN (AES-256 / SHA-HMAC), NAT/PAT internet edge via 200.1.1.1 (+2 more)

### Community 9 - "CI Pipeline Metadata"
Cohesion: 0.15
Nodes (12): concurrency, cancel-in-progress, group, name, on, pull_request, push, workflow_dispatch (+4 more)

### Community 10 - "Community Files & Templates"
Cohesion: 0.23
Nodes (11): Bug Report Issue Template, Lab Issue Template, Contributor Covenant version 2.1, Contributor Covenant Code of Conduct, CI regenerates and diffs the exported configs, Adding a device or a test, Verification commands - audit_lab, check_ipam, pytest, Commit message format type(scope): summary (+3 more)

### Community 11 - "Hardening Overlays"
Cohesion: 0.24
Nodes (9): Hardening overlays - IPsec, SSH, control plane, syslog/NTP, ACL parity, DHCP failover, configs/hardened/README.md - Hardening Overlays, Advisory findings A-01 to A-06 documented but not applied, Academic demo is not safe for production deployment, Before using this lab anywhere real - checklist, SECURITY.md - Security Policy, Private security advisory reporting, Security scope - educational lab with no real assets (+1 more)

### Community 12 - "Audit Findings & Defects"
Cohesion: 0.20
Nodes (10): Audit method - decrypt .pkt and cross-check parsed XML, C-02 Split-brain DNS on two servers, C-03 Malformed DNS record with a leading space, docs/AUDIT-FINDINGS.md - Defect Record, H-01 Nine Switch and five Router hostnames, H-02 Branch PCs named with 192.186 typo, H-05 FTP and TFTP enabled on every server, H-07 Port-security without maximum or violation action (+2 more)

### Community 13 - "Reference Notes & Discrepancies"
Cohesion: 0.18
Nodes (5): Notes versus lab disagreements, Troubleshooting performed (3 problems), Testing and Verification Plan, The Lab File, Rebuilding the hardened lab

### Community 14 - "Service & Traffic Paths"
Cohesion: 0.25
Nodes (7): IP Plan table on the portal, Service architecture - one DHCP server and one DNS server, Worked traffic paths for web and mail, C-04 DHCP pool could lease SVI/HSRP addresses, H-03 core-02 had no DHCP relay path, Centralized DHCP - core-01 for seven networks, IP addressing plan (IPAM)

### Community 15 - "Changelog & Versioning"
Cohesion: 0.29
Nodes (8): Pull Request Template, CHANGELOG.md - Release History, Keep a Changelog 1.1.0 format, Semantic Versioning 2.0.0, Release 0.1.0 - original student lab, Release 1.0.0 - first production-ready release, configs/README.md - Device Configurations, Running-configs exported directly from lab/main_project.pkt

### Community 17 - "DHCP & DNS Integration"
Cohesion: 0.29
Nodes (5): DHCP to DNS integration, Centralized DHCP pools on core-01, DHCP relay (ip helper-address), DNS-DHCP integration notes, DHCP relay explanation

### Community 18 - "Central Server Services"
Cohesion: 0.29
Nodes (6): Server services configuration and DNS A records, Single authoritative DNS rule, Server VLAN 20 addressing, DNS server configuration notes, Email server (SMTP/POP3) notes, HTTP/HTTPS web server notes

### Community 19 - "Device Inventory & Cabling"
Cohesion: 0.29
Nodes (7): Device inventory, Cabling reference (46 cables), Topology Diagrams, ASCII topology diagram, Layer summary table, Mermaid topology diagram, Topology poster (1920x1080 rendered diagram)

### Community 20 - "NAT/PAT Demo Script"
Cohesion: 0.50
Nodes (5): NAT/PAT plus ISP live demonstration script, NAT/PAT plus ISP live demo script (Bengali), Citations (cisco.com, courseiva.com), Reference Material, Original server-services notes

### Community 23 - "Access Port Hardening"
Cohesion: 0.67
Nodes (3): Access port security (portfast, bpduguard, sticky MAC), Access-layer hardening (portfast, bpduguard, port-security), Port down after device replacement (sticky MAC)

### Community 26 - "Viva & Q&A Content"
Cohesion: 0.67
Nodes (3): Examiner demonstration scripts, Viva and Exam Preparation, One-paragraph project summary

## Knowledge Gaps
- **81 isolated node(s):** `Feature Request Issue Template`, `NAT/PAT internet edge via 200.1.1.1`, `42-device inventory`, `Three-tier campus with routed WAN and PAT edge`, `WAN/Distribution layer - HQ-WAN-RTR hub with four IPsec tunnels` (+76 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 200 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `docs/AUDIT-FINDINGS.md - Defect Record` connect `Audit Findings & Defects` to `Corporate Portal Design`, `Layered Architecture Concepts`, `WAN Design Rationale`, `Community Files & Templates`, `Hardening Overlays`, `Service & Traffic Paths`, `Changelog & Versioning`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `audit()` (e.g. with `.add()` and `.check()`) actually correct?**
  _`audit()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Feature Request Issue Template`, `NAT/PAT internet edge via 200.1.1.1`, `42-device inventory` to the rest of the system?**
  _81 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Lab Tooling & Imports` be split into smaller, more focused modules?**
  _Cohesion score 0.07667900581702802 - nodes in this community are weakly interconnected._
- **Why does `README.md - Main Project README` connect `WAN Design Rationale` to `Corporate Portal Design`, `Layered Architecture Concepts`, `Community Files & Templates`, `Hardening Overlays`, `Audit Findings & Defects`, `Service & Traffic Paths`, `Changelog & Versioning`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Should `Test Suite & Fixtures` be split into smaller, more focused modules?**
  _Cohesion score 0.04336734693877551 - nodes in this community are weakly interconnected._
- **Why does `audit()` connect `Lab Tooling & Imports` to `Audit Report Data Model`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._