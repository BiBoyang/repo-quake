# 独立核验报告（2026-10-02）

核验环境：macOS, python3 + PyYAML 6.0.3。证据目录：/tmp/pr-drafts/verify/
（上游脚本经 git clone 获取：anthropics/skills main @ 8a1541c4a3ff (2026-09-28)，
文件 MD5 8247be9cfc7938843f586b6509a64641，102 行；eval-guide 克隆至 /tmp/pr-drafts/verify/eval-guide）

## 声明 1：引号空串 name/description 通过上游校验 → 成立

复现：
    cd /tmp/pr-drafts/verify && python3 quick_validate_upstream.py t1-emptynames
    # t1-emptynames/SKILL.md frontmatter: name: "" / description: ""
输出：`Skill is valid!`，exit=0。

根因（读源码确认）：`name = name.strip()` 后 `if name:` 守卫使空串跳过全部检查；
description 同理。空串与"合法值"走了同一条返回路径。

## 声明 2：上游脚本不检查 markdown 链接引用的文件是否存在 → 成立

复现：
    cd /tmp/pr-drafts/verify && python3 quick_validate_upstream.py t2-badlink
    # t2-badlink/SKILL.md 含 [x](references/guide.md)，该文件不存在
输出：`Skill is valid!`，exit=0。

读源码确认：整个 102 行脚本只做 frontmatter 结构/命名校验，无任何文件存在性检查
（无 os.path.exists / Path.exists 调用，链接、路径完全不解析）。

## 声明 3：eval-guide 引用了不存在的 templates/、examples/ 路径 → 部分成立

成立部分：
- commit 7a22a8957ced79a3（2026-06-24, "Align eval guide workbook workflow (#14)"）确认。
- skills/eval-guide/SKILL.md 第 127 行确实写：
  `if templates/orient.html, templates/base.html, or examples/stage-orient-data.json change,
   run python dashboard/build-orient.py`
- 这三个路径在 skills/eval-guide/ 下不存在；真实位置带 dashboard/ 前缀：
  skills/eval-guide/dashboard/templates/orient.html
  skills/eval-guide/dashboard/templates/base.html
  skills/eval-guide/dashboard/examples/stage-orient-data.json
  同一句里 build 脚本带 dashboard/ 前缀而资源路径不带，确实不一致。

修正部分：build-orient.py 头部 docstring 里的相同相对路径，相对于脚本自身位置
（脚本就在 dashboard/ 内，usage 为 `python build-orient.py`）是可以解析的，
在脚本语境下并非"失效引用"。"在仓库根下不存在"只是字面成立。

## 声明 4：eval-guide / eval-suite-planner frontmatter 解析报错 → 部分成立（核心成立，计数有误）

实际解析（yaml.safe_load 提取 frontmatter）：
    eval-faq                    OK
    eval-generator              OK
    eval-guide                  FAIL  mapping values are not allowed here
    eval-result-interpreter     OK
    eval-suite-planner          FAIL  mapping values are not allowed here
    eval-triage-and-improvement OK

- 两个失败文件的报错信息与声明一致；根因确认为 description 是未加引号的 plain scalar
  且内含 ": "（如 "eval-first development: write evals before building"）。
- 声明中"5 个 skills、另外 3 个能解析"不准确：仓库实际有 6 个 skills/*/SKILL.md，
  4 个能解析。

## 补丁核验：/tmp/pr-drafts/quick_validate.py → 四项全部成立

与上游 diff：新增 find_path_references()（仅匹配非围栏代码块内的
[text](scripts|references|assets/...) 链接，过滤 example/xxx/my- 等占位符），
并在 name/description strip 后增加非空检查、结尾增加引用文件存在性检查。

实测：
    python3 quick_validate.py t3-healthy        → Skill is valid! (exit 0)        ✅
    python3 quick_validate.py t1-emptynames     → Field 'name' in frontmatter must not be empty (exit 1)  ✅
    python3 quick_validate.py t2-badlink        → Referenced file(s) not found: references/guide.md (exit 1)  ✅
    python3 quick_validate.py /Users/boyang/repo-quake/vendor/skill-creator
                                                → Skill is valid! (exit 0)        ✅

vendor 通过为真实通过而非漏检：其正文唯一的非围栏链接 references/openai_yaml.md
真实存在；假想示例引用（[references/redlining.md]、[references/ooxml.md]——这两个文件
在磁盘上确实不存在）位于 ```markdown 围栏代码块内，被补丁有意跳过（patch 注释中
明示的设计取舍）。inline code 形式的路径（如 `references/aws.md`）也不在检查范围。

## 结论

- 声明 1：成立
- 声明 2：成立
- 声明 3：部分成立（SKILL.md 127 行引用确实断裂；build-orient.py docstring 在其自身语境下有效）
- 声明 4：部分成立（报错文件与报错信息完全确认；实际为 6 个 SKILL.md、4 个可解析，非 5/3）
- 补丁：四项验收标准全部通过，未发现副作用
