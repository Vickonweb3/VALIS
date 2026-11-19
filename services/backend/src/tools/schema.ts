/** Minimal JSON Schema subset used for tool inputs: type, enum, min/max, pattern, required, items. */

export type Schema =
  | { type: "string"; enum?: readonly string[]; pattern?: string; minLength?: number; maxLength?: number }
  | { type: "integer" | "number"; minimum?: number; maximum?: number }
  | { type: "boolean" }
  | { type: "array"; items: Schema; maxItems?: number }
  | { type: "object"; properties: Record<string, Schema>; required?: readonly string[]; additionalProperties?: false };

export type ValidationError = { path: string; message: string };

export function validate(schema: Schema, value: unknown, path = "$"): ValidationError[] {
  const err = (message: string): ValidationError[] => [{ path, message }];
  switch (schema.type) {
    case "string": {
      if (typeof value !== "string") return err("expected string");
      if (schema.enum && !schema.enum.includes(value)) return err(`must be one of ${schema.enum.join(", ")}`);
      if (schema.minLength !== undefined && value.length < schema.minLength) return err("too short");
      if (schema.maxLength !== undefined && value.length > schema.maxLength) return err("too long");
      if (schema.pattern && !new RegExp(schema.pattern).test(value)) return err("does not match pattern");
      return [];
    }
    case "integer":
    case "number": {
      if (typeof value !== "number" || !Number.isFinite(value)) return err("expected number");
      if (schema.type === "integer" && !Number.isInteger(value)) return err("expected integer");
      if (schema.minimum !== undefined && value < schema.minimum) return err(`must be >= ${schema.minimum}`);
      if (schema.maximum !== undefined && value > schema.maximum) return err(`must be <= ${schema.maximum}`);
      return [];
    }
    case "boolean":
      return typeof value === "boolean" ? [] : err("expected boolean");
    case "array": {
      if (!Array.isArray(value)) return err("expected array");
      if (schema.maxItems !== undefined && value.length > schema.maxItems) return err("too many items");
      return value.flatMap((v, i) => validate(schema.items, v, `${path}[${i}]`));
    }
    case "object": {
      if (typeof value !== "object" || value === null || Array.isArray(value)) return err("expected object");
      const obj = value as Record<string, unknown>;
      const errors: ValidationError[] = [];
      for (const key of schema.required ?? []) {
        if (!(key in obj)) errors.push({ path: `${path}.${key}`, message: "required" });
      }
      for (const [key, v] of Object.entries(obj)) {
        const sub = schema.properties[key];
        if (!sub) {
          if (schema.additionalProperties === false) errors.push({ path: `${path}.${key}`, message: "unknown property" });
          continue;
        }
        errors.push(...validate(sub, v, `${path}.${key}`));
      }
      return errors;
    }
  }
}
