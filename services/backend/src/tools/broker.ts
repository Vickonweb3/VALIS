/** Server-side tool broker: steps 1–6 of the action pipeline as pure functions. */
import { decide, type OrgPolicy, type PolicyResult, type Risk, type SessionContext, type Source } from "./risk.ts";
import { validate, type Schema, type ValidationError } from "./schema.ts";

export interface ToolSpec {
  id: string;
  version: number;
  description: string;
  inputSchema: Schema;
  risk: Risk;
  executor: "INTENT" | "ACCESSIBILITY" | "SYSTEM" | "CLOUD";
  /** Text shown on the device card; placeholders {name} are filled from validated args only. */
  confirmationTemplate?: string;
  idempotent: boolean;
  timeoutMs: number;
}

export interface ToolCall {
  id: string;
  tool: string;
  args: unknown;
  derivedFrom: readonly Source[];
}

export type BrokerOutcome =
  | { kind: "unknown_tool"; tool: string }
  | { kind: "invalid_args"; errors: ValidationError[] }
  | { kind: "not_in_catalogue"; tool: string }
  | { kind: "duplicate"; toolCallId: string }
  | { kind: "decided"; spec: ToolSpec; policy: PolicyResult; confirmation: string | null };

export class ToolBroker {
  private readonly registry = new Map<string, ToolSpec>();
  private readonly seen = new Set<string>();

  constructor(specs: readonly ToolSpec[]) {
    for (const s of specs) {
      if (this.registry.has(s.id)) throw new Error(`duplicate tool id ${s.id}`);
      this.registry.set(s.id, s);
    }
  }

  /** Tools the model may see: registry ∩ allowed, minus anything above the org ceiling or PROHIBITED. */
  catalogue(allowed: ReadonlySet<string>, org: OrgPolicy): ToolSpec[] {
    const rank = { SAFE: 0, SENSITIVE: 1, CONSEQUENTIAL: 2, PROHIBITED: 3 } as const;
    return [...this.registry.values()].filter(
      (s) => allowed.has(s.id) && s.risk !== "PROHIBITED" && rank[s.risk] <= rank[org.riskCeiling],
    );
  }

  evaluate(call: ToolCall, allowed: ReadonlySet<string>, org: OrgPolicy, session: SessionContext): BrokerOutcome {
    if (this.seen.has(call.id)) return { kind: "duplicate", toolCallId: call.id };
    const spec = this.registry.get(call.tool);
    if (!spec) return { kind: "unknown_tool", tool: call.tool };
    const errors = validate(spec.inputSchema, call.args);
    if (errors.length) return { kind: "invalid_args", errors };
    // PROHIBITED tools are reported as DENY with a spoken reason, not hidden as "unknown".
    if (spec.risk !== "PROHIBITED" && !allowed.has(spec.id)) return { kind: "not_in_catalogue", tool: spec.id };
    this.seen.add(call.id);
    const policy = decide({ toolId: spec.id, risk: spec.risk, derivedFrom: call.derivedFrom, org, session });
    const confirmation =
      policy.decision === "CONFIRM" ? renderConfirmation(spec, call.args as Record<string, unknown>) : null;
    return { kind: "decided", spec, policy, confirmation };
  }
}

/** Builds card text from the template and validated args only; never from model prose. */
export function renderConfirmation(spec: ToolSpec, args: Record<string, unknown>): string {
  const tpl = spec.confirmationTemplate ?? `Allow ${spec.id}?`;
  return tpl.replace(/\{(\w+)\}/g, (_, k: string) => {
    const v = args[k];
    return typeof v === "string" || typeof v === "number" ? sanitizeForCard(String(v)) : "?";
  });
}

function sanitizeForCard(s: string): string {
  // Strip control and bidi-override characters that could disguise the action; cap length.
  // eslint-disable-next-line no-control-regex
  return s.replace(/[\u0000-\u001f\u007f‪-‮⁦-⁩]/g, "").slice(0, 80);
}
