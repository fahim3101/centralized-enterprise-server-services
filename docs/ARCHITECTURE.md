# Architecture

A three-tier enterprise campus network with a routed WAN to four remote
branches and a NAT/PAT Internet edge.

```
                      ┌───────────────────────────┐
                      │        INTERNET           │
                      │  Server3  203.0.113.10    │
                      └─────────────┬─────────────┘
                                    │ 203.0.113.0/24
                      ┌─────────────┴─────────────┐
                      │           ISP             │  200.1.1.2/30
                      └─────────────┬─────────────┘
                                    │
                      ┌─────────────┴─────────────┐
                      │         EDGE-RTR         │  NAT / PAT
                      │  in 10.3.3.2  out 200.1.1.1│
                      └─────────────┬─────────────┘
                                    │ 10.3.3.0/24
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
┌───────┴────────┐                                   ┌────────┴─────────┐
│     core-01     │                                   │     core-02      │
│ HSRP active     │◄──────── 10.1.1.0 / 10.2.2.0 ───►│ HSRP standby     │
│ DHCP server     │                                   │ OSPF             │
│ OSPF area 0     │                                   └────────┬─────────┘
│ default-info    │                                            │
└───────┬────────┘                                   ┌────────┴─────────┐
        │                                            │     leaf-01     │
        │                                            │     leaf-02     │
        │                                            └────────┬─────────┘
        │                                                     │
        │        ┌────────────────────────────────────────────┴────┐
        │        │            HQ ACCESS LAYER                     │
        │        │  access-sales-01 (V10)  access-hr-01 (V11)     │
        │        │  access-accounts-01 (V12)                      │
        │        └─────────────────────────────────────────────────┘
        │
┌───────┴────────┐
│  SERVER VLAN 20│
│  172.10.10.0/24│
│  Server0 Web   │  www.company.com   172.10.10.1
│  Server1 DNS   │  homelab.local     172.10.10.2
│  Server2 Mail  │  mail.company.com  172.10.10.3
└────────────────┘
```

---

## Layer 1 — Access

| Device | VLANs served | Uplinks |
|---|---|---|
| `access-sales-01` | 10 (Sales) | `leaf-01` Gi0/1, `leaf-02` Gi0/1 |
| `access-hr-01` | 11 (HR) | `leaf-01` Gi0/2, `leaf-02` Gi0/2 |
| `access-accounts-01` | 12 (Accounts) | `leaf-01` Gi0/3, `leaf-02` Gi0/3 |

Each access switch is **dual-homed**: it trunks to both leaf switches, so a
single leaf failure never isolates a department. Every host-facing port is
hardened with:

```
 switchport mode access
 switchport access vlan <vlan>
 spanning-tree portfast
 spanning-tree bpduguard enable
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky <mac>
```

`portfast` removes the 30-second STP convergence delay from an edge port;
`bpduguard` shuts the port if a switch is ever plugged into it; port-security
with a sticky MAC pins exactly one host per port.

---

## Layer 2 — Leaf / Core

### Leaf layer — `leaf-01`, `leaf-02`

Two `Catalyst 3560-24PS` in layer-3 mode give a classic **spine-and-leaf**
shape. Each leaf:

* trunks VLANs 10-12 and 20 to both cores
* trunks to the other leaf over an LACP port-channel (`Port-channel1`, three
  physical links, `channel-group 1 mode active`)
* aggregates its uplinks with LACP so the core uplinks are not a single
  point of failure

### Core layer — `core-01`, `core-02`

Both cores run `ip routing` and terminate the SVIs for VLANs 10, 11, 12 and
20.

| | `core-01` | `core-02` |
|---|---|---|
| SVI address | `x.252` | `x.253` |
| HSRP priority | `110` | default (100) |
| Preempt | yes | yes |
| Active for | all four VLANs | standby |
| DHCP | all 7 pools | relay to `10.1.1.1` |
| Default route | static → `10.3.3.2` | OSPF from `core-01` |

`core-01` wins the HSRP election on priority and preempts, so it is the
active gateway and the DHCP server. `core-02` stays ready to take over; its
SVIs and `ip helper-address 10.1.1.1` guarantee that a client on a VLAN
where `core-02` has become active can still obtain a DHCP lease.

---

## Layer 3 — WAN / Distribution

`HQ-WAN-RTR` (Cisco 2811) is the single hub for the four branch sites.

| Interface | Peer | Addressing | Role |
|---|---|---|---|
| Fa0/0 | `core-01` Gi0/1 | `10.1.1.2/24` | OSPF area 0 |
| Fa0/1 | `core-02` Gi0/1 | `10.2.2.1/24` | OSPF area 0 |
| S1/0 | `BR1-WAN-RTR` S1/0 | `5.1.1.0/24` | IPsec, `crypto map VPN-MAP` |
| S1/1 | `BR2-WAN-RTR` S1/0 | `6.1.1.0/24` | IPsec, `crypto map VPN-B2` |
| S1/2 | `BR3-WAN-RTR` S1/0 | `7.1.1.0/24` | IPsec, `crypto map VPN-B3` |
| S1/3 | `BR4-WAN-RTR` S1/0 | `8.1.1.0/24` | IPsec, `crypto map VPN-B4` |

Each tunnel has its own crypto map, its own peer and its own interesting-traffic
ACL, so a branch can only ever reach the network it is supposed to reach:

```
HQ-WAN-RTR                            BR1-WAN-RTR
access-list 110 permit ip             access-list 110 permit ip
  192.168.10.0 0.0.0.255               192.168.13.0 0.0.0.255
  192.168.13.0 0.0.0.255               192.168.10.0 0.0.0.255
```

