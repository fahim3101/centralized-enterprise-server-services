#!/usr/bin/env python3
"""
diff_lab.py — Show exactly what changed between two Packet Tracer lab files.

The ``.pkt`` container is encrypted, so a normal diff is impossible.  This
tool decrypts both files and compares the underlying XML trees, reporting only
the paths that actually differ.

It is the safety net for ``apply_fixes.py``: after a rebuild, the diff must
show the intended changes and nothing else.

Usage
-----
    python diff_lab.py lab/main_project-original.pkt lab/main_project.pkt
    python diff_lab.py original.pkt new.pkt --json diff.json
    python diff_lab.py original.pkt new.pkt --max 200
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pkt_core import decode_bytes  # noqa: E402


def load(path: str) -> ET.Element:
    """Decrypt *path* and return the parsed XML tree."""
    with open(path, "rb") as handle:
        return ET.fromstring(decode_bytes(handle.read()).xml)


def norm(text: str | None) -> str:
    """Normalise whitespace so that re-indentation is not reported as a change."""
    return (text or "").strip()


def walk(a: ET.Element, b: ET.Element, path: str, diffs: list[str], limit: int) -> None:
    """Append a human readable description of every difference to *diffs*."""
    if len(diffs) >= limit:
        return
    if a.tag != b.tag:
        diffs.append(f"{path}: tag {a.tag} -> {b.tag}")
        return
    if norm(a.text) != norm(b.text):
        diffs.append(f"{path}/{a.tag}: {norm(a.text)[:70]!r} -> {norm(b.text)[:70]!r}")
    if a.attrib != b.attrib:
        diffs.append(f"{path}/{a.tag}: attributes {a.attrib} -> {b.attrib}")
    if len(a) != len(b):
        diffs.append(f"{path}/{a.tag}: child count {len(a)} -> {len(b)}")
        return
    for index, (ca, cb) in enumerate(zip(a, b, strict=False)):
        walk(ca, cb, f"{path}/{a.tag}[{index}]", diffs, limit)


def structural_summary(old: ET.Element, new: ET.Element) -> dict[str, object]:
    """Return the counts that must never change when a lab is patched."""
    summary: dict[str, object] = {}
    for tag in ("VERSION", "SCENARIOSET", "OPTIONS", "PHYSICALWORKSPACE", "FILTERS", "CLUSTERS"):
        a = old.find(tag)
        b = new.find(tag)
        if a is None and b is None:
            summary[tag] = "unchanged"
        elif a is None or b is None:
            summary[tag] = "added" if b is not None else "removed"
        else:
            same = norm(a.text) == norm(b.text) and len(a) == len(b)
            summary[tag] = "unchanged" if same else "CHANGED"
    for tag in ("DEVICES", "LINKS", "SHAPETESTS"):
        a = old.find(f"NETWORK/{tag}")
        b = new.find(f"NETWORK/{tag}")
        summary[tag] = (
            len(a) if a is not None else 0,
            len(b) if b is not None else 0,
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("before", help="the original .pkt file")
    parser.add_argument("after", help="the rebuilt .pkt file")
    parser.add_argument("--max", type=int, default=120, help="maximum differences to print")
    parser.add_argument("--json", help="write the differences as JSON")
    args = parser.parse_args(argv)

    for path in (args.before, args.after):
        if not os.path.isfile(path):
            sys.stderr.write(f"error: no such file: {path}\n")
            return 2

    old = load(args.before)
    new = load(args.after)

    diffs: list[str] = []
    walk(old, new, "", diffs, args.max)

    summary = structural_summary(old, new)

    print(f"{len(diffs)} difference(s) between the two labs\n")
    for diff in diffs:
        print("  " + diff)

    print("\nstructural invariants")
    for key, value in summary.items():
        if isinstance(value, tuple):
            before, after = value
            marker = "OK" if before == after else "CHANGED"
            print(f"  {key:<20} {before} -> {after}   [{marker}]")
        else:
            print(f"  {key:<20} {value}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump({"differences": diffs, "summary": summary}, handle, indent=2)
        print(f"\nwrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
