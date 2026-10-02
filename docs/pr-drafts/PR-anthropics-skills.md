# PR 草稿 A：anthropics/skills

**Title:** skill-creator: quick_validate rejects empty name/description and checks referenced files exist

**Body:**

## Problem

`quick_validate.py` currently passes two damage classes that matter for skill integrity:

1. **Empty-string frontmatter values.** All format checks sit behind truthiness guards
   (`if name:` / `if description:`), so `name: ""` parses as an empty string, skips every
   check, and validates as "Skill is valid!". (Unquoted `name:` becomes `None` and is
   accidentally rejected by the type check — so the behavior differs by quoting style.)
2. **No reference-existence check.** SKILL.md may link to bundled files
   (`[guide](references/x.md)`) that don't exist on disk; nothing catches it.

## Repro (upstream main @ 8a1541c; quick_validate.py last touched in 1ed29a03)

```bash
mkdir -p /tmp/qv-demo/blank /tmp/qv-demo/dead-ref
printf -- '---\nname: ""\ndescription: ""\n---\n\n# T\n' > /tmp/qv-demo/blank/SKILL.md
printf -- '---\nname: t\ndescription: demo skill for validation.\n---\n\nSee [g](references/g.md).\n' > /tmp/qv-demo/dead-ref/SKILL.md
python3 quick_validate.py /tmp/qv-demo/blank      # before: "Skill is valid!"  after: rejects empty name
python3 quick_validate.py /tmp/qv-demo/dead-ref   # before: "Skill is valid!"  after: "Referenced file(s) not found: references/g.md"
```

## Change

- Reject empty `name`/`description` after stripping (presence of the key was already
  required; the value now must be non-empty too).
- Add a reference-existence check scoped to **markdown link targets** under
  `scripts/`, `references/`, `assets/`, skipping fenced code blocks and
  placeholder-looking paths. Inline-code mentions in prose are intentionally out of
  scope for a quick check — skill-creator's own SKILL.md uses illustrative example
  paths (e.g. `references/aws.md` in a routing pattern), and checking only link
  targets keeps false positives at zero (verified against skill-creator itself and
  several real-world skills).

## Context

Found during fault-injection experiments on skill integrity (blanking frontmatter,
deleting referenced attachments): the validator reported "Skill is valid!" for every
damaged variant. A community fork of skill-creator already ships a similar
`validate_path_references`; this brings the idea upstream in a false-positive-safe form.
