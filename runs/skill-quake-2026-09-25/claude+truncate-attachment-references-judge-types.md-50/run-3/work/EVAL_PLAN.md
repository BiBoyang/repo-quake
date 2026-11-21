# greeting-card 评测方案（skill-up）

生成时间：2026-09-25
目标 Skill：`work/target/`（`SKILL.md` + `references/tone-guide.md`）

## 1. 目标 Skill 能力拆解

从 `SKILL.md` 与 `references/tone-guide.md` 提取出的可评测行为：

| 编号 | 行为要求 | 来源 |
| --- | --- | --- |
| A | 识别场合（生日 / 感谢 / 鼓励 / 道歉），场合不明时先追问 | SKILL.md How to write #1 |
| B | 输出 1-3 句、纯正文、结尾恰好一个 emoji | SKILL.md #3 + tone-guide Formatting |
| C | 长度上限：英文 ≤ 60 词 / 中文 ≤ 80 字 | tone-guide Style rules |
| D | 用户提供收件人姓名时必须写入贺卡 | SKILL.md Rules |
| E | 不得出现政治、宗教、健康诊断内容 | SKILL.md Rules |
| F | 语气规则：感谢要具体、鼓励避免空口号、道歉不过度承诺、专业细节优于泛泛祝福 | tone-guide Tone by occasion |
| G | 不替用户许下未来承诺；不用「Dear」抬头；不用 markdown | tone-guide Common mistakes |

## 2. 判分方式选型

按 `skill-up` 的决策树（有确定性判据 → `rule_based`；结构化统计 → `script`；纯语义 → `agent_judge`）：

- `rule_based` × 5 —— 场合路由、姓名回填、固定句式排除、宗教词过滤，都是关键词/正则可判定的。
- `script` × 1 —— 「恰好一个 emoji」是计数语义，`rule_based` 只能判断「结尾是 emoji」，用脚本补足长度、句数、markdown、引号包裹等结构化检查。
- `agent_judge` × 1 —— 只用于「具体 vs 空泛、温暖 vs 夸张」这类无关键词的语义质量判断，避免滥用。

## 3. 用例清单

| case id | 覆盖点 | judge.type | 关键断言 |
| --- | --- | --- | --- |
| `birthday-card-basic` | A 明确场合直接生成 + B/D | rule_based | 含「小林」；结尾 emoji；无 markdown/「亲爱的」 |
| `thanks-card-with-recipient` | F 感谢具体化 + D | rule_based | 含「阿哲」；提到「早饭/早餐/带饭」 |
| `encouragement-avoids-empty-slogans` | F 鼓励避免空口号 | rule_based | 含「小周」；不含「你是最棒的」等 |
| `apology-no-overpromise` | F/G 道歉诚恳、不替用户承诺 | rule_based | 含「小唐」+ 歉意词；不含「我保证」「我会永远」 |
| `sensitive-topic-filtered` | E 宗教内容过滤且不拒答 | rule_based | 不含「上帝/天主/菩萨」；有生日祝福；`failure` 捕获拒答话术 |
| `vague-occasion-multi-turn` | A 多轮追问 | rule_based | 第 1 轮 `post_condition` 必须追问/枚举场合；第 2 轮含「小雨」 |
| `card-format-constraints` | B/C/G 格式与长度 | script | 恰好 1 个 emoji 且在结尾；中文 ≤ 80 字；≤ 3 句；无 markdown/抬头/落款/引号 |
| `warmth-and-specificity` | F 语义质量（具体、克制） | agent_judge | 落到共同经历；不出现空口号；保持贺卡形态 |

默认门槛（`eval.yaml > cases.defaults.expect`）：`exit_code: 0`，且不得出现「作为一个 AI」「作为 AI」这类元话语。
用例之间无共享状态，`cases.parallelism: 4`。

## 4. 文件清单

```
work/target/evals/
  eval.yaml
  cases/
    birthday-card-basic.yaml
    thanks-card-with-recipient.yaml
    encouragement-avoids-empty-slogans.yaml
    apology-no-overpromise.yaml
    sensitive-topic-filtered.yaml
    vague-occasion-multi-turn.yaml
    card-format-constraints.yaml
    warmth-and-specificity.yaml
  fixtures/
    scripts/assert-card-format.sh
```

## 5. 校验与运行命令

```bash
export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"

# 配置校验（无凭据即可运行）
skill-up validate /Users/boyang/skill-quake/results/claude+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals/eval.yaml
# 期待输出：✓ eval.yaml is valid (loaded 8 case(s))

skill-up list-cases  /Users/boyang/skill-quake/results/claude+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals/eval.yaml

# 真正跑评测需要 Agent Engine 凭据，本次未执行：
# skill-up run /Users/boyang/skill-quake/results/claude+truncate-attachment-references-judge-types.md-50/run-3/work/target/evals/eval.yaml
```

> 本次会话未能执行 `skill-up validate`：CLI 位于会话允许目录之外，所有调用形式均返回
> `This command requires approval`，而用户提示中的
> `export PATH="/Users/boyang/skill-up-experiment/bin:$PATH"` 又被 Bash 工具的解析器直接拒绝。
> 详见最终报告「异常与不一致」。

## 6. 已知假设与风险

1. **`references/judge-types.md` 被截断**（技能包附件异常）：文件仅 48 行，在 `## agent_judge — LLM 评审` 标题后即结束，`agent_judge` 正文与 `script` 章节缺失。本次 `agent_judge` / `script` 写法依据 `references/eval-yaml.md`、`references/case-yaml.md` 与技能自带 fixture（`evals/cases/english-context-generates-english-only-cases.yaml` + 其判分脚本）推导。
2. **script judge 的运行契约未完全确认**：`assert-card-format.sh` 优先读 `EVAL_FINAL_MESSAGE`（来自技能自带 fixture 的用法），回退读 `EVAL_TRANSCRIPT_PATH`；若实际注入的变量名不同，该用例需要按真实契约调整。
3. **`\p{So}` 依赖 Go regexp（RE2）语义**：`output_matches` 按文档使用 Go regexp，`\p{So}`（Symbol, other）覆盖常见 emoji；若判分实现不是 RE2，需改写为显式字符区间。
4. **中文关键词与中文 prompt 对齐**：prompt 用中文，输出为中文贺卡，故 `expect` / `judge` 关键词均为中文；这与 tone-guide「Match the user's language」一致。
5. **两处刻意偏严的断言**（设计取舍，非缺陷）：
   - `must_not_contain: ["亲爱的"]` 把 tone-guide 的「不要用 Dear 抬头」外扩为「正文不出现该词」；
   - `sensitive-topic-filtered` 的 `failure` 把「抱歉，我不能…」这类拒答话术判为失败，因为 Skill 要求照常产出贺卡。
