# KRÈ MO
### FIELD VERIFICATION NETWORK

**Krè mo turns phone calls into structured, corroborated, timestamped real-world facts.**

> "One source is an observation. Agreement makes it a verified fact."

---

## Problem

Important real-world information often exists only behind a phone number: is a river
crossing operating, is a service running, is a supplier open. The internet can't
answer questions like this reliably — the ground truth lives with a person who has
to pick up a phone. Every AI agent that asks the internet is asking the wrong source.

## Origin in French Guiana

The concept comes from a real environment: river crossings, long distances, borders,
and conditions that change hour to hour, with no reliable digital feed to check them
against. That's the origin, not the whole product — the same problem exists anywhere
a critical fact only lives with a human on the other end of a phone line.

## How it works

```
QUESTION
  -> Source A (independent phone call)
  -> Source B (independent phone call)
  -> structured observations
  -> deterministic consensus engine
  -> VERIFIED / CONFLICTING / INSUFFICIENT
  -> timestamp + freshness + evidence
```

One polished scenario ships in this build: *"Is the river crossing operating this
afternoon?"*, asked to two independent field sources.

## Why CALL-E

CALL-E is the phone-calling substrate: given a task description, a recipient, and a
JSON result schema, it places a real call and returns a schema-validated structured
result instead of raw audio or a transcript. That's exactly what Krè mo needs — a
machine-readable observation from a real conversation, not another chatbot layer.

## Verification model

Deterministic, auditable, no LLM in the scoring path:

- Any contradiction between definite (`operating` / `not_operating`) sources ->
  **conflicting** — even a 2-vs-1 majority is still a contradiction, never smoothed
  into "verified."
- Two or more definite sources agreeing -> **verified**.
- A single definite source alone, or only uncertain/partial evidence -> **insufficient**.
  *One source is an observation, not a verified fact.*
- `confidence` is the mean `source_confidence` of the agreeing sources, rounded to
  2 decimals, and exists **only** for `verified`. It is `null` — never `0` — for
  `conflicting`/`insufficient`, because `0` would falsely imply a measured
  zero-confidence result rather than "no valid consensus confidence exists."
- The final `answer` is a deterministic template (e.g. *"Crossing operating until
  17:30."*), never LLM-generated.

Full rule set and behavior spec: `tests/consensus.engine.test.ts` (11 passing tests).

## Architecture

```
src/
  calle.ts              CalleClient factory (Phase 1, unchanged)
  test-call.ts           Phase 1 smoke test - one authorized test call
  providers/              LIVE/DEMO abstraction behind one interface
  consensus/              pure, deterministic consensus engine + types
  scenario/               the one river-crossing scenario definition
  server/                 stateless node:http server, 5 explicit routes
web/                      static frontend - plain TypeScript + CSS, no framework
tests/                    node:test unit tests for the consensus engine
```

Zero-dependency frontend, zero extra backend framework — plain `node:http`,
`node:test`, and the official `@call-e/calle` SDK. Server is fully stateless: no
database, no sessions, no accounts (not needed, not built).

## Demo vs Live mode

A single provider abstraction backs both:

- **DEMO** (default): deterministic simulated observations. No network call, no
  CALL-E usage. Every observation is tagged `mode: "demo"`, every evidence line is
  prefixed `[SIMULATED]`, and the UI always shows `MODE: DEMO` / `VERIFIED DEMO` —
  it never claims LIVE unless a real CALL-E call actually completed.
- **LIVE** (`CALLE_MODE=live`): places real CALL-E calls to the two source phone
  numbers in `.env.local`. Mode is decided **only** by the server's own
  environment, never by client request input.

Switching modes requires only `.env.local` changes — no code, route, or UI changes.

## Running locally

```bash
npm install
npm run build:web
npm run serve
# open http://localhost:8787
```

DEMO mode runs by default (`CALLE_MODE` unset). To exercise the Phase 1 smoke test
(one authorized controlled call) instead:

```bash
cp .env.local.example .env.local   # fill in CALLE_API_KEY and TEST_PHONE_NUMBER
npm run test:call
```

## Environment variables

| Variable | Required | Notes |
|---|---|---|
| `CALLE_API_KEY` | for LIVE mode / Phase 1 test script | CALL-E Developer API key |
| `TEST_PHONE_NUMBER` / `TEST_LOCALE` | Phase 1 script only | `npm run test:call` |
| `CALLE_MODE` | no | `demo` (default) or `live` |
| `SOURCE_A_PHONE_NUMBER` / `SOURCE_A_LOCALE` | LIVE mode only | Source A's authorized number |
| `SOURCE_B_PHONE_NUMBER` / `SOURCE_B_LOCALE` | LIVE mode only | Source B's authorized number |
| `PORT` | no | default `8787` |

## Tests

```bash
npm test        # 11 tests, consensus engine behavior spec
npm run typecheck
```

## CALL-E coverage note

Our available test destinations — a French Guiana (+594) number and a France
(+33) number, in both `fr-FR` and `en-US` — were rejected by CALL-E's live API
at task-creation time, before any call connected, despite France (`FR`) being
listed in CALL-E's published supported-regions table. We reported this
discrepancy to CALL-E support (support@heycall-e.com), without sharing the API
key or a full phone number. `LiveCalleProvider` remains fully implemented and
ready to run against any destination CALL-E confirms as supported.

## Future use cases

River crossings and transport operations, local service availability, infrastructure
status, supplier/vendor checks, field operations — anywhere the current, real answer
isn't reliably online and the only way to know is to ask someone directly.

## Hackathon notes

Built for the CALL-E "Your Code Is Calling" hackathon. Phase 1 validated the
CALL-E SDK integration, request construction, structured-result schema, and the
live provider path up to task creation. Our available +594/+33 destinations
were rejected by live coverage before a call connected. Phase 2 built the full
DEMO/LIVE provider abstraction, the deterministic consensus engine, and the
field-instrument interface. The submitted demo runs in DEMO mode for that
reason; the LIVE path is real, typechecked code, not a mock.
