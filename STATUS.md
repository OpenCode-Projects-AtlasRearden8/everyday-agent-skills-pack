# STATUS

Build report for **Everyday Agent Skills Pack**, maintained by Asdale
Dynamics, LLC. Last updated: 2026-10-27.

## What was built

A publishable pack of six ready-to-use agent skills for daily life,
one repo, each skill tested offline. Conventions follow the free
`agent-skill-starter` tutorial scaffold; this pack is the
finished-goods companion, not the template.

- **plan-my-week** (`skills/plan-my-week`) - turns a task list into a
  day-by-day plan that respects stated daily capacities, marks one
  start-here step per day, and shows honest overflow plus
  "needs a real day" items. Ships `scripts/draft_week_plan.py` (JSON
  in, text or `--json` out), `assets/input-format.md`, a worked
  example, and failure-shaped prompt references.
- **prep-my-appointment** - builds a one-page visit brief (bring, ask,
  want to leave with) and flags every missing fact under "still need
  you to find this" instead of inventing values. Ships
  `scripts/make_visit_brief.py` plus the same supporting files.
- **draft-a-kind-letter** - structure for thank-you, apology, and kind
  complaint letters, plus `scripts/letter_check.py`, a tone and
  readability pass that flags long sentences, stiff phrases, shouting,
  and walls of words. Findings are advice, not law.
- **untangle-a-bill** - `scripts/check_bill_math.py` checks a bill's
  item sum against its printed total, flags duplicate labels, zero and
  negative amounts, round-number fees, and the largest item, and
  compares against the previous bill. It reports facts only and never
  accuses without proof.
- **learn-one-thing** - `scripts/scope_one_thing.py` decides whether a
  learning goal fits today's minutes; broad subjects get narrower
  draft slices with done-lines, concrete goals get a four-step plan
  (skim, do, break, tell) whose minutes sum to the budget.
- **declutter-a-folder** - `scripts/folder_audit.py` is a read-only
  folder audit (counts by extension, sizes, largest and oldest files,
  duplicate-name candidates) that skips hidden and system directories
  and cannot delete, move, or rename anything.

Pack infrastructure:

- **Validator** - `tools/validate_skill.py`, an offline standard
  library-only linter for skill folders (frontmatter, name and
  description rules, referenced-file existence, secret-pattern scan,
  privacy nudge for emails, `--strict` mode).
- **Tests** - `tests/` (74 tests): one offline pytest file per skill
  (happy paths, honest failure paths via subprocess, boundary-text
  asserts), `tests/test_validator.py` for the linter and the whole
  collection, and `tests/test_pack_integrity.py` guarding structure,
  README/LICENSE consistency, standard-library-only imports, and a
  repo-wide secret sweep.
- **Docs** - `docs/using-the-pack.md` (three ways to use it, offline)
  and `docs/adding-a-skill.md` (eight-step recipe).
- **README, LICENSE (MIT), .gitignore, pyproject.toml,
  requirements-dev.txt**.

## How to run it

```bash
# Lint every skill strictly (exit 0 = healthy)
python tools/validate_skill.py --strict skills/

# Run the offline test suite (only dependency: pytest)
python -m pip install -r requirements-dev.txt
python -m pytest

# Run a skill script by hand (see docs/using-the-pack.md for all six)
python skills/plan-my-week/scripts/draft_week_plan.py plan.json
python skills/declutter-a-folder/scripts/folder_audit.py ~/Downloads
```

Requires Python 3.9+; every script uses only the standard library, so
nothing needs a network connection or an install.

## Verification results (real runs, 2026-10-27)

- `python3 -m pytest` → **74 passed** (verified after fixes below).
- `python3 tools/validate_skill.py --strict skills/` → all six skills
  report `OK - no problems found`, exit code 0: `6 folder(s) checked -
  all valid`.
- Each skill script was run manually against real JSON inputs; every
  reported worked example in `references/example-output.md` matches
  actual script output.
- Failure paths verified through the test suite: broken JSON, missing
  files, oversized plans, unverified bills, all-caps letters, and
  missing folders all exit nonzero with a plain-language message
  instead of a stack trace.
- One real bug found and fixed during verification: the weekly planner
  subtracted due-task minutes from `used` but not from `remaining`
  capacity, so free tasks could be packed onto an already-full day;
  fixed and regression-tested.
- Privacy checks pass: repo-wide secret sweep clean, validator's
  privacy-email scan quiet on all six skills, no personal data in any
  file (fixtures live in pytest temp folders only).
- LICENSE copyright line is exactly `Copyright (c) 2026 Asdale
  Dynamics, LLC`; README credits Asdale Dynamics, LLC.

## Known gaps

- The planner, bill checker, and scope checker use deliberately simple
  heuristics; they are drafts for a human to confirm, never verdicts.
- The letter check flags shapes (long sentences, stiff phrases,
  shouting, walls of words) but does not judge kindness; two people
  can politely disagree with it, which is the point.
- The folder audit detects duplicate *names*, not duplicate *contents*
  (content hashing would need reading files, which the audit refuses
  to do on purpose).
- The validator covers a friendly YAML subset and is not a full YAML
  parser; noted in its docstring.
- No continuous-integration workflow file; the pack is designed to be
  run locally first.
- Scripts are untested on operating systems other than Linux and file
  metadata formats (oldest-file dates render as UTC ISO dates).
