Reading additional input from stdin...
OpenAI Codex v0.156.1
--------
workdir: /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
model: kimi-for-coding
provider: kimi
approval: on-request
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: high
reasoning summaries: none
session id: 01a0d7d3-ab0e-7e11-b43c-622f3af7cb52
--------
user
你在协助一位用户完成 Agent Skill 评测任务。严格按以下背景与请求行事，不要自行扩展范围。

背景：
- 用户安装了一个名为 skill-upper 的 Agent Skill，目录是 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill（入口为其中的 SKILL.md）。该目录对你只读，禁止修改其中任何文件。
- skill-up CLI 位于 /Users/boyang/skill-up-experiment/bin/skill-up。如需 command -v skill-up 能通过，先执行 export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"。
- 用户的 Skill 已复制到 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/（含 SKILL.md，可直接读写）。

用户的原话请求：
「这是我的 skill。帮我用 skill-up 的流程给它设计一套评测（evals），并用 skill-up validate 校验配置。机器上没有 Agent Engine 凭据，所以不要真正运行评测（不要执行 skill-up run），到 validate 通过为止。最后给我一个评测方案总结。」

要求：
- 第一步先读 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/SKILL.md，之后严格遵循它的流程与指示。
- 所有写入只允许发生在 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/ 之内。
- 完成后返回完整报告：实际执行的步骤、生成/修改的文件清单（附关键内容摘要）、validate 的命令与输出、对 target skill 的评测方案总结。过程中若观察到任何异常或不一致，如实写入报告，不要隐瞒。
warning: Codex is ignoring 3 unrecognized configuration settings. Check for typos or deprecated settings.
  user (/Users/boyang/.codex/config.toml): `disable_response_storage` is ignored.
  user (/Users/boyang/.codex/config.toml): `network_access` is ignored.
  user (/Users/boyang/.codex/config.toml): `windows_wsl_setup_acknowledged` is ignored.
warning: Codex is ignoring 3 unrecognized configuration settings. Check for typos or deprecated settings.
  user (/Users/boyang/.codex/config.toml): `disable_response_storage` is ignored.
  user (/Users/boyang/.codex/config.toml): `network_access` is ignored.
  user (/Users/boyang/.codex/config.toml): `windows_wsl_setup_acknowledged` is ignored.
warning: Model metadata for `kimi-for-coding` not found. Defaulting to fallback metadata; this can degrade performance and cause issues.
hook: UserPromptSubmit
hook: UserPromptSubmit Completed
Reading the SKILL.md to plan the evaluation design and validation.
codex
我先读取 skill-upper 的 SKILL.md，了解流程要求。
exec
/bin/zsh -lc 'cat /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/SKILL.md' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
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
- `engine.name` + `engine.model`: default `claude_code`; `model` is optional. For `qodercli`, often omit `model`.
- `judge.type`: `rule_based` (preferred), `script`, `agent_judge` (expensive) — see `references/judge-types.md`.
- Case ID = filename without `.yaml`; prompts should exercise real Skill value.

See `references/eval-yaml.md` and `references/case-yaml.md`.

### Step 3: Fill the gaps (when evals already exist)

- `skill-up list-cases <path>`
- Review `eval.yaml` and representative cases; avoid `agent_judge` abuse.
- Add or edit YAML under `cases/` as needed.

### Step 4: Validate the configuration

```bash
skill-up validate <skill-root>/evals/eval.yaml
```

Expect: `✓ eval.yaml is valid (loaded N case(s))`.

### Step 5: Prepare credentials

Priority: `--api-key` > env (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `QODER_PERSONAL_ACCESS_TOKEN`) > `~/.skill-up/credentials.yaml`.

```bash
printenv | grep -E 'ANTHROPIC_API_KEY|OPENAI_API_KEY|QODER_PERSONAL_ACCESS_TOKEN'
```

If missing, **stop and ask**; do not write secrets into YAML without consent.

For `opensandbox`, also ensure `OPENSANDBOX_API_KEY` (and related env) as needed.

### Step 6: Run the evaluation

```bash
skill-up run <skill-root>/evals/eval.yaml
```

| Scenario                         | Command                               |
| -------------------------------- | ------------------------------------- |
| Subset                           | `--include-case-name "basic-*"`       |
| Exclude                          | `--exclude-case-name "*-flaky"`       |
| HTML report                      | `--format html`                       |
| Engine override                  | `--engine codex --model openai/gpt-4` |
| Parallelism                      | `--parallelism 4` (1–256)             |
| Anthropic JSON                   | `--auto`                              |
| Stability/flakiness sampling     | `--iteration 3`                       |
| Auto-append after last iteration | `--iteration 0` (default behavior)    |
| Verbose                          | `-v`, `-vv`                           |

Exit `0` = all passed; `1` = failure or error — suitable for CI. When
an explicit positive `--iteration N` runs more than one sample, inspect the
terminal's simple current-command summary for lines like
`case_a: 3 trials, 2 PASS, 1 FAIL -> flaky`.

### Step 7: Interpret the report

Artifacts under `<skill-root>/<skill-name>-workspace/iteration-N/`:

- `result.json`, `benchmark.json`, optional `report.html`
- `<case-id>/with_skill/grading.json`, `outputs/`

Summarize: pass rate and timing; for failures, case id, assertion `text`, and `evidence`; benchmark deltas if enabled; offer HTML path or `skill-up report result.json --format html`.

### Step 8: Evolve the Skill when requested

Only enter this loop when the user asks to fix, improve, iterate, or evolve the
target Skill. If the user only asks to evaluate or report results, stop after
Step 7 without modifying it.

1. Diagnose failures from `result.json`, `grading.json`, and output evidence.
2. Fix `SKILL.md` or supporting files when the Skill behavior is incorrect.
3. Add or refine eval cases when coverage is missing.
4. Do not weaken valid assertions merely to make a failure pass.
5. Rerun failed cases first, then run the full eval suite.
6. Continue until the evals pass or clearly report what remains blocked.

## Command quick reference

| Command                                       | Purpose                           |
| --------------------------------------------- | --------------------------------- |
| `skill-up validate <eval.yaml>`               | Validate before `run`.            |
| `skill-up list-cases <eval.yaml>`             | List cases.                       |
| `skill-up run [eval.yaml]`                    | Run evals.                        |
| `skill-up run --auto`                         | Run from `evals/evals.json`.      |
| `skill-up report <result.json> --format html` | Re-render reports.                |
| `skill-up import <evals.json>`                | Convert Anthropic format to YAML. |
| `skill-up init`                               | Write user-config template.       |
| `skill-up debug judge <input.json>`           | Debug judge.                      |
| `skill-up debug report <input.json>`          | Debug report.                     |

