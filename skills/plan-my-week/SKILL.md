---
name: plan-my-week
description: Turns a messy list of tasks into a gentle, buffer-friendly weekly plan with one small first step per day. Use when someone feels buried by their week, keeps losing track of appointments and errands, or asks for a weekly plan without a lecture.
metadata:
  version: 1.0.0
license: MIT
---

# plan-my-week

Turn a jumbled pile of "this week I have to..." into a day-by-day plan
that leaves breathing room, puts first things first, and gives every day
one small, doable starting step.

## When to use it

Use this skill when someone says, or clearly means:

- "Help me plan my week, there is too much going on."
- "I keep forgetting appointments and the big thing keeps not happening."
- "Make a to-do plan that a tired person can actually follow."

## How to do it

1. **Collect the raw week.** Ask for (or find) three kinds of items:
   fixed appointments, tasks with real due days, and everything else.
   Estimate minutes for each task. Guess low when unsure; tired people
   underestimate the day, not the task.

2. **State the daily capacity out loud.** People usually have two to four
   focused hours. Ask how many good minutes per day feel realistic and
   write it down; never assume a full eight-hour day.

3. **Draft the plan.** Build a JSON file in the shape documented in
   `assets/input-format.md`, then run

   ```
   python scripts/draft_week_plan.py plan-input.json
   ```

   The script juggles tasks into days: due-date items land on their day,
   the rest are placed by size into the first day with room, and anything
   that does not fit goes to a visible overflow list instead of hiding.

4. **Shape the result like a friend would.** Read the script's draft and
   tighten it: put the heaviest-tiredness items early in the week, keep
   Monday light, and never fill a day past its capacity. Leave the
   overflow list visible and honest.

5. **Give each day one first step.** The smallest task of each day
   becomes that day's "start here" line. Starts beat schedules.

6. **Say what slipped.** If tasks overflowed, name them plainly and
   suggest one of: shrink the task, push it a day, or drop it with a
   reason. A plan that hides a real limitation will be abandoned by
   Wednesday.

## Boundaries

- Never plan past the stated capacity; a full-looking plan reads nice
  and crumples immediately.
- Never shame the overflow. Overflow means the week was overfull, not
  that the person failed.
- Do not invent appointments or dead dates the person never mentioned.
- No medical or mental-health advice; low energy is not a diagnosis.

## Output format

Match the worked example in `references/example-output.md`: a short
capacity line, day-by-day checkbox lists, one start-here step per day,
and an honest overflow section. Prompt shapes that commonly go wrong,
with the right recovery, are collected in `references/failure-prompts.md`.
