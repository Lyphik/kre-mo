import type { IncomingMessage, ServerResponse } from "node:http";
import { getActiveMode, getProvider } from "../providers/index.js";
import { getSource, SCENARIO_QUESTION, SCENARIO_SUBJECT, SOURCES } from "../scenario/river-crossing.js";
import { computeConsensus } from "../consensus/engine.js";
import type { Observation } from "../providers/types.js";

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(payload),
  });
  res.end(payload);
}

async function readJsonBody(req: IncomingMessage, maxBytes = 1_000_000): Promise<unknown> {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of req) {
    size += (chunk as Buffer).length;
    if (size > maxBytes) {
      throw new Error("Request body too large");
    }
    chunks.push(chunk as Buffer);
  }
  if (chunks.length === 0) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function isObservation(value: unknown): value is Observation {
  if (!value || typeof value !== "object") return false;
  const o = value as Record<string, unknown>;
  return (
    typeof o.sourceId === "string" &&
    typeof o.sourceName === "string" &&
    (o.mode === "live" || o.mode === "demo") &&
    (o.status === "operating" || o.status === "not_operating" || o.status === "uncertain") &&
    (o.valid_until === null || typeof o.valid_until === "string") &&
    typeof o.details === "string" &&
    typeof o.source_confidence === "number" &&
    typeof o.observed_at === "string" &&
    Array.isArray(o.evidence)
  );
}

export async function handleModeRoute(_req: IncomingMessage, res: ServerResponse): Promise<void> {
  sendJson(res, 200, { mode: getActiveMode() });
}

export async function handleScenarioRoute(_req: IncomingMessage, res: ServerResponse): Promise<void> {
  sendJson(res, 200, {
    question: SCENARIO_QUESTION,
    subject: SCENARIO_SUBJECT,
    sources: SOURCES.map((s) => ({ id: s.id, name: s.name, role: s.role })),
  });
}

export async function handleObserveRoute(
  _req: IncomingMessage,
  res: ServerResponse,
  sourceId: string,
): Promise<void> {
  const source = getSource(sourceId);
  if (!source) {
    sendJson(res, 404, { error: "unknown_source", message: `No such source: ${sourceId}` });
    return;
  }
  try {
    const provider = getProvider();
    const observation = await provider.query(source);
    sendJson(res, 200, observation);
  } catch (err) {
    sendJson(res, 502, {
      error: "observe_failed",
      message: err instanceof Error ? err.message : "Unknown error acquiring source.",
    });
  }
}

export async function handleConsensusRoute(req: IncomingMessage, res: ServerResponse): Promise<void> {
  let body: unknown;
  try {
    body = await readJsonBody(req);
  } catch (err) {
    sendJson(res, 413, {
      error: "payload_too_large",
      message: err instanceof Error ? err.message : "Body too large.",
    });
    return;
  }

  const observations = (body as { observations?: unknown }).observations;
  if (!Array.isArray(observations) || observations.length === 0 || !observations.every(isObservation)) {
    sendJson(res, 400, {
      error: "invalid_request",
      message: "Expected { observations: Observation[] } with at least one valid observation.",
    });
    return;
  }

  const result = computeConsensus(observations, new Date(), SCENARIO_SUBJECT);
  sendJson(res, 200, result);
}
