import { test } from "node:test";
import assert from "node:assert/strict";
import { computeConsensus } from "../src/consensus/engine.js";
import type { Observation } from "../src/providers/types.js";

const OBSERVED_AT = "2026-09-11T12:00:00.000Z";
const NOW = new Date("2026-09-11T12:00:14.000Z"); // 14s later

function obs(
  overrides: Partial<Observation> & Pick<Observation, "sourceId" | "status" | "source_confidence">,
): Observation {
  return {
    sourceName: overrides.sourceId === "a" ? "Field Source A" : "Field Source B",
    mode: "demo",
    valid_until: null,
    details: "",
    observed_at: OBSERVED_AT,
    evidence: [],
    ...overrides,
  };
}

// --- Corroboration rule: "one source is an observation, two agreeing
// independent sources can become a verified fact" ---

test("1) one operating source alone -> insufficient (never verified on one source)", () => {
  const result = computeConsensus(
    [obs({ sourceId: "a", status: "operating", source_confidence: 0.95 })],
    NOW,
    "Crossing",
  );
  assert.equal(result.verification_status, "insufficient");
  assert.equal(result.confidence, null);
  assert.equal(result.sources_agreeing, 1);
  assert.equal(result.sources_total, 1);
  assert.equal(result.answer, null);
});

test("2) one not_operating source alone -> insufficient", () => {
  const result = computeConsensus(
    [obs({ sourceId: "a", status: "not_operating", source_confidence: 0.95 })],
    NOW,
    "Crossing",
  );
  assert.equal(result.verification_status, "insufficient");
  assert.equal(result.confidence, null);
  assert.equal(result.sources_agreeing, 1);
  assert.equal(result.answer, null);
});

test("3) two operating sources -> verified", () => {
  const result = computeConsensus(
    [
      obs({ sourceId: "a", status: "operating", source_confidence: 0.9, valid_until: "17:30" }),
      obs({ sourceId: "b", status: "operating", source_confidence: 0.85, valid_until: "17:30" }),
    ],
    NOW,
    "Crossing",
  );
  assert.equal(result.verification_status, "verified");
  assert.equal(result.sources_agreeing, 2);
  assert.equal(result.sources_total, 2);
  assert.equal(result.confidence, 0.88);
  assert.equal(result.valid_until, "17:30");
  assert.equal(result.answer, "Crossing operating until 17:30.");
  assert.equal(result.freshness, "CHECKED 14 SECONDS AGO");
});

test("4) two not_operating sources -> verified", () => {
  const result = computeConsensus(
    [
      obs({ sourceId: "a", status: "not_operating", source_confidence: 0.9 }),
      obs({ sourceId: "b", status: "not_operating", source_confidence: 0.8 }),
    ],
    NOW,
    "Crossing",
  );
  assert.equal(result.verification_status, "verified");
  assert.equal(result.sources_agreeing, 2);
  assert.equal(result.confidence, 0.85);
  assert.equal(result.answer, "Crossing not operating.");
});

test("5) one operating + one uncertain -> insufficient (partial evidence is not corroboration)", () => {
  const result = computeConsensus(
    [
      obs({ sourceId: "a", status: "operating", source_confidence: 0.9 }),
      obs({ sourceId: "b", status: "uncertain", source_confidence: 0 }),
    ],
    NOW,
    "Crossing",
  );
  assert.equal(result.verification_status, "insufficient");
  assert.equal(result.confidence, null);
  assert.equal(result.sources_agreeing, 1);
  assert.equal(result.answer, null);
});

test("6) operating + not_operating -> conflicting, confidence null (never 0)", () => {
  const result = computeConsensus(
    [
      obs({ sourceId: "a", status: "operating", source_confidence: 0.9 }),
      obs({ sourceId: "b", status: "not_operating", source_confidence: 0.7 }),
    ],
    NOW,
    "Crossing",
  );
  assert.equal(result.verification_status, "conflicting");
  assert.equal(result.confidence, null);
  assert.equal(result.sources_agreeing, 1);
  assert.equal(result.answer, "Sources disagree on whether the crossing is operating.");
});

test("7) three sources, 2 operating + 1 not_operating -> conflicting (contradiction always wins, even on a majority)", () => {
  const result = computeConsensus(
    [
      obs({ sourceId: "a", status: "operating", source_confidence: 0.8 }),
      obs({ sourceId: "b", status: "operating", source_confidence: 0.8 }),
      obs({ sourceId: "a", status: "not_operating", source_confidence: 0.9 }),
    ],
    NOW,
    "Crossing",
  );
  assert.equal(result.verification_status, "conflicting");
  assert.equal(result.confidence, null);
  assert.equal(result.sources_agreeing, 2);
});

// --- supplementary coverage ---

test("all sources uncertain -> insufficient, confidence null, no answer", () => {
  const result = computeConsensus(
    [
      obs({ sourceId: "a", status: "uncertain", source_confidence: 0 }),
      obs({ sourceId: "b", status: "uncertain", source_confidence: 0 }),
    ],
    NOW,
    "Crossing",
  );
  assert.equal(result.verification_status, "insufficient");
  assert.equal(result.confidence, null);
  assert.equal(result.sources_agreeing, 0);
  assert.equal(result.answer, null);
});

test("mismatched valid_until across two agreeing sources -> reported valid_until is null", () => {
  const result = computeConsensus(
    [
      obs({ sourceId: "a", status: "operating", source_confidence: 0.9, valid_until: "17:30" }),
      obs({ sourceId: "b", status: "operating", source_confidence: 0.8, valid_until: "18:00" }),
    ],
    NOW,
    "Crossing",
  );
  assert.equal(result.verification_status, "verified");
  assert.equal(result.valid_until, null);
  assert.equal(result.answer, "Crossing operating.");
});

test("three sources, 2 operating + 1 uncertain (no contradiction) -> verified on the 2 agreeing", () => {
  const result = computeConsensus(
    [
      obs({ sourceId: "a", status: "operating", source_confidence: 0.9 }),
      obs({ sourceId: "b", status: "operating", source_confidence: 0.8 }),
      obs({ sourceId: "a", status: "uncertain", source_confidence: 0 }),
    ],
    NOW,
    "Crossing",
  );
  assert.equal(result.verification_status, "verified");
  assert.equal(result.sources_agreeing, 2);
  assert.equal(result.sources_total, 3);
  assert.equal(result.confidence, 0.85);
});

test("empty observations array throws", () => {
  assert.throws(() => computeConsensus([], NOW, "Crossing"));
});
