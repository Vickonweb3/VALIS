import type { OrgPolicy, SessionContext } from "../src/tools/risk.ts";

export const org = (o: Partial<OrgPolicy> = {}): OrgPolicy => ({
  riskCeiling: "CONSEQUENTIAL", allowAlwaysAllow: true, deniedPackages: new Set(), ...o,
});
export const session = (s: Partial<SessionContext> = {}): SessionContext => ({
  confirmedTools: new Set(), alwaysAllowed: new Set(), foregroundPackage: null, recentFailures: 0, quietHours: false, ...s,
});
