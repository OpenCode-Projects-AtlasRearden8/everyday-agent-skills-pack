---
name: learn-one-thing
description: Shrinks an overwhelming learning goal into one small thing a person can actually finish today, then hands back a 20-minute plan with a do-it task and a recall question. Use when someone wants to learn AI, a tool, or a new subject but is drowning in options or has ten spare minutes.
metadata:
  version: 1.0.0
license: MIT
---

# learn-one-thing

Turn "I should learn Python (or spreadsheets, or AI agents, or chess
endgames)" into one small, finishable thing for today - and give it a
defined done-line so finished actually happens.

## When to use it

Use this skill when someone says, or means:

- "I want to learn AI but I do not know where to start."
- "I have twenty minutes, what should I learn right now?"
- "I have three courses bookmarked and I have opened none of them."

## How to do it

1. **Reject the field, pick the thing.** A subject (cooking, coding) is
   not a thing to learn; a thing is small enough to be done. "Print
   today's date with Python in one file" is a thing. Help the person
   notice the difference by example, not lecture.

2. **Run the scope check.** Put the goal and the spare minutes into the
   JSON shape from `assets/goal-input.md` and run

   ```
   python scripts/scope_one_thing.py goal.json
   ```

   The script decides whether the goal fits the minutes, and if it does
   not, suggests narrower slices - each with a verb, an object, and a
   done-line. A slice suggestion is a draft for the person to accept or
   edit; only they know what is usable.

3. **Choose one source.** One link, one chapter, one doc page for the
   thing. Two sources is a safety float for a factual question; three
   is avoidance. When there is no good offline source, say the plan's
   first step is "find the source" and stop there.

4. **Write the plan in four steps.** Skim (look for the shape of the
   thing, 5 minutes), do (actually do it, the longest step), break (the
   moment the plan will realistically die, name it now), tell (say back
   what was learned in one sentence). Without "tell", learning leaks.

5. **Name where it fits.** A learning plan without a time is a wish.
   Anchor it to something that already happens: after lunch, right
   after opening the laptop, while the kettle is on.

6. **Keep the done-line honest.** "Understand regex" is not a done-line;
   "change one pattern until it matches my receipt dates" is. If the
   goal cannot produce a done-line, the goal is still too big.

## Boundaries

- Never claim mastery for the person, or promise a career outcome.
- Never schedule what the person did not say they have minutes for.
- No path ranking of resources the skill has never seen; say what
  makes a source good instead.
- Limited budget does not mean limited learning; do not up-sell
  paid courses by default.

## Output format

Match `references/example-output.md`: goal, the one thing, the done
line, four steps with minutes, and Where it fits. Prompt shapes that
go wrong - cram-it-all, certification pressure, comparison despair -
and the repairs, live in `references/failure-prompts.md`.
