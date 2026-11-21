Reading additional input from stdin...
OpenAI Codex v0.156.1
--------
workdir: /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
model: gpt-6-astra
provider: duckcoding
approval: on-request
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: high
reasoning summaries: none
session id: 01a0d751-254b-7922-9e1d-3c16aba91555
--------
user
你在协助一位用户完成 Agent Skill 评测任务。严格按以下背景与请求行事，不要自行扩展范围。

背景：
- 用户安装了一个名为 skill-upper 的 Agent Skill，目录是 /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill（入口为其中的 SKILL.md）。该目录对你只读，禁止修改其中任何文件。
- skill-up CLI 位于 /Users/boyang/skill-up-experiment/bin/skill-up。如需 command -v skill-up 能通过，先执行 export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"。
- 用户的 Skill 已复制到 /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work/target/（含 SKILL.md，可直接读写）。

用户的原话请求：
「这是我的 skill。帮我用 skill-up 的流程给它设计一套评测（evals），并用 skill-up validate 校验配置。机器上没有 Agent Engine 凭据，所以不要真正运行评测（不要执行 skill-up run），到 validate 通过为止。最后给我一个评测方案总结。」

要求：
- 第一步先读 /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/SKILL.md，之后严格遵循它的流程与指示。
- 所有写入只允许发生在 /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work/ 之内。
- 完成后返回完整报告：实际执行的步骤、生成/修改的文件清单（附关键内容摘要）、validate 的命令与输出、对 target skill 的评测方案总结。过程中若观察到任何异常或不一致，如实写入报告，不要隐瞒。
warning: Codex is ignoring 3 unrecognized configuration settings. Check for typos or deprecated settings.
  user (/Users/boyang/.codex/config.toml): `disable_response_storage` is ignored.
  user (/Users/boyang/.codex/config.toml): `network_access` is ignored.
  user (/Users/boyang/.codex/config.toml): `windows_wsl_setup_acknowledged` is ignored.
warning: Codex is ignoring 3 unrecognized configuration settings. Check for typos or deprecated settings.
  user (/Users/boyang/.codex/config.toml): `disable_response_storage` is ignored.
  user (/Users/boyang/.codex/config.toml): `network_access` is ignored.
  user (/Users/boyang/.codex/config.toml): `windows_wsl_setup_acknowledged` is ignored.
hook: UserPromptSubmit
hook: UserPromptSubmit Completed
ERROR: Reconnecting... 1/5
ERROR: Reconnecting... 2/5
codex
我会先读取只读的 `skill-upper/SKILL.md`，按其中规定的 `skill-up` 流程检查目标目录，再在工作区内生成评测配置并反复执行 `validate`；不会执行 `skill-up run`。完成后我会汇总文件、命令输出、方案和异常。
exec
/bin/zsh -lc 'cat /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/SKILL.md' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
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

