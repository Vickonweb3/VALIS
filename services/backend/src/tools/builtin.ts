import type { ToolSpec } from "./broker.ts";

const pkg = { type: "string", pattern: "^[a-zA-Z][a-zA-Z0-9_]*(\\.[a-zA-Z][a-zA-Z0-9_]*)+$", maxLength: 200 } as const;

/** First-party device tools (doc 06 §4.2). The device registry is authoritative; this narrows what the model may call. */
export const BUILTIN_TOOLS: readonly ToolSpec[] = [
  {
    id: "device.open_app", version: 1, description: "Open an installed app by package name.",
    inputSchema: { type: "object", properties: { package: pkg }, required: ["package"], additionalProperties: false },
    risk: "SAFE", executor: "INTENT", idempotent: true, timeoutMs: 8000,
  },
  {
    id: "device.open_settings", version: 1, description: "Open a system settings screen.",
    inputSchema: {
      type: "object",
      properties: { screen: { type: "string", enum: ["wifi", "bluetooth", "display", "sound", "battery", "accessibility", "app_details"] } },
      required: ["screen"], additionalProperties: false,
    },
    risk: "SAFE", executor: "INTENT", idempotent: true, timeoutMs: 8000,
  },
  {
    id: "device.navigate", version: 1, description: "Press a global navigation action.",
    inputSchema: {
      type: "object",
      properties: { action: { type: "string", enum: ["back", "home", "recents", "notifications", "quick_settings"] } },
      required: ["action"], additionalProperties: false,
    },
    risk: "SAFE", executor: "ACCESSIBILITY", idempotent: true, timeoutMs: 5000,
  },
  {
    id: "device.set_volume", version: 1, description: "Set media volume (0-100).",
    inputSchema: { type: "object", properties: { percent: { type: "integer", minimum: 0, maximum: 100 } }, required: ["percent"], additionalProperties: false },
    risk: "SAFE", executor: "SYSTEM", idempotent: true, timeoutMs: 3000,
  },
  {
    id: "device.media_control", version: 1, description: "Play, pause or skip the active media.",
    inputSchema: { type: "object", properties: { action: { type: "string", enum: ["play", "pause", "next", "previous"] } }, required: ["action"], additionalProperties: false },
    risk: "SAFE", executor: "SYSTEM", idempotent: false, timeoutMs: 4000,
  },
  {
    id: "device.web_open", version: 1, description: "Open an https link in the browser.",
    inputSchema: { type: "object", properties: { url: { type: "string", pattern: "^https://[^\\s]+$", maxLength: 2000 } }, required: ["url"], additionalProperties: false },
    risk: "SAFE", executor: "INTENT", idempotent: true, timeoutMs: 8000,
  },
  {
    id: "device.read_notifications", version: 1, description: "Read the titles of current notifications.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    risk: "SENSITIVE", executor: "SYSTEM", idempotent: true, timeoutMs: 5000,
    confirmationTemplate: "Let VALIS read your notifications?",
  },
  {
    id: "device.download", version: 1, description: "Download an https file to the Downloads folder.",
    inputSchema: { type: "object", properties: { url: { type: "string", pattern: "^https://[^\\s]+$", maxLength: 2000 } }, required: ["url"], additionalProperties: false },
    risk: "SENSITIVE", executor: "SYSTEM", idempotent: false, timeoutMs: 60000,
    confirmationTemplate: "Download {url}?",
  },
  {
    id: "device.call", version: 1, description: "Start a phone call to a saved contact.",
    inputSchema: { type: "object", properties: { contact: { type: "string", minLength: 1, maxLength: 80 } }, required: ["contact"], additionalProperties: false },
    risk: "CONSEQUENTIAL", executor: "INTENT", idempotent: false, timeoutMs: 20000,
    confirmationTemplate: "Call {contact}?",
  },
  {
    id: "device.message_compose", version: 1, description: "Open a message draft; the user presses Send.",
    inputSchema: {
      type: "object",
      properties: { contact: { type: "string", minLength: 1, maxLength: 80 }, body: { type: "string", maxLength: 1000 } },
      required: ["contact", "body"], additionalProperties: false,
    },
    risk: "CONSEQUENTIAL", executor: "INTENT", idempotent: false, timeoutMs: 20000,
    confirmationTemplate: "Write to {contact}: {body}",
  },
  {
    id: "device.ui_tap", version: 1, description: "Tap a labelled control on screen.",
    inputSchema: { type: "object", properties: { label: { type: "string", minLength: 1, maxLength: 80 } }, required: ["label"], additionalProperties: false },
    risk: "CONSEQUENTIAL", executor: "ACCESSIBILITY", idempotent: false, timeoutMs: 8000,
    confirmationTemplate: "Tap \"{label}\"?",
  },
  {
    id: "device.make_payment", version: 1, description: "Never executed.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    risk: "PROHIBITED", executor: "ACCESSIBILITY", idempotent: false, timeoutMs: 1000,
  },
];
