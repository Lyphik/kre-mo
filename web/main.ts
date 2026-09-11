type SourceStatus = "operating" | "not_operating" | "uncertain";
type ProviderMode = "live" | "demo";
type SourceIdent = "a" | "b";

interface Observation {
  sourceId: SourceIdent;
  sourceName: string;
  mode: ProviderMode;
  status: SourceStatus;
  valid_until: string | null;
  details: string;
  source_confidence: number;
  observed_at: string;
  evidence: string[];
}

interface ConsensusResult {
  verification_status: "verified" | "conflicting" | "insufficient";
  sources_agreeing: number;
  sources_total: number;
  confidence: number | null;
  verified_at: string;
  freshness: string;
  valid_until: string | null;
  answer: string | null;
  evidence: string[];
}

interface ScenarioInfo {
  question: string;
  subject: string;
  sources: { id: SourceIdent; name: string; role: string }[];
}

function byId<T extends HTMLElement>(id: string): T {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing element #${id}`);
  return el as T;
}

const modeBadge = byId("mode-badge");
const demoFlag = byId("demo-flag");
const questionText = byId("question-text");
const startButton = byId<HTMLButtonElement>("start-button");
const signal = byId("signal");
const signalState = byId("signal-state");
const resultSection = byId("result");
const errorSection = byId("error");
const errorMessage = byId("error-message");
const evidenceList = byId<HTMLUListElement>("evidence-list");

const IDLE_LABEL = "VERIFY FIELD STATUS";

function setNodeState(id: SourceIdent, state: "idle" | "acquiring" | "done", statusText: string): void {
  const node = byId(`node-${id}`);
  node.dataset.state = state;
  byId(`node-${id}-status`).textContent = statusText;
}

function setSignalState(state: string, label: string): void {
  signal.dataset.state = state;
  signalState.textContent = label;
}

function extractMessage(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "message" in body) {
    const m = (body as { message?: unknown }).message;
    if (typeof m === "string") return m;
  }
  return fallback;
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  const body: unknown = await res.json();
  if (!res.ok) {
    throw new Error(extractMessage(body, `Request failed (${res.status})`));
  }
  return body as T;
}

function renderMode(mode: ProviderMode): void {
  modeBadge.textContent = "";
  const dot = document.createElement("span");
  dot.className = "dot";
  modeBadge.appendChild(dot);
  modeBadge.appendChild(document.createTextNode(mode === "live" ? "MODE: LIVE" : "MODE: DEMO"));
  modeBadge.dataset.mode = mode;

  demoFlag.dataset.mode = mode;
  demoFlag.textContent =
    mode === "live"
      ? "◆ LIVE MODE — REAL CALLS TO AUTHORIZED NUMBERS"
      : "◆ DEMO MODE — SIMULATED SOURCES, NO REAL CALLS PLACED";
}

function showError(message: string): void {
  errorSection.hidden = false;
  errorMessage.textContent = message;
  startButton.disabled = false;
  startButton.textContent = IDLE_LABEL;
}

/** Purely presentational recency label derived from the server's own verified_at timestamp. */
function freshnessQualifier(verifiedAt: string): "FRESH" | "RECENT" | "STALE" {
  const elapsedMs = Date.now() - Date.parse(verifiedAt);
  if (elapsedMs < 30_000) return "FRESH";
  if (elapsedMs < 5 * 60_000) return "RECENT";
  return "STALE";
}

function renderResult(result: ConsensusResult, mode: ProviderMode): void {
  resultSection.hidden = false;
  resultSection.dataset.status = result.verification_status;

  const banner = byId("result-banner");
  const consensus = byId("result-consensus");
  const hero = byId("result-answer");
  const meta = byId("result-meta");

  const label =
    result.verification_status === "verified"
      ? `VERIFIED ${mode.toUpperCase()}`
      : result.verification_status === "conflicting"
        ? `CONFLICTING ${mode.toUpperCase()}`
        : `INSUFFICIENT ${mode.toUpperCase()}`;

  banner.textContent = label;
  consensus.textContent = `${result.sources_agreeing} / ${result.sources_total} SOURCES AGREE`;
  hero.textContent = result.answer ?? "NO DEFINITIVE ANSWER AVAILABLE";
  meta.textContent = `${result.freshness} · ${freshnessQualifier(result.verified_at)}`;

  evidenceList.innerHTML = "";
  for (const line of result.evidence) {
    const li = document.createElement("li");
    li.textContent = line; // never innerHTML - evidence is untrusted transcript-derived text
    evidenceList.appendChild(li);
  }
}

async function runVerification(): Promise<void> {
  startButton.disabled = true;
  startButton.textContent = "VERIFYING…";
  resultSection.hidden = true;
  errorSection.hidden = true;
  evidenceList.innerHTML = "";
  setNodeState("a", "idle", "STANDBY");
  setNodeState("b", "idle", "STANDBY");

  try {
    setSignalState("acquiring-a", "ACQUIRING A");
    setNodeState("a", "acquiring", "ACQUIRING…");
    const obsA = await fetchJson<Observation>("/api/observe/a", { method: "POST" });
    setNodeState("a", "done", obsA.status.replace("_", " ").toUpperCase());

    setSignalState("acquiring-b", "ACQUIRING B");
    setNodeState("b", "acquiring", "ACQUIRING…");
    const obsB = await fetchJson<Observation>("/api/observe/b", { method: "POST" });
    setNodeState("b", "done", obsB.status.replace("_", " ").toUpperCase());

    setSignalState("comparing", "EVALUATING");
    const result = await fetchJson<ConsensusResult>("/api/consensus", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ observations: [obsA, obsB] }),
    });

    setSignalState(result.verification_status, result.verification_status.toUpperCase());
    renderResult(result, obsA.mode);
  } catch (err) {
    setSignalState("idle", "ERROR");
    showError(err instanceof Error ? err.message : "Unknown error.");
    return;
  }

  startButton.disabled = false;
  startButton.textContent = IDLE_LABEL;
}

async function init(): Promise<void> {
  try {
    const [mode, scenario] = await Promise.all([
      fetchJson<{ mode: ProviderMode }>("/api/mode"),
      fetchJson<ScenarioInfo>("/api/scenario"),
    ]);
    renderMode(mode.mode);
    questionText.textContent = scenario.question;

    for (const source of scenario.sources) {
      byId(`node-${source.id}-name`).textContent = source.name;
      byId(`node-${source.id}-role`).textContent = source.role;
    }
  } catch (err) {
    showError(err instanceof Error ? err.message : "Failed to load scenario.");
  }
}

startButton.addEventListener("click", () => {
  void runVerification();
});

void init();
