# letter check script: what it flags

`scripts/letter_check.py draft.md` reads a plain text or markdown draft
and reports findings as ERROR (fix or consciously keep) or WARN (worth a
look). It checks, offline and with the standard library only:

- long sentences: over 25 words, listed with their number
- jargon and stiff phrases: "pursuant to", "per our conversation", and
  friends from a small built-in list
- shouting: any sentence written in ALL CAPS
- a wall-of-words paragraph longer than 120 words with no break

Exit code is 0 for a readable draft, 1 for a draft with findings, 2 for
a file the script could not read. Findings are advice, not law; the
writer decides.
