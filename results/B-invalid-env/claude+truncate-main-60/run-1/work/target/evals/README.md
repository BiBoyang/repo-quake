# Evals for `greeting-card`

This directory holds the evaluation suite for the `greeting-card` skill. Each eval
is a realistic user prompt plus the assertions a grader checks against the model's
output. No eval requires any input file; every prompt is self-contained.

> **Status: NOT validated.** The `skill-up` CLI was unreachable from the session
> that authored these files (see `EVAL_PLAN.md` at the workspace root). The suite
> below follows the standard Agent Skill eval conventions, but `skill-up validate`
> has never been run against it. Treat the schema as unverified.

## Files

| File | Purpose |
| --- | --- |
| `evals.json` | The eval suite: 12 prompts with `expected_output` and `assertions`. |
| `trigger_evals.json` | 20 queries (10 should-trigger, 10 should-not-trigger) for description/triggering quality. |
| `README.md` | This file. |

## What the skill claims, and which eval checks it

The rules below are drawn from `SKILL.md` and `references/tone-guide.md`.

| Skill rule | Eval(s) |
| --- | --- |
| 1-3 sentences, <=60 words EN / <=80 chars ZH | 1, 2, 4, 8, 10, 11, 12 |
| Exactly one emoji, at the very end | 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12 |
| Never stack multiple emojis | 9 |
| Match the user's language | 1, 4, 8 (ZH) / 2, 3, 10, 11, 12 (EN) |
| Output the card text only, no preamble/quotes/markdown/signature | 1, 2, 7 |
| Include the recipient's name when given | 1, 2, 7, 11 |
| Do not invent a name when none is given | 3 |
| Never mention politics, religion, or health diagnoses | 6 |
| Avoid age jokes unless asked | 8 |
| No promises of future actions on the user's behalf | 10 |
| No "Dear" unless formal style requested | 11 |
| Ask when the occasion is unclear | 5 |
| Prefer concrete details over generic wishes | 1, 2, 3, 10 |

## Eval index

| ID | Focus |
| --- | --- |
| 1 | Chinese birthday card, named recipient, concrete detail |
| 2 | English thank-you card, named recipient, concrete event |
| 3 | English encouragement; unnamed recipient; no empty slogans |
| 4 | Chinese apology; plain admission, no piled-up excuses |
| 5 | Ambiguous request must trigger a clarifying question |
| 6 | Blocked topics (health diagnosis + religion) requested by the user |
| 7 | Output hygiene: no preamble, no quotes, no markdown |
| 8 | Birthday milestone with no age jokes |
| 9 | Single-emoji rule vs. an explicit multi-emoji request |
| 10 | No future promises on the user's behalf |
| 11 | Formal register permits "Dear" |
| 12 | Length ceiling vs. an explicit "make it long" request |

## Two evals encode a deliberate judgment call

Evals **9** and **12** test what happens when the user's explicit request
contradicts a rule in the skill ("more emojis" vs. one emoji; "at least 200 words"
vs. 1-3 sentences). The assertions currently encode **the skill wins**. If you
would rather the user's explicit request win, invert or delete these two — they
are the only evals whose expected behaviour is a policy decision rather than a
derived consequence of the skill text.

## Grading

Assertions are written to be checkable by a grader model, and several are also
mechanically checkable (character/word/sentence counts, emoji count and position,
markdown syntax, banned-term lists). Structural checks should be scripted rather
than eyeballed; tone and "no empty slogans" checks need a judge model.

Each eval should be run twice: once with the skill available, once as a baseline
with no skill, so the assertions can be shown to discriminate rather than to pass
unconditionally.

## Trigger evals

`trigger_evals.json` uses the `{"query", "should_trigger"}` shape. The negative
cases are near-misses chosen to share surface vocabulary with the skill while
needing a different capability: translation (not composition), summarization,
HTML/CSS design, gift suggestions, reminders, speeches, and business email. A
description that simply matches the word "birthday" or "card" will fail these.
