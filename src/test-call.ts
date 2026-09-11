/**
 * Phase 1 - smallest possible proof that the CALL-E integration works.
 *
 * Places ONE controlled call to a single authorized test number, asks exactly
 * one question ("Can you hear me clearly?"), and prints the structured result.
 *
 * Run with: npm run test:call
 */
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";
import { makeCalleClient, requireEnv } from "./calle.js";

// Load .env.local from the project root regardless of the current directory.
const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
dotenv.config({ path: resolve(projectRoot, ".env.local") });

/** Strict E.164: leading +, first digit 1-9, then 6-14 more digits. */
const E164 = /^\+[1-9]\d{6,14}$/;

const TASK =
  "Call the recipient and ask one simple question: 'Can you hear me clearly?' " +
  "Do not ask anything else. Thank them and end the call.";

const RESULT_SCHEMA = {
  type: "object",
  required: ["can_hear_clearly"],
  properties: {
    can_hear_clearly: { type: "string", enum: ["yes", "no", "unknown"] },
  },
  additionalProperties: false,
} as const;

async function main(): Promise<void> {
  const client = makeCalleClient();

  const phone = requireEnv("TEST_PHONE_NUMBER");
  if (!E164.test(phone)) {
    // Do not print the value - just fail closed.
    throw new Error(
      "TEST_PHONE_NUMBER is not valid E.164 format (expected e.g. +59400000000).",
    );
  }
  const locale = process.env.TEST_LOCALE?.trim() || "fr-FR";

  // idempotencyKey is optional in the SDK; omitted for this manual Phase-1 test.
  const call = await client.calls.createAndWait(
    {
      task: TASK,
      recipient: { phone, locale },
      resultSchema: RESULT_SCHEMA as unknown as Record<string, unknown>,
      metadata: { project: "kre-mo", phase: "1-first-call" },
    },
    { intervalMs: 2000, timeoutMs: 300_000 },
  );

  const out = {
    status: call.status,
    structuredResult: call.structuredResult,
    taskCompleted: call.taskCompleted,
    completionConfidence: call.completionConfidence,
    evidence: call.evidence,
  };
  console.log(JSON.stringify(out, null, 2));
}

main().catch((err: unknown) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
