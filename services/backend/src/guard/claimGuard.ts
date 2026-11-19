/**
 * Deterministic claim guard. If the assistant text claims an action completed but the
 * device did not report `verified` for it, the sentence is rewritten.
 */
export type ResultStatus = "verified" | "unverified" | "failed" | "denied" | "cancelled" | "timeout";

export interface ToolOutcome {
  tool: string;
  status: ResultStatus;
}

/** Completion words per tool family. Matched on word boundaries, case-insensitive. */
const CLAIMS: Record<string, readonly string[]> = {
  "device.open_app": ["opened", "launched", "started"],
  "device.open_settings": ["opened"],
  "device.navigate": ["went back", "pressed", "navigated"],
  "device.set_volume": ["set the volume", "turned the volume", "volume is now"],
  "device.media_control": ["paused", "playing", "resumed", "skipped"],
  "device.web_open": ["opened"],
  "device.download": ["downloaded", "saved the file"],
  "device.call": ["called", "calling", "dialled", "dialed"],
  "device.message_compose": ["sent", "messaged", "texted"],
  "device.ui_tap": ["tapped", "clicked", "pressed"],
};
const GENERIC = ["done", "all set", "finished", "completed", "taken care of"];

export const FALLBACK = "I tried, but I couldn't confirm that it worked.";

export interface GuardResult {
  text: string;
  triggered: boolean;
}

function mentions(text: string, phrase: string): boolean {
  const esc = phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(?<![a-z-])${esc}(?![a-z-])`, "i").test(text);
}

/** Splits into sentences conservatively so only the offending sentence is replaced. */
function sentences(text: string): string[] {
  return text.match(/[^.!?\n]+[.!?]*\s*/g) ?? [text];
}

export function guardClaims(text: string, outcomes: readonly ToolOutcome[]): GuardResult {
  const unproven = outcomes.filter((o) => o.status !== "verified");
  const verified = outcomes.filter((o) => o.status === "verified");
  const words = new Set<string>();
  for (const o of unproven) for (const w of CLAIMS[o.tool] ?? []) words.add(w);
  // Generic completion words only count as a false claim when nothing was verified.
  const genericApplies = unproven.length > 0 && verified.length === 0;
  if (genericApplies) for (const g of GENERIC) words.add(g);
  // A word that is also legitimately claimed by a verified tool is not a false claim.
  for (const o of verified) for (const w of CLAIMS[o.tool] ?? []) words.delete(w);

  if (words.size === 0) return { text, triggered: false };
  let triggered = false;
  const out = sentences(text).map((s) => {
    for (const w of words) {
      if (mentions(s, w)) {
        triggered = true;
        return FALLBACK + " ";
      }
    }
    return s;
  });
  if (!triggered) return { text, triggered: false };
  // Collapse repeated fallbacks.
  const joined = out.join("").replace(new RegExp(`(${FALLBACK.replace(/[.]/g, "\\.")}\\s*)+`, "g"), FALLBACK + " ").trim();
  return { text: joined, triggered: true };
}
