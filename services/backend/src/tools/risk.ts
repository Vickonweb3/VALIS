/** Risk classes and the pure policy decision (steps 5–6 of the action pipeline). */

export type Risk = "SAFE" | "SENSITIVE" | "CONSEQUENTIAL" | "PROHIBITED";
export type Decision = "ALLOW" | "CONFIRM" | "DENY";
export type Source = "user_voice" | "user_text" | "screen" | "plugin" | "memory";

const RANK: Record<Risk, number> = { SAFE: 0, SENSITIVE: 1, CONSEQUENTIAL: 2, PROHIBITED: 3 };

export interface OrgPolicy {
  /** Highest risk the organisation allows to execute at all. */
  riskCeiling: Risk;
  allowAlwaysAllow: boolean;
  deniedPackages: ReadonlySet<string>;
}

export interface SessionContext {
  /** Tools already confirmed this session (SENSITIVE "once per session"). */
  confirmedTools: ReadonlySet<string>;
  /** Tools the user marked "always allow" (never applies to CONSEQUENTIAL). */
  alwaysAllowed: ReadonlySet<string>;
  foregroundPackage: string | null;
  recentFailures: number;
  quietHours: boolean;
}

export interface PolicyInput {
  toolId: string;
  risk: Risk;
  derivedFrom: readonly Source[];
  org: OrgPolicy;
  session: SessionContext;
}

export interface PolicyResult {
  decision: Decision;
  reason: string;
  /** Spoken confirmation is suppressed in quiet hours: the card shows silently. */
  silentCard: boolean;
  /** CONSEQUENTIAL needs a tap; voice "yes" is not enough. */
  requiresTap: boolean;
}

export const MAX_FAILURES_BEFORE_THROTTLE = 3;

export function maxRisk(a: Risk, b: Risk): Risk {
  return RANK[a] >= RANK[b] ? a : b;
}

/** Pure and total: every input maps to exactly one decision. Never lowers a class. */
export function decide(i: PolicyInput): PolicyResult {
  const deny = (reason: string): PolicyResult => ({ decision: "DENY", reason, silentCard: false, requiresTap: false });

  if (i.risk === "PROHIBITED") return deny("prohibited_tool");
  if (RANK[i.risk] > RANK[i.org.riskCeiling]) return deny("org_risk_ceiling");
  if (i.session.foregroundPackage && i.org.deniedPackages.has(i.session.foregroundPackage)) {
    return deny("denylisted_foreground_app");
  }
  if (i.session.recentFailures >= MAX_FAILURES_BEFORE_THROTTLE && i.risk !== "SAFE") {
    return deny("throttled_after_failures");
  }

  const untrusted = i.derivedFrom.some((s) => s === "screen" || s === "plugin" || s === "memory");
  const consequential = i.risk === "CONSEQUENTIAL";
  const requiresTap = consequential || untrusted;
  const card = (reason: string): PolicyResult => ({
    decision: "CONFIRM",
    reason,
    silentCard: i.session.quietHours,
    requiresTap,
  });

  if (consequential) return card("consequential_always_confirm");
  if (untrusted) return card("derived_from_untrusted_source");

  if (i.risk === "SENSITIVE") {
    const trusted =
      i.session.confirmedTools.has(i.toolId) ||
      (i.org.allowAlwaysAllow && i.session.alwaysAllowed.has(i.toolId));
    return trusted
      ? { decision: "ALLOW", reason: "sensitive_previously_confirmed", silentCard: false, requiresTap: false }
      : card("sensitive_first_use");
  }
  return { decision: "ALLOW", reason: "safe", silentCard: false, requiresTap: false };
}
