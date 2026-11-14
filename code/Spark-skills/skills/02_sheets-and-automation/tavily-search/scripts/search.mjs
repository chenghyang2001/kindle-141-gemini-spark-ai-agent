#!/usr/bin/env node

import { mkdir, readFile, writeFile, stat } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";
import { createHash } from "node:crypto";

// Claude skills 資料目錄
const CACHE_DIR = join(homedir(), ".claude", "skill-data", "tavily-search", "cache");
const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour
const MAX_RETRIES = 3;

function usage() {
  console.error(`Usage: search.mjs "query" [options]

Options:
  -n <count>                Number of results (1-20, default: 10)
  --depth <mode>            Search depth: ultra-fast, fast, basic, advanced (default: basic)
  --topic <topic>           Topic: general or news (default: general)
  --time-range <range>      Time range: day, week, month, year
  --include-domains <list>  Comma-separated domains to include
  --exclude-domains <list>  Comma-separated domains to exclude
  --raw-content             Include full page content
  --timeout <ms>            Request timeout in milliseconds (default: 30000)
  --no-cache                Skip cache (always hit API)
  --cache-ttl <sec>         Cache TTL in seconds (default: 3600)
  --json                    Output raw JSON

Examples:
  search.mjs "python async patterns"
  search.mjs "React hooks tutorial" -n 10
  search.mjs "AI news" --topic news --time-range week
  search.mjs "Python docs" --include-domains docs.python.org,realpython.com`);
  process.exit(2);
}

function cacheKey(body) {
  return createHash("sha256").update(JSON.stringify(body)).digest("hex").slice(0, 16);
}

async function readCache(key, ttlMs) {
  try {
    const path = join(CACHE_DIR, `${key}.json`);
    const s = await stat(path);
    if (Date.now() - s.mtimeMs > ttlMs) return null;
    return JSON.parse(await readFile(path, "utf8"));
  } catch { return null; }
}

