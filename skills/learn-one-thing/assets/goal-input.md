# learn-one-thing input format

The script reads one JSON object:

```json
{
  "goal": "Learn Python",
  "minutes": 20,
  "who": "beginner"
}
```

Field rules:

- `goal` is required, free text, plain language.
- `minutes` is optional (default 20). It must be a positive number; the
  script treats anything under 5 as "yes, still possible, but tiny".
- `who` is optional (default "beginner"). The script uses it only to
  shape the draft slice, not to grade the person.

The scope check is deliberately conservative: a goal it reads as broad
comes back with narrower draft slices and no plan, because a plan for a
field-sized goal is decorative.