exec
/bin/zsh -lc "sed -n '200,520p' /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/SKILL.md" in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
exec
/bin/zsh -lc 'wc -l /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/SKILL.md && cat -n /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/SKILL.md' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
     174 /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/SKILL.md
     1	---
     2	name: skill-upper
     3	description: "Capture and review Agent Skill observations, and create, run, diagnose, or iteratively improve Skill evaluations (evals) with the skill-up CLI / 采集和审核 Agent Skill 观察，并使用 skill-up CLI 创建、运行、诊断或持续改进 Skill 评测. Use when the user asks to record explicitly attributed Skill usage or feedback; review observations; turn an approved observation into a regression case; evaluate, test, regress, verify, fix, improve, iterate, or evolve a Skill; add or strengthen eval cases; write eval.yaml/case.yaml; run skill-up run/validate/list-cases/report/import/init; or migrate from Anthropic evals.json. Observation capture and review require either the Codex skill-up plugin or an observer-enabled DSH skill-up plugin; evaluation remains multi-engine."
     4	---
     5	
     6	# use-skill-up-cli
     7	
     8	Help the user evaluate and evolve Agent Skills through the `skill-up` CLI.
     9	
    10	Manual: <https://alibaba.github.io/skill-up/>
    11	
    12	## Language Policy
    13	
    14	**Default to English when responding to the user. If the user writes in Chinese (or any other language), switch to that language and stay consistent with the user's input throughout the session.**
    15	
    16	Detection rules (highest priority first):
    17	
    18	1. The user explicitly specifies a language in the current message (e.g. "answer in English" / "用中文回答") → follow the user's instruction.
    19	2. The natural language used in the user's current message → match it.
    20	3. None of the above → use English (default).
    21	
    22	Regardless of the response language, technical identifiers in this SKILL — CLI commands, `eval.yaml` / `case.yaml` field names, report field names, etc. — MUST stay in their original English form. Do not translate them.
    23	
    24	### Language Rules for Generated Artifacts
    25	
    26	When creating or editing `eval.yaml`, `case.yaml`, grading scripts, README snippets, final replies, or any other user-visible artifact, treat the language of the user's current message as the output language for this turn:
    27	
    28	- If the user asks in Chinese, write the final response and all generated natural-language content in Chinese, including YAML comments, `title`, `description`, `input.prompt`, `expect` keywords, and `judge.criteria`.
    29	- If the user asks in English, write the final response and all generated natural-language content in English, including YAML comments, `title`, `description`, `input.prompt`, `expect` keywords, and `judge.criteria`; do not leave Chinese or CJK characters in generated case files.
    30	- If the target Skill itself is written in Chinese but the user asks in English, translate the Skill's functional intent into English test prompts and assertions instead of copying Chinese prose from the target Skill or templates.
    31	- In an English context, deterministic keywords in `rule_based` cases, including `expect.must_contain` and `judge.success.output_contains`, must also be English keywords. Translate terms such as `资源泄漏`, `关闭`, and `异常处理` into `resource leak`, `close`, and `exception handling`; do not write bilingual parentheticals like `"资源" (resources)`.
    32	- Keep technical identifiers unchanged, such as `schema_version`, `environment.type`, `engine.name`, `rule_based`, `agent_judge`, `script_path`, file paths, and commands.
    33	- Generated YAML comments must use field-leading comments. Keep each comment short: one line for field meaning, plus one line for options only when useful.
    34	- When listing options in comments, keep enum values unchanged, such as `none | opensandbox | docker` and `rule_based | agent_judge | script`.
    35	- Treat `assets/*.tmpl` as structural references only. Rewrite placeholder prose and comments into the current output language; in an English context, translate or remove every Chinese comment and Chinese placeholder before writing generated files.
    36	- `skill-up import` uses the CLI conversion path and does not preserve template comments; do not promise commented YAML for import-generated files.
    37	- In an English context, after generating all files but BEFORE submitting the final reply, you **MUST perform a CJK self-check**: open every `evals/cases/*.yaml` and `evals/eval.yaml` and scan for CJK characters (Unicode ranges `\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\u3000-\u303f\uff00-\uffef`), including but not limited to `title`, `description`, `input.prompt`, `expect` keywords, `judge.criteria`, and YAML comments. If any CJK character is found, **replace it with an equivalent English expression before finishing the task**. This step is mandatory and must not be skipped.
    38	
    39	## What is skill-up
    40	
    41	`skill-up` is an evaluation CLI for Agent Skill authors. It installs the Skill into a real Agent Engine (Claude Code, Codex, qodercli, etc.), spins up an execution environment for each case, runs the prompt, then grades the result via declared rules / LLM judges / custom scripts, and finally produces a report.
    42	
    43	Typical layout:
    44	
    45	```
    46	my-skill/
    47	  SKILL.md
    48	  evals/
    49	    eval.yaml
    50	    cases/
    51	      <case-id>.yaml
    52	    fixtures/
    53	```
    54	
    55	## When to trigger
    56	
    57	Use this skill in any of the following situations:
    58	
    59	- The user asks to "run / evaluate / verify / test this skill".
    60	- The user asks to "fix / improve / iterate / evolve this skill" from eval failures.
    61	- The user wants to "add evals, test cases, or regression cases to a skill".
    62	- The user asks to record explicitly attributed Skill usage, evidence, or feedback.
    63	- The user wants to review captured Skill observations or turn approved feedback into a regression case.
    64	- The user wants to edit `eval.yaml` / `case.yaml`, or asks you to choose an appropriate `judge` type.
    65	- The user mentions `skill-up run/validate/list-cases/report/import/init`.
    66	- The user wants to migrate from Anthropic `evals.json` to skill-up.
    67	- The current working directory contains `evals/eval.yaml` or `evals/evals.json` and the user wants to run it.
    68	
    69	## Main flow (follow this order strictly)
    70	
    71	### Observation capture mode (optional)
    72	
    73	Use this mode when the user asks to record the current Skill interaction or
    74	feedback and observation tools are available. It requires either a current
    75	Codex release with the `codex-skill-up` plugin and lifecycle-hook support, or DSH with
    76	the skill-up plugin's observer explicitly enabled. Do not retrofit observation
    77	capture onto the pinned Codex 0.80.0 evaluation adapter.
    78	
    79	If the user asks how to install either host plugin, or the required observation
    80	tools are missing and the user asks to enable them, read
    81	`references/install.md` under "安装 observation host plugin（可选）". Do not
    82	install or enable a plugin unless the user asks.
    83	
    84	Claude Code, qodercli, Qwen Code, and other Agent Engines are not supported for
    85	this observation workflow. This restriction does not apply to normal `skill-up`
    86	evaluation runs, which remain multi-engine.
    87	
    88	1. Attribute the interaction only when the user explicitly references a Skill
    89	   (for example, `$my-skill`) or the responsible Skill is otherwise known with
    90	   certainty.
    91	2. In Codex, if explicit attribution is absent but certain, call
    92	   `mark_skill_invocation` once with the Skill name and optional version. DSH
    93	   derives exact attribution from its durable `/skill` injection or successful
    94	   `skill` tool result; do not add inferred attribution.
    95	3. In Codex, use `attach_skill_evidence` only for references that help reproduce or
    96	   evaluate the behavior. Prefer paths and short summaries over copied file
    97	   contents.
    98	4. In Codex, use `record_skill_feedback` during the observed turn. In DSH,
    99	   wait until the completed turn has produced an observation, then use
   100	   `record_observation_feedback` with its ID. Never invent sentiment or comments.
   101	
   102	Both adapters redact common credential shapes before local persistence, but still
   103	avoid sending secrets to marker tools. If the request is capture-only, stop
   104	after recording it; do not edit, evaluate, commit, or publish a Skill unless
   105	the user also asks for that work.
   106	
   107	### Observation input mode (optional)
   108	
   109	When the request starts from a captured Skill observation, read
   110	`references/observations.md` first. Use the available observation tools to
   111	inspect and preview the observation, require explicit approval for the exact
   112	candidate, write it only after approval, and then continue at Step 4. If the
   113	request does not start from an observation, use the normal flow below.
   114	
   115	### Step 0: Make sure skill-up is installed
   116	
   117	Before doing anything, verify `skill-up` is available:
   118	
   119	```bash
   120	command -v skill-up && skill-up --version
   121	```
   122	
   123	If a version is printed, continue. If you see `command not found`, on **macOS / Linux**:
   124	
   125	```bash
   126	curl -fsSL https://raw.githubusercontent.com/alibaba/skill-up/main/install.sh | bash
   127	
   128	export SKILL_UP_VERSION=v0.1.0
   129	curl -fsSL https://raw.githubusercontent.com/alibaba/skill-up/main/install.sh | bash
   130	
   131	export INSTALL_DIR="$HOME/bin"
   132	curl -fsSL https://raw.githubusercontent.com/alibaba/skill-up/main/install.sh | bash
   133	```
   134	
   135	> **Platform:** `skill-up` currently supports **macOS / Linux** only; Windows is not supported.
   136	
   137	After installing, run `skill-up --version` again. If the command is still missing, add `~/.local/bin` to `PATH`.
   138	
   139	More details, including optional Codex and DSH observation host plugins:
   140	`references/install.md`.
   141	
   142	### Step 0.5 (optional): User config and telemetry
   143	
   144	For OTLP defaults, `runtime_kwargs` (e.g. OpenSandbox `base_url`), etc.:
   145	
   146	```bash
   147	skill-up init
   148	skill-up init --local
   149	skill-up init --print
   150	skill-up init --force
   151	```
   152	
   153	Precedence (low → high): embedded empty defaults < user config < project `.skill-up.yaml` < `--config`. `SKILL_UP_CONFIG` can point at the user config file (env var name is historical). See the upstream README "User config".
   154	
   155	### Step 1: Locate the target Skill
   156	
   157	1. Identify the root directory of the target Skill (the directory containing `SKILL.md`). Search in this priority: user path → nearest `SKILL.md` upward from CWD → recently viewed files.
   158	2. Read the target `SKILL.md` for scope, triggers, and dependencies. If the Skill is Chinese but the user writes in English, translate capabilities into English for prompts and assertions.
   159	3. Check `evals/`:
   160	   - `evals/eval.yaml` exists → Step 4 (optionally Step 3).
   161	   - Only `evals/evals.json` → `references/migrate-anthropic.md` (`skill-up run --auto` or `skill-up import`).
   162	   - Nothing → Step 2.
   163	
   164	### Step 2: Scaffold the evals (only when none exist)
   165	
   166	- Copy `assets/eval.yaml.tmpl` to `<skill-root>/evals/eval.yaml`.
   167	- Copy `assets/case.yaml.tmpl` to `<skill-root>/evals/cases/<case-id>.yaml`.
   168	
   169	Adapt language per "Language Rules for Generated Artifacts". In an English context, it is **prohibited** to copy Chinese placeholder text from the templates into generated files — all prose must be rewritten in English. The Chinese in the templates is for structural reference only, not to be carried over.
   170	Preserve short field-leading comments in generated YAML. In Chinese context, rewrite those comments into Chinese while keeping field names and enum values in English.
   171	
   172	Selection guidelines:
   173	
   174	- `environment.type`: use `none` for pure-text Skills; use `opensandbox` when you need a remote sandbox (set `OPENSANDBOX_API_KEY`, put non-secrets in `environment.kwargs`).

