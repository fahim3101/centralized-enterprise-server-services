# Contributing

Thank you for taking the time to improve this lab. This document explains how
to set up a development environment, what the project expects from a change,
and how the automation works.

---

## Ground rules

1. **Never edit `lab/main_project.pkt` by hand in a text editor.** It is an
   encrypted container. Use Packet Tracer, or use the tooling in `scripts/`.
2. **Every change must keep the audit green.** `scripts/audit_lab.py` and
   `scripts/check_ipam.py` have to report zero failures.
3. **Documentation and lab stay in sync.** If you change a configuration, the
   matching document in `docs/` has to change too.
4. **Keep the credentials obviously fake.** The lab password is
   `Centr4l1z3d$Lab0nly$ChangeMe2026` and must be obviously a lab value.

---

## Development setup

```bash
git clone https://github.com/fahim3101/centralized-enterprise-server-services.git
cd centralized-enterprise-server-services

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r scripts/requirements.txt
```

---

## The workflow

### 1. Make your change

| What you are changing | How |
|---|---|
| A device configuration | Open `lab/main_project.pkt` in Packet Tracer, change it, save it as `lab/main_project.pkt`. |
| A configuration programmatically | Edit `scripts/apply_fixes.py` and re-run it — see below. |
| The documentation | Edit the Markdown under `docs/`. |
| The corporate web page | Edit `assets/web/index.html`, then re-run `apply_fixes.py` so the page inside the lab matches. |
| The device inventory | Run `python scripts/pkt_export.py lab/main_project.pkt --list --links --ipam` and paste the output into `docs/DEVICE-INVENTORY.md` / `docs/IPAM.md`. |

### 2. Re-export the configurations

```bash
python scripts/pkt_export.py lab/main_project.pkt --out configs/
```

Commit the regenerated `configs/*.cfg` files together with the lab change.

### 3. Run the checks

```bash
python scripts/audit_lab.py lab/main_project.pkt --strict
python scripts/check_ipam.py lab/main_project.pkt --ipam docs/IPAM.md
python -m pytest scripts/tests -q
```

All three must pass before you open a pull request.

### 4. Rebuild the hardened lab from the original

If you change `scripts/apply_fixes.py`, regenerate the lab from the pristine
copy so the result stays reproducible:

```bash
python scripts/apply_fixes.py lab/main_project-original.pkt --out lab/main_project.pkt
```

`lab/main_project-original.pkt` is the untouched build. It must never be
modified.

---

## Commit message format

```
<type>(<scope>): <short summary>

<why the change was needed>

<what changed>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `chore`.

Example:

```
fix(core): exclude the core SVI addresses from the DHCP pools

The SALES pool covered 192.168.10.252 and .253, which are the SVI
addresses of core-01 and core-02. A lease could collide with them and
black-hole the workstation.

Fixes #14
```

---

## Adding a device

1. Add it in Packet Tracer and cable it in.
2. Give it a hostname that follows the naming convention in
   `docs/DEVICE-INVENTORY.md`.
3. Add its config to `scripts/apply_fixes.py` if it needs hardening.
4. Add it to `DEVICE_NAME_MAP` and `CONFIG_FILE_MAP` in `scripts/pkt_export.py`.
5. Update the inventory, the IPAM and the topology diagram.
6. Re-export, re-audit, commit.

---

## Adding a test

Tests live in `scripts/tests/test_lab.py` and assert against the real lab
file. A good test:

* is named after the behaviour, not the implementation
* fails with a message that explains what broke
* does not depend on the order of devices in the XML

```bash
python -m pytest scripts/tests -q -k dns
```

---

## Code style

* Python follows PEP 8, formatted with `ruff`.
* Line length 100.
* Docstrings on every public function.
* Type hints on function signatures.

```bash
ruff check scripts --select E,F,W,I --line-length 120
ruff format --check scripts --line-length 120
```

---

## Pull request checklist

- [ ] `python scripts/audit_lab.py lab/main_project.pkt --strict` → 0 failures
- [ ] `python scripts/check_ipam.py lab/main_project.pkt --ipam docs/IPAM.md` → 0 problems
- [ ] `python -m pytest scripts/tests -q` → all green
- [ ] `configs/` regenerated and committed
- [ ] The affected document in `docs/` updated
- [ ] `docs/AUDIT-FINDINGS.md` updated if the change fixes a known defect
- [ ] `CHANGELOG.md` updated

---

## Reporting a bug

Use the **Lab issue** template at
[`.github/ISSUE_TEMPLATE/lab_issue.md`](.github/ISSUE_TEMPLATE/lab_issue.md).
Always include the output of:

```bash
python scripts/audit_lab.py lab/main_project.pkt --json
```

---

## Code of conduct

By participating you agree to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md).
