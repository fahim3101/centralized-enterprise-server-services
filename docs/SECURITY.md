# Security Model

The lab implements real security controls. This document describes what is
enforced, what is **not** enforced, and exactly what you would change before
running this design anywhere near production.

---

## 1. Summary

| # | Control | Status | Where |
|---|---|---|---|
| 1 | Inter-department isolation (named extended ACLs) | ✅ Enforced | `core-01` SVIs |
| 2 | Encrypted WAN (IPsec, AES + SHA-HMAC) | ✅ Enforced | HQ ↔ branch serial links |
| 3 | HSRP first-hop redundancy | ✅ Enforced | both cores |
| 4 | Port-security on access ports | ✅ Enforced | all access switches |
| 5 | BPDU guard on access ports | ✅ Enforced | all access switches |
| 6 | Trunk VLAN scoping | ✅ Enforced | both cores |
| 7 | `enable secret` | ✅ Enforced | all devices |
| 8 | `service password-encryption` | ✅ Enforced | all devices |
| 9 | Login banner | ✅ Enforced | all devices |
| 10 | Address translation (PAT) | ✅ Enforced | `EDGE-RTR` |
| 11 | FTP / TFTP disabled on servers | ✅ Enforced | all servers |
| 12 | Single authoritative DNS (no split brain) | ✅ Enforced | `Server1` |
| 13 | IKE Diffie-Hellman group | ⚠️ Legacy (group 2) | all tunnels |
| 14 | Pre-shared key strength | ⚠️ Weak (`VPN123`) | all tunnels |
| 15 | SSH-only management | ❌ Not enforced | `line vty` |
| 16 | AAA / local user accounts | ❌ Not enforced | all devices |
| 17 | Syslog and SNMP | ❌ Not enforced | all devices |
| 18 | Control-plane policing | ❌ Not enforced | `core-01` |
| 19 | DHCP snooping | ❌ Not enforced | access switches |
| 20 | Dynamic ARP inspection | ❌ Not enforced | access switches |

---

## 2. What is enforced

### 2.1 Department isolation

Three named extended ACLs are applied inbound on the `core-01` SVIs:

```
ip access-list extended SALES-SECURITY
 permit udp any eq bootpc any eq bootps
 deny ip 192.168.10.0 0.0.0.255 192.168.11.0 0.0.0.255
 deny ip 192.168.10.0 0.0.0.255 192.168.12.0 0.0.0.255
 permit ip 192.168.10.0 0.0.0.255 any
```

Sales cannot reach HR or Accounts. HR cannot reach Sales or Accounts. Accounts
cannot reach Sales or HR. Everything else — the web server, the DNS server, the
mail server, the Internet and the branches — is permitted, and DHCP keeps
working because the bootpc/bootps permit is the first line.

**Limitation:** the ACLs live on `core-01` only, because `core-01` is always
the active gateway. If `core-02` ever became active on a VLAN whose ACL was
not also applied there, that VLAN would be unfiltered. A production build
applies the same ACL on both cores.

### 2.2 Encrypted WAN

Every HQ ↔ branch link carries IPsec:

```
crypto isakmp policy 10
 encr aes
 authentication pre-share
 group 2
crypto ipsec transform-set VPN-SET esp-aes esp-sha-hmac
crypto map VPN-MAP 10 ipsec-isakmp
 set peer 5.1.1.2
 set transform-set VPN-SET
 match address 110
```

Only the intended traffic is tunnelled. The interesting-traffic ACLs are
mirrored on both ends:

| Tunnel | HQ ACL | Branch ACL |
|---|---|---|
| BR1 | `permit ip 192.168.10.0 0.0.0.255 192.168.13.0 0.0.0.255` | `permit ip 192.168.13.0 0.0.0.255 192.168.10.0 0.0.0.255` |
| BR2 | `… 192.168.14.0 …` | `… 192.168.14.0 …` |
| BR3 | `… 192.168.15.0 …` | `… 192.168.15.0 …` |
| BR4 | `… 192.168.16.0 …` | `… 192.168.16.0 …` |

### 2.3 Access-layer hardening

```
 spanning-tree portfast
 spanning-tree bpduguard enable
 switchport port-security
 switchport port-security maximum 1
 switchport port-security violation shutdown
 switchport port-security mac-address sticky <mac>
```

* `portfast` removes the 30-second STP convergence delay from a host port
* `bpduguard` shuts the port if a switch is connected to it, preventing a
  rogue switch from creating a loop
