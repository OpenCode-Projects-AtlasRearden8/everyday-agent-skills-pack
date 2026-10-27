---
name: untangle-a-bill
description: Breaks a confusing bill into plain-English parts, checks the arithmetic, and builds a list of questions for the biller, without ever claiming an error that was not verified. Use when a bill makes no sense, looks higher than expected, or is scaring the reader.
metadata:
  version: 1.0.0
license: MIT
---

# untangle-a-bill

Take a bill that reads like soup and come out with three things: what
was actually charged, in plain words; whether the numbers even add up;
and a short spoken script for the phone call to the biller.

## When to use it

Use this skill when someone says, or means:

- "My electric bill is double last month and I do not understand it."
- "This hospital statement has fourteen line items and none of them match."
- "There is a 'regulatory recovery surcharge' on this bill - is that real?"

## How to do it

1. **Transcribe before you interpret.** Get each line item exactly as
   printed: label, amount, and any code or date range. Do not paraphrase
   labels yet - the real wording matters on the phone call.

2. **Check the arithmetic.** Enter the items and the printed total into
   the JSON shape from `assets/bill-input.md` and run

   ```
   python scripts/check_bill_math.py bill.json
   ```

   The script sums the items, compares against the stated total, flags
   duplicates, negative weirdness, and the biggest item, and calls out
   round-number charges - the usual suspects for fees that grew by
   accident or by policy.

3. **Translate, but keep the original.** Beside each line, put what it
   likely means in one plain phrase, clearly marked as your
   understanding: "evened out from last month". Guessing that hides the
   line's real meaning is worse than no gloss.

4. **Separate fact from hunch.** The arithmetic is fact. "This fee looks
   new" is a hunch and needs the biller's own history: the person, or
   you, comparing to last month's statement.

5. **Prepare the call, not a courtroom.** Three sentences to say, three
   questions to ask, and the account context written down first. Aim
   the call at understanding and a specific fix, not at winning.

6. **Write down the outcome before hanging up.** Who was spoken to, what
   they said, what happens next and when. Memory of phone calls fades
   in about a day.

## Boundaries

- Never tell someone they were cheated or overcharged as a fact; only
  the biller or a real comparison can make a charge an error.
- Never guess billing codes, tariff names, or regulation details.
- Not financial, legal, or medical-billing advice. Dispute processes
  and deadlines belong to official sources; name where to ask, never
  how it will go.
- Keep account numbers out of any file this skill produces.

## Output format

Match `references/example-output.md`: a plain table of the items, the
math check verdict, a short plain-English gloss per item, then the
call-prep block. The misfires this skill must not pick up, and the
recovery for each, are in `references/failure-prompts.md`.
