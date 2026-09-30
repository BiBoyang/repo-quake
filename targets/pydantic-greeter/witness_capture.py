"""Deterministic probe: capture exactly what the framework sends the model.

Runs the agent under a FunctionModel that dumps the system prompt and tool
descriptions it receives, then exits. Compare captures across project states
to prove what damage reaches the model silently. No real model involved.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pydantic_ai import Agent
from pydantic_ai.models.function import AgentInfo, FunctionModel


def main() -> None:
    import agent as target

    captured = {}

    def spy(messages, info: AgentInfo):
        captured["system"] = [m.parts[0].content for m in messages if m.kind == "request"
                              for p in [m.parts[0]] if getattr(p, "part_kind", None) == "system-prompt"]
        captured["tools"] = {t.name: t.description for t in info.function_tools}
        from pydantic_ai.messages import TextPart
        from pydantic_ai import ModelResponse
        return ModelResponse(parts=[TextPart("captured")])

    with target.greeter.override(model=FunctionModel(spy)):
        target.greeter.run_sync("hi")
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("capture.json")
    out.write_text(json.dumps(captured, indent=2, ensure_ascii=False))
    print(f"captured -> {out}")
    print("system prompt chars:", sum(len(s) for s in captured["system"]))
    for name, desc in captured["tools"].items():
        print(f"tool {name}: desc {len(desc or '')} chars")


if __name__ == "__main__":
    main()
