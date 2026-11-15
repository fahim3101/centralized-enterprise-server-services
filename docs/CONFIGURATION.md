# Configuration Guide

How every service in the lab is configured, in the order you would build it.
Each section states the Packet Tracer UI path *and* the equivalent CLI, so the
guide works whether you are clicking or typing.

---

## 0. Building order

If you are rebuilding the lab from scratch, follow this order — each step
depends on the previous one:

1. Device naming and cabling
2. VLANs and trunking
3. Core SVIs + HSRP
4. DHCP pools on `core-01`
5. OSPF on the core and the WAN routers
6. IPsec tunnels
7. Branch SVIs + DHCP relay
8. NAT/PAT at the edge
9. Server services (DNS, HTTP, HTTPS, SMTP, POP3)
10. Client configuration

---

## 1. VLANs

| VLAN | Name | Users |
|---:|---|---|
| 10 | SALES | HQ Sales workstations |
| 11 | HR | HQ HR workstations |
| 12 | ACCOUNTS | HQ Accounts workstations |
| 13 | BRANCH1 | Branch 1 workstations |
| 14 | BRANCH2 | Branch 2 workstations |
| 15 | BRANCH3 | Branch 3 workstations |
| 16 | BRANCH4 | Branch 4 workstations |
| 20 | SERVERS | Central services |

### CLI — access switch (`access-sales-01`)

```
enable
configure terminal

interface FastEthernet0/1
 switchport mode access
 switchport access vlan 10
 spanning-tree portfast
 spanning-tree bpduguard enable
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky 00E0.B0B2.5AD0
 exit

interface GigabitEthernet0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk allowed vlan 10-12,20
 exit

end
```

### CLI — core trunk (`core-01`)

```
interface FastEthernet0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk allowed vlan 10-12,20
 exit
```

> Both cores use the identical `allowed vlan 10-12,20` list. A mismatch here
> is one of the most common causes of "some VLANs work, others don't".

---

## 2. Core SVIs and HSRP

`core-01` is the active gateway (priority 110 + preempt), `core-02` the
standby.

### `core-01`

```
ip routing

interface Vlan10
 description Sales users
 ip address 192.168.10.252 255.255.255.0
 standby 10 ip 192.168.10.254
 standby 10 priority 110
 standby 10 preempt
 ip access-group SALES-SECURITY in
 exit

interface Vlan11
 description HR users
 ip address 192.168.11.252 255.255.255.0
 standby 11 ip 192.168.11.254
 standby 11 priority 110
 standby 11 preempt
 ip access-group HR-SECURITY in
 exit

interface Vlan12
 description Accounts users
 ip address 192.168.12.252 255.255.255.0
 standby 12 ip 192.168.12.254
 standby 12 priority 110
 standby 12 preempt
 ip access-group ACCOUNTS-SECURITY in
 exit

interface Vlan20
 description Central server VLAN
 ip address 172.10.10.252 255.255.255.0
 standby 20 ip 172.10.10.254
 standby 20 priority 110
 standby 20 preempt
 exit
```

### `core-02`

Identical, except:

* the SVI address is `.253` instead of `.252`
* there is **no** `standby ... priority` line (so it stays at 100)
* **no** `ip access-group` line — the ACLs live on `core-01` only, because
  `core-01` is always the active gateway
* an `ip helper-address 10.1.1.1` is added to VLANs 10/11/12 so the standby
  core can still serve DHCP

```
interface Vlan10
 ip address 192.168.10.253 255.255.255.0
 standby 10 ip 192.168.10.254
 standby 10 preempt
 ip helper-address 10.1.1.1
 exit
```

### Verify

```
core-01# show standby brief
 core-01   10  P  configured  active  Gi0/1     192.168.10.254
```

---

## 3. DHCP — centralised on `core-01`

### Exclusions

Every user network reserves `.1–.20`, the two SVI addresses and the HSRP
address, so a lease can never collide with infrastructure:

```
ip dhcp excluded-address 192.168.10.1 192.168.10.20
ip dhcp excluded-address 192.168.10.252 192.168.10.254
ip dhcp excluded-address 192.168.11.1 192.168.11.20
ip dhcp excluded-address 192.168.11.252 192.168.11.254
ip dhcp excluded-address 192.168.12.1 192.168.12.20
ip dhcp excluded-address 192.168.12.252 192.168.12.254
ip dhcp excluded-address 192.168.13.1 192.168.13.20
ip dhcp excluded-address 192.168.13.252 192.168.13.254
ip dhcp excluded-address 192.168.14.1 192.168.14.20
ip dhcp excluded-address 192.168.14.252 192.168.14.254
ip dhcp excluded-address 192.168.15.1 192.168.15.20
ip dhcp excluded-address 192.168.15.252 192.168.15.254
ip dhcp excluded-address 192.168.16.1 192.168.16.20
ip dhcp excluded-address 192.168.16.252 192.168.16.254
```

### Pools

