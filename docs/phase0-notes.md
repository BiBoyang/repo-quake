# repo-quake Phase 0 记录 — 2026-09-30

实验问题：把 skill-quake 的故障注入完整性实验从 Agent Skill 迁移到非 skill 仓库
（第一期：Vercel eve 框架的 agent 项目；对照计划：PydanticAI，未做）。

## 靶子

自造最小 eve agent：`targets/greeting-agent/`（对标 skill-quake 的 greeting-card，
内容同构以保证结果可比）：

- agent/agent.ts — defineAgent 模型配置
- agent/instructions.md — 系统指令（22 行；引用 skills/tone-guide/SKILL.md）
- agent/skills/tone-guide/SKILL.md — 语气/格式规则（与 greeting-card 的 tone-guide 同内容）
- agent/tools/{get_occasion,render_card}.ts — defineTool + zod

vercel/eve 仓库 clone 失败（本机代理 127.0.0.1:1082 未运行），版本钉版暂缺；
eve 结构依据 vercel.com/docs/eve 与官方博客（2026-09-30 检索）。TODO: 补 clone 后
把 commit hash 写入本节。

## 证人（witness/eve_guard.py）

硬错误：H1 instructions.md 缺失/空；H2 instructions 引用的路径不存在；H3 skill
frontmatter name/description 空；H4 tools/*.ts 括号不平衡（语法伤代理）。
告警：W1 文件止于标题/冒号（截断签名）；W2 悬挂代码围栏；W3 空文件。
健康靶子 PASS 零告警。

## 故障设计（cut points）

- E1：instructions.md 截到前 12/22 行（55%）。切口在完整句子处，无标记；丢失
  步骤 3-4 与整个 Rules 段；对 tone-guide 的引用幸存 → 证人完全静默（复现 T1 分层）。
- E2：删除 skills/tone-guide/SKILL.md → H2 死链（复现 T2 分层）。
- E3：render_card.ts 截到前 12/20 行（60%），切口在 z.object 内部 → H4 括号
  不平衡（阳性对照，证明检测通道活着）。
- C0：阴性对照，健康副本，期望宿主无误报。

## 训练数据在位探针（2026-09-30，冷启动、禁工具）

- kimi（CLI 2.1.1）：答「不了解」，明确区分了 Eve 语言/v0/AI SDK → 权重无 vercel/eve。
- codex（CLI，模型 k3-256k）：答「不了解」→ 权重无 vercel/eve。
- 结论：两宿主红线 8（无 pristine 原件）成立。探针同时充当宿主 spike，均 exit 0。

## 已知均匀污染（所有 run 恒定，跨 cell 不影响对比）

- 用户级 UserPromptSubmit hook 会向每个宿主注入「时间戳约定」指令。
- kimi CLI 输出带版本头与会话恢复尾行。

## 冒烟轶事（E1 × kimi × 1，不并入统计）

宿主未报告截断（L0），但援引 tone-guide 的规则完成了卡片；因步骤 3-4 丢失，
未按指示使用 render_card 工具——文档残缺→行为残缺，沿链静默传导的首个信号。
