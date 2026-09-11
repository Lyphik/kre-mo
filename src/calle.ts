import { CalleClient } from "@call-e/calle";

/**
 * Read a required environment variable, or throw a clear error that never
 * echoes the value itself.
 */
export function requireEnv(name: string): string {
  const raw = process.env[name];
  const value = raw?.trim();
  if (!value) {
    throw new Error(
      `Missing required environment variable: ${name}. Set it in .env.local.`,
    );
  }
  return value;
}

/**
 * Build a CALL-E client from the environment.
 *
 * - `CALLE_API_KEY` (required) is read but never logged.
 * - `CALLE_BASE_URL` (optional) overrides the SDK default when set.
 */
export function makeCalleClient(): CalleClient {
  const options: { apiKey: string; baseUrl?: string } = {
    apiKey: requireEnv("CALLE_API_KEY"),
  };
  const baseUrl = process.env.CALLE_BASE_URL?.trim();
  if (baseUrl) {
    options.baseUrl = baseUrl;
  }
  return new CalleClient(options);
}