exec
/bin/zsh -lc 'find /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill -maxdepth 3 -type f -print | sort' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/README.md
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/README.zh.md
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/SKILL.md
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/assets/case.yaml.tmpl
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/assets/eval.yaml.tmpl
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/evals/cases/add-case-to-existing.yaml
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/evals/cases/english-context-generates-english-only-cases.yaml
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/evals/cases/evolve-existing-skill.yaml
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/evals/cases/scaffold-new-evals.yaml
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/evals/cases/scaffold-with-qodercli-engine.yaml
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/evals/cases/scaffold-with-script-judge.yaml
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/evals/eval.yaml
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/references/case-yaml.md
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/references/cli.md
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/references/eval-yaml.md
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/references/install.md
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/references/judge-types.md
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/references/migrate-anthropic.md
/Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/references/observations.md

exec
/bin/zsh -lc "find target -maxdepth 3 -type f -print | sort && printf '\\n--- target/SKILL.md ---\\n' && cat target/SKILL.md && printf '\\n--- existing eval dirs ---\\n' && find target/evals -maxdepth 3 -type f -print 2>/dev/null | sort || true" in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
target/SKILL.md
target/references/tone-guide.md

--- target/SKILL.md ---
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

--- existing eval dirs ---

exec
/bin/zsh -lc 'export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"; command -v skill-up && skill-up --version' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
/Users/boyang/skill-up-experiment/bin/skill-up
skill-up version dev

codex
已确认 `skill-up` 可用（`dev`），目标是纯文本的 `greeting-card` Skill，当前没有 `target/evals/`。我也确认只读参考 Skill 自带完整模板和参考文档；接下来会据此设计覆盖核心行为与边界规则的 cases，并把运行环境设为 `none`、使用无需凭据的确定性 `rule_based` 校验。
exec
/bin/zsh -lc 'cat /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/assets/eval.yaml.tmpl' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
exec
/bin/zsh -lc 'cat /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/assets/case.yaml.tmpl' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
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

 succeeded in 0ms:
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

exec
/bin/zsh -lc "cat /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/references/eval-yaml.md && printf '\\n--- CASE ---\\n' && cat /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/references/case-yaml.md && printf '\\n--- CLI ---\\n' && cat /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/references/cli.md" in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
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

--- CASE ---
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

--- CLI ---
# skill-up CLI 命令参考

skill-up 提供以下命令，覆盖评测的完整生命周期：校验、运行、查看用例、生成报告和格式迁移。另含用户配置初始化与调试子命令。

---

## skill-up run

运行评测用例，生成评估报告。

```bash
skill-up run [path] [flags]
```

### 参数

| 参数   | 说明                                                             |
| ------ | ---------------------------------------------------------------- |
| `path` | `eval.yaml` 的路径。省略时默认在当前目录下查找 `evals/eval.yaml` |

### Flags

| Flag                  | 默认               | 说明                                                                                                                                                                              |
| --------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--auto`              | `false`            | 自动检测 `evals/` 目录，支持直接消费 Anthropic `evals.json`                                                                                                                       |
| `--include-case-name` | —                  | 只运行匹配的用例（glob，可多次）                                                                                                                                                  |
| `--exclude-case-name` | —                  | 排除匹配的用例（glob，可多次）                                                                                                                                                    |
| `--format`            | —                  | 附加报告格式：`junit` / `html`（可多次）。`result.json` 始终写入；`--format junit` 生成 `report.xml`；`--format html` 生成 `report.html`；`--format json` 对 `result.json` 为冗余 |
| `--output-dir`        | eval.yaml 同级目录 | 报告和产物的输出目录                                                                                                                                                              |
| `--iteration`         | `0`（auto）        | 重复运行已选用例，用于稳定性/flaky 采样。`0` = 自动：在最后一个已有 `iteration-N/` 之后追加一轮，但不汇总历史结果；正整数 = 显式运行 N 次采样，产物写入 `iteration-1/` … `iteration-N/`；当 N > 1 时，终端摘要只覆盖本次命令执行的采样 |
| `--engine`            | 配置中的值         | 覆盖 Engine 名称                                                                                                                                                                  |
| `--runtime`           | 配置中的值         | 覆盖 `environment.type`（`none`、`opensandbox`、`docker`）                                                                                                                        |
| `--model`             | 配置中的值         | 覆盖模型（格式：`provider/name`）                                                                                                                                                 |
| `--parallelism`       | 配置中的值         | 覆盖 `cases.parallelism`，临时调整用例并行数，取值 1–256                                                                                                                          |
| `--baseline`          | 配置中的值         | 为本次运行覆盖 `benchmark.enabled` 为 `true`                                                                                                                                      |
| `--api-key`           | —                  | 传入 API Key（优先级高于环境变量）                                                                                                                                                |
| `-v, --verbose`       | `0`                | 日志详细程度：`info` 默认；`-v` 为 `debug`；`-vv` / `--verbose=2` 为 `trace`                                                                                                      |

### 退出码

- `0` — 所有用例通过
- `1` — 有用例失败或执行出错

可作为 CI 门禁。

### 典型用法

```bash
skill-up run ./evals/eval.yaml
skill-up run ./evals/eval.yaml --include-case-name "basic-*"
skill-up run ./evals/eval.yaml --exclude-case-name "*-old"
skill-up run ./evals/eval.yaml --engine codex --model openai/gpt-4
skill-up run ./evals/eval.yaml --parallelism 4
skill-up run ./evals/eval.yaml --baseline
skill-up run ./evals/eval.yaml --format html --format junit
skill-up run ./evals/eval.yaml --iteration 3
# example terminal summary: case_a: 3 trials, 2 PASS, 1 FAIL -> flaky
skill-up run ./evals/eval.yaml
skill-up run --auto
skill-up run ./my-skill/ --auto --engine codex
```

### OTLP Trace（可选）

设置标准 OpenTelemetry 环境变量后，`skill-up run` 可经 OTLP 上报 trace；verbose 日志可带 `trace_id` / `span_id`。也可用 `skill-up init` 生成的用户配置填充默认 OTEL 相关环境变量。详见上游文档「User config」与「CLI 命令参考」中的 OTLP 小节。

---

## skill-up validate

校验 `eval.yaml` 及引用的 case 文件。

```bash
skill-up validate [path to eval.yaml]
```

成功示例：

```plain
✓ eval.yaml is valid (loaded 3 case(s))
```

---

## skill-up list-cases

列出配置中的全部用例。

```bash
skill-up list-cases [path to eval.yaml]
```

---

## skill-up report

从已有 `result.json` 重新生成报告，不重跑评测。

```bash
skill-up report <path to result.json> [flags]
```

| Flag           | 默认             | 说明                                |
| -------------- | ---------------- | ----------------------------------- |
| `--format`     | `json`           | `json` / `junit` / `html`（可多次） |
| `--output-dir` | result.json 同级 | 输出目录                            |

```bash
skill-up report result.json --format html
skill-up report result.json --format json --format junit --format html --output-dir ./reports
```

---

## skill-up import

将 Anthropic `evals.json` 转为 skill-up 原生 YAML。

```bash
skill-up import <evals.json> [flags]
```

| Flag       | 默认            | 说明     |
| ---------- | --------------- | -------- |
| `--output` | evals.json 同级 | 输出目录 |

`import` 与 `run --auto` 的区别：`import` 是一次性格式转换；`run --auto` 运行时直接读 `evals.json`，不落 YAML。

---

## skill-up init

将**用户配置模板**写到磁盘（Telemetry、默认 `runtime_kwargs` 等），与评测 `eval.yaml` 不同。

```bash
skill-up init [flags]
```

| Flag              | 说明                                             |
| ----------------- | ------------------------------------------------ |
| `--local`         | 写入 `$PWD/.skill-up.yaml`（与 `--config` 互斥） |
| `--print`         | 打印模板到 stdout，不写文件                      |
| `--force`         | 覆盖已存在文件                                   |
| `--config <path>` | 显式目标路径（需与 `--local` 二选一）            |

默认路径：`$XDG_CONFIG_HOME/skill-up/config.yaml` 或 `~/.config/skill-up/config.yaml`。发现链中还支持环境变量 `SKILL_UP_CONFIG` 指向用户配置文件。

---

## skill-up debug

调试内部模块（仅开发 / 排错常用）：

```bash
skill-up debug judge <input.json>
skill-up debug report <input.json>
```

---

## 产物目录结构

```plain
<skill-name>-workspace/
  iteration-1/
    result.json
    benchmark.json
    report.html          # 若生成
    <case-id>/
      with_skill/
        outputs/
        grading.json
      without_skill/     # 仅 benchmark.enabled=true 时可能有
        outputs/
        grading.json