```
ip dhcp pool SALES
 range 192.168.10.21 192.168.10.251
 network 192.168.10.0 255.255.255.0
 default-router 192.168.10.254
 dns-server 172.10.10.2
exit
```

Repeat for `HR`, `ACCOUNTS`, `BRANCH1` … `BRANCH4` with the matching subnet.

> The `dns-server 172.10.10.2` line is the heart of the project: it is how
> every client in every branch learns where the centralised DNS server is,
> without a single manual configuration.

### Verify

```
core-01# show ip dhcp binding
IP address       Client ID / MAC address   Type   Lease expiry  State
192.168.10.21    0063.6973.2e01             arp    00:07:12     Active
```

---

## 4. OSPF — area 0 across all six sites

### `core-01`

```
router ospf 1
 log-adjacency-changes
 network 10.1.1.0 0.0.0.255 area 0
 network 192.168.10.0 0.0.0.255 area 0
 network 192.168.11.0 0.0.0.255 area 0
 network 192.168.12.0 0.0.0.255 area 0
 network 172.10.10.0 0.0.0.255 area 0
 network 10.3.3.0 0.0.0.255 area 0
 default-information originate
 exit
ip route 0.0.0.0 0.0.0.0 10.3.3.2
```

`default-information originate` is what makes the branches Internet-capable
without a direct ISP connection.

### `HQ-WAN-RTR`

```
router ospf 1
 log-adjacency-changes
 network 10.1.1.0 0.0.0.255 area 0
 network 5.1.1.0 0.0.0.255 area 0
 network 6.1.1.0 0.0.0.255 area 0
 network 7.1.1.0 0.0.0.255 area 0
 network 8.1.1.0 0.0.0.255 area 0
 network 10.2.2.0 0.0.0.255 area 0
 exit
```

### Branch routers

`BRn-WAN-RTR` needs two statements — its WAN link and its LAN link:

```
router ospf 1
 network 5.1.1.0 0.0.0.255 area 0
 network 1.1.1.0 0.0.0.255 area 0
 exit
```

The branch **access switch** advertises the branch LAN:

```
router ospf 1
 network 192.168.13.0 0.0.0.255 area 0
 network 1.1.1.0 0.0.0.255 area 0
 exit
```

### Verify

```
core-01# show ip ospf neighbor
Neighbor ID     Pri   State       Dead Time   Address         Interface
10.1.1.2          1   FULL/BDR    00:00:37    10.1.1.2        GigabitEthernet0/1
10.2.2.1          1   FULL/BDR    00:00:38    10.2.2.1        GigabitEthernet0/1
```

---

## 5. IPsec site-to-site VPN

Each branch has its own crypto map, its own peer and its own interesting-traffic
ACL.

### `HQ-WAN-RTR`

```
crypto isakmp policy 10
 encr aes
 authentication pre-share
 group 2
 exit
crypto isakmp key VPN123 address 5.1.1.2
crypto isakmp key VPN123 address 6.1.1.2
crypto isakmp key VPN123 address 7.1.1.2
crypto isakmp key VPN123 address 8.1.1.2
 exit

crypto ipsec transform-set VPN-SET esp-aes esp-sha-hmac
 exit

crypto map VPN-MAP 10 ipsec-isakmp
 set peer 5.1.1.2
 set transform-set VPN-SET
 match address 110
 exit
```

`crypto map VPN-B2`, `VPN-B3` and `VPN-B4` follow the same pattern with
peers `6.1.1.2`, `7.1.1.2`, `8.1.1.2` and ACLs `120`, `130`, `140`.

The maps are applied to the matching serial interface:

```
interface Serial1/0
 ip address 5.1.1.1 255.255.255.0
 clock rate 2000000
 crypto map VPN-MAP
 exit
```

### Interesting traffic ACLs

```
! on HQ-WAN-RTR
access-list 110 permit ip 192.168.10.0 0.0.0.255 192.168.13.0 0.0.0.255
access-list 120 permit ip 192.168.10.0 0.0.0.255 192.168.14.0 0.0.0.255
access-list 130 permit ip 192.168.10.0 0.0.0.255 192.168.15.0 0.0.0.255
access-list 140 permit ip 192.168.10.0 0.0.0.255 192.168.16.0 0.0.0.255

! on the matching branch router (mirrored)
access-list 110 permit ip 192.168.13.0 0.0.0.255 192.168.10.0 0.0.0.255
```

### Verify

```
HQ-WAN-RTR# show crypto ipsec sa
dst              src              state    conn-id   tunnel
203.0.113.10     203.0.113.10     QUICK    9
```

---

## 6. Branch access switches — gateway and DHCP relay

```
ip routing

interface Vlan13
 description Branch 1 users
 ip address 192.168.13.254 255.255.255.0
 ip helper-address 10.1.1.1
 exit

router ospf 1
 network 192.168.13.0 0.0.0.255 area 0
 network 1.1.1.0 0.0.0.255 area 0
 exit
```

`ip helper-address 10.1.1.1` forwards the client's DHCP broadcast to the
central DHCP server on `core-01`.

---

## 7. NAT / PAT at the Internet edge

