# NAT / PAT + ISP — Live Demonstration Script

The complete, ordered script for demonstrating the Internet edge of the lab.
The original author notes for this part of the project are preserved in
[`reference/isp-nat-pat-live-demo.pdf`](reference/isp-nat-pat-live-demo.pdf)
(Bengali); this document is the English, cleaned-up version with the exact
commands and expected output.

**Time needed:** 6–8 minutes for the full run, 2 minutes for the short version.

---

## 1. The design, in one sentence

> "Sir, I implemented centralised Internet access using PAT. Headquarters
> users, centralised servers and all remote branches send Internet-bound
> traffic toward the HQ EDGE-RTR. Branches learn the HQ Internet path through
> OSPF. EDGE-RTR performs PAT, allowing multiple internal addresses to share
> the single ISP-facing address 200.1.1.1."

```
Sales / HR / Accounts
Web / DNS / Email Servers
Branch 1 / 2 / 3 / 4
          │
          ▼
        HQ  (core-01 → core-02)
          │
          ▼
      EDGE-RTR  ── NAT / PAT ──►  ISP  ──►  INTERNET SERVER
                                  200.1.1.2    203.0.113.10
```

---

## 2. Addressing on the edge

| Device | Interface | Address | Role |
|---|---|---|---|
| `EDGE-RTR` | Gi0/0 | `10.3.3.2` | NAT **inside** — enterprise side |
| `EDGE-RTR` | Gi0/1 | `200.1.1.1` | NAT **outside** — ISP facing (PAT address) |
| `ISP` | Gi0/0 | `200.1.1.2` | ISP side of the /30 |
| `ISP` | Gi0/1 | `203.0.113.1` | Towards the simulated Internet |
| `Server3` | Fa0/0 | `203.0.113.10` | The Internet server |

---

## 3. Step 1 — show the NAT roles

```
EDGE-RTR# show running-config | include ip nat
```

**Expected**

```
ip nat inside
ip nat outside
ip nat inside source list 1 interface GigabitEthernet0/1 overload
```

**Say:** "GigabitEthernet0/0 is the NAT inside interface and GigabitEthernet0/1
is the NAT outside interface. The `overload` keyword means PAT is being used
— many internal hosts share one external address."

---

## 4. Step 2 — show which networks get PAT

```
EDGE-RTR# show access-lists 1
```

**Expected**

```
Standard IP access list 1
    10 permit 192.168.10.0 0.0.0.255
    20 permit 192.168.11.0 0.0.0.255
    30 permit 192.168.12.0 0.0.0.255
    40 permit 192.168.13.0 0.0.0.255
    50 permit 192.168.14.0 0.0.0.255
    60 permit 192.168.15.0 0.0.0.255
    70 permit 192.168.16.0 0.0.0.255
    80 permit 172.10.10.0 0.0.0.255
```

| Network | Site |
|---|---|
| `192.168.10.0/24` | Sales |
| `192.168.11.0/24` | HR |
| `192.168.12.0/24` | Accounts |
| `192.168.13.0/24` | Branch 1 |
| `192.168.14.0/24` | Branch 2 |
| `192.168.15.0/24` | Branch 3 |
| `192.168.16.0/24` | Branch 4 |
| `172.10.10.0/24` | Server VLAN |

**Say:** "This standard ACL identifies the internal networks that are allowed to
use PAT. It is used for NAT matching — it is not my department security ACL,
those are the named extended ACLs on the core."

---

## 5. Step 3 — show the default routes

### On `EDGE-RTR`

```
EDGE-RTR# show ip route 0.0.0.0
```

**Expected**

```
Routing entry for 0.0.0.0/0, supernet
  Known via "static", type static, candidate default path
  Routing entry for 0.0.0.0/0
  * 200.1.1.2
```

**Say:** "Unknown Internet destinations are forwarded from EDGE-RTR to the ISP
at 200.1.1.2."

### On `core-01`

```
core-01# show ip route 0.0.0.0
```

**Expected**

```
Routing entry for 0.0.0.0/0, supernet
  Known via "static"
  * 10.3.3.2
```

**Say:** "core-01 sends Internet-bound traffic toward EDGE-RTR at 10.3.3.2."

### On a branch router

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

**Say:** "The branch learns the default route using OSPF. It therefore does not
need a direct ISP connection — Internet traffic is sent toward the HQ first."

---

## 6. Step 4 — generate real traffic

> **Do this before showing the translation table.** Dynamic PAT entries expire
> after a period of inactivity.

### From the HQ

```
SALES-PC1> ping 203.0.113.10
```

**Expected:** 4 replies, 0% loss.

**Say:** "This proves that an HQ client can reach the simulated Internet."

Optionally repeat from `HR-PC1`, `ACCOUNTS-PC1`, `Server1` and `Server2` —
one HQ example is enough if time is short.

### From a branch — this is the important one

```
BR1-PC1> ping 203.0.113.10
```

**Expected:** 4 replies, 0% loss.

**Say:** "Sir, this branch is not directly connected to the ISP. The traffic
reaches HQ through the enterprise WAN and then exits through EDGE-RTR."

---

## 7. Step 5 — the PAT proof

```
EDGE-RTR# show ip nat translations
```

**Expected**

