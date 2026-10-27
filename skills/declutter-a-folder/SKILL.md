---
name: declutter-a-folder
description: Audits a messy folder offline and returns an inventory, duplicate candidates, and a keep-or-archive plan that deletes nothing without the person's say-so. Use when a Downloads pile or projects folder is chaos, or someone is afraid to touch their files.
metadata:
  version: 1.0.0
license: MIT
---

# declutter-a-folder

Turn "I cannot find anything in Downloads" into an inventory, honest
duplicate candidates, and a sort plan that archives rather than
deletes - the person decides, the skill never touches their files.

## When to use it

Use this skill when someone says, or means:

- "My Downloads folder has 2,000 files and I am scared of it."
- "Do I have two copies of this tax folder?"
- "Help me clean up before my laptop dies; where do I even start?"

## How to do it

1. **Pick one folder, the smallest scary one.** Decluttering a whole
   computer is a project; one folder is an afternoon. Say this out
   loud before touching anything.

2. **Scan, do not sort by hand first.** Run

   ```
   python scripts/folder_audit.py ~/Downloads
   ```

   (or any folder path; add `--json` for the raw inventory). The script
   works offline with the standard library and writes nothing. It
   reports counts by extension, total size, largest files, oldest
   files, empty files, and duplicate-name candidates.

3. **Name the five buckets.** Decide the person's buckets before
   moving anything - typical ones are Keep, Archive, Trash-candidates,
   Still-unsure, Hardware-needed (drivers, installers). Moving without
   buckets is how files get lost.

4. **Archive, do not delete.** Empty files and obvious duplicates go to
   an `_archive` folder next to the sorted ones, dated by month.
   Deletion is the person's act alone, and only after a month in
   `_archive` without anyone missing the file.

5. **Protect the seed files.** Documents, photos, tax and medical
   paperwork, and one-of-a-kind files get named explicitly in the plan
   with a "keep, no discussion" mark. Bulk media is where mistakes are
   recoverable; seeds are not.

6. **End with one small next step.** Not "finish sorting 800 files",
   but "empty the Downloads inbox into Keep-or-Archive tomorrow for
   ten minutes". A finished afternoon beats an abandoned system.

## Boundaries

- This skill never deletes, moves, or renames a file; scripts only
  read and report.
- Never call anything trash except obvious installed-program leftovers
  the person can re-download.
- No cloud-upload advice unless asked, and then only naming the
  tradeoffs, not services.
- Scanning folders is fine; reading file *contents* to "check" them is
  not needed and is skipped.

## Output format

Match `references/example-output.md`: audit block, the five buckets
with counts, a short archive rule, and one next step. The misfires -
rename everything, delete at once, organize someone's photo collection
by date guessed from filenames - and the repairs, live in
`references/failure-prompts.md`.
