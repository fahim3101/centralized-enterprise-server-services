## What this pull request changes

<!-- A short description. Link the issue it closes: Closes #123 -->

## Type of change

- [ ] Lab configuration
- [ ] Automation scripts
- [ ] Documentation
- [ ] New device, service or test
- [ ] CI / tooling

## Why

<!-- The problem this solves. -->

## How it was verified

<!-- Paste the command and the result. -->

```
$ python scripts/audit_lab.py lab/main_project.pkt --strict
...
```

## Checklist

- [ ] `python scripts/audit_lab.py lab/main_project.pkt --strict` → 0 failures
- [ ] `python scripts/check_ipam.py lab/main_project.pkt --ipam docs/IPAM.md` → 0 problems
- [ ] `python -m pytest scripts/tests -q` → all green
- [ ] `configs/` regenerated and committed
- [ ] The affected document under `docs/` updated
- [ ] `docs/AUDIT-FINDINGS.md` updated if a known defect was fixed
- [ ] `CHANGELOG.md` updated
- [ ] `lab/main_project-original.pkt` is **not** modified
