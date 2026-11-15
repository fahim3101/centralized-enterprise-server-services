# IP Addressing Plan (IPAM)

Every IPv4 address used in the lab, with its purpose and the device that owns
it. Generated from the live configuration of
[`lab/main_project.pkt`](../lab/main_project.pkt) and validated on every CI run
by [`scripts/check_ipam.py`](../scripts/check_ipam.py).

**Mask convention:** every user, server and WAN network uses
`255.255.255.0` (`/24`) except the ISP link, which uses `255.255.255.252`
(`/30`).

---

## 1. User networks (DHCP served by `core-01`)

| VLAN | Name | Network | HSRP gateway | SVI `core-01` | SVI `core-02` | DHCP range | DNS |
|---:|---|---|---|---|---|---|---|
| 10 | Sales | `192.168.10.0/24` | `192.168.10.254` | `.252` | `.253` | `.21 – .251` | `172.10.10.2` |
| 11 | HR | `192.168.11.0/24` | `192.168.11.254` | `.252` | `.253` | `.21 – .251` | `172.10.10.2` |
| 12 | Accounts | `192.168.12.0/24` | `192.168.12.254` | `.252` | `.253` | `.21 – .251` | `172.10.10.2` |
| 13 | Branch 1 | `192.168.13.0/24` | `192.168.13.254` | — | — | `.21 – .251` | `172.10.10.2` |
| 14 | Branch 2 | `192.168.14.0/24` | `192.168.14.254` | — | — | `.21 – .251` | `172.10.10.2` |
| 15 | Branch 3 | `192.168.15.0/24` | `192.168.15.254` | — | — | `.21 – .251` | `172.10.10.2` |
| 16 | Branch 4 | `192.168.16.0/24` | `192.168.16.254` | — | — | `.21 – .251` | `172.10.10.2` |

**Reserved inside every user network**

| Address | Owner | Reason |
|---|---|---|
| `.1` – `.20` | — | excluded from DHCP, reserved for static/infra hosts |
| `.252` | `core-01` SVI | primary core gateway address |
| `.253` | `core-02` SVI | secondary core gateway address |
| `.254` | HSRP | virtual default gateway advertised to clients |

> The branch networks use the **same** `.21 – .251` range convention even
> though their gateway lives on the branch switch (`192.168.1x.254`), not on a
> core SVI.

---

## 2. Central services — Server VLAN 20

| Address | Device | Service | Hostname(s) |
|---|---|---|---|
| `172.10.10.1` | `Server0` | Web server (HTTP + HTTPS) | `www.company.com` |
| `172.10.10.2` | `Server1` | Authoritative DNS | `homelab.local` |
| `172.10.10.3` | `Server2` | Mail server (SMTP + POP3) | `mail.company.com` |

| Address | Owner | Reason |
|---|---|---|
| `172.10.10.252` | `core-01` SVI | primary server-VLAN gateway |
| `172.10.10.253` | `core-02` SVI | secondary server-VLAN gateway |
| `172.10.10.254` | HSRP | virtual default gateway for the server VLAN |

All three servers are **statically addressed** — the server VLAN has no DHCP
scope, so a DHCP lease can never collide with them.

---

## 3. Inter-site and infrastructure links

| Link | Network | End A | End B |
|---|---|---|---|
| `core-01` ↔ `HQ-WAN-RTR` | `10.1.1.0/24` | `core-01` Gi0/1 = `10.1.1.1` | `HQ-WAN-RTR` Fa0/0 = `10.1.1.2` |
| `core-02` ↔ `HQ-WAN-RTR` | `10.2.2.0/24` | `core-02` Gi0/1 = `10.2.2.2` | `HQ-WAN-RTR` Fa0/1 = `10.2.2.1` |
| `core-01` ↔ `EDGE-RTR` | `10.3.3.0/24` | `core-01` Fa0/3 = `10.3.3.1` | `EDGE-RTR` Gi0/0 = `10.3.3.2` |
| `HQ-WAN-RTR` ↔ `BR1-WAN-RTR` | `5.1.1.0/24` | `HQ-WAN-RTR` S1/0 = `5.1.1.1` | `BR1-WAN-RTR` S1/0 = `5.1.1.2` |
| `HQ-WAN-RTR` ↔ `BR2-WAN-RTR` | `6.1.1.0/24` | `HQ-WAN-RTR` S1/1 = `6.1.1.1` | `BR2-WAN-RTR` S1/0 = `6.1.1.2` |
| `HQ-WAN-RTR` ↔ `BR3-WAN-RTR` | `7.1.1.0/24` | `HQ-WAN-RTR` S1/2 = `7.1.1.1` | `BR3-WAN-RTR` S1/0 = `7.1.1.2` |
| `HQ-WAN-RTR` ↔ `BR4-WAN-RTR` | `8.1.1.0/24` | `HQ-WAN-RTR` S1/3 = `8.1.1.1` | `BR4-WAN-RTR` S1/0 = `8.1.1.2` |
| `BR1-WAN-RTR` ↔ `BR1-ACCESS` | `1.1.1.0/24` | `BR1-WAN-RTR` Fa0/0 = `1.1.1.1` | `BR1-ACCESS` Gi0/1 = `1.1.1.2` |
| `BR2-WAN-RTR` ↔ `BR2-ACCESS` | `2.1.1.0/24` | `BR2-WAN-RTR` Fa0/0 = `2.1.1.1` | `BR2-ACCESS` Gi0/1 = `2.1.1.2` |
| `BR3-WAN-RTR` ↔ `BR3-ACCESS` | `3.1.1.0/24` | `BR3-WAN-RTR` Fa0/0 = `3.1.1.1` | `BR3-ACCESS` Gi0/1 = `3.1.1.2` |
| `BR4-WAN-RTR` ↔ `BR4-ACCESS` | `4.1.1.0/24` | `BR4-WAN-RTR` Fa0/0 = `4.1.1.1` | `BR4-ACCESS` Gi0/1 = `4.1.1.2` |

