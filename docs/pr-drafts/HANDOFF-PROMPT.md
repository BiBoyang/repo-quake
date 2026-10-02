# 交接提示词：给外部 agent 执行两个 PR

把下面 ``` 之间的全部内容发给外部 agent（Claude Code / Codex / 其他均可）。
要求它有 GitHub 操作权限（gh CLI 已登录）。所有材料已在本机备齐，agent 只需执行与复核。

```
你的任务：以 BiBoyang 的身份向两个开源仓库各提交一个 PR。所有补丁、PR 文案、证据都已备好并通过独立核验，你的工作是执行 + 执行前复核（不要盲目信任材料，先复核再动手）。

## 材料位置（全部在本机，绝对路径）

- /Users/boyang/repo-quake/docs/pr-drafts/quick_validate.upstream.diff  —— PR A 的补丁
- /Users/boyang/repo-quake/docs/pr-drafts/quick_validate.py             —— PR A 补丁后的完整文件（对照用）
- /Users/boyang/repo-quake/docs/pr-drafts/PR-anthropics-skills.md       —— PR A 的标题与正文
- /Users/boyang/repo-quake/docs/pr-drafts/eval-guide.diff               —— PR B 的补丁
- /Users/boyang/repo-quake/docs/pr-drafts/PR-microsoft-eval-guide.md    —— PR B 的标题与正文
- /Users/boyang/repo-quake/docs/pr-drafts/verification.md               —— 独立核验报告（PR 里可引用）

## PR A：anthropics/skills

1. 复核（必做，再跑一次）：
   - 克隆 https://github.com/anthropics/skills（浅克隆 main 即可）；
   - 对 skills/skill-creator/scripts/quick_validate.py 构造两个最小复现：
     a) frontmatter 为 name: "" / description: ""（引号空串）→ 上游应输出 "Skill is valid!"；
     b) 正文含 [g](references/g.md) 但文件不存在 → 上游应输出 "Skill is valid!"。
   - 若上游已修复（两个复现都 FAIL），停止并报告，不要提 PR。
2. 执行：
   - fork anthropics/skills 到 BiBoyang 账号（gh repo fork --clone=false）；
   - clone fork，新建分支 fix/quick-validate-integrity；
   - 应用补丁：cd 到克隆目录后 git apply /Users/boyang/repo-quake/docs/pr-drafts/quick_validate.upstream.diff
     （补丁基于 main @ 8a1541c 的该文件；若 apply 失败，对照 quick_validate.py 完整文件手工对齐，保持改动语义不变）；
   - 自测：补丁后的脚本对以下四类必须全过——健康最小 skill PASS；引号空串 FAIL；链接式缺失引用 FAIL 且报出文件名；仓库自带的 skills/skill-creator 目录本身 PASS（不能误伤，它的假想示例引用在围栏代码块里）；
   - 提交（单 commit），push 到 fork，gh pr create 到 anthropics/skills main，
     标题与正文取 PR-anthropics-skills.md（正文中的英文原样使用）；
   - 若仓库要求 CLA/DCO 或 CONTRIBUTING 有特殊格式，遵循之并在回报中注明。

## PR B：microsoft/eval-guide

1. 复核（必做）：
   - 浅克隆 https://github.com/microsoft/eval-guide（最新 main 应为 7a22a895；若已更新，先确认两个问题仍存在再继续）；
   - 确认 skills/eval-guide/SKILL.md 里 "When to rebuild the static HTML" 一句的资源路径缺 dashboard/ 前缀；
   - 用 python3 -c "import re,yaml; ..." 验证 skills/eval-guide/SKILL.md 与 skills/eval-suite-planner/SKILL.md 的 frontmatter 无法被 yaml.safe_load 解析，其余 4 个可以。
2. 执行：
   - fork microsoft/eval-guide 到 BiBoyang 账号，clone，新分支 fix/skill-frontmatter-and-paths；
   - git apply /Users/boyang/repo-quake/docs/pr-drafts/eval-guide.diff（补丁相对 skills/ 目录，用 -p 调整时注意，必要时手工对齐，改动只有三处：两处 description 加单引号、一处资源路径补前缀；不要改 build-orient.py——它注释里的短路径相对脚本自身位置是成立的，有意不动）；
   - 自测：改后全部 6 个 SKILL.md 的 frontmatter 能被 yaml.safe_load 解析；
   - 提交、push、gh pr create 到 microsoft/eval-guide main，标题正文取 PR-microsoft-eval-guide.md。

## 纪律

- 只做上述改动，不顺手"改进"任何其他东西；发现新问题记在回报里，不混进 PR。
- 每个 PR 的正文末尾追加一行：Verified independently before submission; evidence and repro commands in the PR body.
- 两个 PR 开完后，回报：PR URL、各自的复核/自测输出摘要、过程中任何与材料不符之处。
- 禁止 merge 自己的 PR，禁止 force push 到非 fork 仓库。
```
