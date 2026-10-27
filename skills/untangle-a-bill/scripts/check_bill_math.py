#!/usr/bin/env python3
"""Check the arithmetic of a bill and flag things worth asking about.

Reads a JSON file (see assets/bill-input.md) listing line items and the
printed total, then reports: the item breakdown, whether the sum
matches the printed total, duplicates, zero or negative amounts, the
largest item, round-number charges, and how the total compares to last
time. It does not accuse anyone of overcharging; it only reports facts.
Standard library only; works offline.

Usage:
    python check_bill_math.py bill.json
    python check_bill_math.py bill.json --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

__all__ = ["BillCheckError", "check_bill", "render_report", "main"]

TOLERANCE = 0.005
ROUND_THRESHOLD = 5.00


class BillCheckError(Exception):
    """A problem with the input the user should hear about plainly."""


def _money(value: float) -> str:
    return f"{value:.2f}"


def check_bill(spec: dict) -> dict:
    """Return a report dict of facts about the bill, verifiable ones only."""
    if not isinstance(spec, dict):
        raise BillCheckError("the JSON top level must be an object")
    unknown = sorted(set(spec) - {"bill_from", "bill_for", "printed_total", "previous_total", "items"})
    if unknown:
        raise BillCheckError("unrecognized field(s): " + ", ".join(unknown) +
                             " (accepted fields are listed in assets/bill-input.md)")

    bill_from = _optional_text(spec, "bill_from")
    bill_for = _optional_text(spec, "bill_for")

    items = spec.get("items")
    if items is None:
        raise BillCheckError("input needs an 'items' list")
    if not isinstance(items, list) or not items:
        raise BillCheckError("'items' must be a non-empty list of {label, amount} entries")
    cleaned_items = []
    for index, entry in enumerate(items, start=1):
        if not isinstance(entry, dict):
            raise BillCheckError(f"item {index} is not an object: {entry!r}")
        label = entry.get("label")
        if not isinstance(label, str) or not label.strip():
            raise BillCheckError(f"item {index} is missing a text 'label'")
        amount = entry.get("amount")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise BillCheckError(f"item {label.strip()!r}: 'amount' must be a number")
        cleaned_items.append({"label": label.strip(), "amount": float(amount)})

    printed_total = spec.get("printed_total")
    if printed_total is not None:
        if isinstance(printed_total, bool) or not isinstance(printed_total, (int, float)):
            raise BillCheckError("'printed_total' must be a number")
        printed_total = float(printed_total)

    previous_total = spec.get("previous_total")
    if previous_total is not None:
        if isinstance(previous_total, bool) or not isinstance(previous_total, (int, float)):
            raise BillCheckError("'previous_total' must be a number")
        previous_total = float(previous_total)

    item_sum = sum(item["amount"] for item in cleaned_items)
    labels = [item["label"] for item in cleaned_items]
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    zero_items = [item["label"] for item in cleaned_items if item["amount"] == 0]
    negative_items = [f"{item['label']} (-${abs(item['amount']):.2f})" for item in cleaned_items if item["amount"] < 0]

    biggest = max(cleaned_items, key=lambda item: item["amount"])
    round_items = [
        f"{item['label']} (${item['amount']:.2f})"
        for item in cleaned_items
        if item["amount"] >= ROUND_THRESHOLD and item["amount"] == round(item["amount"])
    ]

    math_ok = printed_total is None or abs(item_sum - printed_total) <= TOLERANCE
    difference = None
    if printed_total is not None and previous_total is not None:
        difference = printed_total - previous_total

    return {
        "bill_from": bill_from,
        "bill_for": bill_for,
        "items": cleaned_items,
        "item_sum": round(item_sum, 2),
        "printed_total": round(printed_total, 2) if printed_total is not None else None,
        "math_ok": math_ok,
        "missing_from_total": round(item_sum - printed_total, 2) if printed_total is not None and not math_ok else 0.0,
        "biggest_item": {"label": biggest["label"], "amount": round(biggest["amount"], 2)},
        "duplicate_labels": duplicates,
        "zero_items": zero_items,
        "negative_items": negative_items,
        "round_items": round_items,
        "previous_total": round(previous_total, 2) if previous_total is not None else None,
        "difference_from_previous": round(difference, 2) if difference is not None else None,
    }


def _optional_text(spec: dict, field: str) -> str | None:
    value = spec.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise BillCheckError(f"{field!r} must be a non-empty string if present")
    return value.strip()


def render_report(report: dict) -> str:
    lines: list[str] = []
    header = "Bill breakdown"
    if report["bill_from"]:
        header += f" - {report['bill_from']}"
        if report["bill_for"]:
            header += f", {report['bill_for']}"
    lines.append(header)
    lines.append("")
    lines.append("## Items as printed")
    for item in report["items"]:
        sign = "-" if item["amount"] < 0 else ""
        lines.append(f"- {item['label']}: {sign}${abs(item['amount']):.2f}")
    lines.append(f"Sum of items: ${report['item_sum']:.2f}")
    lines.append("")

    lines.append("## Math check")
    if report["printed_total"] is None:
        lines.append("No printed total was given, so the sum could not be checked. Find the total on the bill itself.")
    elif report["math_ok"]:
        lines.append(f"The items add up to the printed total (${report['printed_total']:.2f}). Whatever is wrong with this bill, arithmetic is not it.")
    else:
        lines.append(f"Printed total ${report['printed_total']:.2f} does not match the item sum of ${report['item_sum']:.2f} (off by ${report['missing_from_total']:.2f}). That gap is worth the first question on the call.")
    lines.append("")

    lines.append("## Worth asking about (facts, not accusations)")
    biggest = report["biggest_item"]
    lines.append(f"- Largest item: {biggest['label']} at ${biggest['amount']:.2f} - the first thing to ask about")
    for label in report["duplicate_labels"]:
        lines.append(f"- {label} appears more than once on the bill")
    for label in report["zero_items"]:
        lines.append(f"- {label} is $0.00 - ask what it is for")
    for entry in report["negative_items"]:
        lines.append(f"- Negative amount: {entry} - possibly a credit or a correction")
    for entry in report["round_items"]:
        lines.append(f"- Round number: {entry} - a common shape for a fee someone added")
    if not any((report["duplicate_labels"], report["zero_items"], report["negative_items"], report["round_items"])):
        lines.append("- Nothing obviously odd in item shape; ask about the biggest item and any fee with a vague name")
    lines.append("")

    if report["difference_from_previous"] is not None:
        diff = report["difference_from_previous"]
        updown = "higher" if diff > 0 else "lower" if diff < 0 else "the same"
        lines.append("## Compared with last time")
        lines.append(f"This bill is ${abs(diff):.2f} {updown} than the previous one (${report['previous_total']:.2f}).")
        lines.append("")
    lines.append("## Before the call, write down")
    lines.append("Your account or member number, the bill date, and one question: 'Can you walk me through this total line by line?'")
    lines.append("Note who you spoke with and what they promised - phone memory fades within a day.")
    return "\n".join(lines).rstrip() + "\n"


def _load_spec(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        reason = str(exc) or exc.__class__.__name__
        raise BillCheckError(f"could not read {path}: {reason}")
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BillCheckError(f"{path} is not valid JSON: {exc.msg} on line {exc.lineno}")
    return spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_bill_math.py",
        description="Check bill arithmetic and flag things worth asking about (offline, standard library only).",
    )
    parser.add_argument("input", help="path to a JSON bill input file")
    parser.add_argument("--json", action="store_true", help="print the report as JSON instead of text")
    args = parser.parse_args(argv)

    try:
        spec = _load_spec(Path(args.input))
        report = check_bill(spec)
    except BillCheckError as exc:
        print(f"untangle-a-bill: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        sys.stdout.write(render_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