### `EDGE-RTR`

```
interface GigabitEthernet0/0
 description inside interface - enterprise side
 ip address 10.3.3.2 255.255.255.0
 ip nat inside
 exit

interface GigabitEthernet0/1
 description outside interface - ISP facing (PAT)
 ip address 200.1.1.1 255.255.255.252
 ip nat outside
 exit

ip nat inside source list 1 interface GigabitEthernet0/1 overload

access-list 1 permit 192.168.10.0 0.0.0.255
access-list 1 permit 192.168.11.0 0.0.0.255
access-list 1 permit 192.168.12.0 0.0.0.255
access-list 1 permit 192.168.13.0 0.0.0.255
access-list 1 permit 192.168.14.0 0.0.0.255
access-list 1 permit 192.168.15.0 0.0.0.255
access-list 1 permit 192.168.16.0 0.0.0.255
access-list 1 permit 172.10.10.0 0.0.0.255

ip route 0.0.0.0 0.0.0.0 200.1.1.2
ip route 192.168.0.0 255.255.0.0 10.3.3.1
ip route 172.10.10.0 255.255.255.0 10.3.3.1
```

> `overload` is what turns NAT into **PAT** — many inside sessions share one
> outside address, distinguished by the TCP/UDP source port.

---

## 8. Department isolation ACLs

Applied inbound on the `core-01` SVIs.

```
ip access-list extended SALES-SECURITY
 permit udp any eq bootpc any eq bootps
 deny ip 192.168.10.0 0.0.0.255 192.168.11.0 0.0.0.255
 deny ip 192.168.10.0 0.0.0.255 192.168.12.0 0.0.0.255
 permit ip 192.168.10.0 0.0.0.255 any
exit

ip access-list extended HR-SECURITY
 permit udp any eq bootpc any eq bootps
 deny ip 192.168.11.0 0.0.0.255 192.168.10.0 0.0.0.255
 deny ip 192.168.11.0 0.0.0.255 192.168.12.0 0.0.0.255
 permit ip 192.168.11.0 0.0.0.255 any
exit

ip access-list extended ACCOUNTS-SECURITY
 permit udp any eq bootpc any eq bootps
 deny ip 192.168.12.0 0.0.0.255 192.168.10.0 0.0.0.255
 deny ip 192.168.12.0 0.0.0.255 192.168.11.0 0.0.0.255
 permit ip 192.168.12.0 0.0.0.255 any
exit
```

The `permit udp any eq bootpc any eq bootps` line comes **first** so DHCP
still works. Without it, the explicit `deny` rules would block the DHCP
renewal traffic of the neighbouring department and clients would show an IP
but lose the DNS server.

---

## 9. Server services

Full details in [`configs/servers/`](../configs/servers/). Summary:

| Server | UI path | What to set |
|---|---|---|
| `Server0` | `Services → HTTP` | HTTP ON, HTTPS ON, upload [`assets/web/index.html`](../assets/web/index.html) as `index.html` |
| `Server1` | `Services → DNS` | DNS ON, add the three A records below |
| `Server2` | `Services → EMAIL` | SMTP ON, POP3 ON, domain `company.com`, users `sales`, `hr`, `shanto` |
| `Server3` | `Services → HTTP` | HTTP ON — the simulated Internet server |

### DNS A records on `Server1`

| Name | Type | Address | TTL |
|---|---|---|---|
| `www.company.com` | A Record | `172.10.10.1` | 86400 |
| `mail.company.com` | A Record | `172.10.10.3` | 86400 |
| `homelab.local` | A Record | `172.10.10.2` | 86400 |

> **Only one server may run the DNS service.** Two DNS servers with different
> zone data is split-brain DNS and produces unpredictable results.

---

## 10. Client configuration

### Workstations (DHCP)

`Desktop → IP Configuration → DHCP` — the client then receives the address,
gateway **and** the DNS server from the centralised pool.

### E-mail clients

| Field | `SALES-PC1` | `HR-PC1` |
|---|---|---|
| Your Name | Sales User | HR User |
| Email Address | `sales@company.com` | `hr@company.com` |
| Incoming Mail Server (POP3) | `mail.company.com` | `mail.company.com` |
| Outgoing Mail Server (SMTP) | `mail.company.com` | `mail.company.com` |
| Username | `sales` | `hr` |
| Password | `sales123` | `hr123` |

The mail server name is a **hostname**, not an IP, so the client resolves it
through the centralised DNS server — which proves DNS and mail working
together.

---

## 11. Management and security baseline

Applied to every infrastructure device:

```
service password-encryption
enable secret 5 $1$Centr4l1z3d$Lab0nly$ChangeMe2026
banner motd ^AUTHORIZED ACCESS ONLY - Centralized Enterprise Server Services | <device> | <role>^
```

Plus, on every routed interface:

```
 description <human readable purpose>
```

Further recommendations that are **not** applied by default are listed in
[`SECURITY.md`](SECURITY.md) and in [`configs/hardened/`](../configs/hardened/).