```
Pro  Inside global        Inside local          Outside local       Outside global
icmp 200.1.1.1:1025       172.10.10.3:1        203.0.113.10:1      203.0.113.10:1025
icmp 200.1.1.1:1028       192.168.13.21:1      203.0.113.10:1      203.0.113.10:1028
icmp 200.1.1.1:1031       192.168.16.21:1      203.0.113.10:1      203.0.113.10:1031
icmp 200.1.1.1:1          192.168.10.23:1      203.0.113.10:1      203.0.113.10:1
```

Explain each column:

| Column | Value in the example | Meaning |
|---|---|---|
| Inside local | `192.168.10.23` | the original internal address |
| Inside global | `200.1.1.1` | how it is represented on the inside of the NAT |
| Outside local | `203.0.113.10:1` | the destination as the router saw it |
| Outside global | `203.0.113.10:1025` | the destination as the Internet sees it |

**Say:** "These are the original internal addresses — Sales, a branch and the
e-mail server. Notice that the inside-global column shows `200.1.1.1` for all
of them. All of these different internal addresses are represented outside by
the same ISP-facing address, 200.1.1.1. That is PAT."

### Pick one line and explain it

```
icmp 200.1.1.1:1025  172.10.10.3:1  203.0.113.10:1  203.0.113.10:1025
```

**Say:** "Sir, `172.10.10.3` is my internal e-mail server. It is communicating
with the Internet server `203.0.113.10`. EDGE-RTR translates the internal
source and represents the session using its ISP-facing address `200.1.1.1`.
The protocol is `icmp` — that is the ping traffic."

---

## 8. Step 6 — NAT statistics

```
EDGE-RTR# show ip nat statistics
```

**Expected**

```
Total translations: 42
Outside Interfaces: GigabitEthernet0/1
Inside Interfaces: GigabitEthernet0/0
Hits: 38
Misses: 4
Expired translations: 1
```

**Say:** "This confirms the enterprise-facing interface is NAT inside and the
ISP-facing interface is NAT outside."

---

## 9. Step 7 — the questions the examiner will ask

**Q. What is NAT doing?**

> "NAT translates an internal source address into an address that represents
> the host on the external side."

```
172.10.10.3   ──NAT──►   200.1.1.1
```

**Q. What is PAT doing?**

> "PAT is a type of NAT that allows many internal devices to share one
> external address. In my project Sales, HR, Accounts, the servers and all the
> branch clients all use the EDGE-RTR ISP-facing address `200.1.1.1`."

**Q. Where is the proof that one IP is shared?**

```
EDGE-RTR# show ip nat translations
```

```
Inside local              Inside global
192.168.10.x   ────────►  200.1.1.1
192.168.11.x   ────────►  200.1.1.1
192.168.13.x   ────────►  200.1.1.1
172.10.10.2    ────────►  200.1.1.1
172.10.10.3    ────────►  200.1.1.1
```

**Say:** "Different inside-local addresses, but the same inside-global address.
That is PAT."

---

## 10. Shortest demo sequence — 6 commands

Use this when time is short.

| # | Device | Command | What it proves |
|---|---|---|---|
| 1 | `SALES-PC1` | `ping 203.0.113.10` | HQ client reaches the Internet |
| 2 | `BR1-PC1` | `ping 203.0.113.10` | Branch reaches the Internet via HQ |
| 3 | `Server1` | `ping 203.0.113.10` | The server VLAN reaches the Internet |
| 4 | `BR1-WAN-RTR` | `show ip route 0.0.0.0` | Branch Internet traffic goes toward HQ |
| 5 | `EDGE-RTR` | `show ip nat translations` | Many internal IPs → one global IP |
| 6 | `EDGE-RTR` | `show ip nat statistics` | NAT inside/outside roles and live counters |

---

## 11. Closing statement

> "Sir, I implemented centralised Internet access using PAT. Headquarters
> users, centralised servers and all remote branches send Internet-bound
> traffic toward the HQ EDGE-RTR. Branches learn the HQ Internet path through
> OSPF. EDGE-RTR performs PAT, allowing multiple internal addresses to share
> the single ISP-facing address 200.1.1.1. I can prove this by generating
> Internet traffic and then using `show ip nat translations`, where multiple
> inside-local addresses map to the same inside-global address."

---

## 12. Common questions during the demo

**"Why is the mask `/30` on the ISP link?"**
Because a point-to-point link needs exactly two usable addresses, and `/30`
provides exactly that. Using a `/24` there would waste 252 addresses and
advertise a network that does not exist.

**"Why does `EDGE-RTR` use static routes instead of OSPF?"**
An edge router should have the simplest control plane. Two summary routes are
easier to audit than an OSPF adjacency and remove any chance of a routing
loop between the OSPF domain and the translation device.

**"What happens to a session that is idle?"**
The dynamic PAT entry expires and the source port is returned to the pool. The
next packet from that host creates a new entry — which is why the translation
table can look empty if you wait too long before showing it.

**"Could a user from outside reach my servers?"**
No. The PAT ACL only matches inside networks, and the only address visible
outside is `200.1.1.1` on a `/30`. There is no inbound mapping, so an external
host cannot initiate a session to `172.10.10.x` or `192.168.x.x`. To publish
a service you would add a static mapping to the NAT statement.
