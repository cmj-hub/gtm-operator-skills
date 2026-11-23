// @jmc-go-to-market/result-envelope: one result format for every tool. Zero dependencies, one file, so agent
// kits can copy it verbatim. Types live in index.d.ts. Contract: result_envelope/v1.

export const CONTRACT = "result_envelope/v1";
export const STATUSES = Object.freeze(["ok", "partial", "abstain", "error"]);
export const CONFIDENCE_BASES = Object.freeze(["jev", "rule", "measured", "model_self_report", "unmeasured"]);
export const ENVELOPE_FIELDS = Object.freeze([
  "summary", "status", "confidence", "abstain", "unknowns", "assumptions", "evidence", "limits", "next_action", "receipt",
]);

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const ISO_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/;
const SPINE_ID_RE = /^sp_[0-9a-f]{16}$/;

const isObj = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
const isStr = (v) => typeof v === "string" && v.trim() !== "";
const realDate = (s) => {
  if (typeof s !== "string" || !DATE_RE.test(s)) return false;
  const d = new Date(`${s}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === s;
};

/** True only for plain JSON values (no BigInt, symbol, function, NaN/Infinity, undefined, cycles). Never throws. */
function isJson(v, seen = new Set(), depth = 0) {
  if (v === null || typeof v === "string" || typeof v === "boolean") return true;
  if (typeof v === "number") return Number.isFinite(v);
  if (typeof v !== "object" || depth > 64 || seen.has(v)) return false;
  seen.add(v);
  try {
    const ok = Array.isArray(v) ? v.every((x) => isJson(x, seen, depth + 1)) : Object.values(v).every((x) => isJson(x, seen, depth + 1));
    return ok;
  } catch {
    return false;
  } finally {
    seen.delete(v);
  }
}

/** Short, safe description of any value for an error message. Never throws. */
function describe(v) {
  try {
    if (isJson(v)) return JSON.stringify(v);
    return typeof v === "bigint" ? `${v}n` : typeof v === "object" && v !== null ? "a non-JSON object" : String(typeof v === "symbol" ? v.description ?? "symbol" : v);
  } catch {
    return "a non-JSON value";
  }
}

/** Validate an object as a result envelope. Extra fields are allowed (the envelope is added beside existing output). Never throws. */
export function validateEnvelope(env) {
  try {
    return validateEnvelopeUnsafe(env);
  } catch (e) {
    return { ok: false, errors: [{ path: "", message: "envelope could not be inspected: " + describe(e?.message) }] };
  }
}

function validateEnvelopeUnsafe(env) {
  const errors = [];
  const err = (path, message) => errors.push({ path, message });
  if (!isObj(env)) return { ok: false, errors: [{ path: "", message: "envelope must be an object" }] };

  if (!isStr(env.summary)) err("summary", "summary must be a non-empty string");
  const statusOk = STATUSES.includes(env.status);
  if (!statusOk) err("status", `status must be one of ${STATUSES.join(", ")}`);

  const c = env.confidence;
  if (!isObj(c)) err("confidence", "confidence must be {value, basis}");
  else {
    const basisOk = CONFIDENCE_BASES.includes(c.basis);
    if (!basisOk) err("confidence.basis", `basis must be one of ${CONFIDENCE_BASES.join(", ")}`);
    if (c.value === null) {
      if (basisOk && c.basis !== "unmeasured") err("confidence.value", "value null requires basis unmeasured; never invent a confidence");
    } else if (typeof c.value !== "number" || !Number.isFinite(c.value) || c.value < 0 || c.value > 1) {
      err("confidence.value", "value must be a number in [0,1] or null");
    } else if (c.basis === "unmeasured") {
      err("confidence.value", "basis unmeasured requires value null");
    }
  }

  const a = env.abstain;
  if (a === null) {
    if (env.status === "abstain") err("abstain", "status abstain requires an abstain object");
  } else if (!isObj(a)) {
    err("abstain", "abstain must be an object or null");
  } else {
    if (statusOk && env.status !== "abstain") err("abstain", "abstain object is only valid when status is abstain");
    if (!isStr(a.reason)) err("abstain.reason", "reason must be a non-empty string");
    if (a.closest !== undefined && typeof a.closest !== "string") err("abstain.closest", "closest must be a string");
    if (a.to_collect !== undefined && !(Array.isArray(a.to_collect) && a.to_collect.every((x) => typeof x === "string"))) {
      err("abstain.to_collect", "to_collect must be an array of strings");
    }
  }

  if (!Array.isArray(env.unknowns)) err("unknowns", "unknowns must be an array");
  else {
    env.unknowns.forEach((u, i) => {
      if (!isObj(u) || !isStr(u.field) || !isStr(u.why)) err(`unknowns[${i}]`, "unknown must be {field, why} with non-empty strings");
    });
    if (env.status === "ok" && env.unknowns.length > 0) err("status", "status ok is invalid while unknowns is non-empty; use partial");
  }

  if (!Array.isArray(env.assumptions)) err("assumptions", "assumptions must be an array");
  else {
    env.assumptions.forEach((x, i) => {
      if (!isObj(x) || !isStr(x.name) || !("value" in x) || x.value === undefined || !isStr(x.source) || !isJson(x.value)) {
        err(`assumptions[${i}]`, "assumption must be {name, value, source} with a JSON value");
      }
    });
  }

  if (!Array.isArray(env.evidence)) err("evidence", "evidence must be an array");
  else {
    env.evidence.forEach((e, i) => {
      const p = `evidence[${i}]`;
      if (!isObj(e)) return err(p, "evidence item must be an object");
      if (!isStr(e.url)) err(`${p}.url`, "url must be a non-empty string");
      if (e.date !== null && !realDate(e.date)) err(`${p}.date`, "date must be YYYY-MM-DD or null");
      if (typeof e.verified !== "boolean") err(`${p}.verified`, "verified must be a boolean");
      if (e.text !== undefined && typeof e.text !== "string") err(`${p}.text`, "text must be a string");
      if (e.retrieved_at !== undefined && !(typeof e.retrieved_at === "string" && ISO_RE.test(e.retrieved_at))) {
        err(`${p}.retrieved_at`, "retrieved_at must be an ISO-8601 timestamp");
      }
      if (e.spine !== undefined) {
        const s = e.spine;
        if (!isObj(s) || typeof s.spine_id !== "string" || !SPINE_ID_RE.test(s.spine_id)) err(`${p}.spine.spine_id`, "spine_id must look like sp_ + 16 hex");
        if (!isObj(s) || !Array.isArray(s.line_ids) || s.line_ids.length === 0 || !s.line_ids.every(isStr)) {
          err(`${p}.spine.line_ids`, "line_ids must be a non-empty array of strings");
        }
      }
    });
  }

  if (!Array.isArray(env.limits) || !env.limits.every((l) => typeof l === "string")) err("limits", "limits must be an array of strings");
  if (env.next_action !== null && typeof env.next_action !== "string") err("next_action", "next_action must be a string or null");

  const r = env.receipt;
  if (!isObj(r)) err("receipt", "receipt must be {tool, version, as_of}");
  else {
    if (!isStr(r.tool)) err("receipt.tool", "tool must be a non-empty string");
    if (!isStr(r.version)) err("receipt.version", "version must be a non-empty string");
    if (!(realDate(r.as_of) || (typeof r.as_of === "string" && ISO_RE.test(r.as_of)))) err("receipt.as_of", "as_of must be YYYY-MM-DD or an ISO-8601 timestamp");
  }

  if (Array.isArray(env.unknowns)) {
    const valid = env.unknowns.filter((u) => isObj(u) && isStr(u.field));
    const c = checkUnknownsNotCollapsed(env, valid);
    if (!c.ok) errors.push(...c.errors);
  }

  return errors.length ? { ok: false, errors } : { ok: true, envelope: env };
}

/** Status is derived, never typed by hand: error beats abstain beats partial beats ok. */
export function deriveStatus({ error = false, abstain = null, unknowns = [] } = {}) {
  if (error) return "error";
  if (abstain) return "abstain";
  if (unknowns && unknowns.length > 0) return "partial";
  return "ok";
}

/** Build a valid envelope. Status is derived; a conflicting `status` input throws. Confidence defaults to unmeasured/null. */
export function makeEnvelope(input) {
  const i = input ?? {};
  const derived = deriveStatus({ error: i.error === true, abstain: i.abstain ?? null, unknowns: i.unknowns ?? [] });
  if (i.status !== undefined && i.status !== derived) throw new Error(`result-envelope: status ${i.status} conflicts with derived status ${derived}; status is set by code`);
  const env = {
    summary: i.summary,
    status: derived,
    confidence: i.confidence ?? { value: null, basis: "unmeasured" },
    abstain: i.abstain ?? null,
    unknowns: i.unknowns ?? [],
    assumptions: i.assumptions ?? [],
    evidence: i.evidence ?? [],
    limits: i.limits ?? [],
    next_action: i.next_action ?? null,
    receipt: i.receipt,
  };
  const v = validateEnvelope(env);
  if (!v.ok) throw new Error(`result-envelope: invalid envelope: ${v.errors.map((e) => `${e.path || "(root)"}: ${e.message}`).join("; ")}`);
  return env;
}

/** Map a content_spine/v1 Evidence row to an envelope evidence item, optionally citing spine lines instead of restating them. */
export function fromSpineEvidence(ev, { verified, spine } = {}) {
  const item = { url: ev.url, date: ev.date ?? null, verified: verified === true };
  if (typeof ev.title === "string" && ev.title !== "") item.text = ev.title;
  if (spine) item.spine = spine;
  return item;
}

const MISSING = Symbol("missing");
function lookup(data, dotted) {
  let cur = data;
  for (const k of dotted.split(".")) {
    if (Array.isArray(cur)) {
      if (!/^\d+$/.test(k) || Number(k) >= cur.length) return MISSING;
      cur = cur[Number(k)];
    } else if (isObj(cur) && k in cur) cur = cur[k];
    else return MISSING;
  }
  return cur;
}

/** A field listed in unknowns must be null/absent in the result data, never 0, false, "cold" or blank. */
export function checkUnknownsNotCollapsed(data, unknowns) {
  const errors = [];
  for (const u of Array.isArray(unknowns) ? unknowns : []) {
    if (!isObj(u) || typeof u.field !== "string" || u.field === "") continue;
    let v;
    try {
      v = lookup(data, u.field);
    } catch {
      errors.push({ path: u.field, message: "field could not be inspected" });
      continue;
    }
    if (v === MISSING || v === null) continue;
    errors.push({ path: u.field, message: `field is listed as unknown but carries ${describe(v)}; it must be null` });
  }
  return errors.length ? { ok: false, errors } : { ok: true };
}

const str = { type: "string", minLength: 1 };
const dateStr = { type: "string", pattern: "^\\d{4}-\\d{2}-\\d{2}$" };

/** JSON Schema (2020-12) for MCP outputSchema. Cross-field rules are in validateEnvelope; the ones JSON Schema can express are here too. */
export const RESULT_ENVELOPE_JSON_SCHEMA = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  title: "ResultEnvelope",
  description: `${CONTRACT}: summary, status (set by code), confidence with basis, abstain, unknowns, assumptions, evidence, limits, next_action, receipt.`,
  type: "object",
  additionalProperties: true,
  required: [...ENVELOPE_FIELDS],
  properties: {
    summary: str,
    status: { enum: [...STATUSES] },
    confidence: {
      type: "object",
      required: ["value", "basis"],
      properties: {
        value: { type: ["number", "null"], minimum: 0, maximum: 1 },
        basis: { enum: [...CONFIDENCE_BASES] },
      },
      oneOf: [
        { properties: { basis: { const: "unmeasured" }, value: { type: "null" } } },
        { properties: { basis: { not: { const: "unmeasured" } }, value: { type: "number" } } },
      ],
    },
    abstain: {
      oneOf: [
        { type: "null" },
        {
          type: "object",
          required: ["reason"],
          properties: { reason: str, closest: { type: "string" }, to_collect: { type: "array", items: { type: "string" } } },
        },
      ],
    },
    unknowns: { type: "array", items: { type: "object", required: ["field", "why"], properties: { field: str, why: str } } },
    assumptions: { type: "array", items: { type: "object", required: ["name", "value", "source"], properties: { name: str, value: {}, source: str } } },
    evidence: {
      type: "array",
      items: {
        type: "object",
        required: ["url", "date", "verified"],
        properties: {
          text: { type: "string" },
          url: str,
          date: { oneOf: [dateStr, { type: "null" }] },
          retrieved_at: { type: "string", format: "date-time" },
          verified: { type: "boolean" },
          spine: {
            type: "object",
            required: ["spine_id", "line_ids"],
            properties: { spine_id: { type: "string", pattern: "^sp_[0-9a-f]{16}$" }, line_ids: { type: "array", minItems: 1, items: str } },
          },
        },
      },
    },
    limits: { type: "array", items: { type: "string" } },
    next_action: { type: ["string", "null"] },
    receipt: {
      type: "object",
      required: ["tool", "version", "as_of"],
      properties: { tool: str, version: str, as_of: { type: "string", minLength: 10 } },
    },
  },
  allOf: [
    {
      if: { properties: { status: { const: "abstain" } }, required: ["status"] },
      then: { properties: { abstain: { type: "object" } } },
      else: { properties: { abstain: { type: "null" } } },
    },
    { if: { properties: { status: { const: "ok" } }, required: ["status"] }, then: { properties: { unknowns: { maxItems: 0 } } } },
  ],
};

/** Add the envelope beside an existing outputSchema (additive: never removes or renames its fields). Throws on a name clash. */
export function withEnvelope(outputSchema) {
  const base = outputSchema ?? { type: "object" };
  const props = base.properties ?? {};
  for (const k of ENVELOPE_FIELDS) {
    if (k in props) throw new Error(`result-envelope: outputSchema already defines "${k}"`);
  }
  const { $schema, title, description, allOf, ...rest } = RESULT_ENVELOPE_JSON_SCHEMA; // eslint-disable-line no-unused-vars
  return {
    ...base,
    type: "object",
    properties: { ...props, ...rest.properties },
    required: [...new Set([...(base.required ?? []), ...ENVELOPE_FIELDS])],
    allOf: [...(base.allOf ?? []), ...allOf],
  };
}
