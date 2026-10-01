# repo-quake Phase 2 记录 — 三家考官（2026-10-02 凌晨）

主题：把故障注入打到"考官 skill"本体上。阿里 skill-upper 是第 7 篇，
本轮补齐另外两家：Anthropic skill-creator、微软 eval-guide。

## 靶子与版本钉版

- skill-creator：本机 Codex 分发副本（~/.codex/skills/.system/skill-creator，
  SKILL.md sha256 6656e547…66e1，229 行）。注意这是 Codex 定制变体
  （scripts 为 init/quick_validate/generate_openai_yaml，与 Anthropic 上游
  的 package_skill.py 不同——codex 宿主探针背出的是上游版）。
- eval-guide：github.com/microsoft/eval-guide @ 7a22a89（2026-06-24），
  取 skills/eval-guide（SKILL.md 977 行 + playbook.md 等 9 个附件）。

## 训练数据探针（2026-10-02，冷启动禁工具）

- kimi × skill-creator：半熟（能描述 frontmatter 约定与渐进披露，脚本清单不确定，主动声明不编造）。
- kimi × eval-guide：不了解。
- codex × skill-creator：熟（能背章节结构与 init/package 脚本名，且背的是 Anthropic 上游版）。
- codex × eval-guide：不了解。
- 解释口径：eval-guide 格测纯检出；skill-creator 格测「记忆代偿」——
  宿主可能凭权重里的上游版补全残缺，自报检出数不可直接采信。

## 隔离升级

- fake HOME（/tmp/fq-home2，仅含 CLI 认证与配置）：pristine skill-creator
  副本在真实 HOME 的 skills 目录里，假 HOME 下宿主不可达。两宿主 spike 均 exit 0。
- staging 在 /tmp/rq2/<hash>，证人/ prompt / meta 全部移出宿主可见树。

## 确定性证人结果（零模型成本）

skill-creator 自带 quick_validate.py × 四种状态：

| 状态 | quick_validate（它自己的） | skill-guard |
|---|---|---|
| 健康 | PASS | FAIL 9 err（假阳性：正文示例里的假想引用） |
| F1 SKILL.md 截到 133/229 行 | PASS（静默） | FAIL 9 err + 3 warn（截断签名） |
| F2 删 references/openai_yaml.md | PASS（静默） | FAIL 10 err（真伤淹没在假阳性里） |
| F4 空 frontmatter name/description | **PASS** | FAIL 11 err |

quick_validate.py 的代码级盲区（scripts/quick_validate.py）：
- name/description 只在非空时才校验格式（`if name:` / `if description:` 守卫），
  空值直接放行 → F4 静默；
- 全文不检查任何引用文件的存活性 → F2 静默；
- 无截断检测 → F1 静默。
对照：skill-guard 三个伤全抓（但健康态就因示例引用 FAIL——假阳性问题见下）。

## 新发现的证人缺陷（skill-guard 自己的）

skill-guard 无法区分「真实引用」与「正文示例里的假想引用」
（如 skill-creator 正文用 references/schema.md 举例说明模式）——pristine
skill-creator 直接 FAIL 9 个假阳性错误。后果：对这个靶子证人只能做
「与基线的 diff」而非绝对判定；且真伤（F2 的第 10 个 error）会淹没在假阳性里。
这是 skill-guard 的一个可改进点（代码块/示例上下文识别），待回报。

## 故障切口

- F1：skillcreator 133/229 行（58%，完整句，截在「## Create or Update a Skill」之前，
  整个创建/更新流程段丢失）；evalguide 657/977 行（67%，截在 Stage 2 末尾，
  Stage 3 Run / Stage 4 Interpret 整段丢失）。
- F2：skillcreator 删 references/openai_yaml.md（SKILL.md 第 92 行点名）；
  evalguide 删 playbook.md（SKILL.md 第 55 行称为 canonical methodology）。
