import { makeCalleClient, requireEnv } from "../calle.js";
import type { Observation, SourceDefinition, SourceProvider, SourceStatus } from "./types.js";

const OBSERVATION_RESULT_SCHEMA = {
  type: "object",
  required: ["status", "valid_until", "details", "source_confidence"],
  properties: {
    status: { type: "string", enum: ["operating", "not_operating", "uncertain"] },
    valid_until: { type: ["string", "null"] },
    details: { type: "string" },
    source_confidence: { type: "number", minimum: 0, maximum: 1 },
  },
  additionalProperties: false,
} as const;

function isSourceStatus(value: unknown): value is SourceStatus {
  return value === "operating" || value === "not_operating" || value === "uncertain";
}

/**
 * Places a real CALL-E call for one source and maps the result to an
 * Observation. Never fabricates a definite answer: if the task did not
 * complete or the structured result is missing/malformed, the observation
 * falls back to status "uncertain" rather than guessing.
 */
export class LiveCalleProvider implements SourceProvider {
  readonly mode = "live" as const;

  async query(source: SourceDefinition): Promise<Observation> {
    const client = makeCalleClient();
    const phone = requireEnv(source.live.phoneEnvVar);
    const locale = requireEnv(source.live.localeEnvVar);

    const task =
      `Call the recipient and ask: "${source.question}" ` +
      "Determine whether the situation is currently operating, not operating, or uncertain, " +
      "any known valid-until time, and any relevant details. " +
      "Do not ask anything else unrelated to this question. Thank them and end the call.";

    const call = await client.calls.createAndWait(
      {
        task,
        recipient: { phone, locale },
        resultSchema: OBSERVATION_RESULT_SCHEMA as unknown as Record<string, unknown>,
        metadata: { project: "kre-mo", phase: "2-river-crossing", sourceId: source.id },
      },
      { intervalMs: 2000, timeoutMs: 300_000 },
    );

    // Only trust structuredResult when the task actually completed - never
    // fabricate a definite answer from a partial or failed call.
    const result =
      call.taskCompleted === true ? (call.structuredResult as Record<string, unknown> | null) : null;
    const status: SourceStatus = result && isSourceStatus(result.status) ? result.status : "uncertain";

    return {
      sourceId: source.id,
      sourceName: source.name,
      mode: "live",
      status,
      valid_until: result && typeof result.valid_until === "string" ? result.valid_until : null,
      details:
        result && typeof result.details === "string"
          ? result.details
          : call.summary ?? "No structured details returned.",
      source_confidence:
        result && typeof result.source_confidence === "number" ? result.source_confidence : 0,
      observed_at: new Date().toISOString(),
      evidence: call.evidence ?? [],
    };
  }
}
