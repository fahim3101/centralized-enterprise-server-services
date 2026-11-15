# Device Inventory

Every device in [`lab/main_project.pkt`](../lab/main_project.pkt), with its
platform, role and the configuration file that contains its running-config.

Regenerate this list with:

```bash
python scripts/pkt_export.py lab/main_project.pkt --list
```

---

## Infrastructure — 18 devices

### HQ core layer

| Device | Model | Role | Config |
|---|---|---|---|
| `core-01` | Catalyst 3560-24PS | Primary core — HSRP active, DHCP server for all 7 pools, OSPF area 0, default-route originator | [`configs/core-01.cfg`](../configs/core-01.cfg) |
| `core-02` | Catalyst 3560-24PS | Secondary core — HSRP standby, OSPF peer, DHCP relay to `core-01` | [`configs/core-02.cfg`](../configs/core-02.cfg) |

### HQ leaf layer

| Device | Model | Role | Config |
|---|---|---|---|
| `leaf-01` | Catalyst 3560-24PS | Leaf 1 — trunks VLAN 10-12/20 to both cores, LACP to `leaf-02` | [`configs/leaf-01.cfg`](../configs/leaf-01.cfg) |
| `leaf-02` | Catalyst 3560-24PS | Leaf 2 — trunks VLAN 10-12/20 to both cores, LACP to `leaf-01` | [`configs/leaf-02.cfg`](../configs/leaf-02.cfg) |

### HQ access layer

| Device | Model | Role | Config |
|---|---|---|---|
| `access-sales-01` | Catalyst 3560-24PS | Access switch for VLAN 10 (Sales), 3 workstations | [`configs/access-sales.cfg`](../configs/access-sales.cfg) |
| `access-hr-01` | Catalyst 3560-24PS | Access switch for VLAN 11 (HR), 3 workstations | [`configs/access-hr.cfg`](../configs/access-hr.cfg) |
| `access-accounts-01` | Catalyst 3560-24PS | Access switch for VLAN 12 (Accounts), 3 workstations | [`configs/access-accounts.cfg`](../configs/access-accounts.cfg) |

### WAN and Internet edge

| Device | Model | Role | Config |
|---|---|---|---|
| `HQ-WAN-RTR` | Cisco 2811 | WAN hub — OSPF area 0, four IPsec site-to-site tunnels | [`configs/hq-wan-router.cfg`](../configs/hq-wan-router.cfg) |
| `EDGE-RTR` | Cisco 2911 | Internet edge — NAT/PAT to the ISP | [`configs/edge-router.cfg`](../configs/edge-router.cfg) |
| `ISP` | Cisco 2911 | Simulated upstream ISP | [`configs/isp-router.cfg`](../configs/isp-router.cfg) |

### Branches — 8 devices

| Device | Model | Role | LAN | WAN | Config |
|---|---|---|---|---|---|
| `BR1-WAN-RTR` | Cisco 2811 | Branch 1 IPsec peer | `1.1.1.1/24` | `5.1.1.2/24` | [`configs/branch1-router.cfg`](../configs/branch1-router.cfg) |
| `BR1-ACCESS` | Catalyst 3560-24PS | Branch 1 access + gateway, VLAN 13 | `192.168.13.254` | `1.1.1.2/24` | [`configs/branch1-access.cfg`](../configs/branch1-access.cfg) |
| `BR2-WAN-RTR` | Cisco 2811 | Branch 2 IPsec peer | `2.1.1.1/24` | `6.1.1.2/24` | [`configs/branch2-router.cfg`](../configs/branch2-router.cfg) |
| `BR2-ACCESS` | Catalyst 3560-24PS | Branch 2 access + gateway, VLAN 14 | `192.168.14.254` | `2.1.1.2/24` | [`configs/branch2-access.cfg`](../configs/branch2-access.cfg) |
| `BR3-WAN-RTR` | Cisco 2811 | Branch 3 IPsec peer | `3.1.1.1/24` | `7.1.1.2/24` | [`configs/branch3-router.cfg`](../configs/branch3-router.cfg) |
| `BR3-ACCESS` | Catalyst 3560-24PS | Branch 3 access + gateway, VLAN 15 | `192.168.15.254` | `3.1.1.2/24` | [`configs/branch3-access.cfg`](../configs/branch3-access.cfg) |
| `BR4-WAN-RTR` | Cisco 2811 | Branch 4 IPsec peer | `4.1.1.1/24` | `8.1.1.2/24` | [`configs/branch4-router.cfg`](../configs/branch4-router.cfg) |
| `BR4-ACCESS` | Catalyst 3560-24PS | Branch 4 access + gateway, VLAN 16 | `192.168.16.254` | `4.1.1.2/24` | [`configs/branch4-access.cfg`](../configs/branch4-access.cfg) |

---

## Servers — 4 devices

