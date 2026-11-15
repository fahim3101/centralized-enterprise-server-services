# Device Configurations

The running-config of every infrastructure device, exported **directly from**
[`lab/main_project.pkt`](../lab/main_project.pkt) — not typed by hand.

```bash
python scripts/pkt_export.py lab/main_project.pkt --out configs/
```

---

## Files

### HQ core layer

| File | Device | Role |
|---|---|---|
| [`core-01.cfg`](core-01.cfg) | `core-01` | Primary core — HSRP active, DHCP server for all 7 pools, OSPF area 0, default-route originator |
| [`core-02.cfg`](core-02.cfg) | `core-02` | Secondary core — HSRP standby, OSPF peer, DHCP relay |

### HQ leaf layer

| File | Device | Role |
|---|---|---|
| [`leaf-01.cfg`](leaf-01.cfg) | `leaf-01` | Leaf 1 — trunks to both cores, LACP to `leaf-02` |
| [`leaf-02.cfg`](leaf-02.cfg) | `leaf-02` | Leaf 2 — trunks to both cores, LACP to `leaf-01` |

### HQ access layer

| File | Device | Role |
|---|---|---|
| [`access-sales.cfg`](access-sales.cfg) | `access-sales-01` | Sales VLAN 10 |
| [`access-hr.cfg`](access-hr.cfg) | `access-hr-01` | HR VLAN 11 |
| [`access-accounts.cfg`](access-accounts.cfg) | `access-accounts-01` | Accounts VLAN 12 |

### WAN and Internet edge

| File | Device | Role |
|---|---|---|
| [`hq-wan-router.cfg`](hq-wan-router.cfg) | `HQ-WAN-RTR` | OSPF area 0, four IPsec site-to-site tunnels |
| [`edge-router.cfg`](edge-router.cfg) | `EDGE-RTR` | NAT/PAT to the ISP |
| [`isp-router.cfg`](isp-router.cfg) | `ISP` | Simulated upstream ISP |

### Branches

| File | Device |
|---|---|
| [`branch1-router.cfg`](branch1-router.cfg) | `BR1-WAN-RTR` |
| [`branch1-access.cfg`](branch1-access.cfg) | `BR1-ACCESS` |
| [`branch2-router.cfg`](branch2-router.cfg) | `BR2-WAN-RTR` |
| [`branch2-access.cfg`](branch2-access.cfg) | `BR2-ACCESS` |
| [`branch3-router.cfg`](branch3-router.cfg) | `BR3-WAN-RTR` |
| [`branch3-access.cfg`](branch3-access.cfg) | `BR3-ACCESS` |
| [`branch4-router.cfg`](branch4-router.cfg) | `BR4-WAN-RTR` |
| [`branch4-access.cfg`](branch4-access.cfg) | `BR4-ACCESS` |

### Servers

Server services do not live in a running-config — Packet Tracer stores them
inside the `.pkt` container. They are documented in
[`servers/README.md`](servers/README.md).

### Hardening overlays

Optional overlays that are **not** applied to the shipped lab:
[`hardened/`](hardened/)

---

## File format

Each file starts with a header block:

```
! =============================================================
!  core-01                | Catalyst 3560-24PS        | HQ Core Layer-1 (primary HSRP + DHCP server + OSPF)
!  Repository : fahim3101/centralized-enterprise-server-services
!  Exported from lab/main_project.pkt (Cisco Packet Tracer 9.0.1)
!  Device hostname in this config: core-01
! =============================================================
```

followed by the verbatim running-config, ending with `end`.

---

## Re-applying a configuration

```bash
# in Packet Tracer, on the device CLI:
enable
configure terminal
<paste the body of the file, without the header>
end
write memory
```

Or copy the whole file into the Packet Tracer CLI window — the `!` comment
lines are valid IOS input.

---

## Platform notes

| Platform | Version | Notes |
|---|---|---|
| Catalyst 3560-24PS | `12.2(37)SE1` | Layer-3 switch, uses `interface VlanN` SVIs |
| Cisco 2811 | `12.4` | Branch and HQ WAN routers |
| Cisco 2911 | `15.1` | `EDGE-RTR` and `ISP` |

The 3560 images do not support `ip ssh`/`crypto key` in the simulation, so
management hardening is limited to `enable secret` and `banner motd`.

---

## Keeping these in sync

The CI pipeline regenerates and diffs these files. If you change the lab and
forget to re-export, CI fails with a diff — that is deliberate.
