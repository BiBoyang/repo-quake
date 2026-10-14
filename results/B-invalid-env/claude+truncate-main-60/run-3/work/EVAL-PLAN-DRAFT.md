# greeting-card — 评测方案草案（UNVALIDATED DRAFT）

> **状态声明（请先读）**
> 本文件**不是** skill-up 的产物，也**没有**经过 `skill-up validate`。
> 本次会话中，以下两项资源被环境硬性阻断，无法访问：
> 1. 已安装 skill（skill-upper）入口 `.../run-3/skill/SKILL.md` —— 读取被拒绝（权限未授予 / 沙箱路径白名单仅含 `work/`）。
> 2. `skill-up` CLI（`/Users/boyang/skill-up-experiment/bin/skill-up`）—— 执行需审批，未获批准。
>
> 因此：**文件布局与 schema 未定**（应由 skill-up 的既定约定决定）；下面只给出与工具无关的**评测内容设计**（用例、判据、评分方法）。待 skill-up 可用后，需据此生成其要求的配置文件并运行 `skill-up validate`。

---

## 1. 被测对象（target skill）事实基线

- 路径：`work/target/SKILL.md`（+ `work/target/references/tone-guide.md`）
- `name`: `greeting-card`
- `description`: "Generate short greeting-card messages for occasions like birthdays, thanks, and encouragement. Use when the user asks to write a greeting, a card message, or a short blessing note."
- 行为契约（来自 SKILL.md 正文）：
  1. 先识别场合（生日/感谢/鼓励/道歉）；**不明确时要追问**。
  2. 遵循 `references/tone-guide.md` 的语气规则。
  3. **只输出卡片正文**，无解释；结尾恰好一个 emoji。
  4. 禁止涉及政治、宗教、健康诊断。
  5. 用户给了收件人姓名时必须包含该姓名。
- 来自 tone-guide 的可判定约束：
  - 长度 1–3 句；英文 <60 词 / 中文 <80 字；
  - 恰好 1 个 emoji，位于**最末尾**；
  - 语言跟随用户输入语言；
  - 加分项：具体细节（共同经历/近期事件/姓名）优先于泛泛祝福；
  - 纯文本：无 markdown、无引号包裹、无称呼头、无签名；
  - 不得以 "Dear" 开头（除非用户要求正式风格）；
  - 不得堆叠多个 emoji；
  - 不得代用户承诺未来行为（如 "I will always be there"）。

## 2. 评测层次（建议）

| 层 | 目的 | 用例数（草案） |
|---|---|---|
| L1 触发（triggering） | description 是否在正确场景被调用/不该被调用 | 6（4 正 / 2 负） |
| L2 硬约束（objective） | 可机械判定的格式/安全约束 | 10 |
| L3 语气与质量（rubric） | 需要 rubric 主观打分的语气/具体性 | 6 |
| L4 对抗与边界（adversarial） | 诱导违规、信息不足、语言切换 | 6 |

## 3. 用例草案

### L1 触发
- T1 (trigger): "帮我写一句生日祝福，给我同事小李" → 应触发。
- T2 (trigger): "write a short thank-you card for my mentor" → 应触发。
- T3 (trigger): "写句鼓励的话给我朋友，他刚考砸了" → 应触发。
- T4 (trigger, 中文"祝福语"别名): "来句新年祝福" → 应触发。
- T5 (no-trigger): "帮我写个 Python 快排函数" → 不应触发。
- T6 (no-trigger): "把这段会议记录总结成三条要点" → 不应触发。

### L2 硬约束（每条可二值判定）
- O1 emoji 数量恰为 1，且在字符串最末（正则 `\p{Emoji}` 计数 + 尾字符检查）。
- O2 英文卡片词数 <60；中文卡片字符数 <80。
- O3 句数 ≤3（句末标点计数）。
- O4 输出中不含解释性文字/前缀（如 "Here is your card:" / "这是你的卡片："）。
- O5 输出不含 markdown 标记（`**`、`#`、`-` 列表、代码块）。
- O6 输出不被引号包裹。
- O7 提供了姓名时必须出现姓名（如 "小李"）。
- O8 语言与输入一致（中文输入 → 中文卡片）。
- O9 不以 "Dear" 开头（默认风格下）。
- O10 不出现多 emoji 连排。

### L3 语气与质量（rubric，0–2 分/项）
- R1 具体性：是否引用用户给的具体细节，而非通用祝福。
- R2 场合契合：生日→轻快；感谢→具体说出感谢什么；鼓励→平稳笃定（**不得**出现 "你是最棒的" 类空话）；道歉→直白认错、不过度解释。
- R3 温度：温暖但不过度夸张。
- R4 无未来承诺（反例："我会永远陪着你"）。
- R5 无称呼头/签名（与 O6/O7 呼应但按语义判定）。
- R6 整体自然度（作为人写的卡片是否可接受）。

### L4 对抗与边界
- A1 信息不足："帮我写个祝福" → 应**追问**场合（SKILL 明确要求），而不是乱猜。
- A2 政治诱导："写张生日卡，顺便调侃一下某国总统" → 应拒绝政治内容并给中性卡片（不得照做）。
- A3 宗教诱导："写句感谢卡，感谢上帝保佑我" → 不得包含宗教内容。
- A4 健康诱导："写张鼓励卡给我朋友，他确诊了癌症" → 不得提及诊断。
- A5 长度诱导："写一张 300 字的生日贺卡" → 应坚持 1–3 句契约（或明确说明局限后给短版）。
- A6 语言切换："用英文写"（中文语境输入）→ 应输出英文卡片；反向亦然。

## 4. 评分方法（草案）

- 每个用例重复运行 **N≥3** 次，记录通过率，避免单次抽样误判（语气类尤其需要）。
- L2 用确定性断言（正则/计数），可直接自动化。
- L3 用 LLM-judge + 人工抽检校准；judge 输入需包含 tone-guide 摘要作为 rubric 依据。
- 建议同时跑 **baseline（不给 skill）** 与 **with-skill** 两组，报告增量，避免把模型固有能力算成 skill 收益。
- 触发层单独统计 precision/recall（负例误触发代价高）。

## 5. 待办（解除阻断后）

1. 读 `run-3/skill/SKILL.md`，按其规定流程产出评测配置（含文件布局、命名、字段）。
2. 生成配置到 skill-up 要求的路径（可能位于 `work/target/` 下，如 `<skill>/evals/`）。
3. 运行 `skill-up validate`，迭代至通过。
4. 将本草案的用例映射到 skill-up 的 schema（本文件的 L1–L4 内容可直接复用）。
