---
name: draft-a-kind-letter
description: Drafts warm, plain-English personal or small-business letters with a tone and readability check, then shows how the draft will read before it is sent. Use when someone needs to write a thank-you note, a kind complaint, a gentle apology, or any message they do not want to get wrong.
metadata:
  version: 1.0.0
license: MIT
---

# draft-a-kind-letter

Help someone say the hard-but-warm thing in a letter: a thank-you after
an interview, an apology to a neighbor, a firm-but-kind complaint about
a bill or a service, a note to a friend in a hard year.

## When to use it

Use this skill when someone asks:

- "Help me write a nice email to my landlord about the repair."
- "I want to thank her, but every draft sounds like a resume."
- "How do I complain about this mess without being ugly?"

## How to do it

1. **Ask for the letter's job in one sentence.** A letter does one job:
   thank, apologize, request, decline, or inform. A draft that tries two
   jobs does neither kindly.

2. **Name the feeling out loud.** One line: what the writer feels and
   what they want the reader to feel. Kindness is aimed, not sprayed.

3. **Draft the letter.** Plain language, short sentences, no sarcasm.
   Borrow structure from the worked examples in
   `references/example-output.md`, but write the actual sentences for
   this person's situation.

4. **Run the tone check.** Save the draft and run

   ```
   python scripts/letter_check.py draft.md
   ```

   The script counts words per sentence, flags jargon and shouting, and
   reports a small set of plain-English findings. Fix or overrule each
   finding on purpose - a good letter can ignore the linter, but should
   know why.

5. **Read the worst line first.** The line the writer is least sure of
   is the one the reader will feel. Rewrite it once, simpler.

6. **Offer one exact send-time choice.** Send now, sleep on it, or have
   another human read it. The writer chooses; the skill never emails.

## Boundaries

- Never send, post, or commit anything anywhere; output stays a draft.
- No flattery, no emotional manipulation, no scare words to get results.
- Keep specifics the person gave; never invent shared memories, dates,
  or promises ("as we discussed in March" only if they said March).
- Not legal or HR advice; a complaint letter is a request, not a claim.

## Output format

Match `references/example-output.md`: greeting, one-sentence purpose,
two or three short body paragraphs, a specific close, and a plain
signature line. The prompts that commonly go wrong - and what the draft
should never pick up from them - are in `references/failure-prompts.md`.