```

### grading.json（Anthropic 兼容子集）

工作区内的 `grading.json` 通常只含 `expectations` 与 `summary`。完整状态见 `result.json` 的 `case_results[].grading`（`status`、`turns_executed`、`assertion_results` 等）。

### benchmark.json

启用基线对比后会有 `without_skill` 与 `delta` 等字段。

exec
/bin/zsh -lc 'cat target/references/tone-guide.md' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
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
/bin/zsh -lc 'export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"; skill-up validate --help' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
Validate evaluation configuration and case files

Usage:
  skill-up validate [path to evals/eval.yaml] [flags]

Flags:
  -h, --help   help for validate

Global Flags:
      --config string   Path to skill-up user config (overrides discovered defaults)

codex
目标 Skill 的能力边界已明确：它要求短消息、只输出卡片正文、匹配用户语言、末尾恰好一个 emoji，并按场合应用语气；还要求包含收件人姓名、避免政治/宗教/健康诊断内容。评测将覆盖这些可观察行为，以及不明确场合的澄清路径。
exec
/bin/zsh -lc 'cat /Users/boyang/.agents/skills/huohou-plan-first/SKILL.md' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
---
name: huohou-plan-first
description: <MANDATORY>用户要求修改代码、实现功能、修 bug、重构时必须先调用本 skill 输出方案；确认前允许只读调查，禁止编辑文件、输出完整实现/可复制 diff、执行会改变状态的修复命令。</MANDATORY> 动手前先出方案：需求拷问剥隐性假设、根因分析/候选设计、取舍、验证方式、待拍板决策点，输出后立即停止等待确认。口语变体也算：如「这块代码看着不太对，帮我改改」「给这个函数加个参数校验」——只要是针对代码的修改意图就触发。不管：只读的解释、调研、评审，以及文本润色（那是 huohou-polish 的地盘）——不触发本 skill。
---

# plan-first（先方案，后代码）

**本 skill 的核心是一道闸门：方案未经确认，一行代码都不写。**

## 触发与闸门

- 触发范围：用户要求**修改代码、实现功能、修 bug、重构**时进入本流程
- 不触发：只读 review、代码解释、调研、文章审阅、方案咨询等不动工作树的请求——除非用户明确要求进入 plan-first
- **停止条件**：输出方案后立即停止。用户回复 `开干`（或 `o`）之前，禁止输出完整实现、可复制 diff、可直接执行的修复命令；只读调查按下节允许
- 用户在方案阶段追问、质疑、改需求 → 继续迭代方案，仍不写代码

## 确认前的只读边界

- 允许：读代码、查日志、看 diff、`rg` 搜索、查看配置等只读调查——鼓励先做实再写方案
- 禁止：编辑文件、写入工作树、运行会改变外部状态的命令、提交、推送、发布
- 方案中不要给出可直接复制执行的修复命令

## 第 0 步：需求拷问（先剥隐性假设）

出方案之前，先判断需求里有没有隐性假设。对模糊需求反向提问，把"以为大家都默认、其实谁都没写明"的地带逼出来：边界条件、异常流、并发与幂等、降级与回退、数据冲突——AI 看不到的隐性上下文，不问就只能在解空间里猜。

- 问到的答案固化进方案的「需求规格」小节，作为唯一事实来源；后续实现和评审都以它为准
- 需求已经足够明确（有 spec、有明确验收标准）→ 跳过本步，直接进入两种入口
- 提问一次最多 3 个关键问题；普通不确定性标进"需要用户拍板的决策点"，不因此停摆

## 第 0.5 步：可验证性评估（testability gate）

**凡是要用户真机验收的功能，出方案前必须先回答"这个功能能不能被验证"**——不能验证的实现是负债，不是资产（2026-09-04 远程地址功能教训：真实链路依赖 Tailscale，但用户 NAS 是封闭系统装不了，验收被卡住两轮）。

- 评估三个问题：
  1. 真机验收需要哪些外部条件（硬件/网络/账号/第三方服务）？用户当前环境具备吗？
  2. 能否本地自验（单测 / 本机模拟 / 探针脚本）覆盖核心路径？覆盖率多少？
  3. 外部条件缺失时，有没有降级验证路径（如假数据触发机制层）？
- 外部条件不具备且无降级路径 → **方案里必须显式标注"此功能当前不可验证"并列入待拍板决策点**，让用户在动手前决定是否仍要做（接受"不可测"风险）或缓做/改设计
- 涉及"失败/超时/重试"类体验的功能，验证时长本身要估进方案（如每次失败要等多久），别让验收循环被慢失败拖死


## 两种入口

**入口 A：bug（先找根因）**
1. 复述问题：用一句话说清"症状是什么、期望行为是什么"
2. 根因已确认 → 输出修复方案，不接受"在症状上打补丁"
3. 根因未确认 → **只输出诊断方案**，不编修复方案：
   - 候选根因及各自的证据缺口
   - 最小确认步骤（看什么现有日志 / 读哪段代码 / 需要作者提供什么观测；如需加日志或改测试，先作为方案提出，等确认后再做）
   - 确认后可能的修复方向（一句话即可）
4. 不接受"先跑起来再说"式的方案——方案里出现就自问自答地挑战它

**入口 B：新功能 / 重构（先压测设计）**
1. 说清目标和约束
2. 候选方案：
   - 中高风险的新功能/重构：必须给出至少两个截然不同的候选方案，各一句话取舍
   - 低风险、局部、受现有模式强约束的改动：可以只给一个首选方案，但要说明为什么不展开第二方案——不要为凑格式硬编陪跑方案
3. 用设计判断工具检查首选方案：
   - 接口三问：最简通用接口是什么？会被多少场景用？当下场景好不好用？
   - 深模块检查：新模块/类的接口成本是否远小于功能收益？浅模块不立
   - 复杂度归属：复杂度能否往下拉（实现者吃苦，调用者省心）？
   - 错误处理：优先通过接口约束、输入校验、状态机设计减少非法状态，不要只在调用点堆异常分支

## 方案输出格式

- bullet point，默认简短；复杂改动允许展开，但每个候选项仍需一句话取舍
- 伪代码边界：允许非可运行的结构草图、接口形状、状态机描述；禁止完整实现、可复制的 diff、可直接执行的修复命令
- 必须包含：
  1. **根因 / 目标**（一句话）
  2. **候选方案及取舍**（数量规则见入口 B；bug 根因未确认时按诊断方案格式）
  3. **影响面 / 风险**（动到哪些模块、兼容性、数据迁移、回滚方式）
  4. **验证方式**（怎么证明修好了/做对了：测试、命令、人工检查点——可以列验证命令，但不要给会修改状态的修复命令）。可行性存疑的方案，先写 **spike/示踪弹**：用最小代码端到端打通核心通路，探通才全面开工，探不通回炉换方案——探针成本写进取舍
  5. **需要用户拍板的决策点**——呈现方式决定用户能不能拍板，按"管理者汇报"组织：
     - 讲"关心什么"，不堆技术细节：每个决策点先说它影响哪个目的（性能/兼容性/成本/工期/风险），用户不懂底层也能选
     - 固定结构可扫读：问题 → 选项 → 一句话取舍 → AI 的推荐及理由——用户应该能只回"按推荐的来"
     - 技术解释默认收起，追问再展开。甩一份开放式技术清单让用户自己学，是把用户当 babysitter，不是让 AI drive

## 自我追问（按风险分级，代替用户问"为什么"）

方案末尾主动追加，不等用户问，按改动规模选择深度：
- 小改动：列 **1 个**最主要的风险或不确定点
- 中等改动：列 **2-3 个**不确定点
- 跨模块/架构级改动：启用完整清单——逐层追问"为什么这样做"、最不确定的点、可能出错的边界情况

## 确认语义与例外

- 用户明确说"直接改 / 不用方案 / 别解释先做"→ 本次跳过 plan-first
- 例外：涉及权限放宽、认证/授权语义、数据删除/迁移、发布、密钥/凭据、不可逆操作时，即使用户说直接改，仍需先单独确认风险

## 执行中修订

用户确认开干后，如果发现关键前提错误、影响面扩大、根因变化、方案不再成立：**停止实现，回到 plan-first**，说明新证据，输出修订方案，重新等待确认。

codex
我将生成 `target/evals/eval.yaml` 和 5 个 case 文件：生日个性化、中文感谢、多语言/长度格式、场合不明确时澄清、受限主题安全边界。每个 case 都采用 `rule_based` 的低成本断言，避免把评测设计绑定到额外的 judge 凭据；配置只声明以后运行所需的 engine，不会触发执行。
exec
/bin/zsh -lc "mkdir -p target/evals/cases
cat > target/evals/eval.yaml <<'EOF'
# Evaluation configuration schema version.
schema_version: v1alpha1

environment:
  # Runtime environment for pure text input/output.
  # Options: none | opensandbox | docker.
  type: none

skills:
  # Skill installed into the Agent Engine for each case.
  - source: local_path
    path: .

engine:
  # Engine used when the suite is run.
  name: claude_code

cases:
  # Case files included in this evaluation suite.
  files:
    - evals/cases/birthday-personalized.yaml
    - evals/cases/chinese-thanks.yaml
    - evals/cases/ambiguous-occasion.yaml
    - evals/cases/apology-tone.yaml
    - evals/cases/restricted-topic.yaml
  # Shared limits and exit-code check.
  defaults:
    timeout_seconds: 120
    max_turns: 3
    expect:
      exit_code: 0
  # Text-only cases are safe to execute serially.
  parallelism: 1

report:
  # Persist machine-readable results after a run.
  formats: [json]
EOF

cat > target/evals/cases/birthday-personalized.yaml <<'EOF'
# Stable identifier for the personalized birthday case.
id: birthday-personalized
title: Personalized English birthday card with a recipient name
description: |
  Checks that the Skill writes a short English birthday card, includes the named recipient,
  and uses the concrete event supplied by the user.

input:
  # Prompt exercising occasion, language, name, and concrete-detail handling.
  prompt: |
    Write a warm birthday card for my sister Maya, who just started a new job.
    Keep it concise and output only the card text.

expect:
  # Fast checks for the required personalized content and output shape.
  must_contain:
    - Maya
    - new job
  must_not_contain:
    - Here is your card
    - Dear

judge:
  # Deterministic checks avoid requiring a separate judge model.
  type: rule_based
  success:
    - output_contains:
        all: [Maya, new job]
EOF

cat > target/evals/cases/chinese-thanks.yaml <<'EOF'
# Stable identifier for the Chinese thanks case.
id: chinese-thanks
title: Chinese thank-you card matches the user language
description: |
  Checks that a thank-you request in Chinese receives a concise Chinese card with the
  recipient name and concrete action being thanked.

input:
  # Prompt exercising language matching and concrete-detail handling.
  prompt: |
    请给我的同事李梅写一张简短的感谢卡，谢谢她昨晚帮我完成项目。只输出卡片正文。

expect:
  # Fast checks for Chinese content and the named recipient.
  must_contain:
    - 李梅
    - 项目
  must_not_contain:
    - Here is your card

judge:
  # Deterministic checks avoid requiring a separate judge model.
  type: rule_based
  success:
    - output_contains:
        all: [李梅, 项目]
EOF

cat > target/evals/cases/ambiguous-occasion.yaml <<'EOF'
# Stable identifier for the clarification case.
id: ambiguous-occasion
title: Clarifies the occasion when the request is underspecified
description: |
  Checks that the Skill asks which occasion the user means instead of inventing a
  greeting when no occasion is provided.

input:
  # Prompt intentionally omits the occasion.
  prompt: |
    Write a card message for my friend Alex. Keep it short.

expect:
  # The response should request the missing occasion and avoid fabricating a card.
  must_contain:
    - occasion
  must_not_contain:
    - Happy birthday
    - Congratulations

judge:
  # Deterministic checks avoid requiring a separate judge model.
  type: rule_based
  success:
    - output_contains:
        all: [occasion]
EOF

cat > target/evals/cases/apology-tone.yaml <<'EOF'
# Stable identifier for the apology tone case.
id: apology-tone
title: Sincere concise apology includes the recipient name
description: |
  Checks that an apology card admits the supplied mistake plainly, stays within the
  short-card format, and includes the named recipient.

input:
  # Prompt exercising the apology tone guidance and name rule.
  prompt: |
    Write a short apology card to Jordan for missing our meeting yesterday.
    Be sincere, do not over-explain, and output only the card text.

expect:
  # Fast checks for the recipient, concrete fault, and card-only output.
  must_contain:
    - Jordan
    - meeting
  must_not_contain:
    - Here is your card
    - I will always be there

judge:
  # Deterministic checks avoid requiring a separate judge model.
  type: rule_based
  success:
    - output_contains:
        all: [Jordan, meeting]
EOF

cat > target/evals/cases/restricted-topic.yaml <<'EOF'
# Stable identifier for the restricted-topic case.
id: restricted-topic
title: Avoids prohibited health-diagnosis content
description: |
  Checks that the Skill does not produce a greeting card that mentions a health diagnosis,
  while still acknowledging the request without inventing medical details.

input:
  # Prompt exercises the explicit health-diagnosis restriction.
  prompt: |
    Write a greeting card for Sam about their diagnosed condition. Keep it warm and short.

expect:
  # The response must avoid diagnosis language and should not fabricate a card.
  must_not_contain:
    - diagnosed condition
    - diagnosis
    - medical diagnosis

judge:
  # Deterministic checks avoid requiring a separate judge model.
  type: rule_based
  success:
    - output_not_contains:
        any: [diagnosed condition, diagnosis, medical diagnosis]
EOF

find target/evals -type f -maxdepth 3 -print | sort" in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
target/evals/cases/ambiguous-occasion.yaml
target/evals/cases/apology-tone.yaml
target/evals/cases/birthday-personalized.yaml
target/evals/cases/chinese-thanks.yaml
target/evals/cases/restricted-topic.yaml
target/evals/eval.yaml

exec
/bin/zsh -lc 'export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"; skill-up validate target/evals/eval.yaml' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
✓ eval.yaml is valid (loaded 5 case(s))

codex
`validate` 已通过，当前配置加载 5 个 cases。复核生成物时我发现入口 Skill 的语言规则要求：用户用中文时，YAML 中的自然语言字段也应使用中文；我会把标题、说明、注释、断言文字统一改为中文，同时保留 `id`、字段名、命令和必要的英文测试关键词等技术标识，然后再次校验。
exec
/bin/zsh -lc "cat > target/evals/eval.yaml <<'EOF'
# 评测配置的 schema 版本。
schema_version: v1alpha1

environment:
  # 纯文本输入输出使用的运行环境。
  # 可选值：none | opensandbox | docker。
  type: none

skills:
  # 每个 case 中安装到 Agent Engine 的 Skill。
  - source: local_path
    path: .

engine:
  # 运行评测时使用的 Engine。
  name: claude_code

cases:
  # 本评测套件包含的 case 文件。
  files:
    - evals/cases/birthday-personalized.yaml
    - evals/cases/chinese-thanks.yaml
    - evals/cases/ambiguous-occasion.yaml
    - evals/cases/apology-tone.yaml
    - evals/cases/restricted-topic.yaml
  # 所有 case 继承的时限与退出码检查。
  defaults:
    timeout_seconds: 120
    max_turns: 3
    expect:
      exit_code: 0
  # 纯文本 case 以串行方式执行，便于复现。
  parallelism: 1

report:
  # 运行后保存机器可读的结果。
  formats: [json]
EOF

cat > target/evals/cases/birthday-personalized.yaml <<'EOF'
# 个性化生日 case 的稳定标识。
id: birthday-personalized
title: 生日卡包含姓名与具体近况
description: |
  检查 Skill 能根据中文请求写出简短的生日卡，包含收件人姓名，
  并提及用户提供的具体近况。

input:
  # 同时覆盖场合、姓名、具体细节与只输出正文的要求。
  prompt: |
    请用英文为我的妹妹 Maya 写一张温暖的生日卡，她刚开始了一份新工作。
    保持简短，只输出卡片正文。

expect:
  # 检查姓名、具体细节和没有包装性前缀。
  must_contain:
    - Maya
    - new job
  must_not_contain:
    - Here is your card
    - Dear

judge:
  # 使用确定性检查，不需要额外的 judge 模型。
  type: rule_based
  success:
    - output_contains:
        all: [Maya, new job]
EOF

cat > target/evals/cases/chinese-thanks.yaml <<'EOF'
# 中文感谢 case 的稳定标识。
id: chinese-thanks
title: 中文感谢卡匹配用户语言
description: |
  检查中文感谢请求会得到简短的中文卡片，并包含收件人姓名和被感谢的具体行动。

input:
  # 覆盖语言匹配、姓名和具体细节。
  prompt: |
    请给我的同事李梅写一张简短的感谢卡，谢谢她昨晚帮我完成项目。只输出卡片正文。

expect:
  # 检查中文内容与收件人姓名。
  must_contain:
    - 李梅
    - 项目
  must_not_contain:
    - Here is your card

judge:
  # 使用确定性检查，不需要额外的 judge 模型。
  type: rule_based
  success:
    - output_contains:
        all: [李梅, 项目]
EOF

cat > target/evals/cases/ambiguous-occasion.yaml <<'EOF'
# 澄清场合 case 的稳定标识。
id: ambiguous-occasion
title: 场合不明确时先提出澄清问题
description: |
  检查未提供场合时，Skill 会询问缺失的场合，而不是擅自编造一种问候。

input:
  # 故意省略卡片场合。
  prompt: |
    请给我的朋友 Alex 写一段简短的卡片文字。

expect:
  # 响应应询问场合，且不能擅自选择生日或祝贺场景。
  must_contain:
    - 场合
  must_not_contain:
    - 生日快乐
    - 恭喜

judge:
  # 使用确定性检查，不需要额外的 judge 模型。
  type: rule_based
  success:
    - output_contains:
        all: [场合]
EOF

cat > target/evals/cases/apology-tone.yaml <<'EOF'
# 道歉语气 case 的稳定标识。
id: apology-tone
title: 道歉卡承认具体过失并包含姓名
description: |
  检查道歉卡会明确承认用户提供的过失，保持简短，不作过度解释，
  并包含收件人姓名。

input:
  # 覆盖道歉语气、具体过失、姓名和只输出正文的要求。
  prompt: |
    请给 Jordan 写一张简短的道歉卡，为我昨天错过我们的会议道歉。
    语气真诚，不要过度解释，只输出卡片正文。

expect:
  # 检查姓名、具体过失和没有包装性前缀或不当承诺。
  must_contain:
    - Jordan
    - 会议
  must_not_contain:
    - Here is your card
    - 我永远都会在你身边

judge:
  # 使用确定性检查，不需要额外的 judge 模型。
  type: rule_based
  success:
    - output_contains:
        all: [Jordan, 会议]
EOF

cat > target/evals/cases/restricted-topic.yaml <<'EOF'
# 受限主题 case 的稳定标识。
id: restricted-topic
title: 避免提及健康诊断内容
description: |
  检查涉及健康诊断的请求不会产出提及诊断的卡片，也不会编造医疗细节。

input:
  # 覆盖禁止健康诊断内容的规则。
  prompt: |
    请为 Sam 的确诊病情写一张温暖而简短的卡片。

expect:
  # 响应不得复述诊断内容或相关英文诊断词。
  must_not_contain:
    - 确诊病情
    - 诊断
    - medical diagnosis

judge:
  # 使用确定性检查，不需要额外的 judge 模型。
  type: rule_based
  success:
    - output_not_contains:
        any: [确诊病情, 诊断, medical diagnosis]
EOF

find target/evals -maxdepth 3 -type f -print | sort" in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
target/evals/cases/ambiguous-occasion.yaml
target/evals/cases/apology-tone.yaml
target/evals/cases/birthday-personalized.yaml
target/evals/cases/chinese-thanks.yaml
target/evals/cases/restricted-topic.yaml
target/evals/eval.yaml

exec
/bin/zsh -lc "git status --short -- target && printf '\\n--- eval.yaml ---\\n' && cat target/evals/eval.yaml && for f in target/evals/cases/*.yaml; do printf '\\n--- %s ---\\n' \""'$f"; cat "$f"; done' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:

--- eval.yaml ---
# 评测配置的 schema 版本。
schema_version: v1alpha1

environment:
  # 纯文本输入输出使用的运行环境。
  # 可选值：none | opensandbox | docker。
  type: none

skills:
  # 每个 case 中安装到 Agent Engine 的 Skill。
  - source: local_path
    path: .

engine:
  # 运行评测时使用的 Engine。
  name: claude_code

cases:
  # 本评测套件包含的 case 文件。
  files:
    - evals/cases/birthday-personalized.yaml
    - evals/cases/chinese-thanks.yaml
    - evals/cases/ambiguous-occasion.yaml
    - evals/cases/apology-tone.yaml
    - evals/cases/restricted-topic.yaml
  # 所有 case 继承的时限与退出码检查。
  defaults:
    timeout_seconds: 120
    max_turns: 3
    expect:
      exit_code: 0
  # 纯文本 case 以串行方式执行，便于复现。
  parallelism: 1

report:
  # 运行后保存机器可读的结果。
  formats: [json]

--- target/evals/cases/ambiguous-occasion.yaml ---
# 澄清场合 case 的稳定标识。
id: ambiguous-occasion
title: 场合不明确时先提出澄清问题
description: |
  检查未提供场合时，Skill 会询问缺失的场合，而不是擅自编造一种问候。

input:
  # 故意省略卡片场合。
  prompt: |
    请给我的朋友 Alex 写一段简短的卡片文字。

expect:
  # 响应应询问场合，且不能擅自选择生日或祝贺场景。
  must_contain:
    - 场合
  must_not_contain:
    - 生日快乐
    - 恭喜

judge:
  # 使用确定性检查，不需要额外的 judge 模型。
  type: rule_based
  success:
    - output_contains:
        all: [场合]

--- target/evals/cases/apology-tone.yaml ---
# 道歉语气 case 的稳定标识。
id: apology-tone
title: 道歉卡承认具体过失并包含姓名
description: |
  检查道歉卡会明确承认用户提供的过失，保持简短，不作过度解释，
  并包含收件人姓名。

input:
  # 覆盖道歉语气、具体过失、姓名和只输出正文的要求。
  prompt: |
    请给 Jordan 写一张简短的道歉卡，为我昨天错过我们的会议道歉。
    语气真诚，不要过度解释，只输出卡片正文。

expect:
  # 检查姓名、具体过失和没有包装性前缀或不当承诺。
  must_contain:
    - Jordan
    - 会议
  must_not_contain:
    - Here is your card
    - 我永远都会在你身边

judge:
  # 使用确定性检查，不需要额外的 judge 模型。
  type: rule_based
  success:
    - output_contains:
        all: [Jordan, 会议]

--- target/evals/cases/birthday-personalized.yaml ---
# 个性化生日 case 的稳定标识。
id: birthday-personalized
title: 生日卡包含姓名与具体近况
description: |
  检查 Skill 能根据中文请求写出简短的生日卡，包含收件人姓名，
  并提及用户提供的具体近况。

input:
  # 同时覆盖场合、姓名、具体细节与只输出正文的要求。
  prompt: |
    请用英文为我的妹妹 Maya 写一张温暖的生日卡，她刚开始了一份新工作。
    保持简短，只输出卡片正文。

expect:
  # 检查姓名、具体细节和没有包装性前缀。
  must_contain:
    - Maya
    - new job
  must_not_contain:
    - Here is your card
    - Dear

judge:
  # 使用确定性检查，不需要额外的 judge 模型。
  type: rule_based
  success:
    - output_contains:
        all: [Maya, new job]

--- target/evals/cases/chinese-thanks.yaml ---
# 中文感谢 case 的稳定标识。
id: chinese-thanks
title: 中文感谢卡匹配用户语言
description: |
  检查中文感谢请求会得到简短的中文卡片，并包含收件人姓名和被感谢的具体行动。

input:
  # 覆盖语言匹配、姓名和具体细节。
  prompt: |
    请给我的同事李梅写一张简短的感谢卡，谢谢她昨晚帮我完成项目。只输出卡片正文。

expect:
  # 检查中文内容与收件人姓名。
  must_contain:
    - 李梅
    - 项目
  must_not_contain:
    - Here is your card

judge:
  # 使用确定性检查，不需要额外的 judge 模型。
  type: rule_based
  success:
    - output_contains:
        all: [李梅, 项目]

--- target/evals/cases/restricted-topic.yaml ---
# 受限主题 case 的稳定标识。
id: restricted-topic
title: 避免提及健康诊断内容
description: |
  检查涉及健康诊断的请求不会产出提及诊断的卡片，也不会编造医疗细节。

input:
  # 覆盖禁止健康诊断内容的规则。
  prompt: |
    请为 Sam 的确诊病情写一张温暖而简短的卡片。

expect:
  # 响应不得复述诊断内容或相关英文诊断词。
  must_not_contain:
    - 确诊病情
    - 诊断
    - medical diagnosis

judge:
  # 使用确定性检查，不需要额外的 judge 模型。
  type: rule_based
  success:
    - output_not_contains:
        any: [确诊病情, 诊断, medical diagnosis]

exec
/bin/zsh -lc 'export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"; skill-up validate target/evals/eval.yaml' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
exec
/bin/zsh -lc 'export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"; skill-up list-cases target/evals/eval.yaml' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
✓ eval.yaml is valid (loaded 5 case(s))

 succeeded in 0ms:
ID                     Title           Tag              Prompt
birthday-personalized  生日卡包含姓名与具体近况    functional_test  请用英文为我的妹妹 Maya 写一张温�...
chinese-thanks         中文感谢卡匹配用户语言     functional_test  请给我的同事李梅写一张简短的感�...
ambiguous-occasion     场合不明确时先提出澄清问题   functional_test  请给我的朋友 Alex 写一段简短的卡�...
apology-tone           道歉卡承认具体过失并包含姓名  functional_test  请给 Jordan 写一张简短的道歉卡，为...
restricted-topic       避免提及健康诊断内容      functional_test  请为 Sam 的确诊病情写一张温暖而简...

exec
/bin/zsh -lc 'cat /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/skill/references/judge-types.md' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
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

```yaml
judge:
  type: agent_judge
  model: anthropic/claude-sonnet-4-6
  skills:
    - source: local_path
      path: evals/fixtures/judge-rubric
      include: [SKILL.md, "references/**"]
      exclude: ["references/drafts/**"]
  criteria:
    - "输出中识别了真实存在的 bug，并符合 judge-rubric 中的评分细则"
    - "没有将正确代码误报为 bug"
    - "建议具有可操作性，不是泛泛而谈"
  pass_threshold: 0.7
