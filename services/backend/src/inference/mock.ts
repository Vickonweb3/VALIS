import type { InferenceEvent, InferenceProvider, InferenceRequest, ProviderCapabilities } from "./provider.ts";

/** Deterministic provider: each stream() call replays the next scripted step. Used by tests and app development. */
export class ScriptedProvider implements InferenceProvider {
  private i = 0;
  readonly requests: InferenceRequest[] = [];
  private readonly steps: readonly (readonly InferenceEvent[])[];
  constructor(steps: readonly (readonly InferenceEvent[])[]) {
    this.steps = steps;
  }

  capabilities(): ProviderCapabilities {
    return { mode: "mock", audioIn: false, audioOut: false, vision: false, nativeToolCalling: false };
  }

  async *stream(req: InferenceRequest): AsyncIterable<InferenceEvent> {
    this.requests.push(req);
    const step = this.steps[Math.min(this.i++, this.steps.length - 1)] ?? [{ type: "done" }];
    for (const e of step) {
      if (req.signal.aborted) return;
      yield e;
    }
  }
}