---

## 4. Internet edge

| Link | Network | End A | End B |
|---|---|---|---|
| `EDGE-RTR` ↔ `ISP` | `200.1.1.0/30` | `EDGE-RTR` Gi0/1 = `200.1.1.1` | `ISP` Gi0/0 = `200.1.1.2` |
| `ISP` ↔ simulated Internet | `203.0.113.0/24` | `ISP` Gi0/1 = `203.0.113.1` | `Server3` = `203.0.113.10` |

`203.0.113.0/24` is the RFC 5737 TEST-NET-3 documentation range, so the
simulated Internet can never collide with a real network.

`200.1.1.1` is the **single** address that every internal host is translated
to on the way out — the proof point for the PAT demonstration.

---

## 5. Routing summary

| Device | Default route | Next hop | Learned via |
|---|---|---|---|
| `core-01` | `0.0.0.0/0` | `10.3.3.2` | static |
| `core-02` | `0.0.0.0/0` | `10.3.3.2` | OSPF (from `core-01`) |
| `HQ-WAN-RTR` | `0.0.0.0/0` | `10.3.3.1` | OSPF (from `core-01`) |
| `BRn-WAN-RTR` | `0.0.0.0/0` | `5.1.1.1` … `8.1.1.1` | OSPF (from `HQ-WAN-RTR`) |
| `EDGE-RTR` | `0.0.0.0/0` | `200.1.1.2` | static |
| `ISP` | `0.0.0.0/0` | `203.0.113.10` | static |

`core-01` originates the default into OSPF with `default-information originate`,
which is how every branch learns the Internet path without a direct ISP
connection.

### Static routes on `EDGE-RTR`

```
ip route 192.168.0.0 255.255.0.0 10.3.3.1     ! all branch and HQ user networks
ip route 172.10.10.0 255.255.255.0 10.3.3.1  ! the server VLAN
```

---

## 6. NAT / PAT translation table

The ACL that selects which internal networks may use the Internet:

```
access-list 1 permit 192.168.10.0 0.0.0.255   ! Sales
access-list 1 permit 192.168.11.0 0.0.0.255   ! HR
access-list 1 permit 192.168.12.0 0.0.0.255   ! Accounts
access-list 1 permit 192.168.13.0 0.0.0.255   ! Branch 1
access-list 1 permit 192.168.14.0 0.0.0.255   ! Branch 2
access-list 1 permit 192.168.15.0 0.0.0.255   ! Branch 3
access-list 1 permit 192.168.16.0 0.0.0.255   ! Branch 4
access-list 1 permit 172.10.10.0 0.0.0.255    ! Server VLAN
```

| Inside local (varies) | Inside global (fixed) | Outside global |
|---|---|---|
| `192.168.10.x` | `200.1.1.1` | `203.0.113.10` |
| `192.168.13.x` | `200.1.1.1` | `203.0.113.10` |
| `172.10.10.3` | `200.1.1.1` | `203.0.113.10` |

---

## 7. Reserved and special addresses

| Address / range | Meaning |
|---|---|
| `192.168.0.0/24` – `192.168.16.255` | Private, used by the enterprise |
| `172.10.10.0/24` | Private, used by the server VLAN |
| `10.1.1.0/24`, `10.2.2.0/24`, `10.3.3.0/24` | Private, infrastructure links |
| `1.1.1.0/24` – `8.1.1.0/24` | Private, branch and WAN links |
| `200.1.1.0/30` | Public, ISP-facing PAT address |
| `203.0.113.0/24` | RFC 5737 TEST-NET-3, simulated Internet |
| `0.0.0.0/0` | Default route |
| `255.255.255.255` | Limited broadcast |
| `*.254` | HSRP virtual gateway on every VLAN |
