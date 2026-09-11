import type { SourceDefinition } from "../providers/types.js";

export const SCENARIO_QUESTION = "Is the river crossing operating this afternoon?";

/** Short noun used to build deterministic answer sentences, e.g. "Crossing operating until 17:30." */
export const SCENARIO_SUBJECT = "Crossing";

// Fictional, neutral source identities for DEMO mode - never a real business
// or operator name. LIVE mode reuses the same identities and role labels;
// only the phone number/locale env vars differ per source.
export const SOURCES: readonly [SourceDefinition, SourceDefinition] = [
  {
    id: "a",
    name: "Field Source A",
    role: "North approach",
    question: SCENARIO_QUESTION,
    live: { phoneEnvVar: "SOURCE_A_PHONE_NUMBER", localeEnvVar: "SOURCE_A_LOCALE" },
    demo: {
      status: "operating",
      valid_until: "17:30",
      details: "Ferry running on schedule, last crossing confirmed 12 minutes ago.",
      source_confidence: 0.9,
      simulatedDelayMs: 1400,
    },
  },
  {
    id: "b",
    name: "Field Source B",
    role: "South approach",
    question: SCENARIO_QUESTION,
    live: { phoneEnvVar: "SOURCE_B_PHONE_NUMBER", localeEnvVar: "SOURCE_B_LOCALE" },
    demo: {
      status: "operating",
      valid_until: "17:30",
      details: "Crossing point open, water level normal for this hour.",
      source_confidence: 0.85,
      simulatedDelayMs: 1800,
    },
  },
];

export function getSource(id: string): SourceDefinition | undefined {
  return SOURCES.find((s) => s.id === id);
}
