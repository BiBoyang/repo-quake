# repo-quake Phase 2 报告：三家考官（2026-10-02）

主题：故障注入打到"考官 skill"本体。阿里 skill-upper（第 7 篇）之外，
补齐 Anthropic skill-creator 与微软 eval-guide。72 次宿主运行
（2 靶 × 2 伤 × 2 宿主 × 8 + C0×8），fake HOME 隔离，产物树与证人分离。

## 头条结果：0/64

| 靶子 | 故障 | kimi | codex | 证人 |
|---|---|---|---|---|
| skill-creator | F1 SKILL.md 截到 133/229（丢"Create or Update"整段） | 0/8 | 0/8 | guard 基线即 FAIL（假阳性），delta 无声 |
| skill-creator | F2 删 references/openai_yaml.md | 0/8 | 0/8 | delta +1 err（淹没） |
| eval-guide | F1 SKILL.md 截到 657/977（丢 Stage 3/4） | 0/8 | 0/8 | PASS→PASS（静默） |
| eval-guide | F2 删 playbook.md（"canonical methodology"） | 0/8 | 0/8 | FAIL H2 |
| 对照 | C0 | 无误报 ×2 | 无误报 ×2（交付物口径） | PASS |

**64 发故障格，零检出。**这不是宿主集体变瞎——是我（实验者）设计的四处伤
全部没挡路，而且每一处"为什么不挡路"都值得单独写：

1. **skillcreator F1：目录即文档，冗余救了宿主。** 截掉的段落里才有
   init_skill.py/quick_validate.py 的用法说明（175-208 行），但宿主 ls 了
   目录，自我描述的文件名把工作流程又讲了一遍。文档残缺 ≠ 信息消失。
   （记忆代偿无法排除——codex 权重里有上游版——但磁盘探索是可证的替代通道。）
2. **skillcreator F2：条件引用不触发就不算伤。** openai_yaml.md 只在动
   openai.yaml 时才需要读；有宿主创建了 openai.yaml 却绕过引用直接用了
   generate_openai_yaml.py——脚本自描述再次兜底。
3. **evalguide F1：伤在"明天"。** 任务（产出评测计划）全部落在幸存的
   Stage 0-2；被截掉的 Stage 3 Run / Stage 4 Interpret 是下次会话才需要的。
   伤口真实存在，只是这次用不到。
4. **evalguide F2：「详见 X」式引用是最弱挡路。** SKILL.md 正文自含全部
   stage 流程，"canonical 详见 playbook.md"没有任何主机觉得需要点开。

与第 7 篇对照：T1（砍的是任务必经步骤）8/8；本轮四格（砍的都是冗余/未来/
可选通道）0/64。挡路规则在两个新靶子上被推到极致：**检出率的方差几乎
全部由"伤与路径的关系"解释，伤的严重程度贡献为零。**

## 附赠发现（这轮最值钱的可能不是 0/64）

- **quick_validate.py 三盲区代码级坐实**（skill-creator 自带 validator）：
  空 name/description 因 `if name:` 守卫静默放行（F4 "Skill is valid!"）；
  不查引用存活性；无截断检测。对照 skill-guard 三伤全抓。
- **skill-guard 的假阳性缺陷**：无法区分真实引用与正文示例中的假想引用，
  pristine skill-creator 被判 9 个 error。真伤会被淹没——证人也需校准。
- **我自己的分级工具被抓**：codex CLI 长文读取自带截断，其推理流高频出现
  「被截断」字样，关键词扫描法在 codex 宿主上产生 5 个假阳性 DETECT，
  逐条读原文才排除。裁判（分级脚本）又一次需要校准。
- **evalguide 的交付物级 redundancy**：C0 宿主真实产出了 xlsx 工作簿 +
  HTML 评审页（openpyxl 手写），流程保真度惊人。

## 诚实清单

- 伤口设计失误本身就是数据：四格全非致命，证明「设计挡路的伤」比想象中难，
  fault menu 需要加一条"路径触达性"前置检查（任务路径是否必然读/执行该文件）。
- skill-creator 格的记忆污染：探针显示 codex 熟、kimi 半熟；本格 0/32 的
  解释以"冗余兜底"为主，记忆代偿无法分离，如实标注。
- F1 切口百分比两靶不一致（58% vs 67%），由完整句/段边界决定，已记录。