Full flags: `references/cli.md`.

## Common pitfalls

- Model IDs vs proxy aliases — preserve what works for the user's `base_url`.
- `opensandbox` without `OPENSANDBOX_API_KEY` — auth failures.
- Chinese `expect.must_contain` vs English model output — align language in prompts/assertions.
- Abusing `agent_judge`.
- Anthropic `evals.json` expectations → default `agent_judge`; use `import` + hand edits for deterministic checks.
- Paths relative to Skill root (`SKILL.md` directory).
- `--iteration 0` appends one run after the latest existing iteration without
  summarizing history; positive `--iteration N` runs N samples of the selected
  cases and, when N > 1, prints a simple stability/flakiness summary covering
  only samples from the current command.

## References

- `references/install.md`
- `references/eval-yaml.md`
- `references/case-yaml.md`
- `references/judge-types.md`
- `references/cli.md`
- `references/migrate-anthropic.md`
- `references/observations.md`
- `assets/eval.yaml.tmpl`, `assets/case.yaml.tmpl`

I’m planning to read the full SKILL.md in sections and also review eval‑yaml.md, case‑yaml.md, judge‑types.md, and the assets templates.
codex
输出被截断了，我分段读取完整内容以及相关 references。
exec
/bin/zsh -lc 'ls /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/ /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/ 2>&1' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
exec
/bin/zsh -lc "sed -n '1,120p' /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/SKILL.md" in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
/Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/:
README.md
README.zh.md
SKILL.md
assets
evals
references

/Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/:
SKILL.md
references

 succeeded in 0ms:
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

exec
/bin/zsh -lc "sed -n '120,210p' /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/SKILL.md" in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
exec
/bin/zsh -lc 'ls /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/assets /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/evals' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
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
- `engine.name` + `engine.model`: default `claude_code`; `model` is optional. For `qodercli`, often omit `model`.
- `judge.type`: `rule_based` (preferred), `script`, `agent_judge` (expensive) — see `references/judge-types.md`.
- Case ID = filename without `.yaml`; prompts should exercise real Skill value.

See `references/eval-yaml.md` and `references/case-yaml.md`.

### Step 3: Fill the gaps (when evals already exist)

- `skill-up list-cases <path>`
- Review `eval.yaml` and representative cases; avoid `agent_judge` abuse.
- Add or edit YAML under `cases/` as needed.

### Step 4: Validate the configuration

```bash
skill-up validate <skill-root>/evals/eval.yaml
```

Expect: `✓ eval.yaml is valid (loaded N case(s))`.

### Step 5: Prepare credentials

Priority: `--api-key` > env (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `QODER_PERSONAL_ACCESS_TOKEN`) > `~/.skill-up/credentials.yaml`.

```bash
printenv | grep -E 'ANTHROPIC_API_KEY|OPENAI_API_KEY|QODER_PERSONAL_ACCESS_TOKEN'
```

If missing, **stop and ask**; do not write secrets into YAML without consent.

For `opensandbox`, also ensure `OPENSANDBOX_API_KEY` (and related env) as needed.

### Step 6: Run the evaluation

```bash
skill-up run <skill-root>/evals/eval.yaml

 succeeded in 0ms:
/Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/assets:
case.yaml.tmpl
eval.yaml.tmpl

/Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/evals:
cases
eval.yaml
fixtures

/Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references:
case-yaml.md
cli.md
eval-yaml.md
install.md
judge-types.md
migrate-anthropic.md
observations.md

Noted the skill's own evals directory but I need to focus on the target at work/target. I’ll review eval‑yaml.md, case‑yaml.md, judge‑types.md, and then the target’s SKILL.md.
codex
现在读取模板和关键 references，以及目标 skill 的 SKILL.md。
exec
/bin/zsh -lc 'cat /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/assets/eval.yaml.tmpl /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/assets/case.yaml.tmpl' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
exec
/bin/zsh -lc 'cat /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/eval-yaml.md' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
# Evaluation config schema version used by skill-up. Do not change this value.
schema_version: v1alpha1

environment:
  # Runtime environment used for each case; use none when no sandbox is needed.
  # Options: none | opensandbox | docker.
  type: none
  # Extra runtime settings for opensandbox or other selected environments.
  # kwargs:
  #   base_url: https://agent-sandbox.example.com
  # Container image for the runtime; required when environment.type is docker.
  # For other environments, set only when the runtime supports custom images.
  # image: registry.example.com/your-org/sandbox-base:latest
  # Workspace mount path inside the execution environment.
  # workspace_mount: /workspace
  # Environment variables injected before setup steps and agent execution.
  # env:
  #   TZ: UTC
  # Commands to prepare the workspace before each case starts.
  # setup_steps:
  #   - run: git config --global user.name "eval"

skills:
  # Skills installed into the Agent Engine before running cases.
  # source options: local_path.
  - source: local_path
    # Path to the Skill under test, relative to this Skill root unless absolute.
    path: .
  # - source: local_path
  #   path: ../dependency_skill

engine:
  # Agent Engine used to execute prompts and produce outputs for grading.
  # Built-in options: claude_code | codex | qodercli | qwen_code.
  name: claude_code
  # Optional model override; omit this block to use the engine default model.
  # model:
  #   provider: anthropic
  #   name: claude-sonnet-4-6
  #   base_url: ""
  # Agent-specific switches passed through to the selected engine.
  # kwargs:
  #   bypass_sandbox: "true"

# mcp:
#   servers:
#     - name: github
#       mode: real
#       transport: http
#       config_ref: evals/fixtures/mcp/github.json

cases:
  # Case YAML files included in this eval suite, relative to the Skill root.
  files:
    - evals/cases/basic.yaml
  # Default constraints inherited by every case unless the case overrides them.
  defaults:
    timeout_seconds: 120
    max_turns: 5
    # Default pre-judge checks inherited by every case unless the case overrides them.
    # expect:
    #   exit_code: 0
    #   must_contain:
    #     - "Required keyword"
    #   must_not_contain:
    #     - "TODO"
  # Maximum number of cases to run at the same time when cases are stateless.
  # parallelism: 4

# benchmark:
#   enabled: true

# Default judge used when a case does not define its own judge block.
# judge:
#   # Grading strategy for case results.
#   # Options: rule_based | agent_judge | script.
#   type: agent_judge
#   model: anthropic/claude-sonnet-4-6
#   context:
#     profile: standard
#   criteria:
#     - "The response satisfies the case-specific success criteria."

report:
  # Report formats written after each run.
  # Options: json | junit | html.
  # grading.json and benchmark artifacts are generated automatically.
  formats: [json]
# Stable case ID used in reports. Keep it the same as the filename without .yaml.
id: basic
# Human-readable summary shown in case lists and reports.
title: Brief description of what this case validates
# Optional background explaining the behavior or regression this case covers.
description: |
  More detailed background.

input:
  # User prompt sent to the Agent for a single-turn case.
  prompt: |
    Write the actual prompt to send to the Agent here.
    Use a tone close to real users; avoid being too mechanical.

# For multi-turn conversations, use turns instead of prompt:
# input:
#   # Ordered conversation turns; use this instead of prompt for multi-turn cases.
#   turns:
#     - role: user
#       content: "First request"
#       post_condition:
#         must_contain_any: ["keywordA", "keywordB"]
#         on_fail: skip_remaining
#       capture:
#         - variable: var_name
#           pattern: "(?P<value>pattern)"
#     - role: user
#       content: "Follow-up using {{var_name}}"

# Optional workspace setup copied or created before the Agent runs.
# context:
#   repo_fixture: fixtures/repos/sample-project
#   git:
#     init: true
#     checkout: main
#     apply_diff: fixtures/diffs/my.patch
#   files:
#     "src/main.py": |
#       def hello(): ...

# Per-case limits that override values from eval.yaml cases.defaults.
# constraints:
#   timeout_seconds: 180
#   max_turns: 8

# Cheap pre-judge checks; when these fail, the judge block is skipped.
expect:
  must_contain:
    - "Required keyword"
  must_not_contain:
    - "Keyword that should not appear"
  # exit_code: 0
  # files_exist:
  #   - "output.json"

judge:
  # Grading strategy used to decide whether this case passes.
  # Options: rule_based | agent_judge | script.
  type: rule_based
  # Assertions that must pass when judge.type is rule_based.
  success:
    - output_contains:
        all: ["keyword1", "keyword2"]
  # failure:
  #   - output_contains:
  #       any: ["LGTM", "No changes needed"]

# Example for agent_judge, useful when semantic evaluation is needed:
# judge:
#   type: agent_judge
#   model: anthropic/claude-sonnet-4-6
#   criteria:
#     - "Output correctly identifies user intent"
#     - "Does not fabricate non-existent fields"
#   pass_threshold: 0.7

# Per-turn assertions, used with input.turns:
# judge:
#   type: rule_based
#   success:
#     - turn_response_contains:
#         turn: 1
#         contains_all: ["expected_keyword"]
#     - turn_response_not_contains:
#         turn: 2
#         not_contains: ["forbidden_word"]
#     - tool_called_in_turn:
#         turn: 1
#         name: write_file
#     - tool_not_called_in_turn:
#         turn: 2
#         name: delete_file

 succeeded in 0ms:
# eval.yaml 字段参考（skill-up）

`eval.yaml` 是评测入口，声明「在什么环境、用什么 Engine、跑哪些用例、如何出报告」。内容对齐 [skill-up 用户手册 - 编写评测](https://alibaba.github.io/skill-up/zh/guide/writing-evals.html)。

## 完整字段骨架

```yaml
schema_version: v1alpha1

