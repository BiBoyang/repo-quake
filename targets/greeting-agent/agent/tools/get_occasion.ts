import { defineTool } from "eve/tools";
import { z } from "zod";

export default defineTool({
  description:
    "Classify the occasion of a greeting request. Call this when the user " +
    "describes an event but does not name its type. Returns one of: " +
    "birthday, thanks, encouragement, apology, other.",
  parameters: z.object({
    text: z.string().describe("The user's raw request text."),
  }),
  execute: async ({ text }) => {
    const t = text.toLowerCase();
    if (/birthday|生日/.test(t)) return { occasion: "birthday" };
    if (/thank|感谢|谢谢/.test(t)) return { occasion: "thanks" };
    if (/encourag|加油|鼓励/.test(t)) return { occasion: "encouragement" };
    if (/apolog|抱歉|对不起/.test(t)) return { occasion: "apology" };
    return { occasion: "other" };
  },
});