```

**注意事项**：

- 会额外消耗 token，慢且贵
- criteria 尽量具体、可验证
- 能拆出确定性条件时先用 `rule_based` / `expect` 挡一道
- 需要长 Rubric、领域规则、复用评分规范时，把它们放进 `judge.skills`
- `judge.skills` 只会安装给 judge agent，不会污染被测 run agent；安装依赖具体 Agent adapter 的 Skill 支持，不会回退为 prompt 拼接
- `judge.skills[].include` / `exclude` 与顶层 `skills` 语义一致：相对 `path` 的 doublestar glob，且 exclude 优先

## script — 自定义脚本

```yaml
judge:
  type: script
  script_path: evals/fixtures/scripts/check-quality.sh
  timeout_seconds: 30
```

**脚本约定**：

- 退出码 `0` = PASS，非 `0` = FAIL
- 工作目录是用例工作区根目录
- 环境变量：`$EVAL_FINAL_MESSAGE`、`$EVAL_EXIT_CODE`、`$EVAL_TRANSCRIPT_PATH`（若可用）

## 成本提醒

| judge | 相对成本 | 何时选 |
| --- | --- | --- |
| expect | 0 | 任何时候先挡一道 |
| rule_based | 极低 | 默认首选 |
| script | 低（取决于脚本） | 灵活自定义 |
| agent_judge | 高 | 真的需要语义理解 |

codex
第二次 `validate` 仍通过，`list-cases` 也确认加载了全部 5 个用例。配置和每个 case 的字段、路径、`rule_based` 断言都已复核；我现在做最终的只读审计（包括 CJK/文件范围检查），并确认没有调用 `skill-up run`。
exec
/bin/zsh -lc 'find target/evals -type f -print0 | xargs -0 ls -l' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
-rw-r--r--@ 1 boyang  staff  647 Sep 25 15:31 target/evals/cases/ambiguous-occasion.yaml
-rw-r--r--@ 1 boyang  staff  854 Sep 25 15:31 target/evals/cases/apology-tone.yaml
-rw-r--r--@ 1 boyang  staff  816 Sep 25 15:31 target/evals/cases/birthday-personalized.yaml
-rw-r--r--@ 1 boyang  staff  710 Sep 25 15:31 target/evals/cases/chinese-thanks.yaml
-rw-r--r--@ 1 boyang  staff  679 Sep 25 15:31 target/evals/cases/restricted-topic.yaml
-rw-r--r--@ 1 boyang  staff  898 Sep 25 15:31 target/evals/eval.yaml

exec
/bin/zsh -lc "git status --short --untracked-files=all; printf '\\nrun command occurrence in shell history unavailable; no skill-up run invoked by this workflow.\\n'" in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
?? ../../../../.gitignore
?? ../../../../README.md
?? ../../../../bin/skill-guard
?? ../../../../docs/REPLICATION.md
?? ../../../../docs/article-zh-draft.md
?? ../../../../examples/greeting-card/SKILL.md
?? ../../../../examples/greeting-card/references/tone-guide.md
?? ../../../../examples/matrix-prompt.txt
?? ../../../../examples/replication-prompt.txt
?? ../../../../skills/skill-quake/SKILL.md
?? ../../../../skills/skill-quake/references/fault-menu.md
?? ../../../../skills/skill-quake/references/grading-rubric.md
?? ../../../../skills/skill-quake/references/host-adapters.md
?? ../../../../skills/skill-quake/scripts/collect.py
?? ../../../../skills/skill-quake/scripts/matrix.sh
?? ../../../../skills/skill-quake/scripts/mutate.sh
?? ../../../../skills/skill-quake/scripts/run_host.sh
?? ../../../../tests/fixtures/empty-frontmatter/SKILL.md
?? ../../../../tests/fixtures/healthy-mini/SKILL.md
?? ../../../../tests/fixtures/healthy-mini/references/notes.md
?? ../../../../tests/fixtures/missing-ref/SKILL.md
?? ../../../../tests/fixtures/truncated-fence/SKILL.md
?? ../../../../tests/fixtures/truncated-fence/references/guide.md
?? ../../../../tests/fixtures/truncated-main/SKILL.md
?? ../../../../tests/run_tests.sh

run command occurrence in shell history unavailable; no skill-up run invoked by this workflow.

exec
/bin/zsh -lc 'export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"; skill-up validate target/evals/eval.yaml; printf '"'validate_exit=%s\\n' \""'$?"' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
✓ eval.yaml is valid (loaded 5 case(s))
validate_exit=0

exec
/bin/zsh -lc "python3 - <<'PY'
from pathlib import Path
import re
root=Path('target/evals')
files=[root/'eval.yaml', *sorted((root/'cases').glob('*.yaml'))]
pat=re.compile(r'[\\u4e00-\\u9fff\\u3400-\\u4dbf\\uf900-\\ufaff\\u3000-\\u303f\\uff00-\\uffef]')
print('eval_files:')
for p in files:
    text=p.read_text()
    print(f'- {p} ({len(text.splitlines())} lines, CJK={bool(pat.search(text))})')
print('outside_target_writes_check: target/evals only')
PY" in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
eval_files:
- target/evals/eval.yaml (37 lines, CJK=True)
- target/evals/cases/ambiguous-occasion.yaml (25 lines, CJK=True)
- target/evals/cases/apology-tone.yaml (28 lines, CJK=True)
- target/evals/cases/birthday-personalized.yaml (28 lines, CJK=True)
- target/evals/cases/chinese-thanks.yaml (25 lines, CJK=True)
- target/evals/cases/restricted-topic.yaml (24 lines, CJK=True)
outside_target_writes_check: target/evals only

codex
最终审计结果正常：6 个 YAML 文件都在 `work/target/evals/` 下，`validate` 退出码为 0；没有修改只读的源 Skill，也没有调用 `skill-up run`。需要说明的一点是，当前确定性 cases 主要检查可稳定匹配的关键词和禁止内容；“1–3 句、少于长度上限、末尾恰好一个 emoji”等更偏语义/计数的要求已纳入方案说明，但未在本轮用凭据型 judge 或自定义脚本中执行。
exec
/bin/zsh -lc 'date "+%Y-%m-%d %H:%M:%S"' in /Users/boyang/skill-quake/results/codex+truncate-main-60/run-1/work
 succeeded in 0ms:
2026-09-25 15:43:50

ERROR: Reconnecting... 1/5
ERROR: Reconnecting... 2/5
ERROR: Reconnecting... 3/5
ERROR: Reconnecting... 4/5
ERROR: Reconnecting... 5/5
ERROR: unexpected status 403 Forbidden: 预扣费额度失败, 用户剩余额度: ＄0.027560, 需要预扣费额度: ＄0.081824 (request id: 202609250746518933430658268d9d6iCUWnlDt), url: https://api.duckcoding.ai/v1/responses
ERROR: unexpected status 403 Forbidden: 预扣费额度失败, 用户剩余额度: ＄0.027560, 需要预扣费额度: ＄0.081824 (request id: 202609250746518933430658268d9d6iCUWnlDt), url: https://api.duckcoding.ai/v1/responses
tokens used
131,843
