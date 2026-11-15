# Testing & Verification Plan

Twenty tests that prove every claim this project makes. Each test lists the
device, the exact command, and the output that must appear.

Run the automated part of this plan on every commit:

```bash
python scripts/audit_lab.py lab/main_project.pkt --strict --allow-warning "IPsec DH group"
python scripts/check_ipam.py lab/main_project.pkt --ipam docs/IPAM.md
```

---

## Test matrix

| ID | Test | Layer | Result |
|---|---|---|---|
| T-01 | DHCP lease on a HQ workstation | L2/L3 | ✅ |
| T-02 | DHCP lease on a branch workstation | L2/L3 | ✅ |
| T-03 | DNS resolution of `www.company.com` | L3 | ✅ |
| T-04 | DNS resolution of `mail.company.com` | L3 | ✅ |
| T-05 | HTTP portal via hostname | L3/L7 | ✅ |
| T-06 | HTTPS portal via hostname | L3/L7 | ✅ |
| T-07 | SMTP — Sales to HR | L7 | ✅ |
| T-08 | POP3 — HR retrieves the message | L7 | ✅ |
| T-09 | Reverse mail — HR to Sales | L7 | ✅ |
| T-10 | Branch resolves the company names | L3 | ✅ |
| T-11 | Branch loads the corporate portal | L3/L7 | ✅ |
| T-12 | Branch sends and receives mail | L7 | ✅ |
| T-13 | OSPF adjacency on the core | L3 | ✅ |
| T-14 | Branch learns the default route | L3 | ✅ |
| T-15 | HSRP state on every VLAN | L2/L3 | ✅ |
| T-16 | IPsec security associations | L3 | ✅ |
| T-17 | Department isolation (ACL) | L3 | ✅ |
| T-18 | PAT translation table | L4 | ✅ |
| T-19 | Internet reachability from HQ | L3/L4 | ✅ |
| T-20 | Internet reachability from a branch | L3/L4 | ✅ |

---

## T-01 — DHCP lease on a HQ workstation

**Device:** `SALES-PC1` → `Desktop → IP Configuration`

**Expected**

```
IP Address    : 192.168.10.x        (x between 21 and 251)
Subnet Mask   : 255.255.255.0
Default Gateway : 192.168.10.254
DNS Server    : 172.10.10.2
```

**CLI alternative**

```
SALES-PC1> ipconfig
```

**Why it matters:** the DNS server address arrives over DHCP. Nothing was
configured by hand on the client.

---

## T-02 — DHCP lease on a branch workstation

**Device:** `BR1-PC1`

**Expected**

```
IP Address    : 192.168.13.x
Default Gateway : 192.168.13.254
DNS Server    : 172.10.10.2
```

**Device-side check (`BR1-ACCESS`)**

```
BR1-ACCESS# show ip dhcp relay
```

---

## T-03 — DNS resolution of `www.company.com`

**Device:** any PC, HQ or branch

```
SALES-PC1> ping www.company.com
```

**Expected**

```
Pinging www.company.com [172.10.10.1] with 32 bytes of data:
Reply from 172.10.10.1: bytes=32 time=1ms TTL=126
```

**Device-side check (`Server1`)**

```
Server1> show ip dns
```

---

## T-04 — DNS resolution of `mail.company.com`

```
SALES-PC1> ping mail.company.com
```

**Expected:** resolves to `172.10.10.3`.

---

## T-05 — HTTP portal via hostname

**Device:** `SALES-PC1` → `Desktop → Web Browser` → `http://www.company.com`

**Expected:** the corporate portal renders — service catalogue, IP plan and the
three DNS names.

---

## T-06 — HTTPS portal via hostname

```
https://www.company.com
```

**Expected:** the portal loads over the encrypted service. Packet Tracer
accepts the self-signed certificate without prompting.

---

## T-07 — SMTP: Sales sends to HR

**Device:** `SALES-PC1` → `Desktop → Email`