| Device | IP | Services | Purpose |
|---|---|---|---|
| `Server0` | `172.10.10.1` | HTTP, HTTPS | Corporate intranet portal (`www.company.com`) |
| `Server1` | `172.10.10.2` | DNS | Authoritative resolver for the enterprise |
| `Server2` | `172.10.10.3` | SMTP, POP3 | Corporate mail (`company.com`) |
| `Server3` | `203.0.113.10` | HTTP (simulated) | The Internet server used for the PAT demo |

Service definitions: [`configs/servers/`](../configs/servers/)

---

## Endpoints — 17 devices

| Device | VLAN | Network | Addressing | Notes |
|---|---|---|---|---|
| `SALES-PC1` | 10 | `192.168.10.0/24` | DHCP | e-mail client `sales@company.com` |
| `SALES-PC2` | 10 | `192.168.10.0/24` | DHCP | |
| `SALES-PC3` | 10 | `192.168.10.0/24` | DHCP | |
| `HR-PC1` | 11 | `192.168.11.0/24` | DHCP | e-mail client `hr@company.com` |
| `HR-PC2` | 11 | `192.168.11.0/24` | DHCP | |
| `HR-PC3` | 11 | `192.168.11.0/24` | DHCP | |
| `ACCOUNTS-PC1` | 12 | `192.168.12.0/24` | DHCP | |
| `ACCOUNTS-PC2` | 12 | `192.168.12.0/24` | DHCP | |
| `ACCOUNTS-PC3` | 12 | `192.168.12.0/24` | DHCP | |
| `BR1-PC1` | 13 | `192.168.13.0/24` | DHCP (relay) | |
| `BR1-PC2` | 13 | `192.168.13.0/24` | DHCP (relay) | |
| `BR2-PC1` | 14 | `192.168.14.0/24` | DHCP (relay) | |
| `BR2-PC2` | 14 | `192.168.14.0/24` | DHCP (relay) | |
| `BR3-PC1` | 15 | `192.168.15.0/24` | DHCP (relay) | |
| `BR3-PC2` | 15 | `192.168.15.0/24` | DHCP (relay) | |
| `BR4-PC1` | 16 | `192.168.16.0/24` | DHCP (relay) | |
| `BR4-PC2` | 16 | `192.168.16.0/24` | DHCP (relay) | |

---

## Name mapping — original → production

The original lab used IP addresses and generic names as device identifiers.
The table below is the migration path, for anyone comparing this repository
against the original build.

| Original display name | Original hostname | New display name | New hostname |
|---|---|---|---|
| `Multilayer Switch0` | `Switch` | `access-sales-01` | `access-sales-01` |
| `Multilayer Switch1` | `Switch` | `access-hr-01` | `access-hr-01` |
| `Multilayer Switch2` | `Switch` | `access-accounts-01` | `access-accounts-01` |
| `central router` | `Router` | `HQ-WAN-RTR` | `HQ-WAN-RTR` |
| `1.1.1.1` | `Router` | `BR1-WAN-RTR` | `BR1-WAN-RTR` |
| `1.1.1.2` | `Switch` | `BR1-ACCESS` | `BR1-ACCESS` |
| `2.1.1.1` | `Router` | `BR2-WAN-RTR` | `BR2-WAN-RTR` |
| `2.1.1.2` | `Switch` | `BR2-ACCESS` | `BR2-ACCESS` |
| `3.1.1.1` | `Router` | `BR3-WAN-RTR` | `BR3-WAN-RTR` |
| `3.1.1.2` | `Switch` | `BR3-ACCESS` | `BR3-ACCESS` |
| `4.1.1.1` | `Router` | `BR4-WAN-RTR` | `BR4-WAN-RTR` |
| `4.1.1.2` | `Switch` | `BR4-ACCESS` | `BR4-ACCESS` |
| `leaf-02` | `leafSw02` | `leaf-02` | `leaf-02` |
| `192.168.10.1` | — | `SALES-PC1` | — |
| `192.168.10.2` | — | `SALES-PC2` | — |
| `192.168.10.3` | — | `SALES-PC3` | — |
| `192.168.11.1` | — | `HR-PC1` | — |
| `192.168.11.2` | — | `HR-PC2` | — |
| `192.168.11.3` | — | `HR-PC3` | — |
| `192.168.12.1` | — | `ACCOUNTS-PC1` | — |
| `192.168.12.2` | — | `ACCOUNTS-PC2` | — |
| `192.168.12.3` | — | `ACCOUNTS-PC3` | — |
| `192.186.13.1` | — | `BR1-PC1` | — |
| `192.186.13.2` | — | `BR1-PC2` | — |
| `192.186.14.1` | — | `BR2-PC1` | — |
| `192.186.14.2` | — | `BR2-PC2` | — |
| `192.186.15.1` | — | `BR3-PC1` | — |
| `192.186.15.2` | — | `BR3-PC2` | — |
| `192.186.16.1` | — | `BR4-PC1` | — |
| `192.186.16.2` | — | `BR4-PC2` | — |

> **Note on the `192.186.x.x` names:** the branch workstations were originally
> labelled with `192.186` — a typo for `192.168`. `192.186` is not even a
> private range. The devices were always using DHCP from the correct
> `192.168.x.x` pools, so only the label was wrong.

