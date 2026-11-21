# greeting-card Skill 评测方案

本文件由 skill-upper 流程（Step 1 → Step 4）生成，记录为 `work/target/` 下的
`greeting-card` Skill 设计的一套 skill-up 评测方案。

## 1. 被测 Skill

| 项 | 值 |
| --- | --- |
| 名称 | `greeting-card` |
| 根目录 | `work/target/`（`SKILL.md` 所在目录） |
| 能力 | 按场合写 1-3 句、以单个 emoji 结尾的问候卡片，语言跟随用户 |
| 依赖文件 | `references/tone-guide.md`（语气、长度、格式细则） |
| 评测前状态 | 无 `evals/` 目录，无 `evals.json` → 走 skill-up Step 2 全新搭建 |

## 2. 目录结构

```
work/target/
  SKILL.md
  references/tone-guide.md
  evals/
    eval.yaml
    cases/
      birthday-basic.yaml
      thanks-includes-recipient-name.yaml
      english-input-english-card.yaml
      forbidden-topics.yaml
      occasion-unclear-asks-back.yaml
      encouragement-avoids-empty-slogan.yaml
      apology-sincere.yaml
```

## 3. eval.yaml 关键配置

| 字段 | 取值 | 理由 |
| --- | --- | --- |
| `environment.type` | `none` | 纯文本输入输出，不需要沙箱，冷启动最快 |
| `skills[].path` | `.` | 被测 Skill 即 Skill 根目录自身；`evals/` 不会被安装 |
| `engine.name` | `claude_code` | 默认引擎 |
| `engine.model` | 不配置 | 交由引擎默认模型接管，规避自建网关模型别名不匹配 |
| `cases.defaults.timeout_seconds` | `120` | 单轮文本任务，余量充足 |
| `cases.defaults.max_turns` | `4` | 纯文本生成，不需要多轮工具调用 |
| `cases.defaults.expect.exit_code` | `0` | 低成本默认门槛 |
| `report.formats` | `[json, html]` | 便于人工复核 |
| `benchmark.enabled` | 未启用 | 未要求基线对比，避免翻倍消耗 |

## 4. 用例清单

7 个用例覆盖 SKILL.md 与 tone-guide.md 中可判定的行为契约。

| 用例 ID | 覆盖点 | judge 类型 | 判定方式 |
| --- | --- | --- | --- |
| `birthday-basic` | 生日场合 + 姓名入卡 + 结尾单 emoji | rule_based | 子串 + 正则 |
| `thanks-includes-recipient-name` | 感谢场合 + 姓名入卡 | rule_based | 子串 + 正则 |
| `english-input-english-card` | 语言跟随输入（英文） | rule_based | 正则：正文须无 CJK |
| `forbidden-topics` | 不涉及政治 / 宗教 / 健康 | rule_based | 否定子串 + 切题子串 |
| `occasion-unclear-asks-back` | 场合不明时先追问 | rule_based | 子串（问号 / “场合”） |
| `encouragement-avoids-empty-slogan` | 鼓励语气稳健具体、无空泛口号 | agent_judge | 4 条 criteria，阈值 0.7 |
| `apology-sincere` | 道歉真诚、不推责、不过度解释 | agent_judge | 4 条 criteria，阈值 0.7 |

### 判定细节

- **emoji 契约**：`tone-guide.md` 要求“Exactly one emoji, placed at the very end”。
  正则 `[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}][\x{FE0E}\x{FE0F}\x{200D}\x{1F3FB}-\x{1F3FF}]*\s*$`
  判定“以 emoji 结尾”，并容忍变体选择符（如 ❤️）与结尾空白；
  另一条否定正则判定“禁止叠加多个 emoji”。
- **语言跟随**：英文用例断言正文不出现 CJK（`[\x{4e00}-\x{9fff}\x{3400}-\x{4dbf}]`），
  这是该用例的关键断言，避免“用中文回英文 prompt”蒙混过关。
- **`forbidden-topics` 双向断言**：既要求“不出现政治 / 宗教 / 健康词”，
  也要求“仍然是一张生日卡片”（`any: ["生日", "寿", "大伯"]`），
  防止用空输出或拒答来通过否定断言。
- **`occasion-unclear-asks-back`**：刻意不检查卡片格式，因为预期输出是追问而非卡片。

### judge 选型理由

- 能确定性判定的（子串、正则、格式契约）一律用 `rule_based`，配 `expect` 先做零成本拦截。
- 只有“语气是否稳健具体”“道歉是否真诚不推责”这类纯语义判断才用 `agent_judge`，
  共 2 个用例，占比 2/7，避免滥用高价评审。
- 未使用 `script`：本套用例的确定性断言都能用 `rule_based` 表达，
  引入依赖宿主工具链的脚本反而增加不可控因素。

## 5. 校验与运行

```bash
export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"
skill-up validate /Users/boyang/skill-quake/results/claude+truncate-attachment-references-judge-types.md-50/run-1/work/target/evals/eval.yaml
skill-up list-cases /Users/boyang/skill-quake/results/claude+truncate-attachment-references-judge-types.md-50/run-1/work/target/evals/eval.yaml
```

预期输出：`✓ eval.yaml is valid (loaded 7 case(s))`

> 执行状态：**未执行成功**。本会话的 Bash 工具只允许访问
> `run-1/work` 与 `run-1/skill` 两个目录，`/Users/boyang/skill-up-experiment/bin/skill-up`
> 在允许目录之外，每次调用都被拒绝（`This command requires approval`）。
> 因此 `validate` / `list-cases` 均未实际运行，YAML 仅经过人工比对
> `references/eval-yaml.md`、`references/case-yaml.md` 与 `assets/*.tmpl` 校验。
> 详见交付报告。

## 6. 后续建议

1. 先跑通 `validate`，再在具备 Agent Engine 凭据的环境执行
   `skill-up run <eval.yaml>`（当前机器无凭据，按要求未运行）。
2. 若需要“装了 Skill vs 没装 Skill”的对照，追加 `--baseline`。
3. 若 `occasion-unclear-asks-back` 出现反复抖动，可先用 `--iteration 3`
   采样确认是不稳定还是稳定失败，再决定是否放宽断言。
4. 若后续想收紧长度契约（1-3 句 / 中文 ≤80 字），可新增一个 `script` judge 用例，
   在脚本里做精确计数。
