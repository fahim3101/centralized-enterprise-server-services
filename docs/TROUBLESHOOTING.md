# Troubleshooting Guide

Real problems that were hit while building this lab, with the diagnostic path
and the fix. Use the **Symptom → Diagnose → Fix** pattern.

---

## 1. `ping www.company.com` → *"Ping request could not find host"*

### Diagnose

Work from the bottom up — never change two things at once.

```
1. ping 172.10.10.2        ← is the DNS server reachable at all?
2. ipconfig                ← does the client actually have a DNS server?
3. show ip dns             ← on Server1: are the records loaded?
```

### Interpretation

| `ping 172.10.10.2` | `ipconfig` shows DNS | Conclusion | Fix |
|---|---|---|---|
| fails | — | L3 problem, not DNS | Go to §2 |
| works | empty | DHCP is not handing out the DNS address | Go to §3 |
| works | `172.10.10.2` | DNS service or zone problem | Go to §4 |

### Fix — §3: DHCP is not advertising the DNS server

```
core-01# conf t
core-01(config)# ip dhcp pool SALES
core-01(dhcp-config)# dns-server 172.10.10.2
core-01(dhcp-config)# exit
```

Then force a renewal on the client:

```
SALES-PC1> ipconfig /release
SALES-PC1> ipconfig /renew
```

> **A PC configured as a DHCP client cannot edit its DNS field.** The field
> is greyed out by design — it is controlled by the DHCP scope. This is the
> single most common confusion in this project.

### Fix — §4: the DNS record is wrong

`Server1` → `Services → DNS` → check the A record. Two traps:

* the record name must have **no leading or trailing space** — `" mail.company.com"`
  is a different name from `"mail.company.com"`
* the record must exist on the **one** authoritative server; if two servers
  run DNS with different data, clients get different answers depending on
  which one they reach first

---

## 2. The client has an IP but cannot reach anything

### Diagnose

```
SALES-PC1> ping 192.168.10.254      ← is the gateway reachable?
SALES-PC1> ping 172.10.10.1         ← is the server VLAN reachable?
```

| Symptom | Cause | Fix |
|---|---|---|
| No reply to the gateway | The SVI is down, or the port is in the wrong VLAN | `show interfaces status`, `show vlan` |
| Gateway OK, server VLAN fails | Routing problem on the core | `show ip route` on `core-01` |
| Both work, but slowly | A spanning-tree loop or a port without `portfast` | `show spanning-tree` |

---

## 3. The DHCP lease is wrong

| Symptom | Cause | Fix |
|---|---|---|
| No lease at all | The pool does not cover the client's subnet | Check `network` and `range` in the pool |
| Lease in the wrong subnet | The client is on the wrong access port | Check `switchport access vlan` on the access switch |
| Lease but no gateway | `default-router` missing from the pool | Add `default-router <vlan>.254` |
| Lease but no DNS server | `dns-server` missing from the pool | Add `dns-server 172.10.10.2` |
| Intermittent dropouts | The lease pool overlaps an SVI address | Extend the exclusions, see §5 |
| A branch PC gets no lease | No DHCP relay configured | Add `ip helper-address 10.1.1.1` on the branch SVI |

---

## 4. E-mail client says *"Server not found"*

This is **not** an OSPF, VLAN, DHCP or DNS problem — the resolution and the
connectivity were already proven by the successful `ping`. Look at the mail
server itself.

### Diagnose

```
Server2> show ip dns       ← does mail.company.com resolve?
Server2> check domain      ← is the SMTP domain actually set?
```

### The actual cause

The `Domain Name` field on `Server2 → Services → EMAIL` was **blank**. The
server had SMTP and POP3 enabled and the correct users, but with no domain it
rejected every connection and the client reported "server not found".

### Fix

```
Server2 → Services → EMAIL → Domain Name: company.com → Set
```

> The mail server must also have the **users** created under
> `Server2 → Services → EMAIL` → user list, with the same names the clients
> use. A client can only log in as a user that exists on the server.

### Other causes of the same message

| Cause | How to confirm |
|---|---|
| The client used an IP address instead of the hostname | The client must use `mail.company.com` |
| The client's e-mail address domain differs from the server's | Client `sales@company.com`, server domain `company.com` |
| The client is configured as POP3 but the server only runs SMTP | Enable POP3 on the server |

---

## 5. A client randomly loses connectivity

### Diagnose

```
core-01# show ip dhcp binding
core-01# show ip arp | include 192.168.10
```

### Cause

The DHCP pool was handing out an address that is also configured on an SVI.
The original exclusions covered only `.1–.20` and `.254`, leaving `.252` and
`.253` — the two core SVI addresses — inside the allocatable range.

### Fix

```
ip dhcp excluded-address 192.168.10.252 192.168.10.254
ip dhcp excluded-address 192.168.11.252 192.168.11.254
ip dhcp excluded-address 192.168.12.252 192.168.12.254
```

Applied to every user network.

---

## 6. A branch cannot reach the Internet

Work through the path in order:

```
1. BR1-PC1> ping 192.168.13.254        ← local gateway
2. BR1-PC1> ping 172.10.10.2           ← central DNS (proves the WAN works)
3. BR1-WAN-RTR# show ip route 0.0.0.0  ← does the branch have a default route?
4. HQ-WAN-RTR# show ip route 0.0.0.0   ← does the HQ have one?
5. EDGE-RTR# show ip nat translations  ← is the traffic being translated?
```

| Fails at | Cause | Fix |
|---|---|---|
| step 2 | The WAN is down | `show ip ospf neighbor` on both ends; check the serial `clock rate 2000000` |
| step 3 | The branch has no default route | `core-01` is missing `default-information originate` in `router ospf 1` |
| step 4 | The HQ core has no default route | `ip route 0.0.0.0 0.0.0.0 10.3.3.2` on `core-01` |
| step 5 | The source address is not in the PAT ACL | Add the missing `access-list 1 permit …` line on `EDGE-RTR` |

> **The most common cause by far:** `default-information originate` missing
> on `core-01`. Without it, OSPF never advertises the default route and every
> branch is an island.

---

## 7. The branch can ping HQ but the branch-to-branch traffic fails

### Cause

By design, only **Sales ↔ branch** pairs are tunnelled. Branch 1 cannot reach
Branch 2 directly, because there is no matching interesting-traffic ACL and no
crypto map for that pair.

### Fix (if it is genuinely required)

Add a second crypto map on `HQ-WAN-RTR` for the branch-to-branch pair, with
its own ACL, and mirror the ACL on both branch routers:

```
access-list 150 permit ip 192.168.13.0 0.0.0.255 192.168.14.0 0.0.0.255
crypto map VPN-B1B2 10 ipsec-isakmp
 set peer 5.1.1.2
 set transform-set VPN-SET
 match address 150
```

---

## 8. The IPsec tunnel is down

```
HQ-WAN-RTR# show crypto ipsec sa
```

| Output | Meaning | Fix |
|---|---|---|
| no entries, tunnel idle | No interesting traffic | Generate traffic, then re-check |
| `QM` state | Phase 1 succeeded, phase 2 negotiating | Check the transform set and the ACL on both ends |
| `dormant` | The peer never answered | Check `crypto isakmp key` — the key and the peer address must match on **both** routers |
| `active` but no traffic | ACL mismatch | `show access-lists` on both ends; the source/destination must be mirrored |

The pre-shared key line must exist on both devices, each naming the **other**
device's address:

```
! on HQ-WAN-RTR
crypto isakmp key VPN123 address 5.1.1.2
! on BR1-WAN-RTR
crypto isakmp key VPN123 address 5.1.1.1
```

---

## 9. `show ip nat translations` is empty

### Cause

Dynamic PAT entries expire after a period of inactivity. The table is only
populated while traffic is flowing.

### Fix

**Generate the traffic first, then look at the table.**

```
Sales PC:  ping 203.0.113.10
Branch PC: ping 203.0.113.10
Server:    ping 203.0.113.10
EDGE-RTR#  show ip nat translations
```

---

## 10. Two devices cannot reach each other although both are up

### Diagnose

```
core-01# show ip access-lists
core-01# show ip route <destination>
```

The most likely cause is the department isolation ACL doing exactly what it
was configured to do. `SALES-SECURITY` denies Sales→HR and Sales→Accounts:

```
deny ip 192.168.10.0 0.0.0.255 192.168.11.0 0.0.0.255
deny ip 192.168.10.0 0.0.0.255 192.168.12.0 0.0.0.255
```

The client still receives an IP address and a DNS server, so the symptom looks
like "the network is broken" when it is actually the security policy working.

---

## 11. A port goes down after a device is replaced

### Cause

`switchport port-security violation shutdown` plus a sticky MAC address means
a replacement host with a different MAC is blocked.

### Fix

Either clear the sticky entry or remove the sticky MAC from the config:

```
access-sales-01# conf t
access-sales-01(config)# interface FastEthernet0/1
access-sales-01(config-if)# no switchport port-security mac-address sticky 00E0.B0B2.5AD0
access-sales-01(config-if)# end
```

---

## 12. Diagnostic command cheat sheet

| Goal | Command |
|---|---|
| Interface state | `show ip interface brief` |
| VLAN membership | `show vlan` / `show interfaces trunk` |
| Trunk allowed VLANs | `show interfaces trunk` |
| HSRP | `show standby brief` |
| DHCP leases | `show ip dhcp binding` |
| DHCP pools | `show ip dhcp pool` |
| OSPF neighbours | `show ip ospf neighbor` |
| OSPF routes | `show ip route ospf` |
| Static routes | `show ip route static` |
| Full routing table | `show ip route` |
| NAT translations | `show ip nat translations` |
| NAT statistics | `show ip nat statistics` |
| IPsec SAs | `show crypto ipsec sa` |
| IPsec policies | `show crypto map` |
| ACL counters | `show ip access-lists` |
| Spanning tree | `show spanning-tree` |
| Port channel | `show etherchannel summary` |
| ARP | `show ip arp` |
| Interface errors | `show interfaces counters errors` |
| DNS on a server | `show ip dns` |
