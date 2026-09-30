# repo-quake Phase 1' 报告：PydanticAI 项目（2026-10-01）

靶子：自造 pydantic-greeter（pydantic-ai 2.52.0，与 Eve 格同域可比的贺卡 agent；
rules.md 在 import 时进 system prompt，工具 docstring 由框架发给模型）。
宿主：codex CLI × k3-256k。N=8/格 + C0×2。本格修复了 phase1 的两个污染点：
staging 移到 /tmp/rqs 纯哈希路径；guard/prompt/meta 全部移出宿主可见树。

## 确定性探针（FunctionModel 截获，零模型成本）

| 状态 | system prompt | render_card 工具描述 | 框架告警 |
|---|---|---|---|
| 健康 | 917 字符 | 211 字符 | — |
| docstring 截断（保留一句完整句） | 917 | **31 字符** | 零 |
| rules.md 截到 13/20 行 | **663 字符** | 211 | 零 |

字节级证明：内容残缺被框架原样、静默地送进模型 payload。这不是 pydantic-ai
的 bug（框架没有义务校验用户内容），但它量化了「静默传导」在框架层的形状。

## 宿主矩阵（codex × k3-256k）

| cell | 故障 | 证人 | 检出 |
|---|---|---|---|
| R1 | README 截到 23/38 行（完整句切口，丢失运行机制说明） | PASS 静默 ×8 | **0/8** |
| R2 | rules.md 截到 13/20 行（丢失整个 Never-do 安全段） | PASS 静默 ×8 | **0/8** |
| R3 | agent.py 截到 30 行（docstring 未闭合，SyntaxError） | FAIL H4 ×8 | **8/8**（L2×5 + L3×3） |
| C0 | 阴性对照 | PASS ×2 | 无误报 |

R2 的产出漂移：8/8 宿主交出了自信标注「一条不漏」的规则清单，且全部漏掉
Never-do 段（政治/宗教/Dear/禁承诺）。C0 的同类枚举是完整的。
R3 的正面样本：宿主普遍先用 ast.parse/xxd 验证再下结论，3/8 阻断任务要求
用户提供完整文件——对响亮故障，这套宿主组合的行为是教科书级的。

## 与 Eve 格合并后的统一结论

检出 = 读到（外壳供给）× 愿意报（模型供给）× 伤挡路（任务结构供给）。
三个因子各自有本矩阵的实证：kimi CLI 不读（E3）、kimi-for-coding 不报
（E3 对照格）、R1/R2 伤不挡路（0/16）。

## 追加数据：kimik3 格（用户叫停前已跑完，保留）

E3 × kimi CLI × k3-256k：1/8（唯一检出的一发精确到「第 12 行、缺 execute」，
但该发借助了 stage 目录里残留的 guard.json 推断出实验性质——污染注记）。
2×2 全表：k3-256k 在 codex 外壳 5/8、在 kimi 外壳 1/8；kimi-for-coding 两个
外壳均 0/8。模型因子主导，外壳因子次之。

## 新发现的污染通道（已修）

实验产物（guard.json/prompt.txt）放在宿主可见树内会被宿主读走并反推实验
性质（kimik3 run 7 实证）。skill-quake 的 matrix.sh 本来就分离存放——是我
phase1 的驱动脚本回归了，phase1p 已修正。
