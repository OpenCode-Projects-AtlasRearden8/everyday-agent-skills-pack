# plan-my-week input format

The script reads a JSON file. Here is the whole shape, with the defaults:

```json
{
  "week_of": "2026-03-09",
  "days": [
    {"day": "Monday", "capacity_minutes": 90},
    {"day": "Tuesday", "capacity_minutes": 120},
    {"day": "Wednesday", "capacity_minutes": 90},
    {"day": "Thursday", "capacity_minutes": 120},
    {"day": "Friday", "capacity_minutes": 60}
  ],
  "tasks": [
    {"name": "Pay water bill", "minutes": 15, "energy": "low", "due": "Monday"},
    {"name": "Call pharmacy refill", "minutes": 20, "energy": "high", "due": "Tuesday"},
    {"name": "Grocery run", "minutes": 60, "energy": "medium"}
  ]
}
```

Field rules:

- `tasks` is required; every task needs `name` and positive `minutes`.
- `energy` is optional (`low`, `medium`, `high`; default `medium`). The
  script records it so the agent can place draining tasks after easy ones.
- `due` is optional and must name a day that is also in `days`.
- `days` is optional. Without it the script invents Monday through Friday
  at 90 minutes each, which is a fine tired-person default.
- `week_of` is optional and free text; it shows up in the plan header.

The smallest valid input is a JSON file containing only `"tasks": []`.
