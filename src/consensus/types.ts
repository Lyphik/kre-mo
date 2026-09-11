import type { Observation } from "../providers/types.js";

export type VerificationStatus = "verified" | "conflicting" | "insufficient";

export interface ConsensusResult {
  verification_status: VerificationStatus;
  sources_agreeing: number;
  sources_total: number;
  /** null (not 0) when no valid consensus confidence exists - see engine.ts. */
  confidence: number | null;
  verified_at: string;
  freshness: string;
  valid_until: string | null;
  /** Deterministic template output, never LLM-generated. Null when not definitive. */
  answer: string | null;
  evidence: string[];
}

export type { Observation };
