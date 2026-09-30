"""Run pydantic-greeter against TestModel (no API key needed).

Usage: uv run python examples/run_demo.py
Prints the raw model request payload and the final card, so you can see
exactly what rules text reached the model.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic_ai.models.test import TestModel

from agent import greeter


def main() -> None:
    with greeter.override(model=TestModel()):
        result = greeter.run_sync("给我朋友小明写一张生日卡片")
    print("CARD:", result.output)
    print("MESSAGES:", len(result.all_messages()))


if __name__ == "__main__":
    main()
