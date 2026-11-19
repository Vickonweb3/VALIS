import { test } from "node:test";
import assert from "node:assert/strict";
import { ScriptedProvider } from "../src/inference/mock.ts";
import type { InferenceEvent } from "../src/inference/provider.ts";
import type { ServerMessage } from "../src/protocol/messages.ts";
import { runTurn, type DeviceResult } from "../src/orchestrator/turn.ts";
import { ToolBroker } from "../src/tools/broker.ts";
import { BUILTIN_TOOLS } from "../src/tools/builtin.ts";
import type { Source } from "../src/tools/risk.ts";
import { org, session } from "./helpers.ts";

const all = new Set(BUILTIN_TOOLS.map((t) => t.id));

function setup(steps: InferenceEvent[][], device: (id: string) => DeviceResult | Promise<DeviceResult>, tainted: Source[] = []) {
  const sent: ServerMessage[] = [];
  const provider = new ScriptedProvider(steps);
  const ac = new AbortController();
  const run = (text = "hi") =>
    runTurn("turn_12345678", text, {
      provider, broker: new ToolBroker(BUILTIN_TOOLS), org: org(), session: session(), allowedTools: all,
      taintedSources: new Set(tainted), history: [], send: (m) => sent.push(m),
      requestDevice: async (id) => device(id), signal: ac.signal,
    });
  return { sent, provider, run, ac };
}
const call = (tool: string, args: unknown, derivedFrom: Source[] = ["user_voice"]): InferenceEvent => ({ type: "tool_call", id: "call_" + tool.replace(/\W/g, "_") + "_1", tool, args, derivedFrom });

test("plain reply is sent final and ends the turn", async () => {
  const t = setup([[{ type: "hint", emotion: "happy", gesture: "wave" }, { type: "text_delta", text: "Hello!" }, { type: "done" }]], () => ({ status: "verified" }));
  const r = await t.run();
  assert.equal(r.text, "Hello!");
  assert.deepEqual(t.sent.map((m) => m.type), ["character.hint", "text.out", "turn.end"]);
});

test("a verified tool call round-trips and the model sees the device status", async () => {
  const t = setup(
    [[call("device.open_app", { package: "com.android.settings" }), { type: "done" }], [{ type: "text_delta", text: "I opened Settings." }, { type: "done" }]],
    () => ({ status: "verified", evidence: { kind: "foreground_package", value: "com.android.settings" } }),
  );
  const r = await t.run("open settings");
  assert.equal(r.claimGuardTriggered, false);
  const second = t.provider.requests[1]!.messages.at(-1)!;
  assert.deepEqual(second, { role: "tool", toolCallId: "call_device_open_app_1", tool: "device.open_app", status: "verified", evidence: "foreground_package=com.android.settings" });
});

test("an unverified result forces the claim guard to rewrite a false 'I opened'", async () => {
  const t = setup(
    [[call("device.open_app", { package: "com.android.settings" }), { type: "done" }], [{ type: "text_delta", text: "I opened Settings." }, { type: "done" }]],
    () => ({ status: "unverified" }),
  );
  const r = await t.run();
  assert.equal(r.claimGuardTriggered, true);
  assert.match(r.text, /couldn't confirm/);
  const end = t.sent.at(-1)!;
  assert.equal(end.type === "turn.end" && end.payload.claim_guard_triggered, true);
  // History stays truthful too.
  assert.ok(r.newMessages.some((m) => m.role === "assistant" && /couldn't confirm/.test(m.text)));
});

test("PROHIBITED tool never reaches the device", async () => {
  let asked = 0;
  const t = setup([[call("device.make_payment", {}), { type: "done" }], [{ type: "text_delta", text: "I can't do that." }, { type: "done" }]], () => { asked++; return { status: "verified" }; });
  const r = await t.run();
  assert.equal(asked, 0);
  assert.deepEqual(r.outcomes, [{ tool: "device.make_payment", status: "denied" }]);
  assert.ok(!t.sent.some((m) => m.type === "tool.request"));
});

test("CONSEQUENTIAL call carries a device-rendered confirmation, never model text", async () => {
  const t = setup([[call("device.call", { contact: "Mum" }), { type: "done" }], [{ type: "done" }]], () => ({ status: "cancelled" }));
  await t.run();
  const req = t.sent.find((m) => m.type === "tool.request");
  assert.ok(req && req.type === "tool.request");
  assert.equal(req.payload.confirmation, "Call Mum?");
});

test("server-known taint cannot be removed by the model's own derived_from", async () => {
  const t = setup([[call("device.open_app", { package: "com.android.settings" }, ["user_voice"]), { type: "done" }], [{ type: "done" }]], () => ({ status: "verified" }), ["screen"]);
  await t.run();
  const req = t.sent.find((m) => m.type === "tool.request");
  assert.ok(req && req.type === "tool.request");
  assert.ok(req.payload.derived_from.includes("screen"));
  assert.notEqual(req.payload.confirmation, null);
});

test("device timeout becomes a timeout result", async () => {
  const t = setup([[call("device.open_app", { package: "com.android.settings" }), { type: "done" }], [{ type: "done" }]], () => { throw new Error("no answer"); });
  const r = await t.run();
  assert.deepEqual(r.outcomes, [{ tool: "device.open_app", status: "timeout" }]);
});

test("a model that loops on tool calls is bounded", async () => {
  const loop: InferenceEvent[] = [call("device.navigate", { action: "back" }), { type: "done" }];
  // Distinct ids per round are needed for the broker's dedupe; vary them.
  let n = 0;
  const steps = Array.from({ length: 12 }, () => [{ ...(loop[0] as Extract<InferenceEvent, { type: "tool_call" }>), id: `call_loop_${n++}_xx` }, loop[1]!] as InferenceEvent[]);
  const t = setup(steps, () => ({ status: "verified" }));
  await t.run();
  assert.ok(t.provider.requests.length <= 6);
});

test("abort stops the turn without hanging", async () => {
  const t = setup([[{ type: "text_delta", text: "partial" }, { type: "done" }]], () => ({ status: "verified" }));
  t.ac.abort();
  const r = await t.run();
  assert.equal(r.outcomes.length, 0);
});