* port-security pins one MAC per port and shuts the port on violation,
  preventing MAC flooding and address spoofing

### 2.4 Management baseline

Applied to all 18 infrastructure devices:

```
service password-encryption
enable secret 5 $1$Centr4l1z3d$Lab0nly$ChangeMe2026
banner motd ^AUTHORIZED ACCESS ONLY - Centralized Enterprise Server Services | <device> | <role>^
```

### 2.5 Edge translation

The PAT ACL only matches inside networks, and there is no inbound mapping.
External hosts therefore **cannot** initiate a session to `192.168.x.x` or
`172.10.10.x`.

---

## 3. What is not enforced — and what to do about it

Ready-to-apply overlays live in [`../configs/hardened/`](../configs/hardened/).

### 3.1 IKE Diffie-Hellman group

**Current:** `group 2` (1024-bit MODP).

**Why it was left:** the `2811` image in Packet Tracer 9 implements the IKE
policy command with a limited set of supported groups. Group 2 works
reliably in the simulation; groups 14 and higher have produced SA rekey
failures during testing.

**Production recommendation:**

```
crypto isakmp policy 10
 encr aes
 authentication pre-share
 group 14
 lifetime 28800
```

### 3.2 Pre-shared key strength

**Current:** the literal key `VPN123`, configured on five devices.

**Why it was left:** the key must be identical on both ends of every tunnel.
Changing it means editing five configurations and re-testing four tunnels
before every demonstration. The project demonstrates the *mechanism* of
site-to-site IPsec, not key distribution.

**Production recommendation:** generate a unique random key per tunnel
(24 characters or more), store it with a secrets manager, and distribute it
over a secure channel. Better still, move to IKEv2 with certificates, which
removes the shared secret entirely.

### 3.3 SSH-only management

```
line vty 0 4
 login local
 transport input ssh
```

`no ip domain-lookup` is **not** recommended here: the branch routers rely on
name resolution during the demonstration, and disabling it breaks that.

### 3.4 Local user accounts with privilege levels

```
username netadmin privilege 15 secret <strong-hash>
username netoperator privilege 5 secret <strong-hash>
enable secret <strong-hash>
line vty 0 4
 login local
 transport input ssh
```

### 3.5 Syslog and SNMP

No syslog server exists in the lab, so logging goes to the console only. A
production build would add a syslog server on the server VLAN, configure
`logging host 172.10.10.x`, and set `logging trap informational`.

### 3.6 Control-plane policing

On an edge router, a UDP flood aimed at the router itself can exhaust the CPU.
`control-plane` policing on `EDGE-RTR` limits that:

```
control-plane
 service-policy input CONTROL-PLANE-POLICY
```

### 3.7 DHCP snooping and dynamic ARP inspection

The access switches currently rely on port-security for layer-2 protection.
A production build adds DHCP snooping (so a rogue DHCP server cannot be
plugged in) and dynamic ARP inspection (so a rogue host cannot spoof the
gateway).

### 3.8 Management access control

Restrict management traffic to a dedicated network:

```
access-list 10 permit 172.10.10.0 0.0.0.255
line vty 0 4
 access-class 10 in
```

---

## 4. Credential policy for this lab

| Item | Value | Note |
|---|---|---|
| `enable secret` | `$1$Centr4l1z3d$Lab0nly$ChangeMe2026` | **Lab only.** Change before any real use. |
| Mailbox `sales` | `sales123` | Demo account, HR department |
| Mailbox `hr` | `hr123` | Demo account, HR department |
| Mailbox `shanto` | `shanto123` | Demo account |
| IPsec PSK | `VPN123` | See §3.2 |

> **Before presenting this lab outside a classroom**, change the `enable
> secret`, the IPsec pre-shared keys and the mailbox passwords, and add
> `login local` with individual user accounts so that every action is
> attributable.

---

## 5. Verification

The automated audit checks the enforced items on every commit:

```bash
python scripts/audit_lab.py lab/main_project.pkt --strict --allow-warning "IPsec DH group"
```

It verifies unique hostnames, password encryption, `enable secret`, login
banners, explicit DHCP ranges, DHCP exclusions, DHCP→DNS integration, a
single authoritative DNS server, the DNS zone contents, the mail domain and
mailboxes, correct client mail identities, FTP/TFTP being disabled, edge port
protection, trunk VLAN scoping, unique interface addresses, HSRP pairing,
OSPF coverage, default-route origination and the PAT configuration.

The one warning it reports — the legacy IKE group — is intentional and is
documented in §3.1.
