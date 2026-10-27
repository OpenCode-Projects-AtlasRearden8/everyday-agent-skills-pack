# prep-my-appointment input format

The script reads a JSON file shaped like this (all fields optional, but
the fewer facts you give, the longer the "still need" list gets):

```json
{
  "what": "Routine checkup with the clinic",
  "where": "Riverside Family Clinic",
  "when": "Thursday, March 12, 3:00 PM",
  "arrive_early_minutes": 15,
  "who_comes_along": " - ",
  "questions_to_ask": [
    "Is this symptom one you have seen before?",
    "What should I watch for after the test?"
  ],
  "cant_miss_bring": ["Photo ID", "Insurance card", "List of current medications"],
  "if_no_show_call": "the clinic's rescheduling line",
  "outcomes_wanted": ["A follow-up date before May", "A plain-language test explanation"]
}
```

Field rules:

- `questions_to_ask`: strings, one question per entry. The script prints
  them numbered.
- `cant_miss_bring`: strings, printed as a checkbox list.
- `outcomes_wanted`: strings. These become the "want to leave with"
  section, since visits are easier to steer with a destination.
- Missing `what`, `where`, or `when` are fine: they appear on the brief
  under "still need you to find this" rather than as invented values.

The smallest valid input is `{"what": "Appointment"}`.
