# Hardening Overlays

These configurations are **not** applied to the shipped lab. They are the
recommended production changes, kept separate so that the demonstration lab
stays reliable while the hardening path stays documented.

Why they are not applied by default is explained for each one in
[`../../docs/SECURITY.md`](../../docs/SECURITY.md) §3.

---

## `ipsec-stronger-parameters.cfg`

**Apply to:** `HQ-WAN-RTR`, `BR1-WAN-RTR`, `BR2-WAN-RTR`, `BR3-WAN-RTR`,
`BR4-WAN-RTR`

```cisco
! Replace the legacy IKE policy with a modern Diffie-Hellman group.
! NOTE: the Cisco 2811 image in Packet Tracer 9 does not support group 14
! reliably - the SA rekey fails in the simulation. Verify on real hardware
! before applying.
crypto isakmp policy 10
 encr aes 256
 authentication pre-share
 group 14
 lifetime 28800
 exit

! Use a unique random key per tunnel instead of a shared literal.
! Generate with:  openssl rand -base64 36
crypto isakmp key <RANDOM-KEY-FOR-5-1-1-2> address 5.1.1.2
crypto isakmp key <RANDOM-KEY-FOR-6-1-1-2> address 6.1.1.2
crypto isakmp key <RANDOM-KEY-FOR-7-1-1-2> address 7.1.1.2
crypto isakmp key <RANDOM-KEY-FOR-8-1-1-2> address 8.1.1.2
 exit
```

---

## `management-ssh-only.cfg`

**Apply to:** all 18 infrastructure devices

```cisco
! Named accounts with privilege levels, instead of an unprivileged shared login
username netadmin privilege 15 secret <TYPE-5-HASH>
username netoperator privilege 5 secret <TYPE-5-HASH>
enable secret <TYPE-5-HASH>
!
line vty 0 4
 login local
 transport input ssh
 session-limit 2
 exec-timeout 10 0
!
! Restrict management to the server VLAN
access-list 10 permit 172.10.10.0 0.0.0.255
line vty 0 4
 access-class 10 in
```

> `no ip domain-lookup` is deliberately **not** included. The branch routers
> rely on name resolution during the demonstration, and disabling it breaks
> that behaviour.

---

## `edge-control-plane.cfg`

**Apply to:** `EDGE-RTR`

```cisco
! Protect the edge router's own control plane from a UDP flood
control-plane
 service-policy input CONTROL-PLANE-POLICY
!
policy-map CONTROL-PLANE-POLICY
 class class-default
  police rate 8000 pps conform-action transmit exceed-action drop
!
```

---

## `syslog-and-ntp.cfg`

**Apply to:** all 18 infrastructure devices

```cisco
! Point the devices at a syslog server on the server VLAN
logging host 172.10.10.2
logging trap informational
logging buffered 32768 informational
!
! Synchronise the clock
ntp server 172.10.10.2
ntp server 203.0.113.10
```

> The lab has no syslog or NTP server. Add one to Server VLAN 20 before
> applying this overlay.

---

## `core-02-acl-parity.cfg`

**Apply to:** `core-02`

```cisco
! core-01 carries the department ACLs. If core-02 ever becomes the active
! gateway for a VLAN, that VLAN would be unfiltered. Apply the same ACLs on
! core-02 for defence in depth.
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
!
interface Vlan10
 ip access-group SALES-SECURITY in
exit
interface Vlan11
 ip access-group HR-SECURITY in
exit
interface Vlan12
 ip access-group ACCOUNTS-SECURITY in
exit
```

---

## `dhcp-failover-note.md`

A single DHCP server is the one remaining single point of failure in the
design: if `core-01` fails, clients on the VLANs where `core-02` has become
active cannot obtain a new lease.

Two options, in order of effort:

### Option A — DHCP server on both cores, split by subnet

Move the branch pools onto `core-02` and keep the HQ pools on `core-01`.
Both cores stay reachable for the relay, no two servers ever answer for the
same subnet, and a core failure still leaves every subnet with a server.

```
! on core-01
ip dhcp pool SALES
 range 192.168.10.21 192.168.10.251
 network 192.168.10.0 255.255.255.0
 default-router 192.168.10.254
 dns-server 172.10.10.2
exit
ip dhcp pool HR
 ...
ip dhcp pool ACCOUNTS
 ...

! on core-02
ip dhcp pool BRANCH1
 range 192.168.13.21 192.168.13.251
 network 192.168.13.0 255.255.255.0
 default-router 192.168.13.254
 dns-server 172.10.10.2
exit
...
```

### Option B — a dedicated DHCP server on the server VLAN

Add a server on `172.10.10.4`, point every `ip helper-address` at it, and let
`core-01` and `core-02` keep only the relay configuration. This is the
cleanest design and the one a production network should use.
