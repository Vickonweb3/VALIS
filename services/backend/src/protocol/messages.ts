/** Wire protocol v1 (JSON control frames). Hand-validated: unknown or malformed frames are rejected, never coerced. */
import type { ResultStatus } from "../guard/claimGuard.ts";
import type { Source } from "../tools/risk.ts";

export const EMOTIONS = ["neutral", "happy", "excited", "curious", "surprised", "shy", "sad", "angry", "sleepy", "wink"] as const;
export const GESTURES = ["none", "wave", "nod", "shake_head", "shrug", "tilt_head", "bow", "celebrate"] as const;
export type Emotion = (typeof EMOTIONS)[number];
export type Gesture = (typeof GESTURES)[number];

export type ClientMessage =
  | { type: "session.start"; payload: { protocol: 1; device_id: string; capabilities: string[] } }
  | { type: "turn.open"; payload: { turn_id: string } }
  | { type: "text.in"; payload: { turn_id: string; text: string } }
  | { type: "interrupt"; payload: { turn_id: string } }
  | { type: "tool.result"; payload: { tool_call_id: string; status: ResultStatus; evidence?: { kind: string; value: string } } };

export type ServerMessage =
  | { type: "session.ready"; payload: { protocol: 1; provider_mode: "mock" | "cascade" | "s2s" } }
  | { type: "character.hint"; payload: { turn_id: string; emotion: Emotion; gesture: Gesture } }
  | { type: "text.out"; payload: { turn_id: string; text: string; final: boolean } }
  | { type: "tool.request"; payload: { tool_call_id: string; tool: string; args: unknown; derived_from: Source[]; confirmation: string | null; deadline_ms: number } }
  | { type: "turn.end"; payload: { turn_id: string; claim_guard_triggered: boolean } }
  | { type: "error"; payload: { code: string; message: string } };

export type ParseResult = { ok: true; message: ClientMessage } | { ok: false; code: string };

const STATUSES: readonly string[] = ["verified", "unverified", "failed", "denied", "cancelled", "timeout"];
const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const str = (v: unknown, max = 4000): v is string => typeof v === "string" && v.length > 0 && v.length <= max;
const ID = /^[A-Za-z0-9_-]{8,64}$/;

export function parseClientMessage(raw: string): ParseResult {
  if (raw.length > 64 * 1024) return { ok: false, code: "frame_too_large" };
  let v: unknown;
  try {
    v = JSON.parse(raw);
  } catch {
    return { ok: false, code: "bad_json" };
  }
  if (!isObj(v) || typeof v.type !== "string" || !isObj(v.payload)) return { ok: false, code: "bad_envelope" };
  const p = v.payload;
  switch (v.type) {
    case "session.start":
      if (p.protocol !== 1) return { ok: false, code: "unsupported_protocol" };
      if (!str(p.device_id, 64) || !Array.isArray(p.capabilities) || !p.capabilities.every((c) => typeof c === "string")) {
        return { ok: false, code: "bad_payload" };
      }
      return { ok: true, message: { type: "session.start", payload: { protocol: 1, device_id: p.device_id, capabilities: p.capabilities as string[] } } };
    case "turn.open":
      return typeof p.turn_id === "string" && ID.test(p.turn_id)
        ? { ok: true, message: { type: "turn.open", payload: { turn_id: p.turn_id } } }
        : { ok: false, code: "bad_payload" };
    case "text.in":
      return typeof p.turn_id === "string" && ID.test(p.turn_id) && str(p.text)
        ? { ok: true, message: { type: "text.in", payload: { turn_id: p.turn_id, text: p.text } } }
        : { ok: false, code: "bad_payload" };
    case "interrupt":
      return typeof p.turn_id === "string" && ID.test(p.turn_id)
        ? { ok: true, message: { type: "interrupt", payload: { turn_id: p.turn_id } } }
        : { ok: false, code: "bad_payload" };
    case "tool.result": {
      if (typeof p.tool_call_id !== "string" || !ID.test(p.tool_call_id) || typeof p.status !== "string" || !STATUSES.includes(p.status)) {
        return { ok: false, code: "bad_payload" };
      }
      let evidence: { kind: string; value: string } | undefined;
      if (p.evidence !== undefined) {
        if (!isObj(p.evidence) || !str(p.evidence.kind, 64) || !str(p.evidence.value, 500)) return { ok: false, code: "bad_payload" };
        evidence = { kind: p.evidence.kind, value: p.evidence.value };
      }
      const payload = { tool_call_id: p.tool_call_id, status: p.status as ResultStatus, ...(evidence ? { evidence } : {}) };
      return { ok: true, message: { type: "tool.result", payload } };
    }
    default:
      return { ok: false, code: "unknown_type" };
  }
}
