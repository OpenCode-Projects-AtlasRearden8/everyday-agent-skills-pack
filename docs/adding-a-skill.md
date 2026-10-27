# Adding a skill to this pack

## Eight steps, fully offline

1. Copy any existing skill folder to `skills/<your-name>`; make the
   folder and the frontmatter `name:` the same lowercase-hyphen string.
2. Write the `description:` first: "Does X. Use when Y.", third person,
   under 1024 characters. This line decides whether agents ever use it.
3. Write the body: one-sentence opener, "When to use it" triggers,
   numbered steps, "Boundaries" (what the skill refuses to do), and an
   "Output format" section.
4. If the skill has helper code, put it in `scripts/` as a standard
   library-only Python file that flags are optional-friendly, prints
   human output by default, offers `--json`, and exits nonzero with a
   friendly one-line error for bad input.
5. Put long detail in `references/` and input shapes in `assets/`,
   then mention each file by its path so the validator checks it.
6. Add `references/example-output.md` (a real worked example verified
   against the script) and `references/failure-prompts.md` (prompts
   that break the skill, with the honest handling for each).
7. Write `tests/test_<your-name>.py`: the strict validation assert,
   happy paths, failure paths, and one boundary-text assert.
8. Run and only stop when all of these pass:

   ```bash
   python tools/validate_skill.py --strict skills/<your-name>
   python -m pytest
   ```

   Then add the skill to the README list and bump its
   `metadata.version` if you changed it later.
