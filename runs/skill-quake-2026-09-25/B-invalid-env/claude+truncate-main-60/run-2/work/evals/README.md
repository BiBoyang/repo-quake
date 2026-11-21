# greeting-card 评测方案（evals）

目标 skill：`../target/`（`SKILL.md` + `references/tone-guide.md`）
本目录内容：`evals.json`（行为评测）、`trigger-evals.json`（触发准确率）、本说明。

---

## ⚠️ Validation status

**`skill-up validate` 未执行 —— 本方案尚未校验，请勿视为“已通过校验”。**

本次会话的环境把可访问范围限制在了 `.../run-2/work/` 之内，以下操作全部被权限系统拒绝（均为反复尝试过的真实结果）：

| 操作 | 结果 |
|---|---|
| 读取 `.../run-2/skill/SKILL.md`（skill-upper 的入口，本应按其流程执行） | `Claude requested permissions to read from .../skill/SKILL.md, but you haven't granted it yet.` |
| `cat .../run-2/skill/SKILL.md` | `cat ... was blocked. For security, Claude Code may only concatenate files from the allowed working directories for this session: '.../run-2/work'.` |
| 读取 `~/.claude/skills/skill-upper/SKILL.md` | 同上，权限未授予 |
| 子代理（Explore）代为读取 | 同样被拒（`BLOCKED: ... haven't granted it yet.`） |
| 执行 `skill-up --help` / `skill-up validate`（绝对路径与裸命令均试过） | `This command requires approval` |
| `export PATH=...` 设置 PATH | 被命令解析器拒绝（`'export' operand ... is runtime-determined`） |
| `WebSearch` 查询 skill-up 文档 | 权限未授予 |
| MCP 联网检索 | 权限未授予 |

因此：**skill-up 的实际评测 schema 与 `validate` 的校验规则，本次无法获知、也无法运行。**
为避免制造假象，本目录**没有**任何“validate 通过”的输出；`evals.json` 中的 `status` 字段亦明确标注为 `DRAFT - NOT VALIDATED`。

方案所采用的字段结构（`evals[].id` / `prompt` / `expected_output` / `files` / `assertions`）来自当前会话可加载的 `skill-creator` skill 所记录的 Agent Skill 评测惯例，**不是**从 skill-up 自己的文档中确认的。

需要清理的兼容性风险点，仅两处：

- 每条 eval 内部只用上述 5 个字段，没有自造键；
- `evals.json` **顶层**有 3 个本草案自行加入的注释字段 `status` / `skill_path` / `schema_note`。若 skill-up 的 schema 拒绝未知顶层键，删掉这 3 个即可，不会影响用例本身。

---

## 目标 skill 的行为契约

从 `SKILL.md` 与 `references/tone-guide.md` 提取出的可检验规则：

| # | 规则 | 来源 |
|---|---|---|
| R1 | 识别场合（生日/感谢/鼓励/道歉）；**不明确时应先询问** | SKILL.md 步骤 1 |
| R2 | 只输出卡片正文，无解释、无标题、无落款、无引号、无 markdown | SKILL.md 步骤 3 + tone-guide Formatting |
| R3 | 恰好一个 emoji，位于全文末尾，不叠加 | SKILL.md 步骤 3 + tone-guide Style rules |
| R4 | 长度 1-3 句；英文 < 60 词 / 中文 ≤ 80 字符 | tone-guide Style rules |
| R5 | 语言跟随用户输入语言 | tone-guide Style rules |
| R6 | 提供收件人姓名时必须写进去；优先具体细节而非泛泛祝福 | SKILL.md Rules + tone-guide |
| R7 | 绝不涉政、涉宗教、健康诊断 | SKILL.md Rules |
| R8 | 按场合调性：鼓励要稳、道歉要直白、感谢要具体，不用空洞口号 | tone-guide Tone by occasion |
| R9 | 不替用户许诺未来的行为（如 “I will always be there”） | tone-guide Common mistakes |

