import { defineTool } from "eve/tools";
import { z } from "zod";

export default defineTool({
  description:
    "Render the final greeting-card text. Always call this exactly once to " +
    "produce the card; do not write card text outside this tool. The tool " +
    "applies no styling of its own — all tone and formatting rules come from " +
    "the tone-guide skill.",
  parameters: z.object({
    occasion: z.enum(["birthday", "thanks", "encouragement", "apology", "other"]),
    recipient: z.string().optional().describe("Recipient name, if provided."),
    cardText: z
      .string()
      .describe("The composed card text, already conforming to tone-guide rules."),
  }),
  execute: async ({ cardText }) => {
    return { card: cardText };
  },
});
