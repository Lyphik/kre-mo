import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";
import {
  handleModeRoute,
  handleScenarioRoute,
  handleObserveRoute,
  handleConsensusRoute,
} from "./routes.js";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
dotenv.config({ path: resolve(projectRoot, ".env.local") });

const PORT = Number(process.env.PORT ?? 8787);

const STATIC_FILES: Record<string, { path: string; type: string }> = {
  "/": { path: resolve(projectRoot, "web/index.html"), type: "text/html; charset=utf-8" },
  "/style.css": { path: resolve(projectRoot, "web/style.css"), type: "text/css; charset=utf-8" },
  "/main.js": { path: resolve(projectRoot, "dist/web/main.js"), type: "text/javascript; charset=utf-8" },
};

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url ?? "/", `http://localhost:${PORT}`);
    const path = url.pathname;

    if (req.method === "GET" && path in STATIC_FILES) {
      const file = STATIC_FILES[path]!;
      const body = await readFile(file.path);
      res.writeHead(200, { "content-type": file.type, "content-length": body.length });
      res.end(body);
      return;
    }

    if (req.method === "GET" && path === "/api/mode") return void (await handleModeRoute(req, res));
    if (req.method === "GET" && path === "/api/scenario") return void (await handleScenarioRoute(req, res));

    const observeMatch = /^\/api\/observe\/([ab])$/.exec(path);
    if (req.method === "POST" && observeMatch) {
      return void (await handleObserveRoute(req, res, observeMatch[1]!));
    }

    if (req.method === "POST" && path === "/api/consensus") return void (await handleConsensusRoute(req, res));

    res.writeHead(404, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: "not_found" }));
  } catch (err) {
    res.writeHead(500, { "content-type": "application/json" });
    res.end(
      JSON.stringify({
        error: "internal_error",
        message: err instanceof Error ? err.message : "Unknown error.",
      }),
    );
  }
});

server.listen(PORT, () => {
  const mode = process.env.CALLE_MODE === "live" ? "live" : "demo";
  console.log(`Kre mo listening on http://localhost:${PORT} (mode: ${mode})`);
});
