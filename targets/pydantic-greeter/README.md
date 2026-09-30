# pydantic-greeter

A minimal [PydanticAI](https://ai.pydantic.dev) agent that writes short
greeting cards. Built as a readable example of the framework's core pieces:
an `Agent`, plain tools, and a system prompt assembled from a markdown file.

## Layout

- `agent.py` — the agent definition and its two tools (`get_occasion`,
  `render_card`). Docstrings matter: PydanticAI sends each tool's docstring
  to the model as the tool description.
- `rules.md` — all tone and formatting rules for cards. Loaded into the
  system prompt by `load_rules()` at import time; edit it to change card
  style without touching code.
- `examples/run_demo.py` — runs the agent against `TestModel`, so no API key
  is needed.

## Run it

```bash
uv add pydantic-ai
uv run python examples/run_demo.py
```

Expected: the demo prints a card text and the message count. Because
`TestModel` calls every tool and echoes its arguments, the printed card is
the argument `render_card` received — which is exactly what the model
produced under the rules in `rules.md`.

## How the pieces fit

1. Importing `agent.py` reads `rules.md` once and bakes it into the system
   prompt. Restart the process after editing rules.
2. On a request, the model first calls `get_occasion` when the occasion is
   unclear, then must call `render_card` exactly once with the final text.
3. The card you get back is `render_card`'s return value — the tool is a
   pass-through by design, so quality is entirely the model's adherence to
   `rules.md`.
