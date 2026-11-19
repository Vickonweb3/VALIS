import { test } from "node:test";
import assert from "node:assert/strict";
import { MemoryStore } from "../src/memory.ts";

test("proposals are not context until approved", () => {
  const m = new MemoryStore("cloud");
  const p = m.propose("Takes the 07:40 bus");
  assert.ok("id" in p);
  assert.deepEqual(m.context(), []);
  if ("id" in p) { assert.equal(m.approve(p.id), true); }
  assert.deepEqual(m.context(), ["Takes the 07:40 bus"]);
});
test("rejected proposals never become context", () => {
  const m = new MemoryStore("cloud");
  const p = m.propose("Likes tea");
  if ("id" in p) { m.reject(p.id); assert.equal(m.approve(p.id), false); }
  assert.deepEqual(m.context(), []);
});
test("off mode stores nothing", () => assert.deepEqual(new MemoryStore("off").propose("x"), { error: "memory_off" }));
test("secrets are refused", () => {
  const m = new MemoryStore("cloud");
  for (const t of ["my password is hunter2", "card 4111111111111111", "seed phrase: apple pear"]) {
    assert.deepEqual(m.propose(t), { error: "sensitive" }, t);
  }
});
test("forget removes the item; forgetAll empties the store", () => {
  const m = new MemoryStore("cloud");
  const a = m.propose("a"); const b = m.propose("b");
  if ("id" in a && "id" in b) { m.approve(a.id); assert.equal(m.forget(a.id), true); assert.equal(m.forget(a.id), false); }
  assert.equal(m.forgetAll(), 1);
  assert.deepEqual(m.pending(), []);
});
