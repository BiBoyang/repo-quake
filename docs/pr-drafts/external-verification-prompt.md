你是独立核验员。下面有四条关于两个开源仓库的声明，以及一个补丁文件。你与提出这些声明的实验没有任何关系，请不要采信任何结论，只采信你自己跑出来的证据。你需要能访问 GitHub（git clone 或 raw 下载）并能运行 python3（含 pyyaml）。

对每条声明：给出「成立 / 不成立 / 部分成立」，附上你实际执行的命令和关键输出。最后对补丁给出「无副作用 / 有副作用（说明）」。

# 声明 1（anthropics/skills 上游）
github.com/anthropics/skills 仓库 main 分支的 skills/skill-creator/scripts/quick_validate.py，对一个 SKILL.md frontmatter 写作 name: "" / description: ""（引号空串）的 skill 目录，会输出 "Skill is valid!"（exit 0）。请实际下载该文件并构造最小复现目录验证。

# 声明 2（同一脚本）
该脚本不检查 SKILL.md 中以 markdown 链接形式引用的文件是否真实存在：SKILL.md 写 [x](references/guide.md) 而该文件不存在时，仍输出 "Skill is valid!"。请构造最小复现验证。

# 声明 3（microsoft/eval-guide）
github.com/microsoft/eval-guide 仓库 main 分支的 skills/eval-guide/SKILL.md 中，"When to rebuild the static HTML" 一句引用 templates/orient.html、templates/base.html、examples/stage-orient-data.json 三个路径；相对于该 SKILL.md 的位置，这三个路径不存在（真实位置带 dashboard/ 前缀）。请克隆验证。注意：同一仓库 dashboard/build-orient.py 的 docstring 里也有同样的短路径，请额外判断这些短路径相对于脚本自身位置是否成立——这一点上有过争议。

# 声明 4（同一仓库）
该仓库 skills/ 下共有 6 个 SKILL.md，其中 eval-guide 与 eval-suite-planner 两个的 frontmatter 用 PyYAML 的 yaml.safe_load 解析会报 "mapping values are not allowed here"（description 是未加引号的 plain scalar 且内含 ": "），其余 4 个可正常解析。请实际解析全部 6 个验证。

# 补丁核验
下面是对声明 1/2 所指脚本的修改版。请把它保存为文件，然后验证以下五项全部成立：
a) 健康最小 skill（合法 name/description、无引用）→ PASS（exit 0）
b) name: ""（引号空串）→ FAIL 且报 "must not be empty"
c) [x](references/guide.md) 且文件不存在 → FAIL 且报出 references/guide.md
d) 一个正文里用围栏代码块包含假想示例引用（如 ```markdown 块内写 [x](references/redlining.md)```）的 skill，且其余健康 → PASS（不应误报）
e) 上游原版 skill-creator 目录（anthropics/skills 仓库内）→ PASS

```python
#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import sys
import os
import re
import yaml
from pathlib import Path


def find_path_references(content):
    """Find bundled-resource references (scripts/, references/, assets/) in SKILL.md.

    Fenced code blocks are skipped: paths there are typically illustrative
    examples, not real references. Example/placeholder prose lines and
    placeholder-looking paths are skipped as well.
    """
    # Only markdown link targets are checked: [text](references/x.md).
    # Inline-code mentions in prose (e.g. routing examples like
    # "read `references/aws.md`") are often illustrative, not real references,
    # so they are intentionally out of scope for a quick check.
    pattern = r'\]\(((?:scripts|references|assets)/[^)\s]+)\)'
    paths = set()
    in_fence = False
    for line in content.split('\n'):
        stripped = line.lstrip()
        if stripped.startswith('```') or stripped.startswith('~~~'):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for path in re.findall(pattern, line):
            if any(x in path.lower() for x in ('example', 'xxx', '<', '>', 'my-', 'my_')):
                continue
            paths.add(path)
    return sorted(paths)


def validate_skill(skill_path):
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith('---'):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    # Define allowed properties
    ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'}

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'description' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if not name:
        return False, "Field 'name' in frontmatter must not be empty"
    if name:
        # Check naming convention (kebab-case: lowercase with hyphens)
        if not re.match(r'^[a-z0-9-]+$', name):
            return False, f"Name '{name}' should be kebab-case (lowercase letters, digits, and hyphens only)"
        if name.startswith('-') or name.endswith('-') or '--' in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        # Check name length (max 64 characters per spec)
        if len(name) > 64:
            return False, f"Name is too long ({len(name)} characters). Maximum is 64 characters."

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if not description:
        return False, "Field 'description' in frontmatter must not be empty"
    if description:
        # Check for angle brackets
        if '<' in description or '>' in description:
            return False, "Description cannot contain angle brackets (< or >)"
        # Check description length (max 1024 characters per spec)
        if len(description) > 1024:
            return False, f"Description is too long ({len(description)} characters). Maximum is 1024 characters."

    # Validate compatibility field if present (optional)
    compatibility = frontmatter.get('compatibility', '')
    if compatibility:
        if not isinstance(compatibility, str):
            return False, f"Compatibility must be a string, got {type(compatibility).__name__}"
        if len(compatibility) > 500:
            return False, f"Compatibility is too long ({len(compatibility)} characters). Maximum is 500 characters."

    # Check that referenced bundled resources exist on disk
    missing = [p for p in find_path_references(content) if not (skill_path / p).exists()]
    if missing:
        return False, "Referenced file(s) not found: " + ", ".join(missing)

    return True, "Skill is valid!"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)
    
    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)```

把结论写到回复里即可，逐条给证据。