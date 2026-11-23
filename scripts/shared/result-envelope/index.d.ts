/**
 * @jmc-go-to-market/result-envelope: one result format for every tool (result_envelope/v1).
 * Zero dependencies, one runtime file. Add the envelope ADDITIVELY beside existing output.
 */

export declare const CONTRACT: "result_envelope/v1";
export declare const STATUSES: readonly ["ok", "partial", "abstain", "error"];
export declare const CONFIDENCE_BASES: readonly ["jev", "rule", "measured", "model_self_report", "unmeasured"];
export declare const ENVELOPE_FIELDS: readonly string[];

export type Status = "ok" | "partial" | "abstain" | "error";
export type ConfidenceBasis = "jev" | "rule" | "measured" | "model_self_report" | "unmeasured";

/** value is null exactly when basis is "unmeasured". Never invent a confidence. */
export type Confidence =
  | { value: null; basis: "unmeasured" }
  | { value: number; basis: Exclude<ConfidenceBasis, "unmeasured"> };

export interface Abstain {
  reason: string;
  closest?: string;
  to_collect?: string[];
}

/** A field the tool could not determine. Never collapse it to 0, false, "cold" or blank. */
export interface Unknown {
  field: string;
  why: string;
}

export interface Assumption {
  name: string;
  value: unknown;
  source: string;
}

/** Cite spine lines (content_spine/v1) instead of restating them. */
export interface SpineRef {
  /** "sp_" + 16 hex */
  spine_id: string;
  line_ids: string[];
}

/** Compatible with content-spine Evidence (url, date); extra spine fields pass through. */
export interface EvidenceItem {
  text?: string;
  url: string;
  /** YYYY-MM-DD, or null when unknown */
  date: string | null;
  /** ISO-8601 */
  retrieved_at?: string;
  verified: boolean;
  spine?: SpineRef;
}

export interface Receipt {
  tool: string;
  version: string;
  /** YYYY-MM-DD or ISO-8601 */
  as_of: string;
}

export interface ResultEnvelope {
  summary: string;
  /** set by code (deriveStatus / makeEnvelope), never typed by hand */
  status: Status;
  confidence: Confidence;
  /** non-null iff status is "abstain" */
  abstain: Abstain | null;
  /** non-empty is never status "ok" */
  unknowns: Unknown[];
  assumptions: Assumption[];
  evidence: EvidenceItem[];
  limits: string[];
  next_action: string | null;
  receipt: Receipt;
}

export interface ValidationError {
  path: string;
  message: string;
}
export type ValidationResult =
  | { ok: true; envelope: ResultEnvelope }
  | { ok: false; errors: ValidationError[] };

/** Extra fields beside the envelope are allowed. Never throws. */
export declare function validateEnvelope(env: unknown): ValidationResult;

export declare function deriveStatus(input?: { error?: boolean; abstain?: Abstain | null; unknowns?: Unknown[] }): Status;

export interface EnvelopeInput {
  summary: string;
  receipt: Receipt;
  error?: boolean;
  /** only accepted if it equals the derived status */
  status?: Status;
  confidence?: Confidence;
  abstain?: Abstain | null;
  unknowns?: Unknown[];
  assumptions?: Assumption[];
  evidence?: EvidenceItem[];
  limits?: string[];
  next_action?: string | null;
}
/** Derives status, defaults confidence to {value:null, basis:"unmeasured"}, validates, throws on invalid. */
export declare function makeEnvelope(input: EnvelopeInput): ResultEnvelope;

/** Map a content-spine Evidence row (structurally typed) to an envelope evidence item. */
export declare function fromSpineEvidence(
  ev: { url: string; date: string | null; title?: string },
  opts?: { verified?: boolean; spine?: SpineRef },
): EvidenceItem;

/** Fields listed in unknowns must be null or absent in `data` (dotted paths allowed). */
export declare function checkUnknownsNotCollapsed(
  data: unknown,
  unknowns: Unknown[],
): { ok: true } | { ok: false; errors: ValidationError[] };

/** JSON Schema 2020-12 for MCP outputSchema. */
export declare const RESULT_ENVELOPE_JSON_SCHEMA: Record<string, unknown> & { type: "object"; required: string[]; properties: Record<string, any> };

/** Merge the envelope into an existing outputSchema without removing fields. Throws on a name clash. */
export declare function withEnvelope<T extends Record<string, unknown>>(outputSchema?: T): Record<string, unknown>;
