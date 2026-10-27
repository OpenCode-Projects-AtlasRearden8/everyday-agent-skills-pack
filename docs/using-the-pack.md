# Using the pack (offline, three ways)

## What you need

Python 3.9+ and nothing else. Every script in this pack runs on the
Python standard library only; pytest is just for the tests.

## 1. Give a skill to an agent

Skills are folders with a `SKILL.md` inside. Copy a skill folder (for
example `skills/untangle-a-bill/`) into whatever location your agent
reads skills from, following your agent's own instructions. The
frontmatter `name:` and `description:` are what the agent reads to
decide when to reach for it.

Works the same way for: plan-my-week (a gentle weekly schedule),
prep-my-appointment (a one-page visit brief), draft-a-kind-letter
(warm, plain letters), untangle-a-bill (bill arithmetic plus phone
prep), learn-one-thing (a done-today slice of a big subject), and
declutter-a-folder (read-only folder audits with a keep-or-archive
plan).

## 2. Use the scripts yourself, without an agent

Each skill's helper script runs by hand. Typical calls:

```bash
python skills/plan-my-week/scripts/draft_week_plan.py plan.json
python skills/prep-my-appointment/scripts/make_visit_brief.py visit.json
python skills/draft-a-kind-letter/scripts/letter_check.py draft.md
python skills/untangle-a-bill/scripts/check_bill_math.py bill.json
python skills/learn-one-thing/scripts/scope_one_thing.py goal.json
python skills/declutter-a-folder/scripts/folder_audit.py ~/Downloads
```

Every script has a built-in `--json` flag for machine-readable output.
Input shapes are documented in each skill's `assets/` file. All of them
fail with a plain-language message instead of a stack trace when the
input is broken or missing.

## 3. Check the whole pack

```bash
python tools/validate_skill.py --strict skills/   # lints every skill
python -m pytest                                  # runs the full offline suite
```

Exit code 0 means everything is healthy. The validator also scans every
skill folder for common secret patterns and warns about stray emails,
so a pack that passes `--strict` has no known personal data inside.

## Privacy ground rules, so you can trust the pack

- Scripts read the files you point them at, and only those files; the
  folder audit reads file metadata, never file contents.
- Scripts write nothing anywhere; all output goes to your terminal.
- No network calls anywhere in the pack, no accounts, no tracking.
- Keep real account numbers, ID numbers, and medical specifics out of
  the JSON input files even so - write "account number" and fill it in
  by hand when you call.
