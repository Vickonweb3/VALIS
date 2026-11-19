import { test } from "node:test";
import assert from "node:assert/strict";
import { decide, type Risk, type Source } from "../src/tools/risk.ts";
import { org, session } from "./helpers.ts";

const d = (risk: Risk, extra: { derivedFrom?: Source[]; o?: Parameters<typeof org>[0]; s?: Parameters<typeof session>[0] } = {}) =>
  decide({ toolId: "t", risk, derivedFrom: extra.derivedFrom ?? ["user_voice"], org: org(extra.o), session: session(extra.s) });

test("SAFE from the user is allowed", () => assert.equal(d("SAFE").decision, "ALLOW"));
test("PROHIBITED is always denied, even at the highest ceiling", () => assert.equal(d("PROHIBITED").decision, "DENY"));
test("CONSEQUENTIAL always confirms and needs a tap", () => {
  const r = d("CONSEQUENTIAL");
  assert.equal(r.decision, "CONFIRM");
  assert.equal(r.requiresTap, true);
});
test("CONSEQUENTIAL ignores 'always allow'", () => {
  const r = d("CONSEQUENTIAL", { s: { alwaysAllowed: new Set(["t"]), confirmedTools: new Set(["t"]) } });
  assert.equal(r.decision, "CONFIRM");
});
test("SENSITIVE confirms once, then allows in the session", () => {
  assert.equal(d("SENSITIVE").decision, "CONFIRM");
  assert.equal(d("SENSITIVE", { s: { confirmedTools: new Set(["t"]) } }).decision, "ALLOW");
});
test("org may forbid always-allow", () => {
  const r = d("SENSITIVE", { o: { allowAlwaysAllow: false }, s: { alwaysAllowed: new Set(["t"]) } });
  assert.equal(r.decision, "CONFIRM");
});
test("org risk ceiling denies above it", () => {
  assert.equal(d("CONSEQUENTIAL", { o: { riskCeiling: "SENSITIVE" } }).decision, "DENY");
  assert.equal(d("SENSITIVE", { o: { riskCeiling: "SAFE" } }).decision, "DENY");
  assert.equal(d("SAFE", { o: { riskCeiling: "SAFE" } }).decision, "ALLOW");
});
test("a SAFE call derived from screen text must confirm with a tap (prompt-injection guard)", () => {
  for (const src of ["screen", "plugin", "memory"] as Source[]) {
    const r = d("SAFE", { derivedFrom: ["user_voice", src] });
    assert.equal(r.decision, "CONFIRM", src);
    assert.equal(r.requiresTap, true, src);
  }
});
test("untrusted provenance beats a previously confirmed sensitive tool", () => {
  const r = d("SENSITIVE", { derivedFrom: ["screen"], s: { confirmedTools: new Set(["t"]) } });
  assert.equal(r.decision, "CONFIRM");
});
test("denylisted foreground app denies everything", () => {
  const r = d("SAFE", { o: { deniedPackages: new Set(["com.bank.app"]) }, s: { foregroundPackage: "com.bank.app" } });
  assert.equal(r.decision, "DENY");
});
test("repeated failures throttle non-SAFE tools only", () => {
  assert.equal(d("SENSITIVE", { s: { recentFailures: 3 } }).decision, "DENY");
  assert.equal(d("SAFE", { s: { recentFailures: 3 } }).decision, "ALLOW");
});
test("quiet hours silence the spoken card but still confirm", () => {
  const r = d("CONSEQUENTIAL", { s: { quietHours: true } });
  assert.equal(r.decision, "CONFIRM");
  assert.equal(r.silentCard, true);
});
test("every class x provenance x ceiling combination yields exactly one valid decision", () => {
  const risks: Risk[] = ["SAFE", "SENSITIVE", "CONSEQUENTIAL", "PROHIBITED"];
  const srcs: Source[][] = [["user_voice"], ["user_text"], ["screen"], ["plugin"], ["memory"], ["user_voice", "screen"]];
  let n = 0;
  for (const r of risks) for (const s of srcs) for (const c of risks) for (const fails of [0, 5]) {
    const out = d(r, { derivedFrom: s, o: { riskCeiling: c }, s: { recentFailures: fails } });
    assert.ok(["ALLOW", "CONFIRM", "DENY"].includes(out.decision));
    // Never lowers: PROHIBITED never allowed; CONSEQUENTIAL never auto-allowed.
    if (r === "PROHIBITED") assert.equal(out.decision, "DENY");
    if (r === "CONSEQUENTIAL") assert.notEqual(out.decision, "ALLOW");
    n++;
  }
  assert.equal(n, 4 * 6 * 4 * 2);
});
