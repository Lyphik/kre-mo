export type SourceStatus = "operating" | "not_operating" | "uncertain";
export type SourceId = "a" | "b";
export type ProviderMode = "live" | "demo";

/** Raw structured fields a source call/fixture must produce. Matches the CALL-E resultSchema exactly. */
export interface RawObservation {
  status: SourceStatus;
  valid_until: string | null;
  details: string;
  source_confidence: number;
}

/** One source's definition: how to reach it live, and its deterministic demo fixture. */
export interface SourceDefinition {
  id: SourceId;
  name: string;
  role: string;
  question: string;
  live: {
    phoneEnvVar: string;
    localeEnvVar: string;
  };
  demo: RawObservation & {
    simulatedDelayMs: number;
  };
}

/** A completed observation, tagged with provenance so DEMO can never be mistaken for LIVE. */
export interface Observation extends RawObservation {
  sourceId: SourceId;
  sourceName: string;
  mode: ProviderMode;
  observed_at: string;
  evidence: string[];
}

export interface SourceProvider {
  readonly mode: ProviderMode;
  query(source: SourceDefinition): Promise<Observation>;
}
