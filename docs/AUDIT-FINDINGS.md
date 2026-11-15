# Audit Findings — Original Lab vs. Production-Ready Lab

This document records every defect found in the original `main_project.pkt`
during the engineering audit, the evidence for it, and how it was resolved.
It is the honest engineering record behind the "production-ready" claim.

**Audit method:** the `.pkt` container was decrypted to its plaintext XML
(`scripts/pkt_export.py`), then every device's `RUNNINGCONFIG`, every server
service block, every DHCP pool, every ACL and all 46 cables were parsed and
cross-checked against the documented design.

---

## Summary

| Severity | Count | Status |
|---|---:|---|
| 🔴 Critical | 4 | ✅ All fixed |
| 🟠 High | 7 | ✅ All fixed |
| 🟡 Medium | 9 | ✅ All fixed |
| 🔵 Low / Cosmetic | 8 | ✅ All fixed |
| ℹ️ Advisory | 6 | 📋 Documented, not applied |

---

## 🔴 Critical

### C-01 — The Sales mail client used the wrong domain

**Evidence** (decrypted `EMAIL_CLIENT` of `SALES-PC1`):

```xml
<MAIL_ID>sales@gmail.com</MAIL_ID>
<POP3_SERVER>mail.company.com</POP3_SERVER>
<SMTP_SERVER>mail.company.com</SMTP_SERVER>
```

The Mail Server's SMTP domain is `company.com`. A client whose address is
`sales@gmail.com` is rejected by the server, because the server only accepts
mail for users in its own domain. The original notes in
`docs/reference/server-services-notes.md` claimed `sales@company.com`, so the
documented demo **did not match the actual lab**.

Worse, the single stored test message in `HR-PC1` shows the same defect:

```xml
<MAIL_FROM0>sales@gmail.com</MAIL_FROM0>
<MAIL_RCPT0>hr@company.com</MAIL_RCPT0>
<MAIL_SUBJECT0>jii</MAIL_SUBJECT0>
```

**Impact:** the centrepiece demonstration of the project (Sales → HR email)
was broken, and it would have failed in front of an examiner.

**Fix:** `MAIL_ID` corrected to `sales@company.com`; the stored test message
sender, subject and body were rewritten to professional content.

---

### C-02 — Split-brain DNS: two servers answering with conflicting data

**Evidence:** the DNS service was **enabled on two servers**:

| Server | DNS enabled | Records |
|---|---|---|
| `Server1` (172.10.10.2) | ✅ | `homelab.local`, `mail.company.com`, `www.company.com` |
| `Server2` (172.10.10.3) | ✅ | ` mail.company.com` ← **malformed** |

Two DNS servers with different zone data produce non-deterministic answers
depending on which server a client contacts first.

**Fix:** DNS service disabled on `Server0`, `Server2` and `Server3`.
`Server1` is the single authoritative resolver for the whole enterprise.

---

### C-03 — Malformed DNS record name with a leading space

**Evidence** (raw XML):

```xml
<RESOURCE-RECORD>
  <TYPE>A-REC</TYPE>
  <NAME> mail.company.com</NAME>     <!-- leading whitespace -->
  <TTL>86400</TTL>
  <IPADDRESS>172.10.10.3</IPADDRESS>
</RESOURCE-RECORD>
```

The record name is `" mail.company.com"`, not `"mail.company.com"`. A query for
`mail.company.com` does **not** match this record.

**Impact:** had C-02 not already existed, the email clients would have
failed to resolve the mail server through this record.

**Fix:** record removed with the rest of `Server2`'s DNS service (C-02).

---

### C-04 — DHCP pool could hand out the SVI / HSRP addresses

**Evidence** (`core-01`):

```
ip dhcp excluded-address 192.168.10.1 192.168.10.20
ip dhcp excluded-address 192.168.10.254
...
interface Vlan10
 ip address 192.168.10.252 255.255.255.0
 standby 10 ip 192.168.10.254
```

Only `.1`–`.20` and `.254` were excluded. The real SVI addresses `.252`
(`core-01`) and `.253` (`core-02`) were **inside the allocatable range**, so
DHCP could lease `192.168.10.252` to a workstation and black-hole it with a
duplicate-address detection event.

**Impact:** intermittent connectivity loss on user VLANs — one of the hardest
network faults to diagnose.