The four branch pairs are `10 ↔ 13`, `10 ↔ 14`, `10 ↔ 15` and `10 ↔ 16`:
Sales-to-branch traffic is tunnelled, branch-to-branch traffic is not.

---

## Routing design

**OSPF area 0** spans HQ and all four branches. It is a flat single-area
design on purpose: the WAN is small, the topology is a star, and a flat area
keeps the routing table and the convergence behaviour easy to explain.

`core-01` originates the default route into OSPF:

```
router ospf 1
 default-information originate
 ip route 0.0.0.0 0.0.0.0 10.3.3.2
```

Every branch therefore learns `0.0.0.0/0` from the HQ core and never needs a
direct ISP connection. The Internet path is always:

```
branch PC → branch switch → branch router → (IPsec) → HQ-WAN-RTR
          → core-01 → EDGE-RTR → PAT → ISP → Internet
```

`EDGE-RTR` does not run OSPF. It reaches the internal networks with two
summary static routes, which is appropriate for an edge device whose only job
is translation:

```
ip route 192.168.0.0 255.255.0.0 10.3.3.1
ip route 172.10.10.0 255.255.255.0 10.3.3.1
```

---

## Service architecture

```
             ┌──────────────── core-01 ────────────────┐
             │  ip dhcp pool SALES / HR / ACCOUNTS /   │
             │              BRANCH1..4                  │
             │  every pool carries:                    │
             │    default-router <vlan>.254             │
             │    dns-server    172.10.10.2             │
             └───────────────────┬─────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
   HQ user VLANs          branch VLANs             branch VLANs
   (relay not needed)   (relay via helper-address  (relay via helper-address
                          10.1.1.1 on BRn-ACCESS)     10.1.1.1 on BRn-ACCESS)
```

One DHCP server serves seven networks and one DNS server serves every site.
That is the "centralized" part of the project title: a client in Branch 4
resolves `www.company.com` through the very same DNS server that a Sales
workstation in the HQ uses, and it learns that address automatically from the
same DHCP service.

### Traffic path — a Sales user opening the company website

```
SALES-PC1
  │  1. DHCP already gave it 192.168.10.x, gw 192.168.10.254, DNS 172.10.10.2
  │  2. DNS query  www.company.com  ──────────────► Server1 (172.10.10.2)
  │                                          reply: 172.10.10.1
  │  3. HTTP GET  www.company.com ──► OSPF lookup ──► core-01
  │                                       └─► EDGE-RTR?  no - 172.10.10.0/24
  │                                            is an OSPF network
  │  4. TCP 80 ──► Server0 (172.10.10.1) ──► corporate portal
```

### Traffic path — a Branch 4 user sending mail

```
BR4-PC1 (192.168.16.x)
  │  1. DHCP relay  BR4-ACCESS → 10.1.1.1 (core-01)
  │  2. DNS        www/mail.company.com ──► Server1 (172.10.10.2)
  │  3. SMTP       mail.company.com = 172.10.10.3
  │  4. OSPF       172.10.10.0/24 via HQ-WAN-RTR (5.1.1.1 → 8.1.1.1)
  │  5. IPsec      encrypted over the serial link to HQ
  │  6. Server2    stores the message
  │  7. POP3       HR-PC1 retrieves it with hr@company.com / hr123
```

---

## Security architecture

| Control | Where | What it does |
|---|---|---|
| Extended ACLs | `core-01` SVIs | Isolate Sales / HR / Accounts from each other |
| DHCP relay | `BRn-ACCESS` | Keeps the DHCP server in one place |
| IPsec (AES/SHA-HMAC) | WAN serial links | Encrypts HQ ↔ branch traffic |
| HSRP | both cores | First-hop redundancy for every VLAN |
| Port-security + BPDU guard | all access ports | Prevents rogue switches and MAC flooding |
| `enable secret` + `service password-encryption` | all devices | Basic credential protection |
| PAT | `EDGE-RTR` | Hides the internal address space from the Internet |
| Trunk VLAN scoping | both cores | Only VLANs 10-12 and 20 cross the trunks |

See [`SECURITY.md`](SECURITY.md) for the full security model and the
recommended hardening steps that are **not** applied by default.

---

## Design decisions and trade-offs

**Why a single OSPF area?**
The WAN is a five-node star. A flat area means one `show ip ospf database`
covers everything, convergence is fast, and there is no area-boundary
summarisation to explain. With more than ~30 routers, area design would
become worthwhile.

**Why DHCP relay instead of a DHCP server per branch?**
Centralisation is the point of the project. It also means the DNS address is
defined once and can never drift between sites. The trade-off is a single
point of failure at `core-01`, mitigated by the relay on `core-02`.

**Why static routes on `EDGE-RTR`?**
An edge router should have the simplest possible control plane. Two summary
routes are easier to audit than an OSPF adjacency, and they remove the
possibility of a routing loop between the OSPF domain and the NAT device.

**Why LACP between the two leaf switches?**
The leaf pair already has two independent paths to two independent cores.
The port-channel between them aggregates bandwidth for east-west traffic and
gives L2 redundancy when a single link fails.

**Known trade-off — a Layer-2 loop between the leaves.**
Both leaf switches trunk to both access switches *and* to each other, which
creates a Layer-2 loop. Spanning Tree (PVST) blocks one of the redundant
paths automatically. In a production build the leaf-to-leaf link would either
be removed or the access switches would be single-homed per VLAN with
link-aggregation to one leaf. This is documented in
[`AUDIT-FINDINGS.md`](AUDIT-FINDINGS.md) as an accepted trade-off for the
teaching topology.