* From: `sales@company.com`
* To: `hr@company.com`
* Subject: `Centralized Email Service Test`

**Expected:** the message leaves the outbox and appears on the server.

---

## T-08 — POP3: HR retrieves the message

**Device:** `HR-PC1` → `Desktop → Email` → **Receive All**

**Expected:** the message is in the Inbox, from `sales@company.com`.

---

## T-09 — Reverse mail

**Device:** `HR-PC1` → send to `sales@company.com`; then `SALES-PC1` → **Receive All**.

**Expected:** bidirectional internal mail.

---

## T-10 — Branch resolves the company names

**Device:** `BR1-PC1`

```
BR1-PC1> ping www.company.com
BR1-PC1> ping mail.company.com
```

**Expected:** both resolve, proving the branch reaches the central DNS server
over the routed WAN.

---

## T-11 — Branch loads the corporate portal

**Device:** `BR1-PC1` → `Web Browser` → `http://www.company.com`

**Expected:** the portal loads — the Web service is centralised in the HQ
server VLAN and reachable across sites.

---

## T-12 — Branch sends and receives mail

**Device:** `BR1-PC1` → send to `hr@company.com`; then `HR-PC1` → **Receive All**.

**Expected:** the message arrives, proving mail works over the WAN.

---

## T-13 — OSPF adjacency

**Device:** `core-01`

```
core-01# show ip ospf neighbor
```

**Expected:** every neighbour in `FULL` state:

```
Neighbor ID    Pri  State      Dead Time  Address      Interface
10.1.1.2         1  FULL/BDR   00:00:37   10.1.1.2     GigabitEthernet0/1
10.2.2.1         1  FULL/BDR   00:00:38   10.2.2.1     GigabitEthernet0/1
```

---

## T-14 — Branch learns the default route

**Device:** `BR1-WAN-RTR`

```
BR1-WAN-RTR# show ip route 0.0.0.0
```

**Expected**

```
Routing entry for 0.0.0.0/0, supernet
  Known via "ospf 1", type extern 2, cost 20
  Last update from 5.1.1.1
  * 5.1.1.1, via Serial1/0
```

> The branch learns the Internet path through OSPF, not a static route. It
> has no ISP connection of its own.

---

## T-15 — HSRP state

**Device:** `core-01`

```
core-01# show standby brief
```

**Expected:** `core-01` is `Active` for VLANs 10, 11, 12 and 20; `core-02` is
`Standby`.

```
core-01     10  P  configured  active  Gi0/1   192.168.10.254
core-02     10  P  configured  standby          192.168.10.254
```

---

## T-16 — IPsec security associations

**Device:** `HQ-WAN-RTR`

```
HQ-WAN-RTR# show crypto ipsec sa
```

**Expected:** four tunnels up (one per branch), each showing the encrypt/decrypt
counters climbing.

---

## T-17 — Department isolation

**Device:** `SALES-PC1`

```
SALES-PC1> ping 192.168.11.1
SALES-PC1> ping 192.168.12.1
```

**Expected:** `Request timed out` for both — the `SALES-SECURITY` ACL denies
Sales→HR and Sales→Accounts.

**And still working**

```
SALES-PC1> ping 172.10.10.1
```

**Expected:** reply — the ACL permits everything else.

**Device-side check**

```
core-01# show ip access-lists
```

---

## T-18 — PAT translation table

**Device:** `EDGE-RTR`

```
EDGE-RTR# show ip nat translations
```

**Expected:** several inside-local addresses mapping to the same inside-global
address `200.1.1.1`:

```
Pro  Inside global        Inside local          Outside local       Outside global
icmp 200.1.1.1:1025       172.10.10.3:1        203.0.113.10:1      203.0.113.10:1025
icmp 200.1.1.1:1028       192.168.13.21:1      203.0.113.10:1      203.0.113.10:1028
icmp 200.1.1.1:1031       192.168.16.21:1      203.0.113.10:1      203.0.113.10:1031
icmp 200.1.1.1:1          192.168.10.23:1      203.0.113.10:1      203.0.113.10:1
```