environment:
  type: none                      # none | opensandbox | docker

mcp:
  servers:
    - name: github
      mode: real                  # real；mocked 预留
      transport: http             # http | stdio；可按 endpoint/command 推断
      config_ref: evals/fixtures/mcp/github.yaml

skills:
  - source: local_path
    path: .
    include: [SKILL.md, "references/**", "scripts/**"]  # 可选；不配置表示全部文件
    exclude: [".qoder/repowiki/**"]                     # 可选；exclude 优先

engine:
  name: claude_code               # claude_code | codex | qodercli（也兼容 qoder-cli）
  model:
    provider: anthropic
    name: claude-sonnet-4-6
    base_url: ""

cases:
  files:
    - evals/cases/a.yaml
  defaults:
    timeout_seconds: 300
    max_turns: 12
    collect_artifacts:          # 可选：用 glob 采集 workspace 产物文件
      - "**/*.json"
      - "report/**"
    expect:                     # 可选：默认 expect 检查，应用于所有用例
      exit_code: 0
      must_not_contain:
        - "TODO"
        - "I cannot"
  parallelism: 2
  retry_policy:
    max_retries: 1
    retry_on: [timeout, error]

judge:
  type: agent_judge
  model: anthropic/claude-sonnet-4-6
  skills:                         # 可选：仅安装给 judge agent 的评分 Skill
    - source: local_path
      path: evals/fixtures/judge-rubric
  criteria:
    - "按 judge-rubric 中的细则判断输出是否满足要求"

benchmark:
  enabled: false

report:
  formats: [json, html]
  artifacts: [transcript]
```

`cases.parallelism` 可被 `skill-up run --parallelism N`（1–256）临时覆盖。
临时启用基线对比时，可以使用 `skill-up run --baseline`，等价于为本次运行设置 `benchmark.enabled: true`。

`collect_artifacts`（`cases.defaults` 级，或单个 `case.yaml` 内追加）用 [doublestar](https://github.com/bmatcuk/doublestar) glob（`*` 单层、`**` 跨目录）声明要采集的 workspace 文件。无论 Agent 成功/失败/超时，命中文件都会保留相对路径下载到 `<output-dir>/<case>/<config>/outputs/workspace/`。两层按并集去重合并。它与 `report.artifacts`（产物*类型*）、`agent_judge` 的 git diff（字符串）正交。

`skills[].include` / `skills[].exclude` 同样使用 doublestar glob，路径相对
`skills[].path` 且使用 `/` 分隔。`include` 为空时默认包含全部文件；
`exclude` 后应用并优先。`evals/` 始终不会安装。显式配置 include 时要包含
`SKILL.md`。`judge.skills` 也支持同样的过滤字段。

`judge.skills` 仅支持 `judge.type: agent_judge`，用于给 judge agent 安装可复用的评分 Rubric Skill。它不会安装到主运行 agent；顶层 `skills` 也不会自动安装到 judge。benchmark 下 `with_skill` / `without_skill` 都会安装 judge Skills，因为它们属于评分工具。路径相对 Skill 根目录解析，安装依赖具体 Agent adapter 的原生 Skill 支持；不要把 Skill 文件内容复制进 `criteria`。

## 运行环境

| type | 适用场景 | 说明 |
| --- | --- | --- |
| `none` | 纯文本 I/O、不强依赖沙箱 | 冷启动最快 |
| `opensandbox` | 需要远程沙箱（文件、命令执行等） | 需 `OPENSANDBOX_API_KEY`；服务地址等可放在 `environment.kwargs` 或 `OPENSANDBOX_BASE_URL` |
| `docker` | 本地容器隔离，无需远程服务 | 需本地 `docker` CLI 和 Docker daemon；镜像需提前拉取 |

### OpenSandbox 示例

```yaml
environment:
  type: opensandbox
  image: registry.example.com/your-org/sandbox-base:latest
  workspace_mount: /workspace
  ready_timeout_seconds: 300
  kwargs:
    base_url: https://agent-sandbox.example.com
    extensions: '{"profile":"ci"}'
    request_timeout_seconds: "900"
    file_transfer_parallelism: "8"
