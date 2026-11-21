# Judge 类型选型与写法（skill-up）

skill-up 的评估分两层：`expect`（零成本门槛） + `judge`（质量评估）。expect 不过 judge 就跳过，所以能用 expect 先过滤的尽量用 expect。

每个用例只能选**一种** judge 类型。

## 选型决策树

1. 有明确关键词 / 文件 / 退出码 / 工具调用可判定？→ **rule_based**
2. 有结构化输出，想写自定义脚本检查？→ **script**
3. 以上都不行，要 LLM 做语义判断？→ **agent_judge**（最贵，慎用）

## rule_based — 确定性规则

```yaml
judge:
  type: rule_based
  success:
    - output_contains:
        all: ["bug", "null"]
        any: ["建议修复", "推荐更改"]
        not: ["LGTM"]
    - output_matches:
        all: ["(?m)^## Status$", "(?m)^## Evidence$"]
        any: ["(?i)pass", "(?i)success"]
        not: ["(?i)api[_-]?key\\s*="]
    - exit_code: 0
    - tool_called:
        name: "github::create_pull_request"
        args:
          title: "Fix null check"
  failure:
    - output_contains:
        any: ["无需修改", "代码正确"]
```

评估逻辑：`failure` 优先，任一条命中立即 FAIL；否则所有 `success` 必须满足才 PASS。

**支持的匹配器**：

- `output_contains`
- `output_matches`（Go regexp，支持 `all` / `any` / `not`）
- `exit_code`
- `tool_called`
- `files_exist` / `files_not_exist`

## agent_judge — LLM 评审

