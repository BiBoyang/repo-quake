---
name: skill-upper
description: "Capture and review Agent Skill observations, and create, run, diagnose, or iteratively improve Skill evaluations (evals) with the skill-up CLI / 采集和审核 Agent Skill 观察，并使用 skill-up CLI 创建、运行、诊断或持续改进 Skill 评测. Use when the user asks to record explicitly attributed Skill usage or feedback; review observations; turn an approved observation into a regression case; evaluate, test, regress, verify, fix, improve, iterate, or evolve a Skill; add or strengthen eval cases; write eval.yaml/case.yaml; run skill-up run/validate/list-cases/report/import/init; or migrate from Anthropic evals.json. Observation capture and review require either the Codex skill-up plugin or an observer-enabled DSH skill-up plugin; evaluation remains multi-engine."
---

# use-skill-up-cli

Help the user evaluate and evolve Agent Skills through the `skill-up` CLI.

Manual: <https://alibaba.github.io/skill-up/>

## Language Policy

**Default to English when responding to the user. If the user writes in Chinese (or any other language), switch to that language and stay consistent with the user's input throughout the session.**

Detection rules (highest priority first):

1. The user explicitly specifies a language in the current message (e.g. "answer in English" / "用中文回答") → follow the user's instruction.
2. The natural language used in the user's current message → match it.
3. None of the above → use English (default).

Regardless of the response language, technical identifiers in this SKILL — CLI commands, `eval.yaml` / `case.yaml` field names, report field names, etc. — MUST stay in their original English form. Do not translate them.

### Language Rules for Generated Artifacts

When creating or editing `eval.yaml`, `case.yaml`, grading scripts, README snippets, final replies, or any other user-visible artifact, treat the language of the user's current message as the output language for this turn:

- If the user asks in Chinese, write the final response and all generated natural-language content in Chinese, including YAML comments, `title`, `description`, `input.prompt`, `expect` keywords, and `judge.criteria`.
- If the user asks in English, write the final response and all generated natural-language content in English, including YAML comments, `title`, `description`, `input.prompt`, `expect` keywords, and `judge.criteria`; do not leave Chinese or CJK characters in generated case files.
- If the target Skill itself is written in Chinese but the user asks in English, translate the Skill's functional intent into English test prompts and assertions instead of copying Chinese prose from the target Skill or templates.
- In an English context, deterministic keywords in `rule_based` cases, including `expect.must_contain` and `judge.success.output_contains`, must also be English keywords. Translate terms such as `资源泄漏`, `关闭`, and `异常处理` into `resource leak`, `close`, and `exception handling`; do not write bilingual parentheticals like `"资源" (resources)`.
- Keep technical identifiers unchanged, such as `schema_version`, `environment.type`, `engine.name`, `rule_based`, `agent_judge`, `script_path`, file paths, and commands.
- Generated YAML comments must use field-leading comments. Keep each comment short: one line for field meaning, plus one line for options only when useful.
- When listing options in comments, keep enum values unchanged, such as `none | opensandbox | docker` and `rule_based | agent_judge | script`.
- Treat `assets/*.tmpl` as structural references only. Rewrite placeholder prose and comments into the current output language; in an English context, translate or remove every Chinese comment and Chinese placeholder before writing generated files.
- `skill-up import` uses the CLI conversion path and does not preserve template comments; do not promise commented YAML for import-generated files.
- In an English context, after generating all files but BEFORE submitting the final reply, you **MUST perform a CJK self-check**: open every `evals/cases/*.yaml` and `evals/eval.yaml` and scan for CJK characters (Unicode ranges `\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\u3000-\u303f\uff00-\uffef`), including but not limited to `title`, `description`, `input.prompt`, `expect` keywords, `judge.criteria`, and YAML comments. If any CJK character is found, **replace it with an equivalent English expression before finishing the task**. This step is mandatory and must not be skipped.

## What is skill-up

`skill-up` is an evaluation CLI for Agent Skill authors. It installs the Skill into a real Agent Engine (Claude Code, Codex, qodercli, etc.), spins up an execution environment for each case, runs the prompt, then grades the result via declared rules / LLM judges / custom scripts, and finally produces a report.

Typical layout:

```
my-skill/
  SKILL.md
  evals/
    eval.yaml
    cases/
      <case-id>.yaml
    fixtures/
```

## When to trigger

Use this skill in any of the following situations:

- The user asks to "run / evaluate / verify / test this skill".
- The user asks to "fix / improve / iterate / evolve this skill" from eval failures.
- The user wants to "add evals, test cases, or regression cases to a skill".
- The user asks to record explicitly attributed Skill usage, evidence, or feedback.
- The user wants to review captured Skill observations or turn approved feedback into a regression case.
- The user wants to edit `eval.yaml` / `case.yaml`, or asks you to choose an appropriate `judge` type.
- The user mentions `skill-up run/validate/list-cases/report/import/init`.
- The user wants to migrate from Anthropic `evals.json` to skill-up.
- The current working directory contains `evals/eval.yaml` or `evals/evals.json` and the user wants to run it.

