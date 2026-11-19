/** The single seam between VALIS and any model. Nothing outside adapters may be model-specific. */
import type { Emotion, Gesture } from "../protocol/messages.ts";
import type { ResultStatus } from "../guard/claimGuard.ts";
import type { Source } from "../tools/risk.ts";

export interface ToolDescriptor {
  id: string;
  description: string;
  inputSchema: unknown;
}

export type ChatMessage =
  | { role: "user"; text: string }
  | { role: "assistant"; text: string }
  /** Built only from the device's reported status; success text is never synthesised. */
  | { role: "tool"; toolCallId: string; tool: string; status: ResultStatus; evidence?: string };

export interface InferenceRequest {
  messages: readonly ChatMessage[];
  tools: readonly ToolDescriptor[];
  signal: AbortSignal;
}

export type InferenceEvent =
  | { type: "text_delta"; text: string }
  | { type: "hint"; emotion: Emotion; gesture: Gesture }
  | { type: "tool_call"; id: string; tool: string; args: unknown; derivedFrom: Source[] }
  | { type: "done" };

export interface ProviderCapabilities {
  mode: "mock" | "cascade" | "s2s";
  audioIn: boolean;
  audioOut: boolean;
  vision: boolean;
  nativeToolCalling: boolean;
}

export interface InferenceProvider {
  capabilities(): ProviderCapabilities;
  stream(req: InferenceRequest): AsyncIterable<InferenceEvent>;
}
