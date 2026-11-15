# The Lab File

| File | What it is |
|---|---|
| [`main_project.pkt`](main_project.pkt) | **The lab.** The hardened, production-ready build. Open this one. |
| [`main_project-original.pkt`](main_project-original.pkt) | The pristine original build, kept for reference and comparison. Never modify it. |

Both files were produced with Cisco Packet Tracer **9.0.1** (`VERSION 9.0.1.0858`).

---

## Opening the lab

1. Start Cisco Packet Tracer 9.0.1.
2. `File → Open` → `main_project.pkt`.
3. Wait about a minute for the DHCP leases to settle and OSPF to converge.
4. Start with `SALES-PC1` → `Desktop → Command Prompt`.

> The `.pkt` format changed in Packet Tracer 7.0. Opening the file in an
> older release will fail. Packet Tracer 8.x and 9.x both work.

---

## First things to try

```
SALES-PC1> ipconfig
```

```
IP Address        : 192.168.10.x
Default Gateway   : 192.168.10.254
DNS Server        : 172.10.10.2
```

```
SALES-PC1> ping www.company.com
SALES-PC1> ping mail.company.com
```

Then open the web browser and go to `http://www.company.com`.

The full test matrix is in [`../docs/TESTING.md`](../docs/TESTING.md).

---

## What the file contains

| | |
|---|---|
| Devices | 42 (18 infrastructure, 4 servers, 17 workstations, 3 power distribution devices) |
| Cables | 46 |
| Sites | 6 (HQ + 4 branches + simulated Internet) |
| VLANs | 10, 11, 12, 13, 14, 15, 16, 20 |
| Routing | OSPF area 0 across all six sites |
| Tunnels | 4 IPsec site-to-site VPNs |
| NAT | 1 PAT instance at `EDGE-RTR` |

---

## The file is encrypted

A `.pkt` is a proprietary encrypted container, so it cannot be diffed or
reviewed in a pull request. This repository works around that by extracting
the plaintext XML and generating everything else from it:

```bash
pip install -r ../scripts/requirements.txt

# dump the decrypted XML
python ../scripts/pkt_export.py main_project.pkt --xml-only --xml-out lab.xml

# list every device with its model and hostname
python ../scripts/pkt_export.py main_project.pkt --list

# audit the lab
python ../scripts/audit_lab.py main_project.pkt --strict
```

---

## Rebuilding the hardened lab

The hardened lab is generated from the pristine original by a deterministic
script, so it can always be reproduced:

```bash
python ../scripts/apply_fixes.py main_project-original.pkt --out main_project.pkt
```

The script applies every fix listed in
[`../docs/AUDIT-FINDINGS.md`](../docs/AUDIT-FINDINGS.md) and then verifies
that the result decodes back to the same XML.

---

## Why there are two files

Keeping the original makes the audit reproducible: anyone can run
`apply_fixes.py` against the pristine build and get the shipped lab back. It
also documents the starting point honestly, instead of pretending the project
was built this way the first time.

---

## Tracked size

The file is under 250 KB, which keeps the repository light enough to clone
quickly while still shipping the complete simulation.