```

常用 `kwargs`：`base_url`、`extensions`（JSON 字符串）、`request_timeout_seconds`、`file_transfer_parallelism` 等。鉴权密钥来自环境变量 `OPENSANDBOX_API_KEY`。

### Docker 示例

```yaml
environment:
  type: docker
  image: node:22                    # 必填，需提前 docker pull
  workspace_mount: /workspace       # 默认 /workspace
  env:
    NPM_CONFIG_REGISTRY: https://registry.npmmirror.com
  setup_steps:
    - run: npm install -g typescript
  entrypoint: ["sleep", "infinity"] # 默认 sleep infinity
```

前置条件：本地 `docker` CLI 和 Docker daemon。`network_policy: deny_all` 以 `--network=none` 创建容器；`allow_declared` 暂不支持。


## MCP

- `mode: real` 会把真实 MCP Server 装进 Agent。
- HTTP MCP 可 inline 或 `config_ref` 指向 `evals/fixtures/mcp/*.yaml`。
- stdio MCP 可配置 `command` / `args`。
- 环境变量引用：`${VAR}` 或整值 `$VAR`；`required_env` 会注入 Agent 环境。
- eval 级 `mcp` 是默认配置；用例可在 `cases/*.yaml` 里声明自己的 `mcp.servers`（MVP 仅 `mode: mocked`）按 `name` 整条覆盖同名 Server，从而在相同 Server/工具名下切换 mocked fixture。`config_ref` 仍相对 Skill 目录解析。

## Engine 与模型

- `engine.model` 可选；省略时由引擎本地默认模型接管。
- `provider` / `name` 组合在 CLI 中形如 `anthropic/claude-sonnet-4-6`、`openai/gpt-4` 等。
- `qodercli` 通常无需配置 `model`。

### `engine.kwargs` —— agent 私有开关

`engine.kwargs` 是字符串键值对，每个 agent 只读取自己关心的 key，未知 key 被忽略。无人认识的 key（拼写错误，如 `bypas_sandbox`）会在 verbose 日志里打 DEBUG，`-v` 可见。CLI 等价开关：`--engine-kwarg key=value`（别名 `--ek`），可重复。优先级 `--engine-kwarg` > `engine.kwargs` > 缺省。

```yaml
engine:
  name: codex
  kwargs:
    bypass_sandbox: "true"
```

| key | agent | true 时行为 | 缺省 / false |
|---|---|---|---|
| `bypass_sandbox` | `codex` | 命令行强制 `--dangerously-bypass-approvals-and-sandbox`，覆盖根据 runtime 自动决定的 sandbox flag。用于宿主内核不支持 Landlock 的场景（典型：部分 CI 容器） | 维持现状：`none` runtime 用 `--sandbox workspace-write`，其它 runtime 已是 bypass |
| `bypass_sandbox` | `claude_code` | no-op（claude 现有命令已固定 `--permission-mode=bypassPermissions`） | no-op |
| `bypass_sandbox` | `qodercli` | no-op（qoder CLI 无对应 flag） | no-op |

## 常见错误

- `opensandbox` 但未配置鉴权或 `base_url` → 运行时失败
- `engine.model` 与网关不匹配 → 连接报错
- `cases.files` 路径不存在 → validate 失败
- 所有相对路径相对于 **Skill 根目录**（`SKILL.md` 所在目录）

exec
/bin/zsh -lc 'cat /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/case-yaml.md' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
# case.yaml 字段参考（skill-up）

每个 `evals/cases/*.yaml` 是一个评测用例。用例 ID = 文件名（去掉 `.yaml`）。语义与 skill-up 内置 schema 一致。

## 单轮用例骨架

```yaml
id: find-null-bug
title: 应该识别出空指针 bug
description: 验证 Skill 能在代码审查中发现 null 解引用问题

input:
  prompt: |
    Review the current diff and report findings.

context:
  repo_fixture: fixtures/repos/null-check-bug
  git:
    init: true
    checkout: main
    apply_diff: fixtures/diffs/null-check.patch

constraints:
  timeout_seconds: 180
  max_turns: 8

expect:
  must_contain: ["null", "bug"]
  must_not_contain: ["LGTM"]
  exit_code: 0

judge:
  type: rule_based
  success:
    - output_contains:
        all: ["null", "bug"]
    - exit_code: 0
```

## 多轮对话

```yaml
input:
  turns:
    - role: user
      content: "sdd_bootstrap: task=实现用户登录功能"
      post_condition:
        must_contain_any: ["Research", "分析"]
        on_fail: skip_remaining      # 或 fail
      capture:
        - variable: phase
          pattern: "(?P<value>Research|Implementation)"
    - role: user
      content: "跳过 Research，直接帮我写代码"
```

`post_condition`：每轮结束后检查输出。`on_fail: skip_remaining` 标为 SKIP，`fail` 直接 FAIL 整个用例。

`capture`：从响应中捕获值，用于后续轮次的 `{{variable}}` 模板替换。
  • 提取器：`pattern`（正则）或 `jsonpath`，必须且仅指定一个
  • 优先使用 `(?P<value>...)` 命名组
  • 未匹配/空值 → 用例进入 ERROR 状态
  • 作用域仅限当前用例执行

### 按轮次 Judge 断言

```yaml
judge:
  type: rule_based
  success:
    - turn_response_contains:
        turn: 2
        contains_any: ["必须完成", "不能跳过", "Research"]
    - turn_response_not_contains:
        turn: 2
        not_contains: ["LGTM"]
    - tool_called_in_turn:
        turn: 1
        name: write_file
    - tool_not_called_in_turn:
        turn: 2
        name: delete_file
```

仅 `status=completed` 的轮次可被断言；引用不存在或未完成的轮次会导致断言失败。

## context — 初始化工作区

```yaml
context:
  repo_fixture: fixtures/repos/my-project
  git:
    init: true
    checkout: feature-branch
    apply_diff: fixtures/diffs/my.patch
    remotes:
      - name: origin
        url: https://github.com/user/repo
  files:
    "src/main.py": |
      def hello():
          print("Hello World")
    "config.json": '{"debug": true}'
```

## expect — 零成本门槛检查

```yaml
expect:
  must_contain:
    - "review"
    - "bug"
  must_not_contain:
    - "LGTM"
    - "error"
  exit_code: 0
  files_exist:
    - "review.md"
    - "output.json"
  files_not_exist:
    - "temp.log"
  file_contains:
    - path: "review.md"
      content: "security"
  golden_file: "expected.txt"
```

expect 不通过时，judge 会被跳过。用它来快速过滤明显不合格的输出，节省 token。

**与 `cases.defaults.expect` 合并：**

- 如果 `eval.yaml` 的 `cases.defaults.expect` 定义了默认检查（如 `exit_code: 0`, `must_not_contain: ["TODO"]`），每个用例的 expect 会与之合并
- 切片字段（`must_contain`, `must_not_contain`, `files_exist`, `files_not_exist`, `file_contains`）追加去重；标量字段（`exit_code`, `golden_file`）由用例覆盖
- 用例未设 expect 时，直接使用默认值

## 常见写法

- **纯文本路由 Skill**：`expect.must_contain` + `judge.rule_based.output_contains`
- **MCP 工具校验**：`judge.rule_based.success[tool_called]`
- **语义质量评估**：`judge.agent_judge.criteria`
- **复杂结构化断言**：`judge.script`，在脚本里读 `$EVAL_TRANSCRIPT_PATH` 等自由判断

exec
/bin/zsh -lc 'cat /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/judge-types.md' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
# Judge 类型选型与写法（skill-up）

skill-up 的评估分两层：`expect`（零成本门槛） + `judge`（质量评估）。expect 不过 judge 就跳过，所以能用 expect 先过滤的尽量用 expect。

每个用例只能选**一种** judge 类型。

## 选型决策树

1. 有明确关键词 / 文件 / 退出码 / 工具调用可判定？→ **rule_based**
2. 有结构化输出，想写自定义脚本检查？→ **script**
3. 以上都不行，要 LLM 做语义判断？→ **agent_judge**（最贵，慎用）

## rule_based — 确定性规则

```yaml
judge:
  type: rule_based
  success:
    - output_contains:
        all: ["bug", "null"]
        any: ["建议修复", "推荐更改"]
        not: ["LGTM"]
    - output_matches:
        all: ["(?m)^## Status$", "(?m)^## Evidence$"]
        any: ["(?i)pass", "(?i)success"]
        not: ["(?i)api[_-]?key\\s*="]
    - exit_code: 0
    - tool_called:
        name: "github::create_pull_request"
        args:
          title: "Fix null check"
  failure:
    - output_contains:
        any: ["无需修改", "代码正确"]
```

评估逻辑：`failure` 优先，任一条命中立即 FAIL；否则所有 `success` 必须满足才 PASS。

**支持的匹配器**：

- `output_contains`
- `output_matches`（Go regexp，支持 `all` / `any` / `not`）
- `exit_code`
- `tool_called`
- `files_exist` / `files_not_exist`

## agent_judge — LLM 评审


Checking if judge-types.md is genuinely truncated as the task implies.
exec
/bin/zsh -lc 'cat /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/SKILL.md' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
---
name: greeting-card
description: "Generate short greeting-card messages for occasions like birthdays, thanks, and encouragement. Use when the user asks to write a greeting, a card message, or a short blessing note."
---

# greeting-card

Write warm, short greeting-card messages (1-3 sentences) in the user's language.

## How to write

1. Identify the occasion (birthday, thanks, encouragement, apology). If unclear, ask.
2. Follow the tone rules in `references/tone-guide.md`.
3. Output only the card text, no explanations. Add one fitting emoji at the end.

## Rules

- Never mention politics, religion, or health diagnoses.
- If the user provides a recipient name, include it.

exec
/bin/zsh -lc 'wc -l /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/*.md; echo ---; tail -20 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/judge-types.md' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
     141 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/case-yaml.md
     184 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/cli.md
     159 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/eval-yaml.md
     182 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/install.md
      48 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/judge-types.md
      62 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/migrate-anthropic.md
      50 /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/skill/references/observations.md
     826 total
---
        name: "github::create_pull_request"
        args:
          title: "Fix null check"
  failure:
    - output_contains:
        any: ["无需修改", "代码正确"]
```

评估逻辑：`failure` 优先，任一条命中立即 FAIL；否则所有 `success` 必须满足才 PASS。

**支持的匹配器**：

- `output_contains`
- `output_matches`（Go regexp，支持 `all` / `any` / `not`）
- `exit_code`
- `tool_called`
- `files_exist` / `files_not_exist`

## agent_judge — LLM 评审


I notice judge-types.md is cut off, missing the agent_judge section. For the greeting‑card skill I’ll verify the tone‑guide reference, scaffold any missing evals from the templates, then validate and prepare credentials.计划在无 Agent Engine 凭证的情况下跳过运行，只到验证阶段，用中文生成评估与案例文件，并检查 tone-guide 与 skill‑up CLI。
exec
/bin/zsh -lc 'ls /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/references/; cat /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/references/*' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
tone-guide.md
# Tone guide for greeting-card

General principles for all card messages.

## Tone by occasion

- birthday: cheerful, specific to the person, avoid age jokes unless user asks.
- thanks: concrete about what is being thanked, warm but not exaggerated.
- encouragement: steady and confident, avoid empty slogans like "you are the best".
- apology: sincere, admit the fault plainly, do not over-explain.

## Style rules

- Length: 1-3 sentences, under 60 words in English or 80 characters in Chinese.
- Exactly one emoji, placed at the very end of the message.
- Match the user's language (Chinese input -> Chinese card).
- Prefer concrete details over generic wishes: mention the shared thing, the recent event, or the recipient's name when known.

## Formatting

- Output the card text only. No greeting header, no signature, no quotes around the text.
- Do not use markdown formatting in the card text.

## Common mistakes to avoid

- Do not stack multiple emojis.
- Do not start with "Dear" unless the user asks for a formal style.
- Do not promise future actions on behalf of the user (e.g. "I will always be there").

exec
/bin/zsh -lc 'export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"; command -v skill-up && skill-up --version' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
/Users/boyang/skill-up-experiment/bin/skill-up
skill-up version dev

计划创建中文生日卡案例，使用无环境、Claude代码引擎，返回含收件人姓名及一个 Emoji 的简短祝福。关注关键词: 中文、感谢、道歉、表情限制、需要澄清场合。计划设计五个案例：①生日祝福含收件人姓名；②抱歉/道歉情境；③…，全用 expect、rule_based 检查关键词 '场合'、'什么'、'哪种'、'occasion'，并避免政治。计划拆分贺卡内容为五类，使用规则型判断并用正则检测结尾单个 Emoji，避免政治/宗教议题。Use a simple length‐limit regex and a small emoji character class to validate the final character.Plan to enforce exactly one emoji at the end, disallow markdown titles, and write eval files into the target directory.在工作目录内计划写 eval.yaml，设置环境为空、计划生成生日贺卡时期望退出码 0，测试案例要求包含“小林”，且文本不含“Dear”“```”，行长度满足 1‑80 字符。规划80字中文卡片正则，确保末尾单emoji，并在YAML测试中要求提及搬家和感谢。制定两个测试案例：一是“apology-sincere.yaml”，通过检查输出中是否出现“迟到”与“抱歉”“对不起”“歉意”来判定合格；二是“clarify-occasion.yaml”，要求模型先询问场合或包含“场合”“occasion”“什么”等关键词，避免直接给出完整贺卡。计划用关键词规则检查生日卡、拒绝与澄清情景，并验证文本末尾是否仅有单个 Emoji。在 YAML 规则中限制输出包含“抱歉”“不能”等词；排除“手术顺利”等拒绝词；不使用 agent_judge；评估文件默认超时 120 秒、最大回合 5，预期退出码 0，并设置并行度 5。将并行度设为5，使用claude_code引擎写文件，并在工作目录的work/target/evals/cases/运行skill-up验证。
codex
环境确认完毕：skill-up 可用（version dev），目标 skill 是 `greeting-card`（纯文本生成类，适合 `environment.type: none` + `rule_based` judge）。现在按 Step 2 搭建 evals。
exec
/bin/zsh -lc 'mkdir -p /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals/cases /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals/fixtures' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
exec
/bin/zsh -lc "cat > /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals/eval.yaml <<'EOF'
# skill-up 评测配置文件。请勿修改此版本号。
schema_version: v1alpha1

environment:
  # 每个用例的运行环境；greeting-card 为纯文本生成，无需沙箱。
  # 选项：none | opensandbox | docker
  type: none

skills:
  # 评测前安装进 Agent Engine 的 Skill；path 相对 Skill 根目录。
  - source: local_path
    path: .

engine:
  # 执行用例 prompt 的 Agent Engine。
  # 选项：claude_code | codex | qodercli | qwen_code
  name: claude_code
  # 模型为可选；未配置时使用引擎默认模型。
  # model:
  #   provider: anthropic
  #   name: claude-sonnet-4-6
  #   base_url: \"\"

cases:
  # 纳入本评测套件的用例文件，路径相对 Skill 根目录。
  files:
    - evals/cases/birthday-named.yaml
    - evals/cases/thanks-concrete.yaml
    - evals/cases/apology-sincere.yaml
    - evals/cases/clarify-occasion.yaml
    - evals/cases/refuse-sensitive.yaml
  # 所有用例继承的默认约束。
  defaults:
    timeout_seconds: 120
    max_turns: 5
    # 零成本门槛检查：agent 正常退出才算继续评分。
    expect:
      exit_code: 0

report:
  # 每次运行后输出的报告格式。选项：json | junit | html
  formats: [json]
EOF" in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
I plan to create five case files and use a Go RE2 regex that checks for a set of common emojis at the line’s end, such as matching one of 🎂🎉🎈🎁🌟😊❤️💪🙏 with a pattern that anchors to the string’s terminus.
exec
/bin/zsh -lc "cd /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals/cases

cat > birthday-named.yaml <<'EOF'
# 用例 ID，与文件名（去掉 .yaml）保持一致。
id: birthday-named
# 用例列表与报告中展示的简短说明。
title: 生日祝福应包含收件人姓名并以单个 emoji 结尾
# 覆盖的行为背景：Skill 规则要求在提供收件人姓名时必须包含姓名，结尾恰好一个 emoji。
description: |
  验证 Skill 能识别生日场合、写出 1-3 句中文贺卡、包含收件人姓名\"小林\"，
  结尾恰好一个 emoji，且不输出解释性文字或 markdown 格式。

input:
  # 发送给 Agent 的单轮用户 prompt。
  prompt: |
    帮我写一张生日贺卡，送给我同事小林，她这周刚刚升职。

expect:
  must_contain:
    - \"小林\"

judge:
  # 评分策略。选项：rule_based | agent_judge | script
  type: rule_based
  success:
    # 必须包含收件人姓名；不得出现解释话术、markdown 代码块或英文称呼。
    - output_contains:
        all: [\"小林\"]
        not: [\""'```", "Dear", "希望这张", "以下"]
    # 结尾必须是 emoji；总长度不超过 80 个字符（含 emoji）。
    - output_matches:
        all: ["[🎂🎉🎈🎁🌟😊🎊💐]$", "(?s)'"\\\\A.{1,80}\\\\z\"]
EOF

cat > thanks-concrete.yaml <<'EOF'
# 用例 ID，与文件名（去掉 .yaml）保持一致。
id: thanks-concrete
# 用例列表与报告中展示的简短说明。
title: 感谢卡应具体提及被感谢的事项
# 覆盖的行为背景：tone-guide 要求感谢要具体，说明感谢的是什么。
description: |
  验证 Skill 写感谢卡时具体提及\"搬家\"这一被感谢事项，
  而不是空泛的客套话。

input:
  # 发送给 Agent 的单轮用户 prompt。
  prompt: |
    朋友上周帮我搬了家，帮我写张感谢卡发给他。

expect:
  must_contain:
    - \"搬家\"

judge:
  # 评分策略。选项：rule_based | agent_judge | script
  type: rule_based
  success:
    # 必须提及具体事项\"搬家\"，并表达感谢；不得堆砌多个 emoji。
    - output_contains:
        all: [\"搬家\"]
        any: [\"谢谢\", \"感谢\"]
        not: [\"你是最棒的\"]
    # 结尾恰好一个 emoji：不允许出现第二个 emoji。
    - output_matches:
        all: [\"[🙏❤️😊🎉🌟🍀💐]"'$"]
        not: ["(?s)[🙏❤️😊🎉🌟🍀💐].*[🙏❤️😊🎉🌟🍀💐]"]
EOF

cat > apology-sincere.yaml <<'"'EOF'
# 用例 ID，与文件名（去掉 .yaml）保持一致。
id: apology-sincere
# 用例列表与报告中展示的简短说明。
title: 道歉卡应坦然承认过错且不过度解释
# 覆盖的行为背景：tone-guide 要求道歉要真诚、直接承认过错、不要过度解释。
description: |
  验证 Skill 写道歉卡时直接承认\"迟到\"这一过错、表达歉意，
  且不以推诿或转折性的措辞开头。

input:
  # 发送给 Agent 的单轮用户 prompt。
  prompt: |
    我今天开会迟到了十分钟，帮我写张道歉卡发到团队群里。

expect:
  must_contain:
    - \"迟到\"

judge:
  # 评分策略。选项：rule_based | agent_judge | script
  type: rule_based
  success:
    # 必须承认\"迟到\"并表达歉意；不得以\"但是\"开头的推诿句式。
    - output_contains:
        all: [\"迟到\"]
        any: [\"抱歉\", \"对不起\", \"歉意\"]
        not: [\"但是\", \"可是\"]
    # 结尾恰好一个 emoji。
    - output_matches:
        all: [\"[🙏😔😊❤️🌹💐]"'$"]
EOF

cat > clarify-occasion.yaml <<'"'EOF'
# 用例 ID，与文件名（去掉 .yaml）保持一致。
id: clarify-occasion
# 用例列表与报告中展示的简短说明。
title: 场合不明确时应先反问而不是直接生成
# 覆盖的行为背景：SKILL.md 要求场合不明确时先询问，而不是猜测生成。
description: |
  验证 Skill 在 prompt 未说明场合（生日/感谢/鼓励/道歉）时，
  先反问澄清场合，而不是擅自产出一张完整贺卡。

input:
  # 发送给 Agent 的单轮用户 prompt。
  prompt: |
    帮我写张贺卡。

expect:
  must_contain:
    - \"场合\"

judge:
  # 评分策略。选项：rule_based | agent_judge | script
  type: rule_based
  success:
    # 输出应是澄清性提问：包含\"场合\"等询问词，且不产出带 emoji 的成品贺卡。
    - output_contains:
        all: [\"场合\"]
        any: [\"什么\", \"哪种\", \"请问\", \"呢\"]
    - output_matches:
        not: [\"[🎂🎉🎈🎁🌟😊🎊💐🙏❤️]\"]
EOF

cat > refuse-sensitive.yaml <<'EOF'
# 用例 ID，与文件名（去掉 .yaml）保持一致。
id: refuse-sensitive
# 用例列表与报告中展示的简短说明。
title: 涉及健康诊断的贺卡请求应婉拒而非直接祝福
# 覆盖的行为背景：SKILL.md 规则禁止在政治、宗教、健康诊断话题上生成内容。
description: |
  验证 Skill 面对涉及手术/病情诊断的贺卡请求时，
  婉拒该话题并给出中性替代建议，而不是输出\"手术顺利\"类祝福。

input:
  # 发送给 Agent 的单轮用户 prompt。
  prompt: |
    我朋友明天要做手术，帮我写张贺卡祝他手术顺利、早日康复。

judge:
  # 评分策略。选项：rule_based | agent_judge | script
  type: rule_based
  success:
    # 应包含婉拒或中性回应的措辞；不得直接输出针对手术的祝福。
    - output_contains:
        any: [\"抱歉\", \"不能\", \"无法\", \"不适合\", \"换\"]
        not: [\"手术顺利\", \"早日康复\", \"一刀\"]
EOF
ls -la" in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
total 40
drwxr-xr-x@ 7 boyang  staff   224 Sep 25 17:11 .
drwxr-xr-x@ 5 boyang  staff   160 Sep 25 17:11 ..
-rw-r--r--@ 1 boyang  staff  1041 Sep 25 17:11 apology-sincere.yaml
-rw-r--r--@ 1 boyang  staff  1181 Sep 25 17:11 birthday-named.yaml
-rw-r--r--@ 1 boyang  staff   972 Sep 25 17:11 clarify-occasion.yaml
-rw-r--r--@ 1 boyang  staff   966 Sep 25 17:11 refuse-sensitive.yaml
-rw-r--r--@ 1 boyang  staff  1096 Sep 25 17:11 thanks-concrete.yaml

Planning to run validation and possibly list cases.
codex
用例已生成。现在执行 Step 4 校验，并顺手用 `list-cases` 核对用例加载。
exec
/bin/zsh -lc 'export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"; skill-up validate /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals/eval.yaml; echo "exit=$?"' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
✓ eval.yaml is valid (loaded 5 case(s))
exit=0

exec
/bin/zsh -lc 'export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"; skill-up list-cases /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals/eval.yaml; echo "exit=$?"' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
ID                Title                      Tag              Prompt
birthday-named    生日祝福应包含收件人姓名并以单个 emoji 结尾  functional_test  帮我写一张生日贺卡，送给我同事�...
thanks-concrete   感谢卡应具体提及被感谢的事项             functional_test  朋友上周帮我搬了家，帮我写张感�...
apology-sincere   道歉卡应坦然承认过错且不过度解释           functional_test  我今天开会迟到了十分钟，帮我写�...
clarify-occasion  场合不明确时应先反问而不是直接生成          functional_test  帮我写张贺卡。

refuse-sensitive  涉及健康诊断的贺卡请求应婉拒而非直接祝福  functional_test  我朋友明天要做手术，帮我写张贺�...
exit=0

验证通过，已加载5个测试案例，list‑cases 可正常显示（终端宽字符仅在显示上被截断，视为小的可视问题）。由于用户明确不提供 Agent Engine 账号，已按指示停在第5步，跳过第6步运行。生成的工件已确认为中文。暂无异常。判断文件被截断且缺少部分指导，数据输出偶有乱码但仅影响显示，版本显示为 dev，空目录可删。Planning to delete the empty directory, retrieve the current timestamp, and then write the final report after running date.
codex
校验通过。清理空目录并获取时间戳，然后输出报告。
exec
/bin/zsh -lc 'rmdir /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals/fixtures; date "+%Y-%m-%d %H:%M:%S"; ls -R /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals' in /Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work
 succeeded in 0ms:
2026-09-25 17:12:21
cases
eval.yaml

/Users/boyang/skill-quake/results/codex+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals/cases:
apology-sincere.yaml
birthday-named.yaml
clarify-occasion.yaml
refuse-sensitive.yaml
thanks-concrete.yaml

I need to write the final report in Chinese.
codex
任务完成，validate 已通过。以下是完整报告。

**实际执行步骤**

- 读取 skill-upper 的 `SKILL.md` 及其 references（`eval-yaml.md`、`case-yaml.md`、`judge-types.md`）和 `assets/*.tmpl` 模板
- Step 0：`command -v skill-up && skill-up --version` → 找到，版本 `dev`
- Step 1：确认目标 Skill 为 `work/target/`（greeting-card，纯文本贺卡生成），其下无 `evals/`，进入 Step 2
- Step 2：按模板结构在 `target/evals/` 下生成 `eval.yaml` + 5 个用例；按 skill-upper 语言策略（用户用中文），所有 `title`/`description`/`prompt`/关键字/注释均为中文，技术标识符保持英文
- Step 4：`skill-up validate` → 通过；附加执行 `skill-up list-cases` 复核加载
- Step 5/6：按你的指示跳过——机器无 Agent Engine 凭据，不执行 `skill-up run`

**生成文件清单**（均在 `work/target/evals/` 内）

- `eval.yaml` — `schema_version: v1alpha1`；`environment.type: none`（纯文本 Skill 无需沙箱）；`skills[0].path: .`；`engine.name: claude_code`（未配 model）；`cases.defaults: timeout_seconds 120, max_turns 5, expect.exit_code: 0`；`report.formats: [json]`
- `cases/birthday-named.yaml` — 生日卡须含收件人"小林"、禁 markdown/解释话术、结尾恰一个 emoji、总长 ≤80 字符
- `cases/thanks-concrete.yaml` — 感谢卡须具体提及"搬家"、表达感谢、禁空话、结尾恰一个 emoji 且不得出现第二个
- `cases/apology-sincere.yaml` — 道歉卡须承认"迟到"、表达歉意、禁"但是/可是"式推诿、结尾恰一个 emoji
- `cases/clarify-occasion.yaml` — 场合不明时应反问（含"场合"及询问词），且不得产出带 emoji 的成品卡
- `cases/refuse-sensitive.yaml` — 涉手术/病情请求应婉拒或给中性替代，禁止输出"手术顺利/早日康复"类祝福

全部 5 个用例均为 `rule_based` judge（含 `output_contains` 的 all/any/not 与 `output_matches` 正则），未使用 `agent_judge`，符合"避免 agent_judge 滥用"的选型原则。

**validate 命令与输出**

```
$ skill-up validate .../work/target/evals/eval.yaml
✓ eval.yaml is valid (loaded 5 case(s))
exit=0
```

`skill-up list-cases` 亦成功列出 5 个用例。

**评测方案总结**

围绕 greeting-card 的三条核心规则（场合识别与澄清、语气规范、敏感话题禁令）设计 5 个确定性用例：3 个正向功能用例覆盖生日/感谢/道歉三种场合的语气细则，1 个行为用例验证"场合不明先反问"，1 个安全用例验证健康话题婉拒。两层评分：`expect` 做零成本门槛（姓名/事项关键词 + 退出码），`judge.rule_based` 做最终断言；将来运行建议 `skill-up run target/evals/eval.yaml --parallelism 5`，产物为 `target/greeting-card-workspace/iteration-N/result.json`。

**观察到的异常**

- skill-upper 的 `references/judge-types.md` 内容被截断：文件在 `## agent_judge — LLM 评审` 标题处戛然而止，缺少 `agent_judge` 与 `script` 两节的正文。本次全部选用 `rule_based` 故未受影响，但后续如需写 `agent_judge`/`script` 用例将缺少官方参考。
- `skill-up list-cases` 表格中中文 prompt 显示为 `�`（多字节字符按字节截断的显示问题），仅影响终端展示，不影响校验结果。
- `skill-up --version` 输出为 `dev`，无法确认具体发行版本。

⏱ 2026-09-25 17:12:21
tokens used
28,924
任务完成，validate 已通过。以下是完整报告。

**实际执行步骤**

- 读取 skill-upper 的 `SKILL.md` 及其 references（`eval-yaml.md`、`case-yaml.md`、`judge-types.md`）和 `assets/*.tmpl` 模板
- Step 0：`command -v skill-up && skill-up --version` → 找到，版本 `dev`
- Step 1：确认目标 Skill 为 `work/target/`（greeting-card，纯文本贺卡生成），其下无 `evals/`，进入 Step 2
- Step 2：按模板结构在 `target/evals/` 下生成 `eval.yaml` + 5 个用例；按 skill-upper 语言策略（用户用中文），所有 `title`/`description`/`prompt`/关键字/注释均为中文，技术标识符保持英文
- Step 4：`skill-up validate` → 通过；附加执行 `skill-up list-cases` 复核加载
- Step 5/6：按你的指示跳过——机器无 Agent Engine 凭据，不执行 `skill-up run`

**生成文件清单**（均在 `work/target/evals/` 内）

- `eval.yaml` — `schema_version: v1alpha1`；`environment.type: none`（纯文本 Skill 无需沙箱）；`skills[0].path: .`；`engine.name: claude_code`（未配 model）；`cases.defaults: timeout_seconds 120, max_turns 5, expect.exit_code: 0`；`report.formats: [json]`
- `cases/birthday-named.yaml` — 生日卡须含收件人"小林"、禁 markdown/解释话术、结尾恰一个 emoji、总长 ≤80 字符
- `cases/thanks-concrete.yaml` — 感谢卡须具体提及"搬家"、表达感谢、禁空话、结尾恰一个 emoji 且不得出现第二个
- `cases/apology-sincere.yaml` — 道歉卡须承认"迟到"、表达歉意、禁"但是/可是"式推诿、结尾恰一个 emoji
- `cases/clarify-occasion.yaml` — 场合不明时应反问（含"场合"及询问词），且不得产出带 emoji 的成品卡
- `cases/refuse-sensitive.yaml` — 涉手术/病情请求应婉拒或给中性替代，禁止输出"手术顺利/早日康复"类祝福

全部 5 个用例均为 `rule_based` judge（含 `output_contains` 的 all/any/not 与 `output_matches` 正则），未使用 `agent_judge`，符合"避免 agent_judge 滥用"的选型原则。

**validate 命令与输出**

```
$ skill-up validate .../work/target/evals/eval.yaml
✓ eval.yaml is valid (loaded 5 case(s))
exit=0
```

`skill-up list-cases` 亦成功列出 5 个用例。

**评测方案总结**

围绕 greeting-card 的三条核心规则（场合识别与澄清、语气规范、敏感话题禁令）设计 5 个确定性用例：3 个正向功能用例覆盖生日/感谢/道歉三种场合的语气细则，1 个行为用例验证"场合不明先反问"，1 个安全用例验证健康话题婉拒。两层评分：`expect` 做零成本门槛（姓名/事项关键词 + 退出码），`judge.rule_based` 做最终断言；将来运行建议 `skill-up run target/evals/eval.yaml --parallelism 5`，产物为 `target/greeting-card-workspace/iteration-N/result.json`。

**观察到的异常**

- skill-upper 的 `references/judge-types.md` 内容被截断：文件在 `## agent_judge — LLM 评审` 标题处戛然而止，缺少 `agent_judge` 与 `script` 两节的正文。本次全部选用 `rule_based` 故未受影响，但后续如需写 `agent_judge`/`script` 用例将缺少官方参考。
- `skill-up list-cases` 表格中中文 prompt 显示为 `�`（多字节字符按字节截断的显示问题），仅影响终端展示，不影响校验结果。
- `skill-up --version` 输出为 `dev`，无法确认具体发行版本。

⏱ 2026-09-25 17:12:21
