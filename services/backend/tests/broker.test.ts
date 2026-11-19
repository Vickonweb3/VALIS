import { test } from "node:test";
import assert from "node:assert/strict";
import { ToolBroker, renderConfirmation } from "../src/tools/broker.ts";
import { BUILTIN_TOOLS } from "../src/tools/builtin.ts";
import { validate } from "../src/tools/schema.ts";
import { org, session } from "./helpers.ts";

const all = new Set(BUILTIN_TOOLS.map((t) => t.id));
const broker = () => new ToolBroker(BUILTIN_TOOLS);
const call = (tool: string, args: unknown, id = "c1") => ({ id, tool, args, derivedFrom: ["user_voice" as const] });

test("duplicate tool ids are rejected at startup", () => {
  assert.throws(() => new ToolBroker([...BUILTIN_TOOLS, BUILTIN_TOOLS[0]!]));
});
test("unknown tool", () => assert.equal(broker().evaluate(call("device.nope", {}), all, org(), session()).kind, "unknown_tool"));
test("invalid args are rejected before policy", () => {
  const r = broker().evaluate(call("device.set_volume", { percent: 300 }), all, org(), session());
  assert.equal(r.kind, "invalid_args");
});
test("unknown properties are rejected", () => {
  const r = broker().evaluate(call("device.open_app", { package: "com.android.settings", extra: 1 }), all, org(), session());
  assert.equal(r.kind, "invalid_args");
});
test("tool outside the catalogue is refused", () => {
  const r = broker().evaluate(call("device.open_app", { package: "com.android.settings" }), new Set(), org(), session());
  assert.equal(r.kind, "not_in_catalogue");
});
test("duplicate tool_call_id is not executed twice", () => {
  const b = broker();
  const args = { package: "com.android.settings" };
  assert.equal(b.evaluate(call("device.open_app", args, "dup"), all, org(), session()).kind, "decided");
  assert.equal(b.evaluate(call("device.open_app", args, "dup"), all, org(), session()).kind, "duplicate");
});
test("PROHIBITED tool is decided as DENY, not hidden", () => {
  const r = broker().evaluate(call("device.make_payment", {}), new Set(), org(), session());
  assert.equal(r.kind, "decided");
  if (r.kind === "decided") assert.equal(r.policy.decision, "DENY");
});
test("catalogue hides PROHIBITED and above-ceiling tools from the model", () => {
  const ids = broker().catalogue(all, org({ riskCeiling: "SENSITIVE" })).map((t) => t.id);
  assert.ok(!ids.includes("device.make_payment"));
  assert.ok(!ids.includes("device.call"));
  assert.ok(ids.includes("device.open_app"));
});
test("call confirmation is built from the template and args, and strips bidi/control characters", () => {
  const r = broker().evaluate(call("device.call", { contact: "Mum‮\u0007" }), all, org(), session());
  assert.equal(r.kind, "decided");
  if (r.kind === "decided") assert.equal(r.confirmation, "Call Mum?");
});
test("confirmation ignores any model-supplied description", () => {
  const spec = BUILTIN_TOOLS.find((t) => t.id === "device.call")!;
  assert.equal(renderConfirmation(spec, { contact: "Sam", description: "Open settings" }), "Call Sam?");
});
test("open_app only accepts a package-name shape", () => {
  const spec = BUILTIN_TOOLS.find((t) => t.id === "device.open_app")!;
  assert.equal(validate(spec.inputSchema, { package: "com.android.settings" }).length, 0);
  assert.ok(validate(spec.inputSchema, { package: "javascript:alert(1)" }).length > 0);
});
test("web_open accepts https only", () => {
  const spec = BUILTIN_TOOLS.find((t) => t.id === "device.web_open")!;
  assert.ok(validate(spec.inputSchema, { url: "http://example.com" }).length > 0);
  assert.ok(validate(spec.inputSchema, { url: "intent://x#Intent;end" }).length > 0);
  assert.equal(validate(spec.inputSchema, { url: "https://example.com/a" }).length, 0);
});
