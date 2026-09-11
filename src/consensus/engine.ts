import type { Observation } from "../providers/types.js";
import type { ConsensusResult, VerificationStatus } from "./types.js";

function round2(value: number): number {
  return Math.round(value * 100) / 100;
}

function mean(values: number[]): number {
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

function formatFreshness(elapsedMs: number): string {
  const seconds = Math.max(0, Math.round(elapsedMs / 1000));
  if (seconds < 60) return `CHECKED ${seconds} SECOND${seconds === 1 ? "" : "S"} AGO`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `CHECKED ${minutes} MINUTE${minutes === 1 ? "" : "S"} AGO`;
  const hours = Math.round(minutes / 60);
  return `CHECKED ${hours} HOUR${hours === 1 ? "" : "S"} AGO`;
}

/** Shared valid_until only when every agreeing source reports the exact same value; otherwise unknown. */
function agreedValidUntil(agreeing: Observation[]): string | null {
  if (agreeing.length === 0) return null;
  const first = agreeing[0]!.valid_until;
  if (first === null) return null;
  return agreeing.every((o) => o.valid_until === first) ? first : null;
}

function buildAnswer(
  status: VerificationStatus,
  agreeing: Observation[],
  validUntil: string | null,
  subject: string,
): string | null {
  if (status === "verified") {
    const winning = agreeing[0]!.status;
    if (winning === "operating") {
      return validUntil ? `${subject} operating until ${validUntil}.` : `${subject} operating.`;
    }
    return `${subject} not operating.`;
  }
  if (status === "conflicting") {
    return `Sources disagree on whether the ${subject.toLowerCase()} is operating.`;
  }
  return null; // insufficient - no definitive summary to give
}

/**
 * Pure, deterministic consensus computation. No I/O, no randomness, no LLM.
 *
 * Kre mo is a corroboration system: one source is an observation, not a
 * verified fact. Rules:
 * - Any direct contradiction between definite (operating/not_operating)
 *   sources -> conflicting, regardless of which side has more sources (a
 *   2-vs-1 majority is still a contradiction, never smoothed into verified).
 * - Otherwise, two or more definite sources agreeing -> verified.
 * - A single definite source alone, or no definite source at all (all
 *   uncertain / partial evidence) -> insufficient. One source alone can
 *   never be "verified" - corroboration requires at least two.
 *
 * Confidence is defined ONLY when verification_status is "verified" (mean of
 * the agreeing sources' source_confidence, rounded to 2 decimals). For
 * "conflicting" or "insufficient" it is `null`, never `0` - zero would imply
 * a measured zero-confidence result, whereas the real meaning is "no valid
 * consensus confidence exists".
 */
export function computeConsensus(
  observations: Observation[],
  now: Date,
  subject = "Crossing",
): ConsensusResult {
  if (observations.length === 0) {
    throw new Error("computeConsensus requires at least one observation");
  }

  const total = observations.length;
  const operating = observations.filter((o) => o.status === "operating");
  const notOperating = observations.filter((o) => o.status === "not_operating");

  let verification_status: VerificationStatus;
  let agreeingObs: Observation[];

  if (operating.length > 0 && notOperating.length > 0) {
    verification_status = "conflicting";
    agreeingObs = operating.length >= notOperating.length ? operating : notOperating;
  } else {
    const definite = operating.length > 0 ? operating : notOperating;
    agreeingObs = definite;
    verification_status = definite.length >= 2 ? "verified" : "insufficient";
  }

  const confidence =
    verification_status === "verified"
      ? round2(mean(agreeingObs.map((o) => o.source_confidence)))
      : null;

  const validUntil = verification_status === "verified" ? agreedValidUntil(agreeingObs) : null;

  const oldest = observations.reduce((a, b) => (a.observed_at < b.observed_at ? a : b));
  const freshness = formatFreshness(now.getTime() - Date.parse(oldest.observed_at));

  return {
    verification_status,
    sources_agreeing: agreeingObs.length,
    sources_total: total,
    confidence,
    verified_at: now.toISOString(),
    freshness,
    valid_until: validUntil,
    answer: buildAnswer(verification_status, agreeingObs, validUntil, subject),
    evidence: observations.flatMap((o) => o.evidence.map((line) => `${o.sourceName}: ${line}`)),
  };
}
