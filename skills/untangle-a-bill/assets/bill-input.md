# untangle-a-bill input format

The script reads a JSON file. Currency signs go outside the numbers:

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

Field rules:

- `items` is a required list; every entry needs `label` (non-empty
  string) and `amount` (a number). Zero amounts are allowed and get
  flagged; negative amounts are allowed and get explained back to you.
- `printed_total` is optional but recommended; the math check needs it.
- `previous_total` is optional; it powers the "how much bigger" note.
- `bill_from` and `bill_for` are optional labels for the header.

Repeating a label twice is allowed on purpose - some bills list the
same service twice - but the script calls it out so it is not missed.