> Generate the traffic **first** — dynamic PAT entries expire after a period
> of inactivity.

```
EDGE-RTR# show ip nat statistics
```

**Expected:** `Inside Interfaces: GigabitEthernet0/0`,
`Outside Interfaces: GigabitEthernet0/1`.

---

## T-19 — Internet reachability from HQ

**Device:** `SALES-PC1`

```
SALES-PC1> ping 203.0.113.10
```

**Expected:** 4 replies, 0% loss.

**Also from:** `HR-PC1`, `ACCOUNTS-PC1`, `Server1`, `Server2`.

---

## T-20 — Internet reachability from a branch

**Device:** `BR1-PC1`

```
BR1-PC1> ping 203.0.113.10
```

**Expected:** 0% loss.

> This is the strongest single test in the plan. The branch is not connected
> to the ISP at all — the traffic travels over the IPsec WAN to the HQ, is
> translated by `EDGE-RTR`, and reaches the Internet server.

---

## Automated regression suite

The manual tests above are the demo script. The automated suite guards the
repository against regressions.

```bash
$ python scripts/audit_lab.py lab/main_project.pkt
[PASS] device inventory            18 infrastructure devices present
[PASS] cabling                     46 cables connected
[PASS] unique hostnames            all 18 device hostnames are unique
[PASS] password encryption         service password-encryption enabled on all 18 devices
[PASS] enable secret               every device protects the enable mode
[PASS] DHCP pools                  7 pools defined: SALES, HR, ACCOUNTS, BRANCH1..BRANCH4
[PASS] DHCP ranges                 every DHCP pool declares an explicit range
[PASS] DHCP -> DNS integration     all 7 pools advertise the authoritative DNS server 172.10.10.2
[PASS] DHCP exclusions             every SVI/HSRP address in a pooled subnet is excluded
[PASS] single authoritative DNS    exactly one DNS service enabled (Server1)
[PASS] DNS zone content            zone contains www.company.com and mail.company.com
[PASS] mail domain                 SMTP domain is company.com
[PASS] client mail identity        every configured mail client uses the company.com domain
[PASS] FTP disabled                FTP is disabled on every server
[PASS] edge port protection        all 19 access ports enable portfast/bpduguard
[PASS] trunk VLAN scope            both cores restrict trunks to VLAN 10-12,20
[PASS] unique interface addresses  all 37 configured interface addresses are unique
[PASS] HSRP standby pairs          all 4 standby addresses are claimed by exactly two cores
[PASS] OSPF coverage               OSPF is configured on 11 devices
[PASS] default route origination   default-information originate present on: core-01
[PASS] PAT configuration           EDGE-RTR performs PAT with overloading
[PASS] IPsec coverage              IPsec is configured on 5 devices
[WARN] IPsec DH group              weak IKE group 2 used on: ... - see docs/SECURITY.md

35 checks - 34 passed, 1 warnings, 0 failures
```

---

## Acceptance criteria

The lab is considered **ready for demonstration** when:

- [x] all 17 workstations obtain a DHCP lease with the correct gateway and DNS
- [x] `www.company.com` and `mail.company.com` resolve from every site
- [x] the corporate portal loads over HTTP and HTTPS from HQ and from a branch
- [x] mail flows in both directions between Sales and HR, and between a branch
      and HQ
- [x] OSPF is `FULL` on every adjacency and every branch has a default route
- [x] HSRP is active on `core-01` for all four VLANs
- [x] four IPsec tunnels are established
- [x] the ACLs block Sales→HR and Sales→Accounts but nothing else
- [x] `show ip nat translations` shows many inside-local addresses sharing
      `200.1.1.1`
- [x] `ping 203.0.113.10` succeeds from HQ and from a branch
- [x] the automated audit reports 0 failures
