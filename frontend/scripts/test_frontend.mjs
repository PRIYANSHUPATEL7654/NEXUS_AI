import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { build } from "vite";


const projectRoot = process.cwd();
const outputRoot = fs.mkdtempSync(path.join(projectRoot, ".nexus-frontend-tests-"));

async function bundle(entry, name) {
  const outDir = path.join(outputRoot, name);
  await build({
    root: projectRoot,
    configFile: false,
    logLevel: "silent",
    build: {
      ssr: path.join(projectRoot, entry),
      outDir,
      emptyOutDir: true,
      rollupOptions: { output: { entryFileNames: "entry.mjs" } },
    },
  });
  return import(`${pathToFileURL(path.join(outDir, "entry.mjs")).href}?v=${Date.now()}`);
}

async function testApiClient() {
  const client = await bundle("src/api/client.ts", "client");
  let captured;
  globalThis.fetch = async (url, options) => {
    captured = { url: String(url), options };
    return new Response(JSON.stringify({ id: 1, timezone: "UTC" }), {
      status: 200, headers: { "Content-Type": "application/json" },
    });
  };
  await client.request("/profile/me", {}, "private-token");
  assert.equal(captured.options.headers.get("Authorization"), "Bearer private-token");
  assert.equal(captured.options.headers.get("Content-Type"), "application/json");

  await client.api.search("private-token", "Atlas plan", 12);
  assert.match(captured.url, /\/intelligence\/search\?q=Atlas%20plan&limit=12$/);
  await client.api.updateProfile("private-token", { preferred_currency: "INR" });
  assert.equal(captured.options.method, "PATCH");
  assert.equal(JSON.parse(captured.options.body).preferred_currency, "INR");

  globalThis.fetch = async () => new Response(JSON.stringify({ detail: "Validation failed" }), {
    status: 422, headers: { "Content-Type": "application/json" },
  });
  await assert.rejects(() => client.request("/profile/me"), (error) => error instanceof client.ApiError && error.status === 422 && error.message === "Validation failed");
}

async function testReusableUiStates() {
  const components = await bundle("src/components/ModuleUi.tsx", "components");
  const errorMarkup = renderToStaticMarkup(React.createElement(components.Notice, { kind: "error" }, "Could not save"));
  assert.match(errorMarkup, /role="alert"/);
  assert.match(errorMarkup, /Could not save/);
  const statusMarkup = renderToStaticMarkup(React.createElement(components.Status, { value: "awaiting_review" }));
  assert.match(statusMarkup, /awaiting review/);
  const emptyMarkup = renderToStaticMarkup(React.createElement(components.Empty, null, "Nothing here"));
  assert.match(emptyMarkup, /empty-state/);
}

try {
  await testApiClient();
  console.log("PASS frontend API client contracts and validation errors");
  await testReusableUiStates();
  console.log("PASS frontend reusable loading/error/empty/status components");
  console.log("2 frontend test groups passed");
} finally {
  fs.rmSync(outputRoot, { recursive: true, force: true });
}
