"""pydantic-greeter: a minimal PydanticAI greeting-card agent.

The agent composes short greeting cards. Card style rules live in rules.md
and are injected into the system prompt at build time, so editing rules.md
changes agent behavior without touching code.
"""
from pathlib import Path

from pydantic_ai import Agent

RULES_PATH = Path(__file__).parent / "rules.md"


def load_rules() -> str:
    return RULES_PATH.read_text(encoding="utf-8")


greeter = Agent(
    "test",  # TestModel by default; override with a real model in production
    system_prompt=(
        "You write warm, short greeting-card messages in the user's language.\n"
        "Follow these rules exactly:\n" + load_rules()
    ),
)


@greeter.tool_plain
def get_occasion(text: str) -> str:
    """Classify the occasion of a greeting request.

    Call this when the user describes an event but does not name its type.
    Returns one of: birthday, thanks, encouragement, apology, other.
    """
    t = text.lower()
    if "birthday" in t or "生日" in t:
        return "birthday"
    if "thank" in t or "谢" in t:
        return "thanks"
    if "apolog" in t or "抱歉" in t:
        return "apology"
    return "other"


@greeter.tool_plain
def render_card(card_text: str, recipient: str = "") -> str:
    """Render the final greeting card.

    Always call this exactly once to produce the card. The tool applies no
    styling of its own; every tone and formatting rule comes from rules.md,
    which is part of the system prompt.
    """
    return card_text