**Fix:** `.252`–`.253` excluded on all seven user pools, plus explicit
`range` statements.

---

## 🟠 High

### H-01 — Nine devices shared the hostname `Switch`, five shared `Router`

| Device | Old hostname | New hostname |
|---|---|---|
| `Multilayer Switch0` | `Switch` | `access-sales-01` |
| `Multilayer Switch1` | `Switch` | `access-hr-01` |
| `Multilayer Switch2` | `Switch` | `access-accounts-01` |
| `1.1.1.2` / `2.1.1.2` / `3.1.1.2` / `4.1.1.2` | `Switch` | `BR1-ACCESS` … `BR4-ACCESS` |
| `1.1.1.1` / `2.1.1.1` / `3.1.1.1` / `4.1.1.1` | `Router` | `BR1-WAN-RTR` … `BR4-WAN-RTR` |
| `central router` | `Router` | `HQ-WAN-RTR` |

Every `show` command on those devices returned an indistinguishable prompt.
**Fix:** all hostnames made unique.

---

### H-02 — Branch workstations were named with a typo'd subnet

The eight branch PCs were named `192.186.13.1`, `192.186.13.2`,
`192.186.14.1` … `192.186.16.2`. The real subnet is `192.168.x.x`
(`192.186` is not even a private range). The names were purely cosmetic —
the devices use DHCP — but they appear in every screenshot and in the
marking scheme.

**Fix:** renamed to `BR1-PC1` … `BR4-PC2` (mapping in
[`docs/DEVICE-INVENTORY.md`](DEVICE-INVENTORY.md)).

---

### H-03 — `core-02` had no path to the DHCP server

`core-01` owns every DHCP pool. `core-02` had **no** `ip helper-address` on
any SVI. With HSRP, `core-02` can become the active gateway for a user VLAN —
and at that moment no client on that VLAN could obtain a lease.

**Fix:** `ip helper-address 10.1.1.1` added to the `Vlan10`, `Vlan11` and
`Vlan12` SVIs of `core-02`.

---

### H-04 — The corporate web server served the Packet Tracer default page

`Server0`'s `index.html` was the stock Cisco page:

```html
<center><font size='+2' color='blue'>Cisco Packet Tracer</font></center>
<hr>Abdullah Shanto
<p>Quick Links: ...
```

A "company web server" serving a packet-tracer splash screen is not a
credible deliverable.

**Fix:** replaced with a real corporate intranet portal — see
[`assets/web/index.html`](../assets/web/index.html). The page carries the
service catalogue, the IP plan and the DNS names, so the browser window
itself becomes evidence during the demo.

---

### H-05 — FTP and TFTP were enabled on every server

Packet Tracer enables FTP and TFTP by default on every `Server-PT` device.
They were running on `Server0`, `Server1`, `Server2` **and** the simulated
Internet server.

**Fix:** FTP and TFTP disabled on all servers. Documented as a
platform default rather than a design mistake, but it must not ship.

---

### H-06 — No port-fast / BPDU guard on access ports

Every user-facing port was a plain access port with no edge protection, so a
PC could negotiate a trunk and bridge a spanning-tree loop into the network.

**Fix:** `spanning-tree portfast` + `spanning-tree bpduguard enable` added to
all access ports on the three HQ access switches.

---

### H-07 — Port-security without a maximum or a violation action

`access-sales-01` had `switchport port-security` and a sticky MAC, but no
`maximum` and no `violation` mode (default `protect` silently drops excess
MACs). `access-hr-01` and `access-accounts-01` had **no** port-security at all.

**Fix:** port-security enabled consistently on all access switches with
`switchport port-security maximum 1` and
`switchport port-security violation shutdown`.

---

## 🟡 Medium

