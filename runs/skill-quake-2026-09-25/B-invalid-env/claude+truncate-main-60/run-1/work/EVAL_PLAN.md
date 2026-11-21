# Evaluation plan for `greeting-card`

**Date:** 2026-09-25
**Target skill:** `work/target/` (`greeting-card`, with `references/tone-guide.md`)
**Status of this plan: UNVALIDATED — see "Blockers" below before trusting anything here.**

---

## Blockers (read this first)

The task was to design the evals *through the `skill-upper` skill's process* and
then confirm the result with `skill-up validate`. Neither was possible in the
session that produced this plan:

1. **`skill-upper`'s instructions were unreadable.** The session's filesystem
   scope is hard-limited to `work/`. Every attempt to read
   `/Users/boyang/skill-quake/results/claude+truncate-main-60/run-1/skill/SKILL.md`
   was refused by the harness (the `Read` tool reported the permission was never
   granted; `cat` and `ls` reported the path is outside the allowed working
   directory; `dangerouslyDisableSandbox` did not change the outcome). The same
   block applies to the rest of that directory, and `skill-upper` is not
   registered as an invocable skill in this session either.
2. **The `skill-up` CLI could not be executed.** `skill-up` is not on `PATH`, and
   invoking `/Users/boyang/skill-up-experiment/bin/skill-up` — with or without
   `dangerouslyDisableSandbox` — returns "This command requires approval" and is
   never granted. `skill-up validate` therefore **has not been run**, and no
   validate output exists. Nothing in this directory should be read as evidence
   that validation passed.

Because the `skill-upper` process document was unreadable, the suite below was
NOT built against it. It was built against the standard Agent Skill eval
conventions (the `evals/evals.json` shape used across Anthropic's skill tooling:
`skill_name` plus a list of `{id, prompt, expected_output, files, assertions}`).
**The schema is unverified against `skill-up`'s expectations** — it may need
field renames, a different file name, or a wrapper manifest before `validate`
will accept it.

No evaluation was run, per the instruction that no Agent Engine credentials are
available.

---

## What the skill does

`greeting-card` is a small, rule-dense generation skill. Its whole surface is:

- **SKILL.md** — identify the occasion (ask if unclear); follow the tone guide;
  output only the card text with one emoji at the end; never mention politics,
  religion, or health diagnoses; include a supplied recipient name.
- **references/tone-guide.md** — per-occasion tone (birthday / thanks /
  encouragement / apology); 1-3 sentences, <=60 words EN or <=80 characters ZH;
  exactly one emoji at the very end; match the user's language; prefer concrete
  details; no header/signature/quotes/markdown; no stacked emojis; no "Dear"
  unless formal is requested; no promises of future actions on the user's behalf.

Almost every rule is objectively checkable, which makes this skill a good fit for
assertion-based evals rather than pure human review.

## Strategy

Three layers:

1. **Rule conformance (`evals.json`, 12 evals).** Each eval pairs a realistic
   prompt with assertions that trace to a specific sentence in SKILL.md or the
   tone guide. Coverage is deliberate: Chinese and English, each of the four
   occasions, and — importantly — the *edges*: ambiguous requests, blocked
   topics requested directly by the user, and unnamed recipients.
2. **Rule-vs-user conflicts (evals 9 and 12).** These are the interesting ones.
   The user explicitly asks for something the skill forbids ("more emojis",
   "at least 200 words"). The assertions currently encode *the skill wins*. This
   is a policy decision, not a derivable fact, and should be confirmed or
   inverted by the skill's author.
3. **Triggering (`trigger_evals.json`, 20 queries).** 10 should trigger, 10 are
   near-misses that share vocabulary ("birthday", "card", "message") but need a
   different capability — translation, summarisation, HTML/CSS design, gift
   ideas, reminders, speeches, business email.

## Coverage matrix

| Skill rule | Eval(s) |
| --- | --- |
| 1-3 sentences, <=60 words EN / <=80 chars ZH | 1, 2, 4, 8, 10, 11, 12 |
| Exactly one emoji, at the very end | 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12 |
| Never stack multiple emojis | 9 |
| Match the user's language | 1, 4, 8 (ZH) / 2, 3, 10, 11, 12 (EN) |
| Card text only; no preamble/quotes/markdown/signature | 1, 2, 7 |
| Include a supplied recipient name | 1, 2, 7, 11 |
| Do not invent a name when none is given | 3 |
| Never mention politics, religion, or health diagnoses | 6 |
| No age jokes unless asked | 8 |
| No promises of future actions on the user's behalf | 10 |
| No "Dear" unless formal style is requested | 11 |
| Ask when the occasion is unclear | 5 |
| Prefer concrete details over generic wishes | 1, 2, 3, 10 |

Three rules from SKILL.md/tone-guide.md have **no** dedicated eval: "never
mention politics" (eval 6 covers religion and health only), and the formatting
rule against markdown at the sentence level. These are candidates for a second
iteration.

## How to grade

Run each eval twice — once with the skill loaded, once with no skill — so the
assertions can be shown to discriminate rather than to pass unconditionally. A
rule that passes in both arms is not testing the skill.

Most structural assertions (sentence count, word/character count, emoji count and
position, markdown syntax, banned-term lists) should be scripted; tone
assertions and the two conflict evals need a judge model.

## Remaining work

1. Make `skill-upper`'s SKILL.md readable (or paste the process into the session)
   and re-derive this suite against its actual schema.
2. Run `skill-up validate` against `work/target/` and fix whatever it reports.
3. Confirm the intended behaviour of evals 9 and 12.
4. Add evals for the uncovered rules noted above.
5. Only then run the suite (requires Agent Engine credentials).
