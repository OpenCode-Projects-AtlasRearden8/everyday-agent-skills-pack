# plan-my-week: worked example output

Input (week with a bill due, a call due, and three loose tasks):

```json
{
  "week_of": "2026-03-09",
  "days": [
    {"day": "Monday", "capacity_minutes": 60},
    {"day": "Tuesday", "capacity_minutes": 90},
    {"day": "Wednesday", "capacity_minutes": 60}
  ],
  "tasks": [
    {"name": "Pay water bill", "minutes": 15, "energy": "low", "due": "Monday"},
    {"name": "Call pharmacy refill", "minutes": 20, "energy": "high", "due": "Tuesday"},
    {"name": "Draft renter letter", "minutes": 45, "energy": "medium"},
    {"name": "Grocery order", "minutes": 30, "energy": "low"},
    {"name": "Backup photos", "minutes": 90, "energy": "medium"}
  ]
}
```

Output:

```text
Week plan (draft) - week of 2026-03-09

## Monday (60 min planned)
- [ ] Pay water bill (15 min, low energy, due this day)
- [ ] Draft renter letter (45 min, medium energy)
  -> Start here: Pay water bill

## Tuesday (90 min planned)
- [ ] Call pharmacy refill (20 min, high energy, due this day)
- [ ] Grocery order (30 min, low energy)
  -> Start here: Call pharmacy refill

## Wednesday (60 min planned)
- (open day - protected space)

## Overflow - did not fit; pick what slips
- Backup photos (90 min, medium energy)
```

Notice what the draft does on purpose:

- Monday takes its 15-minute due item, then exactly one 45-minute task,
  and stops at its 60-minute capacity.
- Wednesday stays open; an open day is protected space, not lazy planning.
- "Backup photos" (90 minutes) did not fit any single day, and the plan
  says so plainly instead of splitting the burden silently.
