import type { Observation, SourceDefinition, SourceProvider } from "./types.js";

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Deterministic simulated source. Never contacts CALL-E, never places a call.
 * Every observation is explicitly tagged mode: "demo" and every evidence line
 * is prefixed "[SIMULATED]" so it cannot be mistaken for a real call result
 * even if rendered without additional labeling.
 */
export class DemoProvider implements SourceProvider {
  readonly mode = "demo" as const;

  async query(source: SourceDefinition): Promise<Observation> {
    await sleep(source.demo.simulatedDelayMs);
    return {
      sourceId: source.id,
      sourceName: source.name,
      mode: "demo",
      status: source.demo.status,
      valid_until: source.demo.valid_until,
      details: source.demo.details,
      source_confidence: source.demo.source_confidence,
      observed_at: new Date().toISOString(),
      evidence: [`[SIMULATED] ${source.demo.details}`],
    };
  }
}
