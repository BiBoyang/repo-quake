# PR 草稿 B：microsoft/eval-guide

**Title:** Fix stale asset paths in orient docs and unquotable YAML in two skill descriptions

**Body:**

Two small correctness fixes, both verified against current main (7a22a89):

## 1. Stale paths in orient rebuild instructions

In `skills/eval-guide/SKILL.md` ("When to rebuild the static HTML"), the sentence that
runs `python dashboard/build-orient.py` lists the files to watch as `templates/orient.html`,
`templates/base.html`, and `examples/stage-orient-data.json` — without the `dashboard/`
prefix the same sentence uses for the script itself. Relative to the SKILL.md location,
those paths don't exist; the files live at `dashboard/templates/` and `dashboard/examples/`.
Looks left over from before the directory move. This PR adds the missing prefix.
(The docstring inside `dashboard/build-orient.py` uses the same short paths, but they are
valid relative to the script's own directory, so it is left unchanged.)

## 2. Two SKILL.md frontmatters are not valid YAML

The `description:` values in `skills/eval-guide/SKILL.md` and
`skills/eval-suite-planner/SKILL.md` are plain (unquoted) scalars containing `": "`,
which strict YAML parsers reject:

```python
import re, yaml
fm = re.match(r'^---\n(.*?)\n---\n', open('skills/eval-guide/SKILL.md').read(), re.S).group(1)
yaml.safe_load(fm)  # yaml.YAMLError: mapping values are not allowed here (line 2, col ~289)
```

2 of the 6 skills in the repo are affected; the other four parse fine. Any tooling that
parses frontmatter with a strict YAML parser (rather than a lenient regex) can't read
these two skills' metadata. Fix: single-quote both description values (no content change).
