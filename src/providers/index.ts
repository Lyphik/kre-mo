import type { ProviderMode, SourceProvider } from "./types.js";
import { DemoProvider } from "./demo-provider.js";
import { LiveCalleProvider } from "./live-provider.js";

/**
 * Single source of truth for which mode is active. Deliberately reads only
 * from the server-side environment - never from client request input - so a
 * request body can never trigger a real phone call. Defaults to "demo".
 */
export function getActiveMode(): ProviderMode {
  return process.env.CALLE_MODE === "live" ? "live" : "demo";
}

export function getProvider(mode: ProviderMode = getActiveMode()): SourceProvider {
  return mode === "live" ? new LiveCalleProvider() : new DemoProvider();
}
