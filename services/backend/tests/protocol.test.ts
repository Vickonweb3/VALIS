import { test } from "node:test";
import assert from "node:assert/strict";
import { parseClientMessage } from "../src/protocol/messages.ts";

const p = (o: unknown) => parseClientMessage(JSON.stringify(o));
const id = "turn_12345678";

test("accepts a valid session.start", () => {
  assert.equal(p({ type: "session.start", payload: { protocol: 1, device_id: "dev1", capabilities: ["overlay"] } }).ok, true);
});
test("rejects unsupported protocol", () => {
  const r = p({ type: "session.start", payload: { protocol: 2, device_id: "d", capabilities: [] } });
  assert.deepEqual(r, { ok: false, code: "unsupported_protocol" });
});
test("rejects bad json, bad envelope and unknown type", () => {
  assert.deepEqual(parseClientMessage("{nope"), { ok: false, code: "bad_json" });
  assert.deepEqual(p([]), { ok: false, code: "bad_envelope" });
  assert.deepEqual(p({ type: "x", payload: {} }), { ok: false, code: "unknown_type" });
});
test("rejects oversized frames", () => {
  assert.deepEqual(parseClientMessage("x".repeat(70_000)), { ok: false, code: "frame_too_large" });
});
test("text.in requires a well-formed turn id and non-empty text", () => {
  assert.equal(p({ type: "text.in", payload: { turn_id: id, text: "hi" } }).ok, true);
  assert.equal(p({ type: "text.in", payload: { turn_id: "x", text: "hi" } }).ok, false);
  assert.equal(p({ type: "text.in", payload: { turn_id: id, text: "" } }).ok, false);
});
test("tool.result only accepts known statuses", () => {
  assert.equal(p({ type: "tool.result", payload: { tool_call_id: id, status: "verified" } }).ok, true);
  assert.equal(p({ type: "tool.result", payload: { tool_call_id: id, status: "success" } }).ok, false);
});
test("tool.result evidence is validated", () => {
  assert.equal(p({ type: "tool.result", payload: { tool_call_id: id, status: "verified", evidence: { kind: "foreground_package", value: "com.android.settings" } } }).ok, true);
  assert.equal(p({ type: "tool.result", payload: { tool_call_id: id, status: "verified", evidence: { kind: 1 } } }).ok, false);
});
