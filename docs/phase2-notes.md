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

## skill-creator quick_validate.py 盲区的三变体确认（2026-10-02 中午，上游钉版）

三变体：Anthropic 上游（anthropics/skills@main，quick_validate.py 最后更新
2026-02-06 1ed29a03，102 行）、Codex 分发版（127 行 minimal）、Claude Code
分发版（223 行，社区增强 fork，含 validate_path_references）。

**确认一：空 frontmatter 静默放行（三变体全部）。**
精确边界：YAML `name:`（空值→None）会被类型检查意外挡下（"got NoneType"）；
而 `name: ""`（引号空串）三变体全部报 "Skill is valid!"。根因：上游 63/78 行
所有格式校验都在 `if name:` / `if description:` 真值守卫后面，空串跳过一切检查，
且无「非空」断言。phase2 的 F4 格（mutate.sh 写引号空串）正是打在这个盲区上。

**确认二：引用存活性零检查（上游 + Codex 版）。**
上游与 Codex 版均无 validate_path_references；最小复现：SKILL.md 引用
不存在的 references/guide.md → 上游报 "Skill is valid!"。Claude 版有社区补丁。
（skill-guard 对同一格 FAIL。）

**确认三：截断无检测。** F1 截断件三变体全 PASS（脚本只查 frontmatter 与
TODO/fence，不看正文完整性）。

PR 形态建议：给上游 anthropics/skills 提 quick_validate.py 补丁——非空断言 +
引用存活性检查（可直接引用 Claude 版 validate_path_references 的实现作先例），
理由栏附本仓库 runs/phase2 与最小复现命令。

## eval-guide 上游可提 issue（2026-10-02 中午确认，main = 7a22a89 为最新提交）

**A. 文档路径失效（doc bug）。** SKILL.md:127 与 dashboard/build-orient.py 头部
注释（6-12 行）引用的 `templates/orient.html`、`templates/base.html`、
`examples/stage-orient-data.json` 均不存在；真实位置在 `dashboard/templates/`、
`dashboard/examples/`（build-orient.py:31 的代码是对的，文档/注释停留在
目录迁移前）。最小验证：`ls` 对比 + build-orient.py 代码路径。

**B. 2/5 个 skill 的 frontmatter 不是合法 YAML。** eval-guide 与
eval-suite-planner 的 description 为未加引号的 plain scalar，内含
": "（如 "…development: write evals…"），PyYAML 直接拒绝解析
（"mapping values are not allowed here"，eval-guide 在 description 第 289 列）。
skill-guard（宽松解析）PASS 了它——我们自己的证人也有这个盲区，记一笔。
影响面：任何用严格 YAML 解析器的工具链（含 Claude 版 quick_validate）都
无法解析这两个 skill 的元数据。修法：description 加引号或改 block scalar。

两者皆适合一个 focused PR（或先 issue 问维护者偏好）。证据命令均已存档。