## Main flow (follow this order strictly)

### Observation capture mode (optional)

Use this mode when the user asks to record the current Skill interaction or
feedback and observation tools are available. It requires either a current
Codex release with the `codex-skill-up` plugin and lifecycle-hook support, or DSH with
the skill-up plugin's observer explicitly enabled. Do not retrofit observation
capture onto the pinned Codex 0.80.0 evaluation adapter.

If the user asks how to install either host plugin, or the required observation
tools are missing and the user asks to enable them, read
`references/install.md` under "安装 observation host plugin（可选）". Do not
install or enable a plugin unless the user asks.

Claude Code, qodercli, Qwen Code, and other Agent Engines are not supported for
this observation workflow. This restriction does not apply to normal `skill-up`
evaluation runs, which remain multi-engine.

1. Attribute the interaction only when the user explicitly references a Skill
   (for example, `$my-skill`) or the responsible Skill is otherwise known with
   certainty.
2. In Codex, if explicit attribution is absent but certain, call
   `mark_skill_invocation` once with the Skill name and optional version. DSH
   derives exact attribution from its durable `/skill` injection or successful
   `skill` tool result; do not add inferred attribution.
3. In Codex, use `attach_skill_evidence` only for references that help reproduce or
   evaluate the behavior. Prefer paths and short summaries over copied file
   contents.
4. In Codex, use `record_skill_feedback` during the observed turn. In DSH,
   wait until the completed turn has produced an observation, then use
   `record_observation_feedback` with its ID. Never invent sentiment or comments.

Both adapters redact common credential shapes before local persistence, but still
avoid sending secrets to marker tools. If the request is capture-only, stop
after recording it; do not edit, evaluate, commit, or publish a Skill unless
the user also asks for that work.

### Observation input mode (optional)

When the request starts from a captured Skill observation, read
`references/observations.md` first. Use the available observation tools to
inspect and preview the observation, require explicit approval for the exact
candidate, write it only after approval, and then continue at Step 4. If the
request does not start from an observation, use the normal flow below.

### Step 0: Make sure skill-up is installed

Before doing anything, verify `skill-up` is available:

```bash
command -v skill-up && skill-up --version
```

If a version is printed, continue. If you see `command not found`, on **macOS / Linux**:

```bash
curl -fsSL https://raw.githubusercontent.com/alibaba/skill-up/main/install.sh | bash

export SKILL_UP_VERSION=v0.1.0
curl -fsSL https://raw.githubusercontent.com/alibaba/skill-up/main/install.sh | bash

export INSTALL_DIR="$HOME/bin"
curl -fsSL https://raw.githubusercontent.com/alibaba/skill-up/main/install.sh | bash
```

> **Platform:** `skill-up` currently supports **macOS / Linux** only; Windows is not supported.

After installing, run `skill-up --version` again. If the command is still missing, add `~/.local/bin` to `PATH`.

More details, including optional Codex and DSH observation host plugins:
`references/install.md`.

### Step 0.5 (optional): User config and telemetry

For OTLP defaults, `runtime_kwargs` (e.g. OpenSandbox `base_url`), etc.:

```bash
skill-up init
skill-up init --local
skill-up init --print
skill-up init --force
```

Precedence (low → high): embedded empty defaults < user config < project `.skill-up.yaml` < `--config`. `SKILL_UP_CONFIG` can point at the user config file (env var name is historical). See the upstream README "User config".

### Step 1: Locate the target Skill

1. Identify the root directory of the target Skill (the directory containing `SKILL.md`). Search in this priority: user path → nearest `SKILL.md` upward from CWD → recently viewed files.
2. Read the target `SKILL.md` for scope, triggers, and dependencies. If the Skill is Chinese but the user writes in English, translate capabilities into English for prompts and assertions.
3. Check `evals/`:
   - `evals/eval.yaml` exists → Step 4 (optionally Step 3).
   - Only `evals/evals.json` → `references/migrate-anthropic.md` (`skill-up run --auto` or `skill-up import`).
   - Nothing → Step 2.

### Step 2: Scaffold the evals (only when none exist)

- Copy `assets/eval.yaml.tmpl` to `<skill-root>/evals/eval.yaml`.
- Copy `assets/case.yaml.tmpl` to `<skill-root>/evals/cases/<case-id>.yaml`.

Adapt language per "Language Rules for Generated Artifacts". In an English context, it is **prohibited** to copy Chinese placeholder text from the templates into generated files — all prose must be rewritten in English. The Chinese in the templates is for structural reference only, not to be carried over.
Preserve short field-leading comments in generated YAML. In Chinese context, rewrite those comments into Chinese while keeping field names and enum values in English.

Selection guidelines:

- `environment.type`: use `none` for pure-text Skills; use `opensandbox` when you need a remote sandbox (set `OPENSANDBOX_API_KEY`, put non-secrets in `environment.kwargs`).
