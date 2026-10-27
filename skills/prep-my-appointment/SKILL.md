---
name: prep-my-appointment
description: Builds a one-page appointment brief with the visit details, a bring list, and questions to ask, while flagging every missing fact instead of inventing it. Use when someone has an upcoming appointment and wants to walk in prepared, not flustered.
metadata:
  version: 1.0.0
license: MIT
---

# prep-my-appointment

Turn "I have a thing coming up and my stomach is in knots" into one page:
what the visit is, what to bring, what to ask, and what is still unknown.

## When to use it

Use this skill when someone mentions an upcoming appointment of any kind:

- "I see the doctor Thursday, help me not forget my questions."
- "I am meeting the apartment manager about the lease; what do I bring?"
- "First visit to the tax preparer - what should take with me?"

## How to do it

1. **Name the visit cleanly.** One line: kind of appointment, the place,
   and the date when known. Requests without a date still get a brief;
   just mark the date "to confirm".

2. **Sort wants into two groups.** "Wants to ask" and "wants to get"
   (a form, a refill, a decision, a discount). A visit that ends with an
   unchecked want feels like a waste even if it went fine.

3. **Build the brief.** Fill in the JSON shape below and run

   ```
   python scripts/make_visit_brief.py visit.json
   ```

   See `assets/visit-input.md` for the exact field rules. The script
   refuses to invent anything: missing facts come back as a "still
   need you to find this" list.

4. **Turn worries into questions.** Restate each anxious sentence the
   person offers ("I am scared they will say my pain is weird") as a
   neutral question they can read off the page ("Is this symptom one
   you have seen before?").

5. **List what to bring - physically.** Cards, papers, bottles, devices,
   glasses. Prefer items named by the office or venue; where you do not
   know, say "call and confirm" rather than guessing a policy.

6. **End with a small pre-visit ritual.** One action the night before
   (pack the bag) and one when arriving (read your questions aloud).
   Anxiety shrinks when the next step is physical.

## Boundaries

- Never produce medical, financial, or legal advice; the questions are
  for the person to ask a real professional.
- Never state what an office or facility requires - that belongs to the
  confirmed source. Unknown policies are listed under "to confirm".
- No guessing at dates, addresses, medication names, or case numbers.
- Keep the brief to one page; a binder is not a prep sheet.

## Output format

Match `references/example-output.md`: visit line, punchy sections
(bring, ask, get, still need to find), and one pre-visit action. The
prompt shapes that go wrong, and the honest repair for each, live in
`references/failure-prompts.md`.
