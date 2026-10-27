# prep-my-appointment: worked example output

Input:

```json
{
  "what": "Yearly blood pressure check",
  "where": "Riverside Family Clinic",
  "when": "Thursday, March 12, 3:00 PM",
  "arrive_early_minutes": 15,
  "cant_miss_bring": ["Photo ID", "Insurance card", "Home readings list"],
  "questions_to_ask": [
    "Is my home reading trend one you would act on?",
    "What side effects of a new medicine should send me back?"
  ],
  "outcomes_wanted": ["A next-check date", "A plain-language note I can read later"]
}
```

Output:

```text
Visit brief: Yearly blood pressure check

## The visit
- What: Yearly blood pressure check
- Where: Riverside Family Clinic
- When: Thursday, March 12, 3:00 PM
- Plan to arrive 15 minutes early

## Bring
- [ ] Photo ID
- [ ] Insurance card
- [ ] Home readings list

## Ask
1. Is my home reading trend one you would act on?
2. What side effects of a new medicine should send me back?

## Want to leave with
- [ ] A next-check date
- [ ] A plain-language note I can read later

## Before you go
Tonight: pack the bag and put it with your keys. Tomorrow at the door: read your questions out loud once.
```

Only an incomplete input gets a "still need you to find this" list. A
complete one does not, because no section politely pretends a gap exists.
