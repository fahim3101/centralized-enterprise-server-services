# Topology Diagrams

## Interactive diagram

Rendered automatically by GitHub from [`topology.mmd`](topology.mmd):

```mermaid
graph LR
    subgraph BR1["Branch 1 — Site 1"]
        direction TB
        B1PC["BR1-PC1<br/>192.168.13.x<br/>DHCP"] --> B1SW["BR1-ACCESS<br/>VLAN 13<br/>192.168.13.254"]
        B1SW --> B1R["BR1-WAN-RTR<br/>1.1.1.1"]
    end

    subgraph BR2["Branch 2 — Site 2"]
        direction TB
        B2PC["BR2-PC1<br/>192.168.14.x<br/>DHCP"] --> B2SW["BR2-ACCESS<br/>VLAN 14<br/>192.168.14.254"]
        B2SW --> B2R["BR2-WAN-RTR<br/>2.1.1.1"]
    end

    subgraph BR3["Branch 3 — Site 3"]
        direction TB
        B3PC["BR3-PC1<br/>192.168.15.x<br/>DHCP"] --> B3SW["BR3-ACCESS<br/>VLAN 15<br/>192.168.15.254"]
        B3SW --> B3R["BR3-WAN-RTR<br/>3.1.1.1"]
    end

    subgraph BR4["Branch 4 — Site 4"]
        direction TB
        B4PC["BR4-PC1<br/>192.168.16.x<br/>DHCP"] --> B4SW["BR4-ACCESS<br/>VLAN 16<br/>192.168.16.254"]
        B4SW --> B4R["BR4-WAN-RTR<br/>4.1.1.1"]
    end

    subgraph HQ["HEADQUARTERS"]
        direction TB
        subgraph ACC["Access Layer"]
            direction LR
            AS["access-sales-01<br/>VLAN 10"] --- ASP["SALES-PC1..3"]
            AH["access-hr-01<br/>VLAN 11"] --- AHP["HR-PC1..3"]
            AA["access-accounts-01<br/>VLAN 12"] --- AAP["ACCOUNTS-PC1..3"]
        end
        LF["leaf-01 / leaf-02<br/>LACP interconnect<br/>trunks VLAN 10-12,20"]
        CR["core-01 / core-02<br/>HSRP · OSPF area 0<br/>DHCP server"]
        LF --- ACC
        LF --- CR
        subgraph SRV["Server VLAN 20 — 172.10.10.0/24"]
            direction LR
            S0["Server0<br/>172.10.10.1<br/>HTTP · HTTPS<br/>www.company.com"]
            S1["Server1<br/>172.10.10.2<br/>DNS<br/>homelab.local"]
            S2["Server2<br/>172.10.10.3<br/>SMTP · POP3<br/>mail.company.com"]
        end
        CR --- SRV
        WR["HQ-WAN-RTR<br/>OSPF + IPsec hub"]
        CR --- WR
    end

    B1R <==>|"Serial 5.1.1.0/24<br/>IPsec VPN"| WR
    B2R <==>|"Serial 6.1.1.0/24<br/>IPsec VPN"| WR
    B3R <==>|"Serial 7.1.1.0/24<br/>IPsec VPN"| WR
    B4R <==>|"Serial 8.1.1.0/24<br/>IPsec VPN"| WR

    CR -->|"10.3.3.0/24"| EDGE["EDGE-RTR<br/>10.3.3.2 / 200.1.1.1<br/>NAT · PAT"]
    EDGE -->|"200.1.1.0/30"| ISP["ISP<br/>200.1.1.2"]
    ISP -->|"203.0.113.0/24"| INT["Server3<br/>203.0.113.10<br/>Internet Server"]

    classDef server fill:#0b3d5c,stroke:#4fc3f7,color:#e8f6ff
    classDef core fill:#124a2c,stroke:#66bb6a,color:#e8ffe8
    classDef branch fill:#4a2d12,stroke:#ffa726,color:#fff3e0
    classDef edge fill:#4a124a,stroke:#ce93d8,color:#f3e5f5
    class S0,S1,S2,INT server
    class CR,LF core
    class B1R,B1SW,B2R,B2SW,B3R,B3SW,B4R,B4SW branch
    class EDGE,ISP edge
```

---

## ASCII diagram

For terminals and printed documentation:

```
                          ┌──────────────────────────────────┐
                          │        SIMULATED INTERNET         │
                          │   Server3   203.0.113.10           │
                          └────────────────┬─────────────────┘
                                           │ 203.0.113.0/24
                          ┌────────────────┴─────────────────┐
                          │            ISP  200.1.1.2        │
                          └────────────────┬─────────────────┘
                                           │ 200.1.1.0/30
                          ┌────────────────┴─────────────────┐
                          │   EDGE-RTR                       │
                          │   Gi0/0 10.3.3.2   (NAT inside)  │
                          │   Gi0/1 200.1.1.1  (NAT outside) │
                          │   PAT · overload                  │
                          └────────────────┬─────────────────┘
                                           │ 10.3.3.0/24
       ┌────────────────────────────────────┴─────────────────────────────────┐
       │                                                                      │
 ┌─────┴──────┐                                                  ┌───────────┴────────┐
 │  core-01   │◄──── 10.1.1.0/24 ────►┌──────────────┐          │      core-02       │
 │ HSRP ACTIVE│                         │  HQ-WAN-RTR  │          │  HSRP STANDBY      │
 │ DHCP SERVER│◄──── 10.2.2.0/24 ────►│ OSPF + IPsec │          │  DHCP relay        │
 │ OSPF area 0│                         │   4 tunnels  │          └───────────┬────────┘
 └─────┬──────┘                         └───┬───┬───┬───┬──────────────────────┘
       │                                     │   │   │   │
       │            ┌────────────────────────┘   │   │   └──────────┐
       │            │                            │   │              │
       │      Serial 5.1.1.0/24                 │   │              │
       │            │                     Serial 6.1.1.0/24          │
       │            ▼                            │   │              │
       │  ┌──────────────────┐                   │   │              │
       │  │  BR1-WAN-RTR     │◄──────────────────┘   │              │
       │  │  1.1.1.1/24      │                       │              │
       │  └────────┬─────────┘◄──────────────────────┘              │
       │           │ Fa0/0                                        │
       │           ▼                                              │
       │  ┌──────────────────┐  Serial 7.1.1.0/24                  │
       │  │  BR2-WAN-RTR     │◄──────────────────────┐              │
       │  │  2.1.1.1/24      │                       │              │
       │  └────────┬─────────┘                       │              │
       │           │                                 │              │
       │  ┌────────▼─────────┐  Serial 8.1.1.0/24    │              │
       │  │  BR3-WAN-RTR     │◄──────────────────────┤              │
       │  │  3.1.1.1/24      │                       │              │
       │  └──────────────────┘                       │              │
       │                                             │              │
       │  ┌──────────────────┐                       │              │
       │  │  BR4-WAN-RTR     │◄──────────────────────┘              │
       │  │  4.1.1.1/24      │                                      │
       │  └──────────────────┘                                      │
       │                                                              │
       │   ┌──────────────────────────────────────────┐             │
       │   │            LEAF LAYER                    │             │
       │   │  leaf-01  ◄──── LACP Po1 ────►  leaf-02   │             │
       │   └───┬──────────────┬──────────────────┬────┘             │
       │       │              │                  │                  │
       ▼       ▼              ▼                  ▼                  │
 ┌─────────┐ ┌─────────┐ ┌─────────┐    ┌──────────────┐            │
 │  VLAN10 │ │  VLAN11 │ │  VLAN12 │    │  SERVER VLAN │            │
 │  SALES  │ │   HR    │ │ACCOUNTS │    │      20      │            │
 │         │ │         │ │         │    │172.10.10.0/24│            │
 │ access- │ │ access- │ │ access- │    │              │            │
 │ sales-01│ │ hr-01   │ │acc-01   │    │ Server0 .1   │            │
 └─────────┘ └─────────┘ └─────────┘    │ Server1 .2   │            │
                                        │ Server2 .3   │            │
                                        └──────────────┘            │
       └────────────────────────────────────────────────────────────┘
```

---

## Layer summary

| Layer | Devices | Key technology |
|---|---|---|
| Access | `access-sales-01`, `access-hr-01`, `access-accounts-01`, `BRn-ACCESS` | VLANs, port-security, portfast/BPDU guard |
| Leaf | `leaf-01`, `leaf-02` | LACP port-channel, layer-3 trunks |
| Core | `core-01`, `core-02` | HSRP, DHCP, OSPF area 0, extended ACLs |
| Distribution / WAN | `HQ-WAN-RTR`, `BRn-WAN-RTR` | OSPF, IPsec site-to-site VPN |
| Edge | `EDGE-RTR`, `ISP` | NAT/PAT, static default routes |
| Services | `Server0`, `Server1`, `Server2` | HTTP/HTTPS, DNS, SMTP/POP3 |
| Internet | `Server3` | Simulated Internet host |

---

## Regenerating the cabling table

```bash
python scripts/pkt_export.py lab/main_project.pkt --links
```

The output is the authoritative list of all 46 cables and is mirrored in
[`../DEVICE-INVENTORY.md`](../DEVICE-INVENTORY.md).
