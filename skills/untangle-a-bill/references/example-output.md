# untangle-a-bill: worked example output

Input:

```json
{
  "bill_from": "Sunbird Electric",
  "bill_for": "March",
  "printed_total": 148.73,
  "previous_total": 91.02,
  "items": [
    {"label": "Energy charge", "amount": 89.14},
    {"label": "Transmission charge", "amount": 21.20},
    {"label": "Taxes", "amount": 12.19},
    {"label": "Regulatory recovery surcharge", "amount": 26.20}
  ]
}
```

Output:

```text
Bill breakdown - Sunbird Electric, March

## Items as printed
- Energy charge: $89.14
- Transmission charge: $21.20
- Taxes: $12.19
- Regulatory recovery surcharge: $26.20
Sum of items: $148.73

## Math check
The items add up to the printed total ($148.73). Whatever is wrong with this bill, arithmetic is not it.

## Worth asking about (facts, not accusations)
- Largest item: Energy charge at $89.14 - the first thing to ask about
- Nothing obviously odd in item shape; ask about the biggest item and any fee with a vague name

## Compared with last time
This bill is $57.71 higher than the previous one ($91.02).

## Before the call, write down
Your account or member number, the bill date, and one question: 'Can you walk me through this total line by line?'
Note who you spoke with and what they promised - phone memory fades within a day.
```

The worked reply adds one thing the script cannot do: a plain-English
gloss per item, clearly marked as an understanding. "Regulatory
recovery surcharge" becomes something like "likely a pass-through fee
the utility charges when regulators allow it - confirm on the call",
still wearing its maybe badge.
