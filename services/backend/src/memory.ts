/** Memory proposals: the model may only propose; items become active solely by user approval. */
export type MemoryStatus = "pending" | "active" | "rejected" | "deleted";
export interface MemoryItem {
  id: string;
  text: string;
  status: MemoryStatus;
  source: "model_proposal" | "user";
}

const SENSITIVE = [/\b(password|passcode|pin)\b/i, /\b\d{13,19}\b/, /\b(ssn|social security)\b/i, /\b(seed phrase|private key)\b/i];

export class MemoryStore {
  private items = new Map<string, MemoryItem>();
  private n = 0;
  readonly mode: "cloud" | "local" | "off";
  constructor(mode: "cloud" | "local" | "off") {
    this.mode = mode;
  }

  propose(text: string): MemoryItem | { error: "memory_off" | "sensitive" | "empty" } {
    if (this.mode === "off") return { error: "memory_off" };
    const t = text.trim();
    if (!t) return { error: "empty" };
    if (SENSITIVE.some((r) => r.test(t))) return { error: "sensitive" };
    const item: MemoryItem = { id: `m${++this.n}`, text: t.slice(0, 500), status: "pending", source: "model_proposal" };
    this.items.set(item.id, item);
    return item;
  }

  approve(id: string): boolean { return this.transition(id, "pending", "active"); }
  reject(id: string): boolean { return this.transition(id, "pending", "rejected"); }
  forget(id: string): boolean {
    const it = this.items.get(id);
    if (!it || it.status === "deleted") return false;
    this.items.delete(id);
    return true;
  }
  forgetAll(): number { const n = this.items.size; this.items.clear(); return n; }
  /** Only approved items are ever offered to the model as context. */
  context(): string[] { return [...this.items.values()].filter((i) => i.status === "active").map((i) => i.text); }
  pending(): MemoryItem[] { return [...this.items.values()].filter((i) => i.status === "pending"); }

  private transition(id: string, from: MemoryStatus, to: MemoryStatus): boolean {
    const it = this.items.get(id);
    if (!it || it.status !== from) return false;
    it.status = to;
    return true;
  }
}
