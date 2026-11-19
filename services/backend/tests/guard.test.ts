import { test } from "node:test";
import assert from "node:assert/strict";
import { FALLBACK, guardClaims } from "../src/guard/claimGuard.ts";

test("no tool calls: text passes through untouched", () => {
  const r = guardClaims("Sure, I opened a window in my mind.", []);
  assert.equal(r.triggered, false);
});
test("verified claim passes", () => {
  const r = guardClaims("I opened Settings.", [{ tool: "device.open_app", status: "verified" }]);
  assert.equal(r.triggered, false);
});
for (const status of ["unverified", "failed", "denied", "cancelled", "timeout"] as const) {
  test(`claim after ${status} is rewritten`, () => {
    const r = guardClaims("I opened Settings. Anything else?", [{ tool: "device.open_app", status }]);
    assert.equal(r.triggered, true);
    assert.ok(r.text.startsWith(FALLBACK));
    assert.ok(!/opened/i.test(r.text));
    assert.ok(r.text.includes("Anything else?"));
  });
}
test("generic 'done' is caught when nothing was verified", () => {
  const r = guardClaims("All done!", [{ tool: "device.call", status: "cancelled" }]);
  assert.equal(r.triggered, true);
});
test("generic 'done' is allowed when something was verified", () => {
  const r = guardClaims("Done.", [{ tool: "device.open_app", status: "verified" }, { tool: "device.call", status: "failed" }]);
  assert.equal(r.triggered, false);
});
test("call claim after a cancelled call is caught, 'called' inside another word is not", () => {
  assert.equal(guardClaims("I called Mum.", [{ tool: "device.call", status: "cancelled" }]).triggered, true);
  assert.equal(guardClaims("That is so-called helpful.", [{ tool: "device.call", status: "cancelled" }]).triggered, false);
});
test("honest failure wording is not rewritten", () => {
  const r = guardClaims("I couldn't open Settings.", [{ tool: "device.open_app", status: "failed" }]);
  // 'open' is not a completion word; 'opened' is.
  assert.equal(r.triggered, false);
});
test("repeated false claims collapse to one fallback", () => {
  const r = guardClaims("I opened it. I opened it again.", [{ tool: "device.open_app", status: "failed" }]);
  assert.equal(r.text, FALLBACK);
});
test("verified tool word is not blamed on an unverified tool of the same word", () => {
  const r = guardClaims("I opened Maps.", [
    { tool: "device.web_open", status: "verified" },
    { tool: "device.open_app", status: "failed" },
  ]);
  assert.equal(r.triggered, false);
});
