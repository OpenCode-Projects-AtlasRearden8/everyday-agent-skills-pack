# declutter-a-folder: worked example output

Given a Downloads folder with a duplicate-name pair, old installers,
and one empty file, the reply is shaped like this:

```text
Folder audit: /home/pat/Downloads
Files found: 214 (486.3 MB)

## By extension
- pdf: 61
- jpg: 37
- zip: 12
- exe: 6
- docx: 14
(no others; full counts in the script output)

## Largest files (archive-candidates are often here)
- windows-installer-x64.iso (3.2 GB)
- vacation-2025-photos.zip (214.0 MB)
- paper-draft-final-v2.docx (1.4 MB)

## Oldest files (forgotten, probably safe to archive)
- receipt-scans-2019.pdf (modified 2019-10-04)
- old-resume.docx (modified 2020-02-11)

## Empty files (safe archive candidates)
- . (that untitled file at the top)

## Same-named files (compare before merging; the audit shows name only)
- taxes-2024.pdf
    taxes/taxes-2024.pdf
    downloads-old/taxes-2024.pdf
```

The reply then proposes, using that audit:

1. Five buckets, named for this person: Keep, Archive-2026-10,
   Trash-later (the installer ISO only, re-downloadable), Still-unsure,
   Named-seeds (receipt scans, tax folders, the tax PDFs themselves).
2. An archive move, not a delete: the ISO goes to `Trash-later` and
   nothing gets erased for thirty days.
3. The one next step: "tomorrow, pull everything dated before 2024
   into Keep-or-Archive for ten minutes."
