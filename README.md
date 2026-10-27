# Everyday Agent Skills Pack

Six small, well-tested agent skills for daily life: weekly planning,
appointments, kind letters, bills, learning, and messy folders.
Written for beginners and low-energy days - plain English, step by
step, never condescending.

A skill is a folder with a `SKILL.md` inside it. The frontmatter says
what the skill does and when an agent should use it; the body walks the
agent through the job. This pack follows the conventions taught by
[agent-skill-starter](../agent-skill-starter/) - the tutorial scaffold -
but ships finished, worked skills instead of a template.

## What's inside

```text
everyday-agent-skills-pack/
├── skills/                        the product: one folder per skill
│   ├── plan-my-week/              tasks + capacities -> gentle weekly plan
│   ├── prep-my-appointment/       visit facts -> one-page brief with gaps flagged
│   ├── draft-a-kind-letter/       kind letters + a tone and readability check
│   ├── untangle-a-bill/           bill items -> math check + phone-call prep
│   ├── learn-one-thing/           big subjects -> one done-today slice + plan
│   └── declutter-a-folder/        read-only folder audit -> archive plan
├── docs/
│   ├── using-the-pack.md          three ways to use it, offline
│   └── adding-a-skill.md          eight-step recipe for new skills
├── tools/
│   └── validate_skill.py          offline skill linter, standard library only
├── tests/                         offline pytest suite, one file per skill
├── README.md                      this file
├── LICENSE                        MIT - Asdale Dynamics, LLC
└── STATUS.md                      build notes and verification results
```

## The skills

| Skill | In one line | Script it ships |
| --- | --- | --- |
| plan-my-week | A weekly plan that respects real capacity, marks one start-here step per day, and shows overflow honestly. | `draft_week_plan.py` |
| prep-my-appointment | A one-page visit brief - bring, ask, want to leave with - that flags missing facts instead of inventing them. | `make_visit_brief.py` |
| draft-a-kind-letter | Thank-you, apology, and kind complaint drafts with a tone check for stiff phrases, shouting, and walls of words. | `letter_check.py` |
| untangle-a-bill | Checks a bill's arithmetic, flags fees worth asking about, and builds a short phone script - it never accuses without proof. | `check_bill_math.py` |
| learn-one-thing | Shrinks "learn Python" into one finishable 20-minute thing with a done-line. | `scope_one_thing.py` |
| declutter-a-folder | A read-only folder audit with duplicate and old-file candidates, plus a keep-or-archive plan that deletes nothing. | `folder_audit.py` |

Every skill version is `1.0.0` in its frontmatter `metadata`.

## Quickstart: three commands, no network

```bash
# 1. Lint every skill strictly (exit 0 = healthy)
python tools/validate_skill.py --strict skills/

# 2. Install pytest (one-time, the only dev dependency)
python -m pip install -r requirements-dev.txt

# 3. Run the full offline test suite
python -m pytest
```

Or run a skill's script yourself - see `docs/using-the-pack.md` for
the six one-line commands and their JSON input shapes.

## What the validator checks

`tools/validate_skill.py` lints skill folders and reports ERRORs and
WARNs with short codes (`name-mismatch`, `secret-found`, ...). It
checks that SKILL.md exists with well-formed frontmatter, that
`name` matches the folder, that `description` reads third-person and
stays under 1024 characters, that the body has instructions, that any
`scripts/`/`references/`/`assets/` file the body mentions actually
exists, and it scans every skill file for common secret patterns and
stray email addresses - a pack that passes `--strict` has no known
personal data inside. Full rule list lives in the validator docstring.

## How the tests work

Each skill gets its own test file that covers the happy path, the
honest failure paths (broken input, missing files, big or vague
goals), and one boundary assert (the skill text says what it refuses
to do). A pack-level file guards the structure: every skill has
worked examples and failure-shaped prompt references, README and
LICENSE line up, scripts import only the standard library, and a
repo-wide secret sweep comes back clean. Fixtures are built in
temporary folders, so testing touches nothing real.

## Privacy and safety ground rules

- Scripts read only the files you point them at, write nothing, and
  make zero network calls.
- The folder auditor reads file metadata, never file contents, and
  cannot delete, move, or rename anything.
- No skill gives legal, financial, medical, or mental-health advice;
  each one names its boundaries in the SKILL.md text.
- No personal data of any kind ships in this repository.

## Requirements

- Python 3.9+ (standard library only; runs offline, no installs)
- pytest 7+ to run the tests (`requirements-dev.txt`)

## Credits

Built by **Asdale Dynamics, LLC** as part of a beginner-friendly AI
toolkit - AI explained like a friend would: plain English, step by
step, never condescending. You will find the same voice in *The
Massive AI Manual* and around the hub at `dylanasdale.github.io`.

The skill format follows the free `agent-skill-starter` template
(same author); this pack is the finished-goods version.

MIT licensed - see `LICENSE` (`Copyright (c) 2026 Asdale Dynamics, LLC`).