async function writeCache(key, data) {
  try {
    await mkdir(CACHE_DIR, { recursive: true });
    await writeFile(join(CACHE_DIR, `${key}.json`), JSON.stringify(data), "utf8");
  } catch { /* best-effort */ }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

const args = process.argv.slice(2);
if (args.length === 0 || args[0] === "-h" || args[0] === "--help") usage();

const query = args[0];
let maxResults = 10;
let searchDepth = "basic";
let topic = "general";
let timeRange = null;
let includeDomains = [];
let excludeDomains = [];
let includeRawContent = false;
let outputJson = false;
let timeoutMs = 30000;
let useCache = true;
let cacheTtlMs = CACHE_TTL_MS;

const VALID_DEPTHS = ["ultra-fast", "fast", "basic", "advanced"];
const VALID_TOPICS = ["general", "news"];
const VALID_RANGES = ["day", "week", "month", "year"];

for (let i = 1; i < args.length; i++) {
  const a = args[i];
  if (a === "-n") {
    const n = Number.parseInt(args[i + 1] ?? "10", 10);
    if (Number.isNaN(n)) { console.error("Error: -n requires a number"); process.exit(2); }
    maxResults = n;
    i++;
    continue;
  }
  if (a === "--depth") {
    const v = args[i + 1] ?? "basic";
    if (!VALID_DEPTHS.includes(v)) {
      console.error(`Error: --depth must be one of: ${VALID_DEPTHS.join(", ")}`);
      process.exit(2);
    }
    searchDepth = v;
    i++;
    continue;
  }
  if (a === "--topic") {
    const v = args[i + 1] ?? "general";
    if (!VALID_TOPICS.includes(v)) {
      console.error(`Error: --topic must be one of: ${VALID_TOPICS.join(", ")}`);
      process.exit(2);
    }
    topic = v;
    i++;
    continue;
  }
  if (a === "--time-range") {
    const v = args[i + 1];
    if (!VALID_RANGES.includes(v)) {
      console.error(`Error: --time-range must be one of: ${VALID_RANGES.join(", ")}`);
      process.exit(2);
    }
    timeRange = v;
    i++;
    continue;
  }
  if (a === "--include-domains") {
    includeDomains = (args[i + 1] ?? "").split(",").map(d => d.trim()).filter(Boolean);
    i++;
    continue;
  }
  if (a === "--exclude-domains") {
    excludeDomains = (args[i + 1] ?? "").split(",").map(d => d.trim()).filter(Boolean);
    i++;
    continue;
  }
  if (a === "--timeout") {
    const t = Number.parseInt(args[i + 1] ?? "30000", 10);
    if (Number.isNaN(t) || t <= 0) { console.error("Error: --timeout requires positive ms"); process.exit(2); }
    timeoutMs = t;
    i++;
    continue;
  }
  if (a === "--no-cache") { useCache = false; continue; }
  if (a === "--cache-ttl") {
    const t = Number.parseInt(args[i + 1] ?? "3600", 10);
    if (Number.isNaN(t) || t < 0) { console.error("Error: --cache-ttl requires non-negative seconds"); process.exit(2); }
    cacheTtlMs = t * 1000;
    i++;
    continue;
  }
  if (a === "--raw-content") { includeRawContent = true; continue; }
  if (a === "--json") { outputJson = true; continue; }
  console.error(`Unknown arg: ${a}`);
  usage();
}

const apiKey = (process.env.TAVILY_API_KEY ?? "").trim();
if (!apiKey) {
  console.error("Error: TAVILY_API_KEY not set");
  console.error("Get your API key at https://tavily.com");
  console.error("Then set:");
  console.error('  bash/zsh:    export TAVILY_API_KEY="tvly-..."');
  console.error('  PowerShell:  $env:TAVILY_API_KEY = "tvly-..."');
  process.exit(1);
}

const body = {
  query,
  max_results: Math.max(1, Math.min(maxResults, 20)),
  search_depth: searchDepth,
  topic,
  include_raw_content: includeRawContent,
};
if (timeRange) body.time_range = timeRange;
if (includeDomains.length > 0) body.include_domains = includeDomains;
if (excludeDomains.length > 0) body.exclude_domains = excludeDomains;

const key = cacheKey(body);
let data = null;
let fromCache = false;

if (useCache) {
  const cached = await readCache(key, cacheTtlMs);
  if (cached) { data = cached; fromCache = true; }
}

if (!data) {
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    let resp;
    try {
      resp = await fetch("https://api.tavily.com/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${apiKey}`,
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
    } catch (err) {
      clearTimeout(timer);
      if (err.name === "AbortError") {
        if (attempt < MAX_RETRIES) {
          console.error(`Timeout (attempt ${attempt}/${MAX_RETRIES}), retrying...`);
          await sleep(1000 * attempt);
          continue;
        }
        console.error(`Error: request timed out after ${timeoutMs}ms`);
        process.exit(124);
      }
      if (attempt < MAX_RETRIES) {
        console.error(`Network error (attempt ${attempt}/${MAX_RETRIES}): ${err.message}`);
        await sleep(1000 * attempt);
        continue;
      }
      console.error(`Error: network failure - ${err.message}`);
      process.exit(1);
    } finally {
      clearTimeout(timer);
    }

    if (resp.ok) {
      data = await resp.json();
      if (useCache) await writeCache(key, data);
      break;
    }

    const text = await resp.text().catch(() => "");
    const status = resp.status;

    // Retry only on 429 / 5xx
    if ((status === 429 || status >= 500) && attempt < MAX_RETRIES) {
      const retryAfter = resp.headers.get("retry-after");
      const wait = retryAfter ? Number(retryAfter) * 1000 : 1000 * Math.pow(2, attempt - 1);
      console.error(`HTTP ${status} (attempt ${attempt}/${MAX_RETRIES}), retrying in ${wait}ms...`);
      await sleep(wait);
      continue;
    }

    let hint = "";
    if (status === 401) hint = " (check TAVILY_API_KEY)";
    else if (status === 429) hint = " (rate limit hit — slow down or upgrade plan)";
    else if (status === 432) hint = " (monthly quota exhausted — top up at tavily.com)";
    else if (status >= 500) hint = " (Tavily upstream error — try again later)";
    console.error(`Tavily Search failed (${status})${hint}: ${text}`);
    process.exit(1);
  }
}

if (outputJson) {
  console.log(JSON.stringify(data, null, 2));
  process.exit(0);
}

if (data.answer) {
  console.log("## Answer\n");
  console.log(data.answer);
  console.log("\n---\n");
}

const results = (data.results ?? []).slice(0, maxResults);
console.log(`## Sources (${results.length} results)\n`);

for (const r of results) {
  const title = String(r?.title ?? "").trim();
  const url = String(r?.url ?? "").trim();
  const content = String(r?.content ?? "").trim();
  const score = r?.score ? ` (relevance: ${(r.score * 100).toFixed(0)}%)` : "";

  if (!title || !url) continue;

  console.log(`- **${title}**${score}`);
  console.log(`  ${url}`);
  if (content) {
    console.log(`  ${content.slice(0, 300)}${content.length > 300 ? "..." : ""}`);
  }
  console.log();
}

if (data.response_time) {
  console.log(`\nResponse time: ${data.response_time}s${fromCache ? " (cached)" : ""}`);
} else if (fromCache) {
  console.log("\n(served from cache)");
}