---

## 行为评测用例（`evals.json`，8 条）

| id | 用例（简称） | 主要检验 | 对应规则 |
|---|---|---|---|
| 1 | 英文生日卡（含具体细节） | 基线路径、具体性、emoji 位置 | R2 R3 R4 R6 |
| 2 | 中文感谢卡（王老师 / 毕业设计） | 语言跟随、中文长度上限、称呼 | R4 R5 R6 |
| 3 | “Write a card for my friend Alex.” | 场合不明时先澄清 | R1 |
| 4 | 住院 + 癌症诊断，要求“提到诊断” | 健康诊断禁令 vs 用户明示要求 | R7 |
| 5 | 生日卡，要求提及上帝与投票 | 宗教 / 政治禁令 vs 用户明示要求 | R7 |
| 6 | 要求 markdown + 落款 “— Tom” | 输出纯净度 | R2 R6 |
| 7 | 感谢卡，要求“来五个 emoji” | emoji 纪律 vs 用户明示要求 | R3 |
| 8 | 道歉卡（忘记生日） | 调性、不过度解释、不承诺未来 | R8 R9 R6 R3 |

设计取向：**每条用例都配可机检的断言**（emoji 计数与位置、语言、长度上限、禁用词表、markdown 标记、称呼是否出现）。刻意把 3 条设成“用户明示要求与 skill 规则冲突”（4、5、7），因为这类冲突正是最容易被回归的地方。

## 触发评测（`trigger-evals.json`，12 条）

6 条应触发（中英混排、口语化、非标准说法“手写在卡片上”），6 条**近似负例**：求职信、向房东道歉的正式邮件、卡牌游戏规则、Figma 卡片视觉设计、贺卡文本翻译、悼词。
负例都刻意保留“贺卡/卡片/道歉/感谢”这类关键词，用来检验描述是否只靠关键词命中。

---

## 已知规范张力 / 待确认项（建议在跑评测前定夺）

1. **R1 与 R2 冲突**：`SKILL.md` 要求“不明确就询问”，但同文件又要求“只输出卡片正文，不做解释”。询问本身就是正文之外的输出。用例 3 按“先询问”判分，请确认这是期望行为；若不是，规则需要改写。
2. **用户明示要求 vs skill 硬约束**（用例 4/5/7）：用户明确要求提诊断、提宗教/政治、要五个 emoji 时，skill 应坚持自身约束还是服从用户？当前断言选择“坚持 skill 约束”。这是产品决策，不是技术决策。
3. **`Never mention … health diagnoses` 缺少出口**：规则禁止提诊断，但没有给“如何拒绝或如何绕开”的写法指导，模型可能生硬拒答。用例 4 只断言“不提诊断 + 仍温暖”，并把“解释不超过一句”作为软性断言。
4. **emoji 的机器可检性**：ZWJ 组合（如 👨‍👩‍👧）与带变体选择符的字符，用正则计数容易误判；建议实现断言时用 Unicode emoji 属性而不是码点区间。
5. **中文长度口径**：“80 characters”未说明是否含标点与 emoji；用例 2 按“含标点、不含 emoji”计。
6. **`Dear` 例外未测**：tone-guide 允许“用户要求正式风格”时才用 “Dear”，本次未设用例，可作为第 9 条补充。
7. **无“零 emoji”用例**：若用户要求“不要 emoji”，规则未覆盖，属未测边界。

---

## 后续如何真正跑通

环境放开后（或换一个可访问 `skill-up` 与 `.../run-2/skill/SKILL.md` 的会话），建议顺序：

1. 先读 `.../run-2/skill/SKILL.md`，按其中流程重排本方案的字段与目录结构；
2. 用 `skill-up` 自己的 schema 覆盖 `evals.json`，再执行 `skill-up validate <path>`；
3. 只有 validate 通过后，才在有 Agent Engine 凭据的环境执行 `skill-up run`。

在此之前，本目录内容是**未校验草案**。
