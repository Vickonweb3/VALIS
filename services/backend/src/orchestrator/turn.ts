/** One conversational turn: provider events -> broker -> device -> verified results -> claim guard. */
import { guardClaims, type ResultStatus, type ToolOutcome } from "../guard/claimGuard.ts";
import type { ChatMessage, InferenceProvider } from "../inference/provider.ts";
import type { ServerMessage } from "../protocol/messages.ts";
import { ToolBroker } from "../tools/broker.ts";
import type { OrgPolicy, SessionContext, Source } from "../tools/risk.ts";

export const MAX_ROUNDS = 6;
export const MAX_TOOL_CALLS = 8;
export const TOOL_DEADLINE_MS = 15_000;

export interface DeviceResult {
  status: ResultStatus;
  evidence?: { kind: string; value: string };
}

export interface TurnDeps {
  provider: InferenceProvider;
  broker: ToolBroker;
  org: OrgPolicy;
  session: SessionContext;
  allowedTools: ReadonlySet<string>;
  /** Sources the server knows tainted this turn (e.g. a screenshot was attached). Cannot be removed by the model. */
  taintedSources: ReadonlySet<Source>;
  history: readonly ChatMessage[];
  send: (m: ServerMessage) => void;
  /** Resolves with the device's tool.result; rejects/aborts on timeout. */
  requestDevice: (toolCallId: string, signal: AbortSignal) => Promise<DeviceResult>;
  signal: AbortSignal;
}

export interface TurnResult {
  text: string;
  outcomes: ToolOutcome[];
  claimGuardTriggered: boolean;
  newMessages: ChatMessage[];
}

export async function runTurn(turnId: string, userText: string, d: TurnDeps): Promise<TurnResult> {
  const messages: ChatMessage[] = [...d.history, { role: "user", text: userText }];
  const outcomes: ToolOutcome[] = [];
  let toolCalls = 0;
  let text = "";

  for (let round = 0; round < MAX_ROUNDS; round++) {
    const catalogue = d.broker
      .catalogue(d.allowedTools, d.org)
      .map((s) => ({ id: s.id, description: s.description, inputSchema: s.inputSchema }));
    let roundText = "";
    const calls: { id: string; tool: string; args: unknown; derivedFrom: Source[] }[] = [];

    for await (const ev of d.provider.stream({ messages: [...messages], tools: catalogue, signal: d.signal })) {
      if (d.signal.aborted) break;
      if (ev.type === "text_delta") roundText += ev.text;
      else if (ev.type === "hint") d.send({ type: "character.hint", payload: { turn_id: turnId, emotion: ev.emotion, gesture: ev.gesture } });
      else if (ev.type === "tool_call") calls.push(ev);
    }
    text += roundText;
    if (roundText) messages.push({ role: "assistant", text: roundText });
    if (d.signal.aborted || calls.length === 0) break;

    for (const call of calls) {
      toolCalls++;
      const result = toolCalls > MAX_TOOL_CALLS ? deny("too_many_tool_calls") : await handleCall(call, d);
      outcomes.push({ tool: call.tool, status: result.status });
      messages.push({
        role: "tool", toolCallId: call.id, tool: call.tool, status: result.status,
        ...(result.evidence ? { evidence: `${result.evidence.kind}=${result.evidence.value}` } : {}),
      });
    }
  }

  const guarded = guardClaims(text.trim(), outcomes);
  if (guarded.text) d.send({ type: "text.out", payload: { turn_id: turnId, text: guarded.text, final: true } });
  d.send({ type: "turn.end", payload: { turn_id: turnId, claim_guard_triggered: guarded.triggered } });
  const newMessages = messages.slice(d.history.length);
  if (guarded.triggered) {
    // Keep history truthful: replace the model's false claim with the rewritten text.
    for (let i = newMessages.length - 1; i >= 0; i--) {
      const m = newMessages[i];
      if (m && m.role === "assistant") { newMessages[i] = { role: "assistant", text: guarded.text }; break; }
    }
  }
  return { text: guarded.text, outcomes, claimGuardTriggered: guarded.triggered, newMessages };
}

const deny = (_reason: string): DeviceResult => ({ status: "denied" });

async function handleCall(
  call: { id: string; tool: string; args: unknown; derivedFrom: Source[] },
  d: TurnDeps,
): Promise<DeviceResult> {
  // Union the model's claim with server-known taint: the model cannot launder provenance.
  const derivedFrom = [...new Set<Source>([...call.derivedFrom, ...d.taintedSources])];
  const out = d.broker.evaluate({ id: call.id, tool: call.tool, args: call.args, derivedFrom }, d.allowedTools, d.org, d.session);
  if (out.kind !== "decided") return { status: "failed" };
  if (out.policy.decision === "DENY") return { status: "denied" };
  d.send({
    type: "tool.request",
    payload: { tool_call_id: call.id, tool: call.tool, args: call.args, derived_from: derivedFrom, confirmation: out.confirmation, deadline_ms: TOOL_DEADLINE_MS },
  });
  const timeout = AbortSignal.any([d.signal, AbortSignal.timeout(TOOL_DEADLINE_MS)]);
  try {
    return await d.requestDevice(call.id, timeout);
  } catch {
    return { status: "timeout" };
  }
}