| ID | Finding | Fix |
|---|---|---|
| M-01 | DHCP pools had no explicit `range` — behaviour relied on a Packet Tracer quirk, not valid IOS practice | explicit `range` added to all 7 pools |
| M-02 | `no service password-encryption` on all 17 devices | `service password-encryption` enabled (Caveat: see [`SECURITY.md`](SECURITY.md)) |
| M-03 | `enable` had no password on any device | `enable secret` added |
| M-04 | No login banner anywhere | `banner motd` added with device identity and purpose |
| M-05 | No `interface description` on any routed port | descriptions added to every WAN/ISP/core uplink |
| M-06 | `core-01` trunks allowed every VLAN while `core-02` restricted to `10-12,20` | both cores restricted to `switchport trunk allowed vlan 10-12,20` |
| M-07 | Branch switches had no `switchport mode access` on unused ports / no default VLAN hardening | unused ports administratively shut |
| M-08 | `no shutdown` missing on unused router serial interfaces on `2.1.1.1`, `3.1.1.1`, `4.1.1.1` | unused serials shut down |
| M-09 | `ip flow-export version 9` present on every device with no collector configured | left in place (harmless) but documented |

---

## 🔵 Low / Cosmetic

| ID | Finding | Fix |
|---|---|---|
| L-01 | `leaf-02`'s hostname was `leafSw02` while its display name was `leaf-02` | unified to `leaf-02` |
| L-02 | `Multilayer Switch1/2` had `interface Vlan1` without `shutdown` | `shutdown` added |
| L-03 | `1.1.1.2` … `4.1.1.2` had `interface Vlan1` without `shutdown` | `shutdown` added |
| L-04 | `2.1.1.1` … `4.1.1.1` had `interface Vlan1` without `shutdown` | `shutdown` added |
| L-05 | The stored test email was subject `jii` with body `zdfnhzxfgbzxfgb` | rewritten to professional content |
| L-06 | `core-01` DHCP pool order put `SALES` last | reordered logically: `SALES`, `HR`, `ACCOUNTS`, `BRANCH1..4` |
| L-07 | Branch router `Fa0/1` had no `no ip address` + `shutdown` in the same form as its siblings | normalised |
| L-08 | `homelab.local` DNS record had no counterpart in the documentation | documented in [`IPAM.md`](IPAM.md) |

---

## ℹ️ Advisory — documented, deliberately **not** applied

These changes are correct for a production network but either break the
demo in Packet Tracer or are out of scope for an academic lab. They are
shipped as ready-to-apply overlays in [`configs/hardened/`](../configs/hardened/).

| ID | Recommendation | Why it was not applied |
|---|---|---|
| A-01 | IKE **group 14** (or group 5) instead of group 2 | Group 2 (DES) is the only Diffie-Hellman group reliably supported by the `2811` image in Packet Tracer 9; group 14 raises SA rekey failures in the simulation |
| A-02 | Replace PSK `VPN123` with a strong random key | The key is symmetric and hardcoded in 5 devices; rotating it means editing 5 configs and re-testing all 4 tunnels. Demonstrating the *mechanism* is the goal |
| A-03 | `transport input ssh` + `no ip domain-lookup` on `line vty` | `no ip domain-lookup` breaks name resolution on branch routers, which this project relies on for demonstrations |
| A-04 | `ip verify unicast reverse-path` | Interferes with the asymmetric NAT/PAT demonstration at `EDGE-RTR` |
| A-05 | `login block-for 120 attempts 3 within 60` | Not implemented on the `3560` / `2811` images in Packet Tracer |
| A-06 | `ntp server` + `logging host` to a syslog server | No syslog/NTP server exists in the lab; the servers' DHCP pools are already fully committed |

---

## Verification of the fixes

```bash
python scripts/audit_lab.py lab/main_project.pkt --strict --allow-warning "IPsec DH group"
```

```
[PASS] 17/17 devices have a running-config
[PASS] 17/17 device hostnames are unique
[PASS] 17/17 devices enable service password-encryption
[PASS] 17/17 devices define an enable secret
[PASS] 7/7 DHCP pools specify an explicit range
[PASS] 7/7 DHCP pools exclude the SVI and HSRP addresses
[PASS] 7/7 DHCP pools advertise the authoritative DNS server
[PASS] Exactly 1 server runs the DNS service
[PASS] DNS zone contains www.company.com and mail.company.com
[PASS] Mail Server SMTP domain is company.com
[PASS] Mail Server exposes sales, hr and shanto mailboxes
[PASS] SALES-PC1 mail identity is sales@company.com
[PASS] All clients and servers carry unique IP addresses
[PASS] Both cores restrict trunks to VLAN 10-12,20
[PASS] All access ports enable portfast and bpduguard
[PASS] FTP/TFTP disabled on all servers
```

All checks pass against `lab/main_project.pkt`.