---

## Cabling reference

All 46 cables, generated with `--links`:

| From | Port | To | Port |
|---|---|---|---|
| `core-01` | Gi0/1 | `HQ-WAN-RTR` | Fa0/0 |
| `core-01` | Gi0/2 | `leaf-02` | Fa0/7 |
| `core-01` | Fa0/3 | `EDGE-RTR` | Gi0/0 |
| `core-01` | Fa0/4 | `Server1` | Fa0/0 |
| `core-01` | Fa0/5 | `Server0` | Fa0/0 |
| `core-01` | Fa0/6 | `Server2` | Fa0/0 |
| `core-02` | Gi0/1 | `HQ-WAN-RTR` | Fa0/1 |
| `core-02` | Fa0/1 | `leaf-01` | Fa0/8 |
| `core-02` | Fa0/2 | `leaf-02` | Fa0/8 |
| `leaf-01` | Fa0/1 | `access-sales-01` | Gi0/1 |
| `leaf-01` | Fa0/2 | `access-hr-01` | Gi0/1 |
| `leaf-01` | Fa0/3 | `access-accounts-01` | Gi0/1 |
| `leaf-01` | Fa0/4 | `leaf-02` | Fa0/4 |
| `leaf-01` | Fa0/5 | `leaf-02` | Fa0/5 |
| `leaf-01` | Fa0/6 | `leaf-02` | Fa0/6 |
| `leaf-01` | Fa0/7 | `core-01` | Fa0/1 |
| `leaf-01` | Fa0/8 | `core-02` | Fa0/1 |
| `leaf-02` | Fa0/1 | `access-sales-01` | Gi0/2 |
| `leaf-02` | Fa0/2 | `access-hr-01` | Gi0/2 |
| `leaf-02` | Fa0/3 | `access-accounts-01` | Gi0/2 |
| `leaf-02` | Fa0/4 | `leaf-01` | Fa0/4 |
| `leaf-02` | Fa0/5 | `leaf-01` | Fa0/5 |
| `leaf-02` | Fa0/6 | `leaf-01` | Fa0/6 |
| `leaf-02` | Fa0/7 | `core-01` | Fa0/2 |
| `leaf-02` | Fa0/8 | `core-02` | Fa0/2 |
| `access-sales-01` | Fa0/1–0/3 | `SALES-PC1..3` | Fa0/0 |
| `access-hr-01` | Fa0/1–0/3 | `HR-PC1..3` | Fa0/0 |
| `access-accounts-01` | Fa0/1–0/3 | `ACCOUNTS-PC1..3` | Fa0/0 |
| `HQ-WAN-RTR` | S1/0 | `BR1-WAN-RTR` | S1/0 |
| `HQ-WAN-RTR` | S1/1 | `BR2-WAN-RTR` | S1/0 |
| `HQ-WAN-RTR` | S1/2 | `BR3-WAN-RTR` | S1/0 |
| `HQ-WAN-RTR` | S1/3 | `BR4-WAN-RTR` | S1/0 |
| `BR1-WAN-RTR` | Fa0/0 | `BR1-ACCESS` | Gi0/1 |
| `BR2-WAN-RTR` | Fa0/0 | `BR2-ACCESS` | Gi0/1 |
| `BR3-WAN-RTR` | Fa0/0 | `BR3-ACCESS` | Gi0/1 |
| `BR4-WAN-RTR` | Fa0/0 | `BR4-ACCESS` | Gi0/1 |
| `BR1-ACCESS` | Fa0/2–0/3 | `BR1-PC1..2` | Fa0/0 |
| `BR2-ACCESS` | Fa0/2–0/3 | `BR2-PC1..2` | Fa0/0 |
| `BR3-ACCESS` | Fa0/2–0/3 | `BR3-PC1..2` | Fa0/0 |
| `BR4-ACCESS` | Fa0/2 | `BR4-PC1` | Fa0/0 |
| `EDGE-RTR` | Gi0/1 | `ISP` | Gi0/0 |
| `ISP` | Gi0/1 | `Server3` | Fa0/0 |

---

## Device naming convention

| Pattern | Meaning | Example |
|---|---|---|
| `core-NN` | HQ core layer | `core-01` |
| `leaf-NN` | HQ leaf layer | `leaf-02` |
| `access-<dept>` | HQ department access switch | `access-hr-01` |
| `BRn-WAN-RTR` | Branch *n* WAN router | `BR3-WAN-RTR` |
| `BRn-ACCESS` | Branch *n* access switch | `BR3-ACCESS` |
| `EDGE-RTR` | Internet edge router | `EDGE-RTR` |
| `HQ-WAN-RTR` | HQ WAN router | `HQ-WAN-RTR` |
| `<DEPT>-PCn` | Workstation | `SALES-PC1` |
| `ServerN` | Packet Tracer server object | `Server0` |

The IOS hostname is always identical to the display name, so the CLI prompt
uniquely identifies the device.
