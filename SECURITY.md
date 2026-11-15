# Security Policy

## Scope

This repository publishes an **educational network lab**. It contains
deliberately weak credentials and legacy cryptographic parameters so that the
lab can be demonstrated and studied safely.

| Asset | Sensitivity |
|---|---|
| `lab/main_project.pkt` | A Packet Tracer simulation. It describes a fictional network. |
| `configs/*.cfg` | Device configurations for the simulation. |
| `docs/` | Documentation. |
| `scripts/` | Tooling that reads the lab file. |

**No real network device, production credential, customer data or personal
data is contained in this repository.** There is no live infrastructure to
attack.

---

## What a "vulnerability" means here

A report is in scope when it concerns the **tooling** in this repository:

* a bug in `scripts/` that corrupts a lab file
* a bug that makes the audit report a false PASS
* an injection or path-traversal issue in the parsers
* a supply-chain risk in the pinned dependencies
* a credential for a **real** system accidentally committed here

A report is **out of scope**:

* the weak `enable secret`, the `VPN123` pre-shared key or the `sales123`
  mailbox passwords — these are intentional and documented in
  [`docs/SECURITY.md`](docs/SECURITY.md)
* "the lab is not hardened enough" — that is the point of the lab, and the
  hardening roadmap is already written down
* anything about the fictional network topology

---

## Reporting

Please report a tooling vulnerability privately by opening a
[security advisory](https://github.com/fahim3101/centralized-enterprise-server-services/security/advisories/new)
on this repository.

Include:

* what the issue is
* the steps to reproduce it
* the version or commit you tested
* the impact you believe it has

We aim to acknowledge a report within 3 working days.

---

## Before using this lab anywhere real

The lab is safe for a classroom. It is **not** safe to deploy. If you are
going to adapt it:

1. Change the `enable secret` on every device.
2. Change the IPsec pre-shared key on every tunnel, or move to IKEv2 with
   certificates.
3. Change the mailbox passwords.
4. Replace `login` with `login local` and individual named accounts.
5. Restrict `line vty` with an access class and `transport input ssh`.
6. Work through the full checklist in [`docs/SECURITY.md`](docs/SECURITY.md).

---

## Dependencies

The scripts depend on `pkt-core` (and `pytest` for the test suite). Report a
vulnerability in that package upstream, not here.
