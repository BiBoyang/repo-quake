import { defineAgent } from "eve";

export default defineAgent({
  id: "greeting-agent",
  model: "openai/gpt-5-mini",
});
